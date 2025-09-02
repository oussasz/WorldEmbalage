"""
Dialog for selecting delivery options for finished product fiches.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QRadioButton, QButtonGroup, QSpinBox, QPushButton,
                            QWidget, QFrame)
from PyQt6.QtCore import Qt


class PalletDeliveryDialog(QDialog):
    """Dialog for choosing delivery method: on pallets or all at once"""
    
    def __init__(self, total_quantity: int, parent=None):
        super().__init__(parent)
        self.total_quantity = total_quantity
        self.delivery_method = None
        self.units_per_pallet = 100  # Default value
        
        self.setWindowTitle("Options de livraison")
        self.setFixedSize(400, 200)
        self.setModal(True)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(f"Quantité totale: {self.total_quantity} caisses")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Radio button group
        self.button_group = QButtonGroup(self)
        
        # Option 1: On pallets
        self.pallets_radio = QRadioButton("Livrer par palettes")
        self.pallets_radio.setChecked(True)  # Default selection
        self.button_group.addButton(self.pallets_radio)
        layout.addWidget(self.pallets_radio)
        
        # Pallet size input
        pallet_widget = QWidget()
        pallet_layout = QHBoxLayout(pallet_widget)
        pallet_layout.setContentsMargins(20, 0, 0, 0)  # Indent
        
        pallet_label = QLabel("Unités par palette:")
        self.pallet_spinbox = QSpinBox()
        self.pallet_spinbox.setRange(1, self.total_quantity)
        self.pallet_spinbox.setValue(100)  # Default value
        self.pallet_spinbox.setSuffix(" caisses")
        
        pallet_layout.addWidget(pallet_label)
        pallet_layout.addWidget(self.pallet_spinbox)
        pallet_layout.addStretch()
        
        layout.addWidget(pallet_widget)
        
        # Option 2: All at once
        self.all_at_once_radio = QRadioButton("Livrer tout d'un coup")
        self.button_group.addButton(self.all_at_once_radio)
        layout.addWidget(self.all_at_once_radio)
        
        # Enable/disable pallet spinbox based on selection
        self.pallets_radio.toggled.connect(self._on_delivery_method_changed)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
        # Set default state
        self._on_delivery_method_changed()
        
    def _on_delivery_method_changed(self):
        """Enable/disable pallet size input based on selected delivery method"""
        self.pallet_spinbox.setEnabled(self.pallets_radio.isChecked())
        
    def get_delivery_options(self):
        """Return the selected delivery options"""
        if self.pallets_radio.isChecked():
            return {
                'method': 'pallets',
                'units_per_pallet': self.pallet_spinbox.value()
            }
        else:
            return {
                'method': 'all_at_once',
                'units_per_pallet': None
            }
    
    def calculate_pallets(self):
        """Calculate pallet distribution for the given quantity"""
        if not self.pallets_radio.isChecked():
            return [(self.total_quantity, 1)]  # Single fiche for all quantity
            
        units_per_pallet = self.pallet_spinbox.value()
        full_pallets = self.total_quantity // units_per_pallet
        remaining_units = self.total_quantity % units_per_pallet
        
        pallets = []
        
        # Add full pallets
        if full_pallets > 0:
            pallets.append((units_per_pallet, full_pallets))
            
        # Add partial pallet if there are remaining units
        if remaining_units > 0:
            pallets.append((remaining_units, 1))
            
        return pallets
