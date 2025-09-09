#!/usr/bin/env python3
"""
Test script to verify supplier order status logic.
This script simulates the order status calculation to ensure it works correctly.
"""

import sys
sys.path.append('src')

from models.orders import SupplierOrderStatus, DeliveryStatus

def test_supplier_order_status_logic():
    """Test the supplier order status calculation logic"""
    
    print("=== Testing Supplier Order Status Logic ===\n")
    
    # Test Case 1: All line items complete
    print("Test Case 1: All line items complete")
    line_items = [
        {'total_received_quantity': 100, 'quantity': 100},  # Complete
        {'total_received_quantity': 50, 'quantity': 50},    # Complete
        {'total_received_quantity': 25, 'quantity': 25},    # Complete
    ]
    
    total_line_items = len(line_items)
    completed_line_items = 0
    partially_received_line_items = 0
    
    for line_item in line_items:
        received_qty = line_item['total_received_quantity']
        ordered_qty = line_item['quantity']
        
        if received_qty >= ordered_qty:
            completed_line_items += 1
        elif received_qty > 0:
            partially_received_line_items += 1
    
    if completed_line_items == total_line_items:
        status = SupplierOrderStatus.COMPLETED
    elif completed_line_items > 0 or partially_received_line_items > 0:
        status = SupplierOrderStatus.PARTIALLY_DELIVERED
    else:
        status = "ORDERED (no status change)"
    
    print(f"  Line items: {completed_line_items}/{total_line_items} complete, {partially_received_line_items} partial")
    print(f"  Expected: COMPLETED, Got: {status}")
    print(f"  ✅ Correct!" if status == SupplierOrderStatus.COMPLETED else "❌ Wrong!")
    print()
    
    # Test Case 2: Some line items complete, some partial
    print("Test Case 2: Some line items complete, some partial")
    line_items = [
        {'total_received_quantity': 100, 'quantity': 100},  # Complete
        {'total_received_quantity': 30, 'quantity': 50},    # Partial
        {'total_received_quantity': 25, 'quantity': 25},    # Complete
    ]
    
    total_line_items = len(line_items)
    completed_line_items = 0
    partially_received_line_items = 0
    
    for line_item in line_items:
        received_qty = line_item['total_received_quantity']
        ordered_qty = line_item['quantity']
        
        if received_qty >= ordered_qty:
            completed_line_items += 1
        elif received_qty > 0:
            partially_received_line_items += 1
    
    if completed_line_items == total_line_items:
        status = SupplierOrderStatus.COMPLETED
    elif completed_line_items > 0 or partially_received_line_items > 0:
        status = SupplierOrderStatus.PARTIALLY_DELIVERED
    else:
        status = "ORDERED (no status change)"
    
    print(f"  Line items: {completed_line_items}/{total_line_items} complete, {partially_received_line_items} partial")
    print(f"  Expected: PARTIALLY_DELIVERED, Got: {status}")
    print(f"  ✅ Correct!" if status == SupplierOrderStatus.PARTIALLY_DELIVERED else "❌ Wrong!")
    print()
    
    # Test Case 3: Some line items complete, some untouched
    print("Test Case 3: Some line items complete, some untouched")
    line_items = [
        {'total_received_quantity': 100, 'quantity': 100},  # Complete
        {'total_received_quantity': 0, 'quantity': 50},     # Not received
        {'total_received_quantity': 25, 'quantity': 25},    # Complete
    ]
    
    total_line_items = len(line_items)
    completed_line_items = 0
    partially_received_line_items = 0
    
    for line_item in line_items:
        received_qty = line_item['total_received_quantity']
        ordered_qty = line_item['quantity']
        
        if received_qty >= ordered_qty:
            completed_line_items += 1
        elif received_qty > 0:
            partially_received_line_items += 1
    
    if completed_line_items == total_line_items:
        status = SupplierOrderStatus.COMPLETED
    elif completed_line_items > 0 or partially_received_line_items > 0:
        status = SupplierOrderStatus.PARTIALLY_DELIVERED
    else:
        status = "ORDERED (no status change)"
    
    print(f"  Line items: {completed_line_items}/{total_line_items} complete, {partially_received_line_items} partial")
    print(f"  Expected: PARTIALLY_DELIVERED, Got: {status}")
    print(f"  ✅ Correct!" if status == SupplierOrderStatus.PARTIALLY_DELIVERED else "❌ Wrong!")
    print()
    
    # Test Case 4: All line items untouched
    print("Test Case 4: All line items untouched")
    line_items = [
        {'total_received_quantity': 0, 'quantity': 100},  # Not received
        {'total_received_quantity': 0, 'quantity': 50},   # Not received
        {'total_received_quantity': 0, 'quantity': 25},   # Not received
    ]
    
    total_line_items = len(line_items)
    completed_line_items = 0
    partially_received_line_items = 0
    
    for line_item in line_items:
        received_qty = line_item['total_received_quantity']
        ordered_qty = line_item['quantity']
        
        if received_qty >= ordered_qty:
            completed_line_items += 1
        elif received_qty > 0:
            partially_received_line_items += 1
    
    if completed_line_items == total_line_items:
        status = SupplierOrderStatus.COMPLETED
    elif completed_line_items > 0 or partially_received_line_items > 0:
        status = SupplierOrderStatus.PARTIALLY_DELIVERED
    else:
        status = "ORDERED (no status change)"
    
    print(f"  Line items: {completed_line_items}/{total_line_items} complete, {partially_received_line_items} partial")
    print(f"  Expected: ORDERED (no status change), Got: {status}")
    print(f"  ✅ Correct!" if status == "ORDERED (no status change)" else "❌ Wrong!")
    print()
    
    # Test Case 5: Edge case - One item complete, rest untouched (THIS SHOULD NOT BE COMPLETED!)
    print("Test Case 5: Edge case - Only one item complete, rest untouched")
    line_items = [
        {'total_received_quantity': 100, 'quantity': 100},  # Complete
        {'total_received_quantity': 0, 'quantity': 50},     # Not received
        {'total_received_quantity': 0, 'quantity': 25},     # Not received
    ]
    
    total_line_items = len(line_items)
    completed_line_items = 0
    partially_received_line_items = 0
    
    for line_item in line_items:
        received_qty = line_item['total_received_quantity']
        ordered_qty = line_item['quantity']
        
        if received_qty >= ordered_qty:
            completed_line_items += 1
        elif received_qty > 0:
            partially_received_line_items += 1
    
    if completed_line_items == total_line_items:
        status = SupplierOrderStatus.COMPLETED
    elif completed_line_items > 0 or partially_received_line_items > 0:
        status = SupplierOrderStatus.PARTIALLY_DELIVERED
    else:
        status = "ORDERED (no status change)"
    
    print(f"  Line items: {completed_line_items}/{total_line_items} complete, {partially_received_line_items} partial")
    print(f"  Expected: PARTIALLY_DELIVERED (NOT COMPLETED!), Got: {status}")
    print(f"  ✅ Correct!" if status == SupplierOrderStatus.PARTIALLY_DELIVERED else "❌ Wrong!")
    print()

if __name__ == "__main__":
    test_supplier_order_status_logic()
    print("=== Test completed ===")
