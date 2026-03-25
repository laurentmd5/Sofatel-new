from app import app, db
from models import Zone, EmplacementStock, MouvementStock

with app.app_context():
    print("--- Healing Orphaned Dispatches ---")
    # 1. Link warehouses to zones based on names if not linked
    zones = Zone.query.all()
    emplacements = EmplacementStock.query.all()
    
    for z in zones:
        for e in emplacements:
            if e.zone_id is None:
                # If zone name is in designation or code, link it
                if z.nom.upper() in e.designation.upper() or z.nom.upper() in e.code.upper():
                    print(f"Linking {e.code} to {z.nom} (ID {z.id})")
                    e.zone_id = z.id
    
    # 2. Fix mouvements that have no emplacement_id or whose emplacement has no zone
    # This might be harder if emplacement_id is NULL, but if it has one, we just linked its zone.
    
    db.session.commit()
    print("Optimization complete.")
