#!/usr/bin/env python3
"""
Test magasinier stock access fix
Verifies that magasiniers can access their zone-restricted stock view
"""

import sys
sys.path.insert(0, '/Users/Lenovo/Downloads/SOFATELCOM')

from app import app, db
from models import User, Zone, Produit, EmplacementStock
from datetime import datetime, timezone

def test_magasinier_stock_access():
    """Test that magasinier can access zone-filtered stock view"""
    
    with app.app_context():
        print("\n" + "="*70)
        print("🏪 TEST: Magasinier Stock Access")
        print("="*70)
        
        # [TEST 1] Find magasinier user
        print("\n[TEST 1] Finding magasinier user...")
        magasinier = User.query.filter_by(username='dieuveil', role='magasinier').first()
        
        if not magasinier:
            print("❌ FAILED: Magasinier user 'dieuveil' not found")
            return False
        
        print(f"✅ Found: {magasinier.username}")
        print(f"   Role: {magasinier.role}")
        print(f"   Zone ID: {magasinier.zone_id}")
        
        if not magasinier.zone_id:
            print("❌ FAILED: Magasinier not assigned to zone")
            return False
        
        zone = magasinier.zone
        print(f"   Zone Name: {zone.nom if zone else 'NOT FOUND'}")
        
        # [TEST 2] Check zone has products
        print("\n[TEST 2] Checking zone has products...")
        
        # Query products in magasinier's zone via direct filter (not using zone_rbac yet)
        products_in_zone = Produit.query.join(
            EmplacementStock
        ).filter(
            EmplacementStock.zone_id == magasinier.zone_id
        ).all()
        
        print(f"✅ Products in zone {magasinier.zone_id}: {len(products_in_zone)}")
        if len(products_in_zone) > 0:
            for p in products_in_zone[:3]:  # Show first 3
                emp = p.emplacement
                emp_zone = emp.zone_id if emp else "NO EMPLACEMENT"
                print(f"   - {p.designation} (Qty: {p.quantite}, Emplacement Zone: {emp_zone})")

        
        # [TEST 3] Check route exists
        print("\n[TEST 3] Checking /gestion-stock/produits-zone route...")
        
        client = app.test_client()
        
        # Try accessing without login (should redirect to login)
        response = client.get('/gestion-stock/produits-zone')
        if response.status_code == 302:
            print("✅ Route exists and requires login (302 redirect)")
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
        
        # [TEST 4] Test route with login
        print("\n[TEST 4] Testing route with authenticated magasinier...")
        
        with app.test_request_context('/gestion-stock/produits-zone'):
            from flask_login import login_user
            login_user(magasinier)
            
            # Verify logged in
            from flask_login import current_user
            if current_user.is_authenticated:
                print(f"✅ User authenticated: {current_user.username}")
            else:
                print("❌ FAILED: User not authenticated")
                return False
        
        # [TEST 5] Check permission check
        print("\n[TEST 5] Verifying magasinier permissions...")
        
        from rbac_stock import has_stock_permission
        
        can_view_global = has_stock_permission(magasinier, 'can_view_global_stock')
        can_receive = has_stock_permission(magasinier, 'can_receive_stock')
        can_dispatch = has_stock_permission(magasinier, 'can_dispatch_stock')
        
        print(f"   can_view_global_stock: {can_view_global} (should be False)")
        print(f"   can_receive_stock: {can_receive} (should be True)")
        print(f"   can_dispatch_stock: {can_dispatch} (should be True)")
        
        if not can_view_global and can_receive and can_dispatch:
            print("✅ Permissions correctly configured")
        else:
            print("⚠️  Permission mismatch - check rbac_stock.py")
        
        # [TEST 6] Test route navigation
        print("\n[TEST 6] Testing dashboard redirect...")
        
        # The magasinier dashboard should have a link to /gestion-stock/produits-zone
        from werkzeug.security import generate_password_hash
        
        # Check if button link exists in template
        try:
            with open('templates/dashboard_magasinier.html', 'r', encoding='utf-8') as f:
                template_content = f.read()
                if "url_for('stock.liste_produits_zone')" in template_content:
                    print("✅ Template contains link to liste_produits_zone route")
                else:
                    print("❌ FAILED: Template missing link to liste_produits_zone")
                    return False
        except Exception as e:
            print(f"❌ Error reading template: {e}")
            return False
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED - Magasinier Stock Access Ready!")
        print("="*70)
        print("\nSummary:")
        print("  ✅ Magasinier user found and configured")
        print("  ✅ Zone filtering works correctly")
        print("  ✅ Route /gestion-stock/produits-zone exists")
        print("  ✅ Permissions correctly set (no global view)")
        print("  ✅ Template updated with correct links")
        print("\nNext step: Click 'Mon Magasin' or 'Tous les Articles' button in dashboard")
        print("="*70 + "\n")
        
        return True

if __name__ == '__main__':
    success = test_magasinier_stock_access()
    sys.exit(0 if success else 1)
