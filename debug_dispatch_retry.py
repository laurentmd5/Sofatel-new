import os
from datetime import date
from flask import Flask
from extensions import db
from models import Equipe, DemandeIntervention, User, Intervention, MembreEquipe
from utils import is_technicien_compatible
from routes.dispatch import normalize_zone_local
from app import app

with app.app_context():
    today = date.today()
    print(f"--- Debug Dispatch Full {today} ---")
    
    # 1. Equipes
    equipes = Equipe.query.filter_by(actif=True, publie=True, date_publication=today).all()
    print(f"Equipes publiées aujourd'hui: {len(equipes)}")
    
    # 2. Demandes
    demandes = DemandeIntervention.query.filter(
        DemandeIntervention.statut.in_(['nouveau', 'a_reaffecter'])
    ).all()
    print(f"Demandes en attente: {len(demandes)}")
    
    # 3. Detailed Check
    for e in equipes:
        print(f"\nEquipe: {e.nom_equipe} | Zone: {e.zone} | Service: {e.service}")
        membre_tech = next((m for m in e.membres if m.type_membre == 'technicien'), None)
        if not membre_tech:
            print(" ! Pas de technicien")
            continue
            
        tech = User.query.get(membre_tech.technicien_id)
        if not tech: continue
        print(f" > Tech: {tech.username} | Technologies: {tech.technologies}")
        
        # Busy?
        busy = Intervention.query.filter(
            Intervention.technicien_id == tech.id,
            Intervention.statut.in_(['en_cours', 'affecte', 'nouveau'])
        ).first()
        if busy:
            print(f" ! Occupé par interv {busy.id} (Statut: {busy.statut})")
            continue
            
        tz = normalize_zone_local(e.zone)
        ts = [s.strip().upper() for s in (e.service or '').split(',')]
        
        for d in demandes[:20]: # Check first 20
            dz = normalize_zone_local(d.zone)
            ds = (d.service or '').strip().upper()
            
            z_m = (tz == dz)
            s_m = (ds in ts)
            t_m = is_technicien_compatible(tech, d)
            
            if z_m and s_m and t_m:
                print(f" [V] MATCH: Demand {d.nd}")
                break
            # else:
            #    print(f"  X D:{d.nd} | Z:{z_m}({tz} vs {dz}) | S:{s_m}({ds}) | T:{t_m}({d.type_techno})")
