from app import app
from extensions import db
from models import EmplacementStock, Zone

with app.app_context():
    print("--- Zones ---")
    for z in Zone.query.all():
        print(f"ID={z.id}, Name='{z.nom}', Code='{z.code}', Actif={z.actif}")
    
    print("\n--- Emplacements ---")
    for e in EmplacementStock.query.all():
        print(f"ID={e.id}, Code='{e.code}', Name='{e.designation}', ZoneID={e.zone_id}")
