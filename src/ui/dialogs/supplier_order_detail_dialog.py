from __future__ import annotations
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QTabWidget, QWidget, QFormLayout, QLineEdit, QTextEdit,
                           QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
                           QFrame, QGridLayout, QAbstractItemView, QScrollArea)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor, QPalette
from typing import Optional
from decimal import Decimal


class SupplierOrderDetailDialog(QDialog):
    """Professional dialog for displaying supplier order details with comprehensive information"""
    
    def __init__(self, supplier_order, parent=None):
        super().__init__(parent)
        self.supplier_order = supplier_order
        self.setWindowTitle(f"Détails Commande Matière Première - {supplier_order.bon_commande_ref}")
        self.setMinimumSize(1200, 600)
        self.resize(1400, 800)
        self.setModal(True)
        
        # Enable resize and ensure the dialog can be scrolled
        self.setSizeGripEnabled(True)
        
        # Apply professional styling
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #495057;
            }
            QLabel {
                color: #495057;
            }
            QLineEdit, QTextEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                background-color: #ffffff;
            }
            QLineEdit:read-only, QTextEdit:read-only {
                background-color: #f8f9fa;
                color: #6c757d;
            }
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
                alternate-background-color: #f8f9fa;
                gridline-color: #dee2e6;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #dee2e6;
            }
            QTableWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            QHeaderView::section {
                background-color: #e9ecef;
                color: #495057;
                padding: 10px;
                border: none;
                border-right: 1px solid #dee2e6;
                font-weight: bold;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                background-color: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                color: #495057;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #007bff;
            }
        """)
        
        self._setup_ui()
        self._populate_data()
    
    def _setup_ui(self):
        """Setup the user interface with tabs and sections"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Header section with key information
        header_frame = self._create_header_section()
        layout.addWidget(header_frame)
        
        # Tab widget for detailed information with enhanced styling
        tab_widget = QTabWidget()
        tab_widget.setMinimumHeight(400)  # Reduced minimum height
        
        # Additional tab styling for better display
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #dee2e6;
                background-color: white;
                border-radius: 6px;
                margin-top: 2px;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                color: #495057;
                padding: 12px 24px;
                margin-right: 3px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 500;
                font-size: 13px;
                min-width: 140px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 3px solid #007bff;
                color: #2c3e50;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e9ecef;
            }
        """)
        
        # General Information Tab
        general_tab = self._create_general_tab()
        tab_widget.addTab(general_tab, "📋 Informations Générales")
        
        # Plaques Details Tab
        plaques_tab = self._create_plaques_tab()
        tab_widget.addTab(plaques_tab, "📦 Détails des Plaques")
        
        # Financial Summary Tab
        financial_tab = self._create_financial_tab()
        tab_widget.addTab(financial_tab, "💰 Résumé Financier")
        
        # History & Notes Tab
        history_tab = self._create_history_tab()
        tab_widget.addTab(history_tab, "📝 Historique & Notes")
        
        layout.addWidget(tab_widget, 1)
        
        # Action buttons with better spacing
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Fermer")
        close_btn.setMinimumHeight(45)
        close_btn.setMinimumWidth(120)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #495057;
            }
        """)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_header_section(self) -> QFrame:
        """Create header section with key order information using consistent styling"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
            QLabel {
                color: #495057;
            }
        """)
        
        layout = QGridLayout(frame)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel(f"Commande Matière Première")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title_label, 0, 0, 1, 4)
        
        # Reference
        ref_label = QLabel("Référence:")
        ref_label.setFont(QFont("", 11, QFont.Weight.Bold))
        ref_label.setStyleSheet("color: #6c757d;")
        ref_value = QLabel(self.supplier_order.bon_commande_ref)
        ref_value.setFont(QFont("", 13, QFont.Weight.Bold))
        ref_value.setStyleSheet("color: #2c3e50;")
        layout.addWidget(ref_label, 1, 0)
        layout.addWidget(ref_value, 1, 1)
        
        # Status with colored badge
        status_label = QLabel("Statut:")
        status_label.setFont(QFont("", 11, QFont.Weight.Bold))
        status_label.setStyleSheet("color: #6c757d;")
        
        status_display = self._get_status_display()
        status_value = QLabel(status_display)
        status_value.setFont(QFont("", 11, QFont.Weight.Bold))
        
        # Color-coded status
        status_colors = {
            'Initial': '#ffc107',
            'Commandé': '#007bff', 
            'En cours': '#fd7e14',
            'Reçu': '#28a745',
            'Annulé': '#dc3545'
        }
        status_color = status_colors.get(status_display, '#6c757d')
        status_value.setStyleSheet(f"""
            background-color: {status_color};
            color: white;
            padding: 6px 12px;
            border-radius: 15px;
            font-weight: bold;
        """)
        status_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(status_label, 1, 2)
        layout.addWidget(status_value, 1, 3)
        
        # Date
        date_label = QLabel("Date de commande:")
        date_label.setFont(QFont("", 11, QFont.Weight.Bold))
        date_label.setStyleSheet("color: #6c757d;")
        date_value = QLabel(self.supplier_order.order_date.strftime("%d/%m/%Y"))
        date_value.setFont(QFont("", 12))
        date_value.setStyleSheet("color: #495057;")
        layout.addWidget(date_label, 2, 0)
        layout.addWidget(date_value, 2, 1)
        
        # Total with emphasis
        total_label = QLabel("Total:")
        total_label.setFont(QFont("", 11, QFont.Weight.Bold))
        total_label.setStyleSheet("color: #6c757d;")
        total_amount = float(self.supplier_order.total_amount) if self.supplier_order.total_amount else 0.0
        total_value = QLabel(f"{total_amount:,.2f} {self.supplier_order.currency}")
        total_value.setFont(QFont("", 14, QFont.Weight.Bold))
        total_value.setStyleSheet("color: #28a745; background-color: #f8f9fa; padding: 8px; border-radius: 4px;")
        layout.addWidget(total_label, 2, 2)
        layout.addWidget(total_value, 2, 3)
        
        return frame
    
    def _create_general_tab(self) -> QWidget:
        """Create general information tab with scrolling"""
        # Main widget
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Content widget that will be scrollable
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Supplier Information Group
        supplier_group = QGroupBox("Informations Fournisseur")
        supplier_layout = QFormLayout(supplier_group)
        supplier_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        supplier_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        supplier_layout.setHorizontalSpacing(15)
        supplier_layout.setVerticalSpacing(10)
        
        supplier_name = QLineEdit(self.supplier_order.supplier.name if self.supplier_order.supplier else "N/A")
        supplier_name.setReadOnly(True)
        supplier_name.setMinimumHeight(35)
        supplier_name.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 8px; font-size: 12px;")
        supplier_layout.addRow("Nom du fournisseur:", supplier_name)
        
        if hasattr(self.supplier_order.supplier, 'contact_person') and self.supplier_order.supplier.contact_person:
            contact = QLineEdit(self.supplier_order.supplier.contact_person)
            contact.setReadOnly(True)
            contact.setMinimumHeight(35)
            contact.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 8px; font-size: 12px;")
            supplier_layout.addRow("Personne de contact:", contact)
        
        if hasattr(self.supplier_order.supplier, 'phone') and self.supplier_order.supplier.phone:
            phone = QLineEdit(self.supplier_order.supplier.phone)
            phone.setReadOnly(True)
            phone.setMinimumHeight(35)
            phone.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 8px; font-size: 12px;")
            supplier_layout.addRow("Téléphone:", phone)
        
        if hasattr(self.supplier_order.supplier, 'email') and self.supplier_order.supplier.email:
            email = QLineEdit(self.supplier_order.supplier.email)
            email.setReadOnly(True)
            email.setMinimumHeight(35)
            email.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 8px; font-size: 12px;")
            supplier_layout.addRow("Email:", email)
        
        layout.addWidget(supplier_group)
        
        # Order Information Group
        order_group = QGroupBox("Informations de Commande")
        order_layout = QFormLayout(order_group)
        order_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        order_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        order_layout.setHorizontalSpacing(15)
        order_layout.setVerticalSpacing(10)
        
        ref_edit = QLineEdit(self.supplier_order.bon_commande_ref or "N/A")
        ref_edit.setReadOnly(True)
        ref_edit.setMinimumHeight(35)
        ref_edit.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 8px; font-weight: bold; font-size: 12px;")
        order_layout.addRow("Référence BC:", ref_edit)
        
        if hasattr(self.supplier_order, 'reference') and self.supplier_order.reference:
            legacy_ref = QLineEdit(self.supplier_order.reference)
            legacy_ref.setReadOnly(True)
            legacy_ref.setMinimumHeight(35)
            legacy_ref.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 8px; font-size: 12px;")
            order_layout.addRow("Référence (legacy):", legacy_ref)
        
        # Status with color coding
        status_display = self._get_status_display()
        status_edit = QLineEdit(status_display)
        status_edit.setReadOnly(True)
        status_edit.setMinimumHeight(35)
        
        # Color-coded status styling
        status_colors = {
            'Initial': '#ffc107',
            'Commandé': '#007bff', 
            'En cours': '#fd7e14',
            'Reçu': '#28a745',
            'Annulé': '#dc3545'
        }
        status_color = status_colors.get(status_display, '#6c757d')
        status_edit.setStyleSheet(f"""
            background-color: {status_color};
            color: white;
            padding: 8px;
            border: none;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
        """)
        order_layout.addRow("Statut:", status_edit)
        
        date_edit = QLineEdit(self.supplier_order.order_date.strftime("%d/%m/%Y") if self.supplier_order.order_date else "N/A")
        date_edit.setReadOnly(True)
        date_edit.setMinimumHeight(35)
        date_edit.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 8px; font-size: 12px;")
        order_layout.addRow("Date de commande:", date_edit)
        
        currency_edit = QLineEdit(self.supplier_order.currency or "EUR")
        currency_edit.setReadOnly(True)
        currency_edit.setMinimumHeight(35)
        currency_edit.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 8px; font-size: 12px;")
        order_layout.addRow("Devise:", currency_edit)
        
        layout.addWidget(order_group)
        
        # Notes Group (always show, even if empty)
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout(notes_group)
        
        notes_text = self.supplier_order.notes or "Aucune note disponible"
        notes_edit = QTextEdit(notes_text)
        notes_edit.setReadOnly(True)
        notes_edit.setMaximumHeight(100)
        notes_edit.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        notes_layout.addWidget(notes_edit)
        
        layout.addWidget(notes_group)
        
        layout.addStretch()
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)  # Always show vertical scrollbar
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Ensure minimum size for content
        content_widget.setMinimumHeight(600)
        
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 14px;
                border-radius: 7px;
                border: 1px solid #dee2e6;
            }
            QScrollBar::handle:vertical {
                background-color: #6c757d;
                border-radius: 6px;
                min-height: 30px;
                margin: 1px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #495057;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #f8f9fa;
                height: 14px;
                border-radius: 7px;
                border: 1px solid #dee2e6;
            }
            QScrollBar::handle:horizontal {
                background-color: #6c757d;
                border-radius: 6px;
                min-width: 30px;
                margin: 1px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #495057;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
        
        return main_widget
    
    def _create_plaques_tab(self) -> QWidget:
        """Create plaques details tab with comprehensive table and scrolling"""
        # Main widget
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Content widget that will be scrollable
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Summary section
        summary_group = QGroupBox("Résumé des Plaques")
        summary_layout = QHBoxLayout(summary_group)
        
        total_plaques = len(self.supplier_order.line_items)
        total_quantity = sum(item.quantity for item in self.supplier_order.line_items)
        
        summary_layout.addWidget(QLabel(f"Nombre total de types de plaques: {total_plaques}"))
        summary_layout.addWidget(QLabel(f"Quantité totale: {total_quantity}"))
        summary_layout.addStretch()
        
        layout.addWidget(summary_group)
        
        # Plaques table
        plaques_group = QGroupBox("Détails des Plaques")
        plaques_layout = QVBoxLayout(plaques_group)
        
        table = QTableWidget()
        headers = [
            "Ligne", "Client", "Dimensions Caisse\n(L×l×H mm)", 
            "Dimensions Plaque\n(L×l×R mm)", "Réf. Matière", 
            "Caractéristiques", "Quantité", "Prix UTTC/Plaque", 
            "Total Ligne", "Notes"
        ]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(self.supplier_order.line_items))
        
        # Set minimum row height for better readability
        vertical_header = table.verticalHeader()
        if vertical_header:
            vertical_header.setDefaultSectionSize(35)
        
        # Populate table with better data handling
        for row, line_item in enumerate(self.supplier_order.line_items):
            # Line number
            table.setItem(row, 0, QTableWidgetItem(str(line_item.line_number)))
            
            # Client
            client_name = "N/A"
            if hasattr(line_item, 'client') and line_item.client:
                client_name = line_item.client.name
            table.setItem(row, 1, QTableWidgetItem(client_name))
            
            # Caisse dimensions - ensure all values are present
            caisse_l = getattr(line_item, 'caisse_length_mm', 0) or 0
            caisse_w = getattr(line_item, 'caisse_width_mm', 0) or 0  
            caisse_h = getattr(line_item, 'caisse_height_mm', 0) or 0
            caisse_dims = f"{caisse_l}×{caisse_w}×{caisse_h}"
            table.setItem(row, 2, QTableWidgetItem(caisse_dims))
            
            # Plaque dimensions - ensure all values are present
            plaque_l = getattr(line_item, 'plaque_length_mm', 0) or 0
            plaque_w = getattr(line_item, 'plaque_width_mm', 0) or 0
            plaque_f = getattr(line_item, 'plaque_flap_mm', 0) or 0
            plaque_dims = f"{plaque_l}×{plaque_w}×{plaque_f}"
            table.setItem(row, 3, QTableWidgetItem(plaque_dims))
            
            # Material reference
            mat_ref = getattr(line_item, 'material_reference', '') or 'N/A'
            table.setItem(row, 4, QTableWidgetItem(mat_ref))
            
            # Characteristics
            cardboard = getattr(line_item, 'cardboard_type', '') or 'N/A'
            table.setItem(row, 5, QTableWidgetItem(cardboard))
            
            # Quantity
            quantity = getattr(line_item, 'quantity', 0) or 0
            table.setItem(row, 6, QTableWidgetItem(str(quantity)))
            
            # Unit price
            unit_price = getattr(line_item, 'prix_uttc_plaque', 0) or 0
            unit_price_str = f"{float(unit_price):,.2f}"
            table.setItem(row, 7, QTableWidgetItem(unit_price_str))
            
            # Total line
            total_line = getattr(line_item, 'total_line_amount', 0) or 0
            total_line_str = f"{float(total_line):,.2f}"
            table.setItem(row, 8, QTableWidgetItem(total_line_str))
            
            # Notes
            notes = getattr(line_item, 'notes', '') or ''
            table.setItem(row, 9, QTableWidgetItem(notes))
        
        # Configure table
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSortingEnabled(True)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Enable horizontal scrolling for the table if needed
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Style the table
        table.setStyleSheet("""
            QTableWidget {
                gridline-color: #dee2e6;
                background-color: white;
                alternate-background-color: #f8f9fa;
                selection-background-color: #e3f2fd;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #dee2e6;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #495057;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                border-right: 1px solid #dee2e6;
                font-weight: bold;
            }
        """)
        
        # Auto-resize columns to fit content and set intelligent sizing
        table.resizeColumnsToContents()
        header = table.horizontalHeader()
        if header:
            # Set specific column widths for better display with minimum sizes
            column_configs = [
                (0, 60, QHeaderView.ResizeMode.Fixed),           # Ligne - fixed small
                (1, 150, QHeaderView.ResizeMode.Interactive),    # Client - expandable
                (2, 180, QHeaderView.ResizeMode.Interactive),    # Dimensions Caisse
                (3, 180, QHeaderView.ResizeMode.Interactive),    # Dimensions Plaque
                (4, 120, QHeaderView.ResizeMode.Interactive),    # Réf. Matière
                (5, 150, QHeaderView.ResizeMode.Stretch),        # Caractéristiques - stretch
                (6, 80, QHeaderView.ResizeMode.Fixed),           # Quantité - fixed small
                (7, 130, QHeaderView.ResizeMode.Interactive),    # Prix UTTC
                (8, 130, QHeaderView.ResizeMode.Interactive),    # Total Ligne
                (9, 200, QHeaderView.ResizeMode.Stretch)         # Notes - stretch
            ]
            
            for col_idx, min_width, resize_mode in column_configs:
                current_width = table.columnWidth(col_idx)
                table.setColumnWidth(col_idx, max(current_width, min_width))
                header.setSectionResizeMode(col_idx, resize_mode)
        
        plaques_layout.addWidget(table)
        layout.addWidget(plaques_group)
        
        # Create scroll area for plaques tab
        scroll_area = QScrollArea()
        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Ensure minimum size for content
        content_widget.setMinimumHeight(500)
        
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 14px;
                border-radius: 7px;
                border: 1px solid #dee2e6;
            }
            QScrollBar::handle:vertical {
                background-color: #6c757d;
                border-radius: 6px;
                min-height: 30px;
                margin: 1px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #495057;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #f8f9fa;
                height: 14px;
                border-radius: 7px;
                border: 1px solid #dee2e6;
            }
            QScrollBar::handle:horizontal {
                background-color: #6c757d;
                border-radius: 6px;
                min-width: 30px;
                margin: 1px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #495057;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
        
        return main_widget
    
    def _create_financial_tab(self) -> QWidget:
        """Create financial summary tab with scrolling"""
        # Main widget
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Content widget that will be scrollable
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Financial summary
        financial_group = QGroupBox("Résumé Financier")
        financial_layout = QFormLayout(financial_group)
        
        # Calculate totals
        subtotal = sum(float(item.total_line_amount) for item in self.supplier_order.line_items)
        total_quantity = sum(item.quantity for item in self.supplier_order.line_items)
        avg_price = subtotal / total_quantity if total_quantity > 0 else 0
        
        # Display financial information with better formatting and auto-sizing
        currency = self.supplier_order.currency or "EUR"
        
        # Create form layout with better spacing and sizing
        financial_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        financial_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        financial_layout.setHorizontalSpacing(15)
        financial_layout.setVerticalSpacing(10)
        
        subtotal_edit = QLineEdit(f"{subtotal:,.2f} {currency}")
        subtotal_edit.setReadOnly(True)
        subtotal_edit.setMinimumHeight(35)
        subtotal_edit.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 8px; font-size: 12px;")
        financial_layout.addRow("Sous-total:", subtotal_edit)
        
        total_amount = float(self.supplier_order.total_amount) if self.supplier_order.total_amount else subtotal
        total_edit = QLineEdit(f"{total_amount:,.2f} {currency}")
        total_edit.setReadOnly(True)
        total_edit.setMinimumHeight(40)
        total_edit.setStyleSheet("font-weight: bold; background-color: #e3f2fd; border: 2px solid #2196f3; padding: 10px; font-size: 14px;")
        financial_layout.addRow("Total TTC:", total_edit)
        
        avg_edit = QLineEdit(f"{avg_price:,.2f} {currency}")
        avg_edit.setReadOnly(True)
        avg_edit.setMinimumHeight(35)
        avg_edit.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 8px; font-size: 12px;")
        financial_layout.addRow("Prix moyen/plaque:", avg_edit)
        
        # Additional metrics
        total_plaques_edit = QLineEdit(str(total_quantity))
        total_plaques_edit.setReadOnly(True)
        total_plaques_edit.setMinimumHeight(35)
        total_plaques_edit.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 8px; font-size: 12px;")
        financial_layout.addRow("Nombre total de plaques:", total_plaques_edit)
        
        lines_count_edit = QLineEdit(str(len(self.supplier_order.line_items)))
        lines_count_edit.setReadOnly(True)
        lines_count_edit.setMinimumHeight(35)
        lines_count_edit.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 8px; font-size: 12px;")
        financial_layout.addRow("Nombre de lignes:", lines_count_edit)
        
        layout.addWidget(financial_group)
        
        # Per-line breakdown
        breakdown_group = QGroupBox("Répartition par Ligne")
        breakdown_layout = QVBoxLayout(breakdown_group)
        
        breakdown_table = QTableWidget()
        breakdown_table.setColumnCount(4)
        breakdown_table.setHorizontalHeaderLabels([
            "Ligne", "Quantité", "Prix Unitaire", "Total"
        ])
        breakdown_table.setRowCount(len(self.supplier_order.line_items))
        
        for row, line_item in enumerate(self.supplier_order.line_items):
            breakdown_table.setItem(row, 0, QTableWidgetItem(str(line_item.line_number)))
            breakdown_table.setItem(row, 1, QTableWidgetItem(str(line_item.quantity)))
            breakdown_table.setItem(row, 2, QTableWidgetItem(f"{float(line_item.prix_uttc_plaque):,.2f}"))
            breakdown_table.setItem(row, 3, QTableWidgetItem(f"{float(line_item.total_line_amount):,.2f}"))
        
        breakdown_table.setAlternatingRowColors(True)
        breakdown_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        breakdown_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        # Style the breakdown table
        breakdown_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #dee2e6;
                background-color: white;
                alternate-background-color: #f8f9fa;
                selection-background-color: #e3f2fd;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #dee2e6;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #495057;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                border-right: 1px solid #dee2e6;
                font-weight: bold;
            }
        """)
        
        # Auto-resize columns for breakdown table
        breakdown_table.resizeColumnsToContents()
        header = breakdown_table.horizontalHeader()
        if header:
            # Set minimum column widths
            breakdown_table.setColumnWidth(0, max(60, breakdown_table.columnWidth(0)))   # Ligne
            breakdown_table.setColumnWidth(1, max(100, breakdown_table.columnWidth(1)))  # Quantité
            breakdown_table.setColumnWidth(2, max(120, breakdown_table.columnWidth(2)))  # Prix Unitaire
            breakdown_table.setColumnWidth(3, max(120, breakdown_table.columnWidth(3)))  # Total
            
            # Set resize modes
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
            header.setStretchLastSection(True)
        breakdown_layout.addWidget(breakdown_table)
        
        layout.addWidget(breakdown_group)
        layout.addStretch()
        
        # Create scroll area for financial tab
        scroll_area = QScrollArea()
        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Ensure minimum size for content
        content_widget.setMinimumHeight(500)
        
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 14px;
                border-radius: 7px;
                border: 1px solid #dee2e6;
            }
            QScrollBar::handle:vertical {
                background-color: #6c757d;
                border-radius: 6px;
                min-height: 30px;
                margin: 1px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #495057;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #f8f9fa;
                height: 14px;
                border-radius: 7px;
                border: 1px solid #dee2e6;
            }
            QScrollBar::handle:horizontal {
                background-color: #6c757d;
                border-radius: 6px;
                min-width: 30px;
                margin: 1px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #495057;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
        
        return main_widget
    
    def _create_history_tab(self) -> QWidget:
        """Create history and tracking tab with scrolling"""
        # Main widget
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Content widget that will be scrollable
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Timeline information
        timeline_group = QGroupBox("Chronologie")
        timeline_layout = QFormLayout(timeline_group)
        
        created_edit = QLineEdit(self.supplier_order.created_at.strftime("%d/%m/%Y %H:%M:%S"))
        created_edit.setReadOnly(True)
        timeline_layout.addRow("Créé le:", created_edit)
        
        updated_edit = QLineEdit(self.supplier_order.updated_at.strftime("%d/%m/%Y %H:%M:%S"))
        updated_edit.setReadOnly(True)
        timeline_layout.addRow("Dernière modification:", updated_edit)
        
        layout.addWidget(timeline_group)
        
        # Status history (if available): show both Receptions and Material Deliveries
        from config.database import SessionLocal
        from models.orders import SupplierOrderLineItem, MaterialDelivery, Reception
        session = None
        try:
            session = SessionLocal()
            receptions = session.query(Reception).filter(Reception.supplier_order_id == self.supplier_order.id).all()
            deliveries = (
                session.query(MaterialDelivery)
                .join(SupplierOrderLineItem, MaterialDelivery.supplier_order_line_item_id == SupplierOrderLineItem.id)
                .filter(SupplierOrderLineItem.supplier_order_id == self.supplier_order.id)
                .all()
            )

            if receptions or deliveries:
                history_group = QGroupBox("Réceptions par Article")
                history_layout = QVBoxLayout(history_group)

                table = QTableWidget()
                # Columns: Type, Date, Quantité, Réf/Notes, Description, Client, Dim Plaque, Qté Restante
                headers = [
                    "Type", "Date", "Quantité", "Référence / Notes",
                    "Description", "Client", "Dimension de Plaque", "Qté Restante"
                ]
                table.setColumnCount(len(headers))
                table.setHorizontalHeaderLabels(headers)

                # Helper to compute remaining quantity per line item
                from models.orders import SupplierOrderStatus
                client_names_cache = {}
                def _client_name(client_id):
                    if not client_id:
                        return "N/A"
                    if client_id in client_names_cache:
                        return client_names_cache[client_id]
                    from models.clients import Client
                    c = session.query(Client).filter(Client.id == client_id).first()
                    name = c.name if c else "N/A"
                    client_names_cache[client_id] = name
                    return name

                # Build combined rows enhanced with line item context
                rows = []
                # Compute running remaining per line item (ordered - cumulative received up to that delivery)
                from collections import defaultdict
                from datetime import datetime

                # Prepare ordered quantities per line item for quick lookup
                ordered_qty_per_line = {}
                for li in session.query(SupplierOrderLineItem).filter(
                    SupplierOrderLineItem.supplier_order_id == self.supplier_order.id
                ).all():
                    try:
                        ordered_qty_per_line[li.id] = int(getattr(li, 'quantity', 0) or 0)
                    except Exception:
                        ordered_qty_per_line[li.id] = 0

                # Sort deliveries by date then id to have a stable chronological order
                def _delivery_sort_key(d):
                    dt = getattr(d, 'delivery_date', None)
                    # Use a very old date if missing to keep them first but stable
                    try:
                        sort_dt = dt or datetime.min
                    except Exception:
                        sort_dt = datetime.min
                    return (sort_dt, getattr(d, 'id', 0) or 0)

                deliveries_sorted = sorted(deliveries, key=_delivery_sort_key)

                running_received = defaultdict(int)  # line_item_id -> cumulative received so far

                # Receptions belong to supplier order, deliveries to line items; the running remaining is computed on deliveries
                for d in deliveries_sorted:
                    li = session.query(SupplierOrderLineItem).filter(
                        SupplierOrderLineItem.id == d.supplier_order_line_item_id
                    ).first()

                    desc = getattr(li, 'notes', None) or getattr(li, 'material_reference', None) or getattr(li, 'cardboard_type', None) or ""
                    client = _client_name(getattr(li, 'client_id', None) if li else None)
                    dims = "N/A"
                    if li:
                        try:
                            dims = f"{li.plaque_width_mm}×{li.plaque_length_mm}×{li.plaque_flap_mm}"
                        except Exception:
                            pass

                    qty_received = 0
                    try:
                        qty_received = int(getattr(d, 'received_quantity', 0) or 0)
                    except Exception:
                        qty_received = 0

                    ordered = ordered_qty_per_line.get(getattr(li, 'id', None), 0)
                    # Update running tally then compute remaining after this delivery
                    line_id = getattr(li, 'id', None)
                    if line_id is not None:
                        running_received[line_id] += qty_received
                        remaining = max(ordered - running_received[line_id], 0)
                    else:
                        remaining = "N/A"

                    rows.append((
                        "Livraison",
                        getattr(d, 'delivery_date', None),
                        qty_received,
                        d.batch_reference or "",
                        desc,
                        client,
                        dims,
                        remaining
                    ))

                # Do not add separate reception rows when deliveries are present to avoid duplicated entries.
                # If desired in the future, receptions can be shown only when no deliveries exist.

                # Sort by date ascending
                def _safe_date(x):
                    return x[1] or QDate.currentDate().toPyDate()
                rows.sort(key=_safe_date)

                table.setRowCount(len(rows))
                for i, (typ, dt, qty, ref, desc, client, dims, rem) in enumerate(rows):
                    table.setItem(i, 0, QTableWidgetItem(typ))
                    try:
                        if dt:
                            table.setItem(i, 1, QTableWidgetItem(dt.strftime("%d/%m/%Y")))
                        else:
                            table.setItem(i, 1, QTableWidgetItem("N/A"))
                    except Exception:
                        table.setItem(i, 1, QTableWidgetItem(str(dt) if dt else "N/A"))
                    table.setItem(i, 2, QTableWidgetItem(str(qty)))
                    table.setItem(i, 3, QTableWidgetItem(ref))
                    table.setItem(i, 4, QTableWidgetItem(desc))
                    table.setItem(i, 5, QTableWidgetItem(client))
                    table.setItem(i, 6, QTableWidgetItem(dims))
                    table.setItem(i, 7, QTableWidgetItem(str(rem)))

                # Wider columns for readability
                table.resizeColumnsToContents()
                try:
                    table.setColumnWidth(0, 90)
                    table.setColumnWidth(1, 120)
                    table.setColumnWidth(2, 90)
                    table.setColumnWidth(3, 160)
                    table.setColumnWidth(4, 220)
                    table.setColumnWidth(5, 180)
                    table.setColumnWidth(6, 160)
                    table.setColumnWidth(7, 120)
                except Exception:
                    pass

                history_layout.addWidget(table)
                layout.addWidget(history_group)
        except Exception as hist_err:
            # Non-fatal: keep UI working
            print(f"Warning: could not load receptions history: {hist_err}")
        finally:
            if session is not None:
                try:
                    session.close()
                except Exception:
                    pass
        
        # Full notes section
        if self.supplier_order.notes:
            notes_group = QGroupBox("Notes Complètes")
            notes_layout = QVBoxLayout(notes_group)
            
            notes_display = QTextEdit(self.supplier_order.notes)
            notes_display.setReadOnly(True)
            notes_layout.addWidget(notes_display)
            
            layout.addWidget(notes_group)
        
        layout.addStretch()
        
        # Create scroll area for history tab
        scroll_area = QScrollArea()
        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Ensure minimum size for content
        content_widget.setMinimumHeight(400)
        
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 14px;
                border-radius: 7px;
                border: 1px solid #dee2e6;
            }
            QScrollBar::handle:vertical {
                background-color: #6c757d;
                border-radius: 6px;
                min-height: 30px;
                margin: 1px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #495057;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #f8f9fa;
                height: 14px;
                border-radius: 7px;
                border: 1px solid #dee2e6;
            }
            QScrollBar::handle:horizontal {
                background-color: #6c757d;
                border-radius: 6px;
                min-width: 30px;
                margin: 1px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #495057;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
        
        return main_widget
    
    def _get_status_display(self) -> str:
        """Get human-readable status display"""
        status_map = {
            'commande_initial': 'Initial',
            'commande_passee': 'Commandé',
            'en_cours': 'En cours',
            'recu': 'Reçu',
            'annule': 'Annulé'
        }
        
        # Handle both enum and string status types
        if hasattr(self.supplier_order.status, 'value'):
            status_value = self.supplier_order.status.value
        else:
            status_value = str(self.supplier_order.status)
            
        return status_map.get(status_value, status_value)
    
    def _populate_data(self):
        """Populate dialog with supplier order data"""
        # Data population is handled in the tab creation methods
        pass
