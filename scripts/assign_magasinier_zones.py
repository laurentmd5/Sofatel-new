"""
SCRIPT: Assigner zones par défaut aux magasiniers orphans

Ce script assigne une zone par défaut (Dakar/zone_id=3) à tous les magasiniers 
qui n'ont pas de zone_id assignée.

Usage:
    python scripts/assign_magasinier_zones.py
"""

from app import app, db
from models import User, Zone
import sys

def main():
    """Assigner zones aux magasiniers orphans"""
    
    with app.app_context():
        # Récupérer zone Dakar (id=3)
        dakar = Zone.query.filter_by(code='DK').first()
        if not dakar:
            print("❌ Erreur: Zone Dakar (code DK) non trouvée")
            sys.exit(1)
        
        print(f"✅ Zone Dakar trouvée: {dakar.nom} (ID: {dakar.id})")
        
        # Trouver magasiniers orphans
        orphans = User.query.filter_by(role='magasinier').filter(User.zone_id == None).all()
        print(f"\n📊 Magasiniers sans zone: {len(orphans)}")
        
        if not orphans:
            print("✅ Aucun magasinier orphan trouvé. Fin du script.")
            return
        
        # Afficher les magasiniers qui vont être mis à jour
        print("\n📋 Magasiniers à mettre à jour:")
        for mag in orphans:
            print(f"  - {mag.username} ({mag.prenom} {mag.nom})")
        
        # Assigner zone par défaut
        count = 0
        for mag in orphans:
            mag.zone_id = dakar.id
            count += 1
        
        try:
            db.session.commit()
            print(f"\n✅ {count} magasiniers assignés à zone: {dakar.nom}")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erreur lors de la mise à jour: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()
