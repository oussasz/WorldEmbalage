"""
Quad view widget for displaying four data grids in a 2x2 layout
with an optional header action bar for global actions.
"""
from PyQt6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt
from ui.widgets.data_grid import DataGrid


class QuadView(QWidget):
    """A widget that displays four data grids in a 2x2 layout with labels"""
    
    def __init__(self, 
                 top_left_title: str, top_left_columns: list,
                 top_right_title: str, top_right_columns: list,
                 bottom_left_title: str, bottom_left_columns: list,
                 bottom_right_title: str, bottom_right_columns: list,
                 parent=None):
        super().__init__(parent)
        self.top_left_grid = None
        self.top_right_grid = None
        self.bottom_left_grid = None
        self.bottom_right_grid = None
        self._header_action_layout: QHBoxLayout | None = None
        self._build_ui(
            top_left_title, top_left_columns,
            top_right_title, top_right_columns,
            bottom_left_title, bottom_left_columns,
            bottom_right_title, bottom_right_columns
        )
    
    def _build_ui(self, 
                  top_left_title: str, top_left_columns: list,
                  top_right_title: str, top_right_columns: list,
                  bottom_left_title: str, bottom_left_columns: list,
                  bottom_right_title: str, bottom_right_columns: list):
        """Build the quad view UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Optional header bar for actions (right-aligned)
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(8, 8, 8, 0)
        header_layout.setSpacing(6)
        header_layout.addStretch()  # push actions to the right
        self._header_action_layout = QHBoxLayout()
        self._header_action_layout.setContentsMargins(0, 0, 0, 0)
        self._header_action_layout.setSpacing(6)
        header_layout.addLayout(self._header_action_layout)
        layout.addWidget(header_widget)
        
        # Create grid layout for 2x2 arrangement
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(5, 5, 5, 5)
        grid_layout.setSpacing(10)
        
        # Top left section
        top_left_widget = self._create_section(top_left_title, top_left_columns)
        self.top_left_grid = top_left_widget.findChild(DataGrid)
        grid_layout.addWidget(top_left_widget, 0, 0)
        
        # Top right section
        top_right_widget = self._create_section(top_right_title, top_right_columns)
        self.top_right_grid = top_right_widget.findChild(DataGrid)
        grid_layout.addWidget(top_right_widget, 0, 1)
        
        # Bottom left section
        bottom_left_widget = self._create_section(bottom_left_title, bottom_left_columns)
        self.bottom_left_grid = bottom_left_widget.findChild(DataGrid)
        grid_layout.addWidget(bottom_left_widget, 1, 0)
        
        # Bottom right section
        bottom_right_widget = self._create_section(bottom_right_title, bottom_right_columns)
        self.bottom_right_grid = bottom_right_widget.findChild(DataGrid)
        grid_layout.addWidget(bottom_right_widget, 1, 1)
        
        layout.addLayout(grid_layout)

    def add_header_action_button(self, text: str, callback):
        """Add a button to the global header action bar (top-right)."""
        if not self._header_action_layout:
            return None
        btn = QPushButton(text)
        btn.setMaximumHeight(25)
        btn.clicked.connect(callback)
        self._header_action_layout.addWidget(btn)
        return btn
    
    def _create_section(self, title: str, columns: list) -> QWidget:
        """Create a section with title and data grid"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Title label
        label = QLabel(title)
        label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50; padding: 5px;")
        layout.addWidget(label)
        
        # Data grid
        grid = DataGrid(columns)
        layout.addWidget(grid)
        
        return widget
    
    def add_top_left_action_button(self, text: str, callback):
        """Add action button to top left section"""
        if self.top_left_grid:
            self.top_left_grid.add_action_button(text, callback)
    
    def add_top_right_action_button(self, text: str, callback):
        """Add action button to top right section"""
        if self.top_right_grid:
            self.top_right_grid.add_action_button(text, callback)
    
    def add_bottom_left_action_button(self, text: str, callback):
        """Add action button to bottom left section"""
        if self.bottom_left_grid:
            self.bottom_left_grid.add_action_button(text, callback)
    
    def add_bottom_right_action_button(self, text: str, callback):
        """Add action button to bottom right section"""
        if self.bottom_right_grid:
            self.bottom_right_grid.add_action_button(text, callback)
    
    def load_top_left_data(self, data: list):
        """Load data into top left grid"""
        if self.top_left_grid:
            self.top_left_grid.load_rows(data)
    
    def load_top_right_data(self, data: list):
        """Load data into top right grid"""
        if self.top_right_grid:
            self.top_right_grid.load_rows(data)
    
    def load_bottom_left_data(self, data: list):
        """Load data into bottom left grid"""
        if self.bottom_left_grid:
            self.bottom_left_grid.load_rows(data)
    
    def load_bottom_right_data(self, data: list):
        """Load data into bottom right grid"""
        if self.bottom_right_grid:
            self.bottom_right_grid.load_rows(data)
    
    def load_top_left_data_with_colors(self, data: list, colors: list):
        """Load data with colors into top left grid"""
        if self.top_left_grid:
            self.top_left_grid.load_rows_with_colors(data, colors)
    
    def load_top_right_data_with_colors(self, data: list, colors: list):
        """Load data with colors into top right grid"""
        if self.top_right_grid:
            self.top_right_grid.load_rows_with_colors(data, colors)
    
    def load_bottom_left_data_with_colors(self, data: list, colors: list):
        """Load data with colors into bottom left grid"""
        if self.bottom_left_grid:
            self.bottom_left_grid.load_rows_with_colors(data, colors)
    
    def load_bottom_right_data_with_colors(self, data: list, colors: list):
        """Load data with colors into bottom right grid"""
        if self.bottom_right_grid:
            self.bottom_right_grid.load_rows_with_colors(data, colors)
