from app import create_app, db
from models import Equipe, DemandeIntervention, Intervention, User
from datetime import date

app = create_app()
with app.app_context():
    today = date.today()
    print(f"--- Debug Auto Dispatch {today} ---")
    
    # 1. Check published teams
    equipes = Equipe.query.filter_by(actif=True, publie=True, date_publication=today).all()
    print(f"Equipes publiées aujourd'hui: {len(equipes)}")
    for e in equipes:
        membre_tech = next((m for m in e.membres if m.type_membre == 'technicien'), None)
        tech_id = membre_tech.technicien_id if membre_tech else "Inconnu"
        
        # Check busy status
        busy = Intervention.query.filter(
            Intervention.technicien_id == tech_id,
            Intervention.statut.in_(['en_cours', 'affecte'])
        ).first()
        
        print(f" - Equipe: {e.nom_equipe}, Zone: {e.zone}, Service: {e.service}, Tech: {tech_id}, Occupé: {'OUI' if busy else 'NON'}")

    # 2. Check pending demands
    demandes = DemandeIntervention.query.filter(
        DemandeIntervention.statut.in_(['nouveau', 'a_reaffecter'])
    ).all()
    print(f"Demandes en attente: {len(demandes)}")
    if demandes:
        for d in demandes[:5]:
            print(f" - Demande ID: {d.id}, ND: {d.nd}, Zone: {d.zone}, Service: {d.service}")
            
    # 3. Test zone matching
    def simple_match_zone(team_zone, demand_zone):
        tz = (team_zone or '').upper()
        dz = (demand_zone or '').upper()
        return (tz == dz) or (tz in dz) or (dz in tz)

    if equipes and demandes:
        print("\nTest Match:")
        for e in equipes:
            for d in demandes:
                match = simple_match_zone(e.zone, d.zone)
                if match:
                    print(f"Match trouvé! Equipe Zone [{e.zone}] vs Demande Zone [{d.zone}]")
                    break
