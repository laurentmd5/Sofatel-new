#!/usr/bin/env python
"""Fix alembic_version table - drop and recreate with larger column"""

from app import app
from models import db
from sqlalchemy import text

ctx = app.app_context()
ctx.push()

try:
    # Step 1: Drop the table and recreate it with proper column size
    print("=== Suppression et recréation de la table alembic_version ===")
    db.session.execute(text('DROP TABLE IF EXISTS alembic_version'))
    db.session.execute(text('''
        CREATE TABLE alembic_version (
            version_num VARCHAR(100) NOT NULL,
            PRIMARY KEY (version_num)
        ) COLLATE utf8mb4_general_ci
    '''))
    db.session.commit()
    print("✅ Table alembic_version recréée avec VARCHAR(100)")
    
except Exception as e:
    print(f"ERREUR: {e}")
    db.session.rollback()
finally:
    ctx.pop()
