from __future__ import annotations
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QLabel, QPushButton, QComboBox, QSpinBox, QTextEdit, QDateEdit, QFrame, QTableWidget
from PyQt6.QtCore import QDate
from decimal import Decimal
from ui.styles import IconManager
from typing import Any


class QuotationDialog(QDialog):
    def __init__(self, clients: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Nouveau Devis')
        self.setWindowIcon(IconManager.get_quotation_icon())
        self.setMinimumWidth(800)
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
        
        # Référence
        self.ref_edit = QLineEdit(); self.ref_edit.setPlaceholderText('Ex: DEV-2025-001')
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
            header.setSectionResizeMode(0, header.ResizeMode.Interactive)
            header.setSectionResizeMode(1, header.ResizeMode.Interactive)
            header.setSectionResizeMode(2, header.ResizeMode.Interactive)
            header.setSectionResizeMode(3, header.ResizeMode.Interactive)
            header.setSectionResizeMode(4, header.ResizeMode.Interactive)
            header.setSectionResizeMode(5, header.ResizeMode.Interactive)
            header.setSectionResizeMode(6, header.ResizeMode.Interactive)
            header.setSectionResizeMode(7, header.ResizeMode.Interactive)
            header.setSectionResizeMode(8, header.ResizeMode.Interactive)
            header.setSectionResizeMode(9, header.ResizeMode.Interactive)
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
        add_btn = QPushButton('Ajouter ligne'); add_btn.clicked.connect(self._add_item_row)
        del_btn = QPushButton('Supprimer ligne'); del_btn.clicked.connect(self._remove_selected_rows)
        row_btns.addStretch(1); row_btns.addWidget(add_btn); row_btns.addWidget(del_btn)
        layout.addLayout(row_btns)
        
        # Add one default row
        self._add_item_row()

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
        
        # Couleur
        color = QComboBox(); color.addItem('Blanc', BoxColor.BLANC); color.addItem('Brun', BoxColor.BRUN)
        self.items_table.setCellWidget(row, 4, color)
        
        # Type carton
        ctype = QLineEdit(); ctype.setPlaceholderText('Ex: Double cannelure BC 7mm'); self.items_table.setCellWidget(row, 5, ctype)
        
        # Cliché
        cliche = QComboBox(); cliche.addItems(['Sans', 'Avec']); self.items_table.setCellWidget(row, 6, cliche)
        
        # Quantité
        qty = QSpinBox(); qty.setRange(1, 100000); qty.setValue(100); self.items_table.setCellWidget(row, 7, qty)
        
        # PU
        unit = QLineEdit(); unit.setPlaceholderText('0.00'); unit.setText('50.00'); self.items_table.setCellWidget(row, 8, unit)
        
        # Total (read-only)
        total = QLineEdit(); total.setReadOnly(True); self.items_table.setCellWidget(row, 9, total)
        
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
            if isinstance(total_w, QLineEdit): total_w.setText(f"{total:.2f}")
        except Exception:
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
            'reference': self.ref_edit.text().strip(),
            'client_id': self.client_combo.currentData(),
            'issue_date': self.issue_date_edit.date().toPyDate(),
            'valid_until': self.valid_until_edit.date().toPyDate(),
            'line_items': items,
            'notes': self.notes_edit.toPlainText().strip()
        }

__all__ = ['QuotationDialog']
