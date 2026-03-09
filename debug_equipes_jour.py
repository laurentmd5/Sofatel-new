import sys
sys.path.insert(0, '.')

from app import app, db
from models import User, Equipe
from datetime import date

with app.app_context():
    cz = User.query.filter_by(role='chef_zone').first()
    print(f'Chef zone: {cz.username} (id={cz.id})')
    print(f'- zone: {repr(cz.zone)}')
    print(f'- zone_id: {cz.zone_id}')
    print(f'- zone_relation: {cz.zone_relation}')
    print()
    
    # Voir toutes ses équipes
    all_equipes = Equipe.query.filter_by(chef_zone_id=cz.id).all()
    print(f'Total équipes du chef_zone: {len(all_equipes)}')
    for e in all_equipes:
        print(f'  - {e.nom_equipe}')
        print(f'    zone={repr(e.zone)}, publie={e.publie}, date_pub={e.date_publication}, actif={e.actif}')
    print()
    
    # Publier une si non publiée
    unpublished = [e for e in all_equipes if not e.publie]
    if unpublished:
        e = unpublished[0]
        print(f'Publication de: {e.nom_equipe}')
        e.publie = True
        e.date_publication = date.today()
        db.session.commit()
        print(f'  -> publie={e.publie}, date_publication={e.date_publication}')
    print()
    
    # Simuler la logique de get_equipes_jour
    today = date.today()
    user_zone = cz.zone  # "Dakar"
    print(f'Recherche équipes du jour pour chef_zone:')
    print(f'  user_zone = {repr(user_zone)}')
    print(f'  today = {today}')
    print(f'  Filtre: chef_zone_id={cz.id}, zone={repr(user_zone)}, publie=True, date_publication={today}, actif=True')
    
    equipes = Equipe.query.filter_by(
        chef_zone_id=cz.id,
        zone=user_zone,
        publie=True,
        date_publication=today,
        actif=True
    ).all()
    print(f'  Résultat: {len(equipes)} équipes')
    for e in equipes:
        print(f'    - {e.nom_equipe}')
