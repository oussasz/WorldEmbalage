#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.database import SessionLocal
from models import Quotation, QuotationLineItem, ClientOrder, Reception, SupplierOrder, ProductionBatch

def test_description_loading():
    """Test the exact same logic used in main_window.py for loading descriptions."""
    session = SessionLocal()
    try:
        print("=== TESTING RAW MATERIALS DESCRIPTION LOGIC ===")
        
        # Test Reception 1 (which should connect to ENAD and the quotation)
        reception = session.query(Reception).filter(Reception.id == 1).first()
        if reception and reception.supplier_order:
            supplier_order = reception.supplier_order
            print(f"Reception 1 -> Supplier Order {supplier_order.id}")
            
            if hasattr(supplier_order, 'line_items') and supplier_order.line_items:
                first_line_item = supplier_order.line_items[0]
                print(f"First line item has client_id: {getattr(first_line_item, 'client_id', 'MISSING')}")
                
                if hasattr(first_line_item, 'client_id') and first_line_item.client_id:
                    # Strategy 1: Try to find client order with matching supplier_order_id
                    client_order = session.query(ClientOrder).filter(
                        ClientOrder.client_id == first_line_item.client_id,
                        ClientOrder.supplier_order_id == supplier_order.id
                    ).first()
                    
                    print(f"Strategy 1 (exact match): {client_order}")
                    
                    # Strategy 2: If no direct link, find ANY client order for this client with a quotation
                    if not client_order:
                        client_order = session.query(ClientOrder).filter(
                            ClientOrder.client_id == first_line_item.client_id,
                            ClientOrder.quotation_id.isnot(None)
                        ).first()
                        print(f"Strategy 2 (any with quotation): {client_order}")
                    
                    if client_order and client_order.quotation:
                        quotation = client_order.quotation
                        print(f"Found quotation {quotation.id} with notes: '{quotation.notes}'")
                        
                        description = "N/A"
                        
                        # Try line items first (priority)
                        if quotation.line_items:
                            first_quotation_line = quotation.line_items[0]
                            if first_quotation_line.description:
                                description = first_quotation_line.description
                                print(f"Got description from line item: '{description}'")
                        
                        # Fallback to quotation notes
                        if description == "N/A" and quotation.notes:
                            notes = quotation.notes
                            if notes.startswith('[ARCHIVED]'):
                                description = f"[Archived] {notes[10:].strip()}" if len(notes) > 10 else notes
                            else:
                                description = notes
                            print(f"Got description from notes: '{description}'")
                        
                        print(f"FINAL DESCRIPTION: '{description}'")
                    else:
                        print("No client order with quotation found")
                else:
                    print("No client_id in line item")
            else:
                print("No line items in supplier order")
        else:
            print("No reception or supplier order found")
            
        print("\n=== TESTING FINISHED PRODUCTS DESCRIPTION LOGIC ===")
        
        # Test Production Batch 1 (which should connect to ENAD and the quotation)
        pb = session.query(ProductionBatch).filter(ProductionBatch.id == 1).first()
        if pb and pb.client_order_id:
            print(f"Production Batch 1 -> Client Order {pb.client_order_id}")
            
            client_order = session.query(ClientOrder).filter(
                ClientOrder.id == pb.client_order_id
            ).first()
            
            if client_order and client_order.quotation:
                quotation = client_order.quotation
                print(f"Found quotation {quotation.id} with notes: '{quotation.notes}'")
                
                description = "N/A"
                
                # Try line items first (priority)
                if quotation.line_items:
                    first_quotation_line = quotation.line_items[0]
                    if first_quotation_line.description and first_quotation_line.description.strip():
                        description = first_quotation_line.description.strip()
                        print(f"Got description from line item: '{description}'")
                
                # Fallback to quotation notes
                if description == "N/A" and quotation.notes and quotation.notes.strip():
                    notes = quotation.notes.strip()
                    if notes.startswith('[ARCHIVED]'):
                        description = f"[Archived] {notes[10:].strip()}" if len(notes) > 10 else notes
                    else:
                        description = notes
                    print(f"Got description from notes: '{description}'")
                
                print(f"FINAL DESCRIPTION: '{description}'")
            else:
                print("No client order with quotation found")
        else:
            print("No production batch or client_order_id found")
            
    finally:
        session.close()

if __name__ == "__main__":
    test_description_loading()