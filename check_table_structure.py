#!/usr/bin/env python
"""Check actual table structure in database"""

from app import app
from models import db
from sqlalchemy import inspect

ctx = app.app_context()
ctx.push()

try:
    inspector = inspect(db.engine)
    cols = inspector.get_columns('note_rh')
    print("\n=== Colonnes dans note_rh ===")
    for col in cols:
        print(f"  - {col['name']}: {col['type']}")
    print(f"\nTotal: {len(cols)} colonnes")
except Exception as e:
    print(f"ERREUR: {e}")
finally:
    ctx.pop()
