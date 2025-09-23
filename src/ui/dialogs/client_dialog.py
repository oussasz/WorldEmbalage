from __future__ import annotations
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt
from ui.styles import IconManager


class ClientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Nouveau Client')
        self.setWindowIcon(IconManager.get_client_icon())
        self.setMinimumWidth(450)
        self.setModal(True)
        
        self.name_edit = QLineEdit()
        self.contact_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.city_edit = QLineEdit()
        self.activity_edit = QLineEdit()
        
        # Additional optional business registration fields
        self.numero_rc_edit = QLineEdit()
        self.nis_edit = QLineEdit()
        self.nif_edit = QLineEdit()
        self.ai_edit = QLineEdit()
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel('Informations Client')
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Form section
        form_frame = QFrame()
        form_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(15)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # Input fields with placeholders
        self.name_edit.setPlaceholderText("Ex: Emballages Distribution SARL")
        self.contact_edit.setPlaceholderText("Ex: Marie Martin")
        self.email_edit.setPlaceholderText("Ex: marie@emballages-distrib.fr")
        self.phone_edit.setPlaceholderText("Ex: +213 21 XX XX XX")
        self.address_edit.setPlaceholderText("Ex: 123 Rue des Industries")
        self.city_edit.setPlaceholderText("Ex: Alger")
        self.activity_edit.setPlaceholderText("Ex: Agroalimentaire (optionnel)")
        
        # Additional optional fields placeholders
        self.numero_rc_edit.setPlaceholderText("Ex: 16/00-123456B15 (optionnel)")
        self.nis_edit.setPlaceholderText("Ex: 0001234567890123 (optionnel)")
        self.nif_edit.setPlaceholderText("Ex: 000123456789012 (optionnel)")
        self.ai_edit.setPlaceholderText("Ex: 16123456789 (optionnel)")
        
        form_layout.addRow('Nom de l\'entreprise:', self.name_edit)
        form_layout.addRow('Personne de contact:', self.contact_edit)
        form_layout.addRow('Email:', self.email_edit)
        form_layout.addRow('Téléphone:', self.phone_edit)
        form_layout.addRow('Adresse:', self.address_edit)
        form_layout.addRow('Ville:', self.city_edit)
        form_layout.addRow("Activité:", self.activity_edit)
        
        # Add separator for business registration section
        separator_label = QLabel()
        separator_label.setStyleSheet("border-top: 1px solid #ccc; margin: 10px 0;")
        form_layout.addRow(separator_label)
        
        business_label = QLabel("Informations commerciales (optionnel)")
        business_label.setStyleSheet("font-weight: bold; color: #666; margin-top: 10px;")
        form_layout.addRow(business_label)
        
        form_layout.addRow('N° RC:', self.numero_rc_edit)
        form_layout.addRow('NIS:', self.nis_edit)
        form_layout.addRow('NIF:', self.nif_edit)
        form_layout.addRow('AI:', self.ai_edit)
        
        layout.addWidget(form_frame)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton('Annuler')
        self.cancel_btn.setProperty("class", "secondary")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton('Enregistrer')
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)

    def get_data(self) -> dict:
        return {
            'name': self.name_edit.text().strip(),
            'contact_name': self.contact_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'phone': self.phone_edit.text().strip(),
            'address': self.address_edit.text().strip(),
            'city': self.city_edit.text().strip(),
            'activity': self.activity_edit.text().strip() or None,
            # Additional optional business registration fields
            'numero_rc': self.numero_rc_edit.text().strip() or None,
            'nis': self.nis_edit.text().strip() or None,
            'nif': self.nif_edit.text().strip() or None,
            'ai': self.ai_edit.text().strip() or None,
        }

__all__ = ['ClientDialog']
