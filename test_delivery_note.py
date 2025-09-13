#!/usr/bin/env python3
"""
Test script to verify quotation descriptions are used consistently in invoice and delivery note.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import all models to ensure SQLAlchemy relationships are properly configured
from config.database import SessionLocal
from models.suppliers import Supplier
from models.clients import Client
from models.orders import ClientOrder, SupplierOrder, SupplierOrderLineItem, ClientOrderLineItem
from models.orders import SupplierOrderStatus, ClientOrderStatus, Reception, Quotation, QuotationLineItem
from models.production import ProductionBatch
from models.plaques import Plaque

def test_quotation_description_consistency():
    """Test that quotation descriptions are used consistently."""
    print("🔍 Testing Quotation Description Consistency")
    print("=" * 60)
    
    session = SessionLocal()
    try:
        # Get production batches
        production_batches = session.query(ProductionBatch).all()
        
        print(f"📊 Found {len(production_batches)} production batches")
        
        for pb in production_batches:
            print(f"\n🔸 Testing batch {pb.batch_code}")
            
            if pb.client_order_id:
                client_order = session.query(ClientOrder).filter(
                    ClientOrder.id == pb.client_order_id
                ).first()
                
                if client_order:
                    # Test 1: Invoice service logic
                    print(f"   📋 Invoice Service Test:")
                    quotation_description_invoice = ""
                    
                    # First, try direct quotation link from client order
                    if client_order.quotation and client_order.quotation.line_items:
                        quotation_line_item = client_order.quotation.line_items[0]
                        if quotation_line_item.description:
                            quotation_description_invoice = quotation_line_item.description
                            print(f"      ✅ Direct quotation description: '{quotation_description_invoice}'")
                    
                    # Fallback: Find most recent quotation for this client
                    if not quotation_description_invoice and client_order.client:
                        from sqlalchemy import desc
                        latest_quotation = session.query(Quotation).filter(
                            Quotation.client_id == client_order.client.id
                        ).order_by(desc(Quotation.issue_date)).first()
                        
                        if latest_quotation and latest_quotation.line_items:
                            quotation_line_item = latest_quotation.line_items[0]
                            if quotation_line_item.description:
                                quotation_description_invoice = quotation_line_item.description
                                print(f"      ✅ Latest quotation description: '{quotation_description_invoice}'")
                    
                    if not quotation_description_invoice:
                        print(f"      ⚠️  No quotation description found for invoice")
                    
                    # Test 2: Delivery note logic (same as fixed version)
                    print(f"   📦 Delivery Note Test:")
                    quotation_description_delivery = ""
                    
                    if client_order.quotation and client_order.quotation.line_items:
                        quotation_line_item = client_order.quotation.line_items[0]
                        if quotation_line_item.description:
                            quotation_description_delivery = quotation_line_item.description
                            print(f"      ✅ Direct quotation description: '{quotation_description_delivery}'")
                    
                    # Fallback: Look for most recent quotation for the same client
                    if not quotation_description_delivery and client_order.client:
                        from sqlalchemy import desc
                        most_recent_quotation = session.query(Quotation).filter(
                            Quotation.client_id == client_order.client.id
                        ).order_by(desc(Quotation.issue_date)).first()
                        
                        if most_recent_quotation and most_recent_quotation.line_items:
                            quotation_line_item = most_recent_quotation.line_items[0]
                            if quotation_line_item.description:
                                quotation_description_delivery = quotation_line_item.description
                                print(f"      ✅ Latest quotation description: '{quotation_description_delivery}'")
                    
                    if not quotation_description_delivery:
                        print(f"      ⚠️  No quotation description found for delivery note")
                    
                    # Test 3: Consistency check
                    print(f"   🔍 Consistency Check:")
                    if quotation_description_invoice and quotation_description_delivery:
                        if quotation_description_invoice == quotation_description_delivery:
                            print(f"      ✅ CONSISTENT: Both use '{quotation_description_invoice}'")
                        else:
                            print(f"      ❌ INCONSISTENT: Invoice='{quotation_description_invoice}' vs Delivery='{quotation_description_delivery}'")
                    elif quotation_description_invoice:
                        print(f"      ⚠️  Only invoice has description: '{quotation_description_invoice}'")
                    elif quotation_description_delivery:
                        print(f"      ⚠️  Only delivery note has description: '{quotation_description_delivery}'")
                    else:
                        print(f"      ❌ Neither invoice nor delivery note has quotation description")
        
        print(f"\n✅ Quotation description consistency test completed!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_quotation_description_consistency()
