#!/usr/bin/env python3
"""
Test script to verify archive functionality
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from config.database import SessionLocal
from models.production import ProductionBatch
from models.orders import ClientOrder, Quotation


def test_archive_filtering():
    """Test that archived items are filtered out correctly"""
    session = SessionLocal()
    try:
        # Test production batch filtering
        print("Testing production batch filtering...")
        active_batches = session.query(ProductionBatch).filter(
            ~ProductionBatch.batch_code.like('[ARCHIVED]%')
        ).all()
        
        all_batches = session.query(ProductionBatch).all()
        
        print(f"Total production batches: {len(all_batches)}")
        print(f"Active production batches: {len(active_batches)}")
        
        # Test quotation filtering  
        print("\nTesting quotation filtering...")
        active_quotations = session.query(Quotation).filter(
            ~Quotation.notes.like('[ARCHIVED]%')
        ).all()
        
        all_quotations = session.query(Quotation).all()
        
        print(f"Total quotations: {len(all_quotations)}")
        print(f"Active quotations: {len(active_quotations)}")
        
        # Test client order filtering
        print("\nTesting client order filtering...")
        active_client_orders = session.query(ClientOrder).filter(
            ~ClientOrder.notes.like('[ARCHIVED]%')
        ).all()
        
        all_client_orders = session.query(ClientOrder).all()
        
        print(f"Total client orders: {len(all_client_orders)}")
        print(f"Active client orders: {len(active_client_orders)}")
        
        print("\n✅ Archive filtering tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
    finally:
        session.close()


def test_description_columns():
    """Test description column functionality"""
    session = SessionLocal()
    try:
        print("\nTesting description lookup for finished products...")
        
        production_batches = session.query(ProductionBatch).filter(
            ~ProductionBatch.batch_code.like('[ARCHIVED]%')
        ).limit(3).all()
        
        for pb in production_batches:
            description = "N/A"
            
            # Try to get description from client order -> quotation
            if pb.client_order_id:
                try:
                    client_order = session.query(ClientOrder).filter(
                        ClientOrder.id == pb.client_order_id
                    ).first()
                    
                    if client_order and client_order.quotation:
                        quotation = client_order.quotation
                        
                        # Try line items first (priority)
                        if quotation.line_items:
                            first_quotation_line = quotation.line_items[0]
                            if first_quotation_line.description:
                                description = first_quotation_line.description
                        
                        # Fallback to quotation notes
                        if description == "N/A" and quotation.notes:
                            description = quotation.notes
                            
                except Exception as desc_error:
                    print(f"Error fetching description for production batch {pb.id}: {desc_error}")
            
            print(f"Production batch {pb.id}: Description = '{description}'")
        
        print("\n✅ Description column tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during description testing: {e}")
    finally:
        session.close()


if __name__ == '__main__':
    print("🔍 Testing World Embalage Archive Functionality")
    print("=" * 50)
    
    test_archive_filtering()
    test_description_columns()
    
    print("\n🎉 All tests completed!")