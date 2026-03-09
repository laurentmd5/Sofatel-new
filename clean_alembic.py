#!/usr/bin/env python
"""Clean alembic_version table"""

from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # Delete bad revisions
        db.session.execute(text("DELETE FROM alembic_version WHERE version_num LIKE '001%' OR version_num LIKE '002%'"))
        db.session.commit()
        print("[OK] Alembic version cleaned - bad revisions removed")
        
        # Show current version
        result = db.session.execute(text("SELECT version_num FROM alembic_version"))
        versions = result.fetchall()
        print(f"[INFO] Current version(s): {[v[0] for v in versions]}")
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        db.session.rollback()
