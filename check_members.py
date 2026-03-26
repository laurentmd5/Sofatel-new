from app import app, db
from models import Equipe, MembreEquipe, User

with app.app_context():
    equipes = Equipe.query.all()
    print(f"DEBUG_MEMBERS: Checking {len(equipes)} teams")
    for e in equipes:
        print(f"Team {e.nom_equipe}:")
        for m in e.membres:
            u = User.query.get(m.technicien_id) if m.technicien_id else None
            print(f" - Member type: {m.type_membre}, User: {u.username if u else 'N/A'}")
