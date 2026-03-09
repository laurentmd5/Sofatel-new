#!/usr/bin/env python
# Script to add zone_id column to user table

from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # Add zone_id column if not exists
        db.session.execute(text("""
            ALTER TABLE user ADD COLUMN zone_id INT NULL;
        """))
        db.session.commit()
        print("[OK] Column zone_id added to user table")
    except Exception as e:
        if "Duplicate column" in str(e):
            print("[OK] Column zone_id already exists")
        else:
            print(f"[ERROR] {str(e)}")
    finally:
        db.session.close()
