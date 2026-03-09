#!/usr/bin/env python3
"""
Test magasinier login flow
Simulates the login process for username=dieuveil, password=passer
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User
from werkzeug.security import check_password_hash

def test_magasinier_login():
    """Test the magasinier login and dashboard redirect"""
    
    with app.app_context():
        print("\n" + "="*70)
        print("TEST: Magasinier Login Flow")
        print("="*70)
        
        # Step 1: Find user
        print("\n[STEP 1] Finding user 'dieuveil'...")
        user = User.query.filter_by(username='dieuveil').first()
        
        if not user:
            print("❌ User not found!")
            return False
        
        print(f"✅ User found: {user.nom} {user.prenom}")
        
        # Step 2: Verify credentials
        print("\n[STEP 2] Verifying credentials...")
        password_valid = user.password_hash and check_password_hash(user.password_hash, 'passer')
        
        if not password_valid:
            print("❌ Password incorrect!")
            return False
        
        print(f"✅ Password valid")
        
        # Step 3: Check role
        print("\n[STEP 3] Checking user role...")
        print(f"   Role: {user.role}")
        
        if user.role != 'magasinier':
            print(f"❌ Role is '{user.role}', expected 'magasinier'")
            return False
        
        print(f"✅ Role is 'magasinier'")
        
        # Step 4: Check zone_id
        print("\n[STEP 4] Checking zone assignment...")
        print(f"   Zone ID: {user.zone_id}")
        print(f"   Zone: {user.zone}")
        
        if not user.zone_id:
            print("❌ User has no zone_id!")
            return False
        
        print(f"✅ User assigned to zone {user.zone_id}")
        
        # Step 5: Check if dashboard_magasinier.html exists
        print("\n[STEP 5] Checking if dashboard_magasinier.html exists...")
        template_path = os.path.join('templates', 'dashboard_magasinier.html')
        
        if os.path.exists(template_path):
            print(f"✅ Template found: {template_path}")
        else:
            print(f"⚠️  Template NOT found: {template_path}")
            print(f"   This will cause a 500 error during dashboard rendering")
            return False
        
        # Step 6: Verify routes/auth.py supports magasinier
        print("\n[STEP 6] Verifying routes/auth.py supports magasinier...")
        with open('routes/auth.py', 'r', encoding='utf-8') as f:
            auth_content = f.read()
            if "current_user.role == 'magasinier'" in auth_content:
                print("✅ auth.py has magasinier support")
            else:
                print("❌ auth.py does NOT have magasinier support")
                return False
        
        print("\n" + "="*70)
        print("✅ ALL CHECKS PASSED - Magasinier login should work!")
        print("="*70)
        return True

if __name__ == '__main__':
    success = test_magasinier_login()
    sys.exit(0 if success else 1)
