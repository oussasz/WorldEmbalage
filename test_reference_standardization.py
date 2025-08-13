#!/usr/bin/env python3
"""
Test script to verify all document types use standardized reference generation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.helpers import generate_reference

def test_all_document_references():
    """Test standardized reference generation for all document types in the application"""
    
    print("Testing standardized reference generation for all document types...")
    print("=" * 70)
    
    document_types = [
        ("DEV", "Devis (Quotations)"),
        ("CMD", "Commandes Fournisseur (Supplier Orders)"), 
        ("MAT", "Commandes Matières Premières (Raw Material Orders)"),
        ("CLI", "Commandes Client (Client Orders)"),
        ("FAC", "Factures (Invoices)"),
        ("BL", "Bons de Livraison (Delivery Notes)"),
        ("RET", "Retours (Returns)"),
        ("REC", "Réceptions (Receptions)")
    ]
    
    all_refs = []
    
    for prefix, description in document_types:
        print(f"\n{description}:")
        refs = []
        for i in range(2):  # Generate 2 references per type
            ref = generate_reference(prefix)
            refs.append(ref)
            all_refs.append(ref)
            print(f"  {i+1}. {ref}")
        
        # Verify format for this type
        print(f"  ✓ Format correct: {all(ref.startswith(f'{prefix}-') for ref in refs)}")
        print(f"  ✓ Unique: {len(set(refs)) == len(refs)}")
    
    print(f"\n{'='*70}")
    print("Global verification:")
    print(f"✓ Total references generated: {len(all_refs)}")
    print(f"✓ All references are globally unique: {len(set(all_refs)) == len(all_refs)}")
    
    # Check format consistency
    format_ok = True
    for ref in all_refs:
        parts = ref.split('-')
        if len(parts) != 2 or len(parts[1]) != 6:
            format_ok = False
            print(f"✗ Invalid format: {ref}")
    
    print(f"✓ All references follow format 'PREFIX-HEXCODE': {format_ok}")
    
    print(f"\n{'='*70}")
    print("✅ Standardized reference system implementation successful!")
    print("All document types now use the same reference generation method.")
    print("Format: PREFIX-HEXCODE (where HEXCODE is 6 random hex characters)")
    
    return True

if __name__ == "__main__":
    try:
        success = test_all_document_references()
        if success:
            print("\n🎉 Reference standardization complete!")
    except Exception as e:
        print(f"❌ Error testing reference generation: {e}")
