#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour corriger les utilisateurs chef_zone existants qui ont zone=NULL
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db
from models import User

def fix_existing_chef_zone_users():
    """Corrige les utilisateurs chef_zone existants qui ont zone=NULL mais zone_id valide"""
    with app.app_context():
        # Trouver tous les utilisateurs chef_zone qui ont zone_id mais zone=NULL
        users_to_fix = User.query.filter(
            User.role == 'chef_zone',
            User.zone_id.isnot(None),
            User.zone == None
        ).all()

        print(f"Trouvé {len(users_to_fix)} utilisateur(s) chef_zone à corriger")

        fixed_count = 0
        for user in users_to_fix:
            if user.zone_relation:
                # Assigner le nom de la zone au champ legacy
                user.zone = user.zone_relation.nom
                print(f"Correction: {user.username} -> zone='{user.zone}' (zone_id={user.zone_id})")
                fixed_count += 1
            else:
                print(f"⚠️  ATTENTION: {user.username} a zone_id={user.zone_id} mais pas de zone_relation!")

        if fixed_count > 0:
            db.session.commit()
            print(f"✅ {fixed_count} utilisateur(s) corrigé(s) avec succès!")
        else:
            print("ℹ️  Aucun utilisateur à corriger trouvé.")

        # Vérification finale
        still_broken = User.query.filter(
            User.role == 'chef_zone',
            User.zone_id.isnot(None),
            User.zone == None
        ).count()

        if still_broken == 0:
            print("✅ VÉRIFICATION: Tous les utilisateurs chef_zone ont maintenant une zone valide!")
        else:
            print(f"❌ PROBLÈME: {still_broken} utilisateur(s) toujours cassé(s)")

if __name__ == '__main__':
    fix_existing_chef_zone_users()