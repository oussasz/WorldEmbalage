"""
Quotation Detail Dialog - Display detailed information about a quotation
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QGroupBox, QFormLayout, QTextEdit, QFrame)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
from models.orders import Quotation
from ui.styles import IconManager
from decimal import Decimal
from datetime import date, datetime


class QuotationDetailDialog(QDialog):
    """Dialog to display detailed quotation information"""
    
    def __init__(self, quotation: Quotation, parent=None):
        super().__init__(parent)
        self.quotation = quotation
        self.setWindowTitle(f'Détails du Devis - {quotation.reference}')
        self.setWindowIcon(IconManager.get_quotation_icon())
        self.setMinimumSize(900, 600)
        self.setModal(True)
        self._build_ui()
    
    def _build_ui(self):
        """Build the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header with quotation reference and status
        self._create_header(layout)
        
        # Basic information section
        self._create_basic_info_section(layout)
        
        # Line items section
        self._create_line_items_section(layout)
        
        # Summary section
        self._create_summary_section(layout)
        
        # Notes section
        self._create_notes_section(layout)
        
        # Buttons
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
        
        # Quotation reference
        ref_label = QLabel(f"Devis: {self.quotation.reference}")
        ref_font = QFont()
        ref_font.setPointSize(18)
        ref_font.setBold(True)
        ref_label.setFont(ref_font)
        ref_label.setStyleSheet("color: #2c3e50;")
        
        # Status badge
        status = "Devis Initial" if self.quotation.is_initial else "Devis Final"
        status_label = QLabel(status)
        status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {'#e3f2fd' if self.quotation.is_initial else '#e8f5e8'};
                color: {'#1976d2' if self.quotation.is_initial else '#388e3c'};
                border: 1px solid {'#bbdefb' if self.quotation.is_initial else '#c8e6c9'};
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
        
        # Client
        client_label = QLabel(self.quotation.client.name if self.quotation.client else "N/A")
        client_label.setStyleSheet("font-weight: normal; color: #495057;")
        info_layout.addRow("Client:", client_label)
        
        # Dates
        issue_date = "N/A"
        if self.quotation.issue_date:
            try:
                # Convert date to datetime if needed, then format
                if isinstance(self.quotation.issue_date, date):
                    issue_date = datetime.combine(self.quotation.issue_date, datetime.min.time()).strftime("%d/%m/%Y")
                else:
                    issue_date = str(self.quotation.issue_date)
            except (AttributeError, TypeError, ValueError):
                issue_date = str(self.quotation.issue_date)
        issue_label = QLabel(issue_date)
        issue_label.setStyleSheet("font-weight: normal; color: #495057;")
        info_layout.addRow("Date d'émission:", issue_label)
        
        valid_until = "N/A"
        if self.quotation.valid_until:
            try:
                # Convert date to datetime if needed, then format
                if isinstance(self.quotation.valid_until, date):
                    valid_until = datetime.combine(self.quotation.valid_until, datetime.min.time()).strftime("%d/%m/%Y")
                else:
                    valid_until = str(self.quotation.valid_until)
            except (AttributeError, TypeError, ValueError):
                valid_until = str(self.quotation.valid_until)
        valid_label = QLabel(valid_until)
        valid_label.setStyleSheet("font-weight: normal; color: #495057;")
        info_layout.addRow("Valable jusqu'au:", valid_label)
        
        # Total amount
        total_amount = f"{self.quotation.total_amount:,.2f} DA" if self.quotation.total_amount else "0.00 DA"
        total_label = QLabel(total_amount)
        total_label.setStyleSheet("font-weight: bold; color: #28a745; font-size: 14px;")
        info_layout.addRow("Montant total:", total_label)
        
        layout.addWidget(info_group)
    
    def _create_line_items_section(self, layout):
        """Create the line items section"""
        items_group = QGroupBox("Articles du Devis")
        items_group.setStyleSheet("QGroupBox { font-weight: bold; color: #2c3e50; }")
        items_layout = QVBoxLayout(items_group)
        
        # Create table for line items
        self.items_table = QTableWidget()
        headers = ["N°", "Description", "Quantité", "Prix Unit.", "Prix Total", 
                  "Dimensions (L×l×H)", "Couleur", "Type Carton", "Cliché"]
        self.items_table.setColumnCount(len(headers))
        self.items_table.setHorizontalHeaderLabels(headers)
        
        # Style the table
        self.items_table.setStyleSheet("""
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
        
        # Populate table with line items
        if self.quotation.line_items:
            self.items_table.setRowCount(len(self.quotation.line_items))
            
            for row, item in enumerate(self.quotation.line_items):
                # Line number
                self.items_table.setItem(row, 0, QTableWidgetItem(str(item.line_number)))
                
                # Description
                description = item.description or ""
                if len(description) > 50:
                    description = description[:47] + "..."
                self.items_table.setItem(row, 1, QTableWidgetItem(description))
                
                # Quantity
                self.items_table.setItem(row, 2, QTableWidgetItem(str(item.quantity)))
                
                # Unit price
                unit_price = f"{item.unit_price:,.2f} DA" if item.unit_price else "0.00 DA"
                self.items_table.setItem(row, 3, QTableWidgetItem(unit_price))
                
                # Total price
                total_price = f"{item.total_price:,.2f} DA" if item.total_price else "0.00 DA"
                self.items_table.setItem(row, 4, QTableWidgetItem(total_price))
                
                # Dimensions
                dimensions = ""
                if item.length_mm and item.width_mm and item.height_mm:
                    dimensions = f"{item.length_mm}×{item.width_mm}×{item.height_mm} mm"
                self.items_table.setItem(row, 5, QTableWidgetItem(dimensions))
                
                # Color
                color_text = ""
                if item.color:
                    color_text = item.color.value if hasattr(item.color, 'value') else str(item.color)
                self.items_table.setItem(row, 6, QTableWidgetItem(color_text))
                
                # Cardboard type
                self.items_table.setItem(row, 7, QTableWidgetItem(item.cardboard_type or ""))
                
                # Cliché
                cliche = "Oui" if item.is_cliche else "Non"
                self.items_table.setItem(row, 8, QTableWidgetItem(cliche))
        
        # Resize columns to content
        self.items_table.resizeColumnsToContents()
        
        # Set minimum column widths
        self.items_table.setColumnWidth(0, 50)   # Line number
        self.items_table.setColumnWidth(1, 200)  # Description
        self.items_table.setColumnWidth(2, 100)  # Quantity
        self.items_table.setColumnWidth(3, 100)  # Unit price
        self.items_table.setColumnWidth(4, 100)  # Total price
        
        items_layout.addWidget(self.items_table)
        layout.addWidget(items_group)
    
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
        
        item_count = len(self.quotation.line_items) if self.quotation.line_items else 0
        stats_layout.addWidget(QLabel(f"Nombre d'articles: {item_count}"))
        
        # Calculate total quantity
        total_qty = 0
        if self.quotation.line_items:
            for item in self.quotation.line_items:
                # Extract numeric quantity
                import re
                qty_text = str(item.quantity)
                numbers = re.findall(r'\d+', qty_text)
                numeric_quantity = int(numbers[-1]) if numbers else 0
                total_qty += numeric_quantity
        
        stats_layout.addWidget(QLabel(f"Quantité totale: {total_qty}"))
        
        summary_layout.addLayout(stats_layout)
        summary_layout.addStretch()
        
        # Total amount (large)
        total_layout = QVBoxLayout()
        total_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        total_label = QLabel("TOTAL:")
        total_label.setStyleSheet("font-size: 14px; color: #6c757d;")
        total_layout.addWidget(total_label)
        
        amount_label = QLabel(f"{self.quotation.total_amount:,.2f} DA" if self.quotation.total_amount else "0.00 DA")
        amount_font = QFont()
        amount_font.setPointSize(20)
        amount_font.setBold(True)
        amount_label.setFont(amount_font)
        amount_label.setStyleSheet("color: #28a745;")
        total_layout.addWidget(amount_label)
        
        summary_layout.addLayout(total_layout)
        layout.addWidget(summary_frame)
    
    def _create_notes_section(self, layout):
        """Create the notes section"""
        if self.quotation.notes:
            notes_group = QGroupBox("Notes")
            notes_group.setStyleSheet("QGroupBox { font-weight: bold; color: #2c3e50; }")
            notes_layout = QVBoxLayout(notes_group)
            
            notes_text = QTextEdit()
            notes_text.setPlainText(self.quotation.notes)
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

__all__ = ['QuotationDetailDialog']
