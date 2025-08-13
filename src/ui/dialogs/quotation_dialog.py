from __future__ import annotations
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QLabel, QPushButton, QComboBox, QSpinBox, QTextEdit, QDateEdit, QFrame, QTableWidget, QCheckBox
from PyQt6.QtCore import QDate
from decimal import Decimal
from ui.styles import IconManager
from typing import Any


class QuotationDialog(QDialog):
    def __init__(self, clients: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Nouveau Devis')
        self.setWindowIcon(IconManager.get_quotation_icon())
        self.setMinimumWidth(1000)  # Increased width to accommodate dimensions column
        self.setModal(True)
        self.clients = clients
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel('Informations Devis')
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Form section
        form_frame = QFrame(); form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(15)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # Référence - Auto-generated using standardized method
        from utils.helpers import generate_reference
        self.ref_edit = QLineEdit()
        self.ref_edit.setText(generate_reference("DEV"))  # Auto-generate with DEV prefix
        self.ref_edit.setPlaceholderText('Ex: DEV-ABC123')
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
        self.issue_date_edit = QDateEdit(); self.issue_date_edit.setDate(QDate.currentDate())
        form_layout.addRow('Date émission:', self.issue_date_edit)
        
        self.valid_until_edit = QDateEdit(); self.valid_until_edit.setDate(QDate.currentDate().addDays(30))
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
        form_layout.addRow('Quantité minimale:', self.min_qty_edit)
        
        layout.addWidget(form_frame)

        # Section lignes
        items_header = QLabel('Lignes du Devis (plusieurs types et dimensions)')
        items_header.setStyleSheet('font-size: 14px; font-weight: 600; color: #444;')
        layout.addWidget(items_header)

        # Use a table-like widget built from editors per row
        # We'll create helper methods to insert editors per row
        self._create_items_table(layout)

        # Notes
        self.notes_edit = QTextEdit(); self.notes_edit.setMaximumHeight(80); self.notes_edit.setPlaceholderText('Notes additionnelles...')
        layout.addWidget(QLabel('Notes:'))
        layout.addWidget(self.notes_edit)
        
        # Buttons
        btn_layout = QHBoxLayout(); btn_layout.addStretch()
        self.cancel_btn = QPushButton('Annuler'); self.cancel_btn.setProperty('class', 'secondary'); self.cancel_btn.clicked.connect(self.reject)
        self.save_btn = QPushButton('Créer Devis'); self.save_btn.setDefault(True); self.save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.cancel_btn); btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def _create_items_table(self, layout):
        from PyQt6.QtWidgets import QTableWidgetItem
        # 11 columns: Description, L, l, H, Dimensions, Couleur, Type, Cliché, Quantité, PU, Total
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
            # Set specific column widths for better display and ensure all text is visible
            header.setSectionResizeMode(0, header.ResizeMode.Interactive)  # Description
            header.setSectionResizeMode(1, header.ResizeMode.Interactive)  # L (mm)
            header.setSectionResizeMode(2, header.ResizeMode.Interactive)  # l (mm)
            header.setSectionResizeMode(3, header.ResizeMode.Interactive)  # H (mm)
            header.setSectionResizeMode(4, header.ResizeMode.Interactive)  # Dimensions
            header.setSectionResizeMode(5, header.ResizeMode.Interactive)  # Couleur
            header.setSectionResizeMode(6, header.ResizeMode.Interactive)  # Type carton
            header.setSectionResizeMode(7, header.ResizeMode.Interactive)  # Cliché
            header.setSectionResizeMode(8, header.ResizeMode.Interactive)  # Quantité
            header.setSectionResizeMode(9, header.ResizeMode.Interactive)  # PU (DA)
            header.setSectionResizeMode(10, header.ResizeMode.Interactive) # Total (DA)
            
            # Set optimal column widths to fit content
            header.resizeSection(0, 150)  # Description
            header.resizeSection(1, 60)   # L (mm)
            header.resizeSection(2, 60)   # l (mm)
            header.resizeSection(3, 60)   # H (mm)
            header.resizeSection(4, 100)  # Dimensions
            header.resizeSection(5, 70)   # Couleur
            header.resizeSection(6, 120)  # Type carton
            header.resizeSection(7, 60)   # Cliché
            header.resizeSection(8, 110)  # Quantité
            header.resizeSection(9, 70)   # PU (DA)
            header.resizeSection(10, 80)  # Total (DA)
            header.setStretchLastSection(False)
        layout.addWidget(self.items_table)
        
        # Row buttons
        row_btns = QHBoxLayout()
        add_btn = QPushButton('Ajouter ligne'); add_btn.clicked.connect(self._add_item_row)
        del_btn = QPushButton('Supprimer ligne'); del_btn.clicked.connect(self._remove_selected_rows)
        row_btns.addStretch(1); row_btns.addWidget(add_btn); row_btns.addWidget(del_btn)
        layout.addLayout(row_btns)
        
        # Add one default row
        self._add_item_row()

    def _on_initial_devis_toggled(self, checked: bool):
        """Handle initial devis checkbox toggle"""
        from PyQt6.QtWidgets import QLineEdit
        
        # Show/hide minimum quantity field
        self.min_qty_edit.setVisible(checked)
        
        # Connect minimum quantity change to update rows
        if checked:
            self.min_qty_edit.textChanged.connect(self._update_min_quantities)
        else:
            self.min_qty_edit.textChanged.disconnect()
        
        for row in range(self.items_table.rowCount()):
            qty_widget = self.items_table.cellWidget(row, 8)  # Quantity column (updated index)
            total_widget = self.items_table.cellWidget(row, 10)  # Total column (updated index)
            
            if isinstance(qty_widget, QLineEdit):
                qty_widget.setEnabled(not checked)
                if checked:
                    min_qty = self.min_qty_edit.text() or "500"
                    qty_widget.setText(f"à partir de {min_qty}")
                else:
                    qty_widget.setText("100")
            
            if isinstance(total_widget, QLineEdit):
                total_widget.setEnabled(not checked)
                if checked:
                    total_widget.setText("N/A")
                else:
                    self._recalc_row_total(row)

    def _update_min_quantities(self):
        """Update all quantity fields when minimum quantity changes"""
        from PyQt6.QtWidgets import QLineEdit
        
        if not self.initial_devis_check.isChecked():
            return
            
        min_qty = self.min_qty_edit.text() or "500"
        
        for row in range(self.items_table.rowCount()):
            qty_widget = self.items_table.cellWidget(row, 8)  # Quantity column (updated index)
            if isinstance(qty_widget, QLineEdit):
                qty_widget.setText(f"à partir de {min_qty}")

    def _update_dimensions(self, row: int):
        """Update the dimensions display for a specific row"""
        from PyQt6.QtWidgets import QLineEdit, QSpinBox
        
        length_widget = self.items_table.cellWidget(row, 1)
        width_widget = self.items_table.cellWidget(row, 2)
        height_widget = self.items_table.cellWidget(row, 3)
        dims_widget = self.items_table.cellWidget(row, 4)
        
        if (isinstance(length_widget, QSpinBox) and isinstance(width_widget, QSpinBox) and 
            isinstance(height_widget, QSpinBox) and isinstance(dims_widget, QLineEdit)):
            
            L = length_widget.value()
            l = width_widget.value()
            H = height_widget.value()
            
            if L > 0 and l > 0 and H > 0:
                dims_widget.setText(f"{L} × {l} × {H}")
            else:
                dims_widget.setText("")

    def _add_item_row(self):
        from PyQt6.QtWidgets import QLineEdit, QComboBox
        from models.orders import BoxColor
        row = self.items_table.rowCount(); self.items_table.insertRow(row)
        
        # Description
        desc = QLineEdit(); desc.setPlaceholderText('Ex: Carton standard'); self.items_table.setCellWidget(row, 0, desc)
        
        # L, l, H as SpinBoxes
        def sb(default: int):
            w = QSpinBox(); w.setRange(1, 10000); w.setSuffix(' mm'); w.setValue(default); return w
        self.items_table.setCellWidget(row, 1, sb(300))
        self.items_table.setCellWidget(row, 2, sb(200))
        self.items_table.setCellWidget(row, 3, sb(150))
        
        # Dimensions (auto-calculated, read-only)
        dims = QLineEdit(); dims.setReadOnly(True); dims.setStyleSheet("background-color: #F8F9FA; color: #495057;")
        self.items_table.setCellWidget(row, 4, dims)
        
        # Couleur
        color = QComboBox(); color.addItem('Blanc', BoxColor.BLANC); color.addItem('Brun', BoxColor.BRUN)
        self.items_table.setCellWidget(row, 5, color)
        
        # Type carton
        ctype = QLineEdit(); ctype.setPlaceholderText('Ex: Double cannelure BC 7mm'); self.items_table.setCellWidget(row, 6, ctype)
        
        # Cliché
        cliche = QComboBox(); cliche.addItems(['Sans', 'Avec']); self.items_table.setCellWidget(row, 7, cliche)
        
        # Quantité
        qty = QLineEdit(); qty.setPlaceholderText('Ex: 1000 ou >1000'); 
        if self.initial_devis_check.isChecked():
            min_qty = self.min_qty_edit.text() or "500"
            qty.setText(f'à partir de {min_qty}')
            qty.setEnabled(False)
        else:
            qty.setText('100')
        self.items_table.setCellWidget(row, 8, qty)
        
        # PU
        unit = QLineEdit(); unit.setPlaceholderText('0.00'); unit.setText('50.00'); self.items_table.setCellWidget(row, 9, unit)
        
        # Total (read-only)
        total = QLineEdit(); total.setReadOnly(True)
        if self.initial_devis_check.isChecked():
            total.setText('N/A')
            total.setEnabled(False)
        self.items_table.setCellWidget(row, 10, total)
        
        # Recalculate
        qty.textChanged.connect(lambda _v, r=row: self._recalc_row_total(r))
        unit.textChanged.connect(lambda _t, r=row: self._recalc_row_total(r))
        
        # Update dimensions when L, l, H change
        length_widget = self.items_table.cellWidget(row, 1)
        width_widget = self.items_table.cellWidget(row, 2)
        height_widget = self.items_table.cellWidget(row, 3)
        
        if isinstance(length_widget, QSpinBox):
            length_widget.valueChanged.connect(lambda _v, r=row: self._update_dimensions(r))
        if isinstance(width_widget, QSpinBox):
            width_widget.valueChanged.connect(lambda _v, r=row: self._update_dimensions(r))
        if isinstance(height_widget, QSpinBox):
            height_widget.valueChanged.connect(lambda _v, r=row: self._update_dimensions(r))
        
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
        qty_w = self.items_table.cellWidget(row, 8)  # Updated quantity column index
        unit_w = self.items_table.cellWidget(row, 9)  # Updated unit price column index
        total_w = self.items_table.cellWidget(row, 10)  # Updated total column index
        try:
            qty_text = qty_w.text() if isinstance(qty_w, QLineEdit) else '0'
            numbers = re.findall(r'\d+', qty_text)
            qty = int(numbers[-1]) if numbers else 0
            
            unit_txt = unit_w.text() if isinstance(unit_w, QLineEdit) else '0'
            unit = Decimal(unit_txt.replace(',', '.') or '0')
            total = unit * qty
            if isinstance(total_w, QLineEdit): total_w.setText(f"{total:.2f}")
        except (ValueError, TypeError, Exception):
            if isinstance(total_w, QLineEdit): total_w.setText('0.00')

    def get_data(self) -> dict:
        from PyQt6.QtWidgets import QLineEdit, QComboBox
        from models.orders import BoxColor
        items: list[dict[str, Any]] = []
        for r in range(self.items_table.rowCount()):
            desc = self.items_table.cellWidget(r, 0)
            length = self.items_table.cellWidget(r, 1)
            width = self.items_table.cellWidget(r, 2)
            height = self.items_table.cellWidget(r, 3)
            dims = self.items_table.cellWidget(r, 4)  # Dimensions (read-only)
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
            dimensions_text = dims.text().strip() if isinstance(dims, QLineEdit) else ''
            col = color.currentData() if isinstance(color, QComboBox) else BoxColor.BLANC
            t = ctype.text().strip() if isinstance(ctype, QLineEdit) else ''
            is_cliche = cliche.currentIndex() == 1 if isinstance(cliche, QComboBox) else False
            q = qty.text().strip() if isinstance(qty, QLineEdit) else '0'
            # Handle "à partir de" quantities for initial devis
            if q.startswith('à partir de'):
                q = '0'  # Don't calculate totals for initial devis
            elif q == 'N/A':
                q = '0'
            try:
                unit_text = unit.text().strip().replace(',', '.') if isinstance(unit, QLineEdit) else '0'
                pu = Decimal(unit_text or '0')
            except Exception:
                pu = Decimal('0')

            import re
            numbers = re.findall(r'\d+', q)
            numeric_q = int(numbers[-1]) if numbers else 0
            
            # For initial devis, don't calculate total
            if self.initial_devis_check.isChecked():
                total = Decimal('0')
            else:
                total = pu * numeric_q
            items.append({
                'description': d,
                'length_mm': L,
                'width_mm': l,
                'height_mm': H,
                'dimensions': dimensions_text,
                'color': col,
                'cardboard_type': t,
                'is_cliche': is_cliche,
                'quantity': q,
                'unit_price': pu,
                'total_price': total
            })
        return {
            'reference': self.ref_edit.text().strip(),
            'client_id': self.client_combo.currentData(),
            'issue_date': self.issue_date_edit.date().toPyDate(),
            'valid_until': self.valid_until_edit.date().toPyDate(),
            'is_initial': self.initial_devis_check.isChecked(),
            'line_items': items,
            'notes': self.notes_edit.toPlainText().strip()
        }

__all__ = ['QuotationDialog']
