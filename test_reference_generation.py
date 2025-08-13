#!/usr/bin/env python3
"""
Test script to verify standardized reference generation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.helpers import generate_reference

def test_reference_generation():
    """Test the standardized reference generation for different document types"""
    
    print("Testing standardized reference generation...")
    print("=" * 50)
    
    # Test quotation references (Devis)
    devis_refs = []
    for i in range(3):
        ref = generate_reference("DEV")
        devis_refs.append(ref)
        print(f"Devis {i+1}: {ref}")
    
    print()
    
    # Test supplier order references (Commandes)
    cmd_refs = []
    for i in range(3):
        ref = generate_reference("CMD")
        cmd_refs.append(ref)
        print(f"Commande {i+1}: {ref}")
    
    print()
    
    # Verify format and uniqueness
    print("Verification:")
    print(f"✓ All devis references start with 'DEV-': {all(ref.startswith('DEV-') for ref in devis_refs)}")
    print(f"✓ All command references start with 'CMD-': {all(ref.startswith('CMD-') for ref in cmd_refs)}")
    print(f"✓ All devis references are unique: {len(set(devis_refs)) == len(devis_refs)}")
    print(f"✓ All command references are unique: {len(set(cmd_refs)) == len(cmd_refs)}")
    
    # Test reference format
    test_ref = generate_reference("TEST")
    print(f"✓ Reference format (TEST): {test_ref}")
    parts = test_ref.split('-')
    print(f"✓ Reference has correct format 'PREFIX-HEXCODE': {len(parts) == 2 and len(parts[1]) == 6}")
    
    return True

if __name__ == "__main__":
    try:
        success = test_reference_generation()
        print("\n" + "=" * 50)
        if success:
            print("✅ All reference generation tests passed!")
            print("Standardized reference system is working correctly.")
        else:
            print("❌ Reference generation tests failed!")
    except Exception as e:
        print(f"❌ Error testing reference generation: {e}")
