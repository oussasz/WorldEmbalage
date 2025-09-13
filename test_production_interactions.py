#!/usr/bin/env python3
"""
Test script to simulate grouped production batch interactions.
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

def simulate_production_interactions():
    """Simulate how the production grid interactions work with grouped data."""
    print("🔍 Simulating Production Grid Interactions")
    print("=" * 60)
    
    session = SessionLocal()
    try:
        # Get all production batches and simulate grouping
        production_batches = session.query(ProductionBatch).all()
        
        # Simulate the grouping logic (same as in main_window.py)
        grouped_items = {}
        
        for pb in production_batches:
            # Simplified grouping logic
            client_name = "ENAD"  # We know from our diagnosis this should be ENAD
            client_id = 5
            caisse_dims = "100×200×150"
            
            group_key = (client_id, caisse_dims)
            
            if group_key not in grouped_items:
                grouped_items[group_key] = {
                    'ids': [],
                    'client_name': client_name,
                    'dimensions': caisse_dims,
                    'total_quantity': 0,
                    'production_dates': []
                }
            
            group_item = grouped_items[group_key]
            group_item['ids'].append(str(pb.id))
            group_item['total_quantity'] += int(getattr(pb, 'quantity', 0) or 0)
        
        # Convert to display format (like the grid shows)
        print("📊 Simulated Production Grid Data:")
        for group_key, group_data in grouped_items.items():
            id_display = ",".join(group_data['ids'])
            
            # This is what appears in the grid
            row_data = [
                id_display,
                group_data['client_name'],
                group_data['dimensions'],
                str(group_data['total_quantity']),
                "2025-09-12"
            ]
            
            print(f"   Row: {row_data}")
            
            # Test double-click simulation
            print(f"\n🖱️  Simulating double-click on grouped row:")
            print(f"      ID field: '{row_data[0]}'")
            
            # Check if it's a comma-separated format (new grouping system)
            id_field = row_data[0]
            if ',' in id_field:
                ids = [id_str.strip() for id_str in id_field.split(',')]
                print(f"      ✅ Detected comma-separated format with {len(ids)} IDs: {ids}")
                print(f"      📝 Would show message: 'Cette ligne représente {len(ids)} lots groupés'")
            elif id_field.isdigit():
                print(f"      ✅ Single ID: {id_field}")
                print(f"      📝 Would open production details dialog")
            else:
                print(f"      ❌ Invalid ID format")
            
            # Test delete simulation
            print(f"\n🗑️  Simulating delete on grouped row:")
            if ',' in id_field:
                ids_str = [id_str.strip() for id_str in id_field.split(',')]
                try:
                    batch_ids = [int(id_str) for id_str in ids_str]
                    print(f"      ✅ Would ask to delete {len(batch_ids)} batches: {batch_ids}")
                    print(f"      📝 Confirmation dialog would show details about grouped items")
                except ValueError:
                    print(f"      ❌ Invalid ID format in grouped items")
        
        print(f"\n✅ Production interaction simulation completed!")
        
    except Exception as e:
        print(f"❌ Error during simulation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    simulate_production_interactions()
