from __future__ import annotations
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, QCheckBox, QSpinBox,
    QLineEdit, QTextEdit, QDialogButtonBox, QGroupBox, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt
from config.database import SessionLocal
from models.orders import Reception, SupplierOrderLineItem, SupplierOrder
from models.clients import Client
from models.production import ProductionBatch, ProductionStage
from datetime import datetime, timezone
from sqlalchemy.orm import joinedload

class AddFinishedProductDialog(QDialog):
    """Dialog to add a new finished product from existing raw material stock."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter Produit Fini")
        self.setMinimumWidth(500)
        
        self.selected_reception = None
        self.reception_data = {}

        self._build_ui()
        self._load_raw_materials()

    def _build_ui(self):
        """Build the user interface."""
        main_layout = QVBoxLayout(self)
        
        # Raw Material Selection
        material_group = QGroupBox("Sélection de la Matière Première")
        material_layout = QFormLayout(material_group)
        
        self.material_combo = QComboBox()
        self.use_all_checkbox = QCheckBox("Utiliser toute la quantité")
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(0, 999999)
        
        material_layout.addRow("Matière première:", self.material_combo)
        material_layout.addRow(self.use_all_checkbox, self.quantity_spin)
        
        main_layout.addWidget(material_group)
        
        # Material Information Display
        info_group = QGroupBox("Informations de la Matière")
        info_layout = QFormLayout(info_group)
        
        self.client_label = QLabel("N/A")
        self.plaque_dims_label = QLabel("N/A")
        self.caisse_dims_label = QLabel("N/A")
        self.material_type_label = QLabel("N/A")
        self.available_qty_label = QLabel("N/A")
        self.order_ref_label = QLabel("N/A")
        
        info_layout.addRow("Client:", self.client_label)
        info_layout.addRow("Dimensions plaque:", self.plaque_dims_label)
        info_layout.addRow("Dimensions caisse:", self.caisse_dims_label)
        info_layout.addRow("Type de carton:", self.material_type_label)
        info_layout.addRow("Quantité disponible:", self.available_qty_label)
        info_layout.addRow("Référence commande:", self.order_ref_label)
        
        main_layout.addWidget(info_group)
        
        # Production Details
        prod_group = QGroupBox("Détails de Production")
        prod_layout = QFormLayout(prod_group)
        
        self.batch_code_edit = QLineEdit()
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Notes sur la production (optionnel)")
        
        prod_layout.addRow("Code du lot:", self.batch_code_edit)
        prod_layout.addRow("Notes:", self.notes_edit)
        
        main_layout.addWidget(prod_group)
        
        # Dialog Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.create_btn = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.create_btn.setText("Créer Produit Fini")
        self.create_btn.setEnabled(False)
        
        main_layout.addWidget(self.button_box)
        
        # Connections
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.material_combo.currentIndexChanged.connect(self._on_material_selected)
        self.use_all_checkbox.stateChanged.connect(self._toggle_quantity_spin)
        
        self.use_all_checkbox.setChecked(True)

    def _load_raw_materials(self):
        """Load available raw materials from receptions."""
        session = SessionLocal()
        try:
            # Aggregate receptions by line item to represent available stock
            receptions = session.query(Reception).options(
                joinedload(Reception.supplier_order)
                .joinedload(SupplierOrder.line_items)
                .joinedload(SupplierOrderLineItem.client)
            ).all()
            
            materials_dict = {}
            for reception in receptions:
                if not reception.supplier_order or not reception.supplier_order.line_items:
                    continue
                
                line_item = reception.supplier_order.line_items[0]
                client = line_item.client
                supplier_order = reception.supplier_order
                
                key = (line_item.id, supplier_order.id)
                
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
                
                plaque_dims = f"{line_item.plaque_width_mm}×{line_item.plaque_length_mm}×{line_item.plaque_flap_mm}"
                cardboard = line_item.cardboard_type or "Standard"
                
                display_text = f"{client_name} - {plaque_dims}mm - {cardboard} ({total_qty} pièces)"
                
                self.material_combo.addItem(display_text, material_data)
                self.reception_data[i + 1] = material_data
                
        except Exception as e:
            print(f"Error loading raw materials: {e}")
        finally:
            session.close()
    
    def _on_material_selected(self, index):
        """Handle material selection."""
        material_data = self.material_combo.currentData()
        self.selected_reception = material_data
        
        if material_data:
            self._populate_material_info(material_data)
            self.create_btn.setEnabled(True)
            
            max_qty = material_data['total_quantity']
            self.quantity_spin.setMaximum(max_qty)
            self.quantity_spin.setValue(max_qty)
            self.use_all_checkbox.setChecked(True)
            
            # Generate batch code
            client_name_short = "".join([c for c in material_data['client_name'][:3] if c.isalnum()]).upper()
            date_str = datetime.now().strftime('%Y%m%d_%H%M')
            self.batch_code_edit.setText(f"PROD_{client_name_short}_{date_str}")
        else:
            self._clear_material_info()
            self.create_btn.setEnabled(False)
            self.batch_code_edit.clear()

    def _populate_material_info(self, data):
        """Fill the info labels with data from the selected material."""
        line_item = data['line_item']
        supplier_order = data['supplier_order']
        
        self.client_label.setText(data['client_name'])
        self.plaque_dims_label.setText(f"{line_item.plaque_width_mm} × {line_item.plaque_length_mm} × {line_item.plaque_flap_mm} mm")
        self.caisse_dims_label.setText(f"{line_item.caisse_length_mm} × {line_item.caisse_width_mm} × {line_item.caisse_height_mm} mm")
        self.material_type_label.setText(line_item.cardboard_type or "Standard")
        self.available_qty_label.setText(f"{data['total_quantity']} pièces")
        self.order_ref_label.setText(supplier_order.bon_commande_ref)

    def _clear_material_info(self):
        """Clear the material info labels."""
        self.client_label.setText("N/A")
        self.plaque_dims_label.setText("N/A")
        self.caisse_dims_label.setText("N/A")
        self.material_type_label.setText("N/A")
        self.available_qty_label.setText("N/A")
        self.order_ref_label.setText("N/A")

    def _toggle_quantity_spin(self, state):
        """Enable/disable the quantity spin box."""
        self.quantity_spin.setEnabled(state != Qt.CheckState.Checked.value)
        if state == Qt.CheckState.Checked.value and self.selected_reception:
            self.quantity_spin.setValue(self.selected_reception['total_quantity'])

    def get_production_data(self):
        """Return the data for the new production batch."""
        if not self.selected_reception:
            return None
        
        return {
            'material_data': self.selected_reception,
            'quantity_used': self.quantity_spin.value(),
            'use_all': self.use_all_checkbox.isChecked(),
            'batch_code': self.batch_code_edit.text().strip(),
            'notes': self.notes_edit.toPlainText().strip()
        }
    
    def accept(self):
        """Validate and accept the dialog."""
        if not self.selected_reception:
            return
            
        if not self.batch_code_edit.text().strip():
            QMessageBox.warning(self, "Erreur", "Le code du lot est requis.")
            return
            
        if self.quantity_spin.value() <= 0:
            QMessageBox.warning(self, "Erreur", "La quantité doit être supérieure à 0.")
            return
            
        super().accept()

__all__ = ['AddFinishedProductDialog']
