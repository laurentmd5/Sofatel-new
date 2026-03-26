from app import create_app, db
from models import Equipe, DemandeIntervention, User, Intervention
from routes.dispatch import normalize_zone_local
from utils import is_technicien_compatible
from datetime import date

app = create_app()
with app.app_context():
    today = date.today()
    print(f"--- Debug Dispatch Logic {today} ---")
    
    equipes = Equipe.query.filter_by(actif=True, publie=True, date_publication=today).all()
    print(f"Nombre d'équipes publiées: {len(equipes)}")
    
    demandes = DemandeIntervention.query.filter(
        DemandeIntervention.statut.in_(['nouveau', 'a_reaffecter'])
    ).all()
    print(f"Nombre de demandes en attente: {len(demandes)}")
    
    if not equipes:
        # Check all active teams date_publication
        all_teams = Equipe.query.filter_by(actif=True).all()
        for t in all_teams:
            print(f" - Team {t.nom_equipe}: Pub={t.publie}, DatePub={t.date_publication}")

    for e in equipes:
        print(f"\nAnalyse équipe: {e.nom_equipe} (Zone: {e.zone}, Service: {e.service})")
        membre_tech = next((m for m in e.membres if m.type_membre == 'technicien'), None)
        if not membre_tech:
            print(" ! Aucun technicien dans l'équipe")
            continue
        
        tech = User.query.get(membre_tech.technicien_id)
        if not tech:
            print(f" ! Technicien ID {membre_tech.technicien_id} introuvable")
            continue
        
        print(f" > Technicien: {tech.username} (Techs: {tech.technologies})")
        
        # Check busy
        busy = Intervention.query.filter(
            Intervention.technicien_id == tech.id,
            Intervention.statut.in_(['en_cours', 'affecte', 'nouveau'])
        ).first()
        if busy:
            print(f" ! Occupé par intervention {busy.id} (Statut: {busy.statut})")
            continue

        team_zone = normalize_zone_local(e.zone)
        team_services = [s.strip().upper() for s in (e.service or '').split(',')]
        
        match_found = False
        for d in demandes:
            demand_zone = normalize_zone_local(d.zone)
            demand_service = (d.service or '').strip().upper()
            
            zone_match = (team_zone == demand_zone)
            service_match = (demand_service in team_services)
            tech_match = is_technicien_compatible(tech, d)
            
            if zone_match and service_match and tech_match:
                print(f" [V] MATCH POSSIBLE avec demande {d.nd}")
                match_found = True
                break
            else:
                # Log why it failed for the first 5 demands of each team
                if not match_found:
                    print(f"  ? Demande {d.nd}: Zone={zone_match}({team_zone} vs {demand_zone}), Service={service_match}({demand_service} in {team_services}), Tech={tech_match}({d.type_techno})")
            
            # Limit demand check to avoid huge logs
            if not match_found and len(demandes) > 10:
                pass 

        if not match_found:
            print(" ! Aucun match trouvé pour cette équipe")
