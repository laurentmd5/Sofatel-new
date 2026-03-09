#!/usr/bin/env python
"""Fix alembic_version table column size"""

from app import app
from models import db
from sqlalchemy import text, inspect

ctx = app.app_context()
ctx.push()

try:
    # Check current column definition
    inspector = inspect(db.engine)
    cols = inspector.get_columns('alembic_version')
    print("=== Colonnes dans alembic_version ===")
    for col in cols:
        print(f"  - {col['name']}: {col['type']}")
    
    # Alter table to INCREASE column size
    print("\n=== Augmentation de la colonne version_num ===")
    db.session.execute(text('ALTER TABLE alembic_version CHANGE COLUMN version_num version_num VARCHAR(255) NOT NULL'))
    db.session.commit()
    print("✅ Colonne version_num augmentée à VARCHAR(255)")
    
except Exception as e:
    print(f"ERREUR: {e}")
finally:
    ctx.pop()
