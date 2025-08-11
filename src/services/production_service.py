from __future__ import annotations
from sqlalchemy.orm import Session
from loguru import logger
from models.production import ProductionBatch, ProductionStage
from sqlalchemy import select


class ProductionService:
    def __init__(self, db: Session):
        self.db = db

    def create_batch(self, client_order_id: int, batch_code: str) -> ProductionBatch:
        batch = ProductionBatch(client_order_id=client_order_id, batch_code=batch_code)
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)
        logger.debug("Created production batch {} for order {}", batch_code, client_order_id)
        return batch

    def advance_stage(self, batch_id: int, stage: ProductionStage) -> ProductionBatch:
        batch = self.db.get(ProductionBatch, batch_id)
        if not batch:
            raise ValueError("Batch not found")
        batch.mark_stage(stage)
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def list_batches(self) -> list[ProductionBatch]:
        return list(self.db.scalars(select(ProductionBatch)).all())

__all__ = ['ProductionService']
