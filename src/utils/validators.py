from __future__ import annotations
from .exceptions import ValidationError


def require_positive_int(value: int, field: str):
    if not isinstance(value, int) or value <= 0:
        raise ValidationError(f"{field} must be a positive integer")


def require_non_empty(value: str, field: str):
    if not value or not value.strip():
        raise ValidationError(f"{field} must not be empty")

__all__ = ['require_positive_int', 'require_non_empty']
