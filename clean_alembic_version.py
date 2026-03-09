#!/usr/bin/env python
"""Check and clean Alembic version table"""

from app import app
from models import db
from sqlalchemy import text

ctx = app.app_context()
ctx.push()

try:
    result = db.session.execute(text('SELECT version_num FROM alembic_version')).fetchall()
    print("=== Versions Alembic appliquées ===")
    for row in result:
        print(f"  - {row[0]}")
    
    # Delete all versions except the valid one
    print("\n=== Nettoyage ===")
    db.session.execute(text('DELETE FROM alembic_version WHERE version_num != :ver'), {'ver': '20260205_002_magasinier_constraints'})
    db.session.commit()
    print("✅ Table alembic_version nettoyée")
except Exception as e:
    print(f"ERREUR: {e}")
finally:
    ctx.pop()
