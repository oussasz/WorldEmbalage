from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal


def format_date(d: date | None) -> str:
    return d.strftime('%d/%m/%Y') if d else ''


def format_datetime(dt: datetime | None) -> str:
    return dt.strftime('%d/%m/%Y %H:%M') if dt else ''


def money(amount: Decimal | float | int, currency: str = 'EUR') -> str:
    if isinstance(amount, (int, float)):
        amount = Decimal(str(amount))
    return f"{amount:.2f} {currency}"

__all__ = ['format_date', 'format_datetime', 'money']
