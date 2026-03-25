from app import app, db
from models import Zone, EmplacementStock, MouvementStock, Produit
import os

with app.app_context():
    output = []
    output.append("--- ZONES ---")
    zones = Zone.query.all()
    for z in zones:
        output.append(f"ID={z.id}, NOM='{z.nom}', CODE='{z.code}'")
        
    output.append("\n--- EMPLACEMENTS ---")
    emplacements = EmplacementStock.query.all()
    for e in emplacements:
        output.append(f"ID={e.id}, CODE='{e.code}', DESIGNATION='{e.designation}', ZONE_ID={e.zone_id}")
        
    output.append("\n--- PENDING DISPATCHES ---")
    # Fetch dispatches (type='entree', workflow_state='EN_ATTENTE')
    dispatches = MouvementStock.query.filter_by(
        type_mouvement='entree', 
        workflow_state='EN_ATTENTE'
    ).all()
    
    for m in dispatches:
        p = Produit.query.get(m.produit_id)
        e = EmplacementStock.query.get(m.emplacement_id) if m.emplacement_id else None
        output.append(f"ID={m.id}, Produit='{p.nom if p else 'N/A'}', Qty={m.quantite}, EmpID={m.emplacement_id}, EmpCode='{e.code if e else 'NONE'}', EmpZoneID={e.zone_id if e else 'NONE'}")

    with open('db_report.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))

print(f"Report written to db_report.txt in {os.getcwd()}")
