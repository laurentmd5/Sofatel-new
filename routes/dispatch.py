"""
Module dispatch — gestion des demandes d'intervention (import, dispatching, affectation).
Routes : /import-demandes, /dispatching, /affecter-demande, /dispatching-automatique, /api/demande/*
"""

import os
from datetime import datetime, date, timezone
import pandas as pd
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app, Blueprint, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from forms import ImportDemandesForm
from models import DemandeIntervention, FichierImport, Intervention, MembreEquipe, User, Equipe
from utils import log_activity, process_excel_file, is_technicien_compatible, send_email, create_sms_notification
from sqlalchemy.exc import OperationalError
from extensions import csrf


dispatch_bp = Blueprint('dispatch', __name__)


@dispatch_bp.route('/import-demandes', methods=['GET', 'POST'])
@login_required
def import_demandes():
    """Import Excel des demandes d'intervention."""
    if current_user.role not in ['chef_pur', 'chef_pilote', 'chef_zone']:
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('dashboard'))

    # Déterminer les choix de service disponibles
    if current_user.role == 'chef_pilote':
        if current_user.service == 'SAV,Production':
            service_choices = [('SAV', 'SAV'), ('Production', 'Production')]
            default_service = None
        else:
            service_choices = [(current_user.service, current_user.service)]
            default_service = current_user.service
    else:
        service_choices = [('SAV', 'SAV'), ('Production', 'Production')]
        default_service = None

    form = ImportDemandesForm(service_choices=service_choices, default_service=default_service)

    if form.validate_on_submit():
        try:
            fichier = form.fichier_excel.data
            filename = secure_filename(fichier.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            fichier.save(filepath)

            result = process_excel_file(filepath, form.service.data, current_user.id)

            if result['success']:
                # ✨ NOUVEAU: Lancer le dispatching automatique pour les demandes importées
                auto_count = auto_dispatch_logic()
                
                log_activity(
                    user_id=current_user.id,
                    action='import',
                    module='demandes',
                    entity_name=f"Import {filename}",
                    details={
                        'nb_lignes': result['nb_lignes'],
                        'service': form.service.data,
                        'fichier': filename,
                        'auto_dispatched': auto_count
                    }
                )
                msg = f"Import réussi: {result['nb_lignes']} demandes importées."
                if auto_count > 0:
                    msg += f" {auto_count} interventions ont été affectées automatiquement aux équipes disponibles."
                flash(msg, 'success')
            else:
                flash(f"Erreur lors de l'import: {result['error']}", 'error')

        except Exception as e:
            current_app.logger.exception('Error processing import file')
            
            # Provide user-friendly error message
            error_msg = str(e).lower()
            if 'permission' in error_msg or 'denied' in error_msg:
                user_msg = 'Problème de permission. Vérifiez les droits d\'accès au fichier.'
            elif 'format' in error_msg or 'encoding' in error_msg:
                user_msg = 'Format de fichier invalide. Utilisez un fichier CSV ou Excel valide.'
            elif 'field' in error_msg or 'column' in error_msg:
                user_msg = 'Erreur technique de base de données. Contactez l\'administrateur.'
            else:
                user_msg = 'Une erreur est survenue lors du traitement du fichier. Vérifiez son format et réessayez.'
            
            flash(user_msg, 'error')

    page = request.args.get('imports_page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    if current_user.role in ['chef_pur', 'chef_pilote']:
        imports = FichierImport.query.filter_by(actif=True).order_by(
            FichierImport.date_import.desc()).paginate(page=page, per_page=per_page, error_out=False)
    else:
        imports = FichierImport.query.filter_by(
            importe_par=current_user.id, actif=True).order_by(
                FichierImport.date_import.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return render_template('import_demandes.html', form=form, imports=imports)


@dispatch_bp.route('/dispatching')
@login_required
def dispatching():
    """Page de dispatching — affectation des demandes aux techniciens."""
    if current_user.role not in ['chef_pur', 'chef_pilote', 'chef_zone']:
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('dashboard'))

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 25, type=int), 100)

    age_filter = request.args.get('age')
    offre_filter = request.args.get('offre')
    priorite_filter = request.args.get('priorite_traitement')
    technologie_filter = request.args.get('technologie')
    zone_filter = request.args.get('zone')

    query = DemandeIntervention.query.filter(
        DemandeIntervention.statut.in_(['nouveau', 'a_reaffecter', 'reporte'])
    )

    if current_user.role == 'chef_pilote' and current_user.service:
        if current_user.service == 'SAV,Production':
            query = query.filter(DemandeIntervention.service.in_(['SAV', 'Production']))
        else:
            query = query.filter_by(service=current_user.service)

    if current_user.role == 'chef_zone' and current_user.zone:
        query = query.filter_by(zone=current_user.zone)

    if age_filter:
        query = query.filter_by(age=age_filter)
    if offre_filter:
        query = query.filter_by(offre=offre_filter)
    if priorite_filter:
        query = query.filter_by(priorite_traitement=priorite_filter)
    if technologie_filter:
        query = query.filter_by(type_techno=technologie_filter)
    if zone_filter:
        query = query.filter_by(zone=zone_filter)

    try:
        demandes_paginated = query.order_by(
            DemandeIntervention.priorite_traitement.desc(),
            DemandeIntervention.date_demande_intervention.asc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        techniciens = User.query.filter_by(role='technicien', actif=True).all()

        # Récupérer les équipes actives
        # On filtre par service si l'utilisateur est un chef pilote (sauf s'il gère les deux)
        equipes_query = Equipe.query.filter_by(actif=True)
        if current_user.role == 'chef_pilote' and current_user.service and current_user.service != 'SAV,Production':
            equipes_query = equipes_query.filter_by(service=current_user.service)
            
        today = date.today()
        equipes = equipes_query.order_by(
            Equipe.publie.desc(), 
            Equipe.date_publication.desc(),
            Equipe.date_creation.desc()
        ).all()
        
        # On garde une trace des équipes publiées aujourd'hui
        equipes_publiees = [e for e in equipes if e.publie and e.date_publication == today]
    except OperationalError as e:
        # Likely DB schema mismatch (missing columns added recently). Log and show friendly message.
        current_app.logger.exception('Database OperationalError in dispatching: possibly missing columns')
        flash('Erreur base de données: schéma incomplet. Veuillez exécuter les migrations (voir IMPROVEMENTS.md).', 'danger')
        class _EmptyPage:
            def __init__(self):
                self.items = []
                self.total = 0
                self.pages = 0
                self.page = page
                self.has_prev = False
                self.has_next = False
        demandes_paginated = _EmptyPage()
        techniciens = []
        equipes = []

    def normalize_zone(zone):
        z = (zone or '').upper()
        if any(x in z for x in ['MBOUR', 'KAOLACK', 'FATICK']):
            if 'MBOUR' in z:
                return 'MBOUR'
            if 'KAOLACK' in z:
                return 'KAOLACK'
            if 'FATICK' in z:
                return 'FATICK'
        return 'DAKAR'

    techniciens_json = [{
        'id': t.id,
        'prenom': t.prenom,
        'nom': t.nom,
        'technologies': t.technologies,
        'zone': normalize_zone(t.zone)
    } for t in techniciens]

    equipes_json = [{
        'id': e.id,
        'nom_equipe': f"★ {e.nom_equipe}" if e.publie and e.date_publication == today else e.nom_equipe,
        'zone': normalize_zone(e.zone),
        'technologies': e.technologies,
        'service': e.service,
        'publie_aujourdhui': e.publie and e.date_publication == today,
        'membres': [
            {
                'id': m.id,
                'nom': m.nom,
                'prenom': m.prenom,
                'technicien_id': m.technicien_id,
                'telephone': m.telephone,
                'type_membre': m.type_membre
            } for m in e.membres
        ]
    } for e in equipes]

    return render_template('dispatching.html',
                           demandes=demandes_paginated,
                           techniciens=techniciens_json,
                           techniciens_json=techniciens_json,
                           equipes=equipes,
                           equipes_json=equipes_json)


@dispatch_bp.route('/api/demande/<int:demande_id>')
@login_required
def get_demande_detail(demande_id):
    """API endpoint — récupère les détails d'une demande d'intervention."""
    demande = db.session.get(DemandeIntervention, demande_id)
    if not demande:
        abort(404)
    
    # ✅ NOUVEAU: Vérifier l'accès selon le rôle
    if current_user.role == 'technicien':
        # Technicien ne peut voir que si la demande lui est affectée
        if demande.technicien_id != current_user.id:
            return jsonify({'error': 'Accès non autorisé'}), 403
    elif current_user.role == 'chef_zone':
        # Chef zone voit seulement les demandes de sa zone
        if demande.zone != current_user.zone:
            return jsonify({'error': 'Accès non autorisé'}), 403
    elif current_user.role == 'chef_pilote':
        # Chef pilote voit seulement les demandes de son service
        if demande.service != current_user.service:
            return jsonify({'error': 'Accès non autorisé'}), 403
    elif current_user.role not in ['chef_pur', 'admin']:
        # Autres rôles : pas d'accès
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    return jsonify({
        'success': True,
        'demande': {
            'id': demande.id,
            'nd': demande.nd,
            'nom_client': demande.nom_client,
            'prenom_client': demande.prenom_client or '',
            'zone': demande.zone,
            'service': demande.service or '',
            'type_techno': demande.type_techno or '',
            'statut': demande.statut,
            'date_demande': demande.date_demande_intervention.isoformat() if demande.date_demande_intervention else None
        }
    })


@dispatch_bp.route('/affecter-demande', methods=['POST'])
@login_required
def affecter_demande():
    """Affecte une demande d'intervention à un technicien."""
    if current_user.role not in ['chef_pur', 'chef_pilote', 'chef_zone']:
        return jsonify({'success': False, 'error': 'Accès non autorisé'})

    try:
        print("Données reçues:", request.json)  # Debug
        demande_id = request.json.get('demande_id')
        technicien_id = request.json.get('technicien_id')
        equipe_id = request.json.get('equipe_id')
        mode = request.json.get('mode', 'manuel')  # manuel ou automatique

        if not demande_id:
            return jsonify({
                'success': False,
                'error': 'ID de demande manquant'
            })
        if not technicien_id:
            return jsonify({
                'success': False,
                'error': 'ID de technicien manquant'
            })

        demande = db.session.get(DemandeIntervention, demande_id)
        if not demande:
            return jsonify({'success': False, 'error': 'Demande non trouvée'})

        # Vérifications de compatibilité
        technicien = db.session.get(User, technicien_id)
        if not technicien or technicien.role != 'technicien':
            return jsonify({
                'success': False,
                'error': 'Technicien non valide'
            })

        # Vérifier la compatibilité technologique
        if not is_technicien_compatible(technicien, demande):
            tech_list = technicien.technologies or 'Aucune'
            return jsonify({
                'success': False,
                'error': f'Incompatibilité: Le technicien {technicien.prenom} {technicien.nom} possède les technologies [{tech_list}] mais la demande requiert [{demande.type_techno}]'
            })

        # Gestion des réaffectations
        intervention_existante = None
        if demande.statut == 'a_reaffecter':
            # Rechercher l'intervention rejetée pour cette demande
            intervention_existante = Intervention.query.filter_by(
                demande_id=demande_id, statut='rejete'
            ).order_by(Intervention.date_debut.desc()).first()  # Prendre la plus récente si plusieurs
            
            if intervention_existante:
                # Remettre l'intervention à 'en_cours' et changer le technicien
                intervention_existante.statut = 'en_cours'
                intervention_existante.technicien_id = technicien_id
                intervention_existante.date_debut = datetime.now(timezone.utc)
                if equipe_id:
                    intervention_existante.equipe_id = equipe_id
                print(f"Intervention {intervention_existante.id} remise à 'en_cours' pour réaffectation")
            else:
                print("Aucune intervention rejetée trouvée pour cette demande réaffectée")

        # Affecter la demande
        demande.technicien_id = technicien_id
        demande.statut = 'affecte'
        demande.date_affectation = datetime.now(timezone.utc)

        # Créer une nouvelle intervention seulement si ce n'est pas une réaffectation ou si aucune intervention existante
        if not intervention_existante:
            intervention = Intervention(demande_id=demande_id,
                                        technicien_id=technicien_id,
                                        equipe_id=equipe_id if equipe_id else None,
                                        date_debut=datetime.now(timezone.utc),
                                        statut='en_cours')
            db.session.add(intervention)
            print(f"Nouvelle intervention créée pour demande {demande_id}")

        db.session.commit()
        
        # Post-commit actions (logging and notifications) should not crash the main flow
        try:
            log_activity(
                user_id=current_user.id,
                action='assign',
                module='demandes',
                entity_id=demande.id,
                entity_name=f"Demande {demande.nd}",
                details={
                    'technicien': f"{technicien.prenom} {technicien.nom}",
                    'zone': demande.zone,
                    'service': demande.service,
                    'type_techno': demande.type_techno,
                    'reaffectation': demande.statut == 'a_reaffecter'
                }
            )
            
            # Envoyer notification SMS (simulé)
            create_sms_notification(technicien_id, demande_id, 'affectation')

            # Envoyer email au technicien
            subject = "Nouvelle intervention affectée"
            recipients = [technicien.email] if technicien.email else []
            body = f"Bonjour {technicien.prenom},\n\nVous avez une nouvelle intervention affectée :\nND : {demande.nd}\nClient : {demande.nom_client} {demande.prenom_client}\nZone : {demande.zone}\n\nMerci de consulter votre espace Sofatelcom."
            send_email(subject, recipients, body=body)
        except Exception as post_e:
            current_app.logger.warning(f"Post-assignment background tasks failed for demand {demande_id}: {str(post_e)}")

        return jsonify({
            'success': True,
            'message': 'Demande affectée avec succès'
        })

    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de l'affectation: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


def auto_dispatch_logic(demande_ids=None):
    """Logique de dispatching automatique des demandes aux équipes disponibles."""
    today = date.today()
    
    # 1. Récupérer les demandes à dispatcher
    query = DemandeIntervention.query.filter(
        DemandeIntervention.statut.in_(['nouveau', 'a_reaffecter'])
    )
    if demande_ids:
        query = query.filter(DemandeIntervention.id.in_(demande_ids))
    
    demandes = query.order_by(
        DemandeIntervention.priorite_traitement.desc(),
        DemandeIntervention.date_demande_intervention.asc()
    ).all()
    
    if not demandes:
        return 0

    # 2. Récupérer les équipes publiées aujourd'hui
    # On reste sur aujourd'hui car une équipe "publiée" l'est pour la journée
    equipes = Equipe.query.filter_by(
        actif=True, 
        publie=True, 
        date_publication=today
    ).all()
    
    if not equipes:
        print(f"DEBUG: Aucune équipe publiée pour aujourd'hui ({today})")
        return 0

    assigned_count = 0
    
    # helper pour la zone — identique à la logique du dispatching
    def normalize_zone_local(zone):
        z = (zone or '').upper()
        if any(x in z for x in ['MBOUR', 'KAOLACK', 'FATICK']):
            if 'MBOUR' in z: return 'MBOUR'
            if 'KAOLACK' in z: return 'KAOLACK'
            if 'FATICK' in z: return 'FATICK'
        return 'DAKAR'

    for equipe in equipes:
        # Trouver le technicien de l'équipe
        membre_tech = next((m for m in equipe.membres if m.type_membre == 'technicien'), None)
        
        # S'il n'y a pas de membre marqué 'technicien', on prend le premier membre si l'équipe n'en a qu'un
        # (Cas où l'utilisateur a créé l'équipe sans spécifier explicitement les rôles internes)
        if not membre_tech and len(equipe.membres) == 1:
            membre_tech = equipe.membres[0]
            
        if not membre_tech or not membre_tech.technicien_id:
            continue
            
        technicien = User.query.get(membre_tech.technicien_id)
        if not technicien:
            continue

        # Vérifier si le technicien est déjà occupé avec une intervention active (affecté, en cours, etc.)
        # Important: Un technicien ne peut avoir qu'une intervention active à la fois dans ce mode
        interv_active = Intervention.query.filter(
            Intervention.technicien_id == technicien.id,
            Intervention.statut.in_(['en_cours', 'affecte', 'nouveau'])
        ).first()
        
        if interv_active:
            print(f"DEBUG: Technicien {technicien.username} déjà occupé par l'intervention {interv_active.id}")
            continue
            
        # Normaliser la zone de l'équipe
        team_norm_zone = normalize_zone_local(equipe.zone)
        
        # Trouver une demande compatible pour cette équipe
        for demande in demandes:
            if demande.statut not in ['nouveau', 'a_reaffecter']:
                continue
                
            # Vérifier zone (doivent être dans la même zone normalisée)
            demand_norm_zone = normalize_zone_local(demande.zone)
            if team_norm_zone != demand_norm_zone:
                continue
                
            # Vérifier service (SAV ou Production - Supporte les équipes mixtes comme "SAV,Production")
            team_services = [s.strip().upper() for s in (equipe.service or '').split(',')]
            demand_service = (demande.service or '').strip().upper()
            if demand_service not in team_services:
                continue
                
            # Vérifier technologies
            if not is_technicien_compatible(technicien, demande):
                continue
                
            # Tout correspond ! On affecte.
            try:
                demande.technicien_id = technicien.id
                demande.statut = 'affecte'
                demande.date_affectation = datetime.now(timezone.utc)
                
                # Créer l'intervention
                intervention = Intervention(
                    demande_id=demande.id,
                    technicien_id=technicien.id,
                    equipe_id=equipe.id,
                    date_debut=datetime.now(timezone.utc),
                    statut='en_cours'
                )
                db.session.add(intervention)
                
                assigned_count += 1
                # Demande marquée comme traitée pour cette boucle
                demande.statut = 'assigned_internal' 
                
                print(f"DEBUG: Affectation automatique: Demande {demande.nd} -> Equipe {equipe.nom_equipe}")
                
                # Une seule demande par équipe à la fois
                break 
                
            except Exception as e:
                print(f"Erreur lors du dispatch auto de la demande {demande.id}: {e}")
                db.session.rollback()

    # Nettoyage du statut temporaire et commit final
    for d in demandes:
        if getattr(d, 'statut', '') == 'assigned_internal':
            d.statut = 'affecte'
            
    db.session.commit()
    return assigned_count


@dispatch_bp.route('/dispatching-automatique', methods=['POST'])
@login_required
@csrf.exempt
def dispatching_automatique():
    """Endpoint API pour déclencher le dispatching automatique manuellement."""
    if current_user.role not in ['chef_pur', 'chef_pilote', 'chef_zone']:
        return jsonify({'success': False, 'error': 'Accès non autorisé'})
        
    count = auto_dispatch_logic()
    return jsonify({
        'success': True,
        'message': f'{count} demandes ont été affectées automatiquement.'
    })
