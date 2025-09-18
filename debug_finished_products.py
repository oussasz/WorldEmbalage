#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.database import SessionLocal
from models import ProductionBatch, ClientOrder, Quotation

def debug_finished_products():
    """Debug finished products description loading specifically."""
    session = SessionLocal()
    try:
        print("=== DEBUGGING FINISHED PRODUCTS DISPLAY LOGIC ===")
        
        production_batches = session.query(ProductionBatch).filter(
            ~ProductionBatch.batch_code.like('[ARCHIVED]%')
        ).all()
        
        grouped_items = {}
        
        for pb in production_batches:
            print(f"\n--- Processing ProductionBatch {pb.id} ---")
            print(f"Quantity: {pb.quantity}")
            print(f"Client Order ID: {pb.client_order_id}")
            
            # Get client order and related information
            client_name = "N/A"
            client_id = None
            caisse_dims = "N/A"
            
            if pb.client_order_id:
                client_order = session.query(ClientOrder).filter(
                    ClientOrder.id == pb.client_order_id
                ).first()
                
                if client_order:
                    client_name = client_order.client.name if client_order.client else "N/A"
                    client_id = client_order.client.id if client_order.client else None
                    print(f"Client: {client_name} (ID: {client_id})")
                
                    # Check for dimensions in production batch (these don't exist in ProductionBatch model)
                    # Dimensions are stored in related quotation line items
                    caisse_dims = "N/A"
                    if pb.client_order and pb.client_order.quotation:
                        quotation = pb.client_order.quotation
                        if quotation.line_items:
                            first_line = quotation.line_items[0]
                            if first_line.length_mm and first_line.width_mm and first_line.height_mm:
                                caisse_dims = f"{first_line.length_mm}×{first_line.width_mm}×{first_line.height_mm}mm"
                                print(f"Dimensions: {caisse_dims}")
                    
                    if caisse_dims == "N/A":
                        print("Dimensions: N/A (no quotation line items found)")
            
            # Get description
            description = "N/A"
            
            # First priority: Check if production batch has description
            if hasattr(pb, 'description') and pb.description and pb.description.strip():
                description = pb.description.strip()
                print(f"Got description from production batch: '{description}'")
            else:
                print("No description in production batch, checking quotation...")
                # Second priority: Try to get description from client order -> quotation
                if pb.client_order_id:
                    try:
                        client_order = session.query(ClientOrder).filter(
                            ClientOrder.id == pb.client_order_id
                        ).first()
                        
                        print(f"Client order quotation_id: {client_order.quotation_id if client_order else 'None'}")
                        
                        if client_order and client_order.quotation:
                            quotation = client_order.quotation
                            print(f"Found quotation {quotation.id}")
                            
                            # Try line items first (priority)
                            if quotation.line_items:
                                first_quotation_line = quotation.line_items[0]
                                if first_quotation_line.description and first_quotation_line.description.strip():
                                    description = first_quotation_line.description.strip()
                                    print(f"Got description from quotation line item: '{description}'")
                            
                            # Fallback to quotation notes
                            if description == "N/A" and quotation.notes and quotation.notes.strip():
                                notes = quotation.notes.strip()
                                if notes.startswith('[ARCHIVED]'):
                                    description = f"[Archived] {notes[10:].strip()}" if len(notes) > 10 else notes
                                else:
                                    description = notes
                                print(f"Got description from quotation notes: '{description}'")
                        else:
                            print("No quotation found for client order")
                    except Exception as desc_error:
                        print(f"Error fetching description: {desc_error}")
            
            print(f"FINAL DESCRIPTION: '{description}'")
            
            # STRICT GROUPING: Only group if SAME CLIENT ID + SAME EXACT DIMENSIONS
            group_key = (client_id, caisse_dims)
            
            # Skip grouping if we don't have both client_id and dimensions
            if client_id is None or caisse_dims == "N/A":
                group_key = (f"ungroupable_{pb.id}", f"batch_{pb.id}")
                print(f"Using ungroupable key: {group_key}")
            else:
                print(f"Using group key: {group_key}")
            
            # Initialize group if it doesn't exist
            if group_key not in grouped_items:
                grouped_items[group_key] = {
                    'ids': [],
                    'client_name': client_name,
                    'dimensions': caisse_dims,
                    'total_quantity': 0,
                    'production_dates': [],
                    'description': description
                }
                print(f"Created new group with description: '{description}'")
            
            # Add to grouped items
            group_item = grouped_items[group_key]
            group_item['ids'].append(str(pb.id))
            group_item['total_quantity'] += int(getattr(pb, 'quantity', 0) or 0)
            
            # If we don't have a description yet in the group, try to use this one
            if group_item.get('description', 'N/A') == 'N/A' and description != 'N/A':
                group_item['description'] = description
                print(f"Updated group description to: '{description}'")
            
            print(f"Group now has description: '{group_item.get('description', 'N/A')}'")
        
        print("\n=== FINAL GROUPED ITEMS ===")
        for group_key, group_data in grouped_items.items():
            print(f"Group {group_key}:")
            print(f"  Client: {group_data['client_name']}")
            print(f"  Dimensions: {group_data['dimensions']}")
            print(f"  Quantity: {group_data['total_quantity']}")
            print(f"  Description: '{group_data.get('description', 'N/A')}'")
            print(f"  IDs: {group_data['ids']}")
            print()
            
    finally:
        session.close()

if __name__ == "__main__":
    debug_finished_products()