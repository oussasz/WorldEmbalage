#!/usr/bin/env python3
"""
Fix existing production batch by creating proper client order relationship
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import sqlite3
from datetime import datetime

def fix_existing_production_batch():
    """Create a proper client order for the existing production batch"""
    db_path = "world_embalage_dev.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get the existing production batch
        cursor.execute("SELECT id, batch_code, client_order_id FROM production_batches WHERE id = 1")
        batch = cursor.fetchone()
        if not batch:
            print("No production batch found with ID 1")
            return
            
        batch_id, batch_code, current_client_order_id = batch
        print(f"Found production batch: {batch_code} with client_order_id: {current_client_order_id}")
        
        # Check if client order 1 exists
        cursor.execute("SELECT id FROM client_orders WHERE id = ?", (current_client_order_id,))
        existing_order = cursor.fetchone()
        
        if existing_order:
            print("Client order already exists, no need to fix")
            return
            
        # Get a supplier order to link to (use the first one)
        cursor.execute("SELECT id, bon_commande_ref FROM supplier_orders LIMIT 1")
        supplier_order = cursor.fetchone()
        if not supplier_order:
            print("No supplier orders found")
            return
            
        supplier_order_id, supplier_ref = supplier_order
        print(f"Using supplier order: {supplier_ref}")
        
        # Get the client from the supplier order line items
        cursor.execute("""
            SELECT client_id FROM supplier_order_line_items 
            WHERE supplier_order_id = ? LIMIT 1
        """, (supplier_order_id,))
        client_result = cursor.fetchone()
        if not client_result:
            print("No client found in supplier order line items")
            return
            
        client_id = client_result[0]
        
        # Create client order
        client_order_ref = f"CMD_{supplier_ref}_{datetime.now().strftime('%Y%m%d')}"
        
        cursor.execute("""
            INSERT INTO client_orders 
            (client_id, supplier_order_id, reference, order_date, status, total_amount, notes, created_at, updated_at)
            VALUES (?, ?, ?, date('now'), 'en_production', 0, ?, datetime('now'), datetime('now'))
        """, (client_id, supplier_order_id, client_order_ref, f"Commande créée automatiquement pour production {batch_code}"))
        
        new_client_order_id = cursor.lastrowid
        print(f"Created client order with ID: {new_client_order_id}, Reference: {client_order_ref}")
        
        # Update the production batch to point to the new client order
        cursor.execute("""
            UPDATE production_batches 
            SET client_order_id = ? 
            WHERE id = ?
        """, (new_client_order_id, batch_id))
        
        print(f"Updated production batch {batch_code} to use client_order_id: {new_client_order_id}")
        
        conn.commit()
        print("Fix completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_existing_production_batch()
