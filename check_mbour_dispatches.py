from app import app, db
from models import MouvementStock, EmplacementStock, Zone, Produit

with app.app_context():
    print("--- Zones ---")
    for z in Zone.query.all():
        print(f"ID={z.id}, Nom='{z.nom}'")
        
    print("\n--- Recent Mouvements (last 10) ---")
    mvts = MouvementStock.query.order_by(MouvementStock.id.desc()).limit(10).all()
    for m in mvts:
        emp = EmplacementStock.query.get(m.emplacement_id) if m.emplacement_id else None
        p = Produit.query.get(m.produit_id) if m.produit_id else None
        print(f"ID={m.id}, Type={m.type_mouvement}, Produit={p.nom if p else 'N/A'}, Emp={emp.code if emp else 'NONE'}, State={m.workflow_state}, ZoneID={emp.zone_id if emp else 'NONE'}")
        
    print("\n--- Emplacements for Mbour ---")
    mbour_zone = Zone.query.filter(Zone.nom.ilike('%mbour%')).first()
    if mbour_zone:
        print(f"Mbour Zone found with ID={mbour_zone.id}")
        emplacements = EmplacementStock.query.filter_by(zone_id=mbour_zone.id).all()
        for e in emplacements:
            print(f"  - Emplacement: ID={e.id}, Code={e.code}, Name={e.designation}")
    else:
        print("Mbour Zone not found!")
