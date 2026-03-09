#!/usr/bin/env python
"""Test que tous les endpoints existent et mappent correctement"""
from flask import url_for
from app import app

endpoints_to_test = [
    'stock.liste_produits_zone',
    'stock.page_entrees_mois',
    'stock.page_sorties_mois',
    'stock.inventaire_physique',
    'stock.page_produits_faibles_stocks',
    'stock.historique_mouvements_zone'
]

with app.app_context():
    # Create a test request context
    with app.test_request_context():
        print("\nVERIFICATION DES ENDPOINTS DU DASHBOARD MAGASINIER:\n")
        for endpoint in endpoints_to_test:
            try:
                url = url_for(endpoint)
                print(f"OK {endpoint:45} -> {url}")
            except Exception as e:
                print(f"ERROR {endpoint:45} -> {str(e)}")
        print("\n")
