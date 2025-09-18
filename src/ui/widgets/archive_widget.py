from __future__ import annotations
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, 
                            QPushButton, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
                            QHeaderView, QSplitter, QTextEdit, QGroupBox, QFormLayout,
                            QMessageBox, QFrame, QScrollArea, QGridLayout, QProgressBar)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor
from config.database import SessionLocal
from models.production import ProductionBatch
from models.orders import ClientOrder, Quotation, SupplierOrder, Reception
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
        """Show context menu with restore option"""
        from PyQt6.QtGui import QAction
        from PyQt6.QtWidgets import QMenu
        
        if self.itemAt(position) is None:
            return
            
        menu = QMenu(self)
        
        restore_action = QAction("🔄 Restore from Archive", self)
        restore_action.triggered.connect(self._restore_selected_item)
        menu.addAction(restore_action)
        
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
    
    def load_data(self, data: list):
        """Load data into table"""
        self.setRowCount(len(data))
        
        for row, row_data in enumerate(data):
            for col, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                
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
        
        # Archive data tabs (no statistics)
        self.tab_widget = QTabWidget()
        self._create_archive_tabs()
        layout.addWidget(self.tab_widget)
    
    def _create_archive_tabs(self):
        """Create unified archive table for archived transactions"""
        # Single unified archive table
        self.archive_table = ArchiveTableWidget([
            "ID", "Client", "Description", "Caisse Dimensions", "Plaque Dimensions", 
            "Prix Achat Plaque", "Prix Vente Caisse", "Date Livraison", "Facture Générée", "Date Archivage"
        ])
        self.archive_table.setObjectName("archived_transaction")
        self.archive_table.itemRestoreRequested.connect(self._handle_restore_request)
        self.tab_widget.addTab(self.archive_table, "📦 Archived Transactions")
    
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
        """Load unified archived transactions combining all workflow data"""
        try:
            session = SessionLocal()
            try:
                # Get archived production batches as the main driver
                production_batches = session.query(ProductionBatch).filter(
                    ProductionBatch.batch_code.like('[ARCHIVED]%')
                ).all()
                
                data = []
                for pb in production_batches:
                    try:
                        # Get client order and related information
                        client_name = "N/A"
                        description = "N/A"
                        caisse_dimensions = "N/A"
                        plaque_dimensions = "N/A"
                        prix_achat_plaque = "N/A"
                        prix_vente_caisse = "N/A"
                        date_livraison = "N/A"
                        facture_generee = "Non"
                        archive_date = self._extract_archive_date_from_batch_code(pb.batch_code)
                        
                        # Get description (priority: production batch -> quotation -> generated)
                        description = "N/A"
                        
                        # First priority: Check production batch description
                        if hasattr(pb, 'description') and pb.description and pb.description.strip():
                            description = pb.description.strip()
                        
                        # Second priority: Get from client order quotation if batch description not available
                        if description == "N/A" and pb.client_order_id:
                            client_order = session.query(ClientOrder).filter(
                                ClientOrder.id == pb.client_order_id
                            ).first()
                            
                            if client_order:
                                # Client
                                if client_order.client:
                                    client_name = client_order.client.name
                                
                                # Date de livraison (use production date)
                                if pb.production_date:
                                    date_livraison = str(pb.production_date)
                                
                                # Prix de vente (from quotation)
                                if client_order.quotation:
                                    quotation = client_order.quotation
                                    if quotation.total_amount:
                                        prix_vente_caisse = f"{quotation.total_amount:,.2f} DZD"
                                    
                                    # Description and dimensions from quotation line items
                                    if quotation.line_items:
                                        line_item = quotation.line_items[0]  # Take first item
                                        
                                        # Description - comprehensive approach
                                        if line_item.description and line_item.description.strip():
                                            description = line_item.description.strip()
                                        elif quotation.notes and quotation.notes.strip():
                                            # Fallback to quotation notes
                                            clean_notes = quotation.notes.replace('[ARCHIVED]', '').strip()
                                            if clean_notes:
                                                description = clean_notes
                                        else:
                                            # Generate description from dimensions and type
                                            if line_item.length_mm and line_item.width_mm and line_item.height_mm:
                                                cardboard_info = line_item.cardboard_type or "Standard"
                                                description = f"Carton {cardboard_info} {line_item.length_mm}×{line_item.width_mm}×{line_item.height_mm}mm"
                                        
                                        # Caisse dimensions
                                        if line_item.length_mm and line_item.width_mm and line_item.height_mm:
                                            caisse_dimensions = f"{line_item.length_mm}×{line_item.width_mm}×{line_item.height_mm}mm"
                                
                                # Prix d'achat plaque and plaque dimensions (from supplier order)
                                if hasattr(client_order, 'supplier_order') and client_order.supplier_order:
                                    supplier_order = client_order.supplier_order
                                    if supplier_order.total_amount:
                                        prix_achat_plaque = f"{supplier_order.total_amount:,.2f} DZD"
                                    
                                    # Get plaque dimensions from supplier order line items
                                    if hasattr(supplier_order, 'line_items') and supplier_order.line_items:
                                        so_line_item = supplier_order.line_items[0]  # Take first item
                                        if hasattr(so_line_item, 'plaque_width_mm') and hasattr(so_line_item, 'plaque_length_mm'):
                                            if so_line_item.plaque_width_mm and so_line_item.plaque_length_mm:
                                                plaque_dimensions = f"{so_line_item.plaque_width_mm}×{so_line_item.plaque_length_mm}mm"
                                                if hasattr(so_line_item, 'plaque_flap_mm') and so_line_item.plaque_flap_mm:
                                                    plaque_dimensions += f" (Rabat: {so_line_item.plaque_flap_mm}mm)"
                                
                                # Check if invoice was generated (simplified check)
                                if client_order.status and client_order.status.value == "terminé":
                                    facture_generee = "Oui"
                        
                        data.append([
                            str(pb.id),
                            client_name,
                            description,
                            caisse_dimensions,
                            plaque_dimensions,
                            prix_achat_plaque,
                            prix_vente_caisse,
                            date_livraison,
                            facture_generee,
                            archive_date
                        ])
                        
                    except Exception as e:
                        print(f"Error processing production batch {pb.id}: {e}")
                        continue
                
                # Sort by archive date (newest first)
                data.sort(key=lambda x: x[9], reverse=True)
                
                self.archive_table.load_data(data)
                
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
