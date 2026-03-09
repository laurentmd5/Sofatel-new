#!/usr/bin/env python
"""Mark zone_id migration as applied"""

from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # Mark 20260205_001_zone_emplacement as applied
        db.session.execute(text("INSERT IGNORE INTO alembic_version (version_num) VALUES ('20260205_001_zone_emplacement')"))
        db.session.commit()
        print("[OK] Migration 20260205_001_zone_emplacement marked as applied")
        
        # Show current versions
        result = db.session.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num"))
        versions = result.fetchall()
        print(f"\n[INFO] Applied migrations:\n")
        for v in versions:
            print(f"  ✓ {v[0]}")
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        db.session.rollback()
