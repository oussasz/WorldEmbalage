"""
Dialog for collecting optional remark when printing raw material labels.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QTextEdit, QPushButton, QFrame)
from PyQt6.QtCore import Qt


class RawMaterialLabelDialog(QDialog):
    """Dialog for collecting optional remark for raw material label printing"""
    
    def __init__(self, material_info: dict, parent=None):
        super().__init__(parent)
        self.material_info = material_info
        self.remark = ""
        
        self.setWindowTitle("Imprimer l'étiquette matière première")
        self.setFixedSize(500, 350)
        self.setModal(True)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Title and material info
        title_label = QLabel("Impression de l'étiquette matière première")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Material information display
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.Shape.Box)
        info_frame.setStyleSheet("background-color: #f5f5f5; padding: 10px; margin: 5px;")
        info_layout = QVBoxLayout(info_frame)
        
        # Display key material information
        client_label = QLabel(f"Client: {self.material_info.get('client', 'N/A')}")
        quantity_label = QLabel(f"Quantité en stock: {self.material_info.get('quantity', 'N/A')}")
        dimensions_label = QLabel(f"Dimensions: {self.material_info.get('plaque_dimensions', 'N/A')}")
        
        info_layout.addWidget(client_label)
        info_layout.addWidget(quantity_label)
        info_layout.addWidget(dimensions_label)
        
        layout.addWidget(info_frame)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Remark input
        remark_label = QLabel("Remarque (optionnel):")
        remark_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(remark_label)
        
        self.remark_text = QTextEdit()
        self.remark_text.setPlaceholderText("Saisissez une remarque optionnelle pour l'étiquette...")
        self.remark_text.setMaximumHeight(80)
        layout.addWidget(self.remark_text)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.print_button = QPushButton("🖨️ Imprimer l'étiquette")
        self.print_button.clicked.connect(self.accept)
        self.print_button.setStyleSheet("font-weight: bold; padding: 8px;")
        
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.print_button)
        
        layout.addLayout(button_layout)
        
    def get_remark(self):
        """Return the entered remark"""
        return self.remark_text.toPlainText().strip()
