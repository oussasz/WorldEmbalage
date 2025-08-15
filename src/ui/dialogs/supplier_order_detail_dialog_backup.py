"""
Supplier Order Detail Dialog - Display detailed information about a supplier order
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QGroupBox, QFormLayout, QTextEdit, QFrame, QTabWidget, QWidget)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor
from models.orders import SupplierOrder
from ui.styles import IconManager
from decimal import Decimal
from datetime import date, datetime


class SupplierOrderDetailDialog(QDialog):
    """Professional dialog to display detailed supplier order information with plaque details"""
    
    def __init__(self, supplier_order: SupplierOrder, parent=None):
        super().__init__(parent)
        self.supplier_order = supplier_order
        self.setWindowTitle(f'Commande de Matière Première - {supplier_order.bon_commande_ref}')
        self.setWindowIcon(IconManager.get_supplier_order_icon())
        self.setMinimumSize(1100, 700)
        self.setModal(True)
        self._build_ui()
    
    def _build_ui(self):
        """Build the comprehensive dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header with order reference and status
        self._create_header(layout)
        
        # Create tabs for different sections
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                background-color: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #f8f9fa;
                color: #495057;
                padding: 12px 20px;
                margin-right: 2px;
                border: 1px solid #dee2e6;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: white;
                color: #2c3e50;
                border-bottom: 1px solid white;
            }
            QTabBar::tab:hover {
                background: #e9ecef;
            }
        """)
        
        # General Information Tab
        general_tab = QWidget()
        self._create_general_tab(general_tab)
        tab_widget.addTab(general_tab, "📋 Informations Générales")
        
        # Plaques Tab
        plaques_tab = QWidget()
        self._create_plaques_tab(plaques_tab)
        tab_widget.addTab(plaques_tab, "📦 Détails des Plaques")
        
        # Receptions Tab
        receptions_tab = QWidget()
        self._create_receptions_tab(receptions_tab)
        tab_widget.addTab(receptions_tab, "📥 Réceptions")
        
        # Returns Tab (if any)
        if hasattr(self.supplier_order, 'returns') and self.supplier_order.returns:
            returns_tab = QWidget()
            self._create_returns_tab(returns_tab)
            tab_widget.addTab(returns_tab, "↩️ Retours")
        
        layout.addWidget(tab_widget)
        
        # Buttons
        self._create_buttons(layout)
    
    def _create_header(self, layout):
        """Create an enhanced header with order information"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #2c3e50, stop:1 #3498db);
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 15px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        
        # Main title
        title_layout = QHBoxLayout()
        
        # Order reference
        ref_label = QLabel(f"Commande: {self.supplier_order.bon_commande_ref}")
        ref_label.setStyleSheet("""
            color: white;
            font-size: 20px;
            font-weight: bold;
        """)
        
        # Status
        status_value = getattr(self.supplier_order, 'status', 'N/A')
        if hasattr(status_value, 'value'):
            status_text = status_value.value
        else:
            status_text = str(status_value)
        
        status_label = QLabel(status_text.replace('_', ' ').title())
        status_color = self._get_status_color(status_text)
        status_label.setStyleSheet(f"""
            background-color: {status_color};
            color: white;
            padding: 8px 16px;
            border-radius: 16px;
            font-weight: bold;
            font-size: 12px;
        """)
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_layout.addWidget(ref_label)
        title_layout.addStretch()
        title_layout.addWidget(status_label)
        
        # Subtitle with supplier and date
        subtitle_layout = QHBoxLayout()
        supplier_name = self.supplier_order.supplier.name if self.supplier_order.supplier else "Fournisseur inconnu"
        order_date = self._format_date(self.supplier_order.order_date)
        
        subtitle_label = QLabel(f"Fournisseur: {supplier_name} • Date: {order_date}")
        subtitle_label.setStyleSheet("""
            color: #ecf0f1;
            font-size: 14px;
            margin-top: 8px;
        """)
        
        subtitle_layout.addWidget(subtitle_label)
        subtitle_layout.addStretch()
        
        header_layout.addLayout(title_layout)
        header_layout.addLayout(subtitle_layout)
        
        layout.addWidget(header_frame)
        self._create_buttons(layout)
    
    def _create_header(self, layout):
        """Create the header section"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        
        # Order reference
        ref_label = QLabel(f"Commande: {self.supplier_order.bon_commande_ref}")
        ref_font = QFont()
        ref_font.setPointSize(18)
        ref_font.setBold(True)
        ref_label.setFont(ref_font)
        ref_label.setStyleSheet("color: #2c3e50;")
        
        # Status badge
        status_colors = {
            'commande_initial': {'bg': '#fff3cd', 'text': '#856404', 'border': '#ffeaa7'},
            'commande_passee': {'bg': '#cce5ff', 'text': '#004085', 'border': '#b8daff'},
            'commande_arrivee': {'bg': '#d4edda', 'text': '#155724', 'border': '#c3e6cb'}
        }
        
        status_value = self.supplier_order.status.value if hasattr(self.supplier_order.status, 'value') else str(self.supplier_order.status)
        
        status_display = {
            'commande_initial': 'Commande Initial',
            'commande_passee': 'Commande Passée',
            'commande_arrivee': 'Commande Arrivée'
        }.get(status_value.lower(), status_value)
        
        status_style = status_colors.get(status_value.lower(), status_colors['commande_initial'])
        
        status_label = QLabel(status_display)
        status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {status_style['bg']};
                color: {status_style['text']};
                border: 1px solid {status_style['border']};
                border-radius: 12px;
                padding: 4px 12px;
                font-weight: bold;
                font-size: 12px;
            }}
        """)
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(ref_label)
        header_layout.addStretch()
        header_layout.addWidget(status_label)
        
        layout.addWidget(header_frame)
    
    def _create_basic_info_section(self, layout):
        """Create the basic information section"""
        info_group = QGroupBox("Informations Générales")
        info_group.setStyleSheet("QGroupBox { font-weight: bold; color: #2c3e50; }")
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(10)
        
        # Supplier information (enhanced)
        supplier_name = self.supplier_order.supplier.name if self.supplier_order.supplier else "N/A"
        supplier_label = QLabel(supplier_name)
        supplier_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 14px;")
        info_layout.addRow("Fournisseur:", supplier_label)
        
        # Supplier contact name
        if self.supplier_order.supplier and hasattr(self.supplier_order.supplier, 'contact_name') and self.supplier_order.supplier.contact_name:
            contact_label = QLabel(self.supplier_order.supplier.contact_name)
            contact_label.setStyleSheet("font-weight: normal; color: #495057;")
            info_layout.addRow("Personne de contact:", contact_label)
        
        # Supplier phone
        if self.supplier_order.supplier and self.supplier_order.supplier.phone:
            phone_label = QLabel(self.supplier_order.supplier.phone)
            phone_label.setStyleSheet("font-weight: normal; color: #495057;")
            info_layout.addRow("Téléphone:", phone_label)
        
        # Supplier email
        if self.supplier_order.supplier and self.supplier_order.supplier.email:
            email_label = QLabel(self.supplier_order.supplier.email)
            email_label.setStyleSheet("font-weight: normal; color: #495057;")
            info_layout.addRow("Email:", email_label)
        
        # Supplier address
        if self.supplier_order.supplier and self.supplier_order.supplier.address:
            address_label = QLabel(self.supplier_order.supplier.address)
            address_label.setStyleSheet("font-weight: normal; color: #495057;")
            address_label.setWordWrap(True)
            info_layout.addRow("Adresse:", address_label)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #dee2e6;")
        info_layout.addRow(separator)
        
        # Order information
        # Order date
        order_date = "N/A"
        if self.supplier_order.order_date:
            try:
                if isinstance(self.supplier_order.order_date, date):
                    order_date = datetime.combine(self.supplier_order.order_date, datetime.min.time()).strftime("%d/%m/%Y")
                else:
                    order_date = str(self.supplier_order.order_date)
            except (AttributeError, TypeError, ValueError):
                order_date = str(self.supplier_order.order_date)
        
        date_label = QLabel(order_date)
        date_label.setStyleSheet("font-weight: normal; color: #495057;")
        info_layout.addRow("Date de commande:", date_label)
        
        # Creation timestamp
        if hasattr(self.supplier_order, 'created_at') and self.supplier_order.created_at:
            try:
                created_at_str = str(self.supplier_order.created_at)
                # Try to format it nicely if it looks like a datetime
                if "T" in created_at_str or " " in created_at_str:
                    # Basic cleanup of ISO format
                    created_at_str = created_at_str.replace("T", " à ").split(".")[0]
                created_label = QLabel(created_at_str)
                created_label.setStyleSheet("font-weight: normal; color: #6c757d; font-size: 12px;")
                info_layout.addRow("Créée le:", created_label)
            except (AttributeError, TypeError, ValueError):
                pass
        
        # Status
        status_value = self.supplier_order.status.value if hasattr(self.supplier_order.status, 'value') else str(self.supplier_order.status)
        status_display = {
            'commande_initial': 'Commande Initial',
            'commande_passee': 'Commande Passée',
            'commande_arrivee': 'Commande Arrivée'
        }.get(status_value.lower(), status_value)
        
        status_info_label = QLabel(status_display)
        status_info_label.setStyleSheet("font-weight: bold; color: #495057;")
        info_layout.addRow("Statut:", status_info_label)
        
        # Total amount
        if hasattr(self.supplier_order, 'total_amount') and self.supplier_order.total_amount:
            currency = getattr(self.supplier_order, 'currency', 'DZD')
            total_label = QLabel(f"{self.supplier_order.total_amount:,.2f} {currency}")
            total_label.setStyleSheet("font-weight: bold; color: #28a745; font-size: 14px;")
            info_layout.addRow("Total UTTC:", total_label)
        
        # Line items summary
        if hasattr(self.supplier_order, 'line_items') and self.supplier_order.line_items:
            items_count = len(self.supplier_order.line_items)
            clients_count = len(set(item.client_id for item in self.supplier_order.line_items if hasattr(item, 'client_id')))
            summary_label = QLabel(f"{items_count} article(s) pour {clients_count} client(s)")
            summary_label.setStyleSheet("font-weight: normal; color: #6c757d;")
            info_layout.addRow("Articles:", summary_label)
        
        layout.addWidget(info_group)
    
    def _create_receptions_section(self, layout):
        """Create the receptions section"""
        receptions_group = QGroupBox("Réceptions")
        receptions_group.setStyleSheet("QGroupBox { font-weight: bold; color: #2c3e50; }")
        receptions_layout = QVBoxLayout(receptions_group)
        
        # Create table for receptions
        self.receptions_table = QTableWidget()
        headers = ["N°", "Date de Réception", "Quantité", "Notes"]
        self.receptions_table.setColumnCount(len(headers))
        self.receptions_table.setHorizontalHeaderLabels(headers)
        
        # Style the table
        self.receptions_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #dee2e6;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #495057;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f8f9fa;
            }
        """)
        
        # Populate table with receptions
        if self.supplier_order.receptions:
            self.receptions_table.setRowCount(len(self.supplier_order.receptions))
            
            for row, reception in enumerate(self.supplier_order.receptions):
                # Reception number
                self.receptions_table.setItem(row, 0, QTableWidgetItem(str(reception.id)))
                
                # Reception date
                reception_date = "N/A"
                if reception.reception_date:
                    try:
                        if isinstance(reception.reception_date, date):
                            reception_date = datetime.combine(reception.reception_date, datetime.min.time()).strftime("%d/%m/%Y")
                        else:
                            reception_date = str(reception.reception_date)
                    except (AttributeError, TypeError, ValueError):
                        reception_date = str(reception.reception_date)
                self.receptions_table.setItem(row, 1, QTableWidgetItem(reception_date))
                
                # Quantity
                self.receptions_table.setItem(row, 2, QTableWidgetItem(str(reception.quantity)))
                
                # Notes
                notes = reception.notes or ""
                if len(notes) > 100:
                    notes = notes[:97] + "..."
                self.receptions_table.setItem(row, 3, QTableWidgetItem(notes))
        else:
            # Show "No receptions" message
            self.receptions_table.setRowCount(1)
            no_data_item = QTableWidgetItem("Aucune réception enregistrée")
            no_data_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.receptions_table.setItem(0, 0, no_data_item)
            self.receptions_table.setSpan(0, 0, 1, 4)
        
        # Resize columns to content
        self.receptions_table.resizeColumnsToContents()
        self.receptions_table.setColumnWidth(0, 60)   # ID
        self.receptions_table.setColumnWidth(1, 150)  # Date
        self.receptions_table.setColumnWidth(2, 100)  # Quantity
        self.receptions_table.setColumnWidth(3, 300)  # Notes
        
        receptions_layout.addWidget(self.receptions_table)
        layout.addWidget(receptions_group)
    
    def _create_returns_section(self, layout):
        """Create the returns section"""
        if self.supplier_order.returns:
            returns_group = QGroupBox("Retours")
            returns_group.setStyleSheet("QGroupBox { font-weight: bold; color: #2c3e50; }")
            returns_layout = QVBoxLayout(returns_group)
            
            # Create table for returns
            self.returns_table = QTableWidget()
            headers = ["N°", "Date de Retour", "Quantité", "Motif"]
            self.returns_table.setColumnCount(len(headers))
            self.returns_table.setHorizontalHeaderLabels(headers)
            
            # Style the table
            self.returns_table.setStyleSheet("""
                QTableWidget {
                    gridline-color: #dee2e6;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    background-color: white;
                }
                QHeaderView::section {
                    background-color: #f8f9fa;
                    color: #495057;
                    padding: 8px;
                    border: none;
                    border-bottom: 2px solid #dee2e6;
                    font-weight: bold;
                }
                QTableWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #f8f9fa;
                }
            """)
            
            # Populate table with returns
            self.returns_table.setRowCount(len(self.supplier_order.returns))
            
            for row, return_item in enumerate(self.supplier_order.returns):
                # Return number
                self.returns_table.setItem(row, 0, QTableWidgetItem(str(return_item.id)))
                
                # Return date
                return_date = "N/A"
                if return_item.return_date:
                    try:
                        if isinstance(return_item.return_date, date):
                            return_date = datetime.combine(return_item.return_date, datetime.min.time()).strftime("%d/%m/%Y")
                        else:
                            return_date = str(return_item.return_date)
                    except (AttributeError, TypeError, ValueError):
                        return_date = str(return_item.return_date)
                self.returns_table.setItem(row, 1, QTableWidgetItem(return_date))
                
                # Quantity
                self.returns_table.setItem(row, 2, QTableWidgetItem(str(return_item.quantity)))
                
                # Reason
                reason = return_item.reason or ""
                if len(reason) > 100:
                    reason = reason[:97] + "..."
                self.returns_table.setItem(row, 3, QTableWidgetItem(reason))
            
            # Resize columns to content
            self.returns_table.resizeColumnsToContents()
            self.returns_table.setColumnWidth(0, 60)   # ID
            self.returns_table.setColumnWidth(1, 150)  # Date
            self.returns_table.setColumnWidth(2, 100)  # Quantity
            self.returns_table.setColumnWidth(3, 300)  # Reason
            
            returns_layout.addWidget(self.returns_table)
            layout.addWidget(returns_group)
    
    def _create_summary_section(self, layout):
        """Create the summary section"""
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        summary_layout = QHBoxLayout(summary_frame)
        
        # Statistics
        stats_layout = QVBoxLayout()
        
        # Count receptions and returns
        reception_count = len(self.supplier_order.receptions) if self.supplier_order.receptions else 0
        return_count = len(self.supplier_order.returns) if self.supplier_order.returns else 0
        
        stats_layout.addWidget(QLabel(f"Nombre de réceptions: {reception_count}"))
        if return_count > 0:
            stats_layout.addWidget(QLabel(f"Nombre de retours: {return_count}"))
        
        # Calculate total quantities
        total_received = 0
        total_returned = 0
        
        if self.supplier_order.receptions:
            total_received = sum(reception.quantity for reception in self.supplier_order.receptions)
        
        if self.supplier_order.returns:
            total_returned = sum(return_item.quantity for return_item in self.supplier_order.returns)
        
        net_quantity = total_received - total_returned
        
        stats_layout.addWidget(QLabel(f"Quantité reçue: {total_received}"))
        if total_returned > 0:
            stats_layout.addWidget(QLabel(f"Quantité retournée: {total_returned}"))
        
        summary_layout.addLayout(stats_layout)
        summary_layout.addStretch()
        
        # Net quantity (large)
        total_layout = QVBoxLayout()
        total_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        net_label = QLabel("QUANTITÉ NETTE:")
        net_label.setStyleSheet("font-size: 14px; color: #6c757d;")
        total_layout.addWidget(net_label)
        
        quantity_label = QLabel(str(net_quantity))
        quantity_font = QFont()
        quantity_font.setPointSize(20)
        quantity_font.setBold(True)
        quantity_label.setFont(quantity_font)
        
        # Color based on status
        if net_quantity > 0:
            quantity_label.setStyleSheet("color: #28a745;")  # Green for positive
        elif net_quantity == 0:
            quantity_label.setStyleSheet("color: #6c757d;")  # Gray for zero
        else:
            quantity_label.setStyleSheet("color: #dc3545;")  # Red for negative
            
        total_layout.addWidget(quantity_label)
        
        summary_layout.addLayout(total_layout)
        layout.addWidget(summary_frame)
    
    def _create_notes_section(self, layout):
        """Create the notes section"""
        if self.supplier_order.notes:
            notes_group = QGroupBox("Notes")
            notes_group.setStyleSheet("QGroupBox { font-weight: bold; color: #2c3e50; }")
            notes_layout = QVBoxLayout(notes_group)
            
            notes_text = QTextEdit()
            notes_text.setPlainText(self.supplier_order.notes)
            notes_text.setReadOnly(True)
            notes_text.setMaximumHeight(100)
            notes_text.setStyleSheet("""
                QTextEdit {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 8px;
                    color: #495057;
                }
            """)
            
            notes_layout.addWidget(notes_text)
            layout.addWidget(notes_group)
    
    def _create_buttons(self, layout):
        """Create the button section"""
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Fermer")
        close_btn.setMinimumSize(100, 35)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

__all__ = ['SupplierOrderDetailDialog']
