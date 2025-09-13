#!/usr/bin/env python3
"""
Test script to demonstrate the new quantity addition workflow
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.database import SessionLocal
from models.production import ProductionBatch
from models.orders import ClientOrder

def test_quantity_addition_workflow():
    """Test the new quantity addition workflow"""
    print("🔍 Testing New Quantity Addition Workflow")
    print("=" * 55)
    
    session = SessionLocal()
    try:
        # Show current production batches
        batches = session.query(ProductionBatch).all()
        print(f"\n📦 Current Production Batches ({len(batches)} total):")
        
        for batch in batches:
            client_order = session.query(ClientOrder).filter(
                ClientOrder.id == batch.client_order_id
            ).first()
            
            print(f"  🔸 Batch ID: {batch.id}")
            print(f"     Code: {batch.batch_code}")
            print(f"     Quantity: {batch.quantity}")
            print(f"     Client Order ID: {batch.client_order_id}")
            if client_order and client_order.client:
                print(f"     Client: {client_order.client.name}")
            print()
        
        # Show how the new workflow will work
        print("🔄 New Workflow Logic:")
        print("=" * 25)
        print("1. When adding finished product:")
        print("   ✅ Check if production batch with same client_order_id exists")
        print("   ✅ If EXISTS: Add quantity to existing batch")
        print("   ✅ If NOT EXISTS: Create new batch")
        print()
        print("2. This ensures:")
        print("   ✅ Same client + same dimensions + same description = ONE lot")
        print("   ✅ No need for grouping afterward")
        print("   ✅ Simpler workflow")
        print()
        
        # Group by client_order_id to show which would be combined
        from collections import defaultdict
        batches_by_client_order = defaultdict(list)
        
        for batch in batches:
            batches_by_client_order[batch.client_order_id].append(batch)
        
        print("📊 Current Batches Grouped by Client Order:")
        for client_order_id, batch_list in batches_by_client_order.items():
            client_order = session.query(ClientOrder).filter(
                ClientOrder.id == client_order_id
            ).first()
            
            total_quantity = sum(b.quantity for b in batch_list)
            client_name = client_order.client.name if client_order and client_order.client else "Unknown"
            
            print(f"  🔸 Client Order {client_order_id} ({client_name}):")
            print(f"     Batches: {len(batch_list)}")
            print(f"     Total Quantity: {total_quantity}")
            
            if len(batch_list) > 1:
                print(f"     ⚠️  Multiple batches - would be combined in new workflow")
                for b in batch_list:
                    print(f"        - {b.batch_code}: {b.quantity}")
            else:
                print(f"     ✅ Single batch: {batch_list[0].batch_code}")
            print()
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_quantity_addition_workflow()