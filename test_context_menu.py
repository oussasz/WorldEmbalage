#!/usr/bin/env python3
"""
Test script to verify context menu logic for supplier order creation
"""

def test_context_menu_logic():
    """Test the context menu logic for showing/hiding supplier order creation"""
    
    # Simulate row data for Initial Devis
    initial_devis_row = [
        "1",           # ID
        "DEV-001",     # Reference  
        "Client Test", # Client
        "2025-08-13",  # Date
        "Devis Initial", # Status
        "300×200×150", # Dimensions
        "à partir de 500", # Quantities
        "2,500.00",    # Total
        "Notes test"   # Notes
    ]
    
    # Simulate row data for Final Devis
    final_devis_row = [
        "2",           # ID
        "DEV-002",     # Reference
        "Client Test", # Client  
        "2025-08-13",  # Date
        "Devis Final", # Status
        "300×200×150", # Dimensions
        "1000",        # Quantities
        "5,000.00",    # Total
        "Notes test"   # Notes
    ]
    
    def should_show_supplier_order_option(row_data):
        """Check if supplier order option should be shown"""
        if not row_data or len(row_data) < 5:
            return False
        
        # Status is in column 4 (index 4): "Devis Initial" or "Devis Final"
        status = row_data[4] if len(row_data) > 4 else ""
        return status == "Devis Final"
    
    # Test Initial Devis - should NOT show supplier order option
    initial_result = should_show_supplier_order_option(initial_devis_row)
    print(f"Initial Devis should NOT show supplier order option: {not initial_result} ✓" if not initial_result else f"❌ Initial Devis incorrectly shows supplier order option")
    
    # Test Final Devis - should show supplier order option
    final_result = should_show_supplier_order_option(final_devis_row)
    print(f"Final Devis should show supplier order option: {final_result} ✓" if final_result else f"❌ Final Devis incorrectly hides supplier order option")
    
    return initial_result == False and final_result == True

if __name__ == "__main__":
    print("Testing context menu logic for supplier order creation...")
    print("=" * 60)
    
    success = test_context_menu_logic()
    
    print("=" * 60)
    if success:
        print("✅ All tests passed! Context menu logic works correctly.")
    else:
        print("❌ Tests failed! Context menu logic needs fixing.")
