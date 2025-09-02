"""
Dialog for adding finished products by selecting raw materials from stock
"""

from __future__ import annotations
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QSpinBox, QDateEdit, 
                             QLineEdit, QFormLayout, QGroupBox, QCheckBox)
from PyQt6.QtCore import Qt, QDate
from config.database import SessionLocal
from models.orders import Reception, SupplierOrder, SupplierOrderLineItem
from models.clients import Client
from models.production import ProductionBatch
from datetime import date


class AddFinishedProductDialog(QDialog):
    """Dialog for adding finished products from raw materials"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter Produit Fini")
        self.setMinimumSize(600, 500)
        self.reception_data = {}
        self.selected_reception = None
        self._build_ui()
        self._load_raw_materials()
    
    def _build_ui(self):
        """Build the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Raw Material Selection Group
        material_group = QGroupBox("Sélection de la Matière Première")
        material_layout = QFormLayout(material_group)
        
        # Raw material dropdown
        self.material_combo = QComboBox()
        self.material_combo.currentIndexChanged.connect(self._on_material_selected)
        material_layout.addRow("Matière première:", self.material_combo)
        
        # Quantity selection
        quantity_layout = QHBoxLayout()
        
        self.use_all_checkbox = QCheckBox("Utiliser toute la quantité")
        self.use_all_checkbox.toggled.connect(self._on_use_all_toggled)
        quantity_layout.addWidget(self.use_all_checkbox)
        
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 9999)
        self.quantity_spin.setSuffix(" plaques")
        self.quantity_spin.valueChanged.connect(self._calculate_loss)
        quantity_layout.addWidget(QLabel("Quantité:"))
        quantity_layout.addWidget(self.quantity_spin)
        
        material_layout.addRow("", quantity_layout)
        
        # Produced quantity field (right below used quantity)
        self.produced_qty_spin = QSpinBox()
        self.produced_qty_spin.setRange(0, 9999)
        self.produced_qty_spin.setSuffix(" caisses")
        self.produced_qty_spin.valueChanged.connect(self._calculate_loss)
        material_layout.addRow("Quantité produite:", self.produced_qty_spin)
        
        # Loss calculation (read-only)
        self.loss_edit = QLineEdit()
        self.loss_edit.setReadOnly(True)
        self.loss_edit.setStyleSheet("background-color: #f0f0f0; color: #333;")
        material_layout.addRow("Perte:", self.loss_edit)
        
        layout.addWidget(material_group)
        
        # Material Information Group (auto-filled)
        info_group = QGroupBox("Informations de la Matière")
        info_layout = QFormLayout(info_group)
        
        self.client_edit = QLineEdit()
        self.client_edit.setReadOnly(True)
        info_layout.addRow("Client:", self.client_edit)
        
        self.dimensions_edit = QLineEdit()
        self.dimensions_edit.setReadOnly(True)
        info_layout.addRow("Dimensions plaque:", self.dimensions_edit)
        
        self.caisse_dimensions_edit = QLineEdit()
        self.caisse_dimensions_edit.setReadOnly(True)
        info_layout.addRow("Dimensions caisse:", self.caisse_dimensions_edit)
        
        self.material_type_edit = QLineEdit()
        self.material_type_edit.setReadOnly(True)
        info_layout.addRow("Type de carton:", self.material_type_edit)
        
        self.available_qty_edit = QLineEdit()
        self.available_qty_edit.setReadOnly(True)
        info_layout.addRow("Quantité disponible:", self.available_qty_edit)
        
        self.order_ref_edit = QLineEdit()
        self.order_ref_edit.setReadOnly(True)
        info_layout.addRow("Référence commande:", self.order_ref_edit)
        
        layout.addWidget(info_group)
        
        # Production Details Group
        production_group = QGroupBox("Détails de Production")
        production_layout = QFormLayout(production_group)
        
        self.batch_code_edit = QLineEdit()
        self.batch_code_edit.setPlaceholderText("Ex: PROD-20250902-143027-0001-ABC")
        production_layout.addRow("Code du lot:", self.batch_code_edit)
        
        self.production_date_edit = QDateEdit()
        self.production_date_edit.setCalendarPopup(True)
        self.production_date_edit.setDate(QDate.currentDate())
        production_layout.addRow("Date de production:", self.production_date_edit)
        
        layout.addWidget(production_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        button_layout.addStretch()
        
        self.create_btn = QPushButton("Créer Produit Fini")
        self.create_btn.clicked.connect(self.accept)
        self.create_btn.setEnabled(False)
        button_layout.addWidget(self.create_btn)
        
        layout.addLayout(button_layout)
    
    def _load_raw_materials(self):
        """Load available raw materials from receptions"""
        session = SessionLocal()
        try:
            # Get all receptions with their supplier order details
            receptions = session.query(Reception).join(Reception.supplier_order).join(SupplierOrder.line_items).join(SupplierOrderLineItem.client).all()
            
            # Group receptions by same material dimensions (merge same materials)
            materials_dict = {}
            
            for reception in receptions:
                supplier_order = reception.supplier_order
                if not supplier_order.line_items:
                    continue
                    
                # Use first line item for material info (assuming one material type per order)
                line_item = supplier_order.line_items[0]
                client = line_item.client
                
                # Create a key based on dimensions and material properties
                key = (
                    line_item.caisse_length_mm,
                    line_item.caisse_width_mm, 
                    line_item.caisse_height_mm,
                    line_item.plaque_width_mm,
                    line_item.plaque_length_mm,
                    line_item.plaque_flap_mm,
                    line_item.cardboard_type or "Standard",
                    client.id if client else 0
                )
                
                if key not in materials_dict:
                    materials_dict[key] = {
                        'receptions': [],
                        'total_quantity': 0,
                        'client_name': client.name if client else "Client inconnu",
                        'line_item': line_item,
                        'supplier_order': supplier_order
                    }
                
                materials_dict[key]['receptions'].append(reception)
                materials_dict[key]['total_quantity'] += reception.quantity
            
            # Populate the combo box
            self.material_combo.clear()
            self.material_combo.addItem("-- Sélectionner une matière première --", None)
            
            for i, (key, material_data) in enumerate(materials_dict.items()):
                line_item = material_data['line_item']
                client_name = material_data['client_name']
                total_qty = material_data['total_quantity']
                
                # Create display text
                plaque_dims = f"{line_item.plaque_width_mm}×{line_item.plaque_length_mm}×{line_item.plaque_flap_mm}"
                caisse_dims = f"{line_item.caisse_length_mm}×{line_item.caisse_width_mm}×{line_item.caisse_height_mm}"
                cardboard = line_item.cardboard_type or "Standard"
                
                display_text = f"{client_name} - {plaque_dims}mm - {cardboard} ({total_qty} pièces)"
                
                self.material_combo.addItem(display_text, material_data)
                self.reception_data[i + 1] = material_data  # Store for quick access
                
        except Exception as e:
            print(f"Error loading raw materials: {e}")
        finally:
            session.close()
    
    def _on_material_selected(self, index):
        """Handle material selection"""
        material_data = self.material_combo.currentData()
        self.selected_reception = material_data
        
        if material_data:
            self._populate_material_info(material_data)
            self.create_btn.setEnabled(True)
            
            # Set max quantity
            max_qty = material_data['total_quantity']
            self.quantity_spin.setMaximum(max_qty)
            self.quantity_spin.setValue(max_qty)
            self.use_all_checkbox.setChecked(True)
        else:
            self._clear_material_info()
            self.create_btn.setEnabled(False)
    
    def _populate_material_info(self, material_data):
        """Populate the material information fields"""
        line_item = material_data['line_item']
        supplier_order = material_data['supplier_order']
        
        # Client
        self.client_edit.setText(material_data['client_name'])
        
        # Dimensions
        plaque_dims = f"{line_item.plaque_width_mm} × {line_item.plaque_length_mm} × {line_item.plaque_flap_mm} mm"
        self.dimensions_edit.setText(plaque_dims)
        
        caisse_dims = f"{line_item.caisse_length_mm} × {line_item.caisse_width_mm} × {line_item.caisse_height_mm} mm"
        self.caisse_dimensions_edit.setText(caisse_dims)
        
        # Material type
        self.material_type_edit.setText(line_item.cardboard_type or "Standard")
        
        # Available quantity
        self.available_qty_edit.setText(f"{material_data['total_quantity']} pièces")
        
        # Order reference
        self.order_ref_edit.setText(supplier_order.bon_commande_ref or supplier_order.reference)
        
        # Generate batch code suggestion using unified reference system
        if not self.batch_code_edit.text():
            from utils.reference_generator import generate_production_reference
            client_short = material_data['client_name'][:3].upper()
            suggested_code = generate_production_reference(client_short)
            self.batch_code_edit.setText(suggested_code)
    
    def _calculate_loss(self):
        """Calculate and display the loss (used quantity - produced quantity)"""
        used_qty = self.quantity_spin.value()
        produced_qty = self.produced_qty_spin.value()
        loss = used_qty - produced_qty
        
        # Format the loss display
        if loss > 0:
            self.loss_edit.setText(f"{loss} plaques")
            self.loss_edit.setStyleSheet("background-color: #ffe6e6; color: #d63031;")  # Light red for loss
        elif loss == 0:
            self.loss_edit.setText(f"{loss} plaques")
            self.loss_edit.setStyleSheet("background-color: #e6ffe6; color: #00b894;")  # Light green for no loss
        else:
            self.loss_edit.setText(f"{abs(loss)} plaques (surplus)")
            self.loss_edit.setStyleSheet("background-color: #e6f3ff; color: #0984e3;")  # Light blue for surplus
    
    def _clear_material_info(self):
        """Clear all material information fields"""
        self.client_edit.clear()
        self.dimensions_edit.clear()
        self.caisse_dimensions_edit.clear()
        self.material_type_edit.clear()
        self.available_qty_edit.clear()
        self.order_ref_edit.clear()
        self.batch_code_edit.clear()
        self.production_date_edit.setDate(QDate.currentDate())
    
    def _on_use_all_toggled(self, checked):
        """Handle use all quantity checkbox"""
        if checked and self.selected_reception:
            self.quantity_spin.setValue(self.selected_reception['total_quantity'])
            self.quantity_spin.setEnabled(False)
        else:
            self.quantity_spin.setEnabled(True)
        # Recalculate loss whenever quantity changes
        self._calculate_loss()
    
    def get_production_data(self):
        """Get the production data for creating the finished product"""
        if not self.selected_reception:
            return None
            
        return {
            'material_data': self.selected_reception,
            'quantity_used': self.quantity_spin.value(),
            'quantity_produced': self.produced_qty_spin.value(),
            'loss': self.quantity_spin.value() - self.produced_qty_spin.value(),
            'use_all': self.use_all_checkbox.isChecked(),
            'batch_code': self.batch_code_edit.text().strip(),
            'production_date': self.production_date_edit.date().toString('yyyy-MM-dd')
        }
    
    def accept(self):
        """Validate and accept the dialog"""
        if not self.selected_reception:
            return
            
        if not self.batch_code_edit.text().strip():
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", "Le code du lot est requis.")
            return
            
        if self.quantity_spin.value() <= 0:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", "La quantité utilisée doit être supérieure à 0.")
            return
            
        if self.produced_qty_spin.value() > self.quantity_spin.value():
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", "La quantité produite ne peut pas être supérieure à la quantité utilisée.")
            return
            
        super().accept()


__all__ = ['AddFinishedProductDialog']
