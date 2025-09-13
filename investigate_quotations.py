#!/usr/bin/env python3
"""
Investigate the current quotation data structure
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.database import SessionLocal
from models.orders import Quotation, QuotationLineItem, ClientOrder
from models.clients import Client

def investigate_quotations():
    """Investigate what quotations exist in the database."""
    print("🔍 Investigating Quotation Data")
    print("=" * 50)
    
    session = SessionLocal()
    try:
        # Check quotations
        quotations = session.query(Quotation).all()
        print(f"📋 Found {len(quotations)} quotations")
        
        for q in quotations:
            print(f"\n🔸 Quotation ID: {q.id}")
            print(f"   Reference: {q.reference}")
            print(f"   Client ID: {q.client_id}")
            if q.client:
                print(f"   Client Name: {q.client.name}")
            print(f"   Issue Date: {q.issue_date}")
            print(f"   Valid Until: {q.valid_until}")
            
            # Check line items
            line_items = session.query(QuotationLineItem).filter(
                QuotationLineItem.quotation_id == q.id
            ).all()
            print(f"   Line Items: {len(line_items)}")
            
            for li in line_items:
                print(f"      - ID: {li.id}")
                print(f"        Description: '{li.description}'")
                print(f"        Quantity: {li.quantity}")
                print(f"        Unit Price: {li.unit_price}")
        
        # Check client orders and their quotation links
        print(f"\n📦 Checking Client Orders and Quotation Links")
        client_orders = session.query(ClientOrder).all()
        print(f"Found {len(client_orders)} client orders")
        
        for co in client_orders:
            print(f"\n🔸 Client Order ID: {co.id}")
            print(f"   Reference: {co.reference}")
            print(f"   Client ID: {co.client_id}")
            if co.client:
                print(f"   Client Name: {co.client.name}")
            print(f"   Quotation ID: {co.quotation_id}")
            
            if co.quotation:
                print(f"   Linked Quotation Reference: {co.quotation.reference}")
                if co.quotation.line_items:
                    for li in co.quotation.line_items:
                        print(f"      - Description: '{li.description}'")
            else:
                print(f"   ⚠️  No quotation linked")
        
        # Check clients
        print(f"\n👥 Checking Clients")
        clients = session.query(Client).all()
        for client in clients:
            print(f"🔸 Client ID: {client.id}, Name: '{client.name}'")
            
            # Find quotations for this client
            client_quotations = session.query(Quotation).filter(
                Quotation.client_id == client.id
            ).all()
            print(f"   Quotations: {len(client_quotations)}")
            
            for q in client_quotations:
                print(f"      - {q.reference}: {len(q.line_items)} line items")
                
    except Exception as e:
        print(f"❌ Error during investigation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    investigate_quotations()
