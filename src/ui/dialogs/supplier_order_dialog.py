from __future__ import annotations
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPushButton, QComboBox, QSpinBox, QTextEdit, QDateEdit
from PyQt6.QtCore import QDate
from typing import Optional


class SupplierOrderDialog(QDialog):
    def __init__(self, suppliers: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Nouveau Bon de Commande Fournisseur')
        self.setMinimumWidth(500)
        self.suppliers = suppliers
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Reference - Auto-generated using unified reference system
        layout.addWidget(QLabel('Référence:'))
        from utils.reference_generator import generate_supplier_order_reference
        self.ref_edit = QLineEdit()
        self.ref_edit.setText(generate_supplier_order_reference())  # Auto-generate with standardized format
        self.ref_edit.setPlaceholderText('Ex: BC001')
        layout.addWidget(self.ref_edit)
        
        # Supplier
        layout.addWidget(QLabel('Fournisseur:'))
        self.supplier_combo = QComboBox()
        for supplier in self.suppliers:
            self.supplier_combo.addItem(supplier.name, supplier.id)
        layout.addWidget(self.supplier_combo)
        
        # Order Date
        layout.addWidget(QLabel('Date de commande:'))
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        layout.addWidget(self.date_edit)
        
        # Material details
        layout.addWidget(QLabel('Type de matériau:'))
        self.material_edit = QLineEdit()
        layout.addWidget(self.material_edit)
        
        # Dimensions
        dim_layout = QHBoxLayout()
        dim_layout.addWidget(QLabel('Longueur (mm):'))
        self.length_spin = QSpinBox()
        self.length_spin.setRange(1, 10000)
        self.length_spin.setValue(1000)
        dim_layout.addWidget(self.length_spin)
        
        dim_layout.addWidget(QLabel('Largeur (mm):'))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 10000)
        self.width_spin.setValue(700)
        dim_layout.addWidget(self.width_spin)
        
        dim_layout.addWidget(QLabel('Rabat (mm):'))
        self.rabat_spin = QSpinBox()
        self.rabat_spin.setRange(1, 1000)
        self.rabat_spin.setValue(100)
        dim_layout.addWidget(self.rabat_spin)
        
        layout.addLayout(dim_layout)
        
        # Quantity
        layout.addWidget(QLabel('Quantité:'))
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 100000)
        self.quantity_spin.setValue(100)
        layout.addWidget(self.quantity_spin)
        
        # Notes
        layout.addWidget(QLabel('Notes:'))
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        layout.addWidget(self.notes_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton('Créer Commande')
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton('Annuler')
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def get_data(self) -> dict:
        return {
            'reference': self.ref_edit.text().strip(),
            'supplier_id': self.supplier_combo.currentData(),
            'order_date': self.date_edit.date().toPyDate(),
            'material_type': self.material_edit.text().strip(),
            'length_mm': self.length_spin.value(),
            'width_mm': self.width_spin.value(),
            'rabat_mm': self.rabat_spin.value(),
            'quantity': self.quantity_spin.value(),
            'notes': self.notes_edit.toPlainText().strip()
        }

__all__ = ['SupplierOrderDialog']
