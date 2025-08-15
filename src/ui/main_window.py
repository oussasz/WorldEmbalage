from __future__ import annotations
import datetime
import logging
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
from ui.dialogs.quotation_detail_dialog import QuotationDetailDialog
from ui.widgets.data_grid import DataGrid
from ui.widgets.dashboard import Dashboard
from ui.widgets.split_view import SplitView
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
            
            clients_suppliers_action = QAction('&Client et Fournisseur', self)
            clients_suppliers_action.setIcon(IconManager.get_client_icon())
            clients_suppliers_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
            data_menu.addAction(clients_suppliers_action)

            devis_action = QAction('&Devis', self)
            devis_action.setIcon(IconManager.get_quotation_icon())
            devis_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))
            data_menu.addAction(devis_action)

            material_orders_action = QAction('&Commande de matière première', self)
            material_orders_action.setIcon(IconManager.get_supplier_order_icon())
            material_orders_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(3))
            data_menu.addAction(material_orders_action)

            stock_action = QAction('&Stock', self)
            stock_action.setIcon(IconManager.get_reception_icon())
            stock_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(4))
            data_menu.addAction(stock_action)

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
        """Create data grids for each entity type with new menu structure."""
        
        # 1. Client et Fournisseur (Split view)
        self.clients_suppliers_split = SplitView(
            "Fournisseurs", ["ID", "Nom", "Contact", "Téléphone", "Email", "Adresse"],
            "Clients", ["ID", "Nom", "Contact", "Téléphone", "Email", "Adresse"]
        )
        self.clients_suppliers_split.add_left_action_button("➕ Nouveau Fournisseur", self._new_supplier)
        self.clients_suppliers_split.add_right_action_button("➕ Nouveau Client", self._new_client)
        self.tab_widget.addTab(self.clients_suppliers_split, IconManager.get_client_icon(), "Client et Fournisseur")
        
        # Store references to individual grids for refresh functionality
        self.suppliers_grid = self.clients_suppliers_split.left_grid
        self.clients_grid = self.clients_suppliers_split.right_grid
        
        # 2. Devis (Enhanced with comprehensive information)
        self.orders_grid = DataGrid(
            ["ID", "Référence", "Client", "Contact", "Date Création", "Date Validité", "Statut", 
             "Articles", "Dimensions", "Quantités", "Types Carton", "Total HT (DA)", "Notes"]
        )
        self.orders_grid.add_action_button("➕ Devis", self._new_quotation)
        
        # Connect double-click to show detail dialog
        self.orders_grid.rowDoubleClicked.connect(self._on_quotation_double_click)
        
        self.tab_widget.addTab(self.orders_grid, IconManager.get_quotation_icon(), "Devis")
        
        # 3. Commande de matière première (renamed from Cmd. Fournisseurs)
        self.supplier_orders_grid = DataGrid(
            ["ID", "Bon Commande", "Fournisseur", "Statut", "Date", "Total UTTC", "Nb Articles", "Clients"]
        )
        self.supplier_orders_grid.add_action_button("➕ Nouvelle", self._new_supplier_order)
        
        # Connect double-click to show detail dialog
        self.supplier_orders_grid.rowDoubleClicked.connect(self._on_supplier_order_double_click)
        
        self.tab_widget.addTab(self.supplier_orders_grid, IconManager.get_supplier_order_icon(), "Commande de matière première")
        
        # 4. Stock (Split view: Raw materials and Finished products)
        self.stock_split = SplitView(
            "Matières Premières", ["ID", "Type", "Référence", "Quantité", "Unité", "Fournisseur", "Date Réception"],
            "Produits Finis", ["ID", "Référence", "Description", "Quantité", "Statut", "Date Production"]
        )
        # Note: We'll use receptions for raw materials and production for finished products
        self.tab_widget.addTab(self.stock_split, IconManager.get_reception_icon(), "Stock")
        
        # Store references for refresh functionality
        self.receptions_grid = self.stock_split.left_grid  # Raw materials
        self.production_grid = self.stock_split.right_grid  # Finished products
        
        # Setup context menus after all grids are created
        self._setup_context_menus()

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
        
        # Supplier orders context menu
        self.supplier_orders_grid.add_context_action("edit", "Modifier commande")
        self.supplier_orders_grid.add_context_action("delete", "Supprimer commande")
        self.supplier_orders_grid.add_context_action("status_initial", "→ Commande Initial")
        self.supplier_orders_grid.add_context_action("status_ordered", "→ Commande Passée")
        self.supplier_orders_grid.add_context_action("status_received", "→ Commande Arrivée")
        
        # Connect supplier orders context menu signals
        self.supplier_orders_grid.contextMenuActionTriggered.connect(self._handle_supplier_orders_context_menu)
        self.supplier_orders_grid.contextMenuAboutToShow.connect(self._customize_supplier_orders_context_menu)

    def _customize_orders_context_menu(self, row: int, row_data: list, menu):
        """Customize context menu based on quotation type and selection"""
        from PyQt6.QtGui import QAction
        
        selected_rows = self.orders_grid.get_selected_row_indices()
        num_selected = len(selected_rows)
        
        # Hide single-item actions if multiple items are selected
        is_single_selection = num_selected <= 1
        for action in menu.actions():
            if action.text() in ["Modifier devis", "Imprimer devis"]:
                action.setVisible(is_single_selection)

        # Add/update actions for multi-selection
        if num_selected > 1:
            # Find existing multi-delete action or create it
            multi_delete_action = next((a for a in menu.actions() if a.text().startswith("Supprimer les")), None)
            if not multi_delete_action:
                multi_delete_action = QAction(f"Supprimer les {num_selected} devis", self)
                multi_delete_action.triggered.connect(lambda: self._handle_orders_context_menu("multi_delete", -1, []))
                menu.addAction(multi_delete_action)
            else:
                multi_delete_action.setText(f"Supprimer les {num_selected} devis")
                multi_delete_action.setVisible(True)
            
            # Hide the single delete action
            single_delete_action = next((a for a in menu.actions() if a.text() == "Supprimer devis"), None)
            if single_delete_action:
                single_delete_action.setVisible(False)
        else:
            # Ensure single delete is visible and multi-delete is hidden
            single_delete_action = next((a for a in menu.actions() if a.text() == "Supprimer devis"), None)
            if single_delete_action:
                single_delete_action.setVisible(True)
            multi_delete_action = next((a for a in menu.actions() if a.text().startswith("Supprimer les")), None)
            if multi_delete_action:
                multi_delete_action.setVisible(False)

        # Logic for "Transformer en commande de matière première"
        can_create_order = False
        if num_selected == 1:
            status = row_data[6] if len(row_data) > 6 else ""  # Column 6 is "Statut"
            if status == "Devis Final":
                can_create_order = True
        elif num_selected > 1:
            # Check if all selected are Final Devis
            all_final = True
            for r_idx in selected_rows:
                status = self.orders_grid.get_row_data(r_idx)[6]  # Column 6 is "Statut"
                if status != "Devis Final":
                    all_final = False
                    break
            if all_final:
                can_create_order = True

        # Find or create the "Transformer en commande de matière première" action
        create_order_action = next((a for a in menu.actions() if a.text().startswith("Transformer en commande")), None)
        if can_create_order:
            if not create_order_action:
                action_text = f"Transformer en commande de matière première ({num_selected} devis)" if num_selected > 1 else "Transformer en commande de matière première"
                create_order_action = QAction(action_text, self)
                create_order_action.triggered.connect(lambda: self._handle_orders_context_menu("create_supplier_order", row, row_data))
                
                # Add separator if needed
                if menu.actions() and not menu.actions()[-1].isSeparator():
                    menu.addSeparator()
                menu.addAction(create_order_action)
            else:
                create_order_action.setText(f"Transformer en commande de matière première ({num_selected} devis)" if num_selected > 1 else "Transformer en commande de matière première")
                create_order_action.setVisible(True)
        elif create_order_action:
            create_order_action.setVisible(False)

    def _on_quotation_double_click(self, row: int):
        """Handle double-click on quotation row to show detailed view"""
        row_data = []
        for col in range(self.orders_grid.table.columnCount()):
            item = self.orders_grid.table.item(row, col)
            if item:
                row_data.append(item.text())
            else:
                row_data.append('')
        
        if not row_data or len(row_data) < 2:
            return
            
        # Extract quotation ID
        quotation_id_str = row_data[0]
        if not quotation_id_str:
            return
            
        try:
            quotation_id = int(quotation_id_str)
        except (ValueError, TypeError):
            QMessageBox.warning(self, 'Erreur', 'ID de devis invalide')
            return
        
        # Get quotation from database and show detail dialog
        session = SessionLocal()
        try:
            quotation = session.get(Quotation, quotation_id)
            if not quotation:
                QMessageBox.warning(self, 'Erreur', 'Devis introuvable')
                return
                
            # Show detail dialog
            detail_dialog = QuotationDetailDialog(quotation, self)
            detail_dialog.exec()
                
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de l\'affichage des détails: {str(e)}')
        finally:
            session.close()

    def _handle_orders_context_menu(self, action_name: str, row: int, row_data: list):
        """Handle context menu actions for orders grid (quotations only)"""
        # Handle multi-selection actions
        if action_name == "multi_delete":
            self._delete_multiple_quotations()
            return
            
        # Handle multi-quotation supplier order creation
        if action_name == "create_supplier_order":
            selected_rows_data = self.orders_grid.get_selected_rows_data()
            if len(selected_rows_data) > 1:
                self._create_supplier_order_for_multiple_quotations(selected_rows_data)
                return
            # Fall through to single quotation handling
            
        # Single selection actions
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
            if len(row_data) > 6 and row_data[6] == "Devis Final":  # Column 6 is "Statut"
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
            
            # Calculate plaque dimensions and collect individual plaques
            plaques = []
            
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
                rabat_plaque = hauteur_caisse // 2  # Use integer division
                
                # Extract numeric quantity
                import re
                qty_text = str(line_item.quantity)
                numbers = re.findall(r'\d+', qty_text)
                numeric_quantity = int(numbers[-1]) if numbers else 1
                
                # Create individual plaque entry
                plaque = {
                    'client_name': quotation.client.name if quotation.client else 'Client inconnu',
                    'client_id': quotation.client_id,
                    'description': line_item.description or '',
                    'largeur_plaque': largeur_plaque,  # Largeur × Longueur × Rabat
                    'longueur_plaque': longueur_plaque,
                    'rabat_plaque': rabat_plaque,
                    'material_reference': getattr(line_item, 'material_reference', '') or '',  # Référence de matière première
                    'cardboard_type': line_item.cardboard_type or '',  # Caractéristiques
                    'quantity': numeric_quantity,  # Quantity from devis
                    'uttc_per_plaque': 0.0,  # UTTC per plaque (to be filled by user)
                    'quotation_reference': quotation.reference
                }
                plaques.append(plaque)
            
            # Create supplier order dialog with multiple plaques
            from ui.dialogs.multi_plaque_supplier_order_dialog import MultiPlaqueSupplierOrderDialog
            dlg = MultiPlaqueSupplierOrderDialog(suppliers, plaques, self)
            dlg.setWindowTitle(f'Créer commande matières pour {reference}')
            
            if dlg.exec() == QDialog.DialogCode.Accepted:
                data = dlg.get_data()
                
                # Create the supplier order
                from services.material_service import MaterialService
                material_service = MaterialService(session)
                
                try:
                    supplier_order = material_service.create_supplier_order(
                        supplier_id=data['supplier_id'],
                        bon_commande_ref=data['reference'],
                        notes=data['notes']
                    )
                    
                    # Add line items for each plaque
                    from models.orders import SupplierOrderLineItem
                    total_amount = Decimal('0')
                    
                    for line_num, plaque_data in enumerate(data['plaques'], 1):
                        line_total = Decimal(str(plaque_data['uttc_per_plaque'])) * plaque_data['quantity']
                        total_amount += line_total
                        
                        line_item = SupplierOrderLineItem(
                            supplier_order_id=supplier_order.id,
                            client_id=plaque_data['client_id'],
                            line_number=line_num,
                            code_article=f"PLQ-{line_num:03d}",  # Generate article code
                            # Caisse dimensions (from original devis)
                            caisse_length_mm=quotation.line_items[line_num-1].length_mm or 0,
                            caisse_width_mm=quotation.line_items[line_num-1].width_mm or 0,
                            caisse_height_mm=quotation.line_items[line_num-1].height_mm or 0,
                            # Plaque dimensions (calculated)
                            plaque_width_mm=plaque_data['largeur_plaque'],
                            plaque_length_mm=plaque_data['longueur_plaque'],
                            plaque_flap_mm=plaque_data['rabat_plaque'],
                            # Pricing
                            prix_uttc_plaque=Decimal(str(plaque_data['uttc_per_plaque'])),
                            quantity=plaque_data['quantity'],
                            total_line_amount=line_total,
                            # Materials
                            cardboard_type=plaque_data['cardboard_type'],
                            material_reference=plaque_data['material_reference'],
                            notes=plaque_data['notes']
                        )
                        session.add(line_item)
                    
                    # Update supplier order total
                    supplier_order.total_amount = total_amount  # type: ignore
                    session.commit()
                    
                    QMessageBox.information(self, 'Succès', 
                        f'Commande de matière première {data["reference"]} créée avec succès.\n'
                        f'Total: {total_amount:.2f} DA\n'
                        f'Plaques: {len(data["plaques"])}')
                    
                    # Refresh the supplier orders grid
                    self.refresh_all()
                    
                except Exception as e:
                    session.rollback()
                    QMessageBox.critical(self, 'Erreur', f'Erreur lors de la création de la commande: {str(e)}')
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de la création de la commande: {str(e)}')
            logging.error(f"Error creating supplier order: {e}")
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
            '3. Sélectionnez "Transformer en commande de matière première"\n\n'
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
                SupplierOrder.status.in_([SupplierOrderStatus.INITIAL, SupplierOrderStatus.ORDERED])
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

    def _delete_multiple_quotations(self):
        """Delete multiple selected quotations"""
        selected_rows_data = self.orders_grid.get_selected_rows_data()
        if not selected_rows_data:
            QMessageBox.warning(self, 'Erreur', 'Aucun devis sélectionné')
            return
            
        quotation_count = len(selected_rows_data)
        references = [row[1] for row in selected_rows_data if len(row) > 1]
        
        reply = QMessageBox.question(
            self, 
            'Confirmation', 
            f'Êtes-vous sûr de vouloir supprimer {quotation_count} devis ?\n\n'
            f'Devis: {", ".join(references[:5])}'
            f'{" et plus..." if len(references) > 5 else ""}\n\n'
            f'Cette action est irréversible.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            session = SessionLocal()
            try:
                deleted_count = 0
                deleted_refs = []
                
                for row_data in selected_rows_data:
                    if len(row_data) < 2:
                        continue
                        
                    try:
                        quotation_id = int(row_data[0])
                        reference = row_data[1]
                        
                        quotation = session.get(Quotation, quotation_id)
                        if quotation:
                            session.delete(quotation)
                            deleted_count += 1
                            deleted_refs.append(reference)
                    except (ValueError, TypeError):
                        continue
                
                if deleted_count > 0:
                    session.commit()
                    QMessageBox.information(self, 'Succès', f'{deleted_count} devis supprimés')
                    self.dashboard.add_activity("S", f"{deleted_count} devis supprimés: {', '.join(deleted_refs[:3])}", "#DC3545")
                    self.refresh_all()
                else:
                    QMessageBox.warning(self, 'Erreur', 'Aucun devis valide trouvé pour suppression')
                    
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, 'Erreur', f'Erreur lors de la suppression: {str(e)}')
            finally:
                session.close()

    def _create_supplier_order_for_multiple_quotations(self, selected_rows_data: list[list[str]]):
        """Create a single supplier order from multiple quotations using the multi-plaque dialog"""
        from models.orders import Quotation, SupplierOrder
        from models.suppliers import Supplier
        
        session = SessionLocal()
        try:
            # Get all quotations
            quotation_ids = []
            for row_data in selected_rows_data:
                if len(row_data) < 2:
                    continue
                try:
                    quotation_ids.append(int(row_data[0]))
                except (ValueError, TypeError):
                    continue
            
            if not quotation_ids:
                QMessageBox.warning(self, 'Erreur', 'Aucun devis valide sélectionné')
                return
                
            quotations = session.query(Quotation).filter(Quotation.id.in_(quotation_ids)).all()
            
            # Verify all are final devis
            non_final = [q.reference for q in quotations if q.is_initial]
            if non_final:
                QMessageBox.warning(self, 'Erreur', 
                                  f'Les devis suivants sont initiaux et ne peuvent pas être utilisés: {", ".join(non_final)}')
                return
            
            # Get suppliers
            suppliers = session.query(Supplier).all()
            if not suppliers:
                QMessageBox.warning(self, 'Erreur', 'Aucun fournisseur disponible. Créez d\'abord un fournisseur.')
                return
            
            # Calculate plaque dimensions and collect individual plaques from all quotations
            plaques = []
            
            for quotation in quotations:
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
                    rabat_plaque = hauteur_caisse // 2  # Use integer division
                    
                    # Extract numeric quantity
                    import re
                    qty_text = str(line_item.quantity)
                    numbers = re.findall(r'\d+', qty_text)
                    numeric_quantity = int(numbers[-1]) if numbers else 1
                    
                    # Create individual plaque entry
                    plaque = {
                        'client_name': quotation.client.name if quotation.client else 'Client inconnu',
                        'client_id': quotation.client_id,
                        'description': line_item.description or '',
                        'largeur_plaque': largeur_plaque,  # Largeur × Longueur × Rabat
                        'longueur_plaque': longueur_plaque,
                        'rabat_plaque': rabat_plaque,
                        'material_reference': getattr(line_item, 'material_reference', '') or '',  # Référence de matière première
                        'cardboard_type': line_item.cardboard_type or '',  # Caractéristiques
                        'quantity': numeric_quantity,  # Quantity from devis
                        'uttc_per_plaque': 0.0,  # UTTC per plaque (to be filled by user)
                        'quotation_reference': quotation.reference
                    }
                    plaques.append(plaque)
            
            if not plaques:
                QMessageBox.warning(self, 'Erreur', 'Aucune plaque valide trouvée dans les devis sélectionnés.')
                return
            
            # Create supplier order dialog with multiple plaques
            from ui.dialogs.multi_plaque_supplier_order_dialog import MultiPlaqueSupplierOrderDialog
            references = [q.reference for q in quotations]
            dlg = MultiPlaqueSupplierOrderDialog(suppliers, plaques, self)
            dlg.setWindowTitle(f'Créer commande matières pour {len(quotations)} devis: {", ".join(references)}')
            
            if dlg.exec() == QDialog.DialogCode.Accepted:
                data = dlg.get_data()
                
                # Create the supplier order
                from services.material_service import MaterialService
                material_service = MaterialService(session)
                
                try:
                    supplier_order = material_service.create_supplier_order(
                        supplier_id=data['supplier_id'],
                        bon_commande_ref=data['reference'],
                        notes=data['notes']
                    )
                    
                    # Add line items for each plaque
                    from models.orders import SupplierOrderLineItem
                    total_amount = Decimal('0')
                    
                    for line_num, plaque_data in enumerate(data['plaques'], 1):
                        line_total = Decimal(str(plaque_data['uttc_per_plaque'])) * plaque_data['quantity']
                        total_amount += line_total
                        
                        # Find original quotation line item to get caisse dimensions
                        original_quotation = next((q for q in quotations if q.reference == plaque_data['quotation_reference']), None)
                        if original_quotation and original_quotation.line_items:
                            original_line = original_quotation.line_items[0]  # Take first line item as reference
                            caisse_length = original_line.length_mm or 0
                            caisse_width = original_line.width_mm or 0
                            caisse_height = original_line.height_mm or 0
                        else:
                            caisse_length = caisse_width = caisse_height = 0
                        
                        line_item = SupplierOrderLineItem(
                            supplier_order_id=supplier_order.id,
                            client_id=plaque_data['client_id'],
                            line_number=line_num,
                            code_article=f"PLQ-{line_num:03d}",  # Generate article code
                            # Caisse dimensions (from original devis)
                            caisse_length_mm=caisse_length,
                            caisse_width_mm=caisse_width,
                            caisse_height_mm=caisse_height,
                            # Plaque dimensions (calculated)
                            plaque_width_mm=plaque_data['largeur_plaque'],
                            plaque_length_mm=plaque_data['longueur_plaque'],
                            plaque_flap_mm=plaque_data['rabat_plaque'],
                            # Pricing
                            prix_uttc_plaque=Decimal(str(plaque_data['uttc_per_plaque'])),
                            quantity=plaque_data['quantity'],
                            total_line_amount=line_total,
                            # Materials
                            cardboard_type=plaque_data['cardboard_type'],
                            material_reference=plaque_data['material_reference'],
                            notes=f"Depuis devis {plaque_data['quotation_reference']} - {plaque_data['notes']}"
                        )
                        session.add(line_item)
                    
                    # Update supplier order total
                    supplier_order.total_amount = total_amount  # type: ignore
                    session.commit()
                    
                    QMessageBox.information(self, 'Succès', 
                        f'Commande de matière première {data["reference"]} créée avec succès.\n'
                        f'Total: {total_amount:.2f} DA\n'
                        f'Plaques: {len(data["plaques"])}\n'
                        f'Devis sources: {", ".join(references)}')
                    
                    # Refresh the supplier orders grid
                    self.refresh_all()
                    
                except Exception as e:
                    session.rollback()
                    QMessageBox.critical(self, 'Erreur', f'Erreur lors de la création de la commande: {str(e)}')
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de la création de la commande: {str(e)}')
            logging.error(f"Error creating supplier order: {e}")
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
            
            # Refresh suppliers (left side of split view)
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
            self.clients_suppliers_split.load_left_data(suppliers_data)
            
            # Refresh clients (right side of split view)
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
            self.clients_suppliers_split.load_right_data(clients_data)
            
            # Refresh orders (quotations only) - filter out orphaned records
            quotations = session.query(Quotation).join(Quotation.client).all()
            
            orders_data = []
            row_colors = []
            
            # Add quotations to the list with comprehensive information
            for q in quotations:
                # Skip quotations without valid client relationships
                if not q.client:
                    continue
                    
                # Collect detailed information from line items
                line_items_count = len(q.line_items)
                dimensions = []
                quantities = []
                cardboard_types = set()
                
                for item in q.line_items:
                    # Collect dimensions
                    if item.length_mm and item.width_mm and item.height_mm:
                        dimensions.append(f"{item.length_mm}×{item.width_mm}×{item.height_mm}")
                    
                    # Collect quantities
                    quantities.append(str(item.quantity))
                    
                    # Collect cardboard types
                    if item.cardboard_type:
                        cardboard_types.add(item.cardboard_type)
                
                # Format dimensions display
                if dimensions:
                    dimensions_str = ", ".join(dimensions[:2])  # Show first 2 dimensions
                    if len(dimensions) > 2:
                        dimensions_str += f" (+{len(dimensions)-2} autres)"
                else:
                    dimensions_str = "N/A"
                
                # Format quantities display
                if quantities:
                    quantities_str = ", ".join(quantities[:2])  # Show first 2 quantities  
                    if len(quantities) > 2:
                        quantities_str += f" (+{len(quantities)-2} autres)"
                else:
                    quantities_str = "N/A"
                
                # Format cardboard types
                if cardboard_types:
                    cardboard_str = ", ".join(sorted(cardboard_types)[:2])
                    if len(cardboard_types) > 2:
                        cardboard_str += f" (+{len(cardboard_types)-2} autres)"
                else:
                    cardboard_str = "Standard"
                
                # Determine status based on type
                status = "Devis Initial" if q.is_initial else "Devis Final"
                
                # Client contact information
                client_contact = ""
                if q.client.contact_name:
                    client_contact = q.client.contact_name
                elif q.client.phone:
                    client_contact = q.client.phone
                elif q.client.email:
                    client_contact = q.client.email
                else:
                    client_contact = "N/A"
                
                # Format dates
                issue_date_str = str(q.issue_date) if q.issue_date else "N/A"
                valid_until_str = str(q.valid_until) if q.valid_until else "N/A"
                
                orders_data.append([
                    str(q.id),
                    str(q.reference or ""),
                    str(q.client.name if q.client else "N/A"),
                    str(client_contact),
                    str(issue_date_str),
                    str(valid_until_str),
                    str(status),
                    f"{line_items_count} article(s)",
                    str(dimensions_str),
                    str(quantities_str),
                    str(cardboard_str),
                    f"{q.total_amount:,.2f}" if q.total_amount is not None else "0.00",
                    str((q.notes[:25] + "..." if q.notes and len(q.notes) > 25 else q.notes) or "")
                ])
                
                # Color coding: light blue for initial devis, light green for final devis
                if q.is_initial:
                    row_colors.append("#E3F2FD")  # Light blue for initial devis
                else:
                    row_colors.append("#E8F5E8")  # Light green for final devis
                
            self.orders_grid.load_rows_with_colors(orders_data, row_colors)
            
            # Refresh supplier orders with comprehensive information
            supplier_orders = session.query(SupplierOrder).join(SupplierOrder.supplier).all()
            
            # Map internal status values to display labels
            status_display_map = {
                'commande_initial': 'Commande Initial',
                'commande_passee': 'Commande Passée', 
                'commande_arrivee': 'Commande Arrivée'
            }
            
            supplier_orders_data = []
            supplier_order_colors = []
            
            for so in supplier_orders:
                # Count line items and get unique clients
                line_items_count = len(so.line_items) if hasattr(so, 'line_items') and so.line_items else 0
                
                # Get unique clients from line items
                clients_set = set()
                if hasattr(so, 'line_items') and so.line_items:
                    for item in so.line_items:
                        if hasattr(item, 'client') and item.client:
                            clients_set.add(item.client.name)
                
                clients_display = ", ".join(sorted(clients_set)) if clients_set else "N/A"
                if len(clients_display) > 50:
                    clients_display = clients_display[:47] + "..."
                
                # Format date
                order_date_str = ""
                if so.order_date:
                    try:
                        # Import datetime to handle conversion
                        import datetime
                        if isinstance(so.order_date, datetime.date):
                            order_date_str = so.order_date.strftime("%d/%m/%Y")
                        else:
                            order_date_str = str(so.order_date)
                    except (AttributeError, TypeError):
                        order_date_str = str(so.order_date)
                
                # Format total amount
                total_amount_str = f"{so.total_amount:,.2f} {so.currency}" if hasattr(so, 'total_amount') and so.total_amount else "0.00 DZD"
                
                supplier_orders_data.append([
                    str(so.id),
                    getattr(so, 'bon_commande_ref', getattr(so, 'reference', '')) or "",  # Use new field or fallback
                    so.supplier.name if so.supplier else "N/A",
                    status_display_map.get(so.status.value if so.status else "", "N/A"),
                    order_date_str,
                    total_amount_str,
                    str(line_items_count),
                    clients_display
                ])
                
                # Color coding based on status
                status_value = so.status.value if so.status else "commande_initial"
                if status_value == "commande_initial":
                    supplier_order_colors.append("#FFF3E0")  # Light orange for initial
                elif status_value == "commande_passee":
                    supplier_order_colors.append("#E3F2FD")  # Light blue for ordered
                elif status_value == "commande_arrivee":
                    supplier_order_colors.append("#E8F5E8")  # Light green for received
                else:
                    supplier_order_colors.append("#FFFFFF")  # White for unknown status
            
            self.supplier_orders_grid.load_rows_with_colors(supplier_orders_data, supplier_order_colors)
            
            # Refresh stock - Raw materials (receptions) on left side
            receptions = session.query(Reception).all()
            receptions_data = [
                [
                    str(r.id),
                    getattr(r.supplier_order, 'notes', '') or "Matière première",  # Type
                    getattr(r, 'reference', ''),  # Reference
                    "N/A",  # Quantity (would need to be added to Reception model)
                    "unité",  # Unit
                    r.supplier_order.supplier.name if r.supplier_order and r.supplier_order.supplier else "N/A",  # Supplier
                    getattr(r, 'reception_date', None) and getattr(r, 'reception_date').isoformat() or "",  # Date
                ]
                for r in receptions
            ]
            self.stock_split.load_left_data(receptions_data)
            
            # Refresh stock - Finished products (production) on right side
            production_batches = session.query(ProductionBatch).all()
            production_data = [
                [
                    str(pb.id),
                    getattr(pb, 'reference', ''),  # Reference
                    getattr(pb, 'client_order', None) and getattr(getattr(pb, 'client_order'), 'reference', 'N/A') or "N/A",  # Description (using client order ref)
                    str(getattr(pb, 'quantity_produced', 0) or 0),  # Quantity
                    getattr(pb, 'status', None) and getattr(pb, 'status').value or "N/A",  # Status
                    getattr(pb, 'start_date', None) and getattr(pb, 'start_date').isoformat() or "",  # Date
                ]
                for pb in production_batches
            ]
            self.stock_split.load_right_data(production_data)
            
            # Update dashboard
            if hasattr(self, 'dashboard'):
                self.dashboard.refresh_data()
                
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de l\'actualisation: {str(e)}')
        finally:
            if session is not None:
                session.close()

    def _on_supplier_order_double_click(self, row: int):
        """Handle double-click on supplier order row to show detailed view"""
        row_data = []
        for col in range(self.supplier_orders_grid.table.columnCount()):
            item = self.supplier_orders_grid.table.item(row, col)
            if item:
                row_data.append(item.text())
            else:
                row_data.append('')
        
        if not row_data or len(row_data) < 2:
            return
            
        # Extract supplier order information
        order_id_str = row_data[0]
        reference = row_data[1] if len(row_data) > 1 else ""
        
        if not order_id_str:
            return
            
        try:
            order_id = int(order_id_str)
        except (ValueError, TypeError):
            return
        
        session = SessionLocal()
        try:
            supplier_order = session.query(SupplierOrder).filter(SupplierOrder.id == order_id).first()
            if not supplier_order:
                QMessageBox.warning(self, 'Erreur', f'Commande {reference} introuvable')
                return
                
            # Show detail dialog (you'll need to create SupplierOrderDetailDialog)
            from ui.dialogs.supplier_order_detail_dialog import SupplierOrderDetailDialog
            detail_dialog = SupplierOrderDetailDialog(supplier_order, self)
            detail_dialog.exec()
                
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de l\'affichage des détails: {str(e)}')
        finally:
            session.close()

    def _handle_supplier_orders_context_menu(self, action_name: str, row: int, row_data: list):
        """Handle context menu actions for supplier orders grid"""
        if not row_data or len(row_data) < 2:
            return
            
        # Extract order information: ID, Reference, Supplier, Status, Date
        order_id_str = row_data[0]
        reference = row_data[1] if len(row_data) > 1 else ""
        
        if not order_id_str:
            return
            
        try:
            order_id = int(order_id_str)
        except (ValueError, TypeError):
            return
        
        if action_name == "edit":
            self._edit_supplier_order_by_id(order_id, reference)
        elif action_name == "delete":
            self._delete_supplier_order_by_id(order_id, reference)
        elif action_name.startswith("status_"):
            status_map = {
                "status_initial": "commande_initial",
                "status_ordered": "commande_passee", 
                "status_received": "commande_arrivee"
            }
            new_status = status_map.get(action_name)
            if new_status:
                self._change_supplier_order_status(order_id, reference, new_status)

    def _customize_supplier_orders_context_menu(self, row: int, row_data: list, menu):
        """Customize context menu based on supplier order status"""
        if not row_data or len(row_data) < 4:
            return
        
        # Status is in column 3 (index 3)
        current_status = row_data[3] if len(row_data) > 3 else ""
        
        # Map display status to internal status values
        status_map = {
            'Commande Initial': 'commande_initial',
            'Commande Passée': 'commande_passee', 
            'Commande Arrivée': 'commande_arrivee'
        }
        
        internal_status = status_map.get(current_status, 'commande_initial')
        
        # Show/hide status actions based on current status and progression rules
        for action in menu.actions():
            if action.text() == "→ Commande Initial":
                # Can always go back to initial (for corrections)
                action.setVisible(internal_status != 'commande_initial')
            elif action.text() == "→ Commande Passée":
                # Can only go to "passée" from "initial"
                action.setVisible(internal_status == 'commande_initial')
            elif action.text() == "→ Commande Arrivée":
                # Can only go to "arrivée" from "passée"
                action.setVisible(internal_status == 'commande_passee')

    def _change_supplier_order_status(self, order_id: int, reference: str, new_status: str):
        """Change the status of a supplier order"""
        session = SessionLocal()
        try:
            supplier_order = session.query(SupplierOrder).filter(SupplierOrder.id == order_id).first()
            if not supplier_order:
                QMessageBox.warning(self, 'Erreur', f'Commande {reference} introuvable')
                return
            
            # Map internal status to enum values
            status_enum_map = {
                'commande_initial': SupplierOrderStatus.INITIAL,
                'commande_passee': SupplierOrderStatus.ORDERED,
                'commande_arrivee': SupplierOrderStatus.RECEIVED
            }
            
            new_enum_status = status_enum_map.get(new_status)
            if not new_enum_status:
                QMessageBox.warning(self, 'Erreur', f'Statut invalide: {new_status}')
                return
            
            # Update the status
            supplier_order.status = new_enum_status
            session.commit()
            
            # Show confirmation and refresh
            status_display_map = {
                'commande_initial': 'Commande Initial',
                'commande_passee': 'Commande Passée', 
                'commande_arrivee': 'Commande Arrivée'
            }
            
            display_status = status_display_map.get(new_status, new_status)
            QMessageBox.information(self, 'Succès', f'Statut de la commande {reference} changé vers "{display_status}"')
            self.refresh_all()
            
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, 'Erreur', f'Erreur lors du changement de statut: {str(e)}')
        finally:
            session.close()

    def _edit_supplier_order_by_id(self, order_id: int, reference: str):
        """Edit a supplier order by ID"""
        # TODO: Implement edit functionality when SupplierOrderEditDialog is created
        QMessageBox.information(self, 'Information', f'Fonctionnalité d\'édition en cours de développement pour la commande {reference}')
        return
        
        # session = SessionLocal()
        # try:
        #     supplier_order = session.query(SupplierOrder).filter(SupplierOrder.id == order_id).first()
        #     if not supplier_order:
        #         QMessageBox.warning(self, 'Erreur', f'Commande {reference} introuvable')
        #         return
        #     
        #     # Get suppliers for the dialog
        #     suppliers = session.query(Supplier).all()
        #     if not suppliers:
        #         QMessageBox.warning(self, 'Erreur', 'Aucun fournisseur disponible.')
        #         return
        #     
        #     # Open edit dialog (you'll need to create an edit version)
        #     from ui.dialogs.supplier_order_edit_dialog import SupplierOrderEditDialog
        #     dlg = SupplierOrderEditDialog(suppliers, supplier_order, self)
        #     
        #     if dlg.exec():
        #         # Refresh the grid
        #         self.refresh_all()
        #         QMessageBox.information(self, 'Succès', f'Commande {reference} modifiée avec succès')
        #         
        # except Exception as e:
        #     QMessageBox.critical(self, 'Erreur', f'Erreur lors de la modification: {str(e)}')
        # finally:
        #     session.close()

    def _delete_supplier_order_by_id(self, order_id: int, reference: str):
        """Delete a supplier order by ID"""
        # Confirm deletion
        reply = QMessageBox.question(
            self, 'Confirmation', 
            f'Êtes-vous sûr de vouloir supprimer la commande {reference} ?\n\nCette action est irréversible.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        session = SessionLocal()
        try:
            supplier_order = session.query(SupplierOrder).filter(SupplierOrder.id == order_id).first()
            if supplier_order:
                session.delete(supplier_order)
                session.commit()
                QMessageBox.information(self, 'Succès', f'Commande {reference} supprimée avec succès')
                self.refresh_all()
            else:
                QMessageBox.warning(self, 'Erreur', 'Commande introuvable')
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de la suppression: {str(e)}')
        finally:
            session.close()

__all__ = ['MainWindow']