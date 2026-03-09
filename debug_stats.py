import sys
sys.path.insert(0, '.')

from app import app, db
from models import User, Equipe
from utils import get_chef_zone_stats
from datetime import date

with app.app_context():
    cz = User.query.filter_by(role='chef_zone').first()
    print(f'Chef zone: {cz.username} (id={cz.id})')
    print(f'- zone: {repr(cz.zone)}')
    print()
    
    # Voir ses équipes publiées
    today = date.today()
    published = Equipe.query.filter_by(chef_zone_id=cz.id, publie=True, date_publication=today, actif=True).all()
    print(f'Équipes du chef_zone publiées AUJOURD\'HUI:')
    for e in published:
        print(f'  - {e.nom_equipe} (zone={repr(e.zone)})')
    print()
    
    # Appeler get_chef_zone_stats avec sa zone
    print('Appel get_chef_zone_stats avec zone:', repr(cz.zone))
    stats = get_chef_zone_stats(cz.zone)
    print('Stats retournées:')
    print(f'  equipes_jour: {stats["equipes_jour"]}')
    print(f'  techniciens_zone: {stats["techniciens_zone"]}')
