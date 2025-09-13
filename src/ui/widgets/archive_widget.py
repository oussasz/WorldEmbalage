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
        
        # Store value label for updates
        card.value_label = value_label
        
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
        
        # Main content splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Statistics
        stats_scroll = QScrollArea()
        self.stats_widget = ArchiveStatsWidget()
        stats_scroll.setWidget(self.stats_widget)
        stats_scroll.setWidgetResizable(True)
        stats_scroll.setMaximumWidth(400)
        main_splitter.addWidget(stats_scroll)
        
        # Right side: Archive data tabs
        self.tab_widget = QTabWidget()
        self._create_archive_tabs()
        main_splitter.addWidget(self.tab_widget)
        
        # Set splitter proportions
        main_splitter.setSizes([300, 800])
        
        layout.addWidget(main_splitter)
    
    def _create_archive_tabs(self):
        """Create tabs for different types of archived data"""
        # Quotations tab
        self.quotations_table = ArchiveTableWidget([
            "ID", "Reference", "Client", "Date Emission", "Date Validité", 
            "Montant Total", "Description", "Date Archivage"
        ])
        self.quotations_table.setObjectName("quotation")
        self.quotations_table.itemRestoreRequested.connect(self._handle_restore_request)
        self.tab_widget.addTab(self.quotations_table, "📋 Quotations")
        
        # Client Orders tab
        self.client_orders_table = ArchiveTableWidget([
            "ID", "Reference", "Client", "Date Commande", "Statut", 
            "Montant Total", "Quotation", "Date Archivage"
        ])
        self.client_orders_table.setObjectName("client_order")
        self.client_orders_table.itemRestoreRequested.connect(self._handle_restore_request)
        self.tab_widget.addTab(self.client_orders_table, "📦 Commandes Clients")
        
        # Production Batches tab
        self.production_table = ArchiveTableWidget([
            "ID", "Code Lot", "Client", "Dimensions", "Quantité", 
            "Date Production", "Commande Client", "Date Archivage"
        ])
        self.production_table.setObjectName("production_batch")
        self.production_table.itemRestoreRequested.connect(self._handle_restore_request)
        self.tab_widget.addTab(self.production_table, "🏭 Production")
        
        # Supplier Orders tab
        self.supplier_orders_table = ArchiveTableWidget([
            "ID", "Reference", "Fournisseur", "Date Commande", "Statut",
            "Clients", "Date Archivage"
        ])
        self.supplier_orders_table.setObjectName("supplier_order")
        self.supplier_orders_table.itemRestoreRequested.connect(self._handle_restore_request)
        self.tab_widget.addTab(self.supplier_orders_table, "🏪 Cmd. Fournisseurs")
        
        # Workflow Timeline tab
        self.timeline_widget = self._create_timeline_widget()
        self.tab_widget.addTab(self.timeline_widget, "🔄 Timeline")
    
    def _create_timeline_widget(self):
        """Create workflow timeline widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Search and filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search:"))
        
        self.timeline_search = QLineEdit()
        self.timeline_search.setPlaceholderText("Search by client, reference, or description...")
        self.timeline_search.textChanged.connect(self._filter_timeline)
        filter_layout.addWidget(self.timeline_search)
        
        layout.addLayout(filter_layout)
        
        # Timeline table
        self.timeline_table = ArchiveTableWidget([
            "Archive Date", "Workflow ID", "Client", "Type", "Reference", 
            "Description", "Value", "Status"
        ])
        layout.addWidget(self.timeline_table)
        
        return widget
    
    def _setup_refresh_timer(self):
        """Setup automatic refresh timer"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_all_data)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def refresh_all_data(self):
        """Refresh all archive data"""
        try:
            self.stats_widget.refresh_stats()
            self._load_archived_quotations()
            self._load_archived_client_orders()
            self._load_archived_production_batches()
            self._load_archived_supplier_orders()
            self._load_workflow_timeline()
        except Exception as e:
            print(f"Error refreshing archive data: {e}")
            traceback.print_exc()
    
    def _load_archived_quotations(self):
        """Load archived quotations"""
        try:
            session = SessionLocal()
            try:
                quotations = session.query(Quotation).filter(
                    Quotation.notes.like('[ARCHIVED]%')
                ).join(Quotation.client).all()
                
                data = []
                for q in quotations:
                    # Extract archive date from notes
                    archive_date = self._extract_archive_date(q.notes)
                    
                    # Get description from line items or notes
                    description = "N/A"
                    if q.line_items:
                        descriptions = [li.description for li in q.line_items if li.description]
                        if descriptions:
                            description = descriptions[0]
                    if description == "N/A" and q.notes:
                        # Extract description from notes (excluding archive marker)
                        clean_notes = q.notes.replace('[ARCHIVED]', '').strip()
                        if clean_notes:
                            description = clean_notes[:50] + "..." if len(clean_notes) > 50 else clean_notes
                    
                    data.append([
                        str(q.id),
                        q.reference or "N/A",
                        q.client.name if q.client else "N/A",
                        str(q.issue_date) if q.issue_date else "N/A",
                        str(q.valid_until) if q.valid_until else "N/A",
                        f"{q.total_amount:,.2f} {q.currency}" if q.total_amount else "0.00",
                        description,
                        archive_date
                    ])
                
                self.quotations_table.load_data(data)
                
            finally:
                session.close()
        except Exception as e:
            print(f"Error loading archived quotations: {e}")
    
    def _load_archived_client_orders(self):
        """Load archived client orders"""
        try:
            session = SessionLocal()
            try:
                client_orders = session.query(ClientOrder).filter(
                    ClientOrder.notes.like('[ARCHIVED]%')
                ).join(ClientOrder.client).all()
                
                data = []
                for co in client_orders:
                    archive_date = self._extract_archive_date(co.notes)
                    
                    # Get quotation reference
                    quotation_ref = "N/A"
                    if co.quotation:
                        quotation_ref = co.quotation.reference
                    
                    data.append([
                        str(co.id),
                        co.reference or "N/A",
                        co.client.name if co.client else "N/A",
                        str(co.order_date) if co.order_date else "N/A",
                        co.status.value if co.status else "N/A",
                        f"{co.total_amount:,.2f}" if co.total_amount else "0.00",
                        quotation_ref,
                        archive_date
                    ])
                
                self.client_orders_table.load_data(data)
                
            finally:
                session.close()
        except Exception as e:
            print(f"Error loading archived client orders: {e}")
    
    def _load_archived_production_batches(self):
        """Load archived production batches"""
        try:
            session = SessionLocal()
            try:
                production_batches = session.query(ProductionBatch).filter(
                    ProductionBatch.batch_code.like('[ARCHIVED]%')
                ).all()
                
                data = []
                for pb in production_batches:
                    # Extract archive date from batch_code
                    archive_date = self._extract_archive_date_from_batch_code(pb.batch_code)
                    
                    # Get client and dimensions info
                    client_name = "N/A"
                    dimensions = "N/A"
                    client_order_ref = "N/A"
                    
                    if pb.client_order_id:
                        client_order = session.query(ClientOrder).filter(
                            ClientOrder.id == pb.client_order_id
                        ).first()
                        
                        if client_order:
                            client_order_ref = client_order.reference
                            if client_order.client:
                                client_name = client_order.client.name
                                
                            # Get dimensions from quotation
                            if client_order.quotation and client_order.quotation.line_items:
                                line_item = client_order.quotation.line_items[0]
                                if line_item.length_mm and line_item.width_mm and line_item.height_mm:
                                    dimensions = f"{line_item.length_mm}×{line_item.width_mm}×{line_item.height_mm}"
                    
                    # Clean batch code for display
                    clean_batch_code = pb.batch_code.replace('[ARCHIVED]', '').strip()
                    
                    data.append([
                        str(pb.id),
                        clean_batch_code,
                        client_name,
                        dimensions,
                        str(pb.quantity or 0),
                        str(pb.production_date) if pb.production_date else "N/A",
                        client_order_ref,
                        archive_date
                    ])
                
                self.production_table.load_data(data)
                
            finally:
                session.close()
        except Exception as e:
            print(f"Error loading archived production batches: {e}")
    
    def _load_archived_supplier_orders(self):
        """Load archived supplier orders"""
        try:
            session = SessionLocal()
            try:
                supplier_orders = session.query(SupplierOrder).filter(
                    SupplierOrder.notes.like('[ARCHIVED]%')
                ).join(SupplierOrder.supplier).all()
                
                data = []
                for so in supplier_orders:
                    archive_date = self._extract_archive_date(so.notes)
                    
                    # Get clients served by this supplier order
                    clients = set()
                    if hasattr(so, 'line_items') and so.line_items:
                        for item in so.line_items:
                            if hasattr(item, 'client') and item.client:
                                clients.add(item.client.name)
                    
                    clients_str = ", ".join(sorted(clients)) if clients else "N/A"
                    
                    data.append([
                        str(so.id),
                        so.reference or so.bon_commande_ref or "N/A",
                        so.supplier.name if so.supplier else "N/A",
                        str(so.order_date) if so.order_date else "N/A",
                        so.status.value if so.status else "N/A",
                        clients_str,
                        archive_date
                    ])
                
                self.supplier_orders_table.load_data(data)
                
            finally:
                session.close()
        except Exception as e:
            print(f"Error loading archived supplier orders: {e}")
    
    def _load_workflow_timeline(self):
        """Load workflow timeline showing archive progression"""
        try:
            session = SessionLocal()
            try:
                timeline_data = []
                
                # Get archived workflows by looking for production batches with client orders
                production_batches = session.query(ProductionBatch).filter(
                    ProductionBatch.batch_code.like('[ARCHIVED]%')
                ).all()
                
                for pb in production_batches:
                    if pb.client_order_id:
                        client_order = session.query(ClientOrder).filter(
                            ClientOrder.id == pb.client_order_id
                        ).first()
                        
                        if client_order:
                            archive_date = self._extract_archive_date_from_batch_code(pb.batch_code)
                            
                            # Calculate workflow value
                            total_value = 0
                            if client_order.quotation:
                                total_value = float(client_order.quotation.total_amount or 0)
                            
                            # Get description
                            description = "N/A"
                            if client_order.quotation and client_order.quotation.line_items:
                                line_item = client_order.quotation.line_items[0]
                                if line_item.description:
                                    description = line_item.description
                            
                            timeline_data.append([
                                archive_date,
                                f"WF-{pb.id}",
                                client_order.client.name if client_order.client else "N/A",
                                "Complete Workflow",
                                client_order.reference or "N/A",
                                description,
                                f"{total_value:,.2f} DZD",
                                "Archived"
                            ])
                
                # Sort by archive date (newest first)
                timeline_data.sort(key=lambda x: x[0], reverse=True)
                
                self.timeline_table.load_data(timeline_data)
                
            finally:
                session.close()
        except Exception as e:
            print(f"Error loading workflow timeline: {e}")
    
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
    
    def _filter_timeline(self):
        """Filter timeline based on search text"""
        search_text = self.timeline_search.text().lower()
        
        for row in range(self.timeline_table.rowCount()):
            visible = False
            
            # Check each column for search text
            for col in range(self.timeline_table.columnCount()):
                item = self.timeline_table.item(row, col)
                if item and search_text in item.text().lower():
                    visible = True
                    break
            
            self.timeline_table.setRowHidden(row, not visible)
    
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
                
                elif item_type == "supplier_order":
                    supplier_order = session.query(SupplierOrder).filter(SupplierOrder.id == item_id).first()
                    if supplier_order and supplier_order.notes and '[ARCHIVED]' in supplier_order.notes:
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
