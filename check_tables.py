#!/usr/bin/env python
"""Check database tables"""

from app import app, db
from sqlalchemy import text, inspect

with app.app_context():
    # Get list of tables
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print("Database tables:")
    for table in sorted(tables):
        print(f"  - {table}")
    
    # Check zone table
    if 'zone' in tables:
        print("\n✓ 'zone' table exists")
        columns = inspector.get_columns('zone')
        print(f"  Columns: {[c['name'] for c in columns]}")
    else:
        print("\n✗ 'zone' table DOES NOT exist")
        print("\nSearching for similar tables:")
        for table in tables:
            if 'zone' in table.lower():
                print(f"  Found: {table}")
