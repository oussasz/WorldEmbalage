#!/usr/bin/env python3
"""
Test script to verify estimated quantity functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from models.orders import QuotationLineItem

def test_estimated_quantities():
    """Test that estimated quantities work correctly"""
    
    print("Testing estimated quantity parsing...")
    
    test_cases = [
        ("1000", 1000),
        (">1000", 1000),
        ("more than 500", 500),
        ("environ 2000", 2000),
        ("minimum 1500", 1500),
        ("100-200", 200),  # Should take the last number
        ("between 50 and 100", 100),
        ("", 0),  # Empty should default to 0
        ("no numbers here", 0),  # No numbers should default to 0
    ]
    
    for quantity_str, expected_numeric in test_cases:
        # Create a line item with the test quantity
        line_item = QuotationLineItem(
            quotation_id=1,
            line_number=1,
            quantity=quantity_str
        )
        
        actual_numeric = line_item.numeric_quantity
        
        if actual_numeric == expected_numeric:
            print(f"✅ '{quantity_str}' → {actual_numeric} (correct)")
        else:
            print(f"❌ '{quantity_str}' → {actual_numeric} (expected {expected_numeric})")
    
    print("\nTesting completed!")

if __name__ == "__main__":
    test_estimated_quantities()
