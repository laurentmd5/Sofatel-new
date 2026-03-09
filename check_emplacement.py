#!/usr/bin/env python
"""Check emplacement_stock columns"""

from app import app, db
from sqlalchemy import text, inspect

with app.app_context():
    inspector = inspect(db.engine)
    columns = inspector.get_columns('emplacement_stock')
    print("emplacement_stock columns:")
    for col in columns:
        print(f"  - {col['name']:20} {col['type']}")
    
    # Check if zone_id exists
    col_names = [c['name'] for c in columns]
    if 'zone_id' in col_names:
        print("\n✓ zone_id column EXISTS")
    else:
        print("\n✗ zone_id column DOES NOT exist - need to add it")
