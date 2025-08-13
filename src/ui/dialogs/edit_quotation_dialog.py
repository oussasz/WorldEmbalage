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
        # 11 columns to match the main dialog: Description, L, l, H, Dimensions, Couleur, Type, Cliché, Quantité, PU, Total
        self.items_table = QTableWidget(0, 11)
        self.items_table.setHorizontalHeaderLabels([
            'Description', 'L (mm)', 'l (mm)', 'H (mm)', 'Dimensions', 'Couleur', 'Type carton', 'Cliché', 'Quantité', 'PU (DA)', 'Total (DA)'
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
            for i in range(10):
                header.setSectionResizeMode(i, header.ResizeMode.Interactive)
            header.resizeSection(0, 180)  # Description
            header.resizeSection(1, 80)   # L (mm)
            header.resizeSection(2, 80)   # l (mm)
            header.resizeSection(3, 80)   # H (mm)
            header.resizeSection(4, 90)   # Couleur
            header.resizeSection(5, 160)  # Type carton
            header.resizeSection(6, 90)   # Cliché
            header.resizeSection(7, 90)   # Quantité
            header.resizeSection(8, 90)   # PU (DA)
            header.resizeSection(9, 100)  # Total (DA)
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
                'is_cliche': line_item.is_cliche,
                'quantity': line_item.quantity,
                'unit_price': str(line_item.unit_price),
                'total_price': str(line_item.total_price)
            })

    def _add_item_row(self, preset_data: dict[str, Any] | None = None):
        from PyQt6.QtWidgets import QLineEdit, QComboBox
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        
        # Description
        desc = QLineEdit()
        desc.setPlaceholderText('Ex: Carton standard')
        if preset_data and preset_data.get('description'):
            desc.setText(str(preset_data['description']))
        self.items_table.setCellWidget(row, 0, desc)
        
        # L, l, H as SpinBoxes
        def sb(default: int):
            w = QSpinBox()
            w.setRange(1, 10000)
            w.setSuffix(' mm')
            w.setValue(default)
            return w
        
        length_spin = sb(int(preset_data.get('length_mm', 300)) if preset_data else 300)
        width_spin = sb(int(preset_data.get('width_mm', 200)) if preset_data else 200)
        height_spin = sb(int(preset_data.get('height_mm', 150)) if preset_data else 150)
        
        self.items_table.setCellWidget(row, 1, length_spin)
        self.items_table.setCellWidget(row, 2, width_spin)
        self.items_table.setCellWidget(row, 3, height_spin)
        
        # Dimensions (read-only, auto-calculated)
        dimensions = QLineEdit()
        dimensions.setReadOnly(True)
        dimensions.setStyleSheet("background-color: #f5f5f5;")
        self.items_table.setCellWidget(row, 4, dimensions)
        
        # Couleur
        color = QComboBox()
        color.addItem('Blanc', BoxColor.BLANC)
        color.addItem('Brun', BoxColor.BRUN)
        if preset_data and preset_data.get('color'):
            for i in range(color.count()):
                if color.itemData(i) == preset_data['color']:
                    color.setCurrentIndex(i)
                    break
        self.items_table.setCellWidget(row, 5, color)
        
        # Type carton
        ctype = QLineEdit()
        ctype.setPlaceholderText('Ex: Double cannelure BC 7mm')
        if preset_data and preset_data.get('cardboard_type'):
            ctype.setText(str(preset_data['cardboard_type']))
        self.items_table.setCellWidget(row, 6, ctype)
        
        # Cliché
        cliche = QComboBox()
        cliche.addItems(['Sans', 'Avec'])
        if preset_data and preset_data.get('is_cliche'):
            cliche.setCurrentIndex(1 if preset_data['is_cliche'] else 0)
        self.items_table.setCellWidget(row, 7, cliche)
        
        # Quantité (now a QLineEdit to handle string quantities)
        qty = QLineEdit()
        qty.setPlaceholderText('Ex: 1000 ou >1000')
        if preset_data and preset_data.get('quantity'):
            qty.setText(str(preset_data['quantity']))
        elif self.initial_devis_check.isChecked():
            min_qty = self.min_qty_edit.text() or "500"
            qty.setText(f'à partir de {min_qty}')
            qty.setEnabled(False)
        else:
            qty.setText('100')
        self.items_table.setCellWidget(row, 8, qty)
        
        # PU
        unit = QLineEdit()
        unit.setPlaceholderText('0.00')
        unit.setText(str(preset_data.get('unit_price', '50.00')) if preset_data else '50.00')
        self.items_table.setCellWidget(row, 9, unit)
        
        # Total (read-only)
        total = QLineEdit()
        total.setReadOnly(True)
        if self.initial_devis_check.isChecked():
            total.setText('N/A')
            total.setEnabled(False)
        self.items_table.setCellWidget(row, 10, total)
        
        # Connect change events
        qty.textChanged.connect(lambda _v, r=row: self._recalc_row_total(r))
        unit.textChanged.connect(lambda _t, r=row: self._recalc_row_total(r))
        
        # Update dimensions when L, l, H change
        length_spin.valueChanged.connect(lambda _v, r=row: self._update_dimensions(r))
        width_spin.valueChanged.connect(lambda _v, r=row: self._update_dimensions(r))
        height_spin.valueChanged.connect(lambda _v, r=row: self._update_dimensions(r))
        
        # Recalculate and update dimensions
        self._recalc_row_total(row)
        self._update_dimensions(row)

    def _remove_selected_rows(self):
        selected_rows = sorted({idx.row() for idx in self.items_table.selectedIndexes()}, reverse=True)
        for r in selected_rows:
            self.items_table.removeRow(r)
        if self.items_table.rowCount() == 0:
            self._add_item_row()

    def _recalc_row_total(self, row: int):
        from PyQt6.QtWidgets import QLineEdit
        import re
        qty_w = self.items_table.cellWidget(row, 8)  # Updated column index
        unit_w = self.items_table.cellWidget(row, 9)
        total_w = self.items_table.cellWidget(row, 10)
        
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

    def _on_initial_devis_toggled(self):
        """Handle initial devis checkbox toggle"""
        is_initial = self.initial_devis_check.isChecked()
        
        # Show/hide minimum quantity field
        self.min_qty_edit.setVisible(is_initial)
        
        # Update all quantity fields
        for row in range(self.items_table.rowCount()):
            qty_widget = self.items_table.cellWidget(row, 8)  # Quantity column
            total_widget = self.items_table.cellWidget(row, 10)  # Total column
            
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

    def _update_minimum_quantities(self):
        """Update all quantity fields when minimum quantity changes"""
        if not self.initial_devis_check.isChecked():
            return
            
        min_qty = self.min_qty_edit.text() or "500"
        
        for row in range(self.items_table.rowCount()):
            qty_widget = self.items_table.cellWidget(row, 8)  # Quantity column
            if isinstance(qty_widget, QLineEdit):
                qty_widget.setText(f'à partir de {min_qty}')

    def get_data(self) -> dict:
        from PyQt6.QtWidgets import QLineEdit, QComboBox
        import re
        items: list[dict[str, Any]] = []
        for r in range(self.items_table.rowCount()):
            desc = self.items_table.cellWidget(r, 0)
            length = self.items_table.cellWidget(r, 1)
            width = self.items_table.cellWidget(r, 2)
            height = self.items_table.cellWidget(r, 3)
            dimensions = self.items_table.cellWidget(r, 4)
            color = self.items_table.cellWidget(r, 5)
            ctype = self.items_table.cellWidget(r, 6)
            cliche = self.items_table.cellWidget(r, 7)
            qty = self.items_table.cellWidget(r, 8)
            unit = self.items_table.cellWidget(r, 9)
            
            # extract values safely
            d = desc.text().strip() if isinstance(desc, QLineEdit) else ''
            L = length.value() if isinstance(length, QSpinBox) else 0
            l = width.value() if isinstance(width, QSpinBox) else 0
            H = height.value() if isinstance(height, QSpinBox) else 0
            dims = dimensions.text().strip() if isinstance(dimensions, QLineEdit) else f"{L} × {l} × {H}"
            col = color.currentData() if isinstance(color, QComboBox) else BoxColor.BLANC
            t = ctype.text().strip() if isinstance(ctype, QLineEdit) else ''
            is_cliche = cliche.currentIndex() == 1 if isinstance(cliche, QComboBox) else False
            
            # Handle string quantities
            qty_text = qty.text() if isinstance(qty, QLineEdit) else '0'
            # Extract numeric quantity from string
            numbers = re.findall(r'\d+', qty_text)
            q = int(numbers[-1]) if numbers else 0
            
            try:
                pu = Decimal(unit.text() if isinstance(unit, QLineEdit) else '0')
            except Exception:
                pu = Decimal('0')
            
            # Calculate total differently for initial devis
            if self.initial_devis_check.isChecked():
                total = Decimal('0')  # No total for initial devis
            else:
                total = pu * q
            
            items.append({
                'description': d,
                'length_mm': L,
                'width_mm': l,
                'height_mm': H,
                'color': col,
                'cardboard_type': t,
                'is_cliche': is_cliche,
                'quantity': qty_text,  # Store as string for initial devis
                'unit_price': pu,
                'total_price': total
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
