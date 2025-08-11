from __future__ import annotations
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPushButton, QComboBox, QSpinBox, QTextEdit, QDateEdit
from PyQt6.QtCore import QDate


class ReceptionDialog(QDialog):
    def __init__(self, supplier_order, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'Réception - Commande {supplier_order.reference}')
        self.setMinimumWidth(500)
        self.supplier_order = supplier_order
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Order info (read-only)
        layout.addWidget(QLabel(f'Commande: {self.supplier_order.reference}'))
        layout.addWidget(QLabel(f'Fournisseur: {self.supplier_order.supplier.name}'))
        
        # Reception Date
        layout.addWidget(QLabel('Date de réception:'))
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        layout.addWidget(self.date_edit)
        
        # Quantity received
        layout.addWidget(QLabel('Quantité reçue:'))
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 100000)
        # TODO: Calculate remaining quantity to receive
        self.quantity_spin.setValue(100)
        layout.addWidget(self.quantity_spin)
        
        # Storage location
        layout.addWidget(QLabel('Emplacement de stockage:'))
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText('Ex: Zone A - Rack 1')
        layout.addWidget(self.location_edit)
        
        # Notes
        layout.addWidget(QLabel('Notes:'))
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        layout.addWidget(self.notes_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton('Enregistrer Réception')
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton('Annuler')
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def get_data(self) -> dict:
        return {
            'supplier_order_id': self.supplier_order.id,
            'reception_date': self.date_edit.date().toPyDate(),
            'quantity': self.quantity_spin.value(),
            'storage_location': self.location_edit.text().strip(),
            'notes': self.notes_edit.toPlainText().strip()
        }

__all__ = ['ReceptionDialog']
