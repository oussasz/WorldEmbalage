from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column
from sqlalchemy import DateTime, func, Integer


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class PKMixin:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


__all__ = [
    'Base', 'TimestampMixin', 'PKMixin'
]
