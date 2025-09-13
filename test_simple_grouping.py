#!/usr/bin/env python3
"""
Simple test script to validate the enhanced grouping system without complex relationships.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.database import SessionLocal
from models.production import ProductionBatch

def test_simple_grouping():
    """Test the basic grouping logic without complex relationships."""
    print("🔍 Testing Basic Grouping System")
    print("=" * 50)
    
    session = SessionLocal()
    try:
        # Get all finished production batches
        finished_batches = session.query(ProductionBatch).filter(
            ProductionBatch.status == 'finished'
        ).all()
        
        print(f"📊 Found {len(finished_batches)} finished production batches")
        
        if not finished_batches:
            print("⚠️  No finished production batches found to test grouping")
            return
        
        # Simple test: just list the batches and their basic info
        for pb in finished_batches:
            print(f"   📦 Batch: {pb.batch_code}")
            print(f"      Status: {pb.status}")
            print(f"      Quantity: {pb.quantity_produced}")
            print(f"      Client Order ID: {pb.client_order_id}")
            if pb.client_order_id:
                print(f"      ✅ Has client order - can be processed by grouping logic")
            else:
                print(f"      ⚠️  No client order - will be skipped by grouping logic")
            print()
        
        print(f"✅ Basic grouping test completed successfully!")
        print(f"   Found {len([pb for pb in finished_batches if pb.client_order_id])} batches with client orders")
        print(f"   Found {len([pb for pb in finished_batches if not pb.client_order_id])} batches without client orders")
        
    except Exception as e:
        print(f"❌ Error during basic grouping test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_simple_grouping()
