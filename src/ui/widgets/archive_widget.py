from __future__ import annotations
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, 
                            QPushButton, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
                            QHeaderView, QSplitter, QTextEdit, QGroupBox, QFormLayout,
                            QMessageBox, QFrame, QScrollArea, QGridLayout, QProgressBar)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor
from config.database import SessionLocal
from models.production import ProductionBatch
from models.orders import ClientOrder, Quotation, SupplierOrder, Reception, QuotationLineItem, SupplierOrderLineItem, Delivery, Invoice
from models.clients import Client
from models.suppliers import Supplier
from datetime import datetime, date
import traceback


class ArchiveStatsWidget(QWidget):
    """Statistics widget showing archive overview"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh_stats()
    
    def _setup_ui(self):
        """Setup statistics UI"""
        layout = QGridLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("📊 Archive Statistics")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title, 0, 0, 1, 3)
        
        # Stats cards
        self.stats_cards = {}
        stats_config = [
            ("quotations", "📋 Quotations Archivées", "#3498db"),
            ("client_orders", "📦 Commandes Clients", "#2ecc71"),
            ("supplier_orders", "🏪 Commandes Fournisseurs", "#e74c3c"),
            ("production", "🏭 Lots de Production", "#f39c12"),
            ("receptions", "📥 Réceptions", "#9b59b6"),
            ("workflows", "🔄 Workflows Complets", "#1abc9c")
        ]
        
        for i, (key, title, color) in enumerate(stats_config):
            card = self._create_stat_card(title, "0", color)
            self.stats_cards[key] = card
            row = 1 + i // 3
            col = i % 3
            layout.addWidget(card, row, col)
    
    def _create_stat_card(self, title: str, value: str, color: str):
        """Create a statistics card"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 10px;
                padding: 5px;
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Value label
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {color};
        """)
        
        # Title label
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 12px;
            color: #7f8c8d;
            margin-top: 5px;
        """)
        title_label.setWordWrap(True)
        
        layout.addWidget(value_label)
        layout.addWidget(title_label)
        
        # Store value label for updates using setProperty
        card.setProperty("value_label", value_label)
        
        return card
    
    def refresh_stats(self):
        """Refresh statistics from database"""
        try:
            session = SessionLocal()
            try:
                # Count archived quotations
                archived_quotations = session.query(Quotation).filter(
                    Quotation.notes.like('[ARCHIVED]%')
                ).count()
                
                # Count archived client orders
                archived_client_orders = session.query(ClientOrder).filter(
                    ClientOrder.notes.like('[ARCHIVED]%')
                ).count()
                
                # Count archived supplier orders
                archived_supplier_orders = session.query(SupplierOrder).filter(
                    SupplierOrder.notes.like('[ARCHIVED]%')
                ).count()
                
                # Count archived production batches
                archived_production = session.query(ProductionBatch).filter(
                    ProductionBatch.batch_code.like('[ARCHIVED]%')
                ).count()
                
                # Count archived receptions (through supplier orders)
                archived_receptions = session.query(Reception).join(Reception.supplier_order).filter(
                    SupplierOrder.notes.like('[ARCHIVED]%')
                ).count()
                
                # Estimate complete workflows (quotation + client order + production)
                complete_workflows = min(archived_quotations, archived_client_orders, archived_production)
                
                # Update cards
                self.stats_cards["quotations"].value_label.setText(str(archived_quotations))
                self.stats_cards["client_orders"].value_label.setText(str(archived_client_orders))
                self.stats_cards["supplier_orders"].value_label.setText(str(archived_supplier_orders))
                self.stats_cards["production"].value_label.setText(str(archived_production))
                self.stats_cards["receptions"].value_label.setText(str(archived_receptions))
                self.stats_cards["workflows"].value_label.setText(str(complete_workflows))
                
            finally:
                session.close()
                
        except Exception as e:
            print(f"Error refreshing archive stats: {e}")


class ArchiveTableWidget(QTableWidget):
    """Enhanced table widget for archive data"""
    
    itemRestoreRequested = pyqtSignal(str, int)  # (item_type, item_id)
    itemDeleteRequested = pyqtSignal(str, int)   # (item_type, item_id)
    
    def __init__(self, headers: list, parent=None):
        super().__init__(0, len(headers), parent)
        self.setHorizontalHeaderLabels(headers)
        self._setup_table()
    
    def _setup_table(self):
        """Setup table appearance and behavior"""
        # Configure headers
        h_header = self.horizontalHeader()
        if h_header:
            h_header.setStretchLastSection(True)
            h_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            
        v_header = self.verticalHeader()
        if v_header:
            v_header.setVisible(False)
            
        # Table styling
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSortingEnabled(True)
        
        # Context menu for restore functionality
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def _show_context_menu(self, position):
        """Show context menu with restore and delete options; works on empty-looking rows too"""
        from PyQt6.QtGui import QAction
        from PyQt6.QtWidgets import QMenu

        # Ensure a row is selected even if cell is visually empty
        row = self.rowAt(position.y())
        if row < 0:
            return
        if self.currentRow() != row:
            # Select a reasonable column (1 = first visible column) if available
            try:
                self.setCurrentCell(row, 1)
            except Exception:
                self.setCurrentCell(row, 0)

        menu = QMenu(self)
        
        restore_action = QAction("🔄 Restore from Archive", self)
        restore_action.triggered.connect(self._restore_selected_item)
        menu.addAction(restore_action)
        
        delete_action = QAction("🗑️ Delete", self)
        delete_action.triggered.connect(self._delete_selected_item)
        menu.addAction(delete_action)
        
        menu.exec(self.mapToGlobal(position))
    
    def _restore_selected_item(self):
        """Restore selected item from archive"""
        current_row = self.currentRow()
        if current_row < 0:
            return
            
        # Get item ID from first column
        id_item = self.item(current_row, 0)
        if not id_item:
            return
            
        try:
            item_id = int(id_item.text())
            # Emit signal with item type and ID for parent to handle
            self.itemRestoreRequested.emit(self.objectName(), item_id)
        except (ValueError, AttributeError):
            pass
    
    def _delete_selected_item(self):
        """Emit delete request for selected row"""
        current_row = self.currentRow()
        if current_row < 0:
            return
        id_item = self.item(current_row, 0)
        if not id_item:
            return
        try:
            item_id = int(id_item.text())
            self.itemDeleteRequested.emit(self.objectName(), item_id)
        except (ValueError, AttributeError):
            pass
    
    def load_data(self, data: list):
        """Load data into table"""
        self.setRowCount(len(data))
        
        for row, row_data in enumerate(data):
            for col, value in enumerate(row_data):
                text = str(value) if value is not None else ''
                # Normalize empties for user visibility (keep ID untouched)
                if col > 0 and (not text.strip() or text.strip().lower() == 'none'):
                    text = 'N/A'
                item = QTableWidgetItem(text)
                
                # Add special styling for archived items
                if col == 0:  # ID column
                    item.setBackground(QColor("#ffe6e6"))  # Light red background
                
                self.setItem(row, col, item)


class ArchiveWidget(QWidget):
    """Comprehensive archive widget for managing archived data"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_refresh_timer()
        self.refresh_all_data()
    
    def _setup_ui(self):
        """Setup the archive widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Header section
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel("🗃️ Archive Management")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_all_data)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Split view: left list, right details
        from PyQt6.QtWidgets import QSplitter
        splitter = QSplitter()
        splitter.setOrientation(Qt.Orientation.Horizontal)

        # Left: simplified list per request (Description, Client, Dimension de caisse)
        self.list_table = ArchiveTableWidget(["ID", "Description", "Client", "Dimension de caisse"])  # keep ID hidden
        self.list_table.setObjectName("archived_transaction")
        self.list_table.itemSelectionChanged.connect(self._on_row_selected)
        # Keep restore via context menu
        self.list_table.itemRestoreRequested.connect(self._handle_restore_request)
        self.list_table.itemDeleteRequested.connect(self._handle_delete_request)
        splitter.addWidget(self.list_table)

        # Hide ID column visually but keep for internal use
        try:
            self.list_table.setColumnHidden(0, True)
        except Exception:
            pass

        # Right: details panel
        self.details_panel = QTextEdit()
        self.details_panel.setReadOnly(True)
        splitter.addWidget(self.details_panel)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 4)

        layout.addWidget(splitter)
    
    # Removed legacy tab-based archive view in favor of split list/details
    
    def _setup_refresh_timer(self):
        """Setup automatic refresh timer"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_all_data)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def refresh_all_data(self):
        """Refresh all archive data"""
        try:
            self._load_archived_transactions()
        except Exception as e:
            print(f"Error refreshing archive data: {e}")
            traceback.print_exc()
    
    def _load_archived_transactions(self):
        """Load archived production entries into simplified list and cache details"""
        try:
            session = SessionLocal()
            try:
                # Get archived production batches as the main driver
                production_batches = session.query(ProductionBatch).filter(
                    ProductionBatch.batch_code.like('[ARCHIVED]%')
                ).all()
                
                data = []
                self._details_cache = {}
                for pb in production_batches:
                    try:
                        # Get client order and related information
                        client_name = "N/A"
                        description = "N/A"
                        caisse_dimensions = "N/A"
                        archive_date = self._extract_archive_date_from_batch_code(pb.batch_code)
                        
                        # Try to fetch ClientOrder and relations
                        co = session.query(ClientOrder).filter(ClientOrder.id == pb.client_order_id).first() if getattr(pb, 'client_order_id', None) else None
                        
                        # Determine client name (prefer ClientOrder, fallback to SupplierOrder line item client)
                        if co and co.client:
                            client_name = co.client.name
                        elif co and getattr(co, 'supplier_order', None) and co.supplier_order.line_items:
                            first_li = co.supplier_order.line_items[0]
                            if getattr(first_li, 'client', None):
                                client_name = first_li.client.name
                        
                        # Determine caisse dimensions (prefer SupplierOrder line item, fallback to quotation line)
                        if co and getattr(co, 'supplier_order', None) and co.supplier_order.line_items:
                            sli = co.supplier_order.line_items[0]
                            if all([sli.caisse_length_mm, sli.caisse_width_mm, sli.caisse_height_mm]):
                                caisse_dimensions = f"{sli.caisse_length_mm}×{sli.caisse_width_mm}×{sli.caisse_height_mm}mm"
                        if caisse_dimensions == "N/A" and co and co.quotation and co.quotation.line_items:
                            qli = co.quotation.line_items[0]
                            if all([qli.length_mm, qli.width_mm, qli.height_mm]):
                                caisse_dimensions = f"{qli.length_mm}×{qli.width_mm}×{qli.height_mm}mm"

                        # Determine description (prefer quotation description, then notes, then generated from dims)
                        if co and co.quotation and co.quotation.line_items:
                            qli = co.quotation.line_items[0]
                            if qli.description and qli.description.strip():
                                description = qli.description.strip()
                            elif co.quotation.notes and co.quotation.notes.strip():
                                description = co.quotation.notes.replace('[ARCHIVED]', '').strip()
                            elif all([qli.length_mm, qli.width_mm, qli.height_mm]):
                                cardboard_info = qli.cardboard_type or 'Standard'
                                description = f"Carton {cardboard_info} {qli.length_mm}×{qli.width_mm}×{qli.height_mm}mm"
                        # Last resort: use production batch description
                        if description == "N/A":
                            _desc_val = getattr(pb, 'description', None)
                            if isinstance(_desc_val, str) and _desc_val.strip():
                                description = _desc_val.strip()
                        
                        # Fill details cache using [ARCHIVE_DETAIL] from ClientOrder.notes if present
                        archived_detail = None
                        try:
                            if pb.client_order_id:
                                co = session.query(ClientOrder).filter(ClientOrder.id == pb.client_order_id).first()
                                if co and co.notes and '[ARCHIVE_DETAIL]' in co.notes:
                                    import json
                                    # Take the last [ARCHIVE_DETAIL] line
                                    lines = [ln.strip() for ln in co.notes.splitlines() if ln.strip().startswith('[ARCHIVE_DETAIL]')]
                                    if lines:
                                        payload = lines[-1][len('[ARCHIVE_DETAIL] '):].strip()
                                        archived_detail = json.loads(payload)
                        except Exception:
                            archived_detail = None

                        # Use archived detail as fallback to reduce N/A in the list
                        if archived_detail and isinstance(archived_detail, dict):
                            q = archived_detail.get('quotation', {}) or {}
                            so = archived_detail.get('supplier_order', {}) or {}
                            if description == "N/A":
                                description = q.get('description') or archived_detail.get('description') or description
                            if caisse_dimensions == "N/A":
                                caisse_dimensions = q.get('caisse_dimensions') or caisse_dimensions
                            if client_name == "N/A":
                                client_name = archived_detail.get('client_name') or client_name

                        # Push to left list
                        data.append([str(pb.id), description, client_name, caisse_dimensions])

                        # Assemble rich details text for right panel: include full data from DB (quotation + supplier order)
                        details_parts = []
                        # Header
                        details_parts.append(
                            (
                                f"Archive Details\n\n"
                                f"Lot: {pb.id}  Code: {getattr(pb, 'batch_code', '')}\n"
                                f"Quantité: {getattr(pb, 'quantity', 'N/A')}   Date production: {getattr(pb, 'production_date', 'N/A')}\n"
                                f"Client: {client_name}\n"
                                f"Description: {description}\n"
                                f"Dimensions caisse: {caisse_dimensions}\n"
                            )
                        )
                        # Quotation section
                        if co and co.quotation:
                            q = co.quotation
                            details_parts.append(
                                (
                                    f"\n— Devis —\n"
                                    f"Référence: {q.reference}\nDate: {getattr(q, 'issue_date', 'N/A')}  Valide jusqu'au: {getattr(q, 'valid_until', 'N/A')}\n"
                                    f"Devise: {getattr(q, 'currency', 'DZD')}  Total: {getattr(q, 'total_amount', 'N/A')}\n"
                                    f"Notes: {getattr(q, 'notes', '') or '—'}\n"
                                )
                            )
                            if q.line_items:
                                details_parts.append("Lignes de devis:")
                                for li in q.line_items:
                                    dims = (
                                        f"{li.length_mm}×{li.width_mm}×{li.height_mm}mm" if all([li.length_mm, li.width_mm, li.height_mm]) else "N/A"
                                    )
                                    color = getattr(li, 'color', None)
                                    color_val = color.value if color else None
                                    details_parts.append(
                                        (
                                            f"  - #{li.line_number} {li.description or ''}\n"
                                            f"    Qté: {li.quantity}  PU: {getattr(li, 'unit_price', 'N/A')}  Total: {getattr(li, 'total_price', 'N/A')}\n"
                                            f"    Dimensions caisse: {dims}  Couleur: {color_val or 'N/A'}  Carton: {li.cardboard_type or 'N/A'}\n"
                                            f"    Réf matière: {getattr(li, 'material_reference', '') or '—'}  Cliché: {'Oui' if getattr(li, 'is_cliche', False) else 'Non'}\n"
                                        )
                                    )
                        # Supplier order section
                        if co and getattr(co, 'supplier_order', None):
                            so = co.supplier_order
                            supplier_name = getattr(getattr(so, 'supplier', None), 'name', 'N/A')
                            details_parts.append(
                                (
                                    f"\n— Commande Matière Première —\n"
                                    f"Bon: {getattr(so, 'bon_commande_ref', getattr(so, 'reference', 'N/A'))}  Date: {getattr(so, 'order_date', 'N/A')}  Statut: {getattr(so, 'status', 'N/A')}\n"
                                    f"Fournisseur: {supplier_name}  Total: {getattr(so, 'total_amount', 'N/A')} {getattr(so, 'currency', 'DZD')}\n"
                                    f"Notes: {getattr(so, 'notes', '') or '—'}\n"
                                )
                            )
                            if so.line_items:
                                details_parts.append("Lignes de commande:")
                                for li in so.line_items:
                                    caisse = f"{li.caisse_length_mm}×{li.caisse_width_mm}×{li.caisse_height_mm}mm"
                                    plaque = f"{li.plaque_width_mm}×{li.plaque_length_mm}mm" + (f" (Rabat: {li.plaque_flap_mm}mm)" if getattr(li, 'plaque_flap_mm', None) else "")
                                    details_parts.append(
                                        (
                                            f"  - {li.code_article}  Qté plaques: {li.quantity}  UTTC: {getattr(li, 'prix_uttc_plaque', 'N/A')}  Total: {getattr(li, 'total_line_amount', 'N/A')}\n"
                                            f"    Caisse: {caisse}  Plaque: {plaque}\n"
                                            f"    Client: {getattr(getattr(li, 'client', None), 'name', 'N/A')}  Réf matière: {getattr(li, 'material_reference', '') or '—'}  Carton: {getattr(li, 'cardboard_type', '') or '—'}\n"
                                            f"    Notes: {getattr(li, 'notes', '') or '—'}\n"
                                        )
                                    )

                        # Delivery and invoice quick summary
                        if co:
                            try:
                                deliveries = session.query(Delivery).filter(Delivery.client_order_id == co.id).all()
                                delivered_qty = sum(getattr(d, 'quantity', 0) or 0 for d in deliveries)
                                invoices = session.query(Invoice).filter(Invoice.client_order_id == co.id).all()
                                details_parts.append(
                                    (
                                        f"\n— Suivi —\n"
                                        f"Livraisons: {len(deliveries)}  Quantité livrée: {delivered_qty}\n"
                                        f"Factures: {len(invoices)}\n"
                                    )
                                )
                            except Exception:
                                pass
                        elif archived_detail and isinstance(archived_detail, dict):
                            # Provide minimal summary from archived detail if DB relations are absent
                            q = archived_detail.get('quotation', {})
                            so = archived_detail.get('supplier_order', {})
                            details_parts.append("\n— Données archivées —")
                            details_parts.append(
                                (
                                    f"Devis: {q.get('reference', 'N/A')}  PU: {q.get('unit_price', 'N/A')}  Total: {q.get('total_price', 'N/A')}\n"
                                    f"Description: {q.get('description', 'N/A')}  Caisse: {q.get('caisse_dimensions', 'N/A')}  Carton: {q.get('cardboard_type', 'N/A')}  Couleur: {q.get('color', 'N/A')}\n"
                                )
                            )
                            details_parts.append(
                                (
                                    f"BC Matière: {so.get('reference', 'N/A')}  Plaque: {so.get('plaque_dimensions', 'N/A')}  UTTC: {so.get('prix_uttc_plaque', 'N/A')}  Total: {so.get('total_amount', 'N/A')}\n"
                                )
                            )

                        # Include archived detail timestamp if present
                        if archived_detail and isinstance(archived_detail, dict):
                            details_parts.append(f"\nArchivé le: {archived_detail.get('archived_at', archive_date)}")
                        else:
                            details_parts.append(f"\nArchivé le: {archive_date}")

                        details_text = "\n".join(details_parts)

                        self._details_cache[str(pb.id)] = details_text
                        
                    except Exception as e:
                        print(f"Error processing production batch {pb.id}: {e}")
                        continue
                
                # Sort by archive date (newest first)
                # Sort by description ascending for easy scan
                try:
                    data.sort(key=lambda x: (x[1] or '').lower())
                except Exception:
                    pass

                self.list_table.load_data(data)
                
            finally:
                session.close()
        except Exception as e:
            print(f"Error loading archived transactions: {e}")
            traceback.print_exc()

    def _extract_archive_date(self, notes: str) -> str:
        """Extract archive date from notes field"""
        if not notes or '[ARCHIVED]' not in notes:
            return "Unknown"
        
        # For now, use current date since we don't store archive timestamp
        # In future, we could enhance this to store actual archive timestamp
        return datetime.now().strftime('%Y-%m-%d %H:%M')
    
    def _extract_archive_date_from_batch_code(self, batch_code: str) -> str:
        """Extract archive date from batch code"""
        if not batch_code or '[ARCHIVED]' not in batch_code:
            return "Unknown"
        
        return datetime.now().strftime('%Y-%m-%d %H:%M')
    
    def _handle_restore_request(self, item_type: str, item_id: int):
        """Handle restore request for archived item"""
        reply = QMessageBox.question(
            self,
            'Confirm Restore',
            f'Are you sure you want to restore this {item_type.replace("_", " ")} '
            f'from archive back to active workflow?\n\n'
            f'This will make the item visible in the main application again.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._restore_item(item_type, item_id)

    def _handle_delete_request(self, item_type: str, item_id: int):
        """Handle delete request for archived item"""
        reply = QMessageBox.warning(
            self,
            'Delete Archived Item',
            'This will permanently delete the archived production lot from the database.\n\n'
            'The linked Devis/Commande ne seront PAS supprimés.\n\n'
            'Do you want to continue?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            session = SessionLocal()
            try:
                if item_type not in {"archived_transaction", "production_batch"}:
                    QMessageBox.information(self, 'Unsupported', 'Only archived production lots can be deleted here.')
                    return
                pb = session.query(ProductionBatch).filter(ProductionBatch.id == item_id).first()
                if not pb:
                    QMessageBox.warning(self, 'Not found', 'Archived production lot not found.')
                    return
                # Only allow delete if it is archived
                if not (pb.batch_code or '').startswith('[ARCHIVED]'):
                    QMessageBox.information(self, 'Blocked', 'Only archived lots can be deleted.')
                    return
                session.delete(pb)
                session.commit()
                QMessageBox.information(self, 'Deleted', 'Archived production lot deleted.')
                self.refresh_all_data()
            finally:
                session.close()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to delete archived item: {e}')

    def _on_row_selected(self):
        """Render details when a row is selected"""
        try:
            current_row = self.list_table.currentRow()
            if current_row < 0:
                return
            id_item = self.list_table.item(current_row, 0)
            if not id_item:
                return
            pb_id = id_item.text()
            details = self._details_cache.get(pb_id, "Aucun détail disponible.")
            self.details_panel.setPlainText(details)
        except Exception as e:
            self.details_panel.setPlainText(f"Erreur lors de l'affichage des détails: {e}")
    
    def _restore_item(self, item_type: str, item_id: int):
        """Restore an item from archive"""
        try:
            session = SessionLocal()
            try:
                success = False
                
                if item_type == "quotation":
                    quotation = session.query(Quotation).filter(Quotation.id == item_id).first()
                    if quotation and quotation.notes and '[ARCHIVED]' in quotation.notes:
                        quotation.notes = quotation.notes.replace('[ARCHIVED]', '').strip()
                        if not quotation.notes:
                            quotation.notes = None
                        success = True
                
                elif item_type == "client_order":
                    client_order = session.query(ClientOrder).filter(ClientOrder.id == item_id).first()
                    if client_order and client_order.notes and '[ARCHIVED]' in client_order.notes:
                        client_order.notes = client_order.notes.replace('[ARCHIVED]', '').strip()
                        if not client_order.notes:
                            client_order.notes = None
                        success = True
                
                elif item_type == "production_batch":
                    production_batch = session.query(ProductionBatch).filter(ProductionBatch.id == item_id).first()
                    if production_batch and '[ARCHIVED]' in production_batch.batch_code:
                        production_batch.batch_code = production_batch.batch_code.replace('[ARCHIVED]', '').strip()
                        success = True
                
                elif item_type == "archived_transaction":
                    # For archived transactions, we restore the entire workflow starting from production batch
                    production_batch = session.query(ProductionBatch).filter(ProductionBatch.id == item_id).first()
                    if production_batch and '[ARCHIVED]' in production_batch.batch_code:
                        # Remove archive marker from production batch
                        production_batch.batch_code = production_batch.batch_code.replace('[ARCHIVED]', '').strip()
                        
                        # Restore related client order if exists
                        if production_batch.client_order_id:
                            client_order = session.query(ClientOrder).filter(
                                ClientOrder.id == production_batch.client_order_id
                            ).first()
                            
                            if client_order and client_order.notes and '[ARCHIVED]' in client_order.notes:
                                client_order.notes = client_order.notes.replace('[ARCHIVED]', '').strip()
                                if not client_order.notes:
                                    client_order.notes = None
                                
                                # Restore related quotation if exists
                                if client_order.quotation and client_order.quotation.notes and '[ARCHIVED]' in client_order.quotation.notes:
                                    client_order.quotation.notes = client_order.quotation.notes.replace('[ARCHIVED]', '').strip()
                                    if not client_order.quotation.notes:
                                        client_order.quotation.notes = None
                                
                                # Restore related supplier order if exists
                                if hasattr(client_order, 'supplier_order') and client_order.supplier_order:
                                    supplier_order = client_order.supplier_order
                                    if supplier_order.notes and '[ARCHIVED]' in supplier_order.notes:
                                        supplier_order.notes = supplier_order.notes.replace('[ARCHIVED]', '').strip()
                                        if not supplier_order.notes:
                                            supplier_order.notes = None
                        
                        success = True
                
                if success:
                    session.commit()
                    QMessageBox.information(
                        self,
                        'Restore Successful',
                        f'{item_type.replace("_", " ").title()} has been successfully restored from archive.'
                    )
                    
                    # Refresh all data
                    self.refresh_all_data()
                else:
                    QMessageBox.warning(
                        self,
                        'Restore Failed',
                        f'Could not restore {item_type.replace("_", " ")} from archive.'
                    )
                
            finally:
                session.close()
                
        except Exception as e:
            QMessageBox.critical(
                self,
                'Error',
                f'Error restoring item from archive: {str(e)}'
            )


__all__ = ['ArchiveWidget']
