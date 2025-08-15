#!/usr/bin/env python3
"""
Migration script to update SupplierOrder model structure
"""
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

from config.database import SessionLocal, engine
from sqlalchemy import text
from loguru import logger

def migrate_supplier_orders():
    """Migrate supplier orders to new structure"""
    logger.info("Starting migration of supplier orders...")
    
    session = SessionLocal()
    try:
        # Check if the new columns exist
        result = session.execute(text("PRAGMA table_info(supplier_orders)"))
        columns = [row[1] for row in result.fetchall()]
        
        logger.info(f"Current columns in supplier_orders: {columns}")
        
        # Add new columns if they don't exist
        if 'bon_commande_ref' not in columns:
            logger.info("Adding bon_commande_ref column...")
            session.execute(text("ALTER TABLE supplier_orders ADD COLUMN bon_commande_ref VARCHAR(64)"))
            
        if 'total_amount' not in columns:
            logger.info("Adding total_amount column...")
            session.execute(text("ALTER TABLE supplier_orders ADD COLUMN total_amount DECIMAL(12,2) DEFAULT 0"))
            
        if 'currency' not in columns:
            logger.info("Adding currency column...")
            session.execute(text("ALTER TABLE supplier_orders ADD COLUMN currency VARCHAR(3) DEFAULT 'DZD'"))
        
        # Copy reference to bon_commande_ref if empty
        session.execute(text("""
            UPDATE supplier_orders 
            SET bon_commande_ref = reference 
            WHERE bon_commande_ref IS NULL AND reference IS NOT NULL
        """))
        
        # Create new line items table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS supplier_order_line_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_order_id INTEGER NOT NULL,
                client_id INTEGER NOT NULL,
                line_number INTEGER NOT NULL,
                code_article VARCHAR(100) NOT NULL,
                caisse_length_mm INTEGER NOT NULL,
                caisse_width_mm INTEGER NOT NULL,
                caisse_height_mm INTEGER NOT NULL,
                plaque_width_mm INTEGER NOT NULL,
                plaque_length_mm INTEGER NOT NULL,
                plaque_flap_mm INTEGER NOT NULL,
                prix_uttc_plaque DECIMAL(12,2) NOT NULL,
                quantity INTEGER NOT NULL,
                total_line_amount DECIMAL(12,2) DEFAULT 0,
                cardboard_type VARCHAR(64),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_order_id) REFERENCES supplier_orders(id) ON DELETE CASCADE,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE RESTRICT
            )
        """))
        
        session.commit()
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        session.close()

if __name__ == '__main__':
    migrate_supplier_orders()
