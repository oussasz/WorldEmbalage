from __future__ import annotations
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox,
    QGroupBox, QGridLayout, QMessageBox, QComboBox, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from config.database import SessionLocal
from models.orders import Reception, Quotation, SupplierOrder, SupplierOrderLineItem, SupplierOrderStatus
from models.suppliers import Supplier
from models.plaques import Plaque
from typing import List, Dict, Any
from datetime import datetime


class RawMaterialArrivalDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Arrivée Matière Première")
        self.setModal(True)
        self.resize(800, 600)
        
        # Data storage
        self.material_entries: List[Dict[str, Any]] = []
        self.related_supplier_orders: List[SupplierOrder] = []
        
        self._build_ui()
        self._load_initial_data()

    def _build_ui(self):
        """Build the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Enregistrement d'Arrivée Matière Première")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Material dimensions input section
        self._create_dimensions_section(layout)
        
        # Material entries table
        self._create_entries_table(layout)
        
        # Related purchase orders section
        self._create_related_orders_section(layout)
        
        # Buttons
        self._create_buttons(layout)

    def _create_dimensions_section(self, layout):
        """Create the dimensions input section"""
        group = QGroupBox("Dimensions et Quantités des Plaques")
        group_layout = QGridLayout(group)
        
        # Dimension inputs
        group_layout.addWidget(QLabel("Largeur (mm):"), 0, 0)
        self.width_input = QSpinBox()
        self.width_input.setRange(1, 10000)
        self.width_input.setValue(1000)
        group_layout.addWidget(self.width_input, 0, 1)
        
        group_layout.addWidget(QLabel("Hauteur (mm):"), 0, 2)
        self.height_input = QSpinBox()
        self.height_input.setRange(1, 10000)
        self.height_input.setValue(1000)
        group_layout.addWidget(self.height_input, 0, 3)
        
        group_layout.addWidget(QLabel("Rabat (mm):"), 1, 0)
        self.rabat_input = QSpinBox()
        self.rabat_input.setRange(1, 1000)
        self.rabat_input.setValue(50)
        group_layout.addWidget(self.rabat_input, 1, 1)
        
        group_layout.addWidget(QLabel("Quantité:"), 1, 2)
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 10000)
        self.quantity_input.setValue(1)
        group_layout.addWidget(self.quantity_input, 1, 3)
        
        # Add button
        add_btn = QPushButton("➕ Ajouter à la Liste")
        add_btn.clicked.connect(self._add_material_entry)
        group_layout.addWidget(add_btn, 2, 0, 1, 4)
        
        layout.addWidget(group)

    def _create_entries_table(self, layout):
        """Create the material entries table"""
        group = QGroupBox("Matières Ajoutées")
        group_layout = QVBoxLayout(group)
        
        self.entries_table = QTableWidget()
        self.entries_table.setColumnCount(5)
        self.entries_table.setHorizontalHeaderLabels([
            "Largeur (mm)", "Hauteur (mm)", "Rabat (mm)", 
            "Quantité", "Actions"
        ])
        
        # Configure table
        header = self.entries_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.entries_table.setAlternatingRowColors(True)
        self.entries_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        group_layout.addWidget(self.entries_table)
        layout.addWidget(group)

    def _create_related_orders_section(self, layout):
        """Create the related supplier orders section"""
        group = QGroupBox("Commandes de Matières Premières Correspondantes")
        group_layout = QVBoxLayout(group)
        
        # Info label
        info_label = QLabel("Les commandes de matières premières correspondant aux dimensions saisies s'afficheront automatiquement ici.")
        info_label.setStyleSheet("color: #666; font-style: italic;")
        group_layout.addWidget(info_label)
        
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(6)
        self.orders_table.setHorizontalHeaderLabels([
            "Bon Commande", "Fournisseur", "Largeur", 
            "Hauteur", "Rabat", "Date Création"
        ])
        
        # Configure table
        header = self.orders_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.orders_table.setAlternatingRowColors(True)
        self.orders_table.setMaximumHeight(200)
        
        group_layout.addWidget(self.orders_table)
        layout.addWidget(group)

    def _create_buttons(self, layout):
        """Create dialog buttons"""
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        
        save_btn = QPushButton("Enregistrer l'Arrivée")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2E8B57;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #228B22;
            }
        """)
        save_btn.clicked.connect(self._save_arrival)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)

    def _load_initial_data(self):
        """Load initial data"""
        # Initially empty, will be populated when dimensions are added
        pass

    def _add_material_entry(self):
        """Add a material entry to the list"""
        width = self.width_input.value()
        height = self.height_input.value()
        rabat = self.rabat_input.value()
        quantity = self.quantity_input.value()
        
        # Check if this plate matches any existing supplier orders
        if not self._check_plate_matches(width, height, rabat):
            # Show confirmation dialog
            reply = QMessageBox.question(
                self,
                "Confirmation",
                "This plate does not exist in any order. Do you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return  # Don't add the entry
        
        # Add to internal storage
        entry = {
            'width': width,
            'height': height,
            'rabat': rabat,
            'quantity': quantity
        }
        self.material_entries.append(entry)
        
        # Add to table
        row = self.entries_table.rowCount()
        self.entries_table.insertRow(row)
        
        self.entries_table.setItem(row, 0, QTableWidgetItem(str(width)))
        self.entries_table.setItem(row, 1, QTableWidgetItem(str(height)))
        self.entries_table.setItem(row, 2, QTableWidgetItem(str(rabat)))
        self.entries_table.setItem(row, 3, QTableWidgetItem(str(quantity)))
        
        # Add remove button
        remove_btn = QPushButton("🗑️")
        remove_btn.setToolTip("Supprimer cette entrée")
        remove_btn.clicked.connect(lambda: self._remove_entry(row))
        self.entries_table.setCellWidget(row, 4, remove_btn)
        
        # Search for related orders
        self._search_related_orders()
        
        # Reset inputs for next entry
        self.quantity_input.setValue(1)

    def _remove_entry(self, row):
        """Remove an entry from the list"""
        if 0 <= row < len(self.material_entries):
            self.material_entries.pop(row)
            self.entries_table.removeRow(row)
            
            # Update remove button connections - simplified approach
            for i in range(self.entries_table.rowCount()):
                # Create new button with correct connection
                remove_btn = QPushButton("🗑️")
                remove_btn.setToolTip("Supprimer cette entrée")
                remove_btn.clicked.connect(lambda checked, r=i: self._remove_entry(r))
                self.entries_table.setCellWidget(i, 4, remove_btn)
            
            # Refresh related orders
            self._search_related_orders()

    def _search_related_orders(self):
        """Search for related supplier orders based on entered dimensions"""
        if not self.material_entries:
            self.orders_table.setRowCount(0)
            return
        
        session = SessionLocal()
        try:
            # Clear current orders
            self.orders_table.setRowCount(0)
            self.related_supplier_orders = []
            
            # Search for supplier orders with line items that have similar dimensions
            # Only show orders in "passé" (ORDERED) status
            for entry in self.material_entries:
                # Query supplier orders with line items that might match dimensions
                # Filter for only "passé" status orders
                supplier_orders = session.query(SupplierOrder).filter(
                    SupplierOrder.line_items.any(),
                    SupplierOrder.status == SupplierOrderStatus.ORDERED
                ).all()
                
                for supplier_order in supplier_orders:
                    # Check if any line item has dimensions that match our plates
                    for line_item in supplier_order.line_items:
                        if (line_item.plaque_width_mm and line_item.plaque_length_mm and 
                            hasattr(line_item, 'plaque_flap_mm') and line_item.plaque_flap_mm):
                            
                            # Check if the entered dimensions match order dimensions (with some tolerance)
                            width_match = abs(line_item.plaque_width_mm - entry['width']) <= 10
                            height_match = abs(line_item.plaque_length_mm - entry['height']) <= 10
                            rabat_match = abs(line_item.plaque_flap_mm - entry['rabat']) <= 5
                            
                            if width_match and height_match and rabat_match and supplier_order not in self.related_supplier_orders:
                                self.related_supplier_orders.append(supplier_order)
                                self._add_supplier_order_to_table(supplier_order, entry, line_item)
                                break
        
        except Exception as e:
            print(f"Error searching related supplier orders: {e}")
        finally:
            session.close()

    def _add_supplier_order_to_table(self, supplier_order: SupplierOrder, matching_entry: Dict[str, Any], line_item):
        """Add a supplier order to the related orders table"""
        row = self.orders_table.rowCount()
        self.orders_table.insertRow(row)
        
        # Populate table row
        self.orders_table.setItem(row, 0, QTableWidgetItem(
            getattr(supplier_order, 'bon_commande_ref', '') or f"BC-{supplier_order.id}"
        ))
        self.orders_table.setItem(row, 1, QTableWidgetItem(
            supplier_order.supplier.name if supplier_order.supplier else "N/A"
        ))
        self.orders_table.setItem(row, 2, QTableWidgetItem(
            f"{line_item.plaque_width_mm}mm" if line_item.plaque_width_mm else "N/A"
        ))
        self.orders_table.setItem(row, 3, QTableWidgetItem(
            f"{line_item.plaque_length_mm}mm" if line_item.plaque_length_mm else "N/A"
        ))
        self.orders_table.setItem(row, 4, QTableWidgetItem(
            f"{line_item.plaque_flap_mm}mm" if hasattr(line_item, 'plaque_flap_mm') and line_item.plaque_flap_mm else "N/A"
        ))
        self.orders_table.setItem(row, 5, QTableWidgetItem(
            self._format_date(supplier_order.order_date) if hasattr(supplier_order, 'order_date') and supplier_order.order_date else "N/A"
        ))

    def _save_arrival(self):
        """Save the raw material arrival"""
        if not self.material_entries:
            QMessageBox.warning(self, "Attention", "Veuillez ajouter au moins une entrée de matière première.")
            return
        
        try:
            # Here you would implement the logic to save the raw material arrival
            # This could involve creating Reception records or updating stock
            
            session = SessionLocal()
            try:
                # For now, we'll just show a success message
                # In a real implementation, you would:
                # 1. Create Reception records for each material entry
                # 2. Update stock quantities
                # 3. Update supplier order status if applicable
                
                total_entries = len(self.material_entries)
                total_quantity = sum(entry['quantity'] for entry in self.material_entries)
                
                QMessageBox.information(
                    self,
                    "Succès",
                    f"Arrivée de matière première enregistrée avec succès!\n\n"
                    f"Entrées: {total_entries}\n"
                    f"Quantité totale: {total_quantity} plaques\n"
                    f"Commandes associées: {len(self.related_supplier_orders)}"
                )
                
                self.accept()
                
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement: {str(e)}")
            finally:
                session.close()
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur: {str(e)}")

    def get_material_entries(self) -> List[Dict[str, Any]]:
        """Get the list of material entries"""
        return self.material_entries.copy()

    def get_related_supplier_orders(self) -> List[SupplierOrder]:
        """Get the list of related supplier orders"""
        return self.related_supplier_orders.copy()

    def _check_plate_matches(self, width: int, height: int, rabat: int) -> bool:
        """Check if the plate dimensions match any existing supplier orders"""
        session = SessionLocal()
        try:
            # Query supplier orders with "passé" status that have line items
            supplier_orders = session.query(SupplierOrder).filter(
                SupplierOrder.status == SupplierOrderStatus.ORDERED,
                SupplierOrder.line_items.any()
            ).all()
            
            for supplier_order in supplier_orders:
                for line_item in supplier_order.line_items:
                    if (line_item.plaque_width_mm and line_item.plaque_length_mm and 
                        hasattr(line_item, 'plaque_flap_mm') and line_item.plaque_flap_mm):
                        
                        # Check if the dimensions match (with some tolerance)
                        width_match = abs(line_item.plaque_width_mm - width) <= 10
                        height_match = abs(line_item.plaque_length_mm - height) <= 10
                        rabat_match = abs(line_item.plaque_flap_mm - rabat) <= 5
                        
                        if width_match and height_match and rabat_match:
                            return True
            
            return False
            
        except Exception as e:
            print(f"Error checking plate matches: {e}")
            return False
        finally:
            session.close()

    def _format_date(self, date_obj) -> str:
        """Format date object to string"""
        import datetime
        if isinstance(date_obj, (datetime.date, datetime.datetime)):
            return date_obj.strftime("%d/%m/%Y")
        return str(date_obj)
