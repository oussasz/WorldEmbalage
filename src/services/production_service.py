from __future__ import annotations
from sqlalchemy.orm import Session
from loguru import logger
from models.production import ProductionBatch
from sqlalchemy import select
from datetime import date


class ProductionService:
    def __init__(self, db: Session):
        self.db = db

    def create_batch(self, client_order_id: int, batch_code: str, quantity: int = 0, production_date: date | None = None, description: str | None = None) -> ProductionBatch:
        batch = ProductionBatch(
            client_order_id=client_order_id, 
            batch_code=batch_code,
            quantity=quantity,
            production_date=production_date or date.today(),
            description=description
        )
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)
        logger.debug("Created production batch {} for order {} with quantity {} and description '{}'", batch_code, client_order_id, quantity, description or "N/A")
        return batch

    def update_batch(self, batch_id: int, quantity: int | None = None, production_date: date | None = None) -> ProductionBatch:
        batch = self.db.get(ProductionBatch, batch_id)
        if not batch:
            raise ValueError("Batch not found")
        
        if quantity is not None:
            batch.quantity = quantity
        if production_date is not None:
            batch.production_date = production_date
            
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def list_batches(self) -> list[ProductionBatch]:
        return list(self.db.scalars(select(ProductionBatch)).all())

__all__ = ['ProductionService']
