from __future__ import annotations
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                            QLabel, QPushButton, QFrame, QScrollArea, QSizePolicy,
                            QTableWidget, QTableWidgetItem, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette
from config.database import SessionLocal
from models.suppliers import Supplier
from models.clients import Client
from models.orders import ClientOrder, SupplierOrder, SupplierOrderLineItem, MaterialDelivery, StockMovement, StockMovementType, Delivery, Quotation
from models.production import ProductionBatch
from models.orders import ClientOrderStatus, SupplierOrderStatus
from ui.styles import IconManager
from typing import Dict, Any, List
from sqlalchemy.sql import func
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
        
    # Stats cards row 1 removed as per user request (clients, fournisseurs, commandes, en production)

        # Stats cards row 2 (requested KPIs)
        stats_layout2 = QHBoxLayout()
        stats_layout2.setSpacing(12)

        self.plaques_stock_card = StatCard("Plaques en stock", "0", "PL", "#0D6EFD")
        self.pf_stock_card = StatCard("PF en stock", "0", "PF", "#20C997")
        self.devis_unconfirmed_card = StatCard("Devis non confirmés", "0", "D", "#6F42C1")
        self.supplier_initial_card = StatCard("Cmd. MP non passées", "0", "CM", "#FD7E14")

        # Navigate suggestions: clicking opens orders tab by default
        self.plaques_stock_card.clicked.connect(lambda: self.tabChangeRequested.emit(3))
        self.pf_stock_card.clicked.connect(lambda: self.tabChangeRequested.emit(5))
        self.devis_unconfirmed_card.clicked.connect(lambda: self.tabChangeRequested.emit(3))
        self.supplier_initial_card.clicked.connect(lambda: self.tabChangeRequested.emit(3))

        stats_layout2.addWidget(self.plaques_stock_card)
        stats_layout2.addWidget(self.pf_stock_card)
        stats_layout2.addWidget(self.devis_unconfirmed_card)
        stats_layout2.addWidget(self.supplier_initial_card)

        layout.addLayout(stats_layout2)

        # Middle section: two analytical tables
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(16)

        # Finished products stock table
        self.pf_table_frame = QFrame()
        self.pf_table_frame.setStyleSheet("""
            QFrame { background: white; border: 1px solid #E2E6EA; border-radius: 8px; }
            QHeaderView::section { background: #F8F9FA; font-weight: 600; }
        """)
        pf_vbox = QVBoxLayout(self.pf_table_frame)
        pf_header = QLabel("📦 Produits finis en stock (Top 10)")
        pf_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2C3E50; margin: 8px;")
        self.pf_table = QTableWidget(0, 6)
        self.pf_table.setHorizontalHeaderLabels(["Désignation", "Client", "Produit", "Livré", "Stock", "%"]) 
        self.pf_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        pf_vbox.addWidget(pf_header)
        pf_vbox.addWidget(self.pf_table)

        # Supplier orders progress table
        self.supplier_table_frame = QFrame()
        self.supplier_table_frame.setStyleSheet("""
            QFrame { background: white; border: 1px solid #E2E6EA; border-radius: 8px; }
            QHeaderView::section { background: #F8F9FA; font-weight: 600; }
        """)
        so_vbox = QVBoxLayout(self.supplier_table_frame)
        so_header = QLabel("📑 Commandes MP en cours")
        so_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2C3E50; margin: 8px;")
        self.supplier_table = QTableWidget(0, 8)
        self.supplier_table.setHorizontalHeaderLabels(["BC", "Ligne", "Client", "Désignation", "Commandé", "Réçu", "Restant", "Progression"]) 
        self.supplier_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        so_vbox.addWidget(so_header)
        so_vbox.addWidget(self.supplier_table)

        mid_layout.addWidget(self.pf_table_frame, 1)
        mid_layout.addWidget(self.supplier_table_frame, 1)

        layout.addLayout(mid_layout)

        # Bottom section: activities only (Quick Actions removed per request)
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(16)

        self.activities_widget = RecentActivityWidget()
        self.activities_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        bottom_layout.addWidget(self.activities_widget, 1)
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
            # Removed non-essential KPI updates (clients, fournisseurs, commandes, en production)

            # Compute requested KPIs
            plaques_stock = self._compute_plaques_stock(session)
            pf_stock_total, pf_rows = self._compute_finished_products_stock(session)
            devis_unconfirmed = self._compute_unconfirmed_quotations(session)
            supplier_initial = self._compute_supplier_orders_initial(session)

            self.plaques_stock_card.update_value(str(plaques_stock))
            self.pf_stock_card.update_value(str(pf_stock_total))
            self.devis_unconfirmed_card.update_value(str(devis_unconfirmed))
            self.supplier_initial_card.update_value(str(supplier_initial))

            # Populate tables
            self._populate_pf_table(pf_rows)
            self._populate_supplier_table(session)
            
            # Update recent activities
            self._update_recent_activities(session)
            
        except Exception as e:
            print(f"Error refreshing dashboard: {e}")
        finally:
            session.close()

    # ----- KPI computations -----
    def _compute_plaques_stock(self, session) -> int:
        """Approximate plaques stock = total deliveries - stock OUT/WASTE movements."""
        try:
            delivered = session.query(func.coalesce(func.sum(MaterialDelivery.received_quantity), 0)).scalar() or 0
        except Exception:
            delivered = 0
        try:
            outs = session.query(func.coalesce(func.sum(StockMovement.quantity), 0)).filter(
                StockMovement.movement_type.in_([StockMovementType.OUT, StockMovementType.WASTE])
            ).scalar() or 0
        except Exception:
            outs = 0
        return max(0, int(delivered) - int(outs))

    def _compute_finished_products_stock(self, session) -> tuple[int, list[dict]]:
        """Compute finished products stock aggregated by designation and client.
        Returns (total_stock, rows) where rows contain designation, client, produced, delivered, stock, percent.
        """
        rows: list[dict] = []
        total_stock = 0
        try:
            # Produced per client order
            produced_by_order = dict(session.query(
                ClientOrder.id, func.coalesce(func.sum(ProductionBatch.quantity), 0)
            ).join(ProductionBatch, ProductionBatch.client_order_id == ClientOrder.id).group_by(ClientOrder.id).all())

            # Delivered per client order
            delivered_by_order = dict(session.query(
                ClientOrder.id, func.coalesce(func.sum(Delivery.quantity), 0)
            ).join(Delivery, Delivery.client_order_id == ClientOrder.id).group_by(ClientOrder.id).all())

            # For each order, derive designation and client
            orders = session.query(ClientOrder).all()
            for order in orders:
                produced = int(produced_by_order.get(order.id, 0) or 0)
                delivered = int(delivered_by_order.get(order.id, 0) or 0)
                stock = max(0, produced - delivered)
                if stock <= 0:
                    continue

                # Derive designation: prefer quotation line item description, else client order line item description, else composed dims
                designation = "Produit fini"
                client_name = order.client.name if order.client else ""
                try:
                    if order.quotation and order.quotation.line_items:
                        qli = order.quotation.line_items[0]
                        if qli.description:
                            designation = qli.description
                        elif qli.length_mm and qli.width_mm and qli.height_mm:
                            designation = f"Caisse carton {qli.length_mm}×{qli.width_mm}×{qli.height_mm}"
                    elif order.line_items:
                        cli = order.line_items[0]
                        if cli.description:
                            designation = cli.description
                        elif cli.length_mm and cli.width_mm and cli.height_mm:
                            designation = f"Caisse carton {cli.length_mm}×{cli.width_mm}×{cli.height_mm}"
                except Exception:
                    pass

                percent = int(round((stock / produced) * 100)) if produced > 0 else 0
                rows.append({
                    'designation': designation,
                    'client': client_name,
                    'produced': produced,
                    'delivered': delivered,
                    'stock': stock,
                    'percent': percent
                })
                total_stock += stock

            # Sort by stock desc and limit top 10
            rows.sort(key=lambda r: r['stock'], reverse=True)
            rows = rows[:10]
        except Exception:
            pass
        return total_stock, rows

    def _compute_unconfirmed_quotations(self, session) -> int:
        """Count quotations not converted to client orders."""
        try:
            # Quotations with no linked client_order
            return session.query(Quotation).filter(Quotation.client_order == None).count()
        except Exception:
            return 0

    def _compute_supplier_orders_initial(self, session) -> int:
        """Count supplier orders not yet passed (status INITIAL)."""
        try:
            return session.query(SupplierOrder).filter(SupplierOrder.status == SupplierOrderStatus.INITIAL).count()
        except Exception:
            return 0

    # ----- Table population -----
    def _populate_pf_table(self, rows: list[dict]):
        try:
            self.pf_table.setRowCount(0)
            for r in rows:
                row = self.pf_table.rowCount()
                self.pf_table.insertRow(row)
                self.pf_table.setItem(row, 0, QTableWidgetItem(str(r.get('designation', ''))))
                self.pf_table.setItem(row, 1, QTableWidgetItem(str(r.get('client', ''))))
                self.pf_table.setItem(row, 2, QTableWidgetItem(str(r.get('produced', 0))))
                self.pf_table.setItem(row, 3, QTableWidgetItem(str(r.get('delivered', 0))))
                self.pf_table.setItem(row, 4, QTableWidgetItem(str(r.get('stock', 0))))
                # Progress bar for stock percentage
                prog = QProgressBar()
                prog.setValue(int(r.get('percent', 0)))
                prog.setFormat("%p%")
                prog.setStyleSheet("QProgressBar { border: 1px solid #ced4da; border-radius: 4px; text-align: center; }"
                                   "QProgressBar::chunk { background-color: #20C997; }")
                self.pf_table.setCellWidget(row, 5, prog)
        except Exception as e:
            print(f"PF table update failed: {e}")

    def _populate_supplier_table(self, session):
        try:
            self.supplier_table.setRowCount(0)
            q = session.query(SupplierOrderLineItem, SupplierOrder).join(SupplierOrder, SupplierOrderLineItem.supplier_order_id == SupplierOrder.id)
            q = q.filter(SupplierOrder.status != SupplierOrderStatus.COMPLETED)
            items = q.order_by(SupplierOrder.order_date.desc(), SupplierOrderLineItem.line_number.asc()).limit(50).all()
            for li, so in items:
                ordered = int(li.quantity or 0)
                received = int(li.total_received_quantity or 0)
                remaining = max(0, ordered - received)
                row = self.supplier_table.rowCount()
                self.supplier_table.insertRow(row)
                self.supplier_table.setItem(row, 0, QTableWidgetItem(so.reference or so.bon_commande_ref))
                self.supplier_table.setItem(row, 1, QTableWidgetItem(str(li.line_number)))
                self.supplier_table.setItem(row, 2, QTableWidgetItem(li.client.name if li.client else ""))
                designation = li.material_reference or li.cardboard_type or "Article"
                self.supplier_table.setItem(row, 3, QTableWidgetItem(designation))
                self.supplier_table.setItem(row, 4, QTableWidgetItem(str(ordered)))
                self.supplier_table.setItem(row, 5, QTableWidgetItem(str(received)))
                self.supplier_table.setItem(row, 6, QTableWidgetItem(str(remaining)))
                # Progress bar
                prog = QProgressBar()
                percent = int(round((received / ordered) * 100)) if ordered > 0 else 0
                prog.setValue(percent)
                prog.setFormat(f"{percent}%")
                prog.setStyleSheet("QProgressBar { border: 1px solid #ced4da; border-radius: 4px; text-align: center; }"
                                   "QProgressBar::chunk { background-color: #0D6EFD; }")
                self.supplier_table.setCellWidget(row, 7, prog)
        except Exception as e:
            print(f"Supplier table update failed: {e}")
            
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
                        f"Production lot {batch.batch_code} - {batch.production_date.strftime('%Y-%m-%d') if batch.production_date else 'N/A'}",
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
