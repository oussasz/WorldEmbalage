#!/usr/bin/env python3
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

from config.database import SessionLocal
from sqlalchemy import text

session = SessionLocal()
try:
    # Check current status values in database
    result = session.execute(text('SELECT DISTINCT status FROM supplier_orders'))
    print('Current status values in database:')
    for row in result:
        print(f'  - {row[0]}')
    
    # Count records by status
    result = session.execute(text('SELECT status, COUNT(*) FROM supplier_orders GROUP BY status'))
    print('\nStatus counts:')
    for row in result:
        print(f'  {row[0]}: {row[1]} records')
        
finally:
    session.close()
