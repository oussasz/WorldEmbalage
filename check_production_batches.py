#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.database import SessionLocal
from models import ProductionBatch

def check_production_batches():
    """Check all production batches to see which ones are included/excluded."""
    session = SessionLocal()
    try:
        print("=== ALL PRODUCTION BATCHES ===")
        all_batches = session.query(ProductionBatch).all()
        for pb in all_batches:
            print(f"ProductionBatch {pb.id}:")
            print(f"  batch_code: '{pb.batch_code}'")
            print(f"  quantity: {pb.quantity}")
            print(f"  client_order_id: {pb.client_order_id}")
            
            # Check if it would be filtered by archive filter
            archived = pb.batch_code and pb.batch_code.startswith('[ARCHIVED]')
            print(f"  Would be filtered (archived): {archived}")
            print()
        
        print("=== PRODUCTION BATCHES AFTER ARCHIVE FILTER ===")
        filtered_batches = session.query(ProductionBatch).filter(
            ~ProductionBatch.batch_code.like('[ARCHIVED]%')
        ).all()
        for pb in filtered_batches:
            print(f"ProductionBatch {pb.id}: batch_code='{pb.batch_code}', client_order_id={pb.client_order_id}")
            
    finally:
        session.close()

if __name__ == "__main__":
    check_production_batches()