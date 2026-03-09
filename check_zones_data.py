#!/usr/bin/env python3
"""
Script pour vérifier les données de zones en base et identifier les problèmes
"""
import sys
sys.path.insert(0, '/Users/Abdoul Niang/Downloads/backup')

from app import app
from models import Zone, User
from extensions import db

def check_zones():
    """Vérifier les zones actives et inactives"""
    with app.app_context():
        print("=" * 60)
        print("VÉRIFICATION DES ZONES")
        print("=" * 60)
        
        # Zones actives
        active_zones = Zone.query.filter_by(actif=True).order_by(Zone.nom).all()
        print(f"\n✓ Zones ACTIVES ({len(active_zones)}):")
        for zone in active_zones:
            print(f"  - ID: {zone.id}, Nom: {zone.nom}, Code: {zone.code}")
        
        # Zones inactives
        inactive_zones = Zone.query.filter_by(actif=False).order_by(Zone.nom).all()
        print(f"\n✗ Zones INACTIVES ({len(inactive_zones)}):")
        for zone in inactive_zones:
            print(f"  - ID: {zone.id}, Nom: {zone.nom}, Code: {zone.code}")
        
        # Utilisateurs avec zones legacy
        print(f"\n" + "=" * 60)
        print("VÉRIFICATION DES UTILISATEURS AVEC ZONES")
        print("=" * 60)
        
        users_with_zone_id = User.query.filter(User.zone_id != None).all()
        print(f"\nUtilisateurs avec zone_id (nouvelle méthode): {len(users_with_zone_id)}")
        for user in users_with_zone_id[:10]:  # Afficher les 10 premiers
            zone_obj = Zone.query.get(user.zone_id)
            print(f"  - {user.username}: zone_id={user.zone_id}, zone_name={zone_obj.nom if zone_obj else 'N/A'}")
        
        # Utilisateurs avec zones legacy (champ zone en string)
        users_with_zone_name = User.query.filter(User.zone != None).all()
        print(f"\nUtilisateurs avec zone (legacy): {len(users_with_zone_name)}")
        
        # Vérifier s'il y a des zones orphelines (zones dans le champ User.zone qui n'existent plus)
        print(f"\n" + "=" * 60)
        print("VÉRIFICATION DES ZONES ORPHELINES")
        print("=" * 60)
        
        # Récupérer tous les noms de zones uniques dans User.zone
        zone_names_in_users = db.session.query(User.zone).distinct().filter(User.zone != None).all()
        zone_names_in_users = [z[0] for z in zone_names_in_users]
        
        print(f"\nZones mentionnées dans User.zone: {len(zone_names_in_users)}")
        active_zone_names = [z.nom for z in active_zones]
        inactive_zone_names = [z.nom for z in inactive_zones]
        
        for zone_name in sorted(zone_names_in_users):
            if zone_name in active_zone_names:
                status = "✓ ACTIVE"
            elif zone_name in inactive_zone_names:
                status = "✗ INACTIVE"
            else:
                status = "⚠ INEXISTANTE"
            print(f"  - {zone_name}: {status}")

if __name__ == '__main__':
    check_zones()
