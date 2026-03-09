import sys
sys.path.insert(0, '.')

from app import app, db
from models import User, Equipe
from datetime import date

with app.app_context():
    # Trouver l'utilisateur avec id=1
    user_1 = User.query.get(1)
    if user_1:
        print(f'Utilisateur id=1: {user_1.username}, role: {user_1.role}, zone: {repr(user_1.zone)}')

    # Trouver un chef_zone
    chef_zone = User.query.filter_by(role='chef_zone').first()
    if chef_zone:
        print(f'Chef zone trouvé: {chef_zone.username} (id={chef_zone.id})')
        print(f'chef_zone.zone: {repr(chef_zone.zone)}')

        # Voir les équipes avec chef_zone_id=1
        equipes_user_1 = Equipe.query.filter_by(chef_zone_id=1).all()
        print(f'Équipes avec chef_zone_id=1: {len(equipes_user_1)}')
        for equipe in equipes_user_1:
            print(f'  Équipe: {equipe.nom_equipe}, zone: {repr(equipe.zone)}, publie: {equipe.publie}')

        # Tester si le chef_zone peut voir ces équipes
        print(f'Le chef_zone actuel (id={chef_zone.id}) peut-il voir les équipes de l\'utilisateur 1 ? {chef_zone.id == 1}')

    else:
        print('Aucun chef_zone trouvé')
