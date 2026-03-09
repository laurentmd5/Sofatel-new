#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour tester la création d'un utilisateur chef_zone avec zone
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db
from models import User, Zone
from werkzeug.security import generate_password_hash

def test_create_chef_zone():
    with app.app_context():
        # Vérifier qu'une zone existe
        zone = Zone.query.first()
        if not zone:
            print("ERREUR: Aucune zone trouvée dans la base de données")
            return

        print(f"Zone disponible: ID={zone.id}, Nom={zone.nom}")

        # Créer un nouvel utilisateur chef_zone
        username = "test_chef_zone_fix"
        existing = User.query.filter_by(username=username).first()
        if existing:
            print(f"Utilisateur {username} existe déjà, suppression...")
            db.session.delete(existing)
            db.session.commit()

        print(f"Création de l'utilisateur {username}...")

        new_user = User(
            username=username,
            email=f"{username}@test.com",
            password_hash=generate_password_hash("password123"),
            role="chef_zone",
            nom="Test",
            prenom="Chef Zone",
            telephone="771234567",
            zone=zone.nom,  # Champ legacy
            zone_id=zone.id,  # FK
            actif=True
        )

        db.session.add(new_user)
        db.session.commit()

        # Vérifier les données
        user = User.query.filter_by(username=username).first()
        if user:
            print("✅ Utilisateur créé avec succès:")
            print(f"   Username: {user.username}")
            print(f"   Rôle: {user.role}")
            print(f"   Zone (string): {user.zone}")
            print(f"   Zone ID: {user.zone_id}")
            if user.zone_relation:
                print(f"   Zone relation nom: {user.zone_relation.nom}")
            else:
                print("   ❌ Zone relation: None")

            # Vérifier que les deux champs sont remplis
            if user.zone and user.zone_id:
                print("✅ SUCCÈS: Les deux champs zone sont correctement remplis!")
            else:
                print("❌ ÉCHEC: Un des champs zone est NULL")
        else:
            print("❌ ERREUR: Utilisateur non trouvé après création")

if __name__ == '__main__':
    test_create_chef_zone()