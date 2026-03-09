#!/usr/bin/env python
"""
Script pour standardiser les noms de zone en format PascalCase
Dakar, Pikine, Mbour, Kaolack, Autres, Fatick
"""

import os
from dotenv import load_dotenv
from app import app, db
from models import Zone, User, Equipe

# Charger les variables d'environnement
load_dotenv()

# Mapping des noms de zone vers le format standardisé (PascalCase)
ZONE_MAPPING = {
    'dakar': 'Dakar',
    'DAKAR': 'Dakar',
    'Dakar': 'Dakar',
    'pikine': 'Pikine',
    'PIKINE': 'Pikine',
    'Pikine': 'Pikine',
    'mbour': 'Mbour',
    'MBOUR': 'Mbour',
    'Mbour': 'Mbour',
    'kaolack': 'Kaolack',
    'KAOLACK': 'Kaolack',
    'Kaolack': 'Kaolack',
    'autres': 'Autres',
    'AUTRES': 'Autres',
    'Autres': 'Autres',
    'fatick': 'Fatick',
    'FATICK': 'Fatick',
    'Fatick': 'Fatick',
}

def standardize_zones():
    """Standardiser les noms de zone dans la base de données"""
    with app.app_context():
        print("\n" + "="*60)
        print("STANDARDISATION DES NOMS DE ZONE")
        print("="*60 + "\n")
        
        # 1. Zones de la table 'zone'
        print("📋 TABLE ZONE")
        print("-" * 60)
        zones = Zone.query.all()
        for zone in zones:
            new_nom = ZONE_MAPPING.get(zone.nom, zone.nom)
            if zone.nom != new_nom:
                print(f"  ✏️  ID {zone.id}: '{zone.nom}' → '{new_nom}'")
                zone.nom = new_nom
        
        if zones:
            db.session.commit()
            print(f"✅ {len(zones)} zones mises à jour\n")
        
        # 2. Utilisateurs avec le champ 'zone' (legacy)
        print("👤 TABLE USER (champ 'zone')")
        print("-" * 60)
        users_with_zone = User.query.filter(User.zone != None).all()
        updated_users = 0
        
        for user in users_with_zone:
            original_zone = user.zone
            # Essayer de standardiser directement
            new_zone = ZONE_MAPPING.get(user.zone, user.zone)
            
            # Si pas trouvé directement, essayer sans espaces/majuscules
            if new_zone == user.zone:
                for key, val in ZONE_MAPPING.items():
                    if user.zone.lower().strip() == key.lower().strip():
                        new_zone = val
                        break
            
            if user.zone != new_zone:
                print(f"  ✏️  {user.username} ({user.role}): '{original_zone}' → '{new_zone}'")
                user.zone = new_zone
                updated_users += 1
        
        if updated_users > 0:
            db.session.commit()
            print(f"✅ {updated_users} utilisateurs mis à jour\n")
        else:
            print("  ℹ️  Aucune mise à jour nécessaire\n")
        
        # 3. Équipes avec le champ 'zone'
        print("👥 TABLE EQUIPE (champ 'zone')")
        print("-" * 60)
        equipes = Equipe.query.all()
        updated_equipes = 0
        
        for equipe in equipes:
            original_zone = equipe.zone
            # Extraire le nom si format "Nom (CODE)"
            if equipe.zone and '(' in equipe.zone:
                zone_name = equipe.zone.split('(')[0].strip()
                zone_code = equipe.zone.split('(')[1].rstrip(')')
            else:
                zone_name = equipe.zone
                zone_code = ""
            
            # Standardiser le nom
            new_zone_name = ZONE_MAPPING.get(zone_name, zone_name)
            
            # Reconstruire le format
            if zone_code:
                new_zone = f"{new_zone_name} ({zone_code})"
            else:
                new_zone = new_zone_name
            
            if equipe.zone != new_zone:
                print(f"  ✏️  {equipe.nom_equipe}: '{original_zone}' → '{new_zone}'")
                equipe.zone = new_zone
                updated_equipes += 1
        
        if updated_equipes > 0:
            db.session.commit()
            print(f"✅ {updated_equipes} équipes mises à jour\n")
        else:
            print("  ℹ️  Aucune mise à jour nécessaire\n")
        
        # Résumé final
        print("="*60)
        print("📊 RÉSUMÉ FINAL")
        print("="*60)
        
        print("\n🔍 État final des zones:")
        final_zones = Zone.query.all()
        for zone in final_zones:
            print(f"  ✅ {zone.id}: {zone.nom} ({zone.code})")
        
        print("\n✨ Standardisation terminée avec succès!")
        print("="*60 + "\n")

if __name__ == '__main__':
    standardize_zones()
