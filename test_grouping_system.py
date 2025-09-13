#!/usr/bin/env python3
"""
Test script to validate the enhanced grouping system for finished products.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.database import SessionLocal
from models.production import ProductionBatch
from models.orders import ClientOrder, SupplierOrder, SupplierOrderLineItem
from models.clients import Client
from models.orders import Quotation, QuotationLineItem
from sqlalchemy.orm import joinedload
from sqlalchemy import and_

def test_grouping_logic():
    """Test the enhanced grouping logic for finished products."""
    print("🔍 Testing Enhanced Grouping System")
    print("=" * 50)
    
    session = SessionLocal()
    try:
        # Get all finished production batches
        finished_batches = session.query(ProductionBatch).filter(
            ProductionBatch.status == 'finished'
        ).all()
        
        print(f"📊 Found {len(finished_batches)} finished production batches")
        
        if not finished_batches:
            print("⚠️  No finished production batches found to test grouping")
            return
        
        # Test the grouping logic for each batch
        groups = {}
        problematic_batches = []
        
        for pb in finished_batches:
            print(f"\n🔸 Processing batch {pb.batch_code}")
            
            try:
                # Initialize default values
                client_name = "N/A"
                client_id = None
                caisse_dims = "N/A"
                plaque_dims = "N/A"
                material_type = "Standard"
                
                if pb.client_order_id:
                    # Load client order separately to avoid relationship issues
                    client_order = session.query(ClientOrder).filter(
                        ClientOrder.id == pb.client_order_id
                    ).first()
                    
                    if client_order:
                        # Get client information
                        if client_order.client_id:
                            client = session.query(Client).filter(
                                Client.id == client_order.client_id
                            ).first()
                            if client:
                                client_name = client.name
                                client_id = client.id
                                print(f"   ✅ Client: {client_name} (ID: {client_id})")
                        
                        # Get dimensions from quotation if available
                        if client_order.quotation_id:
                            quotation = session.query(Quotation).filter(
                                Quotation.id == client_order.quotation_id
                            ).first()
                            if quotation:
                                quotation_lines = session.query(QuotationLineItem).filter(
                                    QuotationLineItem.quotation_id == quotation.id
                                ).first()
                                if quotation_lines and quotation_lines.length_mm and quotation_lines.width_mm and quotation_lines.height_mm:
                                    caisse_dims = f"{quotation_lines.length_mm}×{quotation_lines.width_mm}×{quotation_lines.height_mm}"
                                    print(f"   ✅ Dimensions from quotation: {caisse_dims}")
                        
                        # Fallback to supplier order if needed
                        if caisse_dims == "N/A" and client_order.supplier_order_id:
                            supplier_order = session.query(SupplierOrder).filter(
                                SupplierOrder.id == client_order.supplier_order_id
                            ).first()
                            
                            if supplier_order:
                                supplier_line_items = session.query(SupplierOrderLineItem).filter(
                                    SupplierOrderLineItem.supplier_order_id == supplier_order.id
                                ).first()
                                
                                if supplier_line_items:
                                    if supplier_line_items.caisse_length_mm and supplier_line_items.caisse_width_mm and supplier_line_items.caisse_height_mm:
                                        caisse_dims = f"{supplier_line_items.caisse_length_mm}×{supplier_line_items.caisse_width_mm}×{supplier_line_items.caisse_height_mm}"
                                        print(f"   ✅ Dimensions from supplier order: {caisse_dims}")
                
                # Create grouping key using strict criteria: same client_id + same dimensions
                if client_id and caisse_dims != "N/A":
                    group_key = f"{client_id}_{caisse_dims}"
                    print(f"   📋 Group key: {group_key}")
                    
                    if group_key not in groups:
                        groups[group_key] = {
                            'client_name': client_name,
                            'client_id': client_id,
                            'dimensions': caisse_dims,
                            'batches': [],
                            'total_quantity': 0
                        }
                    
                    groups[group_key]['batches'].append(pb.batch_code)
                    groups[group_key]['total_quantity'] += pb.quantity_produced or 0
                    print(f"   ✅ Added to group {group_key}")
                else:
                    print(f"   ⚠️  Cannot group: missing client_id ({client_id}) or dimensions ({caisse_dims})")
                    problematic_batches.append(pb.batch_code)
                    
            except Exception as e:
                print(f"   ❌ Error processing batch {pb.batch_code}: {e}")
                problematic_batches.append(pb.batch_code)
        
        # Display grouping results
        print(f"\n🎯 GROUPING RESULTS")
        print("=" * 50)
        print(f"📊 Total groups created: {len(groups)}")
        print(f"⚠️  Problematic batches: {len(problematic_batches)}")
        
        for group_key, group_data in groups.items():
            print(f"\n📋 Group: {group_key}")
            print(f"   Client: {group_data['client_name']} (ID: {group_data['client_id']})")
            print(f"   Dimensions: {group_data['dimensions']}")
            print(f"   Batches: {', '.join(group_data['batches'])}")
            print(f"   Total Quantity: {group_data['total_quantity']}")
        
        if problematic_batches:
            print(f"\n⚠️  Problematic batches that couldn't be grouped:")
            for batch_code in problematic_batches:
                print(f"   - {batch_code}")
        
        print(f"\n✅ Grouping test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during grouping test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_grouping_logic()
