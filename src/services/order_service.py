from __future__ import annotations
from sqlalchemy.orm import Session
from loguru import logger
from models.orders import Quotation, ClientOrder, ClientOrderStatus, QuotationLineItem, ClientOrderLineItem
from models.clients import Client
from sqlalchemy import select
from decimal import Decimal
from typing import Sequence, Any, cast


class OrderService:
    def __init__(self, db: Session):
        self.db = db

    def create_quotation(self, client_id: int, reference: str, notes: str | None = None, line_items: Sequence[dict] | None = None) -> Quotation:
        client = self.db.get(Client, client_id)
        if not client:
            raise ValueError("Client not found")
        q = Quotation(client_id=client_id, reference=reference, notes=notes or '')
        self.db.add(q)
        self.db.flush()
        total = Decimal('0')
        for idx, item in enumerate(line_items or [], start=1):
            li = QuotationLineItem(
                quotation_id=q.id,
                line_number=idx,
                description=str(item.get('description') or ''),
                quantity=int(item.get('quantity') or 0),
                unit_price=Decimal(str(item.get('unit_price') or '0')),
                total_price=Decimal(str(item.get('total_price') or '0')),
                length_mm=item.get('length_mm'),
                width_mm=item.get('width_mm'),
                height_mm=item.get('height_mm'),
                color=item.get('color'),
                cardboard_type=item.get('cardboard_type'),
                is_cliche=bool(item.get('is_cliche') or False),
                notes=(str(item.get('notes')).strip() if item.get('notes') else None),
            )
            total += Decimal(str(item.get('total_price') or '0'))
            self.db.add(li)
        # Assign using cast to satisfy type checker for Numeric field
        cast(Any, q).total_amount = float(total)
        self.db.commit()
        self.db.refresh(q)
        return q

    def convert_to_order(self, quotation_id: int, reference: str) -> ClientOrder:
        quotation = self.db.get(Quotation, quotation_id)
        if not quotation:
            raise ValueError("Quotation not found")
        if quotation.client_order:
            raise ValueError("Quotation already converted")
        order = ClientOrder(
            client_id=quotation.client_id,
            quotation_id=quotation.id,
            reference=reference,
            total_amount=quotation.total_amount,
        )
        self.db.add(order)
        self.db.flush()
        # create order line items from quotation line items
        for qli in quotation.line_items:
            oli = ClientOrderLineItem(
                client_order_id=order.id,
                quotation_line_item_id=qli.id,
                line_number=qli.line_number,
                description=qli.description,
                quantity=qli.quantity,
                unit_price=qli.unit_price,
                total_price=qli.total_price,
                length_mm=qli.length_mm,
                width_mm=qli.width_mm,
                height_mm=qli.height_mm,
                color=qli.color,
                cardboard_type=qli.cardboard_type,
                is_cliche=qli.is_cliche,
                notes=qli.notes,
            )
            self.db.add(oli)
        self.db.commit()
        self.db.refresh(order)
        logger.debug("Quotation {} converted to order {}", quotation.reference, order.reference)
        return order

    def update_order_status(self, order_id: int, status: ClientOrderStatus) -> ClientOrder:
        order = self.db.get(ClientOrder, order_id)
        if not order:
            raise ValueError("Order not found")
        order.status = status
        self.db.commit()
        self.db.refresh(order)
        logger.debug("Order {} status updated to {}", order.reference, status)
        return order

    def list_orders(self) -> list[ClientOrder]:
        return list(self.db.scalars(select(ClientOrder)).all())

__all__ = ['OrderService']
