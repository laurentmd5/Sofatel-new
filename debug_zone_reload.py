import sys
sys.path.insert(0, '.')

from app import app, db
from models import User, Zone
from datetime import date

with app.app_context():
    # Trouver un chef_zone
    chef_zone = User.query.filter_by(role='chef_zone').first()
    if not chef_zone:
        print("Aucun chef_zone trouvé")
        exit()
    
    print(f'Chef zone trouvé: {chef_zone.username} (id={chef_zone.id})')
    print(f'  zone actuel: {repr(chef_zone.zone)}')
    print(f'  zone_id actuel: {chef_zone.zone_id}')
    
    # Lister les zones disponibles
    zones = Zone.query.all()
    print(f'\nZones disponibles:')
    for z in zones:
        print(f'  {z.id}: {z.nom} ({z.code})')
    
    # Simuler une modification d'admin: changer la zone
    if len(zones) > 0:
        # Chercher une zone différente de celle actuelle
        new_zone = None
        for z in zones:
            if chef_zone.zone_id != z.id:
                new_zone = z
                break
        
        if new_zone:
            print(f'\nChangement de zone pour {chef_zone.username}:')
            print(f'  ancien zone_id: {chef_zone.zone_id}')
            print(f'  ancien zone: {chef_zone.zone_relation.nom if chef_zone.zone_relation else chef_zone.zone}')
            print(f'  nouvelle zone_id: {new_zone.id} ({new_zone.nom})')
            
            chef_zone.zone_id = new_zone.id
            db.session.commit()
            print(f'  OK Zone changee en BD')
            
            # Simuler le chargement du dashboard (on va rechargement force)
            fresh_user = User.query.get(chef_zone.id)
            print(f'\nApres rechargement force:')
            print(f'  fresh_user.zone_id: {fresh_user.zone_id}')
            print(f'  fresh_user.zone_relation: {fresh_user.zone_relation}')
            if fresh_user.zone_relation:
                print(f'    -> {fresh_user.zone_relation.nom} ({fresh_user.zone_relation.code})')
            
            # Determiner user_zone comme le fait le dashboard
            user_zone = None
            if fresh_user.zone_relation:
                user_zone = f"{fresh_user.zone_relation.nom} ({fresh_user.zone_relation.code})"
            elif fresh_user.zone:
                user_zone = fresh_user.zone
            print(f'  user_zone pour dashboard: {repr(user_zone)}')
            print(f'  OK Le dashboard affichera cette nouvelle zone!')
        else:
            print("Aucune autre zone disponible pour tester")
    else:
        print("Pas de zones disponibles")
