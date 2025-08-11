from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, Enum, ForeignKey
from .base import Base, PKMixin, TimestampMixin
import enum
from typing import TYPE_CHECKING
if TYPE_CHECKING:  # pragma: no cover
    from .orders import StockMovement


class PlaqueStatus(enum.Enum):
    IN_STOCK = 'in_stock'
    RESERVED = 'reserved'
    USED = 'used'
    WASTE = 'waste'


class Plaque(PKMixin, TimestampMixin, Base):
    __tablename__ = 'plaques'

    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    material_type: Mapped[str] = mapped_column(String(64), index=True)
    length_mm: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    width_mm: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    thickness_mm: Mapped[float | None]
    flute_type: Mapped[str | None] = mapped_column(String(16))
    status: Mapped[PlaqueStatus] = mapped_column(Enum(PlaqueStatus), default=PlaqueStatus.IN_STOCK, nullable=False, index=True)

    stock_movements: Mapped[list['StockMovement']] = relationship(back_populates='plaque', cascade='all, delete-orphan')  # type: ignore[name-defined]

    def dimension_str(self) -> str:
        return f"{self.length_mm}x{self.width_mm}"

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Plaque {self.code} {self.dimension_str()}>"

__all__ = ['Plaque', 'PlaqueStatus']
