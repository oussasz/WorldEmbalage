#!/usr/bin/env python3
"""
Comprehensive test script to validate the enhanced grouping system.
Imports all necessary models to avoid SQLAlchemy relationship issues.
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

def test_comprehensive_grouping():
    """Test the enhanced grouping logic for finished products with all models imported."""
    print("🔍 Testing Enhanced Grouping System (Comprehensive)")
    print("=" * 60)
    
    session = SessionLocal()
    try:
        # Get all production batches (all are considered finished products)
        production_batches = session.query(ProductionBatch).all()
        
        print(f"📊 Found {len(production_batches)} production batches")
        
        if not production_batches:
            print("⚠️  No production batches found to test grouping")
            return
        
        # Test the enhanced grouping logic
        groups = {}
        problematic_batches = []
        successful_batches = []
        
        for pb in production_batches:
            print(f"\n🔸 Processing batch {pb.batch_code}")
            
            try:
                # Initialize default values
                client_name = "N/A"
                client_id = None
                caisse_dims = "N/A"
                
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
                    groups[group_key]['total_quantity'] += pb.quantity or 0
                    print(f"   ✅ Added to group {group_key}")
                    successful_batches.append(pb.batch_code)
                else:
                    print(f"   ⚠️  Cannot group: missing client_id ({client_id}) or dimensions ({caisse_dims})")
                    problematic_batches.append(pb.batch_code)
                    
            except Exception as e:
                print(f"   ❌ Error processing batch {pb.batch_code}: {e}")
                import traceback
                traceback.print_exc()
                problematic_batches.append(pb.batch_code)
        
        # Display comprehensive grouping results
        print(f"\n🎯 COMPREHENSIVE GROUPING RESULTS")
        print("=" * 60)
        print(f"📊 Total batches processed: {len(production_batches)}")
        print(f"✅ Successfully grouped batches: {len(successful_batches)}")
        print(f"⚠️  Problematic batches: {len(problematic_batches)}")
        print(f"📋 Total groups created: {len(groups)}")
        
        if groups:
            print(f"\n📊 GROUP DETAILS:")
            for group_key, group_data in groups.items():
                print(f"\n📋 Group: {group_key}")
                print(f"   👤 Client: {group_data['client_name']} (ID: {group_data['client_id']})")
                print(f"   📏 Dimensions: {group_data['dimensions']}")
                print(f"   📦 Batches ({len(group_data['batches'])}): {', '.join(group_data['batches'])}")
                print(f"   🔢 Total Quantity: {group_data['total_quantity']}")
        
        if problematic_batches:
            print(f"\n⚠️  PROBLEMATIC BATCHES:")
            for batch_code in problematic_batches:
                print(f"   - {batch_code}")
        
        # Summary statistics
        groupable_batches = len(successful_batches)
        grouping_efficiency = (groupable_batches / len(production_batches)) * 100 if production_batches else 0
        
        print(f"\n📈 GROUPING STATISTICS:")
        print(f"   • Grouping Efficiency: {grouping_efficiency:.1f}%")
        print(f"   • Average Group Size: {(groupable_batches / len(groups)):.1f} batches" if groups else "   • Average Group Size: N/A")
        print(f"   • Largest Group: {max([len(g['batches']) for g in groups.values()])} batches" if groups else "   • Largest Group: N/A")
        
        print(f"\n✅ Enhanced grouping test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during comprehensive grouping test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_comprehensive_grouping()
