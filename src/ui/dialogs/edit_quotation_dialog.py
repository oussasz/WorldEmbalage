from __future__ import annotations
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QLabel, QPushButton, QComboBox, QSpinBox, QTextEdit, QDateEdit, QFrame, QTableWidget, QMessageBox, QCheckBox
from PyQt6.QtCore import QDate
from decimal import Decimal
from ui.styles import IconManager
from typing import Any
from models.orders import Quotation, QuotationLineItem, BoxColor


class EditQuotationDialog(QDialog):
    def __init__(self, quotation: Quotation, clients: list, parent=None):
        super().__init__(parent)
        self.quotation = quotation
        self.clients = clients
        self.setWindowTitle(f'Modifier Devis - {quotation.reference}')
        self.setWindowIcon(IconManager.get_quotation_icon())
        self.setMinimumWidth(800)
        self.setModal(True)
        self._build()
        self._load_quotation_data()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel(f'Modifier Devis - {self.quotation.reference}')
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Form section
        form_frame = QFrame(); form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(15)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # Référence (read-only)
        self.ref_edit = QLineEdit()
        self.ref_edit.setReadOnly(True)
        form_layout.addRow('Référence:', self.ref_edit)
        
        # Client
        self.client_combo = QComboBox()
        if not self.clients:
            self.client_combo.addItem('Aucun client disponible', None)
        else:
            for client in self.clients:
                self.client_combo.addItem(client.name, client.id)
        form_layout.addRow('Client:', self.client_combo)
        
        # Dates
        self.issue_date_edit = QDateEdit()
        form_layout.addRow('Date émission:', self.issue_date_edit)
        
        self.valid_until_edit = QDateEdit()
        form_layout.addRow('Valide jusqu\'au:', self.valid_until_edit)
        
        # Initial Devis checkbox
        self.initial_devis_check = QCheckBox('Devis Initial (quantités minimales)')
        self.initial_devis_check.setToolTip('Cochez cette option pour spécifier des quantités minimales')
        self.initial_devis_check.toggled.connect(self._on_initial_devis_toggled)
        form_layout.addRow('', self.initial_devis_check)
        
        # Minimum quantity input (only visible when initial devis is checked)
        self.min_qty_edit = QLineEdit()
        self.min_qty_edit.setPlaceholderText('Ex: 500')
        self.min_qty_edit.setText('500')
        self.min_qty_edit.setVisible(False)
        self.min_qty_edit.textChanged.connect(self._update_minimum_quantities)
        form_layout.addRow('Quantité minimale:', self.min_qty_edit)
        
        layout.addWidget(form_frame)

        # Section lignes
        items_header = QLabel('Lignes du Devis (plusieurs types et dimensions)')
        items_header.setStyleSheet('font-size: 14px; font-weight: 600; color: #444;')
        layout.addWidget(items_header)

        self._create_items_table(layout)

        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText('Notes additionnelles...')
        layout.addWidget(QLabel('Notes:'))
        layout.addWidget(self.notes_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton('Annuler')
        self.cancel_btn.setProperty('class', 'secondary')
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton('Sauvegarder')
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)

    def _create_items_table(self, layout):
        from PyQt6.QtWidgets import QTableWidgetItem
        # 12 columns to match the main dialog: Description, Quantité, Prix unitaire HT, Prix total HT, Longueur, Largeur, Hauteur, Couleur, Caractéristique matière, Référence matière première, Cliché, Notes
        self.items_table = QTableWidget(0, 12)
        self.items_table.setHorizontalHeaderLabels([
            'Description', 'Quantité', 'Prix unitaire HT', 'Prix total HT', 'Longueur (mm)', 'Largeur (mm)', 'Hauteur (mm)', 'Couleur', 'Caractéristique matière', 'Référence matière première', 'Cliché', 'Notes'
        ])
        
        # Set minimum row height for better visibility
        vheader = self.items_table.verticalHeader()
        if vheader is not None:
            vheader.setDefaultSectionSize(40)
            vheader.setVisible(False)
        self.items_table.setMinimumHeight(200)
        
        header = self.items_table.horizontalHeader()
        if header is not None:
            # Set specific column widths for better display
            for i in range(12):
                header.setSectionResizeMode(i, header.ResizeMode.Interactive)
            header.resizeSection(0, 150)  # Description
            header.resizeSection(1, 80)   # Quantité
            header.resizeSection(2, 100)  # Prix unitaire HT
            header.resizeSection(3, 100)  # Prix total HT
            header.resizeSection(4, 80)   # Longueur (mm)
            header.resizeSection(5, 80)   # Largeur (mm)
            header.resizeSection(6, 80)   # Hauteur (mm)
            header.resizeSection(7, 70)   # Couleur
            header.resizeSection(8, 140)  # Caractéristique matière
            header.resizeSection(9, 140)  # Référence matière première
            header.resizeSection(10, 60)  # Cliché
            header.resizeSection(11, 100) # Notes
            header.setStretchLastSection(False)
        layout.addWidget(self.items_table)
        
        # Row buttons
        row_btns = QHBoxLayout()
        add_btn = QPushButton('Ajouter ligne')
        add_btn.clicked.connect(self._add_item_row)
        del_btn = QPushButton('Supprimer ligne')
        del_btn.clicked.connect(self._remove_selected_rows)
        row_btns.addStretch(1)
        row_btns.addWidget(add_btn)
        row_btns.addWidget(del_btn)
        layout.addLayout(row_btns)

    def _load_quotation_data(self):
        """Load existing quotation data into the form"""
        self.ref_edit.setText(self.quotation.reference)
        
        # Set client
        for i in range(self.client_combo.count()):
            if self.client_combo.itemData(i) == self.quotation.client_id:
                self.client_combo.setCurrentIndex(i)
                break
        
        # Set dates
        self.issue_date_edit.setDate(QDate.fromString(str(self.quotation.issue_date), "yyyy-MM-dd"))
        if self.quotation.valid_until:
            self.valid_until_edit.setDate(QDate.fromString(str(self.quotation.valid_until), "yyyy-MM-dd"))
        
        # Set initial devis flag
        self.initial_devis_check.setChecked(self.quotation.is_initial)
        
        # Extract minimum quantity from first line item if it's an initial devis
        if self.quotation.is_initial and self.quotation.line_items:
            first_quantity = str(self.quotation.line_items[0].quantity)  # Convert to string
            if 'à partir de' in first_quantity:
                min_qty = first_quantity.replace('à partir de', '').strip()
                self.min_qty_edit.setText(min_qty)
        
        # Set notes
        if self.quotation.notes:
            self.notes_edit.setPlainText(self.quotation.notes)
        
        # Load line items
        for line_item in self.quotation.line_items:
            self._add_item_row(preset_data={
                'description': line_item.description,
                'length_mm': line_item.length_mm,
                'width_mm': line_item.width_mm,
                'height_mm': line_item.height_mm,
                'color': line_item.color,
                'cardboard_type': line_item.cardboard_type,
                'material_reference': getattr(line_item, 'material_reference', ''),  # Handle new field safely
                'is_cliche': line_item.is_cliche,
                'quantity': line_item.quantity,
                'unit_price': str(line_item.unit_price),
                'total_price': str(line_item.total_price),
                'notes': getattr(line_item, 'notes', '')  # Handle notes field safely
            })

    def _add_item_row(self, preset_data: dict[str, Any] | None = None):
        from PyQt6.QtWidgets import QLineEdit, QComboBox, QSpinBox
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        
        # Column 0: Description
        desc = QLineEdit()
        desc.setPlaceholderText('Ex: Carton standard')
        if preset_data and preset_data.get('description'):
            desc.setText(str(preset_data['description']))
        self.items_table.setCellWidget(row, 0, desc)
        
        # Column 1: Quantité
        qty = QLineEdit()
        qty.setPlaceholderText('Ex: 1000 ou >1000')
        if preset_data and preset_data.get('quantity'):
            qty.setText(str(preset_data['quantity']))
        else:
            if self.initial_devis_check.isChecked():
                min_qty = self.min_qty_edit.text() or "500"
                qty.setText(f'à partir de {min_qty}')
                qty.setEnabled(False)
            else:
                qty.setText('100')
        self.items_table.setCellWidget(row, 1, qty)
        
        # Column 2: Prix unitaire HT
        pu = QLineEdit()
        pu.setPlaceholderText('0.00')
        if preset_data and preset_data.get('unit_price'):
            pu.setText(str(preset_data['unit_price']))
        else:
            pu.setText('0.00')
        pu.textChanged.connect(lambda: self._recalc_row_total(row))
        self.items_table.setCellWidget(row, 2, pu)
        
        # Column 3: Prix total HT
        total = QLineEdit()
        total.setReadOnly(True)
        total.setStyleSheet("background-color: #F8F9FA; color: #495057;")
        if preset_data and preset_data.get('total_price'):
            total.setText(str(preset_data['total_price']))
        else:
            if self.initial_devis_check.isChecked():
                total.setText('N/A')
                total.setEnabled(False)
            else:
                total.setText('0.00')
        self.items_table.setCellWidget(row, 3, total)
        
        # Column 4: Longueur (mm)
        def sb(default: int):
            w = QSpinBox()
            w.setRange(1, 10000)
            w.setSuffix(' mm')
            w.setValue(default)
            return w
        
        length_spin = sb(int(preset_data.get('length_mm', 300)) if preset_data else 300)
        self.items_table.setCellWidget(row, 4, length_spin)
        
        # Column 5: Largeur (mm)
        width_spin = sb(int(preset_data.get('width_mm', 200)) if preset_data else 200)
        self.items_table.setCellWidget(row, 5, width_spin)
        
        # Column 6: Hauteur (mm)
        height_spin = sb(int(preset_data.get('height_mm', 150)) if preset_data else 150)
        self.items_table.setCellWidget(row, 6, height_spin)
        
        # Column 7: Couleur
        color = QComboBox()
        color.addItem('Blanc', BoxColor.BLANC)
        color.addItem('Brun', BoxColor.BRUN)
        if preset_data and preset_data.get('color'):
            for i in range(color.count()):
                if color.itemData(i) == preset_data['color']:
                    color.setCurrentIndex(i)
                    break
        self.items_table.setCellWidget(row, 7, color)
        
        # Column 8: Caractéristique matière (renamed from Type carton)
        char_matiere = QLineEdit()
        char_matiere.setPlaceholderText('Ex: Double cannelure BC 7mm')
        if preset_data and preset_data.get('cardboard_type'):
            char_matiere.setText(str(preset_data['cardboard_type']))
        self.items_table.setCellWidget(row, 8, char_matiere)
        
        # Column 9: Référence matière première (new field)
        ref_matiere = QLineEdit()
        ref_matiere.setPlaceholderText('Ex: REF-MAT-001')
        if preset_data and preset_data.get('material_reference'):
            ref_matiere.setText(str(preset_data['material_reference']))
        self.items_table.setCellWidget(row, 9, ref_matiere)
        
        # Column 10: Cliché
        cliche = QComboBox()
        cliche.addItems(['Sans', 'Avec'])
        if preset_data and preset_data.get('is_cliche'):
            cliche.setCurrentIndex(1 if preset_data['is_cliche'] else 0)
        self.items_table.setCellWidget(row, 10, cliche)
        
        # Column 11: Notes
        notes = QLineEdit()
        notes.setPlaceholderText('Notes optionnelles')
        if preset_data and preset_data.get('notes'):
            notes.setText(str(preset_data['notes']))
        self.items_table.setCellWidget(row, 11, notes)
        
        # Connect quantity and unit price changes to recalculate total
        qty.textChanged.connect(lambda _v, r=row: self._recalc_row_total(r))
        pu.textChanged.connect(lambda _t, r=row: self._recalc_row_total(r))
        
        # Setup field validation
        self._setup_field_validation(row)
        
        # Initial validation
        self._validate_row(row)
        
        self._recalc_row_total(row)

    def _remove_selected_rows(self):
        selected_rows = sorted({idx.row() for idx in self.items_table.selectedIndexes()}, reverse=True)
        for r in selected_rows:
            self.items_table.removeRow(r)
        if self.items_table.rowCount() == 0:
            self._add_item_row()

    def _recalc_row_total(self, row: int):
        from PyQt6.QtWidgets import QLineEdit
        import re
        qty_w = self.items_table.cellWidget(row, 1)   # Quantité column
        unit_w = self.items_table.cellWidget(row, 2)  # Prix unitaire HT column
        total_w = self.items_table.cellWidget(row, 3) # Prix total HT column
        
        try:
            # Handle "à partir de" quantities for initial devis
            if self.initial_devis_check.isChecked():
                if isinstance(total_w, QLineEdit):
                    total_w.setText('N/A')
                return
            
            # Extract numeric quantity from string
            qty_text = qty_w.text() if isinstance(qty_w, QLineEdit) else '0'
            numbers = re.findall(r'\d+', qty_text)
            qty = int(numbers[-1]) if numbers else 0
            
            unit_txt = unit_w.text() if isinstance(unit_w, QLineEdit) else '0'
            unit = Decimal(unit_txt or '0')
            total = unit * qty
            if isinstance(total_w, QLineEdit):
                total_w.setText(f"{total:.2f}")
        except Exception:
            if isinstance(total_w, QLineEdit):
                total_w.setText('0.00')

    def _update_dimensions(self, row: int):
        """Update the dimensions column when L, l, H change"""
        try:
            length_widget = self.items_table.cellWidget(row, 1)
            width_widget = self.items_table.cellWidget(row, 2)
            height_widget = self.items_table.cellWidget(row, 3)
            dimensions_widget = self.items_table.cellWidget(row, 4)
            
            if isinstance(length_widget, QSpinBox) and isinstance(width_widget, QSpinBox) and isinstance(height_widget, QSpinBox) and isinstance(dimensions_widget, QLineEdit):
                L = length_widget.value()
                l = width_widget.value()
                H = height_widget.value()
                dimensions_widget.setText(f"{L} × {l} × {H}")
        except Exception:
            pass

    def _validate_field(self, widget, is_required: bool = True):
        """Apply validation styling to a field based on whether it's required and filled"""
        from PyQt6.QtWidgets import QLineEdit
        if not isinstance(widget, QLineEdit):
            return
        
        if is_required:
            if widget.text().strip():
                # Field is filled - remove red border
                widget.setStyleSheet("")
            else:
                # Field is required but empty - add red border
                widget.setStyleSheet("border: 2px solid #dc3545;")
        else:
            # Field is not required - always remove red border
            widget.setStyleSheet("")

    def _validate_row(self, row: int):
        """Validate all fields in a row based on whether it's initial or final devis"""
        from PyQt6.QtWidgets import QLineEdit
        
        is_initial = self.initial_devis_check.isChecked()
        
        # Get widgets
        desc_widget = self.items_table.cellWidget(row, 0)  # Description
        char_matiere_widget = self.items_table.cellWidget(row, 8)  # Caractéristique matière
        ref_matiere_widget = self.items_table.cellWidget(row, 9)  # Référence matière première
        
        # For final devis, these fields are required
        # For initial devis, only description is required
        if isinstance(desc_widget, QLineEdit):
            self._validate_field(desc_widget, is_required=True)  # Always required
        
        if isinstance(char_matiere_widget, QLineEdit):
            self._validate_field(char_matiere_widget, is_required=not is_initial)
            
        if isinstance(ref_matiere_widget, QLineEdit):
            self._validate_field(ref_matiere_widget, is_required=not is_initial)

    def _setup_field_validation(self, row: int):
        """Setup validation for all fields in a row"""
        from PyQt6.QtWidgets import QLineEdit
        
        widgets_to_validate = [
            self.items_table.cellWidget(row, 0),  # Description
            self.items_table.cellWidget(row, 8),  # Caractéristique matière
            self.items_table.cellWidget(row, 9),  # Référence matière première
        ]
        
        for widget in widgets_to_validate:
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(lambda: self._validate_row(row))

    def _on_initial_devis_toggled(self):
        """Handle initial devis checkbox toggle"""
        is_initial = self.initial_devis_check.isChecked()
        
        # Show/hide minimum quantity field
        self.min_qty_edit.setVisible(is_initial)
        
        # Update all quantity fields and revalidate all rows
        for row in range(self.items_table.rowCount()):
            qty_widget = self.items_table.cellWidget(row, 1)  # Quantité column
            total_widget = self.items_table.cellWidget(row, 3)  # Prix total HT column
            
            if isinstance(qty_widget, QLineEdit):
                if is_initial:
                    min_qty = self.min_qty_edit.text() or "500"
                    qty_widget.setText(f'à partir de {min_qty}')
                    qty_widget.setEnabled(False)
                else:
                    qty_widget.setText('100')
                    qty_widget.setEnabled(True)
            
            if isinstance(total_widget, QLineEdit):
                if is_initial:
                    total_widget.setText('N/A')
                    total_widget.setEnabled(False)
                else:
                    total_widget.setEnabled(True)
                    self._recalc_row_total(row)
            
            # Revalidate all fields in the row based on new mode
            self._validate_row(row)

    def _update_minimum_quantities(self):
        """Update all quantity fields when minimum quantity changes"""
        if not self.initial_devis_check.isChecked():
            return
            
        min_qty = self.min_qty_edit.text() or "500"
        
        for row in range(self.items_table.rowCount()):
            qty_widget = self.items_table.cellWidget(row, 1)  # Quantité column
            if isinstance(qty_widget, QLineEdit):
                qty_widget.setText(f'à partir de {min_qty}')

    def get_data(self) -> dict:
        from PyQt6.QtWidgets import QLineEdit, QComboBox, QSpinBox
        import re
        items: list[dict[str, Any]] = []
        for r in range(self.items_table.rowCount()):
            # Column 0: Description
            desc = self.items_table.cellWidget(r, 0)
            # Column 1: Quantité
            qty = self.items_table.cellWidget(r, 1)
            # Column 2: Prix unitaire HT
            unit = self.items_table.cellWidget(r, 2)
            # Column 3: Prix total HT
            total = self.items_table.cellWidget(r, 3)
            # Column 4: Longueur (mm)
            length = self.items_table.cellWidget(r, 4)
            # Column 5: Largeur (mm)
            width = self.items_table.cellWidget(r, 5)
            # Column 6: Hauteur (mm)
            height = self.items_table.cellWidget(r, 6)
            # Column 7: Couleur
            color = self.items_table.cellWidget(r, 7)
            # Column 8: Caractéristique matière
            char_matiere = self.items_table.cellWidget(r, 8)
            # Column 9: Référence matière première
            ref_matiere = self.items_table.cellWidget(r, 9)
            # Column 10: Cliché
            cliche = self.items_table.cellWidget(r, 10)
            # Column 11: Notes
            notes = self.items_table.cellWidget(r, 11)
            
            # Extract values safely
            d = desc.text().strip() if isinstance(desc, QLineEdit) else ''
            q = qty.text().strip() if isinstance(qty, QLineEdit) else '0'
            
            try:
                unit_text = unit.text().strip().replace(',', '.') if isinstance(unit, QLineEdit) else '0'
                pu = Decimal(unit_text or '0')
            except Exception:
                pu = Decimal('0')
            
            try:
                total_text = total.text().strip().replace(',', '.') if isinstance(total, QLineEdit) else '0'
                if total_text == 'N/A':
                    total_value = Decimal('0')
                else:
                    total_value = Decimal(total_text or '0')
            except Exception:
                total_value = Decimal('0')
            
            L = length.value() if isinstance(length, QSpinBox) else 0
            l = width.value() if isinstance(width, QSpinBox) else 0
            H = height.value() if isinstance(height, QSpinBox) else 0
            col = color.currentData() if isinstance(color, QComboBox) else BoxColor.BLANC
            char_mat = char_matiere.text().strip() if isinstance(char_matiere, QLineEdit) else ''
            ref_mat = ref_matiere.text().strip() if isinstance(ref_matiere, QLineEdit) else ''
            is_cliche = cliche.currentIndex() == 1 if isinstance(cliche, QComboBox) else False
            notes_text = notes.text().strip() if isinstance(notes, QLineEdit) else ''
            
            # Handle string quantities - extract numeric part for calculations
            numbers = re.findall(r'\d+', q)
            numeric_q = int(numbers[-1]) if numbers else 0
            
            try:
                pu = Decimal(unit.text() if isinstance(unit, QLineEdit) else '0')
            except Exception:
                pu = Decimal('0')
            
            # Calculate total differently for initial devis
            if self.initial_devis_check.isChecked():
                final_total = Decimal('0')  # No total for initial devis
            else:
                final_total = pu * numeric_q
            
            items.append({
                'description': d,
                'length_mm': L,
                'width_mm': l,
                'height_mm': H,
                'color': col,
                'cardboard_type': char_mat,  # Caractéristique matière
                'material_reference': ref_mat,  # Référence matière première
                'is_cliche': is_cliche,
                'quantity': q,  # Store as string for initial devis
                'unit_price': pu,
                'total_price': final_total,
                'notes': notes_text
            })
        return {
            'reference': self.ref_edit.text().strip(),
            'client_id': self.client_combo.currentData(),
            'issue_date': self.issue_date_edit.date().toPyDate(),
            'valid_until': self.valid_until_edit.date().toPyDate(),
            'line_items': items,
            'notes': self.notes_edit.toPlainText().strip(),
            'is_initial': self.initial_devis_check.isChecked(),
            'minimum_quantity': self.min_qty_edit.text() if self.initial_devis_check.isChecked() else None
        }

__all__ = ['EditQuotationDialog']
