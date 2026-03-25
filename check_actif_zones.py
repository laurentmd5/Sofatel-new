from app import app
from models import Zone

with app.app_context():
    zones_all = Zone.query.all()
    print("ALL ZONES:", [(z.nom, z.actif) for z in zones_all])
    zones_actif = Zone.query.filter_by(actif=True).all()
    print("ACTIF ZONES:", [z.nom for z in zones_actif])
