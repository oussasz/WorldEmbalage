from __future__ import annotations
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                            QLabel, QPushButton, QFrame, QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette
from config.database import SessionLocal
from models.suppliers import Supplier
from models.clients import Client
from models.orders import ClientOrder, SupplierOrder
from models.production import ProductionBatch
from models.orders import ClientOrderStatus, SupplierOrderStatus
from ui.styles import IconManager
from typing import Dict, Any, List
import datetime


class StatCard(QFrame):
    """A card widget to display statistics"""
    
    clicked = pyqtSignal()
    
    def __init__(self, title: str, value: str, icon: str, color: str = "#4A90E2", parent=None):
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui(title, value, icon, color)
        
    def _setup_ui(self, title: str, value: str, icon: str, color: str):
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet(f"""
            QFrame#StatCard {{
                background: white;
                border: 1px solid #E2E6EA;
                border-radius: 8px;
                padding: 16px;
                margin: 4px;
            }}
            QFrame#StatCard:hover {{
                border: 2px solid {color};
                background: #F8F9FA;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Icon and title row
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
        icon_label.setFixedSize(32, 32)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #6C757D; font-size: 12px; font-weight: 500;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label, 1)
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addLayout(header_layout)
        layout.addWidget(value_label)
        
        self.title_label = title_label
        self.value_label = value_label
        
    def update_value(self, new_value: str):
        """Update the card value"""
        self.value_label.setText(new_value)
        
    def mousePressEvent(self, a0):
        if a0 and hasattr(a0, 'button') and a0.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(a0)


class RecentActivityWidget(QFrame):
    """Widget to show recent activities"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #E2E6EA;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("AR Activité Récente")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2C3E50; margin-bottom: 12px;")
        layout.addWidget(header)
        
        # Scroll area for activities
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.activities_widget = QWidget()
        self.activities_layout = QVBoxLayout(self.activities_widget)
        self.activities_layout.setSpacing(8)
        
        scroll.setWidget(self.activities_widget)
        layout.addWidget(scroll)
        
    def add_activity(self, icon: str, text: str, time_str: str, color: str = "#6C757D"):
        """Add an activity item"""
        activity_frame = QFrame()
        activity_frame.setStyleSheet("""
            QFrame {
                background: #F8F9FA;
                border: 1px solid #E9ECEF;
                border-radius: 6px;
                padding: 8px;
                margin: 2px;
            }
        """)
        
        layout = QHBoxLayout(activity_frame)
        layout.setSpacing(12)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Text
        text_label = QLabel(text)
        text_label.setStyleSheet("color: #2C3E50; font-size: 13px;")
        text_label.setWordWrap(True)
        
        # Time
        time_label = QLabel(time_str)
        time_label.setStyleSheet("color: #6C757D; font-size: 11px;")
        time_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        
        layout.addWidget(icon_label)
        layout.addWidget(text_label, 1)
        layout.addWidget(time_label)
        
        self.activities_layout.insertWidget(0, activity_frame)  # Add to top
        
        # Limit to 10 activities
        if self.activities_layout.count() > 10:
            item = self.activities_layout.takeAt(10)
            if item and item.widget():
                widget = item.widget()
                if widget:
                    widget.deleteLater()
                
    def clear_activities(self):
        """Clear all activities"""
        while self.activities_layout.count():
            item = self.activities_layout.takeAt(0)
            if item and item.widget():
                widget = item.widget()
                if widget:
                    widget.deleteLater()


class QuickActionsWidget(QFrame):
    """Widget for quick action buttons"""
    
    actionTriggered = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #E2E6EA;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("⚡ Actions Rapides")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2C3E50; margin-bottom: 12px;")
        layout.addWidget(header)
        
        # Action buttons grid
        grid = QGridLayout()
        grid.setSpacing(8)
        
        actions = [
            ("C", "Nouveau Client", "new_client", "#28A745"),
            ("F", "Nouveau Fournisseur", "new_supplier", "#17A2B8"),
            ("D", "Nouveau Devis", "new_quotation", "#FFC107"),
            ("CM", "Commande Fournisseur", "new_supplier_order", "#6F42C1"),
            ("R", "Réception Matières", "new_reception", "#FD7E14"),
            ("P", "Lot Production", "new_production", "#20C997"),
        ]
        
        for i, (icon, text, action, color) in enumerate(actions):
            btn = QPushButton(f"{icon}\n{text}")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px;
                    font-size: 12px;
                    font-weight: 500;
                    text-align: center;
                    min-height: 60px;
                }}
                QPushButton:hover {{
                    background: {self._darken_color(color)};
                }}
                QPushButton:pressed {{
                    background: {self._darken_color(color, 0.2)};
                }}
            """)
            btn.clicked.connect(lambda checked, a=action: self.actionTriggered.emit(a))
            
            row, col = divmod(i, 2)
            grid.addWidget(btn, row, col)
            
        layout.addLayout(grid)
        layout.addStretch()
        
    def _darken_color(self, color: str, factor: float = 0.1) -> str:
        """Darken a hex color by a factor"""
        # Simple darkening by reducing RGB values
        if color.startswith('#'):
            color = color[1:]
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(max(0, int(c * (1 - factor))) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"


class Dashboard(QWidget):
    """Main dashboard widget"""
    
    actionTriggered = pyqtSignal(str)
    tabChangeRequested = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_refresh_timer()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header
        header = QLabel("TB Tableau de Bord - World Embalage")
        header.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #2C3E50; 
            margin-bottom: 8px;
            padding: 8px 0;
        """)
        layout.addWidget(header)
        
        # Stats cards row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)
        
        self.clients_card = StatCard("Clients", "0", "C", "#28A745")
        self.suppliers_card = StatCard("Fournisseurs", "0", "F", "#17A2B8")
        self.orders_card = StatCard("Commandes", "0", "CO", "#FFC107")
        self.production_card = StatCard("En Production", "0", "P", "#DC3545")
        
        # Connect card clicks to tab changes
        self.clients_card.clicked.connect(lambda: self.tabChangeRequested.emit(1))
        self.suppliers_card.clicked.connect(lambda: self.tabChangeRequested.emit(2))
        self.orders_card.clicked.connect(lambda: self.tabChangeRequested.emit(3))
        self.production_card.clicked.connect(lambda: self.tabChangeRequested.emit(5))
        
        stats_layout.addWidget(self.clients_card)
        stats_layout.addWidget(self.suppliers_card)
        stats_layout.addWidget(self.orders_card)
        stats_layout.addWidget(self.production_card)
        
        layout.addLayout(stats_layout)
        
        # Bottom section with activities and quick actions
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(16)
        
        # Recent activities (2/3 width)
        self.activities_widget = RecentActivityWidget()
        self.activities_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Quick actions (1/3 width)
        self.quick_actions = QuickActionsWidget()
        self.quick_actions.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.quick_actions.setFixedWidth(200)
        self.quick_actions.actionTriggered.connect(self.actionTriggered.emit)
        
        bottom_layout.addWidget(self.activities_widget, 2)
        bottom_layout.addWidget(self.quick_actions, 1)
        
        layout.addLayout(bottom_layout)
        
    def _setup_refresh_timer(self):
        """Setup auto-refresh timer"""
        self.refresh_timer = QTimer()
        self.refresh_timer.setSingleShot(False)
        self.refresh_timer.timeout.connect(self._safe_refresh)
        self.refresh_timer.start(60000)  # Refresh every 60 seconds (increased from 30)
        
    def _safe_refresh(self):
        """Safe refresh wrapper to prevent errors from blocking the timer"""
        try:
            self.refresh_data()
        except Exception as e:
            print(f"Dashboard refresh failed: {e}")
            # Continue timer despite errors
        
    def refresh_data(self):
        """Refresh dashboard data"""
        session = SessionLocal()
        try:
            # Update stats with error handling for missing tables
            try:
                clients_count = session.query(Client).count()
            except Exception:
                clients_count = 0
            
            try:
                suppliers_count = session.query(Supplier).count()
            except Exception:
                suppliers_count = 0
            
            try:
                orders_count = session.query(ClientOrder).count()
            except Exception:
                orders_count = 0
            
            try:
                production_count = session.query(ProductionBatch).count()
            except Exception:
                production_count = 0
            
            self.clients_card.update_value(str(clients_count))
            self.suppliers_card.update_value(str(suppliers_count))
            self.orders_card.update_value(str(orders_count))
            self.production_card.update_value(str(production_count))
            
            # Update recent activities
            self._update_recent_activities(session)
            
        except Exception as e:
            print(f"Error refreshing dashboard: {e}")
        finally:
            session.close()
            
    def _update_recent_activities(self, session):
        """Update recent activities list"""
        try:
            # Get recent orders with error handling
            try:
                recent_orders = session.query(ClientOrder).order_by(ClientOrder.id.desc()).limit(5).all()
            except Exception:
                recent_orders = []
            
            try:
                recent_supplier_orders = session.query(SupplierOrder).order_by(SupplierOrder.id.desc()).limit(3).all()
            except Exception:
                recent_supplier_orders = []
            
            try:
                recent_batches = session.query(ProductionBatch).order_by(ProductionBatch.id.desc()).limit(3).all()
            except Exception:
                recent_batches = []
            
            # Clear existing activities
            if hasattr(self, 'activities_widget'):
                self.activities_widget.clear_activities()
            
            # Add recent client orders
            for order in recent_orders:
                try:
                    self.activities_widget.add_activity(
                        "D", 
                        f"Commande client {order.reference} - {order.status.value}",
                        "Récent",
                        "#FFC107"
                    )
                except Exception:
                    pass
                
            # Add recent supplier orders
            for order in recent_supplier_orders:
                try:
                    self.activities_widget.add_activity(
                        "CM", 
                        f"Commande fournisseur {order.reference} - {order.status.value}",
                        "Récent",
                        "#6F42C1"
                    )
                except Exception:
                    pass
                
            # Add recent production batches
            for batch in recent_batches:
                try:
                    self.activities_widget.add_activity(
                        "P", 
                        f"Production lot {batch.batch_code} - {batch.stage.value}",
                        "Récent",
                        "#20C997"
                    )
                except Exception:
                    pass
        except Exception as e:
            print(f"Error updating recent activities: {e}")
            
    def add_activity(self, icon: str, text: str, color: str = "#6C757D"):
        """Add a new activity to the dashboard"""
        now = datetime.datetime.now()
        time_str = now.strftime("%H:%M")
        self.activities_widget.add_activity(icon, text, time_str, color)
