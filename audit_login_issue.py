#!/usr/bin/env python3
"""
AUDIT SCRIPT: Complete analysis of login/magasinier role issue
Analyzes: User data, login flow, role recognition, dashboard redirects
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User
from werkzeug.security import check_password_hash

def audit_login_system():
    """Complete audit of login and magasinier role system"""
    
    with app.app_context():
        print("\n" + "="*70)
        print("AUDIT: LOGIN & MAGASINIER ROLE SYSTEM")
        print("="*70)
        
        # 1. Find user "dieuveil"
        print("\n[1] SEARCHING FOR USER: dieuveil")
        print("-" * 70)
        user = User.query.filter_by(username='dieuveil').first()
        
        if user:
            print(f"✅ User found:")
            print(f"   ID: {user.id}")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   First name: {user.prenom}")
            print(f"   Last name: {user.nom}")
            print(f"   Role: {user.role}")
            print(f"   Zone: {user.zone}")
            print(f"   Zone ID: {user.zone_id}")
            print(f"   Active: {user.actif}")
            print(f"   Phone: {user.telephone}")
            
            # Test password
            print("\n   Password verification:")
            password_test = check_password_hash(user.password_hash, 'passer')
            print(f"   Password 'passer' match: {password_test}")
        else:
            print("❌ User 'dieuveil' NOT FOUND")
            print("\n   Available users:")
            all_users = User.query.limit(20).all()
            for u in all_users:
                print(f"   - {u.username} (role={u.role})")
            return False
        
        # 2. Check all magasinier users
        print("\n[2] CHECKING ALL MAGASINIER USERS")
        print("-" * 70)
        magasiniers = User.query.filter_by(role='magasinier').all()
        print(f"Found {len(magasiniers)} magasinier users:")
        for m in magasiniers:
            print(f"   ✓ {m.username} (ID={m.id}, zone_id={m.zone_id})")
        
        # 3. Analyze role value
        print("\n[3] ROLE VALUE ANALYSIS")
        print("-" * 70)
        if user:
            print(f"User 'dieuveil' role value: '{user.role}'")
            print(f"Role type: {type(user.role)}")
            print(f"Role length: {len(user.role) if user.role else 'None'}")
            print(f"Role == 'magasinier': {user.role == 'magasinier'}")
            print(f"Role.lower() == 'magasinier': {user.role.lower() == 'magasinier' if user.role else False}")
            
            # Check for hidden characters
            if user.role:
                print(f"Role bytes: {user.role.encode()}")
        
        # 4. Check all unique roles in database
        print("\n[4] ALL UNIQUE ROLES IN DATABASE")
        print("-" * 70)
        roles = db.session.query(User.role).distinct().all()
        for (role,) in roles:
            count = User.query.filter_by(role=role).count()
            print(f"   '{role}': {count} users")
        
        # 5. Check RBAC configuration
        print("\n[5] RBAC CONFIGURATION")
        print("-" * 70)
        try:
            from rbac_stock import STOCK_PERMISSIONS
            print("✅ STOCK_PERMISSIONS found:")
            if 'magasinier' in STOCK_PERMISSIONS:
                print(f"   magasinier permissions: {STOCK_PERMISSIONS['magasinier']}")
            else:
                print("   ❌ 'magasinier' NOT in STOCK_PERMISSIONS")
                print(f"   Available roles: {list(STOCK_PERMISSIONS.keys())}")
        except ImportError as e:
            print(f"❌ Cannot import STOCK_PERMISSIONS: {e}")
        
        # 6. Check if there are role recognition issues in code
        print("\n[6] CHECKING FOR ROLE VALIDATION CODE")
        print("-" * 70)
        print("Looking for potential 'Rôle utilisateur non reconnu' message locations...")
        
        return True

if __name__ == '__main__':
    audit_login_system()
    print("\n" + "="*70)
