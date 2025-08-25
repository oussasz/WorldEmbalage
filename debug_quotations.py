#!/usr/bin/env python3
"""
Diagnostic script to check quotation is_initial values
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.database import SessionLocal
from models.orders import Quotation, ClientOrder
from models.suppliers import Supplier  # Add missing import
from models.clients import Client  # Add missing import
from models.plaques import Plaque  # Add missing import

def debug_quotations():
    """Debug quotation is_initial values"""
    session = SessionLocal()
    
    try:
        print("=== Debugging Quotation is_initial Values ===\n")
        
        # Get all quotations
        quotations = session.query(Quotation).all()
        
        if not quotations:
            print("No quotations found in database")
            return
            
        for q in quotations:
            print(f"Quotation ID: {q.id}")
            print(f"Reference: {q.reference}")
            print(f"is_initial (raw): {repr(q.is_initial)}")
            print(f"is_initial (bool): {bool(q.is_initial)}")
            print(f"Type: {type(q.is_initial)}")
            print(f"getattr(q, 'is_initial', True): {getattr(q, 'is_initial', True)}")
            print(f"getattr(q, 'is_initial', False): {getattr(q, 'is_initial', False)}")
            
            # Check if this quotation has associated client orders
            client_orders = session.query(ClientOrder).filter(ClientOrder.quotation_id == q.id).all()
            print(f"Associated Client Orders: {len(client_orders)}")
            
            if client_orders:
                for co in client_orders:
                    print(f"  - Client Order {co.id}: {co.reference}")
                    print(f"    Quotation via relationship: {co.quotation.reference if co.quotation else 'None'}")
                    print(f"    Quotation is_initial via relationship: {repr(co.quotation.is_initial) if co.quotation else 'None'}")
            
            print("-" * 50)
            
        print(f"\n✅ Found {len(quotations)} quotations")
        
        # Show initial vs final count
        initial_count = sum(1 for q in quotations if q.is_initial)
        final_count = sum(1 for q in quotations if not q.is_initial)
        print(f"Initial quotations: {initial_count}")
        print(f"Final quotations: {final_count}")
        
    except Exception as e:
        print(f"❌ Error debugging quotations: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    debug_quotations()
