from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, Date
from sqlalchemy.sql import func
from .base import Base, PKMixin, TimestampMixin
from datetime import date


class ProductionBatch(PKMixin, TimestampMixin, Base):
    __tablename__ = 'production_batches'

    client_order_id: Mapped[int] = mapped_column(ForeignKey('client_orders.id', ondelete='CASCADE'), index=True, nullable=False)
    batch_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    production_date: Mapped[date | None] = mapped_column(Date())

    # Relationship to client order
    client_order: Mapped['ClientOrder'] = relationship(back_populates='production_batches')  # type: ignore[name-defined]


__all__ = ['ProductionBatch']
