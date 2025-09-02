"""
Unified reference generation system for World Embalage.
All document references follow the standardized format: PREFIX-YYYYMMDD-HHMMSS-NNNN

Where:
- PREFIX: Document type (DEV, BC, CMD, FPF, MP, etc.)
- YYYYMMDD: Date (year-month-day)
- HHMMSS: Time (hour-minute-second)
- NNNN: Sequential number (4 digits, padded with zeros)
"""

from __future__ import annotations
import secrets
from datetime import datetime
from typing import Optional
from config.database import SessionLocal
from sqlalchemy import text


class ReferenceGenerator:
    """Unified reference generator for all document types."""
    
    # Standard prefixes for different document types
    PREFIXES = {
        'quotation': 'DEV',           # Devis
        'supplier_order': 'BC',       # Bon de commande fournisseur
        'client_order': 'CMD',        # Commande client
        'finished_product': 'FPF',    # Fiche produit fini
        'raw_material_label': 'MP',   # Étiquette matière première
        'delivery': 'LIV',            # Livraison
        'invoice': 'FAC',             # Facture
        'reception': 'REC',           # Réception
        'return': 'RET',              # Retour
        'production': 'PROD',         # Production
        'stock_movement': 'MVT',      # Mouvement de stock
    }
    
    @classmethod
    def generate(cls, document_type: str, custom_suffix: Optional[str] = None) -> str:
        """
        Generate a standardized reference for any document type.
        
        Args:
            document_type: Type of document (must be in PREFIXES)
            custom_suffix: Optional custom suffix to append
            
        Returns:
            Standardized reference string
            
        Example:
            generate('quotation') -> 'DEV-20250902-143027-0001'
            generate('quotation', 'URGENT') -> 'DEV-20250902-143027-0001-URGENT'
        """
        if document_type not in cls.PREFIXES:
            raise ValueError(f"Unknown document type: {document_type}. Valid types: {list(cls.PREFIXES.keys())}")
        
        prefix = cls.PREFIXES[document_type]
        now = datetime.now()
        date_part = now.strftime('%Y%m%d')
        time_part = now.strftime('%H%M%S')
        
        # Get sequential number for this date and document type
        sequence_num = cls._get_next_sequence_number(prefix, date_part)
        
        # Build the reference
        reference = f"{prefix}-{date_part}-{time_part}-{sequence_num:04d}"
        
        # Add custom suffix if provided
        if custom_suffix:
            reference += f"-{custom_suffix}"
        
        return reference
    
    @classmethod
    def _get_next_sequence_number(cls, prefix: str, date_part: str) -> int:
        """Get the next sequence number for a given prefix and date."""
        session = SessionLocal()
        try:
            # Check all tables that might contain references with this prefix
            tables_to_check = [
                'quotations',
                'supplier_orders', 
                'client_orders',
                'receptions',
                'returns',
                'deliveries',
                'invoices',
                'production_batches',
                'stock_movements'
            ]
            
            max_sequence = 0
            pattern = f"{prefix}-{date_part}-%"
            
            for table in tables_to_check:
                try:
                    # Try different possible reference column names
                    for ref_col in ['reference', 'bon_commande_ref', 'batch_code']:
                        try:
                            result = session.execute(
                                text(f"""
                                    SELECT COALESCE(MAX(
                                        CAST(SUBSTRING({ref_col}, 
                                            LENGTH(:prefix) + LENGTH(:date_part) + 3,  -- +3 for two dashes
                                            4  -- sequence number length
                                        ) AS INTEGER)
                                    ), 0) as max_seq
                                    FROM {table} 
                                    WHERE {ref_col} LIKE :pattern
                                    AND LENGTH({ref_col}) >= LENGTH(:prefix) + LENGTH(:date_part) + 7  -- minimum expected length
                                """),
                                {
                                    "prefix": prefix,
                                    "date_part": date_part,
                                    "pattern": pattern
                                }
                            ).scalar()
                            
                            if result and result > max_sequence:
                                max_sequence = result
                            break  # If successful, don't try other column names for this table
                        except Exception:
                            continue  # Try next column name
                except Exception:
                    continue  # Skip this table if it doesn't exist or has issues
            
            return max_sequence + 1
            
        except Exception:
            # Fallback: use random suffix if database query fails
            return int(secrets.token_hex(2), 16) % 9999 + 1
        finally:
            session.close()
    
    @classmethod
    def generate_legacy_bc_format(cls) -> str:
        """
        Generate BC reference in legacy format BC{number}/{year} for backward compatibility.
        This method should only be used during transition period.
        """
        session = SessionLocal()
        try:
            current_year = datetime.now().year
            
            # Get the next number for this year in legacy format
            result = session.execute(
                text("""
                    SELECT COALESCE(MAX(
                        CAST(SUBSTRING(bon_commande_ref, 3, POSITION('/' IN bon_commande_ref) - 3) AS INTEGER)
                    ), 0) + 1 as next_number
                    FROM supplier_orders 
                    WHERE bon_commande_ref LIKE :pattern
                    AND bon_commande_ref NOT LIKE 'BC-202%'  -- Exclude new format
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
    
    @classmethod
    def is_standardized_format(cls, reference: str) -> bool:
        """Check if a reference follows the new standardized format."""
        if not reference:
            return False
        
        parts = reference.split('-')
        if len(parts) < 4:
            return False
        
        prefix, date_part, time_part, sequence = parts[:4]
        
        # Check prefix is valid
        if prefix not in cls.PREFIXES.values():
            return False
        
        # Check date part (YYYYMMDD)
        if len(date_part) != 8 or not date_part.isdigit():
            return False
        
        # Check time part (HHMMSS)
        if len(time_part) != 6 or not time_part.isdigit():
            return False
        
        # Check sequence part (4 digits)
        if len(sequence) != 4 or not sequence.isdigit():
            return False
        
        return True
    
    @classmethod
    def extract_info_from_reference(cls, reference: str) -> dict:
        """Extract information from a standardized reference."""
        if not cls.is_standardized_format(reference):
            return {
                'is_standardized': False,
                'prefix': None,
                'date': None,
                'time': None,
                'sequence': None,
                'custom_suffix': None
            }
        
        parts = reference.split('-')
        prefix = parts[0]
        date_part = parts[1]
        time_part = parts[2]
        sequence = parts[3]
        custom_suffix = '-'.join(parts[4:]) if len(parts) > 4 else None
        
        try:
            date_obj = datetime.strptime(date_part, '%Y%m%d').date()
            time_obj = datetime.strptime(time_part, '%H%M%S').time()
        except ValueError:
            date_obj = None
            time_obj = None
        
        return {
            'is_standardized': True,
            'prefix': prefix,
            'date': date_obj,
            'time': time_obj,
            'sequence': int(sequence),
            'custom_suffix': custom_suffix
        }


# Convenience functions for specific document types
def generate_quotation_reference(custom_suffix: Optional[str] = None) -> str:
    """Generate a quotation reference (DEV prefix)."""
    return ReferenceGenerator.generate('quotation', custom_suffix)


def generate_supplier_order_reference(custom_suffix: Optional[str] = None) -> str:
    """Generate a supplier order reference (BC prefix)."""
    return ReferenceGenerator.generate('supplier_order', custom_suffix)


def generate_client_order_reference(custom_suffix: Optional[str] = None) -> str:
    """Generate a client order reference (CMD prefix)."""
    return ReferenceGenerator.generate('client_order', custom_suffix)


def generate_finished_product_reference(custom_suffix: Optional[str] = None) -> str:
    """Generate a finished product fiche reference (FPF prefix)."""
    return ReferenceGenerator.generate('finished_product', custom_suffix)


def generate_raw_material_label_reference(custom_suffix: Optional[str] = None) -> str:
    """Generate a raw material label reference (MP prefix)."""
    return ReferenceGenerator.generate('raw_material_label', custom_suffix)


def generate_delivery_reference(custom_suffix: Optional[str] = None) -> str:
    """Generate a delivery reference (LIV prefix)."""
    return ReferenceGenerator.generate('delivery', custom_suffix)


def generate_invoice_reference(custom_suffix: Optional[str] = None) -> str:
    """Generate an invoice reference (FAC prefix)."""
    return ReferenceGenerator.generate('invoice', custom_suffix)


def generate_reception_reference(custom_suffix: Optional[str] = None) -> str:
    """Generate a reception reference (REC prefix)."""
    return ReferenceGenerator.generate('reception', custom_suffix)


def generate_return_reference(custom_suffix: Optional[str] = None) -> str:
    """Generate a return reference (RET prefix)."""
    return ReferenceGenerator.generate('return', custom_suffix)


def generate_production_reference(custom_suffix: Optional[str] = None) -> str:
    """Generate a production reference (PROD prefix)."""
    return ReferenceGenerator.generate('production', custom_suffix)


def generate_stock_movement_reference(custom_suffix: Optional[str] = None) -> str:
    """Generate a stock movement reference (MVT prefix)."""
    return ReferenceGenerator.generate('stock_movement', custom_suffix)


# Legacy compatibility function
def generate_reference(prefix: str) -> str:
    """
    Legacy function for backward compatibility.
    Maps old prefixes to new standardized system.
    """
    prefix_mapping = {
        'DEV': 'quotation',
        'BC': 'supplier_order', 
        'CMD': 'client_order',
        'FPF': 'finished_product',
        'MP': 'raw_material_label',
        'LIV': 'delivery',
        'FAC': 'invoice',
        'REC': 'reception',
        'RET': 'return',
        'PROD': 'production',
        'MVT': 'stock_movement'
    }
    
    document_type = prefix_mapping.get(prefix)
    if document_type:
        return ReferenceGenerator.generate(document_type)
    else:
        # Fallback for unknown prefixes
        return f"{prefix}-{secrets.token_hex(3).upper()}"


__all__ = [
    'ReferenceGenerator',
    'generate_quotation_reference',
    'generate_supplier_order_reference', 
    'generate_client_order_reference',
    'generate_finished_product_reference',
    'generate_raw_material_label_reference',
    'generate_delivery_reference',
    'generate_invoice_reference',
    'generate_reception_reference',
    'generate_return_reference',
    'generate_production_reference',
    'generate_stock_movement_reference',
    'generate_reference'  # Legacy compatibility
]
