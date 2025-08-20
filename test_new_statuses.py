#!/usr/bin/env python3
"""
Test script to demonstrate the new supplier order statuses
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.database import SessionLocal
from models.orders import SupplierOrder, SupplierOrderStatus

def test_new_statuses():
    """Test the new supplier order statuses"""
    session = SessionLocal()
    
    try:
        # Get all supplier orders
        orders = session.query(SupplierOrder).all()
        
        print("=== Testing New Supplier Order Statuses ===\n")
        
        if not orders:
            print("No supplier orders found in database")
            return
            
        for order in orders:
            print(f"Order ID: {order.id}")
            print(f"Reference: {getattr(order, 'bon_commande_ref', getattr(order, 'reference', 'N/A'))}")
            print(f"Current Status: {order.status.value if order.status else 'N/A'}")
            print(f"Supplier: {order.supplier.name if order.supplier else 'N/A'}")
            
            # Test changing to new statuses
            original_status = order.status
            
            # Test Partially Delivered
            print(f"\n  ✅ Testing: Changing to 'PARTIALLY_DELIVERED'")
            order.status = SupplierOrderStatus.PARTIALLY_DELIVERED
            session.commit()
            print(f"  Status changed to: {order.status.value}")
            
            # Test Completed
            print(f"  ✅ Testing: Changing to 'COMPLETED'")
            order.status = SupplierOrderStatus.COMPLETED
            session.commit()
            print(f"  Status changed to: {order.status.value}")
            
            # Restore original status
            print(f"  🔄 Restoring original status: {original_status.value if original_status else 'N/A'}")
            order.status = original_status
            session.commit()
            
            print("-" * 50)
            
        print("\n✅ All status tests completed successfully!")
        print("\nAvailable statuses:")
        for status in SupplierOrderStatus:
            print(f"  - {status.name}: {status.value}")
            
    except Exception as e:
        print(f"❌ Error testing statuses: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    test_new_statuses()
