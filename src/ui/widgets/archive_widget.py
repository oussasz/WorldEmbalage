from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class ArchiveWidget(QWidget):
    """Archive widget for managing archived data"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the archive widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel("📁 Archive")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 20px;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 8px;
            }
        """)
        layout.addWidget(title_label)
        
        # Placeholder content
        content_label = QLabel("Cette section est prête pour le contenu d'archivage.\n\nVous pouvez maintenant spécifier ce qui doit être affiché ici.")
        content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #7f8c8d;
                padding: 20px;
                border: 2px dashed #bdc3c7;
                border-radius: 8px;
                background-color: #f8f9fa;
            }
        """)
        layout.addWidget(content_label)
        
        # Add stretch to center content
        layout.addStretch()

__all__ = ['ArchiveWidget']
