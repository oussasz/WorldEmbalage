#!/usr/bin/env python3
"""
Migration script to help transition existing references to the new unified format.

This script analyzes existing references in the database and provides
options to:
1. Report current reference formats
2. Optionally update references to the new unified format
3. Generate mapping between old and new references

Usage:
    python migrate_references.py --analyze   # Analyze current references
    python migrate_references.py --migrate   # Migrate to new format (CAREFUL!)
    python migrate_references.py --report    # Generate detailed report
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from config.database import SessionLocal
from utils.reference_generator import ReferenceGenerator
from sqlalchemy import text

# Import models carefully to avoid circular import issues
try:
    from models.orders_new import SupplierOrder, Quotation, ClientOrder
    from models.production import ProductionBatch
except ImportError:
    # Fallback to alternative model imports
    from models.orders import SupplierOrder, Quotation, ClientOrder
    from models.production import ProductionBatch


class ReferenceAnalyzer:
    """Analyze and optionally migrate existing references."""
    
    def __init__(self):
        self.session = SessionLocal()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    def analyze_references(self):
        """Analyze current reference formats in the database."""
        print("=== REFERENCE FORMAT ANALYSIS ===")
        print()
        
        # Check quotations
        print("1. QUOTATIONS:")
        quotations = self.session.query(Quotation).all()
        self._analyze_reference_group(
            quotations, 
            lambda q: q.reference, 
            "quotation"
        )
        
        # Check supplier orders
        print("\n2. SUPPLIER ORDERS (BON COMMANDE):")
        supplier_orders = self.session.query(SupplierOrder).all()
        self._analyze_reference_group(
            supplier_orders, 
            lambda so: so.bon_commande_ref, 
            "supplier_order"
        )
        
        # Check client orders
        print("\n3. CLIENT ORDERS:")
        client_orders = self.session.query(ClientOrder).all()
        self._analyze_reference_group(
            client_orders, 
            lambda co: co.reference, 
            "client_order"
        )
        
        # Check production batches
        print("\n4. PRODUCTION BATCHES:")
        batches = self.session.query(ProductionBatch).all()
        self._analyze_reference_group(
            batches, 
            lambda pb: pb.batch_code, 
            "production"
        )
    
    def _analyze_reference_group(self, items, ref_getter, doc_type):
        """Analyze a group of references."""
        if not items:
            print(f"  No {doc_type} records found.")
            return
        
        standardized_count = 0
        legacy_count = 0
        invalid_count = 0
        
        print(f"  Total records: {len(items)}")
        
        # Sample references
        samples = {'standardized': [], 'legacy': [], 'invalid': []}
        
        for item in items:
            ref = ref_getter(item)
            if not ref:
                invalid_count += 1
                if len(samples['invalid']) < 3:
                    samples['invalid'].append(f"ID {item.id}: <empty>")
                continue
                
            if ReferenceGenerator.is_standardized_format(ref):
                standardized_count += 1
                if len(samples['standardized']) < 3:
                    samples['standardized'].append(f"ID {item.id}: {ref}")
            else:
                legacy_count += 1
                if len(samples['legacy']) < 3:
                    samples['legacy'].append(f"ID {item.id}: {ref}")
        
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
    
    def generate_migration_report(self):
        """Generate a detailed migration report."""
        print("=== MIGRATION IMPACT REPORT ===")
        print()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"reference_migration_report_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write("WORLD EMBALAGE - REFERENCE MIGRATION REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
            self._write_migration_analysis(f)
            
        print(f"Detailed report saved to: {filename}")
    
    def _write_migration_analysis(self, file):
        """Write detailed migration analysis to file."""
        # Analyze each table
        tables_info = [
            ("quotations", Quotation, lambda q: q.reference, "quotation"),
            ("supplier_orders", SupplierOrder, lambda so: so.bon_commande_ref, "supplier_order"),
            ("client_orders", ClientOrder, lambda co: co.reference, "client_order"),
            ("production_batches", ProductionBatch, lambda pb: pb.batch_code, "production")
        ]
        
        for table_name, model_class, ref_getter, doc_type in tables_info:
            file.write(f"\n{table_name.upper()}:\n")
            file.write("-" * 30 + "\n")
            
            items = self.session.query(model_class).all()
            
            for item in items:
                ref = ref_getter(item)
                is_standardized = ReferenceGenerator.is_standardized_format(ref) if ref else False
                
                status = "STANDARDIZED" if is_standardized else "LEGACY" if ref else "EMPTY"
                file.write(f"ID {item.id:4} | {status:12} | {ref or '<empty>'}\n")
                
                if not is_standardized and ref:
                    # Suggest new format
                    new_ref = ReferenceGenerator.generate(doc_type)
                    file.write(f"     | SUGGESTED    | {new_ref}\n")
            
            file.write("\n")
    
    def preview_migration(self):
        """Preview what migration would do without actually changing data."""
        print("=== MIGRATION PREVIEW ===")
        print("This shows what WOULD happen during migration (no changes made)")
        print()
        
        tables_info = [
            ("quotations", Quotation, lambda q: q.reference, "quotation"),
            ("supplier_orders", SupplierOrder, lambda so: so.bon_commande_ref, "supplier_order"), 
            ("client_orders", ClientOrder, lambda co: co.reference, "client_order"),
            ("production_batches", ProductionBatch, lambda pb: pb.batch_code, "production")
        ]
        
        total_changes = 0
        
        for table_name, model_class, ref_getter, doc_type in tables_info:
            print(f"\n{table_name.upper()}:")
            items = self.session.query(model_class).all()
            changes = 0
            
            for item in items:
                ref = ref_getter(item)
                if ref and not ReferenceGenerator.is_standardized_format(ref):
                    new_ref = ReferenceGenerator.generate(doc_type, ref)  # Include old ref as suffix
                    print(f"  ID {item.id}: {ref} -> {new_ref}")
                    changes += 1
                    total_changes += 1
            
            if changes == 0:
                print("  No changes needed")
            else:
                print(f"  {changes} records would be updated")
        
        print(f"\nTotal records that would be changed: {total_changes}")
        
        if total_changes > 0:
            print("\nWARNING: Migration would change existing references!")
            print("Make sure to backup your database before running --migrate")


def main():
    parser = argparse.ArgumentParser(description='Analyze and migrate reference formats')
    parser.add_argument('--analyze', action='store_true', help='Analyze current reference formats')
    parser.add_argument('--report', action='store_true', help='Generate detailed migration report')
    parser.add_argument('--preview', action='store_true', help='Preview migration changes without applying')
    parser.add_argument('--migrate', action='store_true', help='CAUTION: Actually migrate references')
    
    args = parser.parse_args()
    
    if not any([args.analyze, args.report, args.preview, args.migrate]):
        parser.print_help()
        return
    
    try:
        with ReferenceAnalyzer() as analyzer:
            if args.analyze:
                analyzer.analyze_references()
            
            if args.report:
                analyzer.generate_migration_report()
            
            if args.preview:
                analyzer.preview_migration()
            
            if args.migrate:
                print("MIGRATION NOT IMPLEMENTED YET")
                print("This would be a destructive operation that changes existing references.")
                print("Please backup your database first and implement carefully.")
                
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
