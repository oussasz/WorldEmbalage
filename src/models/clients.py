from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from .base import Base, PKMixin, TimestampMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .orders import ClientOrder, Quotation


class Client(PKMixin, TimestampMixin, Base):
    __tablename__ = 'clients'

    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    contact_name: Mapped[str | None] = mapped_column(String(128))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))

    orders: Mapped[list['ClientOrder']] = relationship(back_populates='client', cascade='all, delete-orphan')  # type: ignore[name-defined]
    quotations: Mapped[list['Quotation']] = relationship(back_populates='client', cascade='all, delete-orphan')  # type: ignore[name-defined]

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Client {self.name}>"

__all__ = ['Client']
