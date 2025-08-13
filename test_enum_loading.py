#!/usr/bin/env python3
"""
Test script to debug SQLAlchemy enum loading issue
"""
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

def test_enum_loading():
    try:
        print("=== Testing Enum Loading ===")
        
        # Test enum import
        from models.orders import SupplierOrderStatus, SupplierOrder
        print(f"✓ Successfully imported SupplierOrderStatus enum")
        print(f"  Available values: {[e.value for e in SupplierOrderStatus]}")
        print(f"  Available names: {[e.name for e in SupplierOrderStatus]}")
        
        # Test database connection
        from config.database import SessionLocal
        from sqlalchemy import text
        print(f"✓ Successfully imported database connection")
        
        session = SessionLocal()
        try:
            # Check what's actually in the database
            result = session.execute(text("SELECT id, reference, status FROM supplier_orders LIMIT 5"))
            print(f"\n=== Database Records ===")
            records = result.fetchall()
            if records:
                for record in records:
                    print(f"  ID: {record[0]}, Ref: {record[1]}, Status: '{record[2]}'")
            else:
                print("  No records found")
            
            # Try to load a SupplierOrder object
            print(f"\n=== Testing SQLAlchemy ORM Loading ===")
            try:
                supplier_orders = session.query(SupplierOrder).limit(3).all()
                print(f"✓ Successfully loaded {len(supplier_orders)} supplier orders")
                
                for order in supplier_orders:
                    print(f"  Order ID: {order.id}, Status: {order.status} ({type(order.status)})")
                    if hasattr(order.status, 'value'):
                        print(f"    Status value: '{order.status.value}'")
                        
            except Exception as e:
                print(f"✗ Error loading SupplierOrder objects: {e}")
                import traceback
                traceback.print_exc()
                
        finally:
            session.close()
            
    except Exception as e:
        print(f"✗ Error in test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_enum_loading()
