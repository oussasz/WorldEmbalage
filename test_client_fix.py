#!/usr/bin/env python3
"""
Test script to verify the client name fix.
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

def test_client_name_fix():
    """Test that the client name fix works correctly."""
    print("🔍 Testing Client Name Fix")
    print("=" * 50)
    
    session = SessionLocal()
    try:
        # Test the same logic as the main window grouping
        production_batches = session.query(ProductionBatch).all()
        
        print(f"📊 Found {len(production_batches)} production batches")
        
        for pb in production_batches:
            print(f"\n🔸 Processing batch {pb.batch_code}")
            
            # Initialize default values
            client_name = "N/A"
            client_id = None
            caisse_dims = "N/A"
            
            if pb.client_order_id:
                # Load client order
                client_order = session.query(ClientOrder).filter(
                    ClientOrder.id == pb.client_order_id
                ).first()
                
                if client_order:
                    print(f"   ✅ Client Order ID: {client_order.id}")
                    
                    # First, check supplier order line item for client info (priority)
                    if client_order.supplier_order_id:
                        supplier_order = session.query(SupplierOrder).filter(
                            SupplierOrder.id == client_order.supplier_order_id
                        ).first()
                        
                        if supplier_order:
                            supplier_line_items = session.query(SupplierOrderLineItem).filter(
                                SupplierOrderLineItem.supplier_order_id == supplier_order.id
                            ).first()
                            
                            if supplier_line_items and supplier_line_items.client_id:
                                # PRIORITY: Use client from supplier line item
                                client = session.query(Client).filter(
                                    Client.id == supplier_line_items.client_id
                                ).first()
                                if client:
                                    client_name = client.name
                                    client_id = client.id
                                    print(f"   🎯 Client from Supplier Line Item: '{client_name}' (ID: {client_id})")
                                
                                # Get dimensions
                                if supplier_line_items.caisse_length_mm and supplier_line_items.caisse_width_mm and supplier_line_items.caisse_height_mm:
                                    caisse_dims = f"{supplier_line_items.caisse_length_mm}×{supplier_line_items.caisse_width_mm}×{supplier_line_items.caisse_height_mm}"
                                    print(f"   📏 Dimensions: {caisse_dims}")
                    
                    # FALLBACK: Get client information from client order if not found above
                    if client_name == "N/A" and client_order.client_id:
                        client = session.query(Client).filter(
                            Client.id == client_order.client_id
                        ).first()
                        if client:
                            client_name = client.name
                            client_id = client.id
                            print(f"   🔄 Fallback - Client from Client Order: '{client_name}' (ID: {client_id})")
            
            print(f"   📋 Final Result: Client='{client_name}', Dimensions='{caisse_dims}'")
        
        print(f"\n✅ Client name fix test completed!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_client_name_fix()
