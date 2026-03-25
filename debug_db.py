from app import app, db
from models import Zone, EmplacementStock, MouvementStock, Produit
import sys

with app.app_context():
    print("--- ZONES ---")
    zones = Zone.query.all()
    for z in zones:
        print(f"ID={z.id}, NOM='{z.nom}', CODE='{z.code}'")
        
    print("\n--- EMPLACEMENTS ---")
    emplacements = EmplacementStock.query.all()
    for e in emplacements:
        print(f"ID={e.id}, CODE='{e.code}', DESIGNATION='{e.designation}', ZONE_ID={e.zone_id}")
        
    print("\n--- PENDING DISPATCHES ---")
    dispatches = MouvementStock.query.filter_by(
        type_mouvement='entree', 
        workflow_state='EN_ATTENTE'
    ).all()
    
    if not dispatches:
        print("AUCUN TRANSFERT EN ATTENTE DANS LA BASE")
    else:
        for m in dispatches:
            e = EmplacementStock.query.get(m.emplacement_id) if m.emplacement_id else None
            p = Produit.query.get(m.produit_id) if m.produit_id else None
            print(f"ID={m.id}, Produit={p.ref if p else 'N/A'}, Qty={m.quantite}, EmpID={m.emplacement_id}, EmpZoneID={e.zone_id if e else 'NONE'}")
