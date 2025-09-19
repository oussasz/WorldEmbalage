from __future__ import annotations
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox,
    QGroupBox, QGridLayout, QMessageBox, QComboBox, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from config.database import SessionLocal
from models.orders import Reception, Quotation, SupplierOrder, SupplierOrderLineItem, MaterialDelivery, DeliveryStatus, SupplierOrderStatus, ClientOrder
from services.delivery_tracking_service import DeliveryTrackingService
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
        group_layout.addWidget(QLabel("Langeur(mm):"), 0, 0)
        self.width_input = QSpinBox()
        self.width_input.setRange(1, 10000)
        self.width_input.setValue(1000)
        group_layout.addWidget(self.width_input, 0, 1)
        
        group_layout.addWidget(QLabel("Largeur (mm):"), 0, 2)
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
        
        # Check if an entry with the same dimensions already exists
        existing_entry_index = self._find_existing_entry(width, height, rabat)
        
        if existing_entry_index is not None:
            # Group with existing entry - sum the quantities
            existing_entry = self.material_entries[existing_entry_index]
            existing_entry['quantity'] += quantity
            
            # Update the display table
            self.entries_table.setItem(existing_entry_index, 3, QTableWidgetItem(str(existing_entry['quantity'])))
            
            # Show grouping notification
            QMessageBox.information(
                self,
                "Matières Groupées",
                f"Quantité ajoutée à l'entrée existante.\n"
                f"Dimensions: {width}×{height}×{rabat}mm\n"
                f"Nouvelle quantité totale: {existing_entry['quantity']} plaques"
            )
        else:
            # Add new entry to internal storage
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

    def _find_existing_entry(self, width: int, height: int, rabat: int) -> int | None:
        """
        Find an existing entry with the same dimensions.
        
        Args:
            width: Width in mm
            height: Height in mm  
            rabat: Rabat in mm
            
        Returns:
            Index of existing entry if found, None otherwise
        """
        for i, entry in enumerate(self.material_entries):
            if (entry['width'] == width and 
                entry['height'] == height and 
                entry['rabat'] == rabat):
                return i
        return None

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
            # Only show orders in "passé" (ORDERED) or "partiellement livrée" (PARTIALLY_DELIVERED) status
            for entry in self.material_entries:
                # Query supplier orders with line items that might match dimensions
                # Filter for "passé" and "partiellement livrée" status orders
                supplier_orders = session.query(SupplierOrder).filter(
                    SupplierOrder.line_items.any(),
                    SupplierOrder.status.in_([SupplierOrderStatus.ORDERED, SupplierOrderStatus.PARTIALLY_DELIVERED])
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
        """Save the raw material arrival with partial delivery tracking"""
        if not self.material_entries:
            QMessageBox.warning(self, "Attention", "Veuillez ajouter au moins une entrée de matière première.")
            return
        
        try:
            session = SessionLocal()
            try:
                saved_deliveries = []
                updated_line_items = []
                supplier_orders_used = set()  # Track which supplier orders we used - initialize at method level
                # Aggregate receptions by (supplier_order_id, width, height, rabat)
                reception_aggregates: dict[tuple[int, int, int, int], int] = {}
                
                # Process each material entry
                for entry in self.material_entries:
                    # Find matching supplier order line items
                    matching_line_items = session.query(SupplierOrderLineItem).filter(
                        SupplierOrderLineItem.plaque_width_mm == entry['width'],
                        SupplierOrderLineItem.plaque_length_mm == entry['height'],
                        SupplierOrderLineItem.plaque_flap_mm == entry['rabat']
                    ).all()
                    
                    if matching_line_items:
                        # If there are matches, distribute the received quantity
                        remaining_quantity = entry['quantity']
                        
                        for line_item in matching_line_items:
                            if remaining_quantity <= 0:
                                break
                                
                            # Calculate how much we can apply to this line item
                            needed_quantity = line_item.quantity - (line_item.total_received_quantity or 0)
                            if needed_quantity <= 0:
                                continue  # This line item is already complete
                                
                            applied_quantity = min(remaining_quantity, needed_quantity)
                            
                            # Track supplier order for Reception creation
                            supplier_orders_used.add(line_item.supplier_order_id)
                            # Aggregate reception quantity by (supplier_order_id, dimensions)
                            agg_key = (line_item.supplier_order_id, entry['width'], entry['height'], entry['rabat'])
                            reception_aggregates[agg_key] = reception_aggregates.get(agg_key, 0) + applied_quantity
                            
                            # Create delivery record
                            try:
                                delivery = MaterialDelivery(
                                    supplier_order_line_item_id=line_item.id,
                                    received_quantity=applied_quantity,
                                    batch_reference=f"ARR-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                                    quality_notes=""
                                )
                                session.add(delivery)
                                saved_deliveries.append(delivery)
                                
                                # Update line item totals
                                line_item.total_received_quantity = (line_item.total_received_quantity or 0) + applied_quantity
                                
                                # Update delivery status
                                if line_item.total_received_quantity >= line_item.quantity:
                                    line_item.delivery_status = DeliveryStatus.COMPLETE
                                else:
                                    line_item.delivery_status = DeliveryStatus.PARTIAL
                                    
                                updated_line_items.append(line_item)
                                remaining_quantity -= applied_quantity
                                
                            except Exception as delivery_error:
                                # If MaterialDelivery table doesn't exist yet, skip delivery tracking
                                print(f"Delivery tracking not available: {delivery_error}")
                                # Just update the line item quantities directly
                                line_item.total_received_quantity = (line_item.total_received_quantity or 0) + applied_quantity
                                if hasattr(line_item, 'delivery_status'):
                                    if line_item.total_received_quantity >= line_item.quantity:
                                        line_item.delivery_status = DeliveryStatus.COMPLETE
                                    else:
                                        line_item.delivery_status = DeliveryStatus.PARTIAL
                                updated_line_items.append(line_item)
                                remaining_quantity -= applied_quantity

                    
                    else:
                        # No matching orders - this was already confirmed by user
                        # Aggregate unmatched reception under a default/dummy supplier order
                        key = (1, entry['width'], entry['height'], entry['rabat'])
                        reception_aggregates[key] = reception_aggregates.get(key, 0) + entry['quantity']

                # After processing all entries, update supplier orders' statuses once
                for supplier_order_id in supplier_orders_used:
                    supplier_order = session.query(SupplierOrder).filter(SupplierOrder.id == supplier_order_id).first()
                    if supplier_order:
                        # Check completion status of ALL line items
                        total_line_items = len(supplier_order.line_items)
                        completed_line_items = 0
                        partially_received_line_items = 0
                        
                        for line_item in supplier_order.line_items:
                            received_qty = getattr(line_item, 'total_received_quantity', 0) or 0
                            ordered_qty = line_item.quantity
                            
                            if received_qty >= ordered_qty:
                                # This line item is fully received
                                completed_line_items += 1
                                # Update delivery status if available
                                if hasattr(line_item, 'delivery_status'):
                                    line_item.delivery_status = DeliveryStatus.COMPLETE
                            elif received_qty > 0:
                                # This line item is partially received
                                partially_received_line_items += 1
                                # Update delivery status if available
                                if hasattr(line_item, 'delivery_status'):
                                    line_item.delivery_status = DeliveryStatus.PARTIAL
                            else:
                                # This line item hasn't been received yet
                                if hasattr(line_item, 'delivery_status'):
                                    line_item.delivery_status = DeliveryStatus.PENDING
                        
                        # Update supplier order status based on ALL line items
                        if completed_line_items == total_line_items:
                            # ALL line items are complete
                            supplier_order.status = SupplierOrderStatus.COMPLETED
                        elif completed_line_items > 0 or partially_received_line_items > 0:
                            # Some line items are complete or partial, but not all are complete
                            supplier_order.status = SupplierOrderStatus.PARTIALLY_DELIVERED
                        # If no line items have been received, keep the current status (usually ORDERED)
                        
                        print(f"Updated supplier order {supplier_order_id} status to: {supplier_order.status.value}")
                        print(f"  Line items: {completed_line_items}/{total_line_items} complete, {partially_received_line_items} partial")

                # Create a single Reception per (supplier_order_id, dimensions)
                for (supplier_order_id, w, h, r), qty in reception_aggregates.items():
                    # Get description from related quotation
                    description = f"Arrivée matière: {w}x{h}x{r}mm"  # Default fallback
                    
                    try:
                        # Find supplier order and get description from related quotation
                        supplier_order = session.query(SupplierOrder).filter(SupplierOrder.id == supplier_order_id).first()
                        if supplier_order and hasattr(supplier_order, 'line_items') and supplier_order.line_items:
                            first_line_item = supplier_order.line_items[0]
                            
                            # Find client order through client_id
                            if hasattr(first_line_item, 'client_id') and first_line_item.client_id:
                                # Look for ANY client order for this client that has a quotation with descriptions
                                # We need to be flexible since supplier_order_id linking isn't always consistent
                                client_orders = session.query(ClientOrder).filter(
                                    ClientOrder.client_id == first_line_item.client_id,
                                    ClientOrder.quotation_id.isnot(None)
                                ).all()
                                
                                for client_order in client_orders:
                                    if client_order.quotation:
                                        quotation = client_order.quotation
                                        
                                        # Try line items first (priority)
                                        if quotation.line_items:
                                            for quotation_line in quotation.line_items:
                                                if quotation_line.description and quotation_line.description.strip():
                                                    description = quotation_line.description.strip()
                                                    break  # Use first non-empty description found
                                        
                                        # Fallback to quotation notes if no line item description found
                                        if description == f"Arrivée matière: {w}x{h}x{r}mm" and quotation.notes and quotation.notes.strip():
                                            description = quotation.notes.strip()
                                        
                                        # If we found a good description, break out of client_orders loop
                                        if description != f"Arrivée matière: {w}x{h}x{r}mm":
                                            break
                    except Exception as e:
                        print(f"Warning: Could not fetch description for supplier order {supplier_order_id}: {e}")
                    
                    reception = Reception(
                        supplier_order_id=supplier_order_id,
                        quantity=qty,
                        notes=description
                    )
                    session.add(reception)
                    session.flush()  # ensure reception.id is available for linking

                    # Also log a material delivery event for history tracking
                    try:
                        so = session.query(SupplierOrder).filter(SupplierOrder.id == supplier_order_id).first()
                        target_li = None
                        if so and hasattr(so, 'line_items') and so.line_items:
                            # Prefer matching by plaque dimensions to the aggregated key (w, h, r)
                            for li in so.line_items:
                                if (
                                    getattr(li, 'plaque_width_mm', None) == w and
                                    getattr(li, 'plaque_length_mm', None) == h and
                                    getattr(li, 'plaque_flap_mm', None) == r
                                ):
                                    target_li = li
                                    break
                            if target_li is None:
                                # Fallback: first line item
                                target_li = so.line_items[0]

                            delivery = MaterialDelivery(
                                supplier_order_line_item_id=target_li.id,
                                received_quantity=qty,
                                batch_reference=f"REC-{reception.id}"
                            )
                            session.add(delivery)
                    except Exception as md_err:
                        print(f"Warning: Could not create MaterialDelivery for reception {reception.id}: {md_err}")
                
                session.commit()
                
                total_entries = len(self.material_entries)
                total_quantity = sum(entry['quantity'] for entry in self.material_entries)
                
                # Prepare status update information
                status_info = ""
                if supplier_orders_used:
                    status_info = f"\nCommandes mises à jour: {len(supplier_orders_used)}"
                    for supplier_order_id in supplier_orders_used:
                        supplier_order = session.query(SupplierOrder).filter(SupplierOrder.id == supplier_order_id).first()
                        if supplier_order:
                            status_info += f"\n  - Commande {getattr(supplier_order, 'bon_commande_ref', supplier_order_id)}: {supplier_order.status.value}"
                
                QMessageBox.information(
                    self,
                    "Succès",
                    f"Arrivée de matière première enregistrée avec succès!\n\n"
                    f"Entrées: {total_entries}\n"
                    f"Quantité totale: {total_quantity} plaques\n"
                    f"Livraisons partielles: {len(saved_deliveries)}\n"
                    f"Articles mis à jour: {len(updated_line_items)}"
                    f"{status_info}"
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
                SupplierOrder.status.in_([
                    SupplierOrderStatus.ORDERED,
                    SupplierOrderStatus.PARTIALLY_DELIVERED
                ]),
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
