from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Sequence


@dataclass(slots=True)
class LineItem:
    description: str
    quantity: int
    unit_price: Decimal
    total: Decimal


@dataclass(slots=True)
class QuotationDocument:
    reference: str
    client_name: str
    issue_date: date
    valid_until: date | None
    currency: str
    items: Sequence[LineItem]
    notes: str | None

    @property
    def total_amount(self) -> Decimal:
        return sum((li.total for li in self.items), Decimal('0'))


__all__ = [
    'LineItem', 'QuotationDocument'
]
