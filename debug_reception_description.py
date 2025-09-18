#!/usr/bin/env python3
"""
Debug script to understand why Reception descriptions are showing N/A
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.database import SessionLocal
from models.orders import Reception, SupplierOrder, ClientOrder, Quotation

def debug_reception_descriptions():
    """Debug the most recent Reception records and their description sources"""
    session = SessionLocal()
    try:
        # Get the most recent Reception records
        recent_receptions = session.query(Reception).order_by(Reception.id.desc()).limit(5).all()
        
        print("=== RECENT RECEPTION RECORDS ===")
        for reception in recent_receptions:
            print(f"\nReception ID: {reception.id}")
            print(f"Supplier Order ID: {reception.supplier_order_id}")
            print(f"Quantity: {reception.quantity}")
            print(f"Notes: {reception.notes}")
            print(f"Date: {reception.reception_date}")
            
            # Check the supplier order
            if reception.supplier_order_id:
                supplier_order = session.query(SupplierOrder).filter(
                    SupplierOrder.id == reception.supplier_order_id
                ).first()
                
                if supplier_order:
                    print(f"  Supplier Order found: {supplier_order.id}")
                    print(f"  Line items count: {len(supplier_order.line_items) if supplier_order.line_items else 0}")
                    
                    if supplier_order.line_items:
                        first_line_item = supplier_order.line_items[0]
                        print(f"  First line item client_id: {getattr(first_line_item, 'client_id', 'N/A')}")
                        
                        # Check for client orders
                        if hasattr(first_line_item, 'client_id') and first_line_item.client_id:
                            client_orders = session.query(ClientOrder).filter(
                                ClientOrder.client_id == first_line_item.client_id,
                                ClientOrder.supplier_order_id == supplier_order.id
                            ).all()
                            
                            print(f"  Client orders found: {len(client_orders)}")
                            
                            for co in client_orders:
                                print(f"    Client Order ID: {co.id}")
                                print(f"    Quotation ID: {co.quotation_id}")
                                
                                if co.quotation:
                                    quotation = co.quotation
                                    print(f"    Quotation notes: {quotation.notes}")
                                    print(f"    Quotation line items: {len(quotation.line_items) if quotation.line_items else 0}")
                                    
                                    if quotation.line_items:
                                        for idx, line_item in enumerate(quotation.line_items):
                                            print(f"      Line {idx+1} description: {line_item.description}")
                else:
                    print(f"  No supplier order found for ID: {reception.supplier_order_id}")
            else:
                print("  No supplier order ID in reception")
        
        print("\n=== SUPPLIER ORDERS WITH CLIENT RELATIONSHIPS ===")
        # Check supplier orders that have client relationships
        supplier_orders = session.query(SupplierOrder).order_by(SupplierOrder.id.desc()).limit(3).all()
        
        for so in supplier_orders:
            print(f"\nSupplier Order ID: {so.id}")
            print(f"Status: {so.status.value if so.status else 'None'}")
            
            # Check client orders pointing to this supplier order
            client_orders = session.query(ClientOrder).filter(
                ClientOrder.supplier_order_id == so.id
            ).all()
            
            print(f"Client orders referencing this supplier order: {len(client_orders)}")
            
            for co in client_orders:
                print(f"  Client Order ID: {co.id}, Client ID: {co.client_id}")
                if co.quotation:
                    print(f"    Quotation ID: {co.quotation_id}")
                    print(f"    Quotation notes: {co.quotation.notes}")
                    if co.quotation.line_items:
                        for idx, line_item in enumerate(co.quotation.line_items):
                            print(f"      Line {idx+1}: {line_item.description}")
                            
    except Exception as e:
        print(f"Error during debugging: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    debug_reception_descriptions()