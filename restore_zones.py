#!/usr/bin/env python
"""Restaurer les zones originales du projet"""

from app import app, db
from models import Zone

with app.app_context():
    # Zones originales basées sur le code du projet
    zones_originales = [
        {'nom': 'Dakar', 'code': 'DK', 'region': 'Dakar'},
        {'nom': 'Mbour', 'code': 'MB', 'region': 'Thiès'},
        {'nom': 'Kaolack', 'code': 'KA', 'region': 'Kaolack'},
        {'nom': 'Autres', 'code': 'AU', 'region': 'Autres régions'},
    ]
    
    print("\n=== RESTAURATION DES ZONES ===\n")
    
    # Supprimer les zones existantes
    Zone.query.delete()
    db.session.commit()
    print("[OK] Zones existantes supprimées")
    
    # Insérer les zones originales
    for zone_data in zones_originales:
        zone = Zone(
            nom=zone_data['nom'],
            code=zone_data['code'],
            region=zone_data['region'],
            actif=True
        )
        db.session.add(zone)
    
    db.session.commit()
    print("[OK] Zones originales restaurées\n")
    
    # Afficher les zones
    zones = Zone.query.all()
    print("=== ZONES ACTUELLES ===\n")
    for z in zones:
        print(f"ID {z.id}: {z.nom:15} (CODE: {z.code:5}) [Region: {z.region}]")
    print()
