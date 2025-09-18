#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.database import SessionLocal
from models import Quotation, QuotationLineItem, ClientOrder, Reception, SupplierOrder, ProductionBatch

def debug_descriptions():
    """Debug description loading to see what's happening."""
    session = SessionLocal()
    try:
        print("=== QUOTATIONS WITH DESCRIPTIONS ===")
        quotations = session.query(Quotation).all()
        for q in quotations:
            print(f"Quotation {q.id}: notes='{q.notes}', client={q.client.name if q.client else 'None'}")
            if q.line_items:
                for i, line in enumerate(q.line_items):
                    print(f"  Line {i+1}: description='{line.description}', cardboard='{line.cardboard_type}'")
            else:
                print(f"  No line items")
            print()
        
        print("=== RECEPTIONS AND THEIR SUPPLIER ORDER CONNECTIONS ===")
        receptions = session.query(Reception).all()
        for r in receptions:
            print(f"Reception {r.id}: quantity={r.quantity}")
            if r.supplier_order:
                print(f"  Supplier Order {r.supplier_order.id}: supplier={r.supplier_order.supplier.name if r.supplier_order.supplier else 'None'}")
                if hasattr(r.supplier_order, 'line_items') and r.supplier_order.line_items:
                    print(f"  Supplier order has {len(r.supplier_order.line_items)} line items")
                    for i, line in enumerate(r.supplier_order.line_items):
                        if hasattr(line, 'client') and line.client:
                            print(f"    Line {i+1}: client={line.client.name}")
                        else:
                            print(f"    Line {i+1}: no client")
                else:
                    print(f"  Supplier order has no line items")
            else:
                print(f"  No supplier order")
            print()
            
        print("=== CLIENT ORDERS AND QUOTATION LINKS ===")
        client_orders = session.query(ClientOrder).all()
        for co in client_orders:
            print(f"ClientOrder {co.id}: client={co.client.name if co.client else 'None'}, supplier_order_id={co.supplier_order_id}")
            if co.quotation_id:
                print(f"  Has quotation_id: {co.quotation_id}")
                quotation = session.query(Quotation).filter(Quotation.id == co.quotation_id).first()
                if quotation:
                    print(f"  Quotation found: notes='{quotation.notes}'")
                    if quotation.line_items:
                        for line in quotation.line_items:
                            print(f"    Line description: '{line.description}'")
                else:
                    print(f"  Quotation NOT FOUND!")
            else:
                print(f"  No quotation_id")
            print()
            
        print("=== PRODUCTION BATCHES AND THEIR CONNECTIONS ===")
        production_batches = session.query(ProductionBatch).all()
        for pb in production_batches:
            print(f"ProductionBatch {pb.id}: quantity={pb.quantity}")
            if pb.client_order_id:
                print(f"  Has client_order_id: {pb.client_order_id}")
                client_order = session.query(ClientOrder).filter(ClientOrder.id == pb.client_order_id).first()
                if client_order:
                    print(f"  ClientOrder found: client={client_order.client.name if client_order.client else 'None'}")
                    if client_order.quotation_id:
                        quotation = session.query(Quotation).filter(Quotation.id == client_order.quotation_id).first()
                        if quotation:
                            print(f"    Quotation found: notes='{quotation.notes}'")
                            if quotation.line_items:
                                for line in quotation.line_items:
                                    print(f"      Line description: '{line.description}'")
                        else:
                            print(f"    Quotation NOT FOUND!")
                    else:
                        print(f"    No quotation_id in client order")
                else:
                    print(f"  ClientOrder NOT FOUND!")
            else:
                print(f"  No client_order_id")
            print()
            
    finally:
        session.close()

if __name__ == "__main__":
    debug_descriptions()