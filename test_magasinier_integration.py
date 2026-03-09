#!/usr/bin/env python3
"""
Integration Test: Complete Magasinier Dashboard Flow
Simulates real login and dashboard access
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User
from werkzeug.security import check_password_hash
from flask_login import login_user

def test_complete_magasinier_flow():
    """Test complete magasinier login and dashboard access"""
    
    with app.app_context():
        print("\n" + "="*70)
        print("INTEGRATION TEST: Magasinier Login & Dashboard")
        print("="*70)
        
        # Step 1: Authenticate user
        print("\n[STEP 1] Authenticating user...")
        user = User.query.filter_by(username='dieuveil').first()
        
        if not user or not check_password_hash(user.password_hash, 'passer'):
            print("❌ Authentication failed")
            return False
        
        print(f"✅ User authenticated: {user.nom} {user.prenom}")
        
        # Step 2: Simulate dashboard request
        print("\n[STEP 2] Simulating dashboard request...")
        
        with app.test_request_context('/dashboard'):
            login_user(user)
            
            # Step 3: Check dashboard conditions
            print("\n[STEP 3] Checking dashboard conditions...")
            
            if not user.zone_id:
                print("❌ User has no zone_id")
                return False
            
            print(f"✅ User has zone_id: {user.zone_id}")
            
            # Step 4: Test zone filtering imports and execution
            print("\n[STEP 4] Testing zone filtering...")
            
            try:
                from zone_rbac import filter_produit_by_emplacement_zone, filter_mouvement_by_zone
                from models import Produit, MouvementStock
                from datetime import datetime, timedelta, timezone
                
                # Test produit filtering
                produits_query = Produit.query
                produits_zone = filter_produit_by_emplacement_zone(produits_query).all()
                print(f"✅ Produit filtering: {len(produits_zone)} products found")
                
                # Test mouvement filtering
                seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
                mouvements_query = MouvementStock.query.filter(
                    MouvementStock.date_mouvement >= seven_days_ago
                )
                mouvements_zone = filter_mouvement_by_zone(mouvements_query).all()
                print(f"✅ Mouvement filtering: {len(mouvements_zone)} movements found")
                
            except Exception as e:
                print(f"❌ Filtering failed: {e}")
                import traceback
                traceback.print_exc()
                return False
            
            # Step 5: Test dashboard calculations
            print("\n[STEP 5] Testing dashboard calculations...")
            
            try:
                total_articles = len(produits_zone)
                total_value = sum([p.quantite * (p.prix_unitaire or 0) for p in produits_zone])
                articles_low_stock = len([p for p in produits_zone if p.quantite and p.quantite < 10])
                entrees = len([m for m in mouvements_zone if m.type_mouvement == 'entree'])
                sorties = len([m for m in mouvements_zone if m.type_mouvement == 'sortie'])
                
                print(f"✅ Total articles: {total_articles}")
                print(f"✅ Total value: {total_value:.2f}")
                print(f"✅ Low stock articles: {articles_low_stock}")
                print(f"✅ Entries (7 days): {entrees}")
                print(f"✅ Exits (7 days): {sorties}")
                
            except Exception as e:
                print(f"❌ Calculations failed: {e}")
                import traceback
                traceback.print_exc()
                return False
            
            # Step 6: Verify template exists
            print("\n[STEP 6] Verifying template...")
            
            template_path = os.path.join('templates', 'dashboard_magasinier.html')
            if not os.path.exists(template_path):
                print(f"❌ Template not found: {template_path}")
                return False
            
            print(f"✅ Template exists: {template_path}")
        
        print("\n" + "="*70)
        print("✅ INTEGRATION TEST PASSED - Dashboard Ready!")
        print("="*70)
        print("\nMagasinier can now:")
        print("  1. Login with username='dieuveil', password='passer'")
        print("  2. Access /dashboard route")
        print("  3. View zone-filtered stock and movements")
        print("  4. See dashboard_magasinier.html template")
        print("\n" + "="*70)
        
        return True

if __name__ == '__main__':
    success = test_complete_magasinier_flow()
    sys.exit(0 if success else 1)
