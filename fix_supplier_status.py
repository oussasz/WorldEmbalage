#!/usr/bin/env python3
"""
Script to fix supplier order status values in the database
"""
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

print(f"Working directory: {os.getcwd()}")
print(f"Src directory: {src_dir}")
print(f"Python path: {sys.path[:3]}...")  # Show first 3 entries

try:
    from config.database import SessionLocal
    from sqlalchemy import text
    print("Successfully imported database modules")
    
    def fix_supplier_status():
        print("Starting supplier status fix...")
        session = SessionLocal()
        try:
            # Check current status values in database
            print("Checking current status values...")
            result = session.execute(text('SELECT DISTINCT status FROM supplier_orders'))
            current_statuses = []
            for row in result:
                status = row[0]
                current_statuses.append(status)
                print(f'  - {status}')
            
            if not current_statuses:
                print("No supplier orders found in database")
                return
            
            # Count records by status
            result = session.execute(text('SELECT status, COUNT(*) FROM supplier_orders GROUP BY status'))
            print('\nStatus counts:')
            for row in result:
                print(f'  {row[0]}: {row[1]} records')
            
            print('\nUpdating status values...')
            
            # Map old values to new ones:
            status_mapping = {
                # Lowercase versions
                'commandé': 'commande_initial',
                'pending': 'commande_initial', 
                'confirmed': 'commande_initial',
                'en_transit': 'commande_passee',
                'en_stock': 'commande_arrivee',
                'fermé': 'commande_arrivee',
                # Uppercase versions (enum values)
                'ORDERED': 'commande_passee',  # This was the old default
                'IN_TRANSIT': 'commande_passee',
                'IN_STOCK': 'commande_arrivee',
                'CLOSED': 'commande_arrivee',
                'PENDING': 'commande_initial',
                'CONFIRMED': 'commande_initial'
            }
            
            updated_count = 0
            
            for old_status, new_status in status_mapping.items():
                if old_status in current_statuses:
                    # First count how many records will be updated
                    count_result = session.execute(
                        text("SELECT COUNT(*) FROM supplier_orders WHERE status = :old_status"),
                        {"old_status": old_status}
                    )
                    count = count_result.scalar() or 0
                    
                    if count > 0:
                        # Perform the update
                        session.execute(
                            text("UPDATE supplier_orders SET status = :new_status WHERE status = :old_status"),
                            {"new_status": new_status, "old_status": old_status}
                        )
                        print(f'Updated {count} records from "{old_status}" to "{new_status}"')
                        updated_count += count
            
            if updated_count > 0:
                session.commit()
                print(f'\nTotal: {updated_count} records updated successfully!')
                
                # Show final status counts
                result = session.execute(text('SELECT status, COUNT(*) FROM supplier_orders GROUP BY status'))
                print('\nFinal status counts:')
                for row in result:
                    print(f'  {row[0]}: {row[1]} records')
            else:
                print("No updates were needed")
                
        except Exception as e:
            session.rollback()
            print(f'Error during database operations: {e}')
            import traceback
            traceback.print_exc()
        finally:
            session.close()
            print("Database session closed")

    fix_supplier_status()
        
except ImportError as e:
    print(f'Import error: {e}')
    print('Make sure you are in the correct directory and virtual environment is activated')
    print(f'Expected src directory: {src_dir}')
    print(f'Src directory exists: {src_dir.exists()}')
except Exception as e:
    print(f'Unexpected error: {e}')
    import traceback
    traceback.print_exc()
