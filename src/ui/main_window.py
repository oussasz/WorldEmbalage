from __future__ import annotations
import datetime
from datetime import timezone
import logging
import os
import subprocess
from decimal import Decimal
from pathlib import Path
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMenuBar, QMenu, QMessageBox, QTabWidget, QToolBar, QLineEdit, QStatusBar, QDialog, QPushButton, QCompleter
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QSize, QStringListModel
from config.database import SessionLocal
from models.suppliers import Supplier
from models.clients import Client
from models.orders import ClientOrder, SupplierOrder, SupplierOrderLineItem
from models.orders import SupplierOrderStatus, ClientOrderStatus, Reception, Quotation, QuotationLineItem
from models.production import ProductionBatch
from ui.dialogs.supplier_dialog import SupplierDialog
from ui.dialogs.client_dialog import ClientDialog
from ui.dialogs.supplier_detail_dialog import SupplierDetailDialog
from ui.dialogs.client_detail_dialog import ClientDetailDialog
from ui.dialogs.raw_material_order_dialog import RawMaterialOrderDialog
from ui.dialogs.quotation_dialog import QuotationDialog
from ui.dialogs.edit_quotation_dialog import EditQuotationDialog
from ui.dialogs.reception_dialog import ReceptionDialog
from ui.dialogs.production_dialog import ProductionDialog
from ui.dialogs.quotation_detail_dialog import QuotationDetailDialog
from ui.widgets.data_grid import DataGrid
from ui.widgets.dashboard import Dashboard
from ui.widgets.split_view import SplitView
from ui.widgets.quad_view import QuadView
from ui.styles import IconManager
from services.order_service import OrderService
from services.pdf_form_filler import PDFFormFiller, PDFFillError
from services.pdf_export_service import export_supplier_order_to_pdf
from typing import cast, Any
from ui.widgets.split_view import SplitView
from ui.widgets.data_grid import DataGrid
from ui.widgets.dashboard import Dashboard
from models.orders import QuotationLineItem, ClientOrderLineItem


class MainWindow(QMainWindow):
    def __init__(self):
        # Initialize UI component references
        self.supplier_orders_quad: QuadView
        self.client_orders_grid: DataGrid
        self.orders_grid: DataGrid
        self.clients_suppliers_split: SplitView
        self.dashboard: Dashboard
        
        super().__init__()
        self.setWindowTitle('World Embalage - Gestion Atelier Carton')
        self.setWindowIcon(IconManager.create_text_icon("WE", bg_color="#2C3E50"))
        # Allow maximizing the window
        try:
            self.setMinimumSize(900, 600)
            self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        except Exception:
            pass
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
        try:
            # Rebuild suggestions when switching tabs
            self.tab_widget.currentChanged.connect(lambda _i: self._rebuild_search_completions_safe())
        except Exception:
            pass
        
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

            archive_action = QAction('&Archive', self)
            archive_action.setIcon(IconManager.get_archive_icon())
            archive_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(5))
            data_menu.addAction(archive_action)

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
        # Live filtering as user types
        try:
            self.search_field.textChanged.connect(self._on_search_changed)
        except Exception:
            pass
        # Attach autocomplete (suggestions) to the search field
        try:
            self._search_completer_model = QStringListModel(self)
            self._search_completer = QCompleter(self._search_completer_model, self)
            # Case-insensitive, show popup and match anywhere in the string
            try:
                self._search_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            except Exception:
                pass
            try:
                # Available in Qt >= 5.14; ignore if not
                self._search_completer.setFilterMode(Qt.MatchFlag.MatchContains)
            except Exception:
                pass
            try:
                self._search_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            except Exception:
                pass
            self.search_field.setCompleter(self._search_completer)
        except Exception as _completer_err:
            # Autocomplete is optional; continue without breaking toolbar
            logging.debug(f"Autocomplete setup skipped: {_completer_err}")
        toolbar.addWidget(self.search_field)
        
        toolbar.addSeparator()
        
        # Refresh action with proper icon
        refresh_action = QAction('Actualiser', self)
        refresh_action.setIcon(IconManager.get_refresh_icon())
        refresh_action.setToolTip('Actualiser toutes les données')
        refresh_action.triggered.connect(self.refresh_all)
        toolbar.addAction(refresh_action)

    def _rebuild_search_completions_safe(self) -> None:
        """Wrapper to rebuild search suggestions safely (no exceptions bubble)."""
        try:
            self._rebuild_search_completions()
        except Exception as e:
            logging.debug(f"Rebuild search completions skipped: {e}")

    def _collect_grid_texts(self, grid: DataGrid | None) -> list[str]:
        """Collect suggestion texts from a DataGrid's currently loaded data.
        Uses the grid's cached _all_rows to avoid scraping QTableWidget items.
        """
        results: list[str] = []
        if not grid:
            return results
        try:
            rows = getattr(grid, "_all_rows", []) or []
            # Flatten all cells, keep non-empty strings
            for row in rows:
                for cell in row:
                    if not cell:
                        continue
                    s = str(cell).strip()
                    if s:
                        results.append(s)
        except Exception:
            # Fallback: try reading visible table items
            try:
                table = getattr(grid, "table", None)
                if table:
                    for r in range(table.rowCount()):
                        for c in range(table.columnCount()):
                            item = table.item(r, c)
                            if item and item.text().strip():
                                results.append(item.text().strip())
            except Exception:
                pass
        return results

    def _rebuild_search_completions(self) -> None:
        """Build a suggestion list for the search box based on the active tab's data."""
        # No-op if completer wasn't initialized
        if not hasattr(self, "_search_completer_model"):
            return

        idx = self.tab_widget.currentIndex() if hasattr(self, 'tab_widget') else -1
        suggestions: list[str] = []

        # Dashboard (0) has no grid; Clients/Fournisseurs (1)
        if idx == 1 and hasattr(self, 'clients_suppliers_split') and self.clients_suppliers_split:
            suggestions += self._collect_grid_texts(self.clients_suppliers_split.left_grid)
            suggestions += self._collect_grid_texts(self.clients_suppliers_split.right_grid)
        elif idx == 2 and hasattr(self, 'orders_grid'):
            suggestions += self._collect_grid_texts(self.orders_grid)
        elif idx == 3 and hasattr(self, 'supplier_orders_quad') and self.supplier_orders_quad:
            for grid in [self.supplier_orders_quad.top_left_grid, self.supplier_orders_quad.top_right_grid,
                         self.supplier_orders_quad.bottom_left_grid, self.supplier_orders_quad.bottom_right_grid]:
                suggestions += self._collect_grid_texts(grid)
        elif idx == 4 and hasattr(self, 'stock_split') and self.stock_split:
            suggestions += self._collect_grid_texts(self.stock_split.left_grid)
            suggestions += self._collect_grid_texts(self.stock_split.right_grid)
        else:
            # Default: try major grids if present
            for g in [getattr(self, 'orders_grid', None),
                      getattr(self, 'receptions_grid', None),
                      getattr(self, 'production_grid', None)]:
                suggestions += self._collect_grid_texts(g)

        # Post-process: unique, keep order, add helpful tokens (dimension forms)
        seen = set()
        unique_suggestions: list[str] = []
        import re
        dim_re = re.compile(r"\b(\d{2,5})[x×](\d{2,5})(?:[x×](\d{1,4}))?\b", re.IGNORECASE)
        for s in suggestions:
            if s in seen:
                continue
            seen.add(s)
            unique_suggestions.append(s)
            # Add normalized dimension variants when found
            m = dim_re.search(s)
            if m:
                if m.group(3):
                    a, b, c = m.group(1), m.group(2), m.group(3)
                    for tok in [f"{a}×{b}×{c}", f"{a}x{b}x{c}", f"{a}x{b}x{c}mm"]:
                        if tok not in seen:
                            seen.add(tok)
                            unique_suggestions.append(tok)
                else:
                    a, b = m.group(1), m.group(2)
                    for tok in [f"{a}×{b}", f"{a}x{b}", f"{a}x{b}mm"]:
                        if tok not in seen:
                            seen.add(tok)
                            unique_suggestions.append(tok)

        # Limit to a reasonable number to keep popup snappy
        MAX_SUGGESTIONS = 1500
        final_list = unique_suggestions[:MAX_SUGGESTIONS]
        try:
            self._search_completer_model.setStringList(final_list)
        except Exception:
            pass

    def _on_search_changed(self, text: str):
        """Apply search/filter to the active tab's grid(s).
        Supports:
        - Reference IDs (e.g., DEV-..., BC-..., REC-..., FACT-..., LIV-...)
        - Dimensions: NxMxK or NxM (e.g., 100x200x50, 100x200)
        - Plain text across all columns
        """
        term = (text or "").strip()
        # Determine active tab index mapping used in _create_data_grids order
        current_index = self.tab_widget.currentIndex() if hasattr(self, 'tab_widget') else -1

        # Helper to filter a DataGrid if available
        def filter_grid(grid):
            if not grid:
                return
            if hasattr(grid, 'filter'):
                grid.filter(term)

        # Dimension-aware helper: inject only the dimension token to improve matches in our columns
        import re
        dim_tokens: list[str] = []
        m3 = re.search(r"(\d{2,5})x(\d{2,5})x(\d{1,4})", term.lower())
        m2 = re.search(r"(\d{2,5})x(\d{2,5})", term.lower()) if not m3 else None
        if m3:
            a, b, c = m3.group(1), m3.group(2), m3.group(3)
            # Add both '×' and 'x' variants
            dim_tokens.append(f"{a}×{b}×{c}")
            dim_tokens.append(f"{a}x{b}x{c}")
            dim_tokens.append(f"{a}x{b}x{c}mm")
        elif m2:
            a, b = m2.group(1), m2.group(2)
            dim_tokens.append(f"{a}×{b}")
            dim_tokens.append(f"{a}x{b}")
            dim_tokens.append(f"{a}x{b}mm")

        # Tokens for OR search: original term plus dimension token if detected
        tokens = [term] if term else []
        tokens.extend(dim_tokens)

        # Determine context: 0 Dashboard, 1 Clients/Fournisseurs, 2 Devis, 3 Commande MP, 4 Stock, 5 Archive
        if current_index == 2:  # Devis
            if self.orders_grid:
                if hasattr(self.orders_grid, 'filter_multi'):
                    self.orders_grid.filter_multi(tokens)
                else:
                    filter_grid(self.orders_grid)
        elif current_index == 3:  # Commande de matière première
            quad = self.supplier_orders_quad
            if quad:
                for grid in [quad.top_left_grid, quad.top_right_grid, quad.bottom_left_grid, quad.bottom_right_grid]:
                    if grid and hasattr(grid, 'filter_multi'):
                        grid.filter_multi(tokens)
                    else:
                        filter_grid(grid)
        elif current_index == 4:  # Stock split view
            split = self.stock_split
            if split:
                # Left: Matières premières; Right: Produits finis
                for grid in [split.left_grid, split.right_grid]:
                    if grid and hasattr(grid, 'filter_multi'):
                        grid.filter_multi(tokens)
                    else:
                        filter_grid(grid)
        else:
            # For other tabs that may show grids, apply generic filter where possible
            try:
                if self.clients_suppliers_split:
                    for grid in [self.clients_suppliers_split.left_grid, self.clients_suppliers_split.right_grid]:
                        if grid and hasattr(grid, 'filter_multi'):
                            grid.filter_multi(tokens)
                        else:
                            filter_grid(grid)
            except Exception:
                pass

    def _clear_global_filter(self) -> None:
        """Clear global search field and reapply empty filter across current view."""
        try:
            if hasattr(self, 'search_field') and self.search_field:
                # Avoid emitting duplicate signals if already empty
                if self.search_field.text():
                    self.search_field.clear()
                else:
                    # Explicitly trigger a filter refresh for safety
                    self._on_search_changed("")
        except Exception as e:
            logging.debug(f"Clear filter failed: {e}")

    # ---------- Dimension search (Stock) ----------
    def _parse_dims_tokens(self, text: str) -> tuple[str | None, str | None, str | None]:
        """Parse dimension tokens from a string. Returns (a,b,c) possibly None.
        Accepts formats like '100x200x50', '100×200×50', '100x200', 'L=100 l=200', etc.
        """
        import re
        s = (text or '').lower().strip()
        if not s:
            return (None, None, None)
        # Normalize separators and remove units
        s = s.replace('×', 'x').replace('mm', '')
        # Extract numbers
        nums = re.findall(r"\d{1,5}", s)
        if not nums:
            return (None, None, None)
        a = nums[0] if len(nums) > 0 else None
        b = nums[1] if len(nums) > 1 else None
        c = nums[2] if len(nums) > 2 else None
        return (a, b, c)

    def _raw_row_matches(self, row: list[str], a: str | None, b: str | None, c: str | None) -> bool:
        """Row matcher for raw materials (left grid). Our columns include Description that has [WxLxRmm] token when available."""
        row_l = [str(x).lower() for x in row]
        # Prefer checking the Description column (index 5) and full row as fallback
        description = row_l[5] if len(row_l) > 5 else ''
        haystacks = [description] + row_l
        def contains(tok: str) -> bool:
            for h in haystacks:
                if tok in h:
                    return True
            return False
        # Build expected tokens
        tok_a = f"{a}" if a else None
        tok_b = f"{b}" if b else None
        tok_c = f"{c}" if c else None
        # If all three present, require all three
        if a and b and c:
            return contains(f"{a}x{b}x{c}") or (contains(a) and contains(b) and contains(c))
        # If two present, require both
        if a and b:
            if not (contains(a) and contains(b)):
                return False
        elif a and c:
            if not (contains(a) and contains(c)):
                return False
        elif b and c:
            if not (contains(b) and contains(c)):
                return False
        else:
            # Single token present
            single = a or b or c
            return contains(single) if single else True
        return True

    def _prod_row_matches(self, row: list[str], a: str | None, b: str | None, c: str | None) -> bool:
        """Row matcher for finished products (right grid). Dimensions are in 'Dimensions Caisse' column (index 2)."""
        row_l = [str(x).lower() for x in row]
        dims = row_l[2] if len(row_l) > 2 else ''
        haystacks = [dims] + row_l
        def contains(tok: str) -> bool:
            for h in haystacks:
                if tok in h:
                    return True
            return False
        if a and b and c:
            return contains(f"{a}x{b}x{c}") or (contains(a) and contains(b) and contains(c))
        if a and b:
            return contains(a) and contains(b)
        if a and c:
            return contains(a) and contains(c)
        if b and c:
            return contains(b) and contains(c)
        single = a or b or c
        return contains(single) if single else True

    def _on_raw_dim_search_changed(self, text: str) -> None:
        a, b, c = self._parse_dims_tokens(text)
        grid = self.receptions_grid
        if not grid:
            return
        # Filter using cached rows to avoid mutating original data
        all_rows = getattr(grid, '_all_rows', [])
        if not text.strip():
            grid.load_rows(all_rows)
            return
        filtered = [row for row in all_rows if self._raw_row_matches(row, a, b, c)]
        grid.load_rows(filtered)
        # Update suggestions
        try:
            self._rebuild_dim_completions_raw()
        except Exception:
            pass

    def _on_prod_dim_search_changed(self, text: str) -> None:
        a, b, c = self._parse_dims_tokens(text)
        grid = self.production_grid
        if not grid:
            return
        all_rows = getattr(grid, '_all_rows', [])
        if not text.strip():
            grid.load_rows(all_rows)
            return
        filtered = [row for row in all_rows if self._prod_row_matches(row, a, b, c)]
        grid.load_rows(filtered)
        try:
            self._rebuild_dim_completions_prod()
        except Exception:
            pass

    def _rebuild_dim_completions_raw(self) -> None:
        if not hasattr(self, '_raw_dim_model') or not self.receptions_grid:
            return
        import re
        rows = getattr(self.receptions_grid, '_all_rows', [])
        suggestions: list[str] = []
        dim_re = re.compile(r"\b(\d{2,5})[x×](\d{2,5})(?:[x×](\d{1,4}))?\b", re.IGNORECASE)
        for row in rows:
            for cell in row:
                if not cell:
                    continue
                s = str(cell)
                m = dim_re.search(s)
                if m:
                    if m.group(3):
                        a,b,c = m.group(1), m.group(2), m.group(3)
                        for tok in [f"{a}x{b}x{c}", f"{a}×{b}×{c}"]:
                            suggestions.append(tok)
                    else:
                        a,b = m.group(1), m.group(2)
                        for tok in [f"{a}x{b}", f"{a}×{b}"]:
                            suggestions.append(tok)
        # Add single-dimension tokens as well to help partial search
        singles = set()
        for row in rows:
            for cell in row:
                if not cell:
                    continue
                for num in re.findall(r"\b\d{2,5}\b", str(cell)):
                    singles.add(num)
        suggestions.extend(list(singles))
        # Deduplicate and cap
        seen = set()
        unique = []
        for s in suggestions:
            if s not in seen:
                seen.add(s)
                unique.append(s)
        try:
            self._raw_dim_model.setStringList(unique[:1000])
        except Exception:
            pass

    def _rebuild_dim_completions_prod(self) -> None:
        if not hasattr(self, '_prod_dim_model') or not self.production_grid:
            return
        import re
        rows = getattr(self.production_grid, '_all_rows', [])
        suggestions: list[str] = []
        dim_re = re.compile(r"\b(\d{2,5})[x×](\d{2,5})(?:[x×](\d{1,4}))?\b", re.IGNORECASE)
        for row in rows:
            for cell in row:
                if not cell:
                    continue
                s = str(cell)
                m = dim_re.search(s)
                if m:
                    if m.group(3):
                        a,b,c = m.group(1), m.group(2), m.group(3)
                        for tok in [f"{a}x{b}x{c}", f"{a}×{b}×{c}"]:
                            suggestions.append(tok)
                    else:
                        a,b = m.group(1), m.group(2)
                        for tok in [f"{a}x{b}", f"{a}×{b}"]:
                            suggestions.append(tok)
        singles = set()
        for row in rows:
            for cell in row:
                if not cell:
                    continue
                for num in re.findall(r"\b\d{2,5}\b", str(cell)):
                    singles.add(num)
        suggestions.extend(list(singles))
        seen = set()
        unique = []
        for s in suggestions:
            if s not in seen:
                seen.add(s)
                unique.append(s)
        try:
            self._prod_dim_model.setStringList(unique[:1000])
        except Exception:
            pass

    def _prompt_client_filter(self, scope: str = "") -> None:
        """Show a list of clients to choose from; set the toolbar search to that name to filter.
        scope is informational only; filtering uses the global search handler for the active tab.
        """
        session = None
        try:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox
            session = SessionLocal()
            clients = session.query(Client).order_by(Client.name.asc()).all()
            if not clients:
                QMessageBox.information(self, 'Information', 'Aucun client disponible.')
                return

            dlg = QDialog(self)
            dlg.setWindowTitle("Filtrer par client")
            layout = QVBoxLayout(dlg)
            layout.addWidget(QLabel("Choisir un client:"))

            combo = QComboBox(dlg)
            combo.setEditable(True)  # allow typing to quickly search in the list
            for c in clients:
                display = (c.name or f"Client {c.id}").strip()
                combo.addItem(display, c.id)
            combo.setCurrentIndex(0)
            layout.addWidget(combo)

            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dlg.accept)
            buttons.rejected.connect(dlg.reject)
            layout.addWidget(buttons)

            if dlg.exec() == QDialog.DialogCode.Accepted:
                name = combo.currentText().strip()
                if name:
                    # Set into the global search field to reuse the same filtering logic
                    self.search_field.setText(name)
        except Exception as e:
            logging.error(f"Client filter prompt failed: {e}")
        finally:
            if session is not None:
                session.close()

    def _create_data_grids(self) -> None:
        """Create data grids for each entity type with new menu structure."""
        
        # 1. Client et Fournisseur (Split view)
        self.clients_suppliers_split = SplitView(
            "Fournisseurs", ["ID", "Nom", "Téléphone", "Email", "Adresse"],
            "Clients", ["ID", "Nom", "Téléphone", "Email", "Adresse", "Activité"]
        )
        self.clients_suppliers_split.add_left_action_button("➕ Nouveau Fournisseur", self._new_supplier)
        self.clients_suppliers_split.add_right_action_button("➕ Nouveau Client", self._new_client)
        self.tab_widget.addTab(self.clients_suppliers_split, IconManager.get_client_icon(), "Client et Fournisseur")
        
        # Store references to individual grids for refresh functionality
        self.suppliers_grid = self.clients_suppliers_split.left_grid
        self.clients_grid = self.clients_suppliers_split.right_grid
        
        # 2. Devis (Enhanced with comprehensive information)
        self.orders_grid = DataGrid(
            ["ID", "Référence", "Client", "Date Création", "Date Validité", "Statut", 
             "Articles", "Dimensions", "Quantités", "Types Carton", "Total HT (DA)", "Notes"]
        )
        self.orders_grid.add_action_button("➕ Devis", self._new_quotation)
        # Quick customer filter button and a clear filter next to it
        self.orders_grid.add_action_button("🔎 Filtrer Client", lambda: self._prompt_client_filter('devis'))
        clear_btn_devis = self.orders_grid.add_action_button("✖ Effacer Filtre", self._clear_global_filter)
        try:
            clear_btn_devis.setProperty("class", "secondary")
        except Exception:
            pass
        
        # Connect double-click to show detail dialog
        self.orders_grid.rowDoubleClicked.connect(self._on_quotation_double_click)
        
        self.tab_widget.addTab(self.orders_grid, IconManager.get_quotation_icon(), "Devis")
        
        # Keep client_orders_grid for backend logic but don't add to tabs
        self.client_orders_grid = DataGrid(
            ["ID", "Référence", "Client", "Statut", "Date Création", "Total HT (DA)", "Notes"]
        )
        # Note: Grid created for backend compatibility but not displayed in UI
        
        # 3. Commande de matière première (Quad view: 4 status sections)
        self.supplier_orders_quad = QuadView(
            "Commandes Initiales", ["ID", "Bon Commande", "Fournisseur", "Date", "Total UTTC", "Nb Articles", "Clients"],
            "Commandes Passées", ["ID", "Bon Commande", "Fournisseur", "Statut", "Date", "Total UTTC", "Nb Articles", "Clients"],
            "Partiellement Livrée", ["ID", "Bon Commande", "Fournisseur", "Statut", "Date", "Total UTTC", "Nb Articles", "Clients"],
            "Terminée", ["ID", "Bon Commande", "Fournisseur", "Statut", "Date", "Total UTTC", "Nb Articles", "Clients"]
        )
        self.supplier_orders_quad.add_top_left_action_button("➕ Nouvelle", self._new_supplier_order)
        # Place filter controls in the QuadView header bar (top-right, consistent design)
        try:
            filter_btn_so = self.supplier_orders_quad.add_header_action_button("🔎 Filtrer Client", lambda: self._prompt_client_filter('supplier_orders'))
            clear_btn_so = self.supplier_orders_quad.add_header_action_button("✖ Effacer Filtre", self._clear_global_filter)
            if clear_btn_so:
                clear_btn_so.setProperty("class", "secondary")
        except Exception:
            pass
        
        self.tab_widget.addTab(self.supplier_orders_quad, IconManager.get_supplier_order_icon(), "Commande de matière première")
        
        # 4. Stock (Split view: Raw materials and Finished products)
        self.stock_split = SplitView(
            "Matières Premières", ["ID", "Quantité", "Fournisseur", "Bon Commande", "Client", "Description", "Date Réception"],
            "Produits Finis", ["ID", "Client", "Dimensions Caisse", "Quantité", "Description", "Statut"]
        )
        # Add Raw Material Arrival button to the left side (Raw materials)
        self.stock_split.add_left_action_button("📦 Arrivée Matière Première", self._raw_material_arrival)
        # Quick client filters for stock
        if self.stock_split.left_grid:
            self.stock_split.left_grid.add_action_button("🔎 Filtrer Client", lambda: self._prompt_client_filter('stock_left'))
            clear_btn_stock_left = self.stock_split.left_grid.add_action_button("✖ Effacer Filtre", self._clear_global_filter)
            try:
                clear_btn_stock_left.setProperty("class", "secondary")
            except Exception:
                pass
        if self.stock_split.right_grid:
            self.stock_split.right_grid.add_action_button("🔎 Filtrer Client", lambda: self._prompt_client_filter('stock_right'))
            clear_btn_stock_right = self.stock_split.right_grid.add_action_button("✖ Effacer Filtre", self._clear_global_filter)
            try:
                clear_btn_stock_right.setProperty("class", "secondary")
            except Exception:
                pass
        # Note: We'll use receptions for raw materials and production for finished products
        self.tab_widget.addTab(self.stock_split, IconManager.get_reception_icon(), "Stock")
        
        # Store references for refresh functionality
        self.receptions_grid = self.stock_split.left_grid  # Raw materials
        self.production_grid = self.stock_split.right_grid  # Finished products
        # Add per-grid dimension search fields with autocomplete for Stock
        try:
            from PyQt6.QtWidgets import QLineEdit
            # Raw materials (left): largeur × longueur × rabat
            self._raw_dim_search = QLineEdit()
            self._raw_dim_search.setPlaceholderText("Dimensions (L×l×r) ex: 100x200x50")
            self._raw_dim_search.setClearButtonEnabled(True)
            self._raw_dim_model = QStringListModel(self)
            self._raw_dim_completer = QCompleter(self._raw_dim_model, self)
            try:
                self._raw_dim_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                self._raw_dim_completer.setFilterMode(Qt.MatchFlag.MatchContains)
                self._raw_dim_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            except Exception:
                pass
            self._raw_dim_search.setCompleter(self._raw_dim_completer)
            if self.receptions_grid and hasattr(self.receptions_grid, 'add_header_widget'):
                self.receptions_grid.add_header_widget(self._raw_dim_search)
            self._raw_dim_search.textChanged.connect(self._on_raw_dim_search_changed)

            # Finished products (right): largeur × longueur × hauteur
            self._prod_dim_search = QLineEdit()
            self._prod_dim_search.setPlaceholderText("Dimensions (L×l×h) ex: 100x200x50")
            self._prod_dim_search.setClearButtonEnabled(True)
            self._prod_dim_model = QStringListModel(self)
            self._prod_dim_completer = QCompleter(self._prod_dim_model, self)
            try:
                self._prod_dim_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                self._prod_dim_completer.setFilterMode(Qt.MatchFlag.MatchContains)
                self._prod_dim_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            except Exception:
                pass
            self._prod_dim_search.setCompleter(self._prod_dim_completer)
            if self.production_grid and hasattr(self.production_grid, 'add_header_widget'):
                self.production_grid.add_header_widget(self._prod_dim_search)
            self._prod_dim_search.textChanged.connect(self._on_prod_dim_search_changed)
        except Exception as dim_err:
            logging.debug(f"Dimension search fields setup skipped: {dim_err}")
        
        # 6. Archive
        from ui.widgets.archive_widget import ArchiveWidget
        self.archive_widget = ArchiveWidget()
        self.tab_widget.addTab(self.archive_widget, IconManager.get_archive_icon(), "Archive")
        
        # Setup context menus after all grids are created
        self._setup_context_menus()

    def _setup_context_menus(self):
        """Setup context menus for data grids"""
        # Suppliers context menu
        if self.suppliers_grid:
            self.suppliers_grid.add_context_action("edit", "✏️ Modifier fournisseur")
            self.suppliers_grid.add_context_action("delete", "🗑️ Supprimer fournisseur")
            
            # Connect suppliers context menu signals
            self.suppliers_grid.contextMenuActionTriggered.connect(self._handle_suppliers_context_menu)
            self.suppliers_grid.rowDoubleClicked.connect(self._on_supplier_double_click)
        
        # Clients context menu
        if self.clients_grid:
            self.clients_grid.add_context_action("edit", "✏️ Modifier client")
            self.clients_grid.add_context_action("delete", "🗑️ Supprimer client")
            
            # Connect clients context menu signals
            self.clients_grid.contextMenuActionTriggered.connect(self._handle_clients_context_menu)
            self.clients_grid.rowDoubleClicked.connect(self._on_client_double_click)
        
        # Orders context menu - static actions only
        self.orders_grid.add_context_action("edit", "Modifier devis")
        self.orders_grid.add_context_action("print", "Imprimer devis")
        self.orders_grid.add_context_action("delete", "Supprimer devis")
        # Note: create_supplier_order is added dynamically based on devis type
        
        # Connect context menu signals
        self.orders_grid.contextMenuActionTriggered.connect(self._handle_orders_context_menu)
        self.orders_grid.contextMenuAboutToShow.connect(self._customize_orders_context_menu)

        # Supplier orders context menu (4 sections of quad view)
        # Top Left (Initial Orders) - basic actions
        if hasattr(self.supplier_orders_quad, 'top_left_grid') and self.supplier_orders_quad.top_left_grid:
            self.supplier_orders_quad.top_left_grid.add_context_action("edit", "Modifier commande")
            self.supplier_orders_quad.top_left_grid.add_context_action("delete", "Supprimer commande")
            self.supplier_orders_quad.top_left_grid.add_context_action("export_pdf", "📄 Exporter en PDF")
            self.supplier_orders_quad.top_left_grid.add_context_action("status_ordered", "→ Passer commande")
            
            self.supplier_orders_quad.top_left_grid.contextMenuActionTriggered.connect(self._handle_supplier_orders_context_menu)
            self.supplier_orders_quad.top_left_grid.rowDoubleClicked.connect(self._on_supplier_order_double_click)
        
        # Top Right (Ordered) - status change actions
        if hasattr(self.supplier_orders_quad, 'top_right_grid') and self.supplier_orders_quad.top_right_grid:
            self.supplier_orders_quad.top_right_grid.add_context_action("delete", "Supprimer commande")
            self.supplier_orders_quad.top_right_grid.add_context_action("export_pdf", "📄 Exporter en PDF")
            self.supplier_orders_quad.top_right_grid.add_context_action("status_initial", "→ Commande annulée")
            
            self.supplier_orders_quad.top_right_grid.contextMenuActionTriggered.connect(self._handle_supplier_orders_context_menu)
            self.supplier_orders_quad.top_right_grid.rowDoubleClicked.connect(self._on_supplier_order_double_click)
        
        # Bottom Left (Partially Delivered) - status change actions
        if hasattr(self.supplier_orders_quad, 'bottom_left_grid') and self.supplier_orders_quad.bottom_left_grid:
            self.supplier_orders_quad.bottom_left_grid.add_context_action("delete", "Supprimer commande")
            self.supplier_orders_quad.bottom_left_grid.add_context_action("status_completed", "→ Terminé")
            
            self.supplier_orders_quad.bottom_left_grid.contextMenuActionTriggered.connect(self._handle_supplier_orders_context_menu)
            self.supplier_orders_quad.bottom_left_grid.rowDoubleClicked.connect(self._on_supplier_order_double_click)
        
        # Bottom Right (Completed) - status cannot be changed manually
        if hasattr(self.supplier_orders_quad, 'bottom_right_grid') and self.supplier_orders_quad.bottom_right_grid:
            self.supplier_orders_quad.bottom_right_grid.add_context_action("delete", "Supprimer commande")
            
            self.supplier_orders_quad.bottom_right_grid.contextMenuActionTriggered.connect(self._handle_supplier_orders_context_menu)
            self.supplier_orders_quad.bottom_right_grid.rowDoubleClicked.connect(self._on_supplier_order_double_click)

        # Stock context menu (Raw materials)
        if self.receptions_grid:
            self.receptions_grid.add_context_action("edit", "✏️ Modifier réception")
            self.receptions_grid.add_context_action("delete", "🗑️ Supprimer réception")
            self.receptions_grid.add_context_action("print_label", "🏷️ Imprimer l'étiquette matière première")
            # New action: archive raw material reception(s)
            self.receptions_grid.add_context_action("move_to_archive", "📦 Archiver matière première")
            
            # Connect stock context menu signals
            self.receptions_grid.contextMenuActionTriggered.connect(self._handle_stock_context_menu)
            self.receptions_grid.rowDoubleClicked.connect(self._on_stock_double_click)

        # Production context menu (Finished products)
        if self.production_grid:
            self.production_grid.add_context_action("edit", "✏️ Modifier production")
            self.production_grid.add_context_action("delete", "🗑️ Supprimer production")
            self.production_grid.add_context_action("print_fiche", "🖨️ Imprimer la fiche de produit fini")
            self.production_grid.add_context_action("print_delivery", "📋 Imprimer le bon de livraison")
            self.production_grid.add_context_action("create_invoice", "📝 Créer facture")
            self.production_grid.add_context_action("move_to_archive", "📦 Move to Archive")
            
            # Add "Add finished product" button to production grid
            self.production_grid.add_action_button("➕ Ajouter Produit Fini", self._add_finished_product)
            
            # Connect production context menu signals
            self.production_grid.contextMenuActionTriggered.connect(self._handle_production_context_menu)
            self.production_grid.contextMenuAboutToShow.connect(self._customize_production_context_menu)
            self.production_grid.rowDoubleClicked.connect(self._on_production_double_click)

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
            status = row_data[5] if len(row_data) > 5 else ""  # Column 5 is "Statut" (after removing Contact column)
            if status == "Devis Final":
                can_create_order = True
        elif num_selected > 1:
            # Check if all selected are Final Devis
            all_final = True
            for r_idx in selected_rows:
                status = self.orders_grid.get_row_data(r_idx)[5]  # Column 5 is "Statut" (after removing Contact column)
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

    def _customize_production_context_menu(self, row: int, row_data: list, menu):
        """Customize context menu for finished products based on selection"""
        from PyQt6.QtGui import QAction
        
        if not self.production_grid or not hasattr(self.production_grid, 'get_selected_row_indices'):
            return
            
        selected_rows = self.production_grid.get_selected_row_indices()
        num_selected = len(selected_rows)
        
        if num_selected > 1:
            # Multiple selection: only show Delete, Delivery, Invoice
            
            # Hide edit and print fiche actions for multiple selection
            for action in menu.actions():
                action_text = action.text()
                if ("Modifier production" in action_text or 
                    "Imprimer la fiche de produit fini" in action_text):
                    action.setVisible(False)
                elif "Supprimer production" in action_text and not action_text.startswith("Supprimer les"):
                    action.setVisible(False)  # Hide single delete
            
            # Add or update multi-delete action
            multi_delete_action = None
            for action in menu.actions():
                if action.text().startswith("🗑️ Supprimer les"):
                    multi_delete_action = action
                    break
            
            if not multi_delete_action:
                multi_delete_action = QAction(f"🗑️ Supprimer les {num_selected} productions", self)
                multi_delete_action.triggered.connect(lambda: self._handle_production_context_menu("multi_delete", -1, []))
                menu.addAction(multi_delete_action)
            else:
                multi_delete_action.setText(f"🗑️ Supprimer les {num_selected} productions")
                multi_delete_action.setVisible(True)
                
            # Keep delivery and invoice actions visible but update text
            for action in menu.actions():
                action_text = action.text()
                if "bon de livraison" in action_text.lower():
                    action.setText("📋 Imprimer le bon de livraison")
                    action.setVisible(True)
                elif "imprimer la facture" in action_text.lower() or action_text == "💰 Imprimer la facture":
                    action.setText("💰 Imprimer la facture")
                    action.setVisible(True)
                elif "créer facture" in action_text.lower() or action_text == "📝 Créer facture":
                    action.setText("📝 Créer facture")
                    action.setVisible(True)
                
        else:
            # Single selection: show all actions
            
            # Show all single-item actions
            for action in menu.actions():
                action_text = action.text()
                if ("Modifier production" in action_text or 
                    "Imprimer la fiche de produit fini" in action_text or
                    ("Supprimer production" in action_text and not action_text.startswith("Supprimer les"))):
                    action.setVisible(True)
            
            # Hide multi-delete action
            for action in menu.actions():
                if action.text().startswith("🗑️ Supprimer les"):
                    action.setVisible(False)
                    
            # Reset delivery and invoice action text for single item
            for action in menu.actions():
                action_text = action.text()
                if "bon de livraison" in action_text.lower():
                    action.setText("📋 Imprimer le bon de livraison")
                    action.setVisible(True)
                elif "imprimer la facture" in action_text.lower() or action_text == "💰 Imprimer la facture":
                    action.setText("💰 Imprimer la facture")
                    action.setVisible(True)
                elif "créer facture" in action_text.lower() or action_text == "📝 Créer facture":
                    action.setText("📝 Créer facture")
                    action.setVisible(True)

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
            if len(row_data) > 5 and row_data[5] == "Devis Final":
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
                
                # Rabat de plaque = largeur de caisse / 2
                rabat_plaque = largeur_caisse // 2  # Use integer division
                
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
                    import json
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
                            # Preserve full original devis line data in notes to avoid any information loss
                            notes=(
                                f"Depuis devis {quotation.reference} - {plaque_data['notes']}\n"
                                f"[DEVIS_LINE_SNAPSHOT] " + json.dumps({
                                    'line_number': line_num,
                                    'description': quotation.line_items[line_num-1].description,
                                    'quantity_text': quotation.line_items[line_num-1].quantity,
                                    'unit_price': float(quotation.line_items[line_num-1].unit_price or 0),  # type: ignore[arg-type]
                                    'total_price': float(quotation.line_items[line_num-1].total_price or 0),  # type: ignore[arg-type]
                                    'length_mm': quotation.line_items[line_num-1].length_mm,
                                    'width_mm': quotation.line_items[line_num-1].width_mm,
                                    'height_mm': quotation.line_items[line_num-1].height_mm,
                                    'color': (quotation.line_items[line_num-1].color.value if getattr(quotation.line_items[line_num-1], 'color', None) else None),  # type: ignore[union-attr]
                                    'cardboard_type': quotation.line_items[line_num-1].cardboard_type,
                                    'material_reference': quotation.line_items[line_num-1].material_reference,
                                    'is_cliche': quotation.line_items[line_num-1].is_cliche,
                                    'notes': quotation.line_items[line_num-1].notes,
                                }, ensure_ascii=False)
                            )
                        )
                        session.add(line_item)
                    
                    # Update supplier order total
                    supplier_order.total_amount = total_amount  # type: ignore

                    # Embed a full snapshot of the source quotation in the supplier order notes
                    quotation_snapshot = {
                        'id': quotation.id,
                        'reference': quotation.reference,
                        'client_id': quotation.client_id,
                        'issue_date': str(quotation.issue_date) if quotation.issue_date else None,
                        'valid_until': str(quotation.valid_until) if quotation.valid_until else None,
                        'total_amount': float(quotation.total_amount or 0),  # type: ignore[arg-type]
                        'currency': quotation.currency,
                        'is_initial': bool(quotation.is_initial),
                        'notes': quotation.notes,
                        'line_items': [
                            {
                                'line_number': li.line_number,
                                'description': li.description,
                                'quantity_text': li.quantity,
                                'unit_price': float(li.unit_price or 0),  # type: ignore[arg-type]
                                'total_price': float(li.total_price or 0),  # type: ignore[arg-type]
                                'length_mm': li.length_mm,
                                'width_mm': li.width_mm,
                                'height_mm': li.height_mm,
                                'color': (li.color.value if li.color else None),
                                'cardboard_type': li.cardboard_type,
                                'material_reference': li.material_reference,
                                'is_cliche': li.is_cliche,
                                'notes': li.notes,
                            }
                            for li in quotation.line_items
                        ]
                    }
                    # Append snapshot preserving any existing notes
                    existing_notes = supplier_order.notes or ""
                    supplier_order.notes = (existing_notes + "\n\n[DEVIS_SNAPSHOT] " + json.dumps(quotation_snapshot, ensure_ascii=False)).strip()
                    session.commit()

                    # After successful transfer, delete the original quotation (and its line items via cascade)
                    session.delete(quotation)
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

    def _on_supplier_double_click(self, row: int):
        """Handle double-click on supplier row to show detailed view"""
        if not self.suppliers_grid or not self.suppliers_grid.table:
            return
            
        # Get row data directly from table
        row_data = []
        for col in range(self.suppliers_grid.table.columnCount()):
            item = self.suppliers_grid.table.item(row, col)
            if item:
                row_data.append(item.text())
            else:
                row_data.append('')
                
        if not row_data or len(row_data) < 1:
            return
            
        # Extract supplier ID
        supplier_id_str = row_data[0]
        if not supplier_id_str:
            return
            
        try:
            supplier_id = int(supplier_id_str)
        except (ValueError, TypeError):
            QMessageBox.warning(self, 'Erreur', 'ID de fournisseur invalide')
            return
        
        # Get supplier from database and show detail dialog
        session = SessionLocal()
        try:
            supplier = session.get(Supplier, supplier_id)
            if not supplier:
                QMessageBox.warning(self, 'Erreur', 'Fournisseur introuvable')
                return
                
            # Show detail dialog in read-only mode
            detail_dialog = SupplierDetailDialog(supplier, self, read_only=True)
            detail_dialog.exec()
                
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de l\'affichage des détails: {str(e)}')
        finally:
            session.close()

    def _on_client_double_click(self, row: int):
        """Handle double-click on client row to show detailed view"""
        if not self.clients_grid or not self.clients_grid.table:
            return
            
        # Get row data directly from table
        row_data = []
        for col in range(self.clients_grid.table.columnCount()):
            item = self.clients_grid.table.item(row, col)
            if item:
                row_data.append(item.text())
            else:
                row_data.append('')
                
        if not row_data or len(row_data) < 1:
            return
            
        # Extract client ID
        client_id_str = row_data[0]
        if not client_id_str:
            return
            
        try:
            client_id = int(client_id_str)
        except (ValueError, TypeError):
            QMessageBox.warning(self, 'Erreur', 'ID de client invalide')
            return
        
        # Get client from database and show detail dialog
        session = SessionLocal()
        try:
            client = session.get(Client, client_id)
            if not client:
                QMessageBox.warning(self, 'Erreur', 'Client introuvable')
                return
                
            # Show detail dialog in read-only mode
            detail_dialog = ClientDetailDialog(client, self, read_only=True)
            detail_dialog.exec()
                
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de l\'affichage des détails: {str(e)}')
        finally:
            session.close()

    def _handle_suppliers_context_menu(self, action_name: str, row: int, row_data: list):
        """Handle context menu actions for suppliers grid"""
        if not row_data or len(row_data) < 1:
            return
            
        # Extract supplier ID
        supplier_id_str = row_data[0]
        if not supplier_id_str:
            return
            
        try:
            supplier_id = int(supplier_id_str)
        except (ValueError, TypeError):
            QMessageBox.warning(self, 'Erreur', 'ID de fournisseur invalide')
            return

        session = SessionLocal()
        try:
            supplier = session.get(Supplier, supplier_id)
            if not supplier:
                QMessageBox.warning(self, 'Erreur', 'Fournisseur introuvable')
                return

            if action_name == "edit":
                # Show edit dialog
                detail_dialog = SupplierDetailDialog(supplier, self, read_only=False)
                if detail_dialog.exec():
                    # Update supplier with new data
                    data = detail_dialog.get_data()
                    for key, value in data.items():
                        setattr(supplier, key, value)
                    
                    session.commit()
                    QMessageBox.information(self, 'Succès', f'Fournisseur {data["name"]} modifié')
                    self.dashboard.add_activity("F", f"Fournisseur modifié: {data['name']}", "#FFA500")
                    self.refresh_all()
                    
            elif action_name == "delete":
                # Confirm deletion
                result = QMessageBox.question(
                    self, 
                    'Confirmation', 
                    f'Êtes-vous sûr de vouloir supprimer le fournisseur "{supplier.name}" ?\n\n'
                    'Cette action est irréversible.',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if result == QMessageBox.StandardButton.Yes:
                    # Check if supplier has orders
                    if supplier.supplier_orders:
                        QMessageBox.warning(
                            self, 
                            'Impossible de supprimer', 
                            f'Le fournisseur "{supplier.name}" a des commandes associées.\n'
                            'Supprimez d\'abord toutes les commandes de ce fournisseur.'
                        )
                        return
                    
                    session.delete(supplier)
                    session.commit()
                    QMessageBox.information(self, 'Succès', f'Fournisseur "{supplier.name}" supprimé')
                    self.dashboard.add_activity("F", f"Fournisseur supprimé: {supplier.name}", "#DC3545")
                    self.refresh_all()
                    
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de l\'opération: {str(e)}')
        finally:
            session.close()

    def _handle_clients_context_menu(self, action_name: str, row: int, row_data: list):
        """Handle context menu actions for clients grid"""
        if not row_data or len(row_data) < 1:
            return
            
        # Extract client ID
        client_id_str = row_data[0]
        if not client_id_str:
            return
            
        try:
            client_id = int(client_id_str)
        except (ValueError, TypeError):
            QMessageBox.warning(self, 'Erreur', 'ID de client invalide')
            return

        session = SessionLocal()
        try:
            client = session.get(Client, client_id)
            if not client:
                QMessageBox.warning(self, 'Erreur', 'Client introuvable')
                return

            if action_name == "edit":
                # Show edit dialog
                detail_dialog = ClientDetailDialog(client, self, read_only=False)
                if detail_dialog.exec():
                    # Update client with new data
                    data = detail_dialog.get_data()
                    for key, value in data.items():
                        setattr(client, key, value)
                    
                    session.commit()
                    QMessageBox.information(self, 'Succès', f'Client {data["name"]} modifié')
                    self.dashboard.add_activity("C", f"Client modifié: {data['name']}", "#FFA500")
                    self.refresh_all()
                    
            elif action_name == "delete":
                # Confirm deletion
                result = QMessageBox.question(
                    self, 
                    'Confirmation', 
                    f'Êtes-vous sûr de vouloir supprimer le client "{client.name}" ?\n\n'
                    'Cette action est irréversible.',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if result == QMessageBox.StandardButton.Yes:
                    # Check if client has orders or quotations with proper database queries
                    from models.orders import ClientOrder, Quotation, SupplierOrderLineItem
                    
                    # Count actual orders and quotations in database
                    orders_count = session.query(ClientOrder).filter(ClientOrder.client_id == client.id).count()
                    quotations_count = session.query(Quotation).filter(Quotation.client_id == client.id).count()
                    supplier_order_items_count = session.query(SupplierOrderLineItem).filter(SupplierOrderLineItem.client_id == client.id).count()
                    
                    if orders_count > 0 or quotations_count > 0 or supplier_order_items_count > 0:
                        # Get details about all associated records
                        details_msg = f'Le client "{client.name}" a des commandes ou devis associés.\n'
                        details_msg += f'Trouvé: {orders_count} commande(s), {quotations_count} devis, et {supplier_order_items_count} bon de commande.\n\n'
                        
                        # Show details about client orders
                        if orders_count > 0:
                            client_orders = session.query(ClientOrder).filter(ClientOrder.client_id == client.id).all()
                            details_msg += f"Commandes client concernées:\n"
                            for co in client_orders:
                                details_msg += f"- ID: {co.id}, Ref: {co.reference}, Statut: {co.status.value}\n"
                            details_msg += "\n"
                        
                        # Show details about quotations
                        if quotations_count > 0:
                            quotations = session.query(Quotation).filter(Quotation.client_id == client.id).all()
                            details_msg += f"Devis concernés:\n"
                            for q in quotations:
                                details_msg += f"- ID: {q.id}, Ref: {q.reference}\n"
                            details_msg += "\n"
                        
                        if supplier_order_items_count > 0:
                            # Get the supplier order references
                            from models.orders import SupplierOrder
                            supplier_orders_with_items = session.query(SupplierOrder).join(SupplierOrderLineItem).filter(
                                SupplierOrderLineItem.client_id == client.id
                            ).distinct().all()
                            
                            details_msg += f"Bons de commande concernés:\n"
                            for so in supplier_orders_with_items:
                                details_msg += f"- {so.bon_commande_ref}\n"
                        
                        details_msg += '\nVoulez-vous:'
                        details_msg += '\n- Annuler pour garder le client'  
                        details_msg += '\n- Retry pour supprimer TOUTES les commandes/devis ET le client (dangereux!)'
                        
                        result = QMessageBox.warning(
                            self, 
                            'Impossible de supprimer', 
                            details_msg,
                            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Retry,
                            QMessageBox.StandardButton.Cancel
                        )
                        
                        if result == QMessageBox.StandardButton.Retry:
                            # Force delete - remove all associated records first
                            try:
                                # Delete client orders
                                if orders_count > 0:
                                    client_orders = session.query(ClientOrder).filter(ClientOrder.client_id == client.id).all()
                                    for co in client_orders:
                                        session.delete(co)
                                
                                # Delete quotations
                                if quotations_count > 0:
                                    quotations = session.query(Quotation).filter(Quotation.client_id == client.id).all()
                                    for q in quotations:
                                        session.delete(q)
                                
                                # Delete supplier order line items
                                if supplier_order_items_count > 0:
                                    supplier_line_items = session.query(SupplierOrderLineItem).filter(SupplierOrderLineItem.client_id == client.id).all()
                                    for soli in supplier_line_items:
                                        session.delete(soli)
                                
                                session.commit()
                                QMessageBox.information(self, 'Nettoyage terminé', f'Toutes les commandes/devis associés au client "{client.name}" ont été supprimés.')
                                
                            except Exception as e:
                                session.rollback()
                                QMessageBox.critical(self, 'Erreur', f'Erreur lors du nettoyage: {str(e)}')
                                return
                        else:
                            return
                    
                    session.delete(client)
                    session.commit()
                    QMessageBox.information(self, 'Succès', f'Client "{client.name}" supprimé')
                    self.dashboard.add_activity("C", f"Client supprimé: {client.name}", "#DC3545")
                    self.refresh_all()
                    
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de l\'opération: {str(e)}')
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
                        material_reference=item_data.get('material_reference'),
                        is_cliche=item_data.get('is_cliche', False),
                        notes=item_data.get('notes')
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
                        material_reference=item_data.get('material_reference'),
                        is_cliche=item_data.get('is_cliche', False),
                        notes=item_data.get('notes')
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
                    
                    # Rabat de plaque = largeur de caisse / 2
                    rabat_plaque = largeur_caisse // 2  # Use integer division
                    
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
                    import json
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
                        original_line = None  # initialize to satisfy type checker; assigned when available
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
                            # Preserve original devis line details
                            notes=(
                                f"Depuis devis {plaque_data['quotation_reference']} - {plaque_data['notes']}\n"
                                f"[DEVIS_LINE_SNAPSHOT] " + json.dumps({
                                    'quotation_reference': plaque_data['quotation_reference'],
                                    'line_number': line_num,
                                    'description': original_line.description if (original_quotation and original_quotation.line_items and original_line) else None,
                                    'quantity_text': original_line.quantity if (original_quotation and original_quotation.line_items and original_line) else None,
                                    'unit_price': float((original_line.unit_price if (original_quotation and original_quotation.line_items and original_line) else 0) or 0),  # type: ignore[arg-type]
                                    'total_price': float((original_line.total_price if (original_quotation and original_quotation.line_items and original_line) else 0) or 0),  # type: ignore[arg-type]
                                    'length_mm': caisse_length,
                                    'width_mm': caisse_width,
                                    'height_mm': caisse_height,
                                    'color': (original_line.color.value if (original_quotation and original_quotation.line_items and original_line and original_line.color) else None),  # type: ignore[union-attr]
                                    'cardboard_type': original_line.cardboard_type if (original_quotation and original_quotation.line_items and original_line) else None,
                                    'material_reference': original_line.material_reference if (original_quotation and original_quotation.line_items and original_line) else None,
                                    'is_cliche': bool(original_line.is_cliche) if (original_quotation and original_quotation.line_items and original_line) else None,
                                    'notes': original_line.notes if (original_quotation and original_quotation.line_items and original_line) else None,
                                }, ensure_ascii=False)
                            )
                        )
                        session.add(line_item)
                    
                    # Update supplier order total
                    supplier_order.total_amount = total_amount  # type: ignore

                    # Embed snapshots for all source quotations
                    snapshots = []
                    for q in quotations:
                        snapshots.append({
                            'id': q.id,
                            'reference': q.reference,
                            'client_id': q.client_id,
                            'issue_date': str(q.issue_date) if q.issue_date else None,
                            'valid_until': str(q.valid_until) if q.valid_until else None,
                            'total_amount': float(q.total_amount or 0),  # type: ignore[arg-type]
                            'currency': q.currency,
                            'is_initial': bool(q.is_initial),
                            'notes': q.notes,
                            'line_items': [
                                {
                                    'line_number': li.line_number,
                                    'description': li.description,
                                    'quantity_text': li.quantity,
                                    'unit_price': float(li.unit_price or 0),  # type: ignore[arg-type]
                                    'total_price': float(li.total_price or 0),  # type: ignore[arg-type]
                                    'length_mm': li.length_mm,
                                    'width_mm': li.width_mm,
                                    'height_mm': li.height_mm,
                                    'color': (li.color.value if li.color else None),
                                    'cardboard_type': li.cardboard_type,
                                    'material_reference': li.material_reference,
                                    'is_cliche': li.is_cliche,
                                    'notes': li.notes,
                                }
                                for li in q.line_items
                            ]
                        })
                    existing_notes = supplier_order.notes or ""
                    supplier_order.notes = (existing_notes + "\n\n[DEVIS_SNAPSHOTS] " + json.dumps(snapshots, ensure_ascii=False)).strip()

                    session.commit()

                    # Delete all original quotations after successful transfer
                    for q in quotations:
                        session.delete(q)
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
                QMessageBox.warning(
                    self, 
                    'Devis Initial', 
                    'Les commandes de matières premières ne peuvent être créées que pour les Devis Finaux.\n\n'
                    'Veuillez d\'abord finaliser le devis avant de créer une commande de matières premières.'
                )
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

    def refresh_all(self) -> None:  # type: ignore[misc]
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
                    c.phone or "",
                    c.email or "",
                    c.address or "",
                    getattr(c, 'activity', '') or "",
                ]
                for c in clients
            ]
            self.clients_suppliers_split.load_right_data(clients_data)
            
            # Refresh orders (quotations only) - filter out orphaned and archived records
            quotations = session.query(Quotation).join(Quotation.client).filter(
                ~Quotation.notes.like('[ARCHIVED]%')
            ).all()
            
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
                
                # Format dates
                issue_date_str = str(q.issue_date) if q.issue_date else "N/A"
                valid_until_str = str(q.valid_until) if q.valid_until else "N/A"
                
                orders_data.append([
                    str(q.id),
                    str(q.reference or ""),
                    str(q.client.name if q.client else "N/A"),
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
            
            # Refresh client orders - filter out archived ones
            client_orders = session.query(ClientOrder).join(ClientOrder.client).filter(
                ~ClientOrder.notes.like('[ARCHIVED]%')
            ).all()
            client_orders_data = []
            client_order_colors = []
            
            # Map internal status values to display labels
            client_status_display_map = {
                'en_préparation': 'En Préparation',
                'en_production': 'En Production', 
                'terminé': 'Terminé',
                'confirmed': 'Confirmé'
            }
            
            for co in client_orders:
                # Skip client orders without valid client relationships
                if not co.client:
                    continue
                    
                # Format date
                creation_date_str = ""
                if co.created_at:
                    try:
                        import datetime
                        if isinstance(co.created_at, datetime.datetime):
                            creation_date_str = co.created_at.strftime("%d/%m/%Y")
                        else:
                            creation_date_str = str(co.created_at)
                    except (AttributeError, TypeError):
                        creation_date_str = str(co.created_at)
                
                # Format total amount
                total_amount_str = f"{co.total_amount:,.2f}" if hasattr(co, 'total_amount') and co.total_amount else "0.00"
                
                client_orders_data.append([
                    str(co.id),
                    str(co.reference or ""),
                    str(co.client.name if co.client else "N/A"),
                    client_status_display_map.get(co.status.value if co.status else "", "N/A"),
                    creation_date_str,
                    total_amount_str,
                    str((co.notes[:25] + "..." if co.notes and len(co.notes) > 25 else co.notes) or "")
                ])
                
                # Color coding based on status
                status_value = co.status.value if co.status else "en_préparation"
                if status_value == "en_préparation":
                    client_order_colors.append("#FFF3E0")  # Light orange for preparation
                elif status_value == "en_production":
                    client_order_colors.append("#E3F2FD")  # Light blue for production
                elif status_value == "terminé":
                    client_order_colors.append("#E8F5E8")  # Light green for complete
                elif status_value == "confirmed":
                    client_order_colors.append("#F3E5F5")  # Light purple for confirmed
                else:
                    client_order_colors.append("#FFFFFF")  # White for unknown status
            
            self.client_orders_grid.load_rows_with_colors(client_orders_data, client_order_colors)
            
            # Refresh supplier orders with comprehensive information - filter out archived ones
            supplier_orders = session.query(SupplierOrder).join(SupplierOrder.supplier).filter(
                ~SupplierOrder.notes.like('[ARCHIVED]%')
            ).all()
            
            # Map internal status values to display labels
            status_display_map = {
                'commande_initial': 'Commande Initial',
                'commande_passee': 'Commande Passée', 
                'commande_arrivee': 'Commande Arrivée',
                'partiellement_livre': 'Partiellement Livré',
                'termine': 'Terminé'
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
                elif status_value == "partiellement_livre":
                    supplier_order_colors.append("#FFF9C4")  # Light yellow for partially delivered
                elif status_value == "termine":
                    supplier_order_colors.append("#C8E6C9")  # Darker green for completed
                else:
                    supplier_order_colors.append("#FFFFFF")  # White for unknown status
            
            # Split data between the 4 status sections
            initial_orders_data = []        # Top Left: "Commandes Initiales"
            initial_order_colors = []
            ordered_data = []              # Top Right: "Commandes Passées" 
            ordered_colors = []
            partial_data = []              # Bottom Left: "Partiellement Livrée"
            partial_colors = []
            completed_data = []            # Bottom Right: "Terminée"
            completed_colors = []
            
            for i, so_data in enumerate(supplier_orders_data):
                status_col = so_data[3]  # Status column
                
                if status_col == "Commande Initial":
                    # Initial orders get simplified data (no status column)
                    initial_data = [so_data[0], so_data[1], so_data[2], so_data[4], so_data[5], so_data[6], so_data[7]]
                    initial_orders_data.append(initial_data)
                    initial_order_colors.append(supplier_order_colors[i])
                elif status_col == "Commande Passée":
                    # Ordered status goes to top right
                    ordered_data.append(so_data)
                    ordered_colors.append(supplier_order_colors[i])
                elif status_col == "Partiellement Livré":
                    # Partially delivered goes to bottom left
                    partial_data.append(so_data)
                    partial_colors.append(supplier_order_colors[i])
                elif status_col == "Terminé":
                    # Completed goes to bottom right
                    completed_data.append(so_data)
                    completed_colors.append(supplier_order_colors[i])
                else:
                    # Default: other statuses go to ordered section
                    ordered_data.append(so_data)
                    ordered_colors.append(supplier_order_colors[i])
            
            # Load data into quad view sections
            if self.supplier_orders_quad.top_left_grid:
                self.supplier_orders_quad.top_left_grid.load_rows_with_colors(initial_orders_data, initial_order_colors)
            if self.supplier_orders_quad.top_right_grid:
                self.supplier_orders_quad.top_right_grid.load_rows_with_colors(ordered_data, ordered_colors)
            if self.supplier_orders_quad.bottom_left_grid:
                self.supplier_orders_quad.bottom_left_grid.load_rows_with_colors(partial_data, partial_colors)
            if self.supplier_orders_quad.bottom_right_grid:
                self.supplier_orders_quad.bottom_right_grid.load_rows_with_colors(completed_data, completed_colors)
            
            # Refresh stock - Raw materials (receptions) on left side
            # Refresh stock - Raw materials (receptions) - filter out archived supplier orders
            receptions = session.query(Reception).join(Reception.supplier_order).filter(
                ~SupplierOrder.notes.like('[ARCHIVED]%'),
                ~Reception.notes.like('[ARCHIVED]%')
            ).all()
            
            # Group receptions by dimensions (extracted from notes) AND by client; sum quantities
            # Rules:
            # - Dimensions are parsed strictly from notes pattern: 'Arrivée matière: WxLxRmm'
            # - Merge only when BOTH dimensions AND the set of client IDs match
            # - If dimensions cannot be parsed (unknown), do not merge those receptions
            grouped_receptions = {}
            reception_groups = {}  # To track which receptions belong to each group
            
            for r in receptions:
                # Extract dimensions from notes (format: "Arrivée matière: 100x200x50mm")
                dimensions_key = "unknown"
                if r.notes and "Arrivée matière:" in r.notes:
                    try:
                        # Extract strictly the pattern '<W>x<L>x<R>mm' immediately following the label
                        import re
                        m = re.search(r"Arrivée matière:\s*([0-9]+x[0-9]+x[0-9]+)mm", r.notes)
                        if m:
                            dimensions_key = f"{m.group(1)}mm"  # e.g., '100x200x50mm'
                    except Exception:
                        pass
                
                # Get supplier order information
                bon_commande_ref = ""
                clients_list = []
                clients_ids_set = set()
                supplier_name = "N/A"
                
                if r.supplier_order:
                    # Get the bon de commande reference
                    bon_commande_ref = getattr(r.supplier_order, 'bon_commande_ref', 
                                             getattr(r.supplier_order, 'reference', ''))
                    supplier_name = r.supplier_order.supplier.name if r.supplier_order.supplier else "N/A"
                    
                    # Get unique clients from line items (for display) and stable client IDs (for grouping)
                    if hasattr(r.supplier_order, 'line_items') and r.supplier_order.line_items:
                        unique_clients = set()
                        for item in r.supplier_order.line_items:
                            if hasattr(item, 'client') and item.client:
                                unique_clients.add(item.client.name)
                            if hasattr(item, 'client_id') and item.client_id:
                                clients_ids_set.add(item.client_id)
                        clients_list = sorted(unique_clients)
                
                # Format clients display (keep exact list for grouping)
                clients_display = ", ".join(clients_list) if clients_list else "N/A"
                if len(clients_display) > 40:
                    clients_display = clients_display[:37] + "..."
                
                # Build a canonical clients key from sorted client IDs for grouping
                clients_key = ",".join(map(str, sorted(clients_ids_set))) if clients_ids_set else "N/A"

                # Do NOT merge when dimensions are unknown (avoid accidental merges)
                if dimensions_key == "unknown":
                    # Treat each reception as its own group using a unique key
                    group_key = f"{dimensions_key}|{clients_key}|{r.id}"
                else:
                    # Merge strictly when BOTH dimensions and client(s) match
                    group_key = f"{dimensions_key}|{clients_key}"
                
                if group_key not in grouped_receptions:
                    # First reception for these dimensions
                    grouped_receptions[group_key] = {
                        'ids': [r.id],
                        'reference': f"REC-{r.id}",
                        'quantity': r.quantity,
                        'supplier': supplier_name,
                        'bon_commande': bon_commande_ref or "N/A",
                        'clients': clients_display,
                        'date': getattr(r, 'reception_date', None) and getattr(r, 'reception_date').isoformat() or "",
                        'dimensions': dimensions_key
                    }
                else:
                    # Merge with existing group
                    group = grouped_receptions[group_key]
                    group['ids'].append(r.id)
                    group['quantity'] += r.quantity
                    # Update reference to show it's merged
                    if len(group['ids']) == 2:
                        group['reference'] = f"REC-{min(group['ids'])}-{max(group['ids'])}"
                    else:
                        group['reference'] = f"REC-{min(group['ids'])}+{len(group['ids'])-1}"
                    
                    # Keep the most recent date
                    current_date = getattr(r, 'reception_date', None) and getattr(r, 'reception_date').isoformat() or ""
                    if current_date > group['date']:
                        group['date'] = current_date
                    
                    # Merge bon commande references if different
                    current_bon = bon_commande_ref or "N/A"
                    if current_bon != group['bon_commande'] and current_bon != "N/A":
                        if group['bon_commande'] == "N/A":
                            group['bon_commande'] = current_bon
                        else:
                            group['bon_commande'] = f"{group['bon_commande']}, {current_bon}"
                    
                    # Merge clients if different
                    if clients_display != group['clients'] and clients_display != "N/A":
                        if group['clients'] == "N/A":
                            group['clients'] = clients_display
                        else:
                            combined_clients = f"{group['clients']}, {clients_display}"
                            if len(combined_clients) > 40:
                                combined_clients = combined_clients[:37] + "..."
                            group['clients'] = combined_clients
            
            # Convert grouped data to display format
            receptions_data = []
            for group_key, group in grouped_receptions.items():
                # Get quotation description for raw materials
                description = "N/A"

                # Try to get description from first reception in group
                if group['ids']:
                    first_reception_id = group['ids'][0]
                    try:
                        reception = session.query(Reception).filter(Reception.id == first_reception_id).first()
                        if reception:
                            # If arrival logic already stored a meaningful description in notes, prefer it
                            if reception.notes and reception.notes.strip() and not reception.notes.startswith("Arrivée matière:"):
                                description = reception.notes.strip()

                            if description == "N/A" and reception.supplier_order:
                                supplier_order = reception.supplier_order

                                # Get first line item to find client and quotation info
                                if hasattr(supplier_order, 'line_items') and supplier_order.line_items:
                                    first_line_item = supplier_order.line_items[0]

                                    # Use flexible client-based lookup: ANY client order for this client having a quotation
                                    if hasattr(first_line_item, 'client_id') and first_line_item.client_id:
                                        client_orders = session.query(ClientOrder).filter(
                                            ClientOrder.client_id == first_line_item.client_id,
                                            ClientOrder.quotation_id.isnot(None)
                                        ).all()

                                        for client_order in client_orders:
                                            if client_order.quotation:
                                                quotation = client_order.quotation

                                                # Search all line items for first non-empty description
                                                if quotation.line_items:
                                                    for q_line in quotation.line_items:
                                                        if q_line.description and q_line.description.strip():
                                                            description = q_line.description.strip()
                                                            break

                                                # Fallback to quotation notes if still not found
                                                if description == "N/A" and quotation.notes and quotation.notes.strip():
                                                    description = quotation.notes.strip()

                                                if description != "N/A":
                                                    break  # Stop once we have a description
                    except Exception as e:
                        print(f"Error fetching description for reception {first_reception_id}: {e}")
                        # Keep description as N/A if failure
                
                # Enrich description with dimension token so '100x200x50' searches match reliably
                desc_with_dims = description
                if group.get('dimensions') and group['dimensions'] != 'unknown':
                    try:
                        dims_ascii = group['dimensions'].replace('×', 'x')
                        desc_with_dims = f"{description} [{dims_ascii}]" if description != "N/A" else dims_ascii
                    except Exception:
                        pass

                receptions_data.append([
                    ",".join(map(str, group['ids'])),  # Store all IDs for context menu
                    str(group['quantity']),  # Quantity (summed)
                    group['supplier'],  # Supplier
                    group['bon_commande'],  # Bon Commande (merged)
                    group['clients'],  # Client(s) (merged)
                    desc_with_dims,  # Description + dimensions token
                    group['date'],  # Date (most recent)
                ])
            
            self.stock_split.load_left_data(receptions_data)
            
            # Refresh stock - Finished products (production) on right side
            # Filter out archived production batches
            production_batches = session.query(ProductionBatch).filter(
                ~ProductionBatch.batch_code.like('[ARCHIVED]%')
            ).all()
            
            # Use a dictionary to group items by client and dimensions
            grouped_items = {}
            
            for pb in production_batches:
                try:
                    # Get client order and related information
                    client_name = "N/A"
                    client_id = None
                    plaque_dims = "N/A"
                    caisse_dims = "N/A"
                    material_type = "N/A"
                    
                    if pb.client_order_id:
                        # Load client order first, then related data separately to avoid relationship issues
                        client_order = session.query(ClientOrder).filter(
                            ClientOrder.id == pb.client_order_id
                        ).first()
                        
                        if client_order:
                            # First, check supplier order line item for client info (priority)
                            # This often has the most accurate client information
                            if client_order.supplier_order_id:
                                try:
                                    supplier_order = session.query(SupplierOrder).filter(
                                        SupplierOrder.id == client_order.supplier_order_id
                                    ).first()
                                    
                                    if supplier_order:
                                        supplier_line_items = session.query(SupplierOrderLineItem).filter(
                                            SupplierOrderLineItem.supplier_order_id == supplier_order.id
                                        ).first()
                                        
                                        if supplier_line_items and supplier_line_items.client_id:
                                            # PRIORITY: Use client from supplier line item (most accurate)
                                            client = session.query(Client).filter(
                                                Client.id == supplier_line_items.client_id
                                            ).first()
                                            if client:
                                                client_name = client.name
                                                client_id = client.id
                                            
                                            # Get dimensions from supplier line item
                                            if supplier_line_items.caisse_length_mm and supplier_line_items.caisse_width_mm and supplier_line_items.caisse_height_mm:
                                                caisse_dims = f"{supplier_line_items.caisse_length_mm}×{supplier_line_items.caisse_width_mm}×{supplier_line_items.caisse_height_mm}"
                                
                                except Exception as supplier_error:
                                    print(f"Error loading supplier order for client order {client_order.id}: {supplier_error}")
                            
                            # FALLBACK: Get client information from client order if not found above
                            if client_name == "N/A" and client_order.client_id:
                                client = session.query(Client).filter(
                                    Client.id == client_order.client_id
                                ).first()
                                if client:
                                    client_name = client.name
                                    client_id = client.id
                            
                            # Get dimensions from quotation if available and not already found
                            if caisse_dims == "N/A" and client_order.quotation_id:
                                try:
                                    quotation = session.query(Quotation).filter(
                                        Quotation.id == client_order.quotation_id
                                    ).first()
                                    if quotation:
                                        quotation_lines = session.query(QuotationLineItem).filter(
                                            QuotationLineItem.quotation_id == quotation.id
                                        ).first()
                                        if quotation_lines and quotation_lines.length_mm and quotation_lines.width_mm and quotation_lines.height_mm:
                                            caisse_dims = f"{quotation_lines.length_mm}×{quotation_lines.width_mm}×{quotation_lines.height_mm}"
                                except Exception as quotation_error:
                                    print(f"Error loading quotation for client order {client_order.id}: {quotation_error}")
                    
                    # Get quotation description for finished products
                    description = "N/A"

                    # Priority 0: Stored description on production batch (persisted at creation)
                    if hasattr(pb, 'description') and pb.description and pb.description.strip():
                        description = pb.description.strip()
                    else:
                        # Try to get description from client order -> quotation (direct link)
                        if pb.client_order_id:
                            try:
                                client_order = session.query(ClientOrder).filter(
                                    ClientOrder.id == pb.client_order_id
                                ).first()

                                if client_order and client_order.quotation:
                                    quotation = client_order.quotation

                                    # Try all line items to find first non-empty description
                                    if quotation.line_items:
                                        for ql in quotation.line_items:
                                            if ql.description and ql.description.strip():
                                                description = ql.description.strip()
                                                break

                                    # Fallback to quotation notes
                                    if description == "N/A" and quotation.notes and quotation.notes.strip():
                                        description = quotation.notes.strip()

                                # FLEXIBLE FALLBACK: search other client orders for same client if still N/A
                                if description == "N/A" and client_id:
                                    related_orders = session.query(ClientOrder).filter(
                                        ClientOrder.client_id == client_id,
                                        ClientOrder.quotation_id.isnot(None)
                                    ).all()
                                    for co in related_orders:
                                        if co.quotation:
                                            q = co.quotation
                                            # Prefer line items
                                            if q.line_items:
                                                for ql in q.line_items:
                                                    if ql.description and ql.description.strip():
                                                        description = ql.description.strip()
                                                        break
                                            if description != "N/A":
                                                break
                                            if q.notes and q.notes.strip():
                                                description = q.notes.strip()
                                                break
                            except Exception as desc_error:
                                print(f"Error fetching description for production batch {pb.id}: {desc_error}")
                    
                    # Format production date
                    production_date = "N/A"
                    if hasattr(pb, 'production_date') and pb.production_date:
                        production_date = pb.production_date.strftime('%Y-%m-%d')
                    
                    # STRICT GROUPING: Only group if SAME CLIENT ID + SAME EXACT DIMENSIONS
                    # This ensures products are only merged if they truly belong to same client with identical specs
                    group_key = (client_id, caisse_dims)
                    
                    # Skip grouping if we don't have both client_id and dimensions
                    if client_id is None or caisse_dims == "N/A":
                        # Create unique key for ungroupable items to prevent incorrect merging
                        group_key = (f"ungroupable_{pb.id}", f"batch_{pb.id}")
                    
                    # Initialize group if it doesn't exist
                    if group_key not in grouped_items:
                        grouped_items[group_key] = {
                            'ids': [],
                            'client_name': client_name,
                            'dimensions': caisse_dims,
                            'total_quantity': 0,
                            'production_dates': [],
                            'description': description
                        }
                    
                    # Add to grouped items
                    group_item = grouped_items[group_key]
                    group_item['ids'].append(str(pb.id))
                    group_item['total_quantity'] += int(getattr(pb, 'quantity', 0) or 0)
                    if production_date != "N/A":
                        group_item['production_dates'].append(production_date)
                    
                    # If we don't have a description yet in the group, try to use this one
                    if group_item.get('description', 'N/A') == 'N/A' and description != 'N/A':
                        group_item['description'] = description
                    
                except Exception as e:
                    # Log the error for debugging
                    print(f"Error loading production batch {pb.id}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    
                    # Fallback data if there's an error loading details - use simpler approach
                    try:
                        # Simple fallback: just get basic client info without complex relationships
                        client_name = "Client inconnu"
                        if pb.client_order_id:
                            client_order = session.query(ClientOrder).filter(
                                ClientOrder.id == pb.client_order_id
                            ).first()
                            if client_order and client_order.client_id:
                                client = session.query(Client).filter(Client.id == client_order.client_id).first()
                                if client:
                                    client_name = client.name
                        
                        # Create simple group key without complex logic
                        group_key = (f"simple_{pb.id}", "N/A")
                        if group_key not in grouped_items:
                            grouped_items[group_key] = {
                                'ids': [],
                                'client_name': client_name,
                                'dimensions': "N/A",
                                'total_quantity': 0,
                                'production_dates': [],
                                'description': "N/A"
                            }
                        
                        group_item = grouped_items[group_key]
                        group_item['ids'].append(str(pb.id))
                        group_item['total_quantity'] += int(getattr(pb, 'quantity', 0) or 0)
                        
                    except Exception as fallback_error:
                        print(f"Fallback error for batch {pb.id}: {str(fallback_error)}")
                        # Ultimate fallback - just skip this batch
                        continue
            
            # Convert grouped items to display format
            production_data = []
            for group_key, group_data in grouped_items.items():
                # Always store the exact list of IDs in the first column (comma-separated)
                # This ensures downstream actions (like invoicing) can resolve real IDs.
                id_display = ",".join(group_data['ids'])
                
                # Use most recent production date if multiple
                production_date = "N/A"
                if group_data['production_dates']:
                    production_date = max(group_data['production_dates'])
                
                production_data.append([
                    id_display,
                    group_data['client_name'],
                    group_data['dimensions'],
                    str(group_data['total_quantity']),
                    group_data.get('description', 'N/A'),  # Description from quotation
                    production_date
                ])
            
            self.stock_split.load_right_data(production_data)
            
            # Update dashboard
            if hasattr(self, 'dashboard'):
                self.dashboard.refresh_data()
            # After data refresh, rebuild completer suggestions
            try:
                self._rebuild_search_completions_safe()
            except Exception:
                pass
            # Also rebuild dimension completers for stock searches
            try:
                self._rebuild_dim_completions_raw()
                self._rebuild_dim_completions_prod()
            except Exception:
                pass
                
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de l\'actualisation: {str(e)}')
        finally:
            if session is not None:
                session.close()

    def _on_supplier_order_double_click(self, row: int):
        """Handle double-click on supplier order row to show detailed view"""
        # Try to get data from either grid
        sender = self.sender()
        row_data = []
        
        # Use the get_row_data method if available
        try:
            if sender and hasattr(sender, 'get_row_data') and callable(getattr(sender, 'get_row_data', None)):
                row_data = sender.get_row_data(row)  # type: ignore
        except Exception as e:
            print(f"Error getting row data: {e}")
            return
        
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
        elif action_name == "export_pdf":
            self._export_supplier_order_pdf(order_id, reference)
        elif action_name.startswith("status_"):
            status_map = {
                "status_initial": "commande_initial",
                "status_ordered": "commande_passee", 
                "status_received": "commande_arrivee",
                "status_partial": "partiellement_livre",
                "status_completed": "termine"
            }
            new_status = status_map.get(action_name)
            if new_status:
                self._change_supplier_order_status(order_id, reference, new_status)

    def _export_supplier_order_pdf(self, order_id: int, reference: str):
        """Export supplier order as a professional PDF document using template"""
        try:
            # Generate PDF using the template-based export service
            pdf_path = export_supplier_order_to_pdf(order_id)
            
            if pdf_path:
                # Show success message with option to open file
                reply = QMessageBox.question(
                    self,
                    'PDF Généré',
                    f'Le PDF de la commande {reference} a été généré avec succès.\n\n'
                    f'Fichier: {pdf_path.name}\n\n'
                    'Voulez-vous ouvrir le fichier?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    # Open PDF with default system application
                    if os.name == 'nt':  # Windows
                        os.startfile(str(pdf_path))
                    elif os.name == 'posix':  # macOS and Linux
                        subprocess.run(['xdg-open', str(pdf_path)])
                    
                # Log activity
                self.dashboard.add_activity("PDF", f"Export PDF commande: {reference}", "#DC3545")
                
            else:
                QMessageBox.warning(
                    self,
                    'Erreur',
                    f'Erreur lors de la génération du PDF pour la commande {reference}.\n\n'
                    'Vérifiez que les données de la commande sont complètes et que le template page.pdf est disponible.'
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                'Erreur',
                f'Erreur lors de l\'export PDF: {str(e)}'
            )

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
                'commande_arrivee': SupplierOrderStatus.RECEIVED,
                'partiellement_livre': SupplierOrderStatus.PARTIALLY_DELIVERED,
                'termine': SupplierOrderStatus.COMPLETED
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
                'commande_arrivee': 'Commande Arrivée',
                'partiellement_livre': 'Partiellement Livré',
                'termine': 'Terminé'
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

    def _new_client_order(self) -> None:
        """Create a new client order."""
        QMessageBox.information(self, 'Info', 'Création de nouvelle commande client - Fonctionnalité à implémenter')

    def _handle_client_orders_context_menu(self, action_name: str, row: int, row_data: list):
        """Handle client orders context menu actions"""
        if action_name == "delete":
            if len(row_data) > 1:
                order_id = int(row_data[0])
                reference = row_data[1]
                self._delete_client_order_by_id(order_id, reference)
        elif action_name == "edit":
            QMessageBox.information(self, 'Info', 'Modification de commande client - Fonctionnalité à implémenter')
        elif action_name.startswith("status_"):
            if len(row_data) > 0:
                order_id = int(row_data[0])
                new_status = action_name.replace("status_", "")
                self._update_client_order_status(order_id, new_status)

    def _delete_client_order_by_id(self, order_id: int, reference: str):
        """Delete a client order by ID"""
        reply = QMessageBox.question(
            self, 'Confirmation', 
            f'Êtes-vous sûr de vouloir supprimer la commande client {reference} ?\n\nCette action est irréversible.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        session = SessionLocal()
        try:
            client_order = session.get(ClientOrder, order_id)
            if client_order:
                session.delete(client_order)
                session.commit()
                QMessageBox.information(self, 'Succès', f'Commande client {reference} supprimée avec succès')
                self.refresh_all()
            else:
                QMessageBox.warning(self, 'Erreur', 'Commande introuvable')
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de la suppression: {str(e)}')
        finally:
            session.close()

    def _update_client_order_status(self, order_id: int, new_status: str):
        """Update client order status"""
        from models.orders import ClientOrderStatus
        
        status_map = {
            'preparation': ClientOrderStatus.IN_PREPARATION,
            'production': ClientOrderStatus.IN_PRODUCTION,
            'complete': ClientOrderStatus.COMPLETE
        }
        
        if new_status not in status_map:
            QMessageBox.warning(self, 'Erreur', f'Statut invalide: {new_status}')
            return
            
        session = SessionLocal()
        try:
            client_order = session.get(ClientOrder, order_id)
            if client_order:
                client_order.status = status_map[new_status]
                session.commit()
                QMessageBox.information(self, 'Succès', 'Statut mis à jour')
                self.refresh_all()
            else:
                QMessageBox.warning(self, 'Erreur', 'Commande introuvable')
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de la mise à jour: {str(e)}')
        finally:
            session.close()

    def _on_client_order_double_click(self, row: int):
        """Handle double-click on client order row"""
        QMessageBox.information(self, 'Info', 'Détails de commande client - Fonctionnalité à implémenter')

    def _raw_material_arrival(self):
        """Open dialog for raw material arrival registration"""
        try:
            from ui.dialogs.raw_material_arrival_dialog import RawMaterialArrivalDialog
            
            dialog = RawMaterialArrivalDialog(self)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Refresh the stock data after successful registration
                self.refresh_all()
                
                # Log the activity in dashboard if available
                if hasattr(self, 'dashboard') and self.dashboard:
                    entries = dialog.get_material_entries()
                    total_quantity = sum(entry['quantity'] for entry in entries)
                    self.dashboard.add_activity(
                        "Stock", 
                        f"Arrivée matière première: {total_quantity} plaques", 
                        "#28a745"
                    )
                    
        except ImportError as e:
            QMessageBox.critical(self, 'Erreur', f'Erreur d\'importation du dialogue: {str(e)}')
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de l\'ouverture du dialogue: {str(e)}')

    def _handle_stock_context_menu(self, action_name: str, row: int, row_data: list):
        """Handle context menu actions for stock items (raw materials)"""
        if action_name == "edit":
            self._edit_reception(row_data)
        elif action_name == "delete":
            self._delete_reception(row_data)
        elif action_name == "print_label":
            self._print_raw_material_label(row_data)
        elif action_name == "move_to_archive":
            self._move_reception_to_archive(row_data)

    def _move_reception_to_archive(self, row_data: list):
        """Archive one or multiple receptions (raw materials) by prefixing notes with [ARCHIVED]."""
        from PyQt6.QtWidgets import QMessageBox
        from datetime import datetime
        from models.orders import Reception, ClientOrder, Quotation, QuotationLineItem, SupplierOrder, SupplierOrderLineItem
        session = SessionLocal()
        try:
            if not row_data:
                QMessageBox.warning(self, 'Erreur', 'Données de réception invalides')
                return
            # First column holds comma separated IDs
            id_str = row_data[0]
            try:
                reception_ids = [int(x.strip()) for x in id_str.split(',') if x.strip()]
            except ValueError:
                QMessageBox.warning(self, 'Erreur', 'ID(s) de réception invalides')
                return

            reply = QMessageBox.question(
                self,
                'Confirmer archivage',
                f"Archiver {len(reception_ids)} réception(s) sélectionnée(s) ?\n\nElles seront retirées du stock actif et visibles dans l'onglet Archive (Matières Premières).",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

            archived_count = 0
            for rid in reception_ids:
                reception = session.query(Reception).filter(Reception.id == rid).first()
                if not reception:
                    continue
                if reception.notes and reception.notes.startswith('[ARCHIVED]'):
                    continue  # already archived

                # Attempt to enrich description if current notes are generic
                enriched_description = None
                try:
                    # If notes exist and are not generic arrival auto text, reuse
                    if reception.notes and reception.notes.strip() and not reception.notes.startswith('Arrivée matière:'):
                        enriched_description = reception.notes.strip()
                    else:
                        # Derive from related supplier order -> client order -> quotation line items
                        if reception.supplier_order_id:
                            supplier_order = session.query(SupplierOrder).filter(SupplierOrder.id == reception.supplier_order_id).first()
                            if supplier_order and supplier_order.line_items:
                                so_line = supplier_order.line_items[0]
                                # Find any client order for that client with quotation
                                client_orders = session.query(ClientOrder).filter(
                                    ClientOrder.client_id == so_line.client_id,
                                    ClientOrder.quotation_id.isnot(None)
                                ).all()
                                for co in client_orders:
                                    if co.quotation:
                                        q = co.quotation
                                        if q.line_items:
                                            for ql in q.line_items:
                                                if ql.description and ql.description.strip():
                                                    enriched_description = ql.description.strip()
                                                    break
                                            if enriched_description:
                                                break
                                        if (not enriched_description) and q.notes and q.notes.strip():
                                            enriched_description = q.notes.strip()
                                    if enriched_description:
                                        break
                except Exception as enrich_err:
                    print(f"Warning: could not derive description for reception {rid}: {enrich_err}")

                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
                base_desc = enriched_description or (reception.notes.strip() if reception.notes else 'Matière première')
                reception.notes = f"[ARCHIVED] {timestamp} | {base_desc}"
                archived_count += 1

            session.commit()
            QMessageBox.information(self, 'Archivage terminé', f'{archived_count} réception(s) archivée(s).')
            self.refresh_all()
            if hasattr(self, 'archive_widget'):
                self.archive_widget.refresh_all_data()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, 'Erreur', f'Echec archivage: {e}')
        finally:
            session.close()

    def _on_stock_double_click(self, row: int):
        """Handle double-click on stock item (raw materials)"""
        if not self.receptions_grid or not self.receptions_grid.table:
            return
            
        # Get row data directly from table
        row_data = []
        for col in range(self.receptions_grid.table.columnCount()):
            item = self.receptions_grid.table.item(row, col)
            if item:
                row_data.append(item.text())
            else:
                row_data.append('')
                
        if row_data:
            self._show_reception_details(row_data)

    def _handle_production_context_menu(self, action_name: str, row: int, row_data: list):
        """Handle context menu actions for production items (finished products)"""
        if action_name == "edit":
            self._edit_production(row_data)
        elif action_name == "delete":
            self._delete_production(row_data)
        elif action_name == "multi_delete":
            self._delete_multiple_productions()
        elif action_name == "print_fiche":
            self._print_finished_product_fiche(row_data)
        elif action_name == "print_delivery":
            self._print_delivery_note_for_selection()
        elif action_name == "create_invoice":
            self._create_invoice_for_selection(row_data)
        elif action_name == "print_invoice":
            self._print_invoice_for_selection()
        elif action_name == "move_to_archive":
            self._move_production_to_archive(row_data)

    def _move_production_to_archive(self, row_data: list):
        """Move production batch to archive"""
        from PyQt6.QtWidgets import QMessageBox
        from config.database import SessionLocal
        from models.production import ProductionBatch
        from models.orders import ClientOrder, Quotation, SupplierOrder, QuotationLineItem, SupplierOrderLineItem
        import json
        from datetime import datetime
        
        if not row_data or len(row_data) < 1:
            QMessageBox.warning(self, 'Erreur', 'Données de production invalides')
            return
        
        # Parse production batch IDs (might be comma-separated for grouped items)
        production_ids_str = row_data[0]
        try:
            production_ids = [int(id_str.strip()) for id_str in production_ids_str.split(',')]
        except (ValueError, AttributeError):
            QMessageBox.warning(self, 'Erreur', 'ID de production invalide')
            return
        
        client_name = row_data[1] if len(row_data) > 1 else "N/A"
        dimensions = row_data[2] if len(row_data) > 2 else "N/A"
        quantity = row_data[3] if len(row_data) > 3 else "N/A"
        
        # Confirm the action
        reply = QMessageBox.question(
            self,
            'Confirmer l\'archivage',
            f'Êtes-vous sûr de vouloir archiver cette production ?\n\n'
            f'Client: {client_name}\n'
            f'Dimensions: {dimensions}\n'
            f'Quantité: {quantity}\n\n'
            f'Cette action déplacera SEULEMENT ce produit fini vers l\'archive.\n'
            f'Les matières premières, devis et commandes associés resteront actifs.\n\n'
            f'Cette action peut être annulée depuis l\'onglet Archive.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        session = SessionLocal()
        try:
            # Get all production batches to archive
            production_batches = session.query(ProductionBatch).filter(
                ProductionBatch.id.in_(production_ids)
            ).all()
            
            if not production_batches:
                QMessageBox.warning(self, 'Erreur', 'Aucun lot de production trouvé')
                return
            
            archived_items = []
            
            # Build archive detail payload joined from devis (quotation) and supplier order
            def _build_archive_detail(batches):
                try:
                    first = batches[0]
                except Exception:
                    return None
                co = session.query(ClientOrder).filter(ClientOrder.id == first.client_order_id).first() if first.client_order_id else None
                client_name = co.client.name if co and co.client else "N/A"
                # Quotation details
                q_ref = None
                q_desc = None
                caisse_dims = None
                cardboard_type = None
                color = None
                unit_price = None
                total_price = None
                if co and co.quotation:
                    q_ref = co.quotation.reference
                    if co.quotation.line_items:
                        li: QuotationLineItem = co.quotation.line_items[0]
                        q_desc = (li.description or '').strip() or None
                        if li.length_mm and li.width_mm and li.height_mm:
                            caisse_dims = f"{li.length_mm}×{li.width_mm}×{li.height_mm}mm"
                        cardboard_type = li.cardboard_type
                        try:
                            _col = getattr(li, 'color', None)
                            color = _col.value if _col is not None else None
                        except Exception:
                            color = None
                        try:
                            unit_price = float(li.unit_price) if li.unit_price is not None else 0.0  # type: ignore[arg-type]
                        except Exception:
                            unit_price = 0.0
                        try:
                            total_price = float(li.total_price) if li.total_price is not None else 0.0  # type: ignore[arg-type]
                        except Exception:
                            total_price = 0.0
                # Supplier order details
                so_ref = None
                plaque_dims = None
                plaque_price = None
                so_total_amount = None
                if co and getattr(co, 'supplier_order', None):
                    so: SupplierOrder = co.supplier_order
                    so_ref = getattr(so, 'bon_commande_ref', None) or getattr(so, 'reference', None)
                    try:
                        so_total_amount = float(getattr(so, 'total_amount', 0) or 0)  # type: ignore[arg-type]
                    except Exception:
                        so_total_amount = 0.0
                    if so.line_items:
                        sli: SupplierOrderLineItem = so.line_items[0]
                        w = getattr(sli, 'plaque_width_mm', None)
                        L = getattr(sli, 'plaque_length_mm', None)
                        r = getattr(sli, 'plaque_flap_mm', None)
                        if w and L:
                            plaque_dims = f"{w}×{L}mm" + (f" (Rabat: {r}mm)" if r else "")
                        try:
                            plaque_price = float(getattr(sli, 'prix_uttc_plaque', 0) or 0)  # type: ignore[arg-type]
                        except Exception:
                            plaque_price = 0.0

                detail = {
                    'archived_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'production_batch_ids': [int(b.id) for b in batches],
                    'client': client_name,
                    'quotation': {
                        'reference': q_ref,
                        'description': q_desc,
                        'caisse_dimensions': caisse_dims,
                        'cardboard_type': cardboard_type,
                        'color': color,
                        'unit_price': unit_price,
                        'total_price': total_price,
                    },
                    'supplier_order': {
                        'reference': so_ref,
                        'plaque_dimensions': plaque_dims,
                        'prix_uttc_plaque': plaque_price,
                        'total_amount': so_total_amount,
                    }
                }
                return detail

            # Archive ONLY the production batches themselves (no cascading)
            for pb in production_batches:
                # Mark production batch as archived by modifying batch_code
                if not pb.batch_code.startswith("[ARCHIVED]"):
                    pb.batch_code = f"[ARCHIVED] {pb.batch_code}"
                
                archived_items.append(f"Produit fini: {pb.batch_code}")
            
            # Append structured archive note into ClientOrder.notes for traceability
            try:
                if production_batches:
                    co_id = production_batches[0].client_order_id
                    if co_id:
                        co = session.query(ClientOrder).filter(ClientOrder.id == co_id).first()
                        if co is not None:
                            detail = _build_archive_detail(production_batches)
                            if detail:
                                block = "[ARCHIVE_DETAIL] " + json.dumps(detail, ensure_ascii=False)
                                existing = (co.notes or '').strip()
                                co.notes = (existing + "\n" + block).strip() if existing else block
            except Exception as note_err:
                print(f"Warning: failed to append archive note: {note_err}")

            # Commit the changes (only production batches are archived)
            session.commit()
            
            # Show success message with summary
            archived_summary = '\n'.join(archived_items)
            QMessageBox.information(
                self,
                'Archivage terminé',
                f'Les produits finis suivants ont été archivés :\n\n{archived_summary}\n\n'
                f'Les matières premières, devis et commandes associés restent actifs et disponibles.'
            )
            
            # Refresh the grids to hide archived items
            self.refresh_all()
            
        except Exception as e:
            session.rollback()
            QMessageBox.critical(
                self,
                'Erreur',
                f'Erreur lors de l\'archivage : {str(e)}'
            )
        finally:
            session.close()

    def _on_production_double_click(self, row: int):
        """Handle double-click on production item (finished products)"""
        if not self.production_grid or not self.production_grid.table:
            return
            
        # Get row data directly from table
        row_data = []
        for col in range(self.production_grid.table.columnCount()):
            item = self.production_grid.table.item(row, col)
            if item:
                row_data.append(item.text())
            else:
                row_data.append('')
                
        if row_data:
            self._show_production_details(row_data)

    def _edit_reception(self, row_data: list):
        """Edit a reception record or manage merged receptions"""
        reception_ids_str = row_data[0]
        reception_ref = row_data[1]  # Reference column
        
        # Handle multiple IDs (comma-separated for merged entries)
        reception_ids = [int(id_str.strip()) for id_str in reception_ids_str.split(',')]
        
        if len(reception_ids) == 1:
            # Single reception - show simple quantity edit
            reception_id = reception_ids[0]
            self._show_single_reception_edit_dialog(reception_id)
        else:
            # Multiple receptions - show advanced management dialog
            self._show_merged_reception_edit_dialog(reception_ids, reception_ref)

    def _show_single_reception_edit_dialog(self, reception_id: int):
        """Show dialog to edit quantity of a single reception"""
        try:
            session = SessionLocal()
            try:
                reception = session.get(Reception, reception_id)
                if not reception:
                    QMessageBox.warning(self, 'Erreur', 'Réception non trouvée')
                    return
                
                # Create dialog
                dialog = QDialog(self)
                dialog.setWindowTitle(f'Modifier Réception REC-{reception.id}')
                dialog.setMinimumWidth(400)
                
                layout = QVBoxLayout(dialog)
                
                # Info label
                info_label = QLabel(f'Référence: REC-{reception.id}\n'
                                  f'Date: {reception.reception_date}\n'
                                  f'Notes: {reception.notes or "Aucune"}')
                layout.addWidget(info_label)
                
                # Quantity input
                qty_layout = QHBoxLayout()
                qty_layout.addWidget(QLabel('Quantité:'))
                qty_input = QLineEdit(str(reception.quantity))
                qty_layout.addWidget(qty_input)
                layout.addLayout(qty_layout)
                
                # Buttons
                button_layout = QHBoxLayout()
                save_btn = QPushButton('Sauvegarder')
                cancel_btn = QPushButton('Annuler')
                button_layout.addWidget(save_btn)
                button_layout.addWidget(cancel_btn)
                layout.addLayout(button_layout)
                
                # Connect buttons
                save_btn.clicked.connect(lambda: self._save_single_reception_edit(
                    dialog, reception_id, qty_input.text()))
                cancel_btn.clicked.connect(dialog.reject)
                
                dialog.exec()
            finally:
                session.close()
                
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de l\'édition: {str(e)}')

    def _save_single_reception_edit(self, dialog: QDialog, reception_id: int, new_quantity: str):
        """Save changes to a single reception"""
        try:
            quantity = int(float(new_quantity.replace(',', '.')))
            if quantity <= 0:
                QMessageBox.warning(dialog, 'Erreur', 'La quantité doit être positive')
                return
                
            session = SessionLocal()
            try:
                reception = session.get(Reception, reception_id)
                if reception:
                    reception.quantity = quantity
                    session.commit()
                    dialog.accept()
                    self._load_stock_data()  # Refresh stock display
                    QMessageBox.information(self, 'Succès', 'Quantité mise à jour avec succès')
                else:
                    QMessageBox.warning(dialog, 'Erreur', 'Réception non trouvée')
            finally:
                session.close()
                    
        except ValueError:
            QMessageBox.warning(dialog, 'Erreur', 'Quantité invalide')
        except Exception as e:
            QMessageBox.critical(dialog, 'Erreur', f'Erreur lors de la sauvegarde: {str(e)}')

    def _show_merged_reception_edit_dialog(self, reception_ids: list, reception_ref: str):
        """Show dialog to manage merged receptions"""
        try:
            session = SessionLocal()
            try:
                receptions = session.query(Reception).filter(Reception.id.in_(reception_ids)).all()
                
                if not receptions:
                    QMessageBox.warning(self, 'Erreur', 'Réceptions non trouvées')
                    return
                
                # Create dialog
                dialog = QDialog(self)
                dialog.setWindowTitle(f'Gérer Réceptions Groupées ({reception_ref})')
                dialog.setMinimumWidth(600)
                dialog.setMinimumHeight(400)
                
                layout = QVBoxLayout(dialog)
                
                # Info label
                info_label = QLabel(f'Réferences groupées: {reception_ref}\n'
                                  f'Nombre de réceptions: {len(receptions)}')
                layout.addWidget(info_label)
                
                # Table for individual receptions
                from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
                table = QTableWidget()
                table.setColumnCount(4)
                table.setHorizontalHeaderLabels(['Référence', 'Quantité', 'Date', 'Actions'])
                table.setRowCount(len(receptions))
                
                # Populate table
                for row, reception in enumerate(receptions):
                    table.setItem(row, 0, QTableWidgetItem(f"REC-{reception.id}"))
                    
                    # Editable quantity
                    qty_item = QTableWidgetItem(str(reception.quantity))
                    table.setItem(row, 1, qty_item)
                    
                    table.setItem(row, 2, QTableWidgetItem(str(reception.reception_date)))
                    
                    # Delete button
                    delete_btn = QPushButton('Supprimer')
                    delete_btn.clicked.connect(lambda checked, r_id=reception.id: 
                                             self._delete_individual_reception(r_id, dialog))
                    table.setCellWidget(row, 3, delete_btn)
                
                # Auto-resize columns
                header = table.horizontalHeader()
                if header:
                    header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
                    header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
                    header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
                    header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
                
                layout.addWidget(table)
                
                # Buttons
                button_layout = QHBoxLayout()
                save_btn = QPushButton('Sauvegarder Quantités')
                close_btn = QPushButton('Fermer')
                button_layout.addWidget(save_btn)
                button_layout.addWidget(close_btn)
                layout.addLayout(button_layout)
                
                # Connect buttons
                save_btn.clicked.connect(lambda: self._save_merged_reception_quantities(
                    dialog, table, receptions))
                close_btn.clicked.connect(dialog.accept)
                
                dialog.exec()
            finally:
                session.close()
                
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de l\'ouverture du dialogue: {str(e)}')

    def _save_merged_reception_quantities(self, dialog: QDialog, table, receptions: list):
        """Save quantity changes for merged receptions"""
        try:
            session = SessionLocal()
            try:
                for row, reception in enumerate(receptions):
                    qty_item = table.item(row, 1)
                    if qty_item:
                        new_quantity = int(float(qty_item.text().replace(',', '.')))
                        if new_quantity <= 0:
                            QMessageBox.warning(dialog, 'Erreur', 
                                              f'La quantité pour REC-{reception.id} doit être positive')
                            return
                        
                        # Update reception
                        db_reception = session.get(Reception, reception.id)
                        if db_reception:
                            db_reception.quantity = new_quantity
                
                session.commit()
                self._load_stock_data()
                QMessageBox.information(self, 'Succès', 'Quantités mises à jour avec succès')
            finally:
                session.close()
                
        except ValueError:
            QMessageBox.warning(dialog, 'Erreur', 'Quantité invalide détectée')
        except Exception as e:
            QMessageBox.critical(dialog, 'Erreur', f'Erreur lors de la sauvegarde: {str(e)}')

    def _delete_individual_reception(self, reception_id: int, parent_dialog: QDialog):
        """Delete an individual reception from a merged group"""
        try:
            session = SessionLocal()
            try:
                reception = session.get(Reception, reception_id)
                if not reception:
                    QMessageBox.warning(parent_dialog, 'Erreur', 'Réception non trouvée')
                    return
                
                reply = QMessageBox.question(
                    parent_dialog,
                    'Confirmer la suppression',
                    f'Êtes-vous sûr de vouloir supprimer la réception "REC-{reception.id}"?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    session.delete(reception)
                    session.commit()
                    parent_dialog.accept()  # Close dialog to refresh
                    self._load_stock_data()
                    QMessageBox.information(self, 'Succès', 'Réception supprimée avec succès')
            finally:
                session.close()
                    
        except Exception as e:
            QMessageBox.critical(parent_dialog, 'Erreur', f'Erreur lors de la suppression: {str(e)}')

    def _delete_reception(self, row_data: list):
        """Delete a reception record (or multiple merged records)"""
        reception_ids_str = row_data[0]
        reception_ref = row_data[1]  # Reference column
        
        # Handle multiple IDs (comma-separated for merged entries)
        reception_ids = [int(id_str.strip()) for id_str in reception_ids_str.split(',')]
        
        if len(reception_ids) == 1:
            message = f'Êtes-vous sûr de vouloir supprimer la réception "{reception_ref}"?'
        else:
            message = f'Êtes-vous sûr de vouloir supprimer les {len(reception_ids)} réceptions groupées "{reception_ref}"?'
        
        reply = QMessageBox.question(
            self, 
            'Confirmer la suppression',
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            session = SessionLocal()
            try:
                deleted_count = 0
                for reception_id in reception_ids:
                    reception = session.get(Reception, reception_id)
                    if reception:
                        session.delete(reception)
                        deleted_count += 1
                
                session.commit()
                
                if deleted_count > 0:
                    if deleted_count == 1:
                        QMessageBox.information(self, 'Succès', 'Réception supprimée avec succès')
                    else:
                        QMessageBox.information(self, 'Succès', f'{deleted_count} réceptions supprimées avec succès')
                    self.refresh_all()
                else:
                    QMessageBox.warning(self, 'Erreur', 'Aucune réception trouvée')
                    
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, 'Erreur', f'Erreur lors de la suppression: {str(e)}')
            finally:
                session.close()

    def _show_reception_details(self, row_data: list):
        """Show detailed information about a reception (or multiple merged receptions)"""
        reception_ids_str = row_data[0]
        
        # Handle multiple IDs (comma-separated for merged entries)
        reception_ids = [int(id_str.strip()) for id_str in reception_ids_str.split(',')]
        
        session = SessionLocal()
        try:
            if len(reception_ids) == 1:
                # Single reception
                reception = session.get(Reception, reception_ids[0])
                if reception:
                    details = f"""Détails de la Réception
                    
ID: {reception.id}
Référence: {getattr(reception, 'reference', '') or f"REC-{reception.id}"}
Quantité: {reception.quantity}
Date de réception: {reception.reception_date}
Fournisseur: {reception.supplier_order.supplier.name if reception.supplier_order and reception.supplier_order.supplier else "N/A"}
Bon de commande: {getattr(reception.supplier_order, 'bon_commande_ref', '') if reception.supplier_order else "N/A"}
Notes: {reception.notes or "Aucune note"}"""
                    
                    QMessageBox.information(self, 'Détails de la Réception', details)
                else:
                    QMessageBox.warning(self, 'Erreur', 'Réception introuvable')
            else:
                # Multiple merged receptions
                receptions = []
                total_quantity = 0
                dimensions = "N/A"
                suppliers = set()
                dates = []
                
                for reception_id in reception_ids:
                    reception = session.get(Reception, reception_id)
                    if reception:
                        receptions.append(reception)
                        total_quantity += reception.quantity
                        dates.append(reception.reception_date)
                        
                        if reception.supplier_order and reception.supplier_order.supplier:
                            suppliers.add(reception.supplier_order.supplier.name)
                        
                        # Extract dimensions from first reception's notes
                        if dimensions == "N/A" and reception.notes and "Arrivée matière:" in reception.notes:
                            try:
                                parts = reception.notes.split(":")
                                if len(parts) > 1:
                                    dim_part = parts[1].strip()
                                    if "mm" in dim_part:
                                        dimensions = dim_part
                            except:
                                pass
                
                if receptions:
                    details = f"""Détails des Réceptions Groupées

Nombre de réceptions: {len(receptions)}
IDs: {', '.join(map(str, reception_ids))}
Dimensions: {dimensions}
Quantité totale: {total_quantity}
Fournisseur(s): {', '.join(suppliers) if suppliers else "N/A"}
Dates: {min(dates)} à {max(dates)}

Détails individuels:"""
                    
                    for i, reception in enumerate(receptions, 1):
                        details += f"""
  {i}. REC-{reception.id}: {reception.quantity} unités le {reception.reception_date}"""
                    
                    QMessageBox.information(self, 'Détails des Réceptions Groupées', details)
                else:
                    QMessageBox.warning(self, 'Erreur', 'Aucune réception trouvée')
                    
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de la récupération des détails: {str(e)}')
        finally:
            session.close()

    def _add_finished_product(self):
        """Add a new finished product from raw materials"""
        from ui.dialogs.add_finished_product_dialog import AddFinishedProductDialog
        from models.production import ProductionBatch
        
        dialog = AddFinishedProductDialog(self)
        if dialog.exec():
            data = dialog.get_production_data()
            if not data:
                return
                
            session = SessionLocal()
            try:
                # Create production batch record
                material_data = data['material_data']
                line_item = material_data['line_item']
                supplier_order = material_data['supplier_order']
                
                # Create a client order if one doesn't exist for this supplier order
                from models.orders import ClientOrder, ClientOrderStatus
                
                existing_client_order = session.query(ClientOrder).filter(
                    ClientOrder.supplier_order_id == supplier_order.id
                ).first()
                
                if existing_client_order:
                    client_order_id = existing_client_order.id
                else:
                    # Create new client order using unified reference system
                    from utils.reference_generator import generate_client_order_reference
                    client_order = ClientOrder(
                        client_id=line_item.client_id,
                        supplier_order_id=supplier_order.id,
                        reference=generate_client_order_reference(supplier_order.bon_commande_ref),
                        status=ClientOrderStatus.IN_PRODUCTION,
                        total_amount=0,  # Will be calculated later
                        notes=f"Commande créée automatiquement pour production {data['batch_code']}"
                    )
                    session.add(client_order)
                    session.flush()  # Get the ID
                    client_order_id = client_order.id
                
                # Parse production date
                from datetime import datetime as dt
                production_date = None
                if data.get('production_date'):
                    try:
                        production_date = dt.strptime(data['production_date'], '%Y-%m-%d').date()
                    except:
                        production_date = dt.now().date()
                else:
                    production_date = dt.now().date()

                # Check if a production batch with same characteristics already exists
                # Same characteristics: same client_order_id (which includes client and dimensions)
                existing_batch = session.query(ProductionBatch).filter(
                    ProductionBatch.client_order_id == client_order_id
                ).first()
                
                if existing_batch:
                    # Add quantity to existing batch instead of creating new one
                    old_quantity = existing_batch.quantity
                    existing_batch.quantity += data['quantity_produced']

                    # If the existing batch was archived, automatically restore it
                    if existing_batch.batch_code.startswith('[ARCHIVED]'):
                        restored_code = existing_batch.batch_code.replace('[ARCHIVED]', '').strip()
                        print(f"DEBUG: Existing batch {existing_batch.id} was archived. Restoring code to '{restored_code}'")
                        existing_batch.batch_code = restored_code
                        # Optional: notify user it was restored
                        try:
                            QMessageBox.information(
                                self,
                                "Lot restauré",
                                "Le lot existant était archivé et a été restauré automatiquement pour recevoir la nouvelle production."
                            )
                        except Exception:
                            pass

                    # Populate description if missing
                    if (not existing_batch.description) or (not existing_batch.description.strip()):
                        try:
                            # Attempt to derive description from any quotation for same client
                            from models.orders import ClientOrder, Quotation, QuotationLineItem
                            line_client_id = line_item.client_id
                            related_orders = session.query(ClientOrder).filter(
                                ClientOrder.client_id == line_client_id,
                                ClientOrder.quotation_id.isnot(None)
                            ).all()
                            derived_description = None
                            for co in related_orders:
                                if co.quotation and co.quotation.line_items:
                                    for ql in co.quotation.line_items:
                                        if ql.description and ql.description.strip():
                                            derived_description = ql.description.strip()
                                            break
                                    if derived_description:
                                        break
                                if (not derived_description) and co.quotation and co.quotation.notes and co.quotation.notes.strip():
                                    derived_description = co.quotation.notes.strip()
                            # Fallback to any reception note used
                            if (not derived_description) and material_data.get('receptions'):
                                for r in material_data['receptions']:
                                    if r.notes and r.notes.strip() and not r.notes.startswith("Arrivée matière:"):
                                        derived_description = r.notes.strip()
                                        break
                            if derived_description:
                                existing_batch.description = derived_description[:255]
                        except Exception as desc_pop_err:
                            print(f"Warning: could not populate existing batch description: {desc_pop_err}")
                    
                    print(f"DEBUG: Found existing batch {existing_batch.batch_code}")
                    print(f"DEBUG: Adding {data['quantity_produced']} to existing quantity {old_quantity}")
                    print(f"DEBUG: New total quantity: {existing_batch.quantity}")
                    
                    QMessageBox.information(
                        self, 
                        "Quantité ajoutée", 
                        f"Quantité ajoutée au lot existant!\n"
                        f"Lot: {existing_batch.batch_code}\n"
                        f"Ancienne quantité: {old_quantity}\n"
                        f"Nouvelle quantité: {existing_batch.quantity}\n"
                        f"Quantité ajoutée: {data['quantity_produced']}"
                    )
                    
                    production_batch = existing_batch
                else:
                    # Create new production batch
                    # Derive description prior to creation
                    derived_description = None
                    try:
                        from models.orders import ClientOrder, Quotation, QuotationLineItem
                        line_client_id = line_item.client_id
                        related_orders = session.query(ClientOrder).filter(
                            ClientOrder.client_id == line_client_id,
                            ClientOrder.quotation_id.isnot(None)
                        ).all()
                        for co in related_orders:
                            if co.quotation and co.quotation.line_items:
                                for ql in co.quotation.line_items:
                                    if ql.description and ql.description.strip():
                                        derived_description = ql.description.strip()
                                        break
                                if derived_description:
                                    break
                            if (not derived_description) and co.quotation and co.quotation.notes and co.quotation.notes.strip():
                                derived_description = co.quotation.notes.strip()
                        # Fallback: notes from receptions used (first meaningful)
                        if (not derived_description) and material_data.get('receptions'):
                            for r in material_data['receptions']:
                                if r.notes and r.notes.strip() and not r.notes.startswith("Arrivée matière:"):
                                    derived_description = r.notes.strip()
                                    break
                    except Exception as pre_desc_err:
                        print(f"Warning: could not derive production batch description: {pre_desc_err}")

                    production_batch = ProductionBatch(
                        client_order_id=client_order_id,
                        batch_code=data['batch_code'],
                        quantity=data['quantity_produced'],
                        production_date=production_date,
                        description=(derived_description[:255] if derived_description else None)
                    )
                    
                    session.add(production_batch)
                    
                    print(f"DEBUG: Created new production batch {data['batch_code']}")
                    print(f"DEBUG: Initial quantity: {data['quantity_produced']}")
                    
                    QMessageBox.information(
                        self, 
                        "Lot créé", 
                        f"Nouveau lot de production créé!\n"
                        f"Code de lot: {data['batch_code']}\n"
                        f"Quantité: {data['quantity_produced']}"
                    )
                
                # Update raw material quantities
                quantity_remaining = data['quantity_used']
                receptions_list = material_data['receptions']
                
                print(f"DEBUG: Starting stock deduction for {quantity_remaining} units")
                print(f"DEBUG: Available receptions: {len(receptions_list)}")
                
                # Re-query reception objects in current session to avoid detached instance errors
                reception_ids = [r.id for r in receptions_list]
                current_receptions = session.query(Reception).filter(Reception.id.in_(reception_ids)).order_by(Reception.id).all()
                
                print(f"DEBUG: Re-queried {len(current_receptions)} receptions in current session")
                
                deleted_reception_ids = set()
                for i, reception in enumerate(current_receptions):
                    print(f"DEBUG: Reception {i+1}: ID={reception.id}, Quantity={reception.quantity}")
                    if quantity_remaining <= 0:
                        break
                        
                    if reception.quantity <= quantity_remaining:
                        # Use entire reception
                        print(f"DEBUG: Deleting entire reception {reception.id} (quantity: {reception.quantity})")
                        quantity_remaining -= reception.quantity
                        session.delete(reception)
                        deleted_reception_ids.add(reception.id)
                    else:
                        # Use partial reception
                        old_qty = reception.quantity
                        reception.quantity -= quantity_remaining
                        print(f"DEBUG: Reducing reception {reception.id} from {old_qty} to {reception.quantity}")
                        quantity_remaining = 0
                
                print(f"DEBUG: Stock deduction complete, remaining: {quantity_remaining}")
                
                print(f"DEBUG: About to commit transaction...")
                session.commit()
                print(f"DEBUG: Transaction committed successfully")
                
                # Verify the changes were saved by re-querying (skip deleted ones)
                print(f"DEBUG: Verifying changes in database...")
                for reception in current_receptions:
                    if reception.id in deleted_reception_ids:
                        print(f"DEBUG: Reception {reception.id} was deleted; skipping refresh")
                        continue
                    try:
                        refreshed = session.query(Reception).filter(Reception.id == reception.id).first()
                        if refreshed is not None:
                            session.refresh(refreshed)
                            print(f"DEBUG: Reception {refreshed.id} quantity after commit: {refreshed.quantity}")
                        else:
                            print(f"DEBUG: Reception {reception.id} no longer exists in DB")
                    except Exception as refresh_err:
                        print(f"DEBUG: Skipping refresh for reception {reception.id}: {refresh_err}")
                
                # Clear any cached objects to ensure fresh data
                session.expunge_all()
                print(f"DEBUG: Session expunged")
                
                # Refresh both grids
                self.refresh_all()
                
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la création du produit fini: {str(e)}")
            finally:
                session.close()

    def _edit_production(self, row_data: list):
        """Edit a production record (not available for merged items)"""
        import re
        id_field = row_data[0]
        
        # Check if it's a merged format
        if re.match(r'^\d+-\d+ \(\d+\)$', id_field):
            QMessageBox.information(
                self, 
                "Modification non disponible", 
                "La modification n'est pas disponible pour les éléments groupés.\n\n"
                "Cette ligne représente plusieurs lots de production fusionnés. "
                "Pour modifier un lot spécifique, veuillez d'abord désactiver le groupage "
                "ou utiliser une vue détaillée."
            )
            return
        
        # Single item - proceed with edit
        if not id_field.isdigit():
            QMessageBox.warning(self, "Erreur", "ID de production invalide.")
            return
            
        production_id = int(id_field)
        
        session = SessionLocal()
        try:
            production_batch = session.query(ProductionBatch).filter(
                ProductionBatch.id == production_id
            ).first()
            
            if not production_batch:
                QMessageBox.warning(self, "Erreur", "Lot de production non trouvé!")
                return
            
            from ui.dialogs.production_details_dialog import ProductionDetailsDialog
            dialog = ProductionDetailsDialog(production_batch, editable=True, parent=self)
            if dialog.exec():
                # Refresh the grid after successful edit
                self.refresh_all()
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ouverture du dialogue: {str(e)}")
        finally:
            session.close()

    def _delete_production(self, row_data: list):
        """Delete a production record (with special handling for merged items)"""
        import re
        id_field = row_data[0]
        
        # Check if it's a comma-separated format (new grouping system)
        if ',' in id_field:
            ids_str = [id_str.strip() for id_str in id_field.split(',')]
            try:
                batch_ids = [int(id_str) for id_str in ids_str]
            except ValueError:
                QMessageBox.warning(self, "Erreur", "Format d'ID invalide dans les éléments groupés.")
                return
            
            reply = QMessageBox.question(
                self,
                "Supprimer les lots groupés",
                f"Voulez-vous supprimer tous les {len(batch_ids)} lots de production groupés ?\n\n"
                f"IDs concernés : {', '.join(ids_str)}\n"
                f"Client : {row_data[1] if len(row_data) > 1 else 'N/A'}\n"
                f"Dimensions : {row_data[2] if len(row_data) > 2 else 'N/A'}\n"
                f"Quantité totale : {row_data[3] if len(row_data) > 3 else 'N/A'}\n\n"
                f"Cette action est irréversible.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self._delete_multiple_production_ids(batch_ids)
            return
        
        # Check if it's the old merged format
        if re.match(r'^\d+-\d+ \(\d+\)$', id_field):
            # Extract all IDs from old merged format
            range_match = re.match(r'^(\d+)-(\d+) \((\d+)\)$', id_field)
            if range_match:
                start_id = int(range_match.group(1))
                end_id = int(range_match.group(2))
                batch_ids = list(range(start_id, end_id + 1))
                count = int(range_match.group(3))
                
                reply = QMessageBox.question(
                    self,
                    "Supprimer les lots groupés",
                    f"Voulez-vous supprimer tous les {count} lots de production groupés ?\n\n"
                    f"IDs concernés : {', '.join(map(str, batch_ids))}\n"
                    f"Client : {row_data[1] if len(row_data) > 1 else 'N/A'}\n"
                    f"Quantité totale : {row_data[3] if len(row_data) > 3 else 'N/A'}\n\n"
                    f"Cette action est irréversible.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self._delete_multiple_production_ids(batch_ids)
            return
        
        # Single item - proceed with normal delete
        if not id_field.isdigit():
            QMessageBox.warning(self, "Erreur", "ID de production invalide.")
            return
            
        production_id = int(id_field)
        production_ref = row_data[1] if len(row_data) > 1 else f"ID {production_id}"
        
        reply = QMessageBox.question(
            self, 
            'Confirmer la suppression',
            f'Êtes-vous sûr de vouloir supprimer la production "{production_ref}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            session = SessionLocal()
            try:
                production_batch = session.query(ProductionBatch).filter(
                    ProductionBatch.id == production_id
                ).first()
                
                if production_batch:
                    session.delete(production_batch)
                    session.commit()
                    
                    QMessageBox.information(self, "Succès", f"Production '{production_ref}' supprimée avec succès!")
                    self.refresh_all()
                else:
                    QMessageBox.warning(self, "Erreur", "Lot de production non trouvé!")
                    
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression: {str(e)}")
            finally:
                session.close()

    def _delete_multiple_production_ids(self, batch_ids: list[int]):
        """Delete multiple production batches by their IDs"""
        session = SessionLocal()
        try:
            deleted_count = 0
            errors = []
            
            for batch_id in batch_ids:
                try:
                    production_batch = session.query(ProductionBatch).filter(
                        ProductionBatch.id == batch_id
                    ).first()
                    
                    if production_batch:
                        session.delete(production_batch)
                        deleted_count += 1
                    else:
                        errors.append(f"Lot {batch_id} non trouvé")
                        
                except Exception as e:
                    errors.append(f"Lot {batch_id}: {str(e)}")
            
            if deleted_count > 0:
                session.commit()
                message = f"{deleted_count} lot(s) de production supprimé(s) avec succès!"
                if errors:
                    message += f"\n\nErreurs : {'; '.join(errors[:3])}"  # Show first 3 errors
                QMessageBox.information(self, "Suppression terminée", message)
                self.refresh_all()
            else:
                session.rollback()
                QMessageBox.warning(self, "Erreur", f"Aucun lot supprimé. Erreurs : {'; '.join(errors)}")
                
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression multiple: {str(e)}")
        finally:
            session.close()

    def _show_production_details(self, row_data: list):
        """Show detailed information about a production (handles merged items)"""
        import re
        id_field = row_data[0]
        
        # Check if it's a comma-separated format (new grouping system)
        if ',' in id_field:
            ids = [id_str.strip() for id_str in id_field.split(',')]
            QMessageBox.information(
                self, 
                "Éléments groupés", 
                f"Cette ligne représente {len(ids)} lots de production groupés:\n\n"
                f"IDs: {', '.join(ids)}\n"
                f"Client: {row_data[1] if len(row_data) > 1 else 'N/A'}\n"
                f"Dimensions: {row_data[2] if len(row_data) > 2 else 'N/A'}\n"
                f"Quantité totale: {row_data[3] if len(row_data) > 3 else 'N/A'}\n\n"
                "Pour voir les détails d'un lot spécifique, vous pouvez utiliser "
                "le menu de recherche ou filtrer les données."
            )
            return
        
        # Check if it's the old merged format
        if re.match(r'^\d+-\d+ \(\d+\)$', id_field):
            QMessageBox.information(
                self, 
                "Détails non disponibles", 
                "L'affichage des détails n'est pas disponible pour les éléments groupés.\n\n"
                "Cette ligne représente plusieurs lots de production fusionnés. "
                "Pour voir les détails d'un lot spécifique, veuillez d'abord désactiver "
                "le groupage ou utiliser une vue détaillée."
            )
            return
        
        if not id_field.isdigit():
            QMessageBox.warning(self, "Erreur", "ID de production invalide.")
            return
            
        production_id = int(id_field)
        
        session = SessionLocal()
        try:
            production_batch = session.query(ProductionBatch).filter(
                ProductionBatch.id == production_id
            ).first()
            
            if not production_batch:
                QMessageBox.warning(self, "Erreur", "Lot de production non trouvé!")
                return
            
            from ui.dialogs.production_details_dialog import ProductionDetailsDialog
            dialog = ProductionDetailsDialog(production_batch, editable=False, parent=self)
            dialog.exec()
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ouverture du dialogue: {str(e)}")
        finally:
            session.close()

    def _load_stock_data(self):
        """Refresh the stock data display"""
        try:
            # Use the existing refresh method to reload all data including stock
            self.refresh_all()
        except Exception as e:
            print(f"Error refreshing stock data: {e}")

    def _print_finished_product_fiche(self, row_data: list):
        """Handle printing finished product fiche with pallet options (supports merged items)"""
        try:
            # Extract production batch ID(s) from row data
            if not row_data or len(row_data) == 0:
                QMessageBox.warning(self, "Erreur", "Aucune donnée de production sélectionnée.")
                return
            
            # Parse ID field - could be single ID, comma-separated IDs, or merged format like "1-3 (2)"
            import re
            id_field = row_data[0]
            batch_ids = []
            
            # Check for comma-separated IDs like "8,9,10,11,12"
            if ',' in id_field and all(part.strip().isdigit() for part in id_field.split(',')):
                batch_ids = [int(part.strip()) for part in id_field.split(',')]
            # Check if it's a merged format like "1-3 (2)" or just a single ID
            elif re.match(r'^\d+-\d+ \(\d+\)$', id_field):
                # Extract range from merged format
                range_match = re.match(r'^(\d+)-(\d+) \((\d+)\)$', id_field)
                if range_match:
                    start_id = int(range_match.group(1))
                    end_id = int(range_match.group(2))
                    batch_ids = list(range(start_id, end_id + 1))
                else:
                    QMessageBox.warning(self, "Erreur", "Format d'ID invalide.")
                    return
            elif id_field.isdigit():
                # Single ID
                batch_ids = [int(id_field)]
            else:
                QMessageBox.warning(self, "Erreur", "ID de lot de production invalide.")
                return
            
            # Get other info from row data
            client_name = row_data[1] if len(row_data) > 1 else ""
            dimensions = row_data[2] if len(row_data) > 2 else ""
            total_quantity = int(row_data[3]) if len(row_data) > 3 and row_data[3] else 0
            
            if total_quantity <= 0:
                QMessageBox.warning(self, "Erreur", "Quantité invalide.")
                return
            
            # Show pallet delivery dialog
            from ui.dialogs.pallet_delivery_dialog import PalletDeliveryDialog
            delivery_dialog = PalletDeliveryDialog(total_quantity, self)
            
            if delivery_dialog.exec() == QDialog.DialogCode.Accepted:
                delivery_options = delivery_dialog.get_delivery_options()
                pallets = delivery_dialog.calculate_pallets()
                
                # Generate PDFs based on pallet distribution
                from services.pdf_export_service import export_finished_product_fiche
                
                generated_files = []
                copy_number = 1
                total_copies = sum(copies for _, copies in pallets)
                
                for quantity_per_pallet, num_copies in pallets:
                    for copy in range(num_copies):
                        try:
                            # For merged items, use the first batch ID as representative
                            representative_batch_id = batch_ids[0]
                            pdf_path = export_finished_product_fiche(
                                representative_batch_id, 
                                quantity_per_pallet, 
                                copy_number, 
                                total_copies,
                                dimensions  # Pass dimensions from grid
                            )
                            if pdf_path:
                                generated_files.append(pdf_path)
                            copy_number += 1
                        except Exception as e:
                            print(f"Error generating PDF for copy {copy_number}: {e}")
                            continue
                
                if generated_files:
                    # Show success message with file count
                    file_count = len(generated_files)
                    message = f"{file_count} fiche(s) de produit fini générée(s) avec succès.\n\n"
                    message += "Fichiers générés:\n"
                    for file_path in generated_files:
                        message += f"- {file_path.name}\n"
                    
                    QMessageBox.information(self, "Succès", message)
                    
                    # Optionally open the generated reports folder
                    import subprocess
                    import platform
                    
                    reports_dir = generated_files[0].parent
                    if platform.system() == "Windows":
                        subprocess.run(f'explorer "{reports_dir}"', shell=True)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", str(reports_dir)])
                    else:  # Linux
                        subprocess.run(["xdg-open", str(reports_dir)])
                        
                else:
                    QMessageBox.warning(self, "Erreur", "Aucun fichier PDF n'a pu être généré.")
            
        except Exception as e:
            print(f"Error printing finished product fiche: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération de la fiche: {str(e)}")

    def _print_raw_material_label(self, row_data: list):
        """Handle printing raw material label with optional remark"""
        try:
            # Extract reception data from row
            # Column structure: ["ID", "Quantité", "Fournisseur", "Bon Commande", "Client", "Date Réception"]
            if not row_data or len(row_data) == 0:
                QMessageBox.warning(self, "Erreur", "Aucune donnée de réception sélectionnée.")
                return
            
            # Parse reception IDs (can be comma-separated for grouped receptions)
            ids_str = row_data[0]
            try:
                reception_ids = [int(id_str.strip()) for id_str in ids_str.split(',')]
            except (ValueError, AttributeError):
                QMessageBox.warning(self, "Erreur", "ID de réception invalide.")
                return
            
            quantity = row_data[1] if len(row_data) > 1 else "0"
            supplier = row_data[2] if len(row_data) > 2 else "N/A"
            bon_commande = row_data[3] if len(row_data) > 3 else "N/A"
            client = row_data[4] if len(row_data) > 4 else "N/A"
            date_reception = row_data[5] if len(row_data) > 5 else "N/A"
            
            # Prepare material info for the dialog
            material_info = {
                'client': client,
                'quantity': quantity,
                'supplier': supplier,
                'bon_commande': bon_commande,
                'date_reception': date_reception,
                'plaque_dimensions': 'N/A'  # Will be filled from database
            }
            
            # Show dialog to collect optional remark
            from ui.dialogs.raw_material_label_dialog import RawMaterialLabelDialog
            label_dialog = RawMaterialLabelDialog(material_info, self)
            
            if label_dialog.exec() == QDialog.DialogCode.Accepted:
                remark = label_dialog.get_remark()
                
                # Generate PDF label
                from services.pdf_export_service import export_raw_material_label
                
                try:
                    pdf_path = export_raw_material_label(reception_ids, remark)
                    
                    if pdf_path:
                        QMessageBox.information(
                            self, "Succès", 
                            f"Étiquette matière première générée avec succès!\n\n"
                            f"Fichier sauvegardé: {pdf_path.name}"
                        )
                        
                        # Optionally open the reports folder
                        import subprocess
                        import platform
                        
                        reports_dir = pdf_path.parent
                        if platform.system() == "Linux":
                            subprocess.run(["xdg-open", str(reports_dir)])
                        elif platform.system() == "Windows":
                            subprocess.run(f'explorer "{reports_dir}"', shell=True)
                        elif platform.system() == "Darwin":  # macOS
                            subprocess.run(["open", str(reports_dir)])
                    else:
                        QMessageBox.warning(self, "Erreur", "Impossible de générer l'étiquette PDF.")
                        
                except Exception as e:
                    print(f"Error generating raw material label: {e}")
                    QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération de l'étiquette: {str(e)}")
            
        except Exception as e:
            print(f"Error printing raw material label: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'impression de l'étiquette: {str(e)}")

    def _print_delivery_note(self, row_data: list):
        """Print delivery note for finished products with partial/all quantity selection.
        - Presents a dialog to choose delivered quantity (all or specific)
        - Generates the delivery note PDF
        - Records a Delivery row with status and a notes token to trace which batches/dimensions were delivered
        """
        from PyQt6.QtWidgets import QDialog, QMessageBox
        from config.database import SessionLocal
        from models.production import ProductionBatch
        from models.orders import ClientOrder, Quotation, Delivery, DeliveryStatus
        from models.clients import Client
        from services.document_service import DocumentService
        from utils.reference_generator import generate_delivery_reference
        from datetime import date
        from sqlalchemy.orm import joinedload
        import subprocess
        import platform
        import re
        
        # Extract basic information from row data
        if not row_data or len(row_data) == 0:
            QMessageBox.warning(self, "Erreur", "Aucune donnée de production sélectionnée.")
            return
        
        try:
            # Parse ID field - could be single ID, comma-separated IDs, or merged format like "1-3 (2)"
            id_field = row_data[0]
            batch_ids = []
            
            # Check for comma-separated IDs like "8,9,10,11,12"
            if ',' in id_field and all(part.strip().isdigit() for part in id_field.split(',')):
                batch_ids = [int(part.strip()) for part in id_field.split(',')]
            # Check if it's a merged format like "1-3 (2)" or just a single ID
            elif re.match(r'^\d+-\d+ \(\d+\)$', id_field):
                # Extract range from merged format
                range_match = re.match(r'^(\d+)-(\d+) \((\d+)\)$', id_field)
                if range_match:
                    start_id = int(range_match.group(1))
                    end_id = int(range_match.group(2))
                    batch_ids = list(range(start_id, end_id + 1))
                else:
                    QMessageBox.warning(self, "Erreur", "Format d'ID invalide.")
                    return
            elif id_field.isdigit():
                # Single ID
                batch_ids = [int(id_field)]
            else:
                QMessageBox.warning(self, "Erreur", "ID de lot de production invalide.")
                return
                
            session = SessionLocal()
            try:
                # Get all production batches for this merged item
                batches = session.query(ProductionBatch).filter(
                    ProductionBatch.id.in_(batch_ids)
                ).all()
                
                if not batches:
                    QMessageBox.warning(self, "Erreur", f"Lots de production {id_field} introuvables.")
                    return
                
                # Since items are merged, they should all have the same client and dimensions
                # Use the first batch to get client information
                first_batch = batches[0]
                
                # Get client order with quotation and client data eagerly loaded
                client_order = session.query(ClientOrder).options(
                    joinedload(ClientOrder.quotation).joinedload(Quotation.line_items),
                    joinedload(ClientOrder.supplier_order),
                    joinedload(ClientOrder.client)
                ).filter(ClientOrder.id == first_batch.client_order_id).first()
                
                if not client_order:
                    QMessageBox.warning(self, "Erreur", "Commande client introuvable pour ce lot.")
                    return
                
                # Calculate total quantity from all batches
                total_quantity = sum(getattr(batch, 'quantity', 0) or 0 for batch in batches)
                
                # Get client details from the first batch's client order
                client_details = None
                if client_order.supplier_order and client_order.supplier_order.line_items:
                    line_item = client_order.supplier_order.line_items[0]
                    if line_item.client:
                        client_details = {
                            'name': line_item.client.name,
                            'address': getattr(line_item.client, 'address', ''),
                            'phone': getattr(line_item.client, 'phone', ''),
                            'email': getattr(line_item.client, 'email', '')
                        }
                
                # Fallback: Use direct client relationship if supplier order client not available
                if not client_details and client_order.client:
                    client_details = {
                        'name': client_order.client.name,
                        'address': getattr(client_order.client, 'address', ''),
                        'phone': getattr(client_order.client, 'phone', ''),
                        'email': getattr(client_order.client, 'email', '')
                    }
                
                # Get the designation from quotation line items if available (PRIORITY)
                designation_from_quotation = ""
                
                if client_order and client_order.quotation and client_order.quotation.line_items:
                    # Use the first quotation line item description as the designation
                    quotation_line_item = client_order.quotation.line_items[0]
                    if quotation_line_item.description:
                        designation_from_quotation = quotation_line_item.description
                        print(f"DEBUG Delivery Note: Found quotation description: '{designation_from_quotation}'")
                
                # Fallback: Look for most recent quotation for the same client if no direct quotation link
                if not designation_from_quotation and client_order and client_order.client:
                    from models.orders import Quotation, QuotationLineItem
                    from sqlalchemy import desc
                    most_recent_quotation = session.query(Quotation).filter(
                        Quotation.client_id == client_order.client.id
                    ).order_by(desc(Quotation.issue_date)).first()
                    
                    if most_recent_quotation and most_recent_quotation.line_items:
                        quotation_line_item = most_recent_quotation.line_items[0]
                        if quotation_line_item.description:
                            designation_from_quotation = quotation_line_item.description
                            print(f"DEBUG Delivery Note: Found recent quotation description: '{designation_from_quotation}'")
                
                # Final fallback to auto-generated description if no quotation found
                if not designation_from_quotation:
                    designation_from_quotation = f"Cartons {row_data[2]}" if len(row_data) > 2 else "Cartons"
                    print(f"DEBUG Delivery Note: Using fallback description: '{designation_from_quotation}'")
                
                # Ask user which quantity to deliver
                from ui.dialogs.delivery_quantity_dialog import DeliveryQuantityDialog
                qty_dialog = DeliveryQuantityDialog(total_quantity, self)
                if qty_dialog.exec() != QDialog.DialogCode.Accepted:
                    return
                delivered_qty = qty_dialog.chosen_quantity()
                if delivered_qty <= 0:
                    QMessageBox.warning(self, "Quantité invalide", "Veuillez saisir une quantité positive à livrer.")
                    return

                # Create delivery item with chosen quantity
                delivery_items = [{
                    'description': designation_from_quotation,
                    'quantity': delivered_qty,
                    'unit_price': 0.0,
                    'batch_ids': batch_ids,
                    'client_order_id': first_batch.client_order_id
                }]
                
                # Generate delivery reference
                delivery_ref = generate_delivery_reference()
                
                # Get today's date
                delivery_date = date.today()
                
                # Generate PDF
                doc_service = DocumentService()
                pdf_path = doc_service.build_delivery_note(
                    reference=delivery_ref,
                    client_name=client_details['name'] if client_details else "Client inconnu",
                    delivery_date=delivery_date,
                    lines=[{
                        'designation': item['description'],
                        'dimensions': row_data[2] if len(row_data) > 2 else "N/A",
                        'quantity': str(item['quantity'])
                    } for item in delivery_items],
                    client_details=f"{client_details['name']}\n{client_details.get('address', '')}" if client_details else ""
                )
                
                if pdf_path:
                    # Record a Delivery row for traceability
                    try:
                        dims = row_data[2] if len(row_data) > 2 else "N/A"
                        # Notes include tokens to later compute remaining: BATCH_IDS and DIMS
                        notes_token = f"BATCH_IDS={','.join(map(str, batch_ids))};DIMS={dims}"
                        delivery_status = DeliveryStatus.COMPLETE if delivered_qty >= total_quantity else DeliveryStatus.PARTIAL

                        delivery_row = Delivery(
                            client_order_id=first_batch.client_order_id,
                            delivery_date=delivery_date,
                            status=delivery_status,
                            quantity=delivered_qty,
                            notes=notes_token
                        )
                        session.add(delivery_row)
                        # Adjust stock of finished products: reduce batch quantities or archive
                        try:
                            remaining_to_deliver = int(delivered_qty)
                            if remaining_to_deliver >= total_quantity:
                                # Fully delivered: archive all involved batches so they disappear from stock view
                                for b in batches:
                                    if not getattr(b, 'batch_code', '').startswith('[ARCHIVED]'):
                                        b.batch_code = f"[ARCHIVED] {b.batch_code}"
                            else:
                                # Partial delivery: decrement quantities across batches in order
                                for b in batches:
                                    if remaining_to_deliver <= 0:
                                        break
                                    q = int(getattr(b, 'quantity', 0) or 0)
                                    if q <= 0:
                                        continue
                                    take = min(q, remaining_to_deliver)
                                    b.quantity = max(0, q - take)
                                    remaining_to_deliver -= take
                                    # If a batch hits zero, archive it
                                    if b.quantity == 0 and not getattr(b, 'batch_code', '').startswith('[ARCHIVED]'):
                                        b.batch_code = f"[ARCHIVED] {b.batch_code}"
                        except Exception as stock_err:
                            # Don't block delivery recording if stock update fails
                            print(f"Warning: Failed to update production stock on delivery: {stock_err}")

                        session.commit()
                    except Exception as rec_err:
                        session.rollback()
                        print(f"Warning: Failed to record Delivery row: {rec_err}")

                    # Try to open the PDF
                    try:
                        if platform.system() == "Darwin":  # macOS
                            subprocess.run(["open", pdf_path])
                        elif platform.system() == "Windows":
                            subprocess.run(["start", pdf_path], shell=True)
                        else:  # Linux
                            subprocess.run(["xdg-open", pdf_path])
                        
                        QMessageBox.information(self, "Succès", f"Bon de livraison généré: {delivery_ref}")
                    except Exception as e:
                        QMessageBox.information(self, "Succès", f"Bon de livraison généré: {delivery_ref}\nFichier: {pdf_path}")
                else:
                    QMessageBox.warning(self, "Erreur", "Impossible de générer le bon de livraison.")
                    
            finally:
                session.close()
                # Refresh UI to reflect updated stock quantities/archived batches
                try:
                    self.refresh_all()
                except Exception:
                    pass
                
        except Exception as e:
            print(f"Error generating delivery note: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération du bon de livraison: {str(e)}")

    def _print_invoice(self, row_data: list):
        """Print invoice for finished product (placeholder)"""
        from PyQt6.QtWidgets import QMessageBox
        
        # Extract basic information from row data
        if not row_data or len(row_data) == 0:
            QMessageBox.warning(self, "Erreur", "Aucune donnée de production sélectionnée.")
            return
        
        batch_id = row_data[0] if row_data[0] else "N/A"
        client_name = row_data[1] if len(row_data) > 1 else "N/A"
        quantity = row_data[3] if len(row_data) > 3 else "N/A"
        
        # TODO: Implement invoice generation with unified reference
        QMessageBox.information(
            self, 
            "Facture", 
            f"Fonctionnalité en cours de développement.\n\n"
            f"Lot: {batch_id}\n"
            f"Client: {client_name}\n"
            f"Quantité: {quantity}\n\n"
            f"La facture sera générée avec référence unifiée prochainement."
        )

    def _delete_multiple_productions(self):
        """Delete multiple selected productions"""
        from PyQt6.QtWidgets import QMessageBox
        
        if not self.production_grid or not hasattr(self.production_grid, 'get_selected_rows_data'):
            return
            
        selected_rows_data = self.production_grid.get_selected_rows_data()
        if not selected_rows_data:
            QMessageBox.warning(self, "Aucune sélection", "Aucune production sélectionnée.")
            return

        production_count = len(selected_rows_data)
        batch_ids = [row[0] for row in selected_rows_data if len(row) > 0]
        
        # TODO: Implement multiple production deletion
        QMessageBox.information(
            self,
            "Suppression multiple",
            f"Fonctionnalité en cours de développement.\n\n"
            f"{production_count} productions sélectionnées:\n"
            f"IDs: {', '.join(batch_ids)}\n\n"
            f"La suppression multiple sera implémentée prochainement."
        )

    def _print_delivery_note_for_selection(self):
        """Print delivery notes for selected finished products"""
        from PyQt6.QtWidgets import QMessageBox
        from config.database import SessionLocal
        from models.production import ProductionBatch
        from models.orders import ClientOrder, Quotation
        from models.clients import Client
        from services.document_service import DocumentService
        from utils.reference_generator import generate_delivery_reference
        from datetime import date
        from sqlalchemy.orm import joinedload
        from collections import defaultdict
        import subprocess
        import platform
        
        if not self.production_grid or not hasattr(self.production_grid, 'get_selected_rows_data'):
            # Fall back to single item if no multi-selection support
            return
            
        selected_rows_data = self.production_grid.get_selected_rows_data()
        if not selected_rows_data:
            QMessageBox.warning(self, "Aucune sélection", "Aucune production sélectionnée.")
            return

        if len(selected_rows_data) == 1:
            # Single selection - use existing method
            self._print_delivery_note(selected_rows_data[0])
        else:
            # Multiple selection - Group by client and dimensions, then generate merged delivery notes
            try:
                session = SessionLocal()
                try:
                    # Group items by client to create separate delivery notes per client
                    client_groups = defaultdict(list)
                    
                    for row_data in selected_rows_data:
                        if not row_data or len(row_data) == 0:
                            continue
                            
                        batch_id = int(row_data[0]) if row_data[0] and row_data[0].isdigit() else None
                        if not batch_id:
                            continue
                            
                        # Get production batch with related data
                        batch = session.query(ProductionBatch).filter(
                            ProductionBatch.id == batch_id
                        ).first()
                        
                        if not batch:
                            continue
                        
                        # Get client order with quotation and client data eagerly loaded
                        client_order = session.query(ClientOrder).options(
                            joinedload(ClientOrder.quotation).joinedload(Quotation.line_items),
                            joinedload(ClientOrder.client)
                        ).filter(
                            ClientOrder.id == batch.client_order_id
                        ).first()
                        
                        if not client_order or not client_order.client:
                            continue
                        
                        client = client_order.client
                        
                        # Get dimensions and designation from quotation if available
                        box_dimensions = "N/A"
                        quotation_designation = ""
                        if client_order.quotation and client_order.quotation.line_items:
                            line_item = client_order.quotation.line_items[0]  # First item
                            if line_item.length_mm and line_item.width_mm and line_item.height_mm:
                                box_dimensions = f"{line_item.length_mm}×{line_item.width_mm}×{line_item.height_mm}"
                            # Get designation from quotation description
                            if line_item.description:
                                quotation_designation = line_item.description
                        elif client_order.client:
                            # Fallback: Look for most recent quotation for the same client
                            most_recent_quotation = session.query(Quotation).filter(
                                Quotation.client_id == client_order.client.id
                            ).order_by(Quotation.issue_date.desc()).first()
                            
                            if most_recent_quotation and most_recent_quotation.line_items:
                                line_item = most_recent_quotation.line_items[0]
                                if line_item.description:
                                    quotation_designation = line_item.description
                                if line_item.length_mm and line_item.width_mm and line_item.height_mm:
                                    box_dimensions = f"{line_item.length_mm}×{line_item.width_mm}×{line_item.height_mm}"
                        
                        # Use quotation description as designation, fallback to generic description
                        designation = quotation_designation if quotation_designation else f"Caisse {client_order.reference}"
                        
                        # Group by client ID
                        client_groups[client.id].append({
                            'client': client,
                            'client_order': client_order,
                            'batch': batch,
                            'dimensions': box_dimensions,
                            'designation': designation
                        })
                    
                    # Generate delivery note for each client group
                    generated_count = 0
                    errors = []
                    
                    for client_id, items in client_groups.items():
                        try:
                            client = items[0]['client']
                            
                            # Merge items with same dimensions
                            merged_items = defaultdict(int)  # dimensions -> total_quantity
                            designations = defaultdict(set)  # dimensions -> set of designations
                            
                            for item in items:
                                dimensions = item['dimensions']
                                quantity = item['batch'].quantity
                                designation = item['designation']
                                
                                merged_items[dimensions] += quantity
                                designations[dimensions].add(designation)
                            
                            # Generate unified reference
                            delivery_reference = generate_delivery_reference()
                            
                            # Prepare client details block
                            client_details = client.name
                            if client.contact_name:
                                client_details += f"\nContact: {client.contact_name}"
                            if client.address:
                                client_details += f"\n{client.address}"
                            if client.city:
                                client_details += f"\n{client.city}"
                            if client.country:
                                client_details += f"\n{client.country}"
                            if client.phone:
                                client_details += f"\nTél: {client.phone}"
                            if client.email:
                                client_details += f"\nEmail: {client.email}"
                            
                            # Prepare merged lines
                            lines = []
                            for dimensions, total_quantity in merged_items.items():
                                # Use the first designation if multiple, or combine them
                                designation_set = designations[dimensions]
                                if len(designation_set) == 1:
                                    designation = list(designation_set)[0]
                                else:
                                    # Multiple orders with same dimensions - create generic designation
                                    designation = f"Caisses {dimensions}"
                                
                                lines.append({
                                    'designation': designation,
                                    'dimensions': dimensions,
                                    'quantity': str(total_quantity)
                                })
                            
                            # Generate PDF
                            doc_service = DocumentService()
                            pdf_path = doc_service.build_delivery_note(
                                reference=delivery_reference,
                                client_name=client.name,
                                delivery_date=date.today(),
                                lines=lines,
                                client_details=client_details
                            )
                            
                            # Open the PDF (only for the first one to avoid opening too many)
                            if generated_count == 0:
                                try:
                                    if platform.system() == 'Darwin':  # macOS
                                        subprocess.call(['open', str(pdf_path)])
                                    elif platform.system() == 'Windows':  # Windows
                                        subprocess.call(['start', str(pdf_path)], shell=True)
                                    else:  # Linux
                                        subprocess.call(['xdg-open', str(pdf_path)])
                                except Exception:
                                    pass  # Ignore PDF opening errors
                            
                            generated_count += 1
                            
                        except Exception as e:
                            # Use client name if available, otherwise use client_id
                            client_name = items[0]['client'].name if items and 'client' in items[0] and items[0]['client'] else f"Client ID {client_id}"
                            errors.append(f"Client {client_name}: {str(e)}")
                    
                    # Show summary
                    if errors:
                        error_text = "\n".join(errors[:5])  # Show first 5 errors
                        if len(errors) > 5:
                            error_text += f"\n... et {len(errors) - 5} autres erreurs"
                        
                        QMessageBox.warning(
                            self,
                            "Génération partiellement réussie",
                            f"{generated_count} bon(s) de livraison généré(s) avec succès.\n\n"
                            f"Erreurs rencontrées:\n{error_text}"
                        )
                    else:
                        total_items = len(selected_rows_data)
                        merged_info = f"({total_items} éléments fusionnés par client et dimensions)"
                        
                        QMessageBox.information(
                            self,
                            "Génération réussie",
                            f"{generated_count} bon(s) de livraison généré(s) avec succès!\n"
                            f"{merged_info}"
                        )
                        
                finally:
                    session.close()
                    
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    f"Erreur lors de la génération multiple: {str(e)}"
                )

    def _create_invoice_for_selection(self, row_data: list):
        """Create invoice for selected finished product(s)"""
        # Check if production grid is available
        if not self.production_grid or not hasattr(self.production_grid, 'get_selected_rows_data'):
            QMessageBox.warning(self, 'Erreur', 'Grille de production non disponible')
            return
        
        # Get selected rows data - if no selection, use the clicked row
        selected_rows_data = self.production_grid.get_selected_rows_data()
        if not selected_rows_data and row_data:
            # If no rows are selected but we have the clicked row, use it
            selected_rows_data = [row_data]
        elif not selected_rows_data:
            QMessageBox.warning(self, 'Erreur', 'Aucun produit fini sélectionné')
            return
        
        try:
            # Extract production IDs
            production_ids = []
            for row in selected_rows_data:
                if len(row) < 1:
                    continue
                raw = (row[0] or "").strip()
                if not raw:
                    continue
                # Support formats:
                #  - "123"
                #  - "12,13,18"
                #  - "10-15 (6)" (fallback: assume consecutive IDs)
                try:
                    if "," in raw:
                        for part in raw.split(","):
                            part = part.strip()
                            if part.isdigit():
                                production_ids.append(int(part))
                    elif "-" in raw:
                        # Extract range like "10-15" optionally followed by count
                        range_part = raw.split(" ")[0]
                        a_str, b_str = range_part.split("-", 1)
                        a = int(a_str)
                        b = int(b_str)
                        if a <= b:
                            production_ids.extend(list(range(a, b + 1)))
                    else:
                        production_ids.append(int(raw))
                except (ValueError, TypeError):
                    # Skip unparsable entries
                    continue
            
            if not production_ids:
                QMessageBox.warning(self, 'Erreur', 'Aucun produit fini valide sélectionné')
                return
            
            # Import required services
            from services.invoice_service import InvoiceService
            from services.pdf_form_filler import PDFFormFiller, PDFFillError
            
            # Ask whether to include TVA
            from PyQt6.QtWidgets import QMessageBox as _QMessageBox
            tva_dialog = _QMessageBox(self)
            tva_dialog.setWindowTitle('TVA')
            tva_dialog.setText('Inclure la TVA (19%) dans la facture ?')
            tva_dialog.setIcon(_QMessageBox.Icon.Question)
            btn_with_tva = tva_dialog.addButton('Avec TVA', _QMessageBox.ButtonRole.YesRole)
            btn_without_tva = tva_dialog.addButton('Sans TVA', _QMessageBox.ButtonRole.NoRole)
            tva_dialog.addButton(_QMessageBox.StandardButton.Cancel)
            tva_dialog.exec()

            clicked = tva_dialog.clickedButton()
            if clicked == tva_dialog.button(_QMessageBox.StandardButton.Cancel):
                return
            include_tva = (clicked == btn_with_tva)

            # Prepare invoice data with TVA choice
            with InvoiceService() as invoice_service:
                invoice_data = invoice_service.prepare_invoice_data(production_ids, include_tva=include_tva)
            
            # Generate PDF invoice
            pdf_filler = PDFFormFiller()
            try:
                output_path = pdf_filler.fill_invoice_template(invoice_data)
                
                # Try to open the PDF with default system viewer
                if output_path.exists():
                    import subprocess
                    import os
                    
                    if os.name == 'nt':  # Windows
                        os.startfile(str(output_path))
                    elif os.name == 'posix':  # Linux/Unix
                        subprocess.run(['xdg-open', str(output_path)], check=False)
                    else:  # macOS
                        subprocess.run(['open', str(output_path)], check=False)
                    
                    QMessageBox.information(
                        self, 
                        'Succès', 
                        f'Facture générée avec succès:\n{output_path.name}\n\n'
                        f'Numéro: {invoice_data.get("invoice_number", "N/A")}\n'
                        f'Client: {invoice_data.get("client_name", "N/A")}\n'
                        f'Total TTC NET: {invoice_data.get("total_ttc_net", 0):.2f} DA\n\n'
                        f'Emplacement: {output_path.parent}'
                    )
                    
                    # Add activity to dashboard
                    self.dashboard.add_activity("F", f"Facture créée: {invoice_data.get('invoice_number', 'N/A')}", "#28A745")
                else:
                    QMessageBox.warning(self, 'Erreur', 'Le fichier PDF n\'a pas pu être créé')
                    
            except PDFFillError as e:
                QMessageBox.critical(self, 'Erreur PDF', f'Erreur lors de la génération de la facture:\n{str(e)}')
            except Exception as e:
                QMessageBox.critical(self, 'Erreur', f'Erreur inattendue lors de la génération:\n{str(e)}')
                
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de la création de la facture:\n{str(e)}')
            import logging
            logging.error(f"Error creating invoice: {e}")

    def _print_invoice_for_selection(self):
        """Print invoices for selected finished products"""
        from PyQt6.QtWidgets import QMessageBox
        
        if not self.production_grid or not hasattr(self.production_grid, 'get_selected_rows_data'):
            # Fall back to single item if no multi-selection support
            return
            
        selected_rows_data = self.production_grid.get_selected_rows_data()
        if not selected_rows_data:
            QMessageBox.warning(self, "Aucune sélection", "Aucune production sélectionnée.")
            return

        if len(selected_rows_data) == 1:
            # Single selection - use existing method
            self._print_invoice(selected_rows_data[0])
        else:
            # Multiple selection
            production_count = len(selected_rows_data)
            batch_ids = [row[0] for row in selected_rows_data if len(row) > 0]
            clients = [row[1] for row in selected_rows_data if len(row) > 1]
            total_quantity = sum(int(row[3]) if len(row) > 3 and row[3].isdigit() else 0 for row in selected_rows_data)
            
            # TODO: Implement multiple invoice generation
            QMessageBox.information(
                self,
                "Factures multiples",
                f"Fonctionnalité en cours de développement.\n\n"
                f"{production_count} factures à générer:\n"
                f"Lots: {', '.join(batch_ids)}\n"
                f"Clients: {', '.join(set(clients))}\n"
                f"Quantité totale: {total_quantity}\n\n"
                f"La génération multiple sera implémentée prochainement."
            )


__all__ = ['MainWindow']