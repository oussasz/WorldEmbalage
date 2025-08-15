from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Date, Enum, ForeignKey, Numeric, Text, DateTime, Boolean
from sqlalchemy.sql import func
from .base import Base, PKMixin, TimestampMixin
import enum
from typing import TYPE_CHECKING
if TYPE_CHECKING:  # pragma: no cover
    from .suppliers import Supplier
    from .clients import Client
    from .plaques import Plaque

# Enums
class SupplierOrderStatus(str, enum.Enum):
    INITIAL = 'commande_initial'
    ORDERED = 'commande_passee'
    RECEIVED = 'commande_arrivee'


class ClientOrderStatus(str, enum.Enum):
    IN_PREPARATION = 'en_préparation'
    IN_PRODUCTION = 'en_production'
    COMPLETE = 'terminé'
    CONFIRMED = 'confirmed'


class DeliveryStatus(str, enum.Enum):
    PARTIAL = 'partiel'
    COMPLETE = 'complet'


class BoxColor(str, enum.Enum):
    BLANC = 'blanc'
    BRUN = 'brun'


class SupplierOrder(PKMixin, TimestampMixin, Base):
    __tablename__ = 'supplier_orders'

    supplier_id: Mapped[int] = mapped_column(ForeignKey('suppliers.id', ondelete='RESTRICT'), index=True, nullable=False)
    bon_commande_ref: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)  # Format: BC16/2025
    order_date: Mapped[Date] = mapped_column(Date, server_default=func.current_date(), index=True)
    status: Mapped[SupplierOrderStatus] = mapped_column(
        Enum(SupplierOrderStatus, native_enum=False), 
        default=SupplierOrderStatus.INITIAL, 
        index=True
    )
    total_amount: Mapped[Numeric] = mapped_column(Numeric(12, 2), nullable=False, default=0)  # Total UTTC
    currency: Mapped[str] = mapped_column(String(3), default='DZD')
    notes: Mapped[str | None] = mapped_column(Text())

    supplier: Mapped['Supplier'] = relationship(back_populates='supplier_orders')  # type: ignore[name-defined]
    line_items: Mapped[list['SupplierOrderLineItem']] = relationship(back_populates='supplier_order', cascade='all, delete-orphan')
    receptions: Mapped[list['Reception']] = relationship(back_populates='supplier_order', cascade='all, delete-orphan')
    returns: Mapped[list['Return']] = relationship(back_populates='supplier_order', cascade='all, delete-orphan')


class SupplierOrderLineItem(PKMixin, TimestampMixin, Base):
    __tablename__ = 'supplier_order_line_items'

    supplier_order_id: Mapped[int] = mapped_column(ForeignKey('supplier_orders.id', ondelete='CASCADE'), nullable=False, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey('clients.id', ondelete='RESTRICT'), nullable=False, index=True)  # Client for this material
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)  # Order within the bon de commande
    
    # Article information
    code_article: Mapped[str] = mapped_column(String(100), nullable=False)  # Code article
    
    # Mesure de caisse (box dimensions)
    caisse_length_mm: Mapped[int] = mapped_column(Integer, nullable=False)  # L
    caisse_width_mm: Mapped[int] = mapped_column(Integer, nullable=False)   # l
    caisse_height_mm: Mapped[int] = mapped_column(Integer, nullable=False)  # H
    
    # Dimension de plaque (calculated plaque dimensions)
    plaque_width_mm: Mapped[int] = mapped_column(Integer, nullable=False)    # largeur plaque
    plaque_length_mm: Mapped[int] = mapped_column(Integer, nullable=False)   # longueur plaque
    plaque_flap_mm: Mapped[int] = mapped_column(Integer, nullable=False)     # rabat plaque
    
    # Pricing and quantity
    prix_uttc_plaque: Mapped[Numeric] = mapped_column(Numeric(12, 2), nullable=False)  # Prix UTTC par plaque
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)  # Quantité de plaques
    total_line_amount: Mapped[Numeric] = mapped_column(Numeric(12, 2), nullable=False, default=0)  # quantity * prix_uttc_plaque
    
    # Additional specifications
    cardboard_type: Mapped[str | None] = mapped_column(String(64))  # Type de carton
    notes: Mapped[str | None] = mapped_column(Text())

    supplier_order: Mapped['SupplierOrder'] = relationship(back_populates='line_items')
    client: Mapped['Client'] = relationship()  # type: ignore[name-defined]


class Reception(PKMixin, TimestampMixin, Base):
    __tablename__ = 'receptions'

    supplier_order_id: Mapped[int] = mapped_column(ForeignKey('supplier_orders.id', ondelete='CASCADE'), index=True, nullable=False)
    reception_date: Mapped[Date] = mapped_column(Date, server_default=func.current_date(), index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text())

    supplier_order: Mapped['SupplierOrder'] = relationship(back_populates='receptions')


class Return(PKMixin, TimestampMixin, Base):
    __tablename__ = 'returns'

    supplier_order_id: Mapped[int] = mapped_column(ForeignKey('supplier_orders.id', ondelete='CASCADE'), index=True, nullable=False)
    return_date: Mapped[Date] = mapped_column(Date, server_default=func.current_date(), index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text())

    supplier_order: Mapped['SupplierOrder'] = relationship(back_populates='returns')


class Quotation(PKMixin, TimestampMixin, Base):
    __tablename__ = 'quotations'

    client_id: Mapped[int] = mapped_column(ForeignKey('clients.id', ondelete='RESTRICT'), nullable=False, index=True)
    reference: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    issue_date: Mapped[Date] = mapped_column(Date, server_default=func.current_date(), index=True)
    valid_until: Mapped[Date | None] = mapped_column(Date)
    total_amount: Mapped[Numeric] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), default='DZD')
    is_initial: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text())

    client: Mapped['Client'] = relationship(back_populates='quotations')  # type: ignore[name-defined]
    client_order: Mapped['ClientOrder'] = relationship(back_populates='quotation', uselist=False)
    line_items: Mapped[list['QuotationLineItem']] = relationship(back_populates='quotation', cascade='all, delete-orphan')


class QuotationLineItem(PKMixin, TimestampMixin, Base):
    __tablename__ = 'quotation_line_items'

    quotation_id: Mapped[int] = mapped_column(ForeignKey('quotations.id', ondelete='CASCADE'), nullable=False, index=True)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)  # ordre dans le devis
    description: Mapped[str | None] = mapped_column(String(255))  # description libre
    quantity: Mapped[str] = mapped_column(String(100), nullable=False, default='1')
    unit_price: Mapped[Numeric] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_price: Mapped[Numeric] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    
    # Spécifications techniques du carton
    length_mm: Mapped[int | None] = mapped_column(Integer)
    width_mm: Mapped[int | None] = mapped_column(Integer)
    height_mm: Mapped[int | None] = mapped_column(Integer)
    color: Mapped[BoxColor | None] = mapped_column(Enum(BoxColor, native_enum=False))
    cardboard_type: Mapped[str | None] = mapped_column(String(64))  # épaisseur / cannelure
    is_cliche: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    notes: Mapped[str | None] = mapped_column(Text())

    quotation: Mapped['Quotation'] = relationship(back_populates='line_items')

    @property
    def numeric_quantity(self) -> int:
        """Extracts the numeric part of the quantity string for calculations."""
        import re
        numbers = re.findall(r'\d+', self.quantity)
        return int(numbers[-1]) if numbers else 0


class ClientOrder(PKMixin, TimestampMixin, Base):
    __tablename__ = 'client_orders'

    client_id: Mapped[int] = mapped_column(ForeignKey('clients.id', ondelete='RESTRICT'), nullable=False, index=True)
    quotation_id: Mapped[int | None] = mapped_column(ForeignKey('quotations.id', ondelete='SET NULL'), index=True)
    supplier_order_id: Mapped[int | None] = mapped_column(ForeignKey('supplier_orders.id', ondelete='SET NULL'), index=True)
    reference: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    order_date: Mapped[Date] = mapped_column(Date, server_default=func.current_date(), index=True)
    status: Mapped[ClientOrderStatus] = mapped_column(Enum(ClientOrderStatus, native_enum=False), default=ClientOrderStatus.IN_PREPARATION, index=True)
    total_amount: Mapped[Numeric] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text())

    client: Mapped['Client'] = relationship(back_populates='orders')  # type: ignore[name-defined]
    quotation: Mapped['Quotation'] = relationship(back_populates='client_order')
    supplier_order: Mapped['SupplierOrder'] = relationship()
    line_items: Mapped[list['ClientOrderLineItem']] = relationship(back_populates='client_order', cascade='all, delete-orphan')

    deliveries: Mapped[list['Delivery']] = relationship(back_populates='client_order', cascade='all, delete-orphan')
    invoices: Mapped[list['Invoice']] = relationship(back_populates='client_order', cascade='all, delete-orphan')


class ClientOrderLineItem(PKMixin, TimestampMixin, Base):
    __tablename__ = 'client_order_line_items'

    client_order_id: Mapped[int] = mapped_column(ForeignKey('client_orders.id', ondelete='CASCADE'), nullable=False, index=True)
    quotation_line_item_id: Mapped[int | None] = mapped_column(ForeignKey('quotation_line_items.id', ondelete='SET NULL'), index=True)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)  # ordre dans la commande
    description: Mapped[str | None] = mapped_column(String(255))  # description libre
    quantity: Mapped[str] = mapped_column(String(100), nullable=False, default='1')
    unit_price: Mapped[Numeric] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_price: Mapped[Numeric] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    
    # Spécifications techniques du carton
    length_mm: Mapped[int | None] = mapped_column(Integer)
    width_mm: Mapped[int | None] = mapped_column(Integer)
    height_mm: Mapped[int | None] = mapped_column(Integer)
    color: Mapped[BoxColor | None] = mapped_column(Enum(BoxColor, native_enum=False))
    cardboard_type: Mapped[str | None] = mapped_column(String(64))  # épaisseur / cannelure
    is_cliche: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    notes: Mapped[str | None] = mapped_column(Text())

    client_order: Mapped['ClientOrder'] = relationship(back_populates='line_items')
    quotation_line_item: Mapped['QuotationLineItem'] = relationship()

    @property
    def numeric_quantity(self) -> int:
        """Extracts the numeric part of the quantity string for calculations."""
        import re
        numbers = re.findall(r'\d+', self.quantity)
        return int(numbers[-1]) if numbers else 0


class Delivery(PKMixin, TimestampMixin, Base):
    __tablename__ = 'deliveries'

    client_order_id: Mapped[int] = mapped_column(ForeignKey('client_orders.id', ondelete='CASCADE'), nullable=False, index=True)
    delivery_date: Mapped[Date] = mapped_column(Date, server_default=func.current_date(), index=True)
    status: Mapped[DeliveryStatus] = mapped_column(Enum(DeliveryStatus, native_enum=False), default=DeliveryStatus.PARTIAL, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text())

    client_order: Mapped['ClientOrder'] = relationship(back_populates='deliveries')


class Invoice(PKMixin, TimestampMixin, Base):
    __tablename__ = 'invoices'

    client_order_id: Mapped[int] = mapped_column(ForeignKey('client_orders.id', ondelete='CASCADE'), nullable=False, index=True)
    invoice_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    issue_date: Mapped[Date] = mapped_column(Date, server_default=func.current_date(), index=True)
    due_date: Mapped[Date | None] = mapped_column(Date)
    total_ht: Mapped[Numeric] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_tva: Mapped[Numeric] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_ttc: Mapped[Numeric] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), default='DZD')

    client_order: Mapped['ClientOrder'] = relationship(back_populates='invoices')


class StockMovementType(str, enum.Enum):
    IN = 'in'
    OUT = 'out'
    WASTE = 'waste'


class StockMovement(PKMixin, TimestampMixin, Base):
    __tablename__ = 'stock_movements'

    plaque_id: Mapped[int] = mapped_column(ForeignKey('plaques.id', ondelete='RESTRICT'), index=True, nullable=False)
    movement_date: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    movement_type: Mapped[StockMovementType] = mapped_column(Enum(StockMovementType, native_enum=False), index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    related_order_id: Mapped[int | None] = mapped_column(Integer, index=True)  # could link to supplier or client order
    notes: Mapped[str | None] = mapped_column(Text())

    plaque: Mapped['Plaque'] = relationship(back_populates='stock_movements')  # type: ignore[name-defined]

__all__ = [
    'SupplierOrder', 'SupplierOrderLineItem', 'Reception', 'Return', 'Quotation', 'QuotationLineItem', 
    'ClientOrder', 'ClientOrderLineItem', 'Delivery', 'Invoice', 'StockMovement', 'SupplierOrderStatus', 
    'ClientOrderStatus', 'DeliveryStatus', 'StockMovementType', 'BoxColor'
]
