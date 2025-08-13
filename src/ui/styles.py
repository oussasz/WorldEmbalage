"""
UI Styles and Themes for World Embalage Application
"""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont, QPixmap, QPainter, QColor
from PyQt6.QtWidgets import QApplication

class IconManager:
    """Manages application icons with fallback to text-based icons"""
    
    @staticmethod
    def create_text_icon(text: str, size: int = 32, bg_color: str = "transparent", text_color: str = "#000000") -> QIcon:
        """Create a simple text-based icon, now transparent by default."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if bg_color != "transparent":
            painter.setBrush(QColor(bg_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(0, 0, size, size)
            
        painter.setPen(QColor(text_color))
        
        # Use a larger font size for emojis
        font = QFont("Segoe UI Emoji", size // 2, QFont.Weight.Normal)
        painter.setFont(font)
        painter.drawText(0, 0, size, size, Qt.AlignmentFlag.AlignCenter, text)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def get_dashboard_icon() -> QIcon:
        return IconManager.create_text_icon("📊")

    @staticmethod
    def get_supplier_icon() -> QIcon:
        return IconManager.create_text_icon("🏪")

    @staticmethod
    def get_client_icon() -> QIcon:
        return IconManager.create_text_icon("👥")

    @staticmethod
    def get_quotation_icon() -> QIcon:
        return IconManager.create_text_icon("📋")

    @staticmethod
    def get_supplier_order_icon() -> QIcon:
        return IconManager.create_text_icon("📦")

    @staticmethod
    def get_reception_icon() -> QIcon:
        return IconManager.create_text_icon("📥")

    @staticmethod
    def get_production_icon() -> QIcon:
        return IconManager.create_text_icon("🏭")

    @staticmethod
    def get_refresh_icon() -> QIcon:
        return IconManager.create_text_icon("🔄")


class StyleManager:
    """Manages application styling and themes"""
    
    WHITE_THEME = """
    /* GLOBAL ------------------------------------------------ */
    QWidget { background: #FFFFFF; color: #222222; font-size: 13px; }
    * { selection-background-color: #4A90E2; selection-color: #FFFFFF; }
    QToolTip { background: #2C3E50; color: #FFFFFF; border: 1px solid #1B2834; padding: 4px 6px; border-radius: 4px; }

    /* MAIN WINDOW */
    QMainWindow { background: #FFFFFF; }

    /* MENU BAR */
    QMenuBar { background: #F5F6F7; border-bottom: 1px solid #DADFE3; padding: 4px 6px; }
    QMenuBar::item { background: transparent; padding: 6px 12px; margin: 0 2px; border-radius: 4px; }
    QMenuBar::item:selected { background: #E4E8EB; color: #111111; }
    QMenuBar::item:pressed { background: #D5DADF; }

    QMenu { background: #FFFFFF; border: 1px solid #DADFE3; padding: 4px 0; }
    QMenu::item { padding: 6px 18px; color: #222222; }
    QMenu::item:selected { background: #4A90E2; color: #FFFFFF; }
    QMenu::separator { height: 1px; background: #E2E6EA; margin: 4px 8px; }

    /* TOOLBAR */
    QToolBar { background: #F5F6F7; border: none; border-bottom: 1px solid #DADFE3; padding: 4px; }
    QToolBar QLineEdit { background: #FFFFFF; color: #222222; border: 1px solid #C8D0D7; border-radius: 6px; padding: 6px 10px; }
    QToolBar QLineEdit:focus { border: 1px solid #4A90E2; }

    /* TABS */
    QTabWidget::pane { border: 1px solid #DADFE3; border-radius: 6px; top: 1px; }
    QTabBar::tab { background: #F2F3F5; color: #555555; padding: 8px 18px; border: 1px solid #DADFE3; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; }
    QTabBar::tab:selected { background: #FFFFFF; color: #222222; }
    QTabBar::tab:hover:!selected { background: #E9ECEF; color: #222222; }

    /* BUTTONS */
    QPushButton { background: #4A90E2; color: #FFFFFF; border: none; border-radius: 6px; padding: 6px 14px; font-weight: 500; }
    QPushButton:hover { background: #357ABD; }
    QPushButton:pressed { background: #2D6599; }
    QPushButton:disabled { background: #BFC7CE; color: #777777; }
    QPushButton[class="secondary"] { background: #6C757D; }
    QPushButton[class="secondary"]:hover { background: #5B6369; }

    /* INPUTS */
    QLineEdit, QTextEdit, QSpinBox, QComboBox, QDateEdit { background: #FFFFFF; color: #222222; border: 1px solid #C8D0D7; border-radius: 6px; padding: 6px 10px; }
    QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus, QDateEdit:focus { border: 1px solid #4A90E2; }
    QLineEdit::placeholder, QTextEdit::placeholder { color: #9AA2A9; }

    QComboBox QAbstractItemView { background: #FFFFFF; color: #222222; selection-background-color: #4A90E2; selection-color: #FFFFFF; border: 1px solid #C8D0D7; }

    /* TABLE */
    QTableWidget { 
        background: #FFFFFF; 
        gridline-color: #ECEFF1; 
        border: 1px solid #DADFE3; 
        border-radius: 6px; 
        alternate-background-color: #F8F9FA;
    }
    QTableWidget::item { 
        color: #222222; 
        padding: 4px 8px; 
        border-bottom: 1px solid #F0F1F2;
    }
    QTableWidget::item:selected { 
        background: #D7E9FA; 
        color: #1A1A1A; 
    }
    QTableWidget::item:hover { 
        background: #E8F4FD; 
    }
    QHeaderView::section { 
        background: #F5F6F7; 
        color: #3A3F44; 
        padding: 8px 12px; 
        border: none; 
        border-right: 1px solid #DADFE3;
        border-bottom: 1px solid #DADFE3; 
        font-weight: 600; 
        text-align: left;
    }
    QHeaderView::section:hover { 
        background: #E9ECEF; 
    }
    QHeaderView::section:pressed { 
        background: #DDE1E5; 
    }

    /* SCROLLBAR */
    QScrollBar:vertical { background: #F2F3F5; width: 12px; margin: 2px 0 2px 0; border-radius: 6px; }
    QScrollBar::handle:vertical { background: #C8D0D7; border-radius: 6px; min-height: 24px; }
    QScrollBar::handle:vertical:hover { background: #B1BBC3; }

    /* DIALOG */
    QDialog { background: #FFFFFF; }
    QLabel { color: #222222; }
    QTextEdit { min-height: 60px; }

    /* STATUS BAR */
    QStatusBar { background: #F5F6F7; color: #222222; border-top: 1px solid #DADFE3; }
    """
    
    @staticmethod
    def apply_white_theme(app: QApplication):
        """Apply the white theme to the application"""
        app.setStyleSheet(StyleManager.WHITE_THEME)
        font = QFont("Segoe UI", 10)
        app.setFont(font)

__all__ = ['StyleManager', 'IconManager']
