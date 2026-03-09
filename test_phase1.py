#!/usr/bin/env python3
"""Test suite for magasinier interface - PHASE 1 validation"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from datetime import datetime

load_dotenv()

# Database connection
engine = create_engine(os.getenv('SQLALCHEMY_DATABASE_URI'))

print("=" * 70)
print("🧪 PHASE 1 TESTING - MAGASINIER INTERFACE")
print("=" * 70)

# TEST 1: Verify migrations applied
print("\n[TEST 1] 🔍 Migration Status")
print("-" * 70)
with engine.connect() as conn:
    result = conn.execute(text('SELECT * FROM alembic_version'))
    versions = [row[0] for row in result]
    print(f"Applied migrations: {versions}")
    if '20260205_002_magasinier_constraints' in versions:
        print("✅ Migration 002 applied (zone indexes created)")
    else:
        print("❌ Migration 002 not applied")

# TEST 2: Verify database schema
print("\n[TEST 2] 🔍 Database Schema - User table")
print("-" * 70)
inspector = inspect(engine)
user_columns = {col['name']: col['type'] for col in inspector.get_columns('user')}
print(f"Column zone_id exists: {'zone_id' in user_columns}")
if 'zone_id' in user_columns:
    print(f"  Type: {user_columns['zone_id']}")
    print("✅ zone_id column present on user table")

# TEST 3: Verify indexes created
print("\n[TEST 3] 🔍 Database Indexes")
print("-" * 70)
user_indexes = inspector.get_indexes('user')
ix_zone_exists = any(idx['name'] == 'ix_user_zone_id' for idx in user_indexes)
print(f"ix_user_zone_id exists: {ix_zone_exists}")
if ix_zone_exists:
    print("✅ Zone index created on user table")

emplacement_indexes = inspector.get_indexes('emplacement_stock')
ix_emplacement_zone_exists = any(idx['name'] == 'ix_emplacement_stock_zone_id' for idx in emplacement_indexes)
print(f"ix_emplacement_stock_zone_id exists: {ix_emplacement_zone_exists}")
if ix_emplacement_zone_exists:
    print("✅ Zone index created on emplacement_stock table")

# TEST 4: Verify zones in database
print("\n[TEST 4] 🔍 Zones Configuration")
print("-" * 70)
with engine.connect() as conn:
    # First, check zone table columns
    zone_columns = {col['name'] for col in inspector.get_columns('zone')}
    print(f"Zone table columns: {zone_columns}")
    
    result = conn.execute(text('SELECT * FROM zone ORDER BY id LIMIT 5'))
    zones = result.fetchall()
    print(f"Total zones: {len(zones)}")
    for row in zones:
        print(f"  {row}")
    if len(zones) >= 4:
        print("✅ All 4+ zones present")

# TEST 5: Verify magasinier users and zones
print("\n[TEST 5] 🔍 Magasinier Users Status")
print("-" * 70)
with engine.connect() as conn:
    # Count total magasiniers
    result = conn.execute(text("SELECT COUNT(*) FROM user WHERE role = 'magasinier'"))
    total_mag = result.scalar()
    print(f"Total magasiniers: {total_mag}")
    
    # Count magasiniers with zone
    result = conn.execute(text("SELECT COUNT(*) FROM user WHERE role = 'magasinier' AND zone_id IS NOT NULL"))
    mag_with_zone = result.scalar()
    print(f"Magasiniers with zone_id: {mag_with_zone}/{total_mag}")
    
    if mag_with_zone == total_mag:
        print("✅ All magasiniers have zone assigned")
    else:
        print(f"⚠️  {total_mag - mag_with_zone} magasiniers still without zone")
        
    # Show first few magasiniers
    result = conn.execute(text("""
        SELECT id, username, zone_id, 
               COALESCE((SELECT nom FROM zone WHERE zone.id = user.zone_id), 'NULL') as zone_name
        FROM user 
        WHERE role = 'magasinier'
        LIMIT 3
    """))
    print("\nSample magasiniers:")
    for user_id, username, zone_id, zone_name in result:
        print(f"  - {username}: zone_id={zone_id} ({zone_name})")

# TEST 6: Verify dashboard template
print("\n[TEST 6] 🔍 Template Files")
print("-" * 70)
template_path = "templates/dashboard_magasinier.html"
if os.path.exists(template_path):
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        has_zone_badge = 'zone_badge' in content or 'Zone:' in content
        has_stats = 'statistiques' in content.lower() or 'stats' in content.lower()
        has_movements = 'mouvement' in content.lower() or 'movement' in content.lower()
    print(f"✅ dashboard_magasinier.html exists ({len(content)} chars)")
    print(f"  - Zone badge: {'✅' if has_zone_badge else '❌'}")
    print(f"  - Statistics: {'✅' if has_stats else '❌'}")
    print(f"  - Movements: {'✅' if has_movements else '❌'}")
else:
    print(f"❌ Template not found: {template_path}")

# TEST 7: Verify routes.py modifications
print("\n[TEST 7] 🔍 Routes Configuration")
print("-" * 70)
with open('routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
    has_magasinier_login_check = ("not user.zone_id" in content or "not current_user.zone_id" in content) and "magasinier" in content
    has_magasinier_dashboard = "elif current_user.role == 'magasinier'" in content
    has_dashboard_magasinier_render = "render_template('dashboard_magasinier.html'" in content

print(f"Login zone validation: {'✅' if has_magasinier_login_check else '❌'}")
print(f"Magasinier dashboard route: {'✅' if has_magasinier_dashboard else '❌'}")
print(f"Dashboard template rendering: {'✅' if has_dashboard_magasinier_render else '❌'}")

if has_magasinier_login_check and has_magasinier_dashboard and has_dashboard_magasinier_render:
    print("\n✅ All route modifications in place")

# FINAL SUMMARY
print("\n" + "=" * 70)
print("📊 PHASE 1 TEST SUMMARY")
print("=" * 70)

checks = [
    ('Migration 002 applied', '20260205_002_magasinier_constraints' in str(versions) or '20260205_002_magasinier' in str(versions)),
    ('zone_id column exists', 'zone_id' in user_columns),
    ('Indexes created', ix_zone_exists and ix_emplacement_zone_exists),
    ('Zones present', len(zones) >= 4),
    ('All magasiniers have zones', mag_with_zone == total_mag),
    ('Dashboard template exists', os.path.exists(template_path)),
    ('Route modifications applied', has_magasinier_login_check and has_magasinier_dashboard),
]

passed = sum(1 for _, result in checks if result)
total = len(checks)

for check_name, result in checks:
    status = "✅" if result else "❌"
    print(f"{status} {check_name}")

print("\n" + "=" * 70)
if passed == total:
    print(f"🎉 ALL TESTS PASSED ({passed}/{total})")
    print("✅ PHASE 1 ready for browser testing!")
else:
    print(f"⚠️  {passed}/{total} tests passed, {total-passed} failed")
    print("⚠️  Address failures before proceeding")
print("=" * 70)
