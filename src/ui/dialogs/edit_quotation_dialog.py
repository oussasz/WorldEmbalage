from __future__ import annotations
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QLabel, QPushButton, QComboBox, QSpinBox, QTextEdit, QDateEdit, QFrame, QTableWidget, QMessageBox
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
        # 10 columns: Description, L, l, H, Couleur, Type, Cliché, Quantité, PU, Total
        self.items_table = QTableWidget(0, 10)
        self.items_table.setHorizontalHeaderLabels([
            'Description', 'L (mm)', 'l (mm)', 'H (mm)', 'Couleur', 'Type carton', 'Cliché', 'Quantité', 'PU (DA)', 'Total (DA)'
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
        
        # Couleur
        color = QComboBox()
        color.addItem('Blanc', BoxColor.BLANC)
        color.addItem('Brun', BoxColor.BRUN)
        if preset_data and preset_data.get('color'):
            for i in range(color.count()):
                if color.itemData(i) == preset_data['color']:
                    color.setCurrentIndex(i)
                    break
        self.items_table.setCellWidget(row, 4, color)
        
        # Type carton
        ctype = QLineEdit()
        ctype.setPlaceholderText('Ex: Double cannelure BC 7mm')
        if preset_data and preset_data.get('cardboard_type'):
            ctype.setText(str(preset_data['cardboard_type']))
        self.items_table.setCellWidget(row, 5, ctype)
        
        # Cliché
        cliche = QComboBox()
        cliche.addItems(['Sans', 'Avec'])
        if preset_data and preset_data.get('is_cliche'):
            cliche.setCurrentIndex(1 if preset_data['is_cliche'] else 0)
        self.items_table.setCellWidget(row, 6, cliche)
        
        # Quantité
        qty = QSpinBox()
        qty.setRange(1, 100000)
        qty.setValue(int(preset_data.get('quantity', 100)) if preset_data else 100)
        self.items_table.setCellWidget(row, 7, qty)
        
        # PU
        unit = QLineEdit()
        unit.setPlaceholderText('0.00')
        unit.setText(str(preset_data.get('unit_price', '50.00')) if preset_data else '50.00')
        self.items_table.setCellWidget(row, 8, unit)
        
        # Total (read-only)
        total = QLineEdit()
        total.setReadOnly(True)
        self.items_table.setCellWidget(row, 9, total)
        
        # Recalculate
        qty.valueChanged.connect(lambda _v, r=row: self._recalc_row_total(r))
        unit.textChanged.connect(lambda _t, r=row: self._recalc_row_total(r))
        self._recalc_row_total(row)

    def _remove_selected_rows(self):
        selected_rows = sorted({idx.row() for idx in self.items_table.selectedIndexes()}, reverse=True)
        for r in selected_rows:
            self.items_table.removeRow(r)
        if self.items_table.rowCount() == 0:
            self._add_item_row()

    def _recalc_row_total(self, row: int):
        from PyQt6.QtWidgets import QLineEdit
        qty_w = self.items_table.cellWidget(row, 7)
        unit_w = self.items_table.cellWidget(row, 8)
        total_w = self.items_table.cellWidget(row, 9)
        try:
            qty = qty_w.value() if isinstance(qty_w, QSpinBox) else 0
            unit_txt = unit_w.text() if isinstance(unit_w, QLineEdit) else '0'
            unit = Decimal(unit_txt or '0')
            total = unit * qty
            if isinstance(total_w, QLineEdit):
                total_w.setText(f"{total:.2f}")
        except Exception:
            if isinstance(total_w, QLineEdit):
                total_w.setText('0.00')

    def get_data(self) -> dict:
        from PyQt6.QtWidgets import QLineEdit, QComboBox
        items: list[dict[str, Any]] = []
        for r in range(self.items_table.rowCount()):
            desc = self.items_table.cellWidget(r, 0)
            length = self.items_table.cellWidget(r, 1)
            width = self.items_table.cellWidget(r, 2)
            height = self.items_table.cellWidget(r, 3)
            color = self.items_table.cellWidget(r, 4)
            ctype = self.items_table.cellWidget(r, 5)
            cliche = self.items_table.cellWidget(r, 6)
            qty = self.items_table.cellWidget(r, 7)
            unit = self.items_table.cellWidget(r, 8)
            # extract values safely
            d = desc.text().strip() if isinstance(desc, QLineEdit) else ''
            L = length.value() if isinstance(length, QSpinBox) else 0
            l = width.value() if isinstance(width, QSpinBox) else 0
            H = height.value() if isinstance(height, QSpinBox) else 0
            col = color.currentData() if isinstance(color, QComboBox) else BoxColor.BLANC
            t = ctype.text().strip() if isinstance(ctype, QLineEdit) else ''
            is_cliche = cliche.currentIndex() == 1 if isinstance(cliche, QComboBox) else False
            q = qty.value() if isinstance(qty, QSpinBox) else 0
            try:
                pu = Decimal(unit.text() if isinstance(unit, QLineEdit) else '0')
            except Exception:
                pu = Decimal('0')
            total = pu * q
            items.append({
                'description': d,
                'length_mm': L,
                'width_mm': l,
                'height_mm': H,
                'color': col,
                'cardboard_type': t,
                'is_cliche': is_cliche,
                'quantity': q,
                'unit_price': pu,
                'total_price': total
            })
        return {
            'client_id': self.client_combo.currentData(),
            'issue_date': self.issue_date_edit.date().toPyDate(),
            'valid_until': self.valid_until_edit.date().toPyDate(),
            'line_items': items,
            'notes': self.notes_edit.toPlainText().strip()
        }

__all__ = ['EditQuotationDialog']
