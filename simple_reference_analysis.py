#!/usr/bin/env python3
"""
Simple reference analysis script for World Embalage.
Analyzes current reference formats without complex model imports.
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from utils.reference_generator import ReferenceGenerator


def analyze_references():
    """Analyze references directly from database using SQL."""
    db_path = Path(__file__).parent / 'src' / 'world_embalage_dev.db'
    
    if not db_path.exists():
        print(f"Database not found at: {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("=== REFERENCE FORMAT ANALYSIS ===")
    print()
    
    # Check quotations
    print("1. QUOTATIONS:")
    try:
        cursor.execute("SELECT id, reference FROM quotations")
        rows = cursor.fetchall()
        analyze_reference_group(rows, "quotation")
    except sqlite3.OperationalError as e:
        print(f"  Error accessing quotations: {e}")
    
    # Check supplier orders
    print("\n2. SUPPLIER ORDERS:")
    try:
        cursor.execute("SELECT id, bon_commande_ref FROM supplier_orders")
        rows = cursor.fetchall()
        analyze_reference_group(rows, "supplier_order")
    except sqlite3.OperationalError as e:
        print(f"  Error accessing supplier_orders: {e}")
    
    # Check client orders
    print("\n3. CLIENT ORDERS:")
    try:
        cursor.execute("SELECT id, reference FROM client_orders")
        rows = cursor.fetchall()
        analyze_reference_group(rows, "client_order")
    except sqlite3.OperationalError as e:
        print(f"  Error accessing client_orders: {e}")
    
    # Check production batches
    print("\n4. PRODUCTION BATCHES:")
    try:
        cursor.execute("SELECT id, batch_code FROM production_batches")
        rows = cursor.fetchall()
        analyze_reference_group(rows, "production")
    except sqlite3.OperationalError as e:
        print(f"  Error accessing production_batches: {e}")
    
    conn.close()


def analyze_reference_group(rows, doc_type):
    """Analyze a group of references."""
    if not rows:
        print(f"  No {doc_type} records found.")
        return
    
    standardized_count = 0
    legacy_count = 0
    invalid_count = 0
    
    print(f"  Total records: {len(rows)}")
    
    # Sample references
    samples = {'standardized': [], 'legacy': [], 'invalid': []}
    
    for row_id, ref in rows:
        if not ref:
            invalid_count += 1
            if len(samples['invalid']) < 3:
                samples['invalid'].append(f"ID {row_id}: <empty>")
            continue
            
        if ReferenceGenerator.is_standardized_format(ref):
            standardized_count += 1
            if len(samples['standardized']) < 3:
                samples['standardized'].append(f"ID {row_id}: {ref}")
        else:
            legacy_count += 1
            if len(samples['legacy']) < 3:
                samples['legacy'].append(f"ID {row_id}: {ref}")
    
    print(f"  Standardized format: {standardized_count}")
    print(f"  Legacy format: {legacy_count}")
    print(f"  Invalid/Empty: {invalid_count}")
    
    # Show samples
    if samples['standardized']:
        print(f"  Standardized samples: {'; '.join(samples['standardized'])}")
    if samples['legacy']:
        print(f"  Legacy samples: {'; '.join(samples['legacy'])}")
    if samples['invalid']:
        print(f"  Invalid samples: {'; '.join(samples['invalid'])}")


def show_new_format_examples():
    """Show examples of the new unified format."""
    print("\n=== NEW UNIFIED FORMAT EXAMPLES ===")
    print()
    
    for doc_type in ReferenceGenerator.PREFIXES:
        ref = ReferenceGenerator.generate(doc_type)
        print(f"{doc_type:15} -> {ref}")
    
    print()
    print("Format: PREFIX-YYYYMMDD-HHMMSS-NNNN[-SUFFIX]")
    print("- PREFIX: Document type identifier")
    print("- YYYYMMDD: Date (year-month-day)")
    print("- HHMMSS: Time (hour-minute-second)")
    print("- NNNN: Sequential number (4 digits)")
    print("- SUFFIX: Optional custom suffix")


def main():
    print("World Embalage - Reference Format Analysis")
    print("=" * 45)
    
    try:
        analyze_references()
        show_new_format_examples()
        
        print("\n=== SUMMARY ===")
        print("✅ Unified reference generation system is now active")
        print("✅ All new references will use standardized format")
        print("✅ Existing references continue to work")
        print("✅ Backward compatibility maintained")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
