"""
Dialog for viewing and editing production batch details
"""
from __future__ import annotations
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QLineEdit, QLabel, QPushButton, QDateEdit, QGroupBox, QMessageBox, QSpinBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from models.production import ProductionBatch
from models.orders import ClientOrder
from typing import Dict, Any, Optional


class ProductionDetailsDialog(QDialog):
    """Dialog for viewing and editing production batch details"""
    
    def __init__(self, production_batch: ProductionBatch, editable: bool = False, parent=None):
        super().__init__(parent)
        self.production_batch = production_batch
        self.editable = editable
        self.setWindowTitle('Détails de Production' if not editable else 'Modifier Production')
        self.setMinimumSize(600, 400)
        self._setup_ui()
        self._load_data()
        
    def _setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel('Détails du Lot de Production' if not self.editable else 'Modifier le Lot de Production')
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # General Information Group
        general_group = QGroupBox("Informations Générales")
        general_layout = QFormLayout(general_group)
        
        # Batch Code
        self.batch_code_edit = QLineEdit()
        self.batch_code_edit.setReadOnly(not self.editable)
        general_layout.addRow("Code du lot:", self.batch_code_edit)
        
        # Client Order Reference
        self.client_order_label = QLabel()
        general_layout.addRow("Commande client:", self.client_order_label)
        
        # Client Information
        self.client_info_label = QLabel()
        general_layout.addRow("Client:", self.client_info_label)
        
        layout.addWidget(general_group)
        
        # Raw Material Information Group
        material_group = QGroupBox("Informations de la Matière Première")
        material_layout = QFormLayout(material_group)
        
        self.material_client_label = QLabel()
        material_layout.addRow("Client de la matière:", self.material_client_label)
        
        self.plaque_dimensions_label = QLabel()
        material_layout.addRow("Dimensions plaque:", self.plaque_dimensions_label)
        
        self.caisse_dimensions_label = QLabel()
        material_layout.addRow("Dimensions caisse:", self.caisse_dimensions_label)
        
        self.material_type_label = QLabel()
        material_layout.addRow("Type de carton:", self.material_type_label)
        
        self.supplier_order_ref_label = QLabel()
        material_layout.addRow("Référence commande fournisseur:", self.supplier_order_ref_label)
        
        layout.addWidget(material_group)
        
        # Production Details
        production_group = QGroupBox("Détails de Production")
        production_layout = QFormLayout(production_group)
        
        # Quantity
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(0, 999999)
        self.quantity_spin.setReadOnly(not self.editable)
        production_layout.addRow("Quantité:", self.quantity_spin)
        
        # Production Date
        self.production_date_edit = QDateEdit()
        self.production_date_edit.setCalendarPopup(True)
        self.production_date_edit.setEnabled(self.editable)
        production_layout.addRow("Date de production:", self.production_date_edit)
        
        layout.addWidget(production_group)
        
        # Timestamps Group (read-only)
        timestamps_group = QGroupBox("Informations Système")
        timestamps_layout = QFormLayout(timestamps_group)
        
        self.created_at_label = QLabel()
        timestamps_layout.addRow("Créé le:", self.created_at_label)
        
        self.updated_at_label = QLabel()
        timestamps_layout.addRow("Modifié le:", self.updated_at_label)
        
        layout.addWidget(timestamps_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        if self.editable:
            save_btn = QPushButton("💾 Enregistrer")
            save_btn.clicked.connect(self.accept)
            buttons_layout.addWidget(save_btn)
            
            cancel_btn = QPushButton("❌ Annuler")
            cancel_btn.clicked.connect(self.reject)
            buttons_layout.addWidget(cancel_btn)
        else:
            close_btn = QPushButton("✅ Fermer")
            close_btn.clicked.connect(self.accept)
            buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        
    def _load_data(self):
        """Load production batch data into the form"""
        if not self.production_batch:
            return
            
        # Basic information
        self.batch_code_edit.setText(self.production_batch.batch_code or "")
        
        # Client order information and material data loading
        if hasattr(self.production_batch, 'client_order_id') and self.production_batch.client_order_id:
            # We'll need to query the client order since it's not directly available
            from config.database import SessionLocal
            session = SessionLocal()
            try:
                from models.orders import ClientOrder, SupplierOrder, SupplierOrderLineItem, Reception
                client_order = session.query(ClientOrder).filter(
                    ClientOrder.id == self.production_batch.client_order_id
                ).first()
                
                if client_order:
                    self.client_order_label.setText(client_order.reference or "N/A")
                    
                    if hasattr(client_order, 'client') and client_order.client:
                        client = client_order.client
                        client_info = f"{client.name or 'N/A'}"
                        if hasattr(client, 'phone') and client.phone:
                            client_info += f" - {client.phone}"
                        self.client_info_label.setText(client_info)
                    else:
                        self.client_info_label.setText("Client non disponible")
                        
                    # Get raw material information from supplier orders linked to this client order
                    if client_order.supplier_order_id:
                        supplier_order = session.query(SupplierOrder).filter(
                            SupplierOrder.id == client_order.supplier_order_id
                        ).first()
                        
                        if supplier_order and supplier_order.line_items:
                            line_item = supplier_order.line_items[0]  # Use first line item
                            
                            # Material client info (from line item)
                            if line_item.client:
                                self.material_client_label.setText(line_item.client.name or "N/A")
                            else:
                                self.material_client_label.setText("N/A")
                            
                            # Plaque dimensions
                            plaque_dims = f"{line_item.plaque_width_mm} × {line_item.plaque_length_mm} × {line_item.plaque_flap_mm} mm"
                            self.plaque_dimensions_label.setText(plaque_dims)
                            
                            # Caisse dimensions
                            caisse_dims = f"{line_item.caisse_length_mm} × {line_item.caisse_width_mm} × {line_item.caisse_height_mm} mm"
                            self.caisse_dimensions_label.setText(caisse_dims)
                            
                            # Material type
                            self.material_type_label.setText(line_item.cardboard_type or "Standard")
                            
                            # Supplier order reference
                            self.supplier_order_ref_label.setText(supplier_order.bon_commande_ref or "N/A")
                        else:
                            # No supplier order found, set defaults
                            self._set_material_info_na()
                    else:
                        # No supplier order ID in client order
                        self._set_material_info_na()
                else:
                    # Client order not found
                    self.client_order_label.setText("N/A")
                    self.client_info_label.setText("N/A")
                    self._set_material_info_na()
            except Exception as e:
                print(f"Error loading client order data: {e}")
                self.client_order_label.setText("Erreur de chargement")
                self.client_info_label.setText("Erreur de chargement")
                self._set_material_info_na()
            finally:
                session.close()
        else:
            self.client_order_label.setText("N/A")
            self.client_info_label.setText("N/A")
            self._set_material_info_na()
            
        # Production details
        self.quantity_spin.setValue(getattr(self.production_batch, 'quantity', 0) or 0)
        
        # Production date
        if hasattr(self.production_batch, 'production_date') and self.production_batch.production_date:
            self.production_date_edit.setDate(QDate.fromString(
                self.production_batch.production_date.strftime('%Y-%m-%d'), 'yyyy-MM-dd'
            ))
        else:
            self.production_date_edit.setDate(QDate.currentDate())
        
        # System timestamps
        if hasattr(self.production_batch, 'created_at') and self.production_batch.created_at:
            try:
                # Convert to string and format
                created_str = str(self.production_batch.created_at)
                if len(created_str) > 16:
                    created_str = created_str[:16]  # Take first 16 chars (YYYY-MM-DD HH:MM)
                self.created_at_label.setText(created_str)
            except:
                self.created_at_label.setText("N/A")
        else:
            self.created_at_label.setText("N/A")
            
        if hasattr(self.production_batch, 'updated_at') and self.production_batch.updated_at:
            try:
                # Convert to string and format
                updated_str = str(self.production_batch.updated_at)
                if len(updated_str) > 16:
                    updated_str = updated_str[:16]  # Take first 16 chars (YYYY-MM-DD HH:MM)
                self.updated_at_label.setText(updated_str)
            except:
                self.updated_at_label.setText("N/A")
        else:
            self.updated_at_label.setText("N/A")
    
    def _set_material_info_na(self):
        """Set all material information fields to N/A"""
        self.material_client_label.setText("N/A")
        self.plaque_dimensions_label.setText("N/A")
        self.caisse_dimensions_label.setText("N/A")
        self.material_type_label.setText("N/A")
        self.supplier_order_ref_label.setText("N/A")
    
    def get_production_data(self) -> Optional[Dict[str, Any]]:
        """Get the edited production data"""
        if not self.editable:
            return None
            
        return {
            'batch_code': self.batch_code_edit.text().strip(),
            'quantity': self.quantity_spin.value(),
            'production_date': self.production_date_edit.date().toString('yyyy-MM-dd') if self.production_date_edit.date().isValid() else None
        }


__all__ = ['ProductionDetailsDialog']
