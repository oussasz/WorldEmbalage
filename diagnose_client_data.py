#!/usr/bin/env python3
"""
Diagnostic script to check client data and relationships.
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

def diagnose_client_data():
    """Diagnose client data and relationships."""
    print("🔍 Diagnosing Client Data and Relationships")
    print("=" * 60)
    
    session = SessionLocal()
    try:
        # First, let's see all clients
        clients = session.query(Client).all()
        print(f"📊 Found {len(clients)} clients:")
        for client in clients:
            print(f"   ID: {client.id}, Name: '{client.name}'")
        
        print("\n" + "="*60)
        
        # Check production batches and their relationships
        production_batches = session.query(ProductionBatch).all()
        print(f"📦 Found {len(production_batches)} production batches:")
        
        for pb in production_batches:
            print(f"\n🔸 Batch: {pb.batch_code}")
            print(f"   ID: {pb.id}")
            print(f"   Quantity: {pb.quantity}")
            print(f"   Client Order ID: {pb.client_order_id}")
            
            if pb.client_order_id:
                # Get client order
                client_order = session.query(ClientOrder).filter(
                    ClientOrder.id == pb.client_order_id
                ).first()
                
                if client_order:
                    print(f"   ✅ Client Order found: ID {client_order.id}")
                    print(f"      Client ID: {client_order.client_id}")
                    print(f"      Supplier Order ID: {client_order.supplier_order_id}")
                    print(f"      Quotation ID: {client_order.quotation_id}")
                    
                    # Get client from client order
                    if client_order.client_id:
                        client = session.query(Client).filter(
                            Client.id == client_order.client_id
                        ).first()
                        if client:
                            print(f"      ✅ Client from Client Order: '{client.name}' (ID: {client.id})")
                        else:
                            print(f"      ❌ Client with ID {client_order.client_id} not found!")
                    else:
                        print(f"      ⚠️  No client_id in client order")
                    
                    # Check supplier order lineitem if available
                    if client_order.supplier_order_id:
                        supplier_order = session.query(SupplierOrder).filter(
                            SupplierOrder.id == client_order.supplier_order_id
                        ).first()
                        
                        if supplier_order:
                            supplier_line_items = session.query(SupplierOrderLineItem).filter(
                                SupplierOrderLineItem.supplier_order_id == supplier_order.id
                            ).all()
                            
                            print(f"      📋 Supplier Order: {supplier_order.reference}")
                            print(f"         Line items: {len(supplier_line_items)}")
                            
                            for line_item in supplier_line_items:
                                print(f"         - Line Item ID: {line_item.id}")
                                print(f"           Client ID in line item: {line_item.client_id}")
                                if line_item.client_id:
                                    client_from_line = session.query(Client).filter(
                                        Client.id == line_item.client_id
                                    ).first()
                                    if client_from_line:
                                        print(f"           ✅ Client from Line Item: '{client_from_line.name}' (ID: {client_from_line.id})")
                                    else:
                                        print(f"           ❌ Client with ID {line_item.client_id} not found in line item!")
                                
                                # Show dimensions
                                if hasattr(line_item, 'caisse_length_mm'):
                                    print(f"           Dimensions: {line_item.caisse_length_mm}×{line_item.caisse_width_mm}×{line_item.caisse_height_mm}")
                    
                    # Check quotation if available
                    if client_order.quotation_id:
                        quotation = session.query(Quotation).filter(
                            Quotation.id == client_order.quotation_id
                        ).first()
                        if quotation:
                            print(f"      📋 Quotation: {quotation.reference}")
                            quotation_lines = session.query(QuotationLineItem).filter(
                                QuotationLineItem.quotation_id == quotation.id
                            ).all()
                            for qline in quotation_lines:
                                print(f"         - Quotation Line: {qline.length_mm}×{qline.width_mm}×{qline.height_mm}")
                else:
                    print(f"   ❌ Client Order with ID {pb.client_order_id} not found!")
            else:
                print(f"   ⚠️  No client order ID")
        
    except Exception as e:
        print(f"❌ Error during diagnosis: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    diagnose_client_data()
