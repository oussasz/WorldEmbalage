from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QPushButton, QMenu
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QAction, QColor
from typing import Sequence, Callable, Optional


class DataGrid(QWidget):
    # Signal emitted when a row is double-clicked
    rowDoubleClicked = pyqtSignal(int)
    # Signal emitted when a context menu action is triggered (action_name, row_index, row_data)
    contextMenuActionTriggered = pyqtSignal(str, int, list)
    # Signal emitted before context menu is shown (row_index, row_data, menu)
    contextMenuAboutToShow = pyqtSignal(int, list, QMenu)
    
    def __init__(self, headers: Sequence[str], parent=None):
        super().__init__(parent)
        self.headers = list(headers)
        self.table = QTableWidget(0, len(self.headers))
        self._setup_table()
        self._build_ui()
        self._all_rows: list[list[str]] = []
        self._context_actions: list[tuple[str, str, str]] = []  # (action_name, label, icon)

    def _setup_table(self):
        self.table.setHorizontalHeaderLabels(self.headers)
        
        # Configure headers with intelligent sizing
        h_header = self.table.horizontalHeader()
        if h_header:
            # Set different resize modes based on column content
            for i, header in enumerate(self.headers):
                if header.upper() in ['ID', 'QTÉ', 'QUANTITÉ']:
                    # Fixed width for small numeric columns
                    h_header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
                elif header.upper() in ['STATUT', 'STATUS', 'ÉTAT']:
                    # Medium fixed width for status columns
                    h_header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                    h_header.resizeSection(i, 120)
                else:
                    # Stretch for text columns (names, descriptions, etc.)
                    h_header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            
            # Apply header styling
            header_font = QFont("Segoe UI", 10, QFont.Weight.DemiBold)
            h_header.setFont(header_font)
            h_header.setMinimumSectionSize(60)  # Minimum column width
            h_header.setDefaultSectionSize(100)  # Default column width
            h_header.setStretchLastSection(True)  # Last column takes remaining space
        
        v_header = self.table.verticalHeader()
        if v_header:
            v_header.setVisible(False)
            v_header.setDefaultSectionSize(38)  # Slightly taller rows for better readability
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection) # Allow multi-select
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        
        # Improve table appearance
        self.table.setShowGrid(True)
        self.table.setWordWrap(False)
        self.table.setCornerButtonEnabled(False)
        
        # Connect double-click signal
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        # Enable context menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Info header
        info_layout = QHBoxLayout()
        self.info_label = QLabel('Aucune donnée')
        self.info_label.setStyleSheet("color: #6c757d; font-size: 12px; padding: 5px;")
        info_layout.addWidget(self.info_label)
        info_layout.addStretch()
        
        # Quick action buttons
        self.action_layout = QHBoxLayout()
        self.action_layout.addStretch()
        info_layout.addLayout(self.action_layout)
        
        layout.addLayout(info_layout)
        layout.addWidget(self.table)

    def add_action_button(self, text: str, callback):
        """Add an action button to the grid header"""
        btn = QPushButton(text)
        btn.setMaximumHeight(25)
        btn.clicked.connect(callback)
        self.action_layout.insertWidget(self.action_layout.count() - 1, btn)
        return btn

    def add_header_widget(self, widget):
        """Add a custom widget (e.g., QLineEdit) to the grid header next to action buttons."""
        try:
            if hasattr(widget, 'setMaximumHeight'):
                widget.setMaximumHeight(25)
            self.action_layout.insertWidget(self.action_layout.count() - 1, widget)
            return widget
        except Exception:
            # Fallback: append at the end
            self.action_layout.addWidget(widget)
            return widget

    def load_rows(self, rows: Sequence[Sequence[str]]):
        """Public API to load (or reload) full dataset into the grid.
        Garantit un rendu stable même avec le tri activé.
        """
        self._all_rows = [list(map(lambda v: '' if v is None else str(v), r)) for r in rows]
        self._render_rows(self._all_rows)
        self._update_info_label(len(self._all_rows))
        # Adjust column widths after loading data
        QTimer.singleShot(10, self._adjust_column_widths)

    def load_rows_with_colors(self, rows: Sequence[Sequence[str]], row_colors: Optional[Sequence[Optional[str]]] = None):
        """Load rows with optional color coding for each row.
        row_colors: list of color codes (e.g., '#ffeeee', 'lightblue') or None for default color
        """
        self._all_rows = [list(map(lambda v: '' if v is None else str(v), r)) for r in rows]
        self._render_rows_with_colors(self._all_rows, row_colors)
        self._update_info_label(len(self._all_rows))
        # Adjust column widths after loading data
        QTimer.singleShot(10, self._adjust_column_widths)

    def refresh_data(self, rows: Sequence[Sequence[str]]):
        """Refresh table data and adjust column widths."""
        self.load_rows(rows)

    def _render_rows(self, rows: Sequence[Sequence[str]]):
        """Render a list of rows into the table safely.
        On désactive temporairement le tri et les updates pour éviter affichage vide.
        """
        if not self.table:
            return
        sorting_prev = self.table.isSortingEnabled()
        self.table.setSortingEnabled(False)
        self.table.setUpdatesEnabled(False)
        try:
            self.table.clearContents()
            self.table.setRowCount(len(rows))
            for r_index, row in enumerate(rows):
                for c, val in enumerate(row):
                    # Placeholder visible si valeur vide
                    display = val if (isinstance(val, str) and val.strip()) else '—'
                    item = QTableWidgetItem(display)
                    # Conserver valeur brute pour tri (si vide => '')
                    item.setData(Qt.ItemDataRole.UserRole, val)
                    self.table.setItem(r_index, c, item)
        finally:
            self.table.setUpdatesEnabled(True)
            self.table.setSortingEnabled(sorting_prev)
            if sorting_prev:
                # Retrigger tri courant sur première colonne par défaut
                self.table.sortItems(0, Qt.SortOrder.AscendingOrder)
            vp = self.table.viewport()
            if vp:
                vp.update()
        
        # Ajuster la hauteur après rendu
        v_header = self.table.verticalHeader()
        if v_header:
            v_header.setDefaultSectionSize(35)

    def _render_rows_with_colors(self, rows: Sequence[Sequence[str]], row_colors: Optional[Sequence[Optional[str]]] = None):
        """Render a list of rows into the table with optional color coding.
        row_colors: list of color codes for each row, or None for default colors
        """
        if not self.table:
            return
        sorting_prev = self.table.isSortingEnabled()
        self.table.setSortingEnabled(False)
        self.table.setUpdatesEnabled(False)
        try:
            self.table.clearContents()
            self.table.setRowCount(len(rows))
            for r_index, row in enumerate(rows):
                # Get row color if provided
                row_color = None
                if row_colors and r_index < len(row_colors) and row_colors[r_index]:
                    row_color = QColor(row_colors[r_index])
                
                for c, val in enumerate(row):
                    # Placeholder visible si valeur vide
                    display = val if (isinstance(val, str) and val.strip()) else '—'
                    item = QTableWidgetItem(display)
                    # Conserver valeur brute pour tri (si vide => '')
                    item.setData(Qt.ItemDataRole.UserRole, val)
                    
                    # Apply row color if specified
                    if row_color:
                        item.setBackground(row_color)
                    
                    self.table.setItem(r_index, c, item)
        finally:
            self.table.setUpdatesEnabled(True)
            self.table.setSortingEnabled(sorting_prev)
            if sorting_prev:
                # Retrigger tri courant sur première colonne par défaut
                self.table.sortItems(0, Qt.SortOrder.AscendingOrder)
            vp = self.table.viewport()
            if vp:
                vp.update()
        
        # Ajuster la hauteur après rendu
        v_header = self.table.verticalHeader()
        if v_header:
            v_header.setDefaultSectionSize(35)

    def filter(self, text: str):
        if not text:
            self._render_rows(self._all_rows)
            self._update_info_label(len(self._all_rows))
            return
        
        text_lower = text.lower()
        filtered = [row for row in self._all_rows if any(text_lower in str(cell).lower() for cell in row)]
        self._render_rows(filtered)
        self._update_info_label(len(filtered), len(self._all_rows))

    def filter_multi(self, texts: list[str]):
        """Filter rows if ANY of the provided texts matches any cell (OR semantics).
        Empty or whitespace-only texts are ignored. If no valid texts, shows all rows.
        """
        tokens = [t.strip().lower() for t in texts if t and t.strip()]
        if not tokens:
            self._render_rows(self._all_rows)
            self._update_info_label(len(self._all_rows))
            return

        def row_matches(row: list[str]) -> bool:
            r = [str(cell).lower() for cell in row]
            for tok in tokens:
                for cell in r:
                    if tok in cell:
                        return True
            return False

        filtered = [row for row in self._all_rows if row_matches(row)]
        self._render_rows(filtered)
        self._update_info_label(len(filtered), len(self._all_rows))

    def _update_info_label(self, shown_count: int, total_count: int | None = None):
        if total_count is None:
            total_count = shown_count
        
        if shown_count == 0:
            self.info_label.setText('Aucune donnée')
        elif shown_count == total_count:
            self.info_label.setText(f'{shown_count} élément(s)')
        else:
            self.info_label.setText(f'{shown_count} sur {total_count} élément(s)')

    def resizeEvent(self, a0):
        """Handle resize events to maintain optimal column sizing."""
        super().resizeEvent(a0)
        self._adjust_column_widths()
    
    def _adjust_column_widths(self):
        """Intelligently adjust column widths based on content and available space."""
        if not self.table or not self.headers:
            return
            
        h_header = self.table.horizontalHeader()
        if not h_header:
            return
        
        viewport = self.table.viewport()
        if not viewport:
            return
        
        total_width = viewport.width()
        if total_width <= 0:
            return
        
        # Calculate required widths for fixed and content-sized columns
        fixed_width = 0
        content_columns = []
        stretch_columns = []
        
        for i, header in enumerate(self.headers):
            if header.upper() in ['ID', 'QTÉ', 'QUANTITÉ']:
                # Content-sized columns - ensure minimum width
                min_width = max(h_header.sectionSizeHint(i), 60)
                h_header.resizeSection(i, min_width)
                fixed_width += min_width
                content_columns.append(i)
            elif header.upper() in ['STATUT', 'STATUS', 'ÉTAT']:
                # Medium fixed columns
                fixed_width += 120
            else:
                stretch_columns.append(i)
        
        # Distribute remaining width among stretch columns
        remaining_width = total_width - fixed_width
        if stretch_columns and remaining_width > 0:
            column_width = max(remaining_width // len(stretch_columns), 150)
            for col in stretch_columns:
                h_header.resizeSection(col, column_width)

    def _on_item_double_clicked(self, item):
        """Handle double-click on table item"""
        row = item.row()
        self.rowDoubleClicked.emit(row)

    def get_selected_row_data(self) -> list[str] | None:
        """Get data from the currently selected row"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return None
        
        row_data = []
        for col in range(self.table.columnCount()):
            item = self.table.item(current_row, col)
            if item:
                row_data.append(item.text())
            else:
                row_data.append('')
        return row_data

    def add_context_action(self, action_name: str, label: str, icon: str = ""):
        """Add a context menu action"""
        self._context_actions.append((action_name, label, icon))

    def _show_context_menu(self, position):
        """Show context menu at the given position"""
        if not self._context_actions:
            return
            
        item = self.table.itemAt(position)
        if not item:
            return
            
        row = item.row()
        row_data = []
        for col in range(self.table.columnCount()):
            cell_item = self.table.item(row, col)
            if cell_item:
                row_data.append(cell_item.text())
            else:
                row_data.append('')
        
        menu = QMenu(self)
        
        # Add static context actions first
        for action_name, label, icon in self._context_actions:
            action = QAction(label, self)
            if icon:
                # Could set icon here if needed
                pass
            action.triggered.connect(lambda checked, name=action_name: 
                                   self.contextMenuActionTriggered.emit(name, row, row_data))
            menu.addAction(action)
        
        # Then emit signal to allow parent to customize menu
        if hasattr(self, 'contextMenuAboutToShow'):
            self.contextMenuAboutToShow.emit(row, row_data, menu)
        
        menu.exec(self.table.mapToGlobal(position))

    def get_selected_row_indices(self) -> list[int]:
        """Get list of selected row indices"""
        selected_rows = []
        for item in self.table.selectedItems():
            row = item.row()
            if row not in selected_rows:
                selected_rows.append(row)
        return sorted(selected_rows)

    def get_row_data(self, row: int) -> list[str]:
        """Get data for a specific row"""
        row_data = []
        for col in range(self.table.columnCount()):
            cell_item = self.table.item(row, col)
            if cell_item:
                row_data.append(cell_item.text())
            else:
                row_data.append('')
        return row_data

    def get_selected_rows_data(self) -> list[list[str]]:
        """Get data for all selected rows"""
        selected_indices = self.get_selected_row_indices()
        return [self.get_row_data(row) for row in selected_indices]

__all__ = ['DataGrid']
