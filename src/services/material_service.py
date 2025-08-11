from __future__ import annotations
from sqlalchemy.orm import Session
from loguru import logger
from models.orders import SupplierOrder, SupplierOrderStatus, Reception, Return
from models.suppliers import Supplier
from sqlalchemy import select
from typing import Iterable


class MaterialService:
    def __init__(self, db: Session):
        self.db = db

    def create_supplier_order(self, supplier_id: int, reference: str, notes: str | None = None) -> SupplierOrder:
        logger.debug("Creating supplier order ref={} supplier_id={}", reference, supplier_id)
        supplier = self.db.get(Supplier, supplier_id)
        if not supplier:
            raise ValueError("Supplier not found")
        order = SupplierOrder(supplier_id=supplier_id, reference=reference, notes=notes)
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def record_reception(self, supplier_order_id: int, quantity: int, notes: str | None = None) -> Reception:
        order = self.db.get(SupplierOrder, supplier_order_id)
        if not order:
            raise ValueError("Supplier order not found")
        reception = Reception(supplier_order_id=supplier_order_id, quantity=quantity, notes=notes)
        self.db.add(reception)
        # Update status heuristically (in real app, compute based on ordered vs received)
        order.status = SupplierOrderStatus.IN_STOCK
        self.db.commit()
        self.db.refresh(reception)
        return reception

    def record_return(self, supplier_order_id: int, quantity: int, reason: str | None = None) -> Return:
        order = self.db.get(SupplierOrder, supplier_order_id)
        if not order:
            raise ValueError("Supplier order not found")
        ret = Return(supplier_order_id=supplier_order_id, quantity=quantity, reason=reason)
        self.db.add(ret)
        self.db.commit()
        self.db.refresh(ret)
        return ret

    def list_orders(self) -> Iterable[SupplierOrder]:
        return self.db.scalars(select(SupplierOrder)).all()

__all__ = ['MaterialService']
