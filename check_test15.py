#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour vérifier les données de l'utilisateur test15
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db
from models import User

def check_user_test15():
    with app.app_context():
        user = User.query.filter_by(username='test15').first()
        if user:
            print(f'Utilisateur trouvé: {user.username}')
            print(f'Rôle: {user.role}')
            print(f'Zone (string): {user.zone}')
            print(f'Zone ID: {user.zone_id}')
            if user.zone_relation:
                print(f'Zone relation nom: {user.zone_relation.nom}')
            else:
                print('Zone relation: None')
        else:
            print('Utilisateur test15 non trouvé')

if __name__ == '__main__':
    check_user_test15()