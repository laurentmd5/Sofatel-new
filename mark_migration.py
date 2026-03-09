#!/usr/bin/env python
"""Mark migration as applied"""

from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # Mark 8d5157421e44 as applied (it was already partially applied)
        db.session.execute(text("INSERT IGNORE INTO alembic_version (version_num) VALUES ('8d5157421e44')"))
        db.session.commit()
        print("[OK] Migration 8d5157421e44 marked as applied")
        
        # Show current versions
        result = db.session.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num"))
        versions = result.fetchall()
        print(f"[INFO] Applied versions: {[v[0] for v in versions]}")
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        db.session.rollback()
