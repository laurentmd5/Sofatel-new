#!/usr/bin/env python3
"""
Test: Magasinier dashboard import verification
Ensures all imports and functions exist
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Produit, MouvementStock
from flask_login import login_user

def test_magasinier_imports():
    """Test that all required functions import correctly"""
    
    with app.app_context():
        print("\n" + "="*70)
        print("TEST: Magasinier Dashboard Imports")
        print("="*70)
        
        # Test 1: Import zone_rbac functions
        print("\n[TEST 1] Importing zone_rbac functions...")
        try:
            from zone_rbac import filter_produit_by_emplacement_zone, filter_mouvement_by_zone
            print("✅ Successfully imported:")
            print("   - filter_produit_by_emplacement_zone")
            print("   - filter_mouvement_by_zone")
        except ImportError as e:
            print(f"❌ Import failed: {e}")
            return False
        
        # Test 2: Import models
        print("\n[TEST 2] Importing required models...")
        try:
            from models import Produit, MouvementStock
            print("✅ Successfully imported:")
            print("   - Produit")
            print("   - MouvementStock")
        except ImportError as e:
            print(f"❌ Import failed: {e}")
            return False
        
        # Test 3: Get a magasinier user
        print("\n[TEST 3] Finding magasinier user...")
        user = User.query.filter_by(username='dieuveil').first()
        
        if not user:
            print("❌ User 'dieuveil' not found")
            return False
        
        print(f"✅ Found user: {user.nom} {user.prenom}")
        print(f"   Role: {user.role}")
        print(f"   Zone ID: {user.zone_id}")
        
        # Test 4: Simulate dashboard query with proper user context
        print("\n[TEST 4] Testing dashboard queries...")
        
        # Simulate login
        with app.test_request_context():
            login_user(user)
            
            # Try to query produits
            try:
                produits_query = Produit.query
                print("✅ Produit.query created")
            except Exception as e:
                print(f"❌ Produit.query failed: {e}")
                return False
            
            # Try to filter produits
            try:
                produits_zone = filter_produit_by_emplacement_zone(produits_query).all()
                print(f"✅ filter_produit_by_emplacement_zone: {len(produits_zone)} products")
            except Exception as e:
                print(f"❌ filter_produit_by_emplacement_zone failed: {e}")
                return False
            
            # Try to query mouvements
            try:
                from datetime import datetime, timedelta, timezone
                seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
                mouvements_query = MouvementStock.query.filter(
                    MouvementStock.date_mouvement >= seven_days_ago
                )
                print("✅ MouvementStock.query created")
            except Exception as e:
                print(f"❌ MouvementStock.query failed: {e}")
                return False
            
            # Try to filter mouvements
            try:
                mouvements_zone = filter_mouvement_by_zone(mouvements_query).all()
                print(f"✅ filter_mouvement_by_zone: {len(mouvements_zone)} movements")
            except Exception as e:
                print(f"❌ filter_mouvement_by_zone failed: {e}")
                return False
        
        print("\n" + "="*70)
        print("✅ ALL IMPORT TESTS PASSED")
        print("="*70)
        return True

if __name__ == '__main__':
    success = test_magasinier_imports()
    sys.exit(0 if success else 1)
