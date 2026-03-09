#!/usr/bin/env python
"""
Test complet du dashboard magasinier
- Simuler un login magasinier
- Accéder au dashboard
- Vérifier que tous les URLs générés sont corrects
"""
from app import app
from models import User, db, Zone
import json

# Configuration test
TEST_USER = {
    'username': 'magasinier_test',
    'email': 'mag@test.com',
    'nom': 'Test',
    'prenom': 'Magasinier',
    'password': 'password123',
    'role': 'magasinier'
}

def test_magasinier_dashboard():
    print("\n" + "="*70)
    print("TEST DASHBOARD MAGASINIER")
    print("="*70 + "\n")
    
    with app.test_client() as client:
        with app.app_context():
            # Create or get test zone
            zone = Zone.query.first()
            if not zone:
                zone = Zone(nom='Test Zone', code='TZ')
                db.session.add(zone)
                db.session.commit()
            
            # Create test user if doesn't exist
            test_user = User.query.filter_by(username='dieuveil').first()
            if not test_user:
                print("⚠ No test user 'dieuveil' found. Using existing magasinier.")
                test_user = User.query.filter_by(role='magasinier').first()
            
            if test_user:
                print(f"Testing with user: {test_user.username} (Role: {test_user.role}, Zone: {test_user.zone_id})")
                
                # Login
                login_response = client.post('/auth/login', data={
                    'username': test_user.username,
                    'password': 'password123'  # This might not match, but test anyway
                }, follow_redirects=True)
                
                # Try to access dashboard directly
                print("\n1. Testing GET /magasinier/tableau-de-bord")
                response = client.get('/magasinier/tableau-de-bord')
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("   ✓ Dashboard loads successfully")
                    # Check for broken urls
                    if b'stock.produits_zone' in response.data:
                        print("   ✗ Found broken url_for call: stock.produits_zone")
                    if b'stock.entrees_mois' in response.data:
                        print("   ✗ Found broken url_for call: stock.entrees_mois")
                    if b'/gestion-stock/produits-zone' in response.data:
                        print("   ✓ Found correct url: /gestion-stock/produits-zone")
                    if b'/gestion-stock/entrees-mois' in response.data:
                        print("   ✓ Found correct url: /gestion-stock/entrees-mois")
                else:
                    print(f"   ✗ Error {response.status_code}")
                    if response.data:
                        # Try to extract error message
                        try:
                            if b'Traceback' in response.data:
                                print("   Flask error detected in response")
                                # Extract just the error message
                                lines = response.data.decode('utf-8', errors='ignore').split('\n')
                                for line in lines[-10:]:
                                    if line.strip():
                                        print(f"   → {line[:100]}")
                        except:
                            pass
            else:
                print("✗ No magasinier user found in database")
    
    print("\n" + "="*70)

if __name__ == '__main__':
    test_magasinier_dashboard()
