"""
Unified reference generation system for World Embalage.
All document references follow the short format: PPNNN

Where:
- PP: Two-letter document type prefix (DV, BC, CM, FP, MP, etc.)
- NNN: Sequential number (3 digits, padded with zeros)

Examples: DV001, BC001, CM001, FP001, MP001
"""

from __future__ import annotations
import secrets
from datetime import datetime
from typing import Optional
from config.database import SessionLocal
from sqlalchemy import text


class ReferenceGenerator:
    """Unified reference generator for all document types with short format."""
    
    # Short prefixes for different document types (2 letters + 3 digits = 5 chars total)
    PREFIXES = {
        'quotation': 'DV',            # Devis
        'supplier_order': 'BC',       # Bon de commande fournisseur
        'client_order': 'CM',         # Commande client
        'finished_product': 'FP',     # Fiche produit fini
        'raw_material_label': 'MP',   # Étiquette matière première
        'delivery': 'LV',             # Livraison
        'invoice': 'FC',              # Facture
        'reception': 'RC',            # Réception
        'return': 'RT',               # Retour
        'production': 'PD',           # Production
        'stock_movement': 'MV',       # Mouvement de stock
    }
    
    # Legacy prefixes for backward compatibility
    LEGACY_PREFIXES = {
        'quotation': 'DEV',           # Old format
        'supplier_order': 'BC',       # Stays the same
        'client_order': 'CMD',        # Old format
        'finished_product': 'FPF',    # Old format
        'raw_material_label': 'MP',   # Stays the same
        'delivery': 'LIV',            # Old format
        'invoice': 'FAC',             # Old format
        'reception': 'REC',           # Old format
        'return': 'RET',              # Old format
        'production': 'PROD',         # Old format
        'stock_movement': 'MVT',      # Old format
    }
    
    @classmethod
    def generate(cls, document_type: str, custom_suffix: Optional[str] = None) -> str:
        """
        Generate a short reference for any document type.
        
        Args:
            document_type: Type of document (must be in PREFIXES)
            custom_suffix: Optional custom suffix to append (ignored in short format)
            
        Returns:
            Short reference string (5 characters: PPNNN)
            
        Example:
            generate('quotation') -> 'DV001'
            generate('supplier_order') -> 'BC001'
        """
        if document_type not in cls.PREFIXES:
            raise ValueError(f"Unknown document type: {document_type}. Valid types: {list(cls.PREFIXES.keys())}")
        
        prefix = cls.PREFIXES[document_type]
        
        # Get sequential number for this document type
        sequence_num = cls._get_next_sequence_number(prefix)
        
        # Build the short reference: PP + NNN
        reference = f"{prefix}{sequence_num:03d}"
        
        return reference
    
    @classmethod
    def _get_next_sequence_number(cls, prefix: str) -> int:
        """Get the next sequence number for a given prefix (short format)."""
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
            pattern = f"{prefix}%"
            
            for table in tables_to_check:
                try:
                    # Try different possible reference column names
                    for ref_col in ['reference', 'bon_commande_ref', 'batch_code']:
                        try:
                            result = session.execute(
                                text(f"""
                                    SELECT COALESCE(MAX(
                                        CAST(SUBSTRING({ref_col}, 3, 3) AS INTEGER)
                                    ), 0) as max_seq
                                    FROM {table} 
                                    WHERE {ref_col} LIKE :pattern
                                    AND LENGTH({ref_col}) = 5
                                    AND {ref_col} REGEXP '^[A-Z]{{2}}[0-9]{{3}}$'
                                """),
                                {
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
            return int(secrets.token_hex(1), 16) % 999 + 1
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
        """Check if a reference follows the new short format (PPNNN)."""
        if not reference or len(reference) != 5:
            return False
        
        # Check if it matches the pattern: 2 letters + 3 digits
        if not (reference[:2].isalpha() and reference[2:].isdigit()):
            return False
        
        # Check if prefix is valid
        prefix = reference[:2]
        if prefix not in cls.PREFIXES.values():
            return False
        
        return True
    
    @classmethod
    def extract_info_from_reference(cls, reference: str) -> dict:
        """Extract information from a short reference."""
        if not cls.is_standardized_format(reference):
            return {
                'is_standardized': False,
                'prefix': None,
                'sequence': None,
                'document_type': None
            }
        
        prefix = reference[:2]
        sequence = int(reference[2:])
        
        # Find document type from prefix
        document_type = None
        for doc_type, doc_prefix in cls.PREFIXES.items():
            if doc_prefix == prefix:
                document_type = doc_type
                break
        
        return {
            'is_standardized': True,
            'prefix': prefix,
            'sequence': sequence,
            'document_type': document_type
        }


# Convenience functions for specific document types
def generate_quotation_reference(custom_suffix: Optional[str] = None) -> str:
    """Generate a quotation reference (DV prefix)."""
    return ReferenceGenerator.generate('quotation')


def generate_supplier_order_reference(custom_suffix: Optional[str] = None) -> str:
    """Generate a supplier order reference (BC prefix)."""
    return ReferenceGenerator.generate('supplier_order')


def generate_client_order_reference(custom_suffix: Optional[str] = None) -> str:
    """Generate a client order reference (CM prefix)."""
    return ReferenceGenerator.generate('client_order')


def generate_finished_product_reference(custom_suffix: Optional[str] = None) -> str:
    """Generate a finished product fiche reference (FP prefix)."""
    return ReferenceGenerator.generate('finished_product')


def generate_raw_material_label_reference(custom_suffix: Optional[str] = None) -> str:
    """Generate a raw material label reference (MP prefix)."""
    return ReferenceGenerator.generate('raw_material_label')


def generate_delivery_reference(custom_suffix: Optional[str] = None) -> str:
    """Generate a delivery reference (LV prefix)."""
    return ReferenceGenerator.generate('delivery')


def generate_invoice_reference(custom_suffix: Optional[str] = None) -> str:
    """Generate an invoice reference (FC prefix)."""
    return ReferenceGenerator.generate('invoice')


def generate_reception_reference(custom_suffix: Optional[str] = None) -> str:
    """Generate a reception reference (RC prefix)."""
    return ReferenceGenerator.generate('reception')


def generate_return_reference(custom_suffix: Optional[str] = None) -> str:
    """Generate a return reference (RT prefix)."""
    return ReferenceGenerator.generate('return')


def generate_production_reference(custom_suffix: Optional[str] = None) -> str:
    """Generate a production reference (PD prefix)."""
    return ReferenceGenerator.generate('production')


def generate_stock_movement_reference(custom_suffix: Optional[str] = None) -> str:
    """Generate a stock movement reference (MV prefix)."""
    return ReferenceGenerator.generate('stock_movement')


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
