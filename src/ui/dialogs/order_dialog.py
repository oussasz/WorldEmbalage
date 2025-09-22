from __future__ import annotations
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QLabel, QPushButton, QDateEdit
from PyQt6.QtCore import QDate


class OrderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Nouvelle Commande Client')
        
        # Auto-generate reference using unified system
        from utils.reference_generator import generate_client_order_reference
        self.ref_edit = QLineEdit()
        self.ref_edit.setText(generate_client_order_reference())
        self.ref_edit.setPlaceholderText('Ex: CM001')
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Référence'))
        layout.addWidget(self.ref_edit)
        layout.addWidget(QLabel('Date'))
        layout.addWidget(self.date_edit)
        btn = QPushButton('Créer')
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

    def get_data(self) -> dict:
        return {
            'reference': self.ref_edit.text().strip(),
            'date': self.date_edit.date().toPyDate(),
        }

__all__ = ['OrderDialog']
