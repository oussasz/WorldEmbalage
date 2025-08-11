from __future__ import annotations
import secrets


def generate_reference(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(3).upper()}"

__all__ = ['generate_reference']
