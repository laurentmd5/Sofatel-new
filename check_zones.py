#!/usr/bin/env python
"""Vérifier les zones actuelles en base de données"""

from app import app, db
from models import Zone

with app.app_context():
    zones = Zone.query.all()
    print("\n=== ZONES ACTUELLES EN BASE ===\n")
    for z in zones:
        print(f"ID {z.id}: {z.nom:20} (CODE: {z.code:10}) [Actif: {z.actif}]")
    print(f"\nTotal: {len(zones)} zones\n")
