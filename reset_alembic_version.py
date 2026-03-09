#!/usr/bin/env python
"""Reset Alembic version in database"""

from app import app
from models import db
from sqlalchemy import text

ctx = app.app_context()
ctx.push()

try:
    db.session.execute(text('UPDATE alembic_version SET version_num = :ver'), {'ver': '20260205_002_magasinier_constraints'})
    db.session.commit()
    print("✅ Version Alembic résetée à 20260205_002_magasinier_constraints")
except Exception as e:
    print(f"ERREUR: {e}")
finally:
    ctx.pop()
