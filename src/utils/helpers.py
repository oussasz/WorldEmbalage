from __future__ import annotations

# Import the new unified reference generation system
from .reference_generator import (
    ReferenceGenerator,
    generate_quotation_reference,
    generate_supplier_order_reference,
    generate_client_order_reference,
    generate_finished_product_reference,
    generate_raw_material_label_reference,
    generate_delivery_reference,
    generate_invoice_reference,
    generate_reception_reference,
    generate_return_reference,
    generate_production_reference,
    generate_stock_movement_reference
)


def generate_reference(prefix: str) -> str:
    """
    Legacy function for backward compatibility.
    Now uses the unified reference generation system.
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
        # For compatibility with any unknown prefixes
        import secrets
        return f"{prefix}-{secrets.token_hex(3).upper()}"


def generate_bon_commande_ref() -> str:
    """
    Generate a supplier order reference using the new unified system.
    For backward compatibility, this function is maintained but now uses
    the standardized format instead of the legacy BC{number}/{year} format.
    """
    return generate_supplier_order_reference()


def generate_bon_commande_ref_legacy() -> str:
    """
    Generate a BC reference in legacy format BC{number}/{year}.
    This function is kept for transition period only.
    Use generate_supplier_order_reference() for new implementations.
    """
    return ReferenceGenerator.generate_legacy_bc_format()


__all__ = [
    'generate_reference', 
    'generate_bon_commande_ref',
    'generate_bon_commande_ref_legacy',
    # Export all the new reference generators
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
    'generate_stock_movement_reference'
]
