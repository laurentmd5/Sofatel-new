
import os
import sys
from datetime import date

# Add the app directory to sys.path
sys.path.append(os.getcwd())

from app import create_app, db
from models import Equipe, User

app = create_app()
with app.app_context():
    print(f"Today is: {date.today()}")
    
    total_equipes = Equipe.query.count()
    print(f"Total teams: {total_equipes}")
    
    active_equipes = Equipe.query.filter_by(actif=True).all()
    print(f"Active teams: {len(active_equipes)}")
    for e in active_equipes:
        print(f"  - ID: {e.id}, Name: {e.nom_equipe}, Zone: {e.zone}, Service: {e.service}, Publié: {e.publie}, Date Pub: {e.date_publication}")
    
    publiees_today = Equipe.query.filter_by(actif=True, publie=True, date_publication=date.today()).all()
    print(f"Published today: {len(publiees_today)}")
    for e in publiees_today:
        print(f"  - ID: {e.id}, Name: {e.nom_equipe}, Zone: {e.zone}")

    # Inspect current user role and zone (simulating chef_zone)
    # Let's say we check for 'magasinier' or 'chef_zone' users
    chefs = User.query.filter(User.role.in_(['chef_zone', 'chef_pilote'])).all()
    for c in chefs:
        print(f"Chef: {c.username}, Role: {c.role}, Zone: {c.zone}, Service: {c.service}")
