from __future__ import annotations
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, 
                           QPushButton, QComboBox, QSpinBox, QTextEdit, QDateEdit, 
                           QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QColor
from typing import Optional, Any
from decimal import Decimal


class MultiPlaqueSupplierOrderDialog(QDialog):
    def __init__(self, suppliers: list, plaques: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle('Nouvelle Commande de Matière Première')
        self.setMinimumWidth(1200)
        self.setMinimumHeight(600)
        self.suppliers = suppliers
        self.plaques = plaques
        self._build_ui()
        self._populate_plaques()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Header section
        header_layout = QHBoxLayout()
        
        # Reference
        ref_layout = QVBoxLayout()
        ref_layout.addWidget(QLabel('Référence:'))
        from utils.helpers import generate_reference
        self.ref_edit = QLineEdit()
        self.ref_edit.setText(generate_reference("BC"))  # Bon de Commande
        ref_layout.addWidget(self.ref_edit)
        header_layout.addLayout(ref_layout)
        
        # Supplier
        supplier_layout = QVBoxLayout()
        supplier_layout.addWidget(QLabel('Fournisseur:'))
        self.supplier_combo = QComboBox()
        for supplier in self.suppliers:
            self.supplier_combo.addItem(supplier.name, supplier.id)
        supplier_layout.addWidget(self.supplier_combo)
        header_layout.addLayout(supplier_layout)
        
        # Order Date
        date_layout = QVBoxLayout()
        date_layout.addWidget(QLabel('Date de commande:'))
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        date_layout.addWidget(self.date_edit)
        header_layout.addLayout(date_layout)
        
        layout.addLayout(header_layout)
        
        # Plaques table
        layout.addWidget(QLabel('Plaques à commander:'))
        self.plaques_table = QTableWidget(0, 8)
        self.plaques_table.setHorizontalHeaderLabels([
            'Client', 'Dimensions (L×l×R mm)', 'Référence matière', 'Caractéristiques', 
            'Quantité', 'UTTC/plaque', 'Total', 'Notes'
        ])
        
        # Set column widths
        header = self.plaques_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Client
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Dimensions
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # Référence matière
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # Caractéristiques
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Quantité
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # UTTC/plaque
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Total
            header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)           # Notes
        
        layout.addWidget(self.plaques_table)
        
        # Total section
        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel('Total commande:'))
        self.total_label = QLabel('0.00 DA')
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        total_layout.addWidget(self.total_label)
        total_layout.addStretch()
        layout.addLayout(total_layout)
        
        # Notes
        layout.addWidget(QLabel('Notes générales:'))
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        layout.addWidget(self.notes_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton('Créer Commande')
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton('Annuler')
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def _populate_plaques(self):
        """Populate the table with plaque data"""
        self.plaques_table.setRowCount(len(self.plaques))
        
        for row, plaque in enumerate(self.plaques):
            # Client
            client_item = QTableWidgetItem(plaque['client_name'])
            client_item.setFlags(client_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make read-only
            self.plaques_table.setItem(row, 0, client_item)
            
            # Dimensions
            dimensions = f"{plaque['longueur_plaque']}×{plaque['largeur_plaque']}×{plaque['rabat_plaque']}"
            dim_item = QTableWidgetItem(dimensions)
            dim_item.setFlags(dim_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make read-only
            self.plaques_table.setItem(row, 1, dim_item)
            
            # Référence matière
            ref_item = QTableWidgetItem(plaque['material_reference'])
            self.plaques_table.setItem(row, 2, ref_item)
            
            # Caractéristiques
            char_item = QTableWidgetItem(plaque['cardboard_type'])
            self.plaques_table.setItem(row, 3, char_item)
            
            # Quantité
            qty_item = QTableWidgetItem(str(plaque['quantity']))
            qty_item.setFlags(qty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make read-only
            self.plaques_table.setItem(row, 4, qty_item)
            
            # UTTC/plaque (editable)
            uttc_item = QTableWidgetItem(str(plaque['uttc_per_plaque']))
            # Highlight empty or zero UTTC in red
            if plaque['uttc_per_plaque'] <= 0:
                uttc_item.setBackground(QColor(255, 200, 200))  # Light red background
            self.plaques_table.setItem(row, 5, uttc_item)
            
            # Total (calculated)
            total = plaque['quantity'] * plaque['uttc_per_plaque']
            total_item = QTableWidgetItem(f"{total:.2f}")
            total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make read-only
            self.plaques_table.setItem(row, 6, total_item)
            
            # Notes
            notes_item = QTableWidgetItem(f"Devis: {plaque['quotation_reference']}")
            self.plaques_table.setItem(row, 7, notes_item)
        
        # Connect item changed signal to update totals
        self.plaques_table.itemChanged.connect(self._on_item_changed)
        self._update_total()

    def _on_item_changed(self, item):
        """Handle changes to table items"""
        if item.column() == 5:  # UTTC/plaque column
            try:
                row = item.row()
                uttc_text = item.text().strip()
                
                if not uttc_text or uttc_text == "0" or uttc_text == "0.00":
                    # Highlight empty or zero UTTC in red
                    item.setBackground(QColor(255, 200, 200))  # Light red background
                    uttc = 0.0
                else:
                    uttc = float(uttc_text)
                    if uttc <= 0:
                        # Highlight negative or zero values in red
                        item.setBackground(QColor(255, 200, 200))  # Light red background
                    else:
                        # Clear highlighting for valid values
                        item.setBackground(QColor(255, 255, 255))  # White background
                
                quantity_item = self.plaques_table.item(row, 4)
                if quantity_item is not None:
                    quantity = int(quantity_item.text())
                    total = uttc * quantity
                    
                    # Update total column
                    total_item = self.plaques_table.item(row, 6)
                    if total_item is not None:
                        total_item.setText(f"{total:.2f}")
                
                # Update overall total
                self._update_total()
            except (ValueError, TypeError):
                # Reset to 0 if invalid input and highlight in red
                item.setText("0.00")
                item.setBackground(QColor(255, 200, 200))  # Light red background

    def _update_total(self):
        """Update the total command amount"""
        total = 0.0
        for row in range(self.plaques_table.rowCount()):
            total_item = self.plaques_table.item(row, 6)
            if total_item and total_item.text():
                try:
                    total += float(total_item.text())
                except (ValueError, TypeError):
                    pass
        
        self.total_label.setText(f"{total:.2f} DA")

    def get_data(self) -> dict:
        """Get the dialog data including all plaques"""
        plaques_data = []
        
        for row in range(self.plaques_table.rowCount()):
            # Get original plaque data
            original_plaque = self.plaques[row]
            
            # Get updated values from table
            ref_item = self.plaques_table.item(row, 2)
            char_item = self.plaques_table.item(row, 3)
            uttc_item = self.plaques_table.item(row, 5)
            notes_item = self.plaques_table.item(row, 7)
            
            plaque_data = {
                'client_id': original_plaque['client_id'],
                'client_name': original_plaque['client_name'],
                'description': original_plaque['description'],
                'largeur_plaque': original_plaque['largeur_plaque'],
                'longueur_plaque': original_plaque['longueur_plaque'],
                'rabat_plaque': original_plaque['rabat_plaque'],
                'quantity': original_plaque['quantity'],
                'material_reference': ref_item.text() if ref_item else '',
                'cardboard_type': char_item.text() if char_item else '',
                'uttc_per_plaque': float(uttc_item.text()) if uttc_item else 0.0,
                'notes': notes_item.text() if notes_item else '',
                'quotation_reference': original_plaque['quotation_reference']
            }
            plaques_data.append(plaque_data)
        
        return {
            'reference': self.ref_edit.text().strip(),
            'supplier_id': self.supplier_combo.currentData(),
            'order_date': self.date_edit.date().toPyDate(),
            'plaques': plaques_data,
            'notes': self.notes_edit.toPlainText().strip()
        }

    def accept(self):
        """Override accept to validate data before closing"""
        from PyQt6.QtWidgets import QMessageBox
        
        # Validate reference
        if not self.ref_edit.text().strip():
            QMessageBox.warning(self, 'Erreur', 'Veuillez saisir une référence de commande.')
            return
        
        # Validate supplier selection
        if not self.supplier_combo.currentData():
            QMessageBox.warning(self, 'Erreur', 'Veuillez sélectionner un fournisseur.')
            return
        
        # Validate UTTC fields
        empty_uttc_rows = []
        for row in range(self.plaques_table.rowCount()):
            uttc_item = self.plaques_table.item(row, 5)
            if uttc_item:
                try:
                    uttc_value = float(uttc_item.text())
                    if uttc_value <= 0:
                        empty_uttc_rows.append(row + 1)
                except (ValueError, TypeError):
                    empty_uttc_rows.append(row + 1)
            else:
                empty_uttc_rows.append(row + 1)
        
        if empty_uttc_rows:
            QMessageBox.warning(self, 'Validation', 
                f'Veuillez remplir les prix UTTC/plaque pour les lignes: {", ".join(map(str, empty_uttc_rows))}\n\n'
                'Les champs UTTC/plaque sont obligatoires et doivent être supérieurs à 0.')
            return
        
        # If all validations pass, call parent accept
        super().accept()
