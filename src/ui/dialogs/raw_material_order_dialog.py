from __future__ import annotations
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QLabel, QPushButton, QComboBox, QSpinBox, QTextEdit, QDateEdit, QFrame, QGroupBox
from PyQt6.QtCore import QDate
from typing import Optional, Any
from models.orders import ClientOrder, QuotationLineItem
from ui.styles import IconManager


class RawMaterialOrderDialog(QDialog):
    def __init__(self, suppliers: list, client_order: ClientOrder, parent=None):
        super().__init__(parent)
        self.suppliers = suppliers
        self.client_order = client_order
        self.setWindowTitle(f'Commande Matières Premières - {client_order.reference}')
        self.setWindowIcon(IconManager.get_material_icon())
        self.setMinimumWidth(700)
        self.setModal(True)
        self._calculated_dimensions = {}
        self._build_ui()
        self._calculate_material_requirements()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel(f'Commande Matières pour {self.client_order.reference}')
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Order Information
        order_frame = QFrame()
        order_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        order_layout = QFormLayout(order_frame)
        order_layout.setSpacing(15)
        
        # Reference
        self.ref_edit = QLineEdit()
        self.ref_edit.setPlaceholderText('Ex: MAT-2025-001')
        order_layout.addRow('Référence commande:', self.ref_edit)
        
        # Supplier
        self.supplier_combo = QComboBox()
        for supplier in self.suppliers:
            self.supplier_combo.addItem(supplier.name, supplier.id)
        order_layout.addRow('Fournisseur:', self.supplier_combo)
        
        # Order Date
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        order_layout.addRow('Date commande:', self.date_edit)
        
        layout.addWidget(order_frame)
        
        # Material Calculations Section
        calc_group = QGroupBox("Calculs Automatiques des Plaques")
        calc_group.setStyleSheet("QGroupBox { font-weight: bold; color: #2C3E50; }")
        calc_layout = QVBoxLayout(calc_group)
        
        self.calc_label = QLabel()
        self.calc_label.setStyleSheet("color: #34495E; font-size: 12px; margin: 10px;")
        calc_layout.addWidget(self.calc_label)
        
        layout.addWidget(calc_group)
        
        # Material Specifications
        material_frame = QFrame()
        material_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        material_layout = QFormLayout(material_frame)
        material_layout.setSpacing(15)
        
        # Material type
        self.material_edit = QLineEdit()
        self.material_edit.setPlaceholderText('Ex: Plaque carton ondulé BC 7mm')
        material_layout.addRow('Type matériau:', self.material_edit)
        
        # Calculated dimensions (read-only)
        self.calc_length_edit = QLineEdit()
        self.calc_length_edit.setReadOnly(True)
        self.calc_length_edit.setStyleSheet("background-color: #F8F9FA; color: #495057;")
        material_layout.addRow('Longueur plaque calculée (mm):', self.calc_length_edit)
        
        self.calc_width_edit = QLineEdit()
        self.calc_width_edit.setReadOnly(True)
        self.calc_width_edit.setStyleSheet("background-color: #F8F9FA; color: #495057;")
        material_layout.addRow('Largeur plaque calculée (mm):', self.calc_width_edit)
        
        self.calc_rabat_edit = QLineEdit()
        self.calc_rabat_edit.setReadOnly(True)
        self.calc_rabat_edit.setStyleSheet("background-color: #F8F9FA; color: #495057;")
        material_layout.addRow('Rabat calculé (mm):', self.calc_rabat_edit)
        
        # Manual override option
        override_layout = QHBoxLayout()
        override_layout.addWidget(QLabel('Dimensions manuelles (optionnel):'))
        
        self.manual_length_spin = QSpinBox()
        self.manual_length_spin.setRange(0, 10000)
        self.manual_length_spin.setValue(0)
        self.manual_length_spin.setSpecialValueText("Auto")
        override_layout.addWidget(QLabel('L:'))
        override_layout.addWidget(self.manual_length_spin)
        
        self.manual_width_spin = QSpinBox()
        self.manual_width_spin.setRange(0, 10000)
        self.manual_width_spin.setValue(0)
        self.manual_width_spin.setSpecialValueText("Auto")
        override_layout.addWidget(QLabel('l:'))
        override_layout.addWidget(self.manual_width_spin)
        
        material_layout.addRow(override_layout)
        
        # Quantity
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 100000)
        self.quantity_spin.setValue(100)
        material_layout.addRow('Quantité plaques:', self.quantity_spin)
        
        layout.addWidget(material_frame)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText('Notes additionnelles sur la commande...')
        layout.addWidget(QLabel('Notes:'))
        layout.addWidget(self.notes_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton('Annuler')
        self.cancel_btn.setProperty("class", "secondary")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton('Créer Commande')
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)

    def _calculate_material_requirements(self):
        """Calculate material requirements based on client order quotation line items"""
        if not self.client_order.quotation or not self.client_order.quotation.line_items:
            self.calc_label.setText("⚠️ Aucune donnée de devis trouvée pour calculer les dimensions")
            return
        
        calculations = []
        total_quantity = 0
        max_length = 0
        max_width = 0
        max_rabat = 0
        
        for line_item in self.client_order.quotation.line_items:
            if line_item.length_mm and line_item.width_mm:
                # Formules spécifiées par l'utilisateur:
                # largeur de plaque = largeur de carton + longueur de carton
                plaque_width = line_item.width_mm + line_item.length_mm
                
                # longueur de plaque = (largeur de carton + longueur de carton) * 2
                plaque_length = (line_item.width_mm + line_item.length_mm) * 2
                
                # Rabat = largeur de carton / 2
                rabat = line_item.width_mm / 2
                
                calculations.append({
                    'description': line_item.description or f"Ligne {line_item.line_number}",
                    'carton_length': line_item.length_mm,
                    'carton_width': line_item.width_mm,
                    'carton_height': line_item.height_mm or 0,
                    'quantity': line_item.quantity,
                    'plaque_length': plaque_length,
                    'plaque_width': plaque_width,
                    'rabat': rabat
                })
                
                total_quantity += line_item.quantity
                max_length = max(max_length, plaque_length)
                max_width = max(max_width, plaque_width)
                max_rabat = max(max_rabat, rabat)
        
        if calculations:
            # Format calculation display
            calc_text = "📐 Calculs basés sur les dimensions du devis:\\n\\n"
            for calc in calculations:
                calc_text += f"• {calc['description']}:\\n"
                calc_text += f"  Carton: {calc['carton_length']}×{calc['carton_width']}×{calc['carton_height']}mm (Qté: {calc['quantity']})\\n"
                calc_text += f"  → Plaque: {calc['plaque_length']:.0f}×{calc['plaque_width']:.0f}mm (Rabat: {calc['rabat']:.0f}mm)\\n\\n"
            
            calc_text += f"📦 Recommandation: Plaque standard {max_length:.0f}×{max_width:.0f}mm"
            
            self.calc_label.setText(calc_text)
            
            # Set calculated values
            self._calculated_dimensions = {
                'length': int(max_length),
                'width': int(max_width),
                'rabat': int(max_rabat),
                'total_quantity': total_quantity
            }
            
            self.calc_length_edit.setText(f"{max_length:.0f}")
            self.calc_width_edit.setText(f"{max_width:.0f}")
            self.calc_rabat_edit.setText(f"{max_rabat:.0f}")
            
            # Set suggested quantity (could be optimized based on material efficiency)
            self.quantity_spin.setValue(total_quantity)
            
            # Auto-fill material type based on most common type in quotation
            cardboard_types = [li.cardboard_type for li in self.client_order.quotation.line_items if li.cardboard_type]
            if cardboard_types:
                most_common_type = max(set(cardboard_types), key=cardboard_types.count)
                self.material_edit.setText(f"Plaque {most_common_type}")
        else:
            self.calc_label.setText("⚠️ Dimensions de carton manquantes dans le devis")

    def get_data(self) -> dict:
        # Use manual dimensions if specified, otherwise use calculated
        final_length = self.manual_length_spin.value() if self.manual_length_spin.value() > 0 else self._calculated_dimensions.get('length', 0)
        final_width = self.manual_width_spin.value() if self.manual_width_spin.value() > 0 else self._calculated_dimensions.get('width', 0)
        
        return {
            'reference': self.ref_edit.text().strip(),
            'supplier_id': self.supplier_combo.currentData(),
            'order_date': self.date_edit.date().toPyDate(),
            'material_type': self.material_edit.text().strip(),
            'length_mm': final_length,
            'width_mm': final_width,
            'rabat_mm': self._calculated_dimensions.get('rabat', 0),
            'quantity': self.quantity_spin.value(),
            'calculated_data': self._calculated_dimensions,
            'notes': self.notes_edit.toPlainText().strip()
        }

__all__ = ['RawMaterialOrderDialog']
