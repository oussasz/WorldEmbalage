from __future__ import annotations
import datetime
import os
import subprocess
from decimal import Decimal
from pathlib import Path
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QMenuBar, QMenu, QMessageBox, QTabWidget, QToolBar, QLineEdit, QStatusBar, QDialog
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QSize
from config.database import SessionLocal
from models.suppliers import Supplier
from models.clients import Client
from models.orders import ClientOrder, SupplierOrder
from models.orders import SupplierOrderStatus, ClientOrderStatus, Reception, Quotation
from models.production import ProductionBatch
from ui.dialogs.supplier_dialog import SupplierDialog
from ui.dialogs.client_dialog import ClientDialog
from ui.dialogs.raw_material_order_dialog import RawMaterialOrderDialog
from ui.dialogs.quotation_dialog import QuotationDialog
from ui.dialogs.edit_quotation_dialog import EditQuotationDialog
from ui.dialogs.reception_dialog import ReceptionDialog
from ui.dialogs.production_dialog import ProductionDialog
from ui.widgets.data_grid import DataGrid
from ui.widgets.dashboard import Dashboard
from ui.styles import IconManager
from services.order_service import OrderService
from services.pdf_form_filler import PDFFormFiller, PDFFillError
from typing import cast, Any
from models.orders import QuotationLineItem, ClientOrderLineItem


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('World Embalage - Gestion Atelier Carton')
        self.setWindowIcon(IconManager.create_text_icon("WE", bg_color="#2C3E50"))
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the main UI structure."""
        from ui.styles import IconManager
        from PyQt6.QtCore import QSize
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add app header with logo and name
        self._create_app_header(layout)
        
        # Content layout with margins
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)
        layout.addWidget(content_widget)
        
        # Menu bar
        self._create_menu_bar()
        
        # Toolbar with search
        self._create_toolbar()
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setIconSize(QSize(20, 20)) # Set icon size for tabs
        content_layout.addWidget(self.tab_widget)
        
        # Create dashboard
        self.dashboard = Dashboard()
        self.tab_widget.addTab(self.dashboard, IconManager.get_dashboard_icon(), "Tableau de Bord")
        
        # Create data grids for different entities
        self._create_data_grids()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("World Embalage - Prêt")
        
        # Resize window
        self.resize(1400, 800)
        
        # Load initial data
        self.refresh_all()

    def _create_app_header(self, layout) -> None:
        """Create the app header with logo and name"""
        from pathlib import Path
        from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget, QVBoxLayout
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import Qt
        
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-bottom: 1px solid #DADFE3; /* Light gray border */
                padding: 5px 0;
            }
            QLabel {
                background-color: transparent;
            }
        """)
        
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 5, 15, 5)
        header_layout.setSpacing(15)
        
        # App logo
        logo_label = QLabel()
        logo_path = Path(__file__).resolve().parent.parent.parent / 'LOGO.jpg'
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            scaled_pixmap = pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setFixedSize(50, 50)
        else:
            # Fallback text logo for white background
            logo_label.setText("WE")
            logo_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50; background-color: #f0f0f0; border-radius: 25px;")
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_label.setFixedSize(50, 50)
        
        # App name and subtitle with dark text
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        app_name = QLabel("World Embalage")
        app_name.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        
        app_subtitle = QLabel("Gestion complette et robuste")
        app_subtitle.setStyleSheet("font-size: 12px; color: #555555;")
        
        title_layout.addWidget(app_name)
        title_layout.addWidget(app_subtitle)
        
        header_layout.addWidget(logo_label)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        layout.addWidget(header_widget)

    def _create_menu_bar(self) -> None:
        """Create the application menu bar."""
        menubar = self.menuBar()
        if menubar is None:
            return

        # File menu
        file_menu = menubar.addMenu('&Fichier')
        if file_menu:
            quit_action = QAction('&Quitter', self)
            quit_action.setShortcut('Ctrl+Q')
            quit_action.triggered.connect(self.close)
            file_menu.addAction(quit_action)

        # Data menu
        data_menu = menubar.addMenu('&Données')
        if data_menu:
            from ui.styles import IconManager
            
            suppliers_action = QAction('&Fournisseurs', self)
            suppliers_action.setIcon(IconManager.get_supplier_icon())
            suppliers_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
            data_menu.addAction(suppliers_action)

            clients_action = QAction('&Clients', self)
            clients_action.setIcon(IconManager.get_client_icon())
            clients_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))
            data_menu.addAction(clients_action)

            orders_action = QAction('Devis', self)
            orders_action.setIcon(IconManager.get_quotation_icon())
            orders_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(3))
            data_menu.addAction(orders_action)

    def _create_toolbar(self) -> None:
        """Create the main toolbar."""
        from ui.styles import IconManager
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Search field with proper icon
        search_label = QLabel("Recherche:")
        search_label.setStyleSheet("padding: 5px; font-weight: bold;")
        toolbar.addWidget(search_label)
        
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Rechercher...")
        self.search_field.setMaximumWidth(250)
        toolbar.addWidget(self.search_field)
        
        toolbar.addSeparator()
        
        # Refresh action with proper icon
        refresh_action = QAction('Actualiser', self)
        refresh_action.setIcon(IconManager.get_refresh_icon())
        refresh_action.setToolTip('Actualiser toutes les données')
        refresh_action.triggered.connect(self.refresh_all)
        toolbar.addAction(refresh_action)

    def _create_data_grids(self) -> None:
        """Create data grids for each entity type."""
        # Suppliers tab
        self.suppliers_grid = DataGrid(
            ["ID", "Nom", "Contact", "Téléphone", "Email", "Adresse"]
        )
        self.suppliers_grid.add_action_button("➕ Nouveau", self._new_supplier)
        self.tab_widget.addTab(self.suppliers_grid, IconManager.get_supplier_icon(), "Fournisseurs")
        
        # Clients tab
        self.clients_grid = DataGrid(
            ["ID", "Nom", "Contact", "Téléphone", "Email", "Adresse"]
        )
        self.clients_grid.add_action_button("➕ Nouveau", self._new_client)
        self.tab_widget.addTab(self.clients_grid, IconManager.get_client_icon(), "Clients")
        
        # Orders tab with enhanced context menu
        self.orders_grid = DataGrid(
            ["ID", "Référence", "Client", "Date", "Statut", "Dimensions", "Quantités", "Total (DA)", "Notes"]
        )
        self.orders_grid.add_action_button("➕ Devis", self._new_quotation)
        
        # Setup context menu for orders
        self._setup_context_menus()
        
        self.tab_widget.addTab(self.orders_grid, IconManager.get_quotation_icon(), "Devis")
        
        # Supplier Orders tab
        self.supplier_orders_grid = DataGrid(
            ["ID", "Référence", "Fournisseur", "Statut", "Date"]
        )
        self.supplier_orders_grid.add_action_button("➕ Nouvelle", self._new_supplier_order)
        self.tab_widget.addTab(self.supplier_orders_grid, IconManager.get_supplier_order_icon(), "Cmd. Fournisseurs")
        
        # Receptions tab
        self.receptions_grid = DataGrid(
            ["ID", "Référence", "Commande", "Date", "Statut"]
        )
        self.receptions_grid.add_action_button("➕ Nouvelle", self._new_reception)
        self.tab_widget.addTab(self.receptions_grid, IconManager.get_reception_icon(), "Réceptions")
        
        # Production tab
        self.production_grid = DataGrid(
            ["ID", "Référence", "Commande", "Date début", "Statut", "Quantité"]
        )
        self.production_grid.add_action_button("➕ Nouveau", self._new_production)
        self.tab_widget.addTab(self.production_grid, IconManager.get_production_icon(), "Production")

    def _setup_context_menus(self):
        """Setup context menus for data grids"""
        # Orders context menu - static actions only
        self.orders_grid.add_context_action("edit", "Modifier devis")
        self.orders_grid.add_context_action("print", "Imprimer devis")
        self.orders_grid.add_context_action("delete", "Supprimer devis")
        # Note: create_supplier_order is added dynamically based on devis type
        
        # Connect context menu signals
        self.orders_grid.contextMenuActionTriggered.connect(self._handle_orders_context_menu)
        self.orders_grid.contextMenuAboutToShow.connect(self._customize_orders_context_menu)

    def _customize_orders_context_menu(self, row: int, row_data: list, menu):
        """Customize context menu based on quotation type"""
        from PyQt6.QtGui import QAction
        
        if not row_data or len(row_data) < 5:
            return
        
        # Status is in column 4 (index 4): "Devis Initial" or "Devis Final"
        status = row_data[4] if len(row_data) > 4 else ""
        
        # Only add "Créer commande matières" for Final Devis
        if status == "Devis Final":
            # Add separator if there are already actions
            if menu.actions():
                menu.addSeparator()
            
            # Add dynamic action for creating supplier order
            action = QAction("Créer commande matières", self)
            action.triggered.connect(lambda checked: 
                                   self.orders_grid.contextMenuActionTriggered.emit("create_supplier_order", row, row_data))
            menu.addAction(action)

    def _handle_orders_context_menu(self, action_name: str, row: int, row_data: list):
        """Handle context menu actions for orders grid (quotations only)"""
        if not row_data or len(row_data) < 2:
            return
            
        # Extract order information: ID, Reference (no Type column anymore)
        order_id_str = row_data[0]
        reference = row_data[1] if len(row_data) > 1 else ""
        
        if not order_id_str:
            return
            
        try:
            order_id = int(order_id_str)
        except (ValueError, TypeError):
            return
        
        # Since we only show quotations now, all actions are for quotations
        if action_name == "edit":
            self._edit_quotation_by_id(order_id, reference)
        elif action_name == "print":
            self._print_quotation_by_id(order_id, reference)
        elif action_name == "delete":
            self._delete_quotation_by_id(order_id, reference)
        elif action_name == "create_supplier_order":
            # Check if this is a Final Devis before allowing supplier order creation
            if len(row_data) > 4 and row_data[4] == "Devis Final":
                self._create_supplier_order_for_quotation(order_id, reference)
            else:
                QMessageBox.information(self, 'Information', 
                                      'Les commandes de matières premières ne peuvent être créées que pour les Devis Finaux.')
                
    def _create_supplier_order_for_quotation(self, quotation_id: int, reference: str):
        """Create a supplier order based on a quotation's materials with automatic dimension calculations"""
        from models.orders import Quotation, SupplierOrder
        from models.suppliers import Supplier
        from ui.dialogs.supplier_order_dialog import SupplierOrderDialog
        from datetime import date
        
        session = SessionLocal()
        try:
            # Get the quotation
            quotation = session.query(Quotation).filter(Quotation.id == quotation_id).first()
            if not quotation:
                QMessageBox.warning(self, 'Erreur', f'Devis {reference} introuvable')
                return
            
            # Check if it's a Final Devis
            if quotation.is_initial:
                QMessageBox.information(self, 'Information', 
                                      'Les commandes de matières premières ne peuvent être créées que pour les Devis Finaux.')
                return
            
            # Get suppliers for the dialog
            suppliers = session.query(Supplier).all()
            if not suppliers:
                QMessageBox.warning(self, 'Erreur', 'Aucun fournisseur disponible. Créez d\'abord un fournisseur.')
                return
            
            # Calculate plaque dimensions and collect carton types
            plaque_calculations = []
            carton_types = set()
            total_quantity = 0
            
            for line_item in quotation.line_items:
                # Extract dimensions (in mm) with defaults for None values
                largeur_caisse = line_item.width_mm or 0  # l (width)
                longueur_caisse = line_item.length_mm or 0  # L (length) 
                hauteur_caisse = line_item.height_mm or 0  # H (height)
                
                # Skip items without proper dimensions
                if largeur_caisse == 0 or longueur_caisse == 0 or hauteur_caisse == 0:
                    continue
                
                # Calculate plaque dimensions
                # La largeur de plaque = largeur de caisse + hauteur de caisse
                largeur_plaque = largeur_caisse + hauteur_caisse
                
                # La longueur de plaque = (largeur de caisse + longueur de carton) * 2
                longueur_plaque = (largeur_caisse + longueur_caisse) * 2
                
                # Rabat de plaque = hauteur de caisse / 2
                rabat_plaque = hauteur_caisse / 2
                
                # Extract numeric quantity
                import re
                qty_text = str(line_item.quantity)
                numbers = re.findall(r'\d+', qty_text)
                numeric_quantity = int(numbers[-1]) if numbers else 1
                total_quantity += numeric_quantity
                
                # Collect carton type
                if line_item.cardboard_type:
                    carton_types.add(line_item.cardboard_type)
                
                plaque_calculations.append({
                    'description': line_item.description,
                    'largeur_plaque': largeur_plaque,
                    'longueur_plaque': longueur_plaque,
                    'rabat_plaque': rabat_plaque,
                    'quantity': numeric_quantity,
                    'carton_type': line_item.cardboard_type
                })
            
            if not plaque_calculations:
                QMessageBox.warning(self, 'Erreur', 'Aucun élément trouvé dans le devis pour calculer les dimensions.')
                return
            
            # For multiple items, use the largest dimensions to ensure all items can be cut from the same plaque
            max_largeur = max(calc['largeur_plaque'] for calc in plaque_calculations)
            max_longueur = max(calc['longueur_plaque'] for calc in plaque_calculations)
            max_rabat = max(calc['rabat_plaque'] for calc in plaque_calculations)
            
            # Get the most common carton type, or combine if multiple types
            if len(carton_types) == 1:
                carton_type = list(carton_types)[0]
            elif len(carton_types) > 1:
                carton_type = " + ".join(sorted(carton_types))
            else:
                carton_type = "Carton standard"
            
            # Create supplier order dialog
            dlg = SupplierOrderDialog(suppliers, self)
            dlg.setWindowTitle(f'Créer commande matières pour {reference}')
            
            # Pre-fill ALL fields with calculated values
            from utils.helpers import generate_reference
            dlg.ref_edit.setText(generate_reference("CMD"))  # Standardized reference generation
            dlg.material_edit.setText(carton_type)
            dlg.length_spin.setValue(int(max_longueur))  # Calculated plaque length
            dlg.width_spin.setValue(int(max_largeur))    # Calculated plaque width
            dlg.rabat_spin.setValue(int(max_rabat))      # Calculated rabat
            dlg.quantity_spin.setValue(total_quantity)   # Total quantity needed
            
            # Pre-fill notes with detailed calculations
            calculation_details = f"Commande générée depuis le devis {reference}\n\n"
            calculation_details += "Calculs détaillés des plaques:\n"
            for i, calc in enumerate(plaque_calculations, 1):
                calculation_details += f"\nArticle {i}: {calc['description']}\n"
                calculation_details += f"- Largeur plaque: {calc['largeur_plaque']} mm\n"
                calculation_details += f"- Longueur plaque: {calc['longueur_plaque']} mm\n"
                calculation_details += f"- Rabat plaque: {calc['rabat_plaque']} mm\n"
                calculation_details += f"- Quantité: {calc['quantity']}\n"
                calculation_details += f"- Type carton: {calc['carton_type']}\n"
            
            calculation_details += f"\nDimensions maximales retenues:\n"
            calculation_details += f"Longueur: {max_longueur} mm, Largeur: {max_largeur} mm\n"
            calculation_details += f"Quantité totale: {total_quantity}"
            
            dlg.notes_edit.setPlainText(calculation_details)
            
            if dlg.exec():
                data = dlg.get_data()
                
                # Create supplier order
                supplier_order = SupplierOrder(
                    supplier_id=data['supplier_id'],
                    reference=data['reference'],
                    order_date=data['order_date'],
                    notes=data['notes']
                )
                
                session.add(supplier_order)
                session.commit()
                
                QMessageBox.information(self, 'Succès', 
                                      f'Commande matières créée avec succès!\n\n'
                                      f'Référence: {data["reference"]}\n'
                                      f'Matériau: {data["material_type"]}\n'
                                      f'Dimensions calculées automatiquement:\n'
                                      f'  • Longueur: {data["length_mm"]} mm\n'
                                      f'  • Largeur: {data["width_mm"]} mm\n'
                                      f'  • Rabat: {data["rabat_mm"]} mm\n'
                                      f'Quantité totale: {data["quantity"]}')
                self.dashboard.add_activity("M", f"Commande matières créée depuis {reference}", "#28A745")
                self.refresh_all()
                
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de la création de la commande: {str(e)}')
        finally:
            session.close()

    def _new_supplier(self) -> None:
        """Open dialog to create a new supplier."""
        dlg = SupplierDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            session = SessionLocal()
            try:
                supplier = Supplier(**data)
                session.add(supplier)
                session.commit()
                QMessageBox.information(self, 'Succès', f'Fournisseur {data["name"]} créé')
                self.dashboard.add_activity("F", f"Nouveau fournisseur: {data['name']}", "#17A2B8")
                self.refresh_all()
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, 'Erreur', f'Erreur lors de la création: {str(e)}')
            finally:
                session.close()

    def _new_client(self) -> None:
        """Open dialog to create a new client."""
        dlg = ClientDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            session = SessionLocal()
            try:
                client = Client(**data)
                session.add(client)
                session.commit()
                QMessageBox.information(self, 'Succès', f'Client {data["name"]} créé')
                self.dashboard.add_activity("C", f"Nouveau client: {data['name']}", "#28A745")
                self.refresh_all()
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, 'Erreur', f'Erreur lors de la création: {str(e)}')
            finally:
                session.close()

    def _new_supplier_order(self) -> None:
        """Open dialog to create a new supplier order."""
        # For standalone supplier orders, redirect to context menu workflow
        QMessageBox.information(
            self, 
            'Information', 
            'Pour créer une commande matières avec calculs automatiques:\n\n'
            '1. Allez dans l\'onglet "Commandes"\n'
            '2. Clic droit sur une commande client\n'
            '3. Sélectionnez "Créer commande matières"\n\n'
            'Les dimensions des plaques seront calculées automatiquement.'
        )

    def _new_quotation(self) -> None:
        """Open dialog to create a new quotation."""
        session = SessionLocal()
        try:
            clients = session.query(Client).all()
            if not clients:
                QMessageBox.warning(self, 'Attention', 'Aucun client disponible. Créez d\'abord un client.')
                return
            
            dlg = QuotationDialog(clients, self)
            if dlg.exec():
                data = dlg.get_data()
                line_items_data = data['line_items']
                
                # Validation
                if not data['reference']:
                    QMessageBox.warning(self, 'Validation', 'Référence requise')
                    return
                if not line_items_data:
                    QMessageBox.warning(self, 'Validation', 'Au moins un article requis')
                    return
                
                # Create quotation
                quotation = Quotation(
                    reference=data['reference'],
                    client_id=data['client_id'],
                    issue_date=data['issue_date'],
                    valid_until=data['valid_until'],
                    is_initial=data.get('is_initial', False),
                    notes=data['notes']
                )
                session.add(quotation)
                session.flush()  # Get quotation ID
                
                # Create line items
                total_amount = Decimal('0')
                for idx, item_data in enumerate(line_items_data, start=1):
                    unit_price = Decimal(str(item_data['unit_price']))
                    quantity_str = str(item_data['quantity'])
                    
                    # Extract numeric quantity for calculations
                    import re
                    numbers = re.findall(r'\d+', quantity_str)
                    numeric_quantity = int(numbers[-1]) if numbers else 0
                    total_price = unit_price * numeric_quantity
                    
                    line_item = QuotationLineItem(
                        quotation_id=quotation.id,
                        line_number=idx,
                        description=item_data['description'],
                        quantity=quantity_str,  # Store original string
                        unit_price=unit_price,
                        total_price=total_price,
                        length_mm=item_data.get('length_mm'),
                        width_mm=item_data.get('width_mm'),
                        height_mm=item_data.get('height_mm'),
                        color=item_data.get('color'),
                        cardboard_type=item_data.get('cardboard_type'),
                        is_cliche=item_data.get('is_cliche', False)
                    )
                    session.add(line_item)
                    total_amount += total_price
                
                # Create client order
                client_order = ClientOrder(
                    client_id=data['client_id'],
                    reference=data['reference'],
                    order_date=data['issue_date'],
                    total_amount=total_amount,
                    quotation_id=quotation.id
                )
                session.add(client_order)
                session.flush()  # Get client order ID
                
                # Create order line items
                for idx, item_data in enumerate(line_items_data, start=1):
                    unit_price = Decimal(str(item_data['unit_price']))
                    quantity_str = str(item_data['quantity'])
                    
                    # Extract numeric quantity for calculations
                    import re
                    numbers = re.findall(r'\d+', quantity_str)
                    numeric_quantity = int(numbers[-1]) if numbers else 0
                    total_price = unit_price * numeric_quantity
                    
                    order_line_item = ClientOrderLineItem(
                        client_order_id=client_order.id,
                        line_number=idx,
                        description=item_data['description'],
                        quantity=quantity_str,
                        unit_price=unit_price,
                        total_price=total_price,
                        length_mm=item_data.get('length_mm'),
                        width_mm=item_data.get('width_mm'),
                        height_mm=item_data.get('height_mm'),
                        color=item_data.get('color'),
                        cardboard_type=item_data.get('cardboard_type'),
                        is_cliche=item_data.get('is_cliche', False)
                    )
                    session.add(order_line_item)
                
                session.commit()
                QMessageBox.information(self, 'Succès', f'Devis {data["reference"]} créé avec {len(line_items_data)} articles')
                self.dashboard.add_activity("D", f"Nouveau devis: {data['reference']}", "#FFC107")
                self.refresh_all()
                
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de la création: {str(e)}')
        finally:
            session.close()

    def _edit_quotation(self):
        """Placeholder for edit quotation - method for backward compatibility"""
        pass
    
    def _delete_quotation(self):
        """Placeholder for delete quotation - method for backward compatibility"""
        pass
    
    def _edit_quotation_context(self):
        """Placeholder for context menu edit quotation"""
        pass
    
    def _delete_quotation_context(self):
        """Placeholder for context menu delete quotation"""
        pass

    def _new_reception(self) -> None:
        """Open dialog to create a new reception."""
        session = SessionLocal()
        try:
            orders = session.query(SupplierOrder).filter(
                SupplierOrder.status.in_([SupplierOrderStatus.PENDING, SupplierOrderStatus.CONFIRMED])
            ).all()
            if not orders:
                QMessageBox.warning(self, 'Attention', 'Aucune commande fournisseur en attente.')
                return
                
            dlg = ReceptionDialog(orders, self)
            if dlg.exec():
                data = dlg.get_data()
                if not data['reference']:
                    QMessageBox.warning(self, 'Validation', 'Référence requise')
                    return
                reception = Reception(**data)
                session.add(reception)
                session.commit()
                QMessageBox.information(self, 'Succès', f'Réception {data["reference"]} créée')
                self.dashboard.add_activity("R", f"Nouvelle réception: {data['reference']}", "#6F42C1")
                self.refresh_all()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de la création: {str(e)}')
        finally:
            session.close()

    def _new_production(self) -> None:
        """Open dialog to create a new production batch."""
        session = SessionLocal()
        try:
            orders = session.query(ClientOrder).filter(
                ClientOrder.status.in_([ClientOrderStatus.CONFIRMED, ClientOrderStatus.IN_PRODUCTION])
            ).all()
            if not orders:
                QMessageBox.warning(self, 'Attention', 'Aucune commande client confirmée.')
                return
                
            dlg = ProductionDialog(orders, self)
            if dlg.exec():
                data = dlg.get_data()
                if not data['reference']:
                    QMessageBox.warning(self, 'Validation', 'Référence requise')
                    return
                batch = ProductionBatch(**data)
                session.add(batch)
                session.commit()
                QMessageBox.information(self, 'Succès', f'Lot de production {data["reference"]} créé')
                self.dashboard.add_activity("P", f"Nouveau lot: {data['reference']}", "#DC3545")
                self.refresh_all()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de la création: {str(e)}')
        finally:
            session.close()

    def _edit_quotation_by_id(self, order_id: int, reference: str):
        """Edit quotation by order ID"""
        session = SessionLocal()
        try:
            quotation = session.get(Quotation, order_id)
            if not quotation:
                QMessageBox.warning(self, 'Erreur', 'Devis introuvable')
                return
                
            clients = session.query(Client).all()
            dlg = EditQuotationDialog(quotation, clients, self)
            
            if dlg.exec():
                data = dlg.get_data()
                line_items_data = data['line_items']
                
                if not data.get('reference'):
                    QMessageBox.warning(self, 'Validation', 'Référence requise')
                    return
                if not line_items_data:
                    QMessageBox.warning(self, 'Validation', 'Au moins un article requis')
                    return
                
                # Update quotation
                quotation.reference = data.get('reference') or quotation.reference
                quotation.client_id = data['client_id']
                quotation.issue_date = data.get('issue_date') or quotation.issue_date
                quotation.valid_until = data['valid_until']
                quotation.notes = data['notes']
                quotation.is_initial = data.get('is_initial', False)
                
                # Delete existing line items
                for item in quotation.line_items:
                    session.delete(item)
                
                # Create new line items
                total_amount = Decimal('0')
                for idx, item_data in enumerate(line_items_data, start=1):
                    unit_price = Decimal(str(item_data['unit_price']))
                    quantity_str = str(item_data['quantity'])
                    
                    # Extract numeric quantity for calculations
                    import re
                    numbers = re.findall(r'\d+', quantity_str)
                    numeric_quantity = int(numbers[-1]) if numbers else 0
                    total_price = unit_price * numeric_quantity
                    
                    line_item = QuotationLineItem(
                        quotation_id=quotation.id,
                        line_number=idx,
                        description=item_data['description'],
                        quantity=quantity_str,
                        unit_price=unit_price,
                        total_price=total_price,
                        length_mm=item_data.get('length_mm'),
                        width_mm=item_data.get('width_mm'),
                        height_mm=item_data.get('height_mm'),
                        color=item_data.get('color'),
                        cardboard_type=item_data.get('cardboard_type'),
                        is_cliche=item_data.get('is_cliche', False)
                    )
                    session.add(line_item)
                    total_amount += total_price
                
                # Update quotation totals
                quotation.total_amount = total_amount  # type: ignore
                
                session.commit()
                QMessageBox.information(self, 'Succès', f'Devis {data.get("reference", "unknown")} modifié')
                self.dashboard.add_activity("M", f"Devis modifié: {data.get('reference', 'unknown')}", "#17A2B8")
                self.refresh_all()
                
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de la modification: {str(e)}')
        finally:
            session.close()

    def _print_quotation_by_id(self, order_id: int, reference: str):
        """Print quotation by generating PDF from template"""
        session = SessionLocal()
        try:
            quotation = session.get(Quotation, order_id)
            if not quotation:
                QMessageBox.warning(self, 'Erreur', 'Devis introuvable')
                return
            
            # Get quotation data for PDF
            order_service = OrderService(session)
            quotation_data = order_service.get_quotation_for_pdf(quotation.id)
            
            # Generate PDF using template
            pdf_filler = PDFFormFiller()
            try:
                output_path = pdf_filler.fill_devis_template(quotation_data)
                
                # Try to open the PDF with default system viewer
                if output_path.exists():
                    if os.name == 'nt':  # Windows
                        os.startfile(str(output_path))
                    elif os.name == 'posix':  # Linux/Unix
                        subprocess.run(['xdg-open', str(output_path)], check=False)
                    else:  # macOS
                        subprocess.run(['open', str(output_path)], check=False)
                    
                    QMessageBox.information(
                        self, 
                        'Succès', 
                        f'PDF généré avec succès:\n{output_path.name}\n\nEmplacement: {output_path.parent}'
                    )
                    self.dashboard.add_activity("P", f"PDF généré: {reference}", "#28A745")
                else:
                    QMessageBox.warning(self, 'Erreur', 'Le fichier PDF n\'a pas pu être créé')
                    
            except PDFFillError as e:
                QMessageBox.critical(self, 'Erreur PDF', f'Erreur lors de la génération du PDF:\n{str(e)}')
            except Exception as e:
                QMessageBox.critical(self, 'Erreur', f'Erreur inattendue:\n{str(e)}')
                
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de la récupération des données:\n{str(e)}')
        finally:
            session.close()

    def _delete_quotation_by_id(self, order_id: int, reference: str):
        """Delete quotation by order ID"""
        reply = QMessageBox.question(
            self, 
            'Confirmation', 
            f'Êtes-vous sûr de vouloir supprimer le devis {reference} ?\n\nCette action est irréversible.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            session = SessionLocal()
            try:
                quotation = session.get(Quotation, order_id)
                if quotation:
                    # Delete quotation and line items (cascade should handle this)
                    session.delete(quotation)
                    session.commit()
                    QMessageBox.information(self, 'Succès', f'Devis {reference} supprimé')
                    self.dashboard.add_activity("S", f"Devis supprimé: {reference}", "#DC3545")
                    self.refresh_all()
                else:
                    QMessageBox.warning(self, 'Erreur', 'Devis introuvable')
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, 'Erreur', f'Erreur lors de la suppression: {str(e)}')
            finally:
                session.close()

    def _create_supplier_order_for_client_order(self, order_id: int, reference: str):
        """Create a supplier order for raw materials based on client order"""
        session = SessionLocal()
        try:
            client_order = session.get(ClientOrder, order_id)
            if not client_order:
                QMessageBox.warning(self, 'Erreur', 'Commande introuvable')
                return
            
            # Check if this is based on an initial quotation
            if client_order.quotation and client_order.quotation.is_initial:
                QMessageBox.warning(self, 'Attention', 'Impossible de créer une commande matières premières pour un devis initial. Veuillez d\'abord spécifier les quantités.')
                return
                
            suppliers = session.query(Supplier).all()
            if not suppliers:
                QMessageBox.warning(self, 'Attention', 'Aucun fournisseur disponible. Créez d\'abord un fournisseur.')
                return
            
            dlg = RawMaterialOrderDialog(suppliers, client_order, self)
            
            if dlg.exec():
                data = dlg.get_data()
                if not data['reference']:
                    QMessageBox.warning(self, 'Validation', 'Référence requise')
                    return
                    
                # Create supplier order linked to client order
                supplier_order = SupplierOrder(
                    supplier_id=data['supplier_id'],
                    reference=data['reference'],
                    notes=f"Matières pour commande client {reference}\n"
                            f"Plaques {data['length_mm']}×{data['width_mm']}mm\n"
                            f"Type: {data['material_type']}\n"
                            f"Quantité: {data['quantity']}\n"
                            f"{data.get('notes', '')}"
                )
                session.add(supplier_order)
                session.flush()
                
                # Link client order to supplier order
                client_order.supplier_order_id = supplier_order.id
                session.commit()
                
                calc_info = ""
                if data.get('calculated_data'):
                    calc_info = f" (calculé automatiquement)"
                
                QMessageBox.information(
                    self, 
                    'Succès', 
                    f'Commande matières {data["reference"]} créée{calc_info}\n\n'
                    f'Dimensions plaque: {data["length_mm"]}×{data["width_mm"]}mm\n'
                    f'Quantité: {data["quantity"]} plaques\n'
                    f'Liée à la commande client: {reference}'
                )
                self.dashboard.add_activity("CM", f"Commande matières pour {reference}: {data['reference']}", "#6F42C1")
                self.refresh_all()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de la création: {str(e)}')
        finally:
            session.close()

    def refresh_all(self) -> None:
        """Refresh all data grids."""
        session = None
        try:
            session = SessionLocal()
            
            # Refresh suppliers
            suppliers = session.query(Supplier).all()
            suppliers_data = [
                [
                    str(s.id),
                    s.name or "",
                    getattr(s, 'contact_person', '') or "",
                    s.phone or "",
                    s.email or "",
                    s.address or "",
                ]
                for s in suppliers
            ]
            self.suppliers_grid.load_rows(suppliers_data)
            
            # Refresh clients
            clients = session.query(Client).all()
            clients_data = [
                [
                    str(c.id),
                    c.name or "",
                    getattr(c, 'contact_person', '') or "",
                    c.phone or "",
                    c.email or "",
                    c.address or "",
                ]
                for c in clients
            ]
            self.clients_grid.load_rows(clients_data)
            
            # Refresh orders (quotations only) - filter out orphaned records
            quotations = session.query(Quotation).join(Quotation.client).all()
            
            orders_data = []
            row_colors = []
            
            # Add quotations to the list
            for q in quotations:
                # Skip quotations without valid client relationships
                if not q.client:
                    continue
                    
                # Get dimensions summary from line items
                dimensions = []
                quantities = []
                for item in q.line_items:
                    if item.length_mm and item.width_mm and item.height_mm:
                        dimensions.append(f"{item.length_mm}×{item.width_mm}×{item.height_mm}")
                    quantities.append(str(item.quantity))
                
                dimensions_str = ", ".join(str(d) for d in dimensions[:2])  # Show first 2 dimensions
                if len(dimensions) > 2:
                    dimensions_str += f" (+{len(dimensions)-2})"
                
                quantities_str = ", ".join(str(q) for q in quantities[:2])  # Show first 2 quantities  
                if len(quantities) > 2:
                    quantities_str += f" (+{len(quantities)-2})"
                
                # Determine status based on type
                status = "Devis Initial" if q.is_initial else "Devis Final"
                
                orders_data.append([
                    str(q.id),
                    str(q.reference or ""),
                    str(q.client.name if q.client else "N/A"),
                    str(q.issue_date) if q.issue_date else "",
                    str(status),
                    str(dimensions_str or "N/A"),
                    str(quantities_str or "N/A"), 
                    f"{q.total_amount:,.2f}" if q.total_amount is not None else "0.00",
                    str((q.notes[:30] + "..." if q.notes and len(q.notes) > 30 else q.notes) or "")
                ])
                
                # Color coding: light blue for initial devis, light green for final devis
                if q.is_initial:
                    row_colors.append("#E3F2FD")  # Light blue for initial devis
                else:
                    row_colors.append("#E8F5E8")  # Light green for final devis
                
            self.orders_grid.load_rows_with_colors(orders_data, row_colors)
            
            # Refresh supplier orders
            supplier_orders = session.query(SupplierOrder).all()
            supplier_orders_data = [
                [
                    str(so.id),
                    so.reference or "",
                    so.supplier.name if so.supplier else "N/A",
                    so.status.value if so.status else "N/A",
                    getattr(so, 'created_date', None) and getattr(so, 'created_date').isoformat() or "",
                ]
                for so in supplier_orders
            ]
            self.supplier_orders_grid.load_rows(supplier_orders_data)
            
            # Refresh receptions
            receptions = session.query(Reception).all()
            receptions_data = [
                [
                    str(r.id),
                    getattr(r, 'reference', ''),
                    r.supplier_order.reference if r.supplier_order else "N/A",
                    getattr(r, 'reception_date', None) and getattr(r, 'reception_date').isoformat() or "",
                    getattr(r, 'status', None) and getattr(r, 'status').value or "N/A",
                ]
                for r in receptions
            ]
            self.receptions_grid.load_rows(receptions_data)
            
            # Refresh production
            production_batches = session.query(ProductionBatch).all()
            production_data = [
                [
                    str(pb.id),
                    getattr(pb, 'reference', ''),
                    getattr(pb, 'client_order', None) and getattr(getattr(pb, 'client_order'), 'reference', 'N/A') or "N/A",
                    getattr(pb, 'start_date', None) and getattr(pb, 'start_date').isoformat() or "",
                    getattr(pb, 'status', None) and getattr(pb, 'status').value or "N/A",
                    str(getattr(pb, 'quantity_produced', 0) or 0),
                ]
                for pb in production_batches
            ]
            self.production_grid.load_rows(production_data)
            
            # Update dashboard
            if hasattr(self, 'dashboard'):
                self.dashboard.refresh_data()
                
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de l\'actualisation: {str(e)}')
        finally:
            if session is not None:
                session.close()

__all__ = ['MainWindow']