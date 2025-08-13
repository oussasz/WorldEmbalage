#!/usr/bin/env python3
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

try:
    from config.database import SessionLocal
    from models.orders import SupplierOrder, SupplierOrderStatus
    from models.suppliers import Supplier  # Import Supplier to resolve relationship
    
    print("Testing SQLAlchemy enum loading...")
    
    session = SessionLocal()
    try:
        # Try to query supplier orders
        supplier_orders = session.query(SupplierOrder).all()
        print(f"Found {len(supplier_orders)} supplier orders")
        
        for order in supplier_orders:
            print(f"Order {order.id}: {order.reference} - Status: {order.status} (type: {type(order.status)})")
            print(f"  Status value: {order.status.value if hasattr(order.status, 'value') else 'N/A'}")
            
    except Exception as e:
        print(f"Error loading supplier orders: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
        
    # Test enum values
    print("\nEnum values:")
    for status in SupplierOrderStatus:
        print(f"  {status.name} = '{status.value}'")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
