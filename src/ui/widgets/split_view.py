"""
Split view widget for displaying two data grids side by side
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSplitter
from PyQt6.QtCore import Qt
from ui.widgets.data_grid import DataGrid


class SplitView(QWidget):
    """A widget that displays two data grids side by side with labels"""
    
    def __init__(self, left_title: str, left_columns: list, right_title: str, right_columns: list, parent=None):
        super().__init__(parent)
        self.left_grid = None
        self.right_grid = None
        self._build_ui(left_title, left_columns, right_title, right_columns)
    
    def _build_ui(self, left_title: str, left_columns: list, right_title: str, right_columns: list):
        """Build the split view UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create splitter for horizontal split
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left side
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(5)
        
        left_label = QLabel(left_title)
        left_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50; padding: 5px;")
        left_layout.addWidget(left_label)
        
        self.left_grid = DataGrid(left_columns)
        left_layout.addWidget(self.left_grid)
        
        # Right side
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(5)
        
        right_label = QLabel(right_title)
        right_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50; padding: 5px;")
        right_layout.addWidget(right_label)
        
        self.right_grid = DataGrid(right_columns)
        right_layout.addWidget(self.right_grid)
        
        # Add to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        # Set equal sizes
        splitter.setSizes([500, 500])
    
    def add_left_action_button(self, text: str, callback):
        """Add action button to left grid"""
        if self.left_grid:
            self.left_grid.add_action_button(text, callback)
    
    def add_right_action_button(self, text: str, callback):
        """Add action button to right grid"""
        if self.right_grid:
            self.right_grid.add_action_button(text, callback)
    
    def load_left_data(self, data: list):
        """Load data into left grid"""
        if self.left_grid:
            self.left_grid.load_rows(data)
    
    def load_right_data(self, data: list):
        """Load data into right grid"""
        if self.right_grid:
            self.right_grid.load_rows(data)

__all__ = ['SplitView']
