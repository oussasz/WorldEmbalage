from __future__ import annotations
import secrets
from datetime import datetime


def generate_reference(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(3).upper()}"


def generate_bon_commande_ref() -> str:
    """Generate a BC reference in format BC{number}/{year}"""
    from config.database import SessionLocal
    from models.orders import SupplierOrder
    from sqlalchemy import func, text
    
    session = SessionLocal()
    try:
        current_year = datetime.now().year
        
        # Get the next number for this year
        result = session.execute(
            text("""
                SELECT COALESCE(MAX(
                    CAST(SUBSTRING(bon_commande_ref, 3, POSITION('/' IN bon_commande_ref) - 3) AS INTEGER)
                ), 0) + 1 as next_number
                FROM supplier_orders 
                WHERE bon_commande_ref LIKE :pattern
            """),
            {"pattern": f"BC%/{current_year}"}
        ).scalar()
        
        next_number = result if result else 1
        return f"BC{next_number:02d}/{current_year}"
        
    except Exception:
        # Fallback to simple numbering if query fails
        return f"BC01/{datetime.now().year}"
    finally:
        session.close()


__all__ = ['generate_reference', 'generate_bon_commande_ref']
