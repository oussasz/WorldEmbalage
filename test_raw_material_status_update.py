#!/usr/bin/env python3
"""
Test script to verify raw material arrival status updates
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.database import SessionLocal
from models.orders import SupplierOrder, SupplierOrderLineItem, SupplierOrderStatus, MaterialDelivery, DeliveryStatus

def test_status_updates():
    """Test the supplier order status update logic"""
    session = SessionLocal()
    
    try:
        print("=== Testing Supplier Order Status Updates ===\n")
        
        # Get all supplier orders with line items
        orders = session.query(SupplierOrder).all()
        
        if not orders:
            print("No supplier orders found in database")
            return
            
        for order in orders:
            print(f"Order ID: {order.id}")
            print(f"Reference: {getattr(order, 'bon_commande_ref', getattr(order, 'reference', 'N/A'))}")
            print(f"Current Status: {order.status.value if order.status else 'N/A'}")
            print(f"Supplier: {order.supplier.name if order.supplier else 'N/A'}")
            print(f"Line Items: {len(order.line_items) if order.line_items else 0}")
            
            if order.line_items:
                for i, line_item in enumerate(order.line_items, 1):
                    received_qty = getattr(line_item, 'total_received_quantity', 0) or 0
                    ordered_qty = line_item.quantity
                    status = getattr(line_item, 'delivery_status', 'N/A')
                    remaining = max(0, ordered_qty - received_qty)
                    
                    print(f"  Line Item {i}:")
                    print(f"    Dimensions: {line_item.plaque_width_mm}×{line_item.plaque_length_mm}×{line_item.plaque_flap_mm}mm")
                    print(f"    Ordered: {ordered_qty}, Received: {received_qty}, Remaining: {remaining}")
                    print(f"    Status: {status.value if hasattr(status, 'value') else status}")
                    
                    # Check deliveries for this line item
                    deliveries = session.query(MaterialDelivery).filter(
                        MaterialDelivery.supplier_order_line_item_id == line_item.id
                    ).all()
                    
                    if deliveries:
                        print(f"    Deliveries ({len(deliveries)}):")
                        for delivery in deliveries:
                            print(f"      - {delivery.received_quantity} @ {delivery.batch_reference}")
                    else:
                        print(f"    No deliveries recorded")
            
            print("-" * 60)
            
        print("\n✅ Status update test completed!")
        
        # Show available statuses
        print("\nAvailable supplier order statuses:")
        for status in SupplierOrderStatus:
            print(f"  - {status.name}: {status.value}")
            
    except Exception as e:
        print(f"❌ Error testing status updates: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    test_status_updates()
