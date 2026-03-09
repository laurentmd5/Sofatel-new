#!/usr/bin/env python
"""Test dashboard rendering avec authentification"""
from app import app
from flask import session
from models import User, db

with app.test_client() as client:
    with app.app_context():
        # Find a magasinier user
        user = User.query.filter_by(role='magasinier').first()
        
        if user:
            print(f"\nTesting with: {user.username}")
            print(f"Role: {user.role}, Zone: {user.zone_id}\n")
            
            # Simulate login by using Flask-Login's session
            with client.session_transaction() as sess:
                sess['user_id'] = user.id
                sess['_fresh'] = True
            
            # Test dashboard rendering
            print("Testing dashboard rendering...")
            response = client.get('/magasinier/tableau-de-bord')
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✓ Dashboard renders successfully\n")
                
                # Check for url_for errors
                html_content = response.data.decode('utf-8', errors='ignore')
                
                test_urls = [
                    ('/gestion-stock/produits-zone', 'Voir Tous les Produits'),
                    ('/gestion-stock/historique-mouvements-zone', 'Historique'),
                    ('/gestion-stock/entrees-mois', 'Entrees'),
                    ('/gestion-stock/sorties-mois', 'Sorties'),
                    ('/gestion-stock/produits-faibles-stocks', 'Produits Faibles'),
                ]
                
                print("Checking URLs in template:")
                for url, label in test_urls:
                    if url in html_content:
                        print(f"  ✓ Found: {url}")
                    else:
                        print(f"  ✗ Missing: {url}")
                
                # Check for template errors
                if 'Traceback' in html_content or 'error' in html_content.lower():
                    print("\n⚠ Potential errors in response")
                else:
                    print("\n✓ No errors detected in response")
            else:
                print(f"✗ Error {response.status_code}")
                if 'Traceback' in response.data.decode('utf-8', errors='ignore'):
                    print("✗ Flask error detected")
        else:
            print("No magasinier user found")
