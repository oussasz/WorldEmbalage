from __future__ import annotations
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPushButton, QComboBox, QSpinBox, QTextEdit


class ProductionDialog(QDialog):
    def __init__(self, client_orders: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Nouveau Lot de Production')
        self.setMinimumWidth(500)
        self.client_orders = client_orders
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Batch Code
        layout.addWidget(QLabel('Code du lot:'))
        self.batch_code_edit = QLineEdit()
        self.batch_code_edit.setPlaceholderText('Ex: LOT-2025-001')
        layout.addWidget(self.batch_code_edit)
        
        # Client Order
        layout.addWidget(QLabel('Commande client:'))
        self.order_combo = QComboBox()
        for order in self.client_orders:
            self.order_combo.addItem(f'{order.reference} - {order.client.name}', order.id)
        layout.addWidget(self.order_combo)
        
        # Production Quantity
        layout.addWidget(QLabel('Quantité à produire:'))
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
        self.ok_btn = QPushButton('Créer Lot')
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton('Annuler')
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def get_data(self) -> dict:
        return {
            'batch_code': self.batch_code_edit.text().strip(),
            'client_order_id': self.order_combo.currentData(),
            'quantity': self.quantity_spin.value(),
            'notes': self.notes_edit.toPlainText().strip()
        }

__all__ = ['ProductionDialog']
