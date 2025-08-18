from __future__ import annotations
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QLabel, QPushButton, QFrame, QTextEdit
from PyQt6.QtCore import Qt
from ui.styles import IconManager
from models.clients import Client


class ClientDetailDialog(QDialog):
    def __init__(self, client: Client, parent=None, read_only: bool = False):
        super().__init__(parent)
        self.client = client
        self.read_only = read_only
        self.setWindowTitle(f'Client - {client.name}' if read_only else f'Modifier Client - {client.name}')
        self.setWindowIcon(IconManager.get_client_icon())
        self.setMinimumWidth(500)
        self.setModal(True)
        
        # Form fields
        self.name_edit = QLineEdit()
        self.contact_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.city_edit = QLineEdit()
        
        self._populate_fields()
        self._build()

    def _populate_fields(self):
        """Populate form fields with client data"""
        self.name_edit.setText(self.client.name or '')
        self.contact_edit.setText(self.client.contact_name or '')
        self.email_edit.setText(self.client.email or '')
        self.phone_edit.setText(self.client.phone or '')
        self.address_edit.setText(self.client.address or '')
        self.city_edit.setText(self.client.city or '')
        
        if self.read_only:
            for field in [self.name_edit, self.contact_edit, self.email_edit, 
                         self.phone_edit, self.address_edit, self.city_edit]:
                field.setReadOnly(True)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_text = 'Informations Client' if self.read_only else 'Modifier Client'
        header = QLabel(header_text)
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Client ID and timestamps (read-only section)
        if self.read_only:
            info_frame = QFrame()
            info_frame.setFrameStyle(QFrame.Shape.StyledPanel)
            info_layout = QFormLayout(info_frame)
            info_layout.setSpacing(10)
            
            id_label = QLabel(str(self.client.id))
            id_label.setStyleSheet("font-weight: bold; color: #007bff;")
            info_layout.addRow('ID:', id_label)
            
            if hasattr(self.client, 'created_at') and self.client.created_at:
                created_label = QLabel(str(self.client.created_at).split('.')[0])
                info_layout.addRow('Créé le:', created_label)
            
            if hasattr(self.client, 'updated_at') and self.client.updated_at:
                updated_label = QLabel(str(self.client.updated_at).split('.')[0])
                info_layout.addRow('Modifié le:', updated_label)
            
            layout.addWidget(info_frame)
        
        # Form section
        form_frame = QFrame()
        form_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(15)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # Input fields with placeholders
        if not self.read_only:
            self.name_edit.setPlaceholderText("Ex: Emballages Distribution SARL")
            self.contact_edit.setPlaceholderText("Ex: Marie Martin")
            self.email_edit.setPlaceholderText("Ex: marie@emballages-distrib.fr")
            self.phone_edit.setPlaceholderText("Ex: +213 21 XX XX XX")
            self.address_edit.setPlaceholderText("Ex: 123 Rue des Industries")
            self.city_edit.setPlaceholderText("Ex: Alger")
        
        form_layout.addRow('Nom de l\'entreprise:', self.name_edit)
        form_layout.addRow('Personne de contact:', self.contact_edit)
        form_layout.addRow('Email:', self.email_edit)
        form_layout.addRow('Téléphone:', self.phone_edit)
        form_layout.addRow('Adresse:', self.address_edit)
        form_layout.addRow('Ville:', self.city_edit)
        
        layout.addWidget(form_frame)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        if self.read_only:
            close_btn = QPushButton('Fermer')
            close_btn.clicked.connect(self.accept)
            btn_layout.addWidget(close_btn)
        else:
            cancel_btn = QPushButton('Annuler')
            cancel_btn.setProperty("class", "secondary")
            cancel_btn.clicked.connect(self.reject)
            btn_layout.addWidget(cancel_btn)
            
            save_btn = QPushButton('Enregistrer')
            save_btn.setDefault(True)
            save_btn.clicked.connect(self.accept)
            btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)

    def get_data(self) -> dict:
        """Get form data for updating the client"""
        return {
            'name': self.name_edit.text().strip(),
            'contact_name': self.contact_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'phone': self.phone_edit.text().strip(),
            'address': self.address_edit.text().strip(),
            'city': self.city_edit.text().strip(),
        }

__all__ = ['ClientDetailDialog']
