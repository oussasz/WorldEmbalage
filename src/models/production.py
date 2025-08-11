from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, Enum, Text, DateTime
from sqlalchemy.sql import func
from .base import Base, PKMixin, TimestampMixin
import enum
from datetime import datetime, timezone


class ProductionStage(enum.Enum):
    CUT_PRINT = 'découpe_impression'
    GLUE_ECLIPSAGE = 'collage_éclipsage'
    COMPLETE = 'terminé'


class ProductionBatch(PKMixin, TimestampMixin, Base):
    __tablename__ = 'production_batches'

    client_order_id: Mapped[int] = mapped_column(ForeignKey('client_orders.id', ondelete='CASCADE'), index=True, nullable=False)
    batch_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    stage: Mapped[ProductionStage] = mapped_column(Enum(ProductionStage), default=ProductionStage.CUT_PRINT, nullable=False, index=True)
    produced_quantity: Mapped[int] = mapped_column(Integer, default=0)
    waste_quantity: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def mark_stage(self, stage: ProductionStage):
        self.stage = stage
        if stage == ProductionStage.COMPLETE:
            self.completed_at = datetime.now(timezone.utc)

__all__ = ['ProductionBatch', 'ProductionStage']
