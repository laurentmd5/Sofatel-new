import os
import traceback
from itsdangerous import URLSafeTimedSerializer
import pandas as pd
from datetime import datetime, date, timezone
from flask import json, render_template, request, redirect, session, url_for, flash, jsonify, current_app, send_from_directory, abort
from flask_login import login_user, logout_user, login_required, current_user
from pymysql.err import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import base64
import os
from PIL import Image
from app import db
from forms import FicheTechniqueForm
from models import FicheTechnique, Intervention
import io
from app import app, db
from models import *
from forms import *
from utils import log_activity, get_chef_pur_stats, get_chef_pilote_stats, get_chef_zone_stats, get_technicien_interventions, get_performance_data, build_stats_by_zone_tech
from kpi_utils import get_unified_performance_data
from extensions import csrf  # needed to exempt login in tests

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


# Surveys routes moved to routes/surveys.py (blueprint 'surveys')
# See routes/surveys.py for implementation and registration via register_blueprints(app)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password_hash and user.actif and check_password_hash(
                user.password_hash, form.password.data):
            
            # 🔴 PHASE 1 FIX: Valider que magasinier a une zone assignée
            if user.role and user.role.lower() == 'magasinier':
                if not user.zone_id:
                    flash('⚠️ Erreur: Vous n\'êtes pas assigné à une zone. Contactez votre administrateur.', 'error')
                    current_app.logger.warning(
                        f'Connexion magasinier bloquée: utilisateur {user.username} sans zone_id'
                    )
                    return render_template('login.html', form=form)
            
            login_user(user)
            session.permanent = True
            log_activity(
                user_id=user.id,
                action='login',
                module='auth',
                entity_name=f"{user.prenom} {user.nom}",
                details={'username': user.username, 'role': user.role}
            )
            
            flash('Connexion réussie!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(
                url_for('dashboard'))
        flash('Nom d\'utilisateur ou mot de passe incorrect.', 'error')

    return render_template('login.html', form=form)


@app.route('/api/check-session')
def check_session():
    if current_user.is_authenticated:
        return jsonify({'authenticated': True})
    return jsonify({'authenticated': False})

@app.route('/api/extend-session', methods=['POST'])
def extend_session():
    if current_user.is_authenticated:
        session.modified = True
        return jsonify({'success': True})
    return jsonify({'success': False}), 401

@app.route('/logout')
@login_required
def logout():
    # Ajout du log de déconnexion
    """ log = UserConnectionLog(
        user_id=current_user.id,
        action='logout',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit() """
    log_activity(
        user_id=current_user.id,
        action='logout',
        module='auth',
        entity_name=f"{current_user.prenom} {current_user.nom}",
        details={'username': current_user.username}
    )
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    try:
        if current_user.role == 'chef_pur':
            performance_data = get_performance_data()
            stats_by_zone_tech = build_stats_by_zone_tech()
            last_update = datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')
            techniciens = User.query.filter_by(role='technicien', actif=True).all()
            # Afficher toutes les équipes actives, qu'elles soient publiées ou non
            equipes = Equipe.query.filter_by(actif=True).order_by(Equipe.date_creation.desc()).all()
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
                'nom_equipe': e.nom_equipe,
                'technologies': e.technologies,
                'zone': normalize_zone(e.zone)
            } for e in equipes]
            equipes_mapping = {}
            for technicien in techniciens:
                technicien_zone = normalize_zone(technicien.zone)
                equipes_mapping[technicien.id] = [
                    equipe for equipe in equipes
                    if normalize_zone(equipe.zone) == technicien_zone and any(
                        m.technicien_id == technicien.id for m in equipe.membres)
                ]
            return render_template('dashboard_chef_pur.html',
                                   stats=get_chef_pur_stats(),
                                   stats_by_zone_tech=stats_by_zone_tech,
                                   last_update=last_update,
                                   performance_data=performance_data,
                                   zones=performance_data.get('zones', []),
                                   pilots=performance_data.get('pilots', []),
                                   techniciens_json=techniciens_json,
                                   equipes_json=equipes_json,
                                   equipes_mapping=equipes_mapping)
        elif current_user.role == 'chef_pilote':
            return render_template('dashboard_chef_pilote.html',
                                   stats=get_chef_pilote_stats(
                                       current_user.service, current_user))
        elif current_user.role == 'chef_zone':
            print(f"DEBUG: Utilisateur chef_zone connecté: {current_user.username}")
            
            # 🔴 FORCE RELOAD: Rechargement forcé des données utilisateur depuis la BD
            # pour éviter que les changements d'admin ne soient cachés par la session
            fresh_user = User.query.get(current_user.id)
            if not fresh_user:
                flash('⚠️ Erreur: Utilisateur non trouvé', 'error')
                return redirect(url_for('logout'))
            
            print(f"DEBUG: Données utilisateur reloadées depuis la BD")
            print(f"  - zone: {fresh_user.zone}")
            print(f"  - zone_id: {fresh_user.zone_id}")
            print(f"  - zone_relation: {fresh_user.zone_relation}")
            
            # Déterminer la zone depuis les données FRAÎCHES (pas du cache session)
            user_zone = None
            if fresh_user.zone_relation:
                user_zone = f"{fresh_user.zone_relation.nom} ({fresh_user.zone_relation.code})"
                print(f"DEBUG: Zone depuis zone_relation: {user_zone}")
            elif fresh_user.zone:
                user_zone = fresh_user.zone
                print(f"DEBUG: Zone depuis zone texte: {user_zone}")
            else:
                flash('⚠️ Erreur: Vous n\'êtes pas assigné à une zone. Contactez votre administrateur.', 'error')
                return redirect(url_for('logout'))
            
            print(f"DEBUG: Dashboard chef_zone - Zone utilisée: {user_zone}")
            
            try:
                stats = get_chef_zone_stats(user_zone)
                print(f"DEBUG: Stats retournées par get_chef_zone_stats: {stats}")
            except Exception as e:
                print(f"DEBUG: Erreur dans get_chef_zone_stats: {e}")
                flash(f'⚠️ Erreur lors du calcul des statistiques: {str(e)}', 'error')
                stats = {
                    'equipes_jour': 0,
                    'techniciens_zone': 0,
                    'interventions_cours': 0,
                    'interventions_terminees_jour': 0
                }
            
            try:
                stats_pur = get_chef_pur_stats(zone=user_zone)
                stats_pur['performance_data'] = get_performance_data(zone=user_zone)
            except Exception as e:
                print(f"DEBUG: Erreur dans get_chef_pur_stats: {e}")
                stats_pur = {'performance_data': {}}
            
            print(f"DEBUG: Stats finales envoyées au template: {stats}")
            
            return render_template('dashboard_chef_zone.html',
                                   stats=stats,
                                   stats_pur=stats_pur,
                                   user_zone=user_zone,
                                   fresh_user=fresh_user)
        elif current_user.role == 'technicien':
            return render_template('dashboard_technicien.html',
                                   interventions=get_technicien_interventions(
                                       current_user.id))
        elif current_user.role == 'gestionnaire_stock':
            return redirect(url_for('stock.gestion_stock'))
        elif current_user.role == 'magasinier':
            # 🔴 PHASE 1 FIX: Dashboard spécialisé pour magasinier
            # Vérifier que magasinier a une zone assignée
            if not current_user.zone_id:
                flash('⚠️ Erreur: Vous n\'êtes pas assigné à une zone. Contactez votre administrateur.', 'error')
                return redirect(url_for('logout'))
            
            from zone_rbac import filter_produit_by_emplacement_zone, filter_mouvement_by_zone
            
            # Stats zone magasinier - FIXED: Use zone_relation (object) not legacy zone string
            zone = current_user.zone_relation
            
            # Produits de la zone
            produits_query = Produit.query
            produits_zone = filter_produit_by_emplacement_zone(produits_query).all()
            
            # Mouvements récents (7 jours)
            seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
            mouvements_query = MouvementStock.query.filter(
                MouvementStock.date_mouvement >= seven_days_ago
            )
            mouvements_zone = filter_mouvement_by_zone(mouvements_query).all()
            
            # Stock summary
            total_articles = len(produits_zone)
            # FIXED: Use prix_vente instead of non-existent prix_unitaire
            total_value = sum([p.quantite * (float(p.prix_vente) if p.prix_vente else 0) for p in produits_zone])
            articles_low_stock = len([p for p in produits_zone if p.quantite and p.quantite < 10])
            
            # Mouvements par type
            entrees = len([m for m in mouvements_zone if m.type_mouvement == 'entree'])
            sorties = len([m for m in mouvements_zone if m.type_mouvement == 'sortie'])
            
            # ✅ NOUVEAU: Réservations techniciens en attente (inclut hors intervention)
            reservations_en_attente = db.session.query(ReservationPiece).join(
                User, ReservationPiece.utilisateur_id == User.id
            ).filter(
                User.zone_id == current_user.zone_id,
                ReservationPiece.statut == ReservationPiece.STATUT_EN_ATTENTE
            ).all()
            
            nb_reservations_attente = len(reservations_en_attente)
            
            return render_template('dashboard_magasinier.html',
                                 zone=zone,
                                 total_articles=total_articles,
                                 total_value=total_value,
                                 articles_low_stock=articles_low_stock,
                                 produits_zone=produits_zone,
                                 mouvements_zone=mouvements_zone,
                                 entrees_7j=entrees,
                                 sorties_7j=sorties,
                                 nb_reservations_attente=nb_reservations_attente)
        else:
            flash('Rôle utilisateur non reconnu.', 'error')
            return redirect(url_for('logout'))
    except OperationalError:
        current_app.logger.exception('Database OperationalError in dashboard — possibly missing columns')
        flash('Erreur base de données: schéma incomplet. Veuillez exécuter les migrations (voir IMPROVEMENTS.md).', 'danger')
        # Render empty/placeholder dashboard to avoid 500 and give operators a hint
        return render_template('dashboard_chef_pur.html',
                               stats={},
                               stats_by_zone_tech={},
                               last_update=None,
                               performance_data={},
                               zones=[],
                               pilots=[],
                               techniciens_json=[],
                               equipes_json=[],
                               equipes_mapping={})

@app.route('/dashboard/rh')
@login_required
def dashboard_rh():
    """RH Dashboard - Manage leave requests and team absences"""
    allowed_roles = ['rh', 'chef_pur']
    if current_user.role not in allowed_roles:
        flash('Accès refusé: seuls les utilisateurs RH et Chef PUR peuvent accéder au dashboard RH', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('dashboard_rh.html')


# ===== KPI DASHBOARD ROUTES: UPGRADED IN routes/auth.py =====
# ✅ The KPI dashboard route has been upgraded in routes/auth.py
# ✅ Merged with enhanced KPI data sourcing + fallback logic
# ✅ No duplication: single /dashboard/kpi endpoint
# ✅ Access: chef_pur, chef_zone, admin

# Dispatch/import routes moved to routes/dispatch.py (blueprint 'dispatch')
# See routes/dispatch.py for implementation and registration via register_blueprints(app)

@app.route('/import-demandes')
def import_demandes():
    """Compatibility wrapper: redirect old top-level endpoint name to the
    dispatch blueprint's implementation.
    """
    return redirect(url_for('dispatch.import_demandes'))

# Dispatching/import endpoints moved to routes/dispatch.py (blueprint 'dispatch')
# See routes/dispatch.py for implementation and registration via register_blueprints(app)


""" @app.route('/dispatching')
@login_required
def dispatching():
    if current_user.role not in ['chef_pur', 'chef_pilote', 'chef_zone']:
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('dashboard'))

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 25, type=int),
                   100)  # Limite à 100

    query = DemandeIntervention.query.filter(
        DemandeIntervention.statut.in_(['nouveau', 'a_reaffecter']))
    if current_user.role == 'chef_pilote' and current_user.service:
        if current_user.service == 'SAV,Production':
            # Chef pilote principal voit les deux services
            query = query.filter(DemandeIntervention.service.in_(['SAV', 'Production']))
        else:
            # Chef pilote normal voit seulement son service
            query = query.filter_by(service=current_user.service)

    if current_user.role == 'chef_zone' and current_user.zone:
        query = query.filter_by(zone=current_user.zone)

    demandes_paginated = query.order_by(
        DemandeIntervention.priorite_traitement.desc(),
        DemandeIntervention.date_demande_intervention.asc()).paginate(
            page=page, per_page=per_page, error_out=False)

    demandes = demandes_paginated.items

    techniciens = User.query.filter_by(role='technicien', actif=True).all()
    equipes = Equipe.query.filter_by(actif=True,
                                     publie=True,
                                     date_publication=date.today()).all()

    # --- NORMALISATION DES ZONES POUR LES DEMANDES ---
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

    # Appliquer la normalisation sur les objets pour le JS
    techniciens_json = [{
        'id': t.id,
        'prenom': t.prenom,
        'nom': t.nom,
        'technologies': t.technologies,
        'zone': normalize_zone(t.zone)
    } for t in techniciens]
    equipes_json = [{
        'id': e.id,
        'nom_equipe': e.nom_equipe,
        'technologies': e.technologies,
        'zone': normalize_zone(e.zone)
    } for e in equipes]

    # Normaliser la zone sur chaque demande AVANT de passer au template
    for d in demandes:
        d.zone = normalize_zone(d.zone)

    equipes_mapping = {}
    for technicien in techniciens:
        technicien_zone = normalize_zone(technicien.zone)
        equipes_mapping[technicien.id] = [
            equipe for equipe in equipes
            if normalize_zone(equipe.zone) == technicien_zone and any(
                m.technicien_id == technicien.id for m in equipe.membres)
        ]
    ages = [row[0] for row in db.session.query(DemandeIntervention.age).distinct().all() if row[0]]
    offres = [row[0] for row in db.session.query(DemandeIntervention.offre).distinct().all() if row[0]]
    priorites = [row[0] for row in db.session.query(DemandeIntervention.priorite_traitement).distinct().all() if row[0]]

    return render_template('dispatching.html',
                           demandes=demandes_paginated,
                           techniciens=techniciens,
                           equipes=equipes,
                           ages=ages,
                           offres=offres,
                           priorites=priorites,
                           techniciens_json=techniciens_json,
                           equipes_json=equipes_json,
                           equipes_mapping=equipes_mapping)

 """
""" @app.route('/affecter-demande', methods=['POST'])
@login_required
def affecter_demande():
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
            return jsonify({
                'success':
                False,
                'error':
                'Technicien non compatible avec cette technologie'
            })

        # Affecter la demande
        demande.technicien_id = technicien_id
        demande.statut = 'affecte'
        demande.date_affectation = datetime.now(timezone.utc)

        if equipe_id:
            # Créer une intervention liée à l'équipe
            intervention = Intervention(demande_id=demande_id,
                                        technicien_id=technicien_id,
                                        equipe_id=equipe_id,
                                        date_debut=datetime.now(timezone.utc),
                                        statut='en_cours')
            db.session.add(intervention)

        db.session.commit()
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
                'type_techno': demande.type_techno
            }
        )
        # Envoyer notification SMS (simulé)
        create_sms_notification(technicien_id, demande_id, 'affectation')

        # Envoyer email au technicien
        subject = "Nouvelle intervention affectée"
        recipients = [technicien.email] if technicien.email else []
        body = f"Bonjour {technicien.prenom},\n\nVous avez une nouvelle intervention affectée :\nND : {demande.nd}\nClient : {demande.nom_client} {demande.prenom_client}\nZone : {demande.zone}\n\nMerci de consulter votre espace Sofatelcom."
        send_email(subject, recipients, body=body)

        return jsonify({
            'success': True,
            'message': 'Demande affectée avec succès'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

"""

@app.route('/affecter-demande', methods=['POST'])
@login_required
def affecter_demande():
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
            return jsonify({
                'success': False,
                'error': 'Technicien non compatible avec cette technologie'
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
                intervention_existante.date_debut = datetime.now(timezone.utc)  # Optionnel : mettre à jour la date
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
            # We don't flash an error here to not confuse the user JSON response

        return jsonify({
            'success': True,
            'message': 'Demande affectée avec succès'
        })

    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de l'affectation: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/dispatching-automatique', methods=['POST'])
@login_required
def dispatching_automatique():
    if current_user.role not in ['chef_pur', 'chef_pilote']:
        return jsonify({'success': False, 'error': 'Accès non autorisé'})

    try:
        # Récupérer les demandes non affectées
        query = DemandeIntervention.query.filter_by(statut='nouveau')
        if current_user.role == 'chef_pilote' and current_user.service:
            query = query.filter_by(service=current_user.service)

        demandes = query.all()
        affectations = 0

        for demande in demandes:
            # Trouver le meilleur technicien selon les critères
            technicien = find_best_technicien(demande)
            if technicien:
                demande.technicien_id = technicien.id
                demande.statut = 'affecte'
                demande.date_affectation = datetime.now(timezone.utc)

                # Créer notification SMS
                create_sms_notification(technicien.id, demande.id,
                                        'affectation')
                affectations += 1

        db.session.commit()

        return jsonify({
            'success':
            True,
            'message':
            f'{affectations} demandes affectées automatiquement'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/demande/<int:demande_id>')
@login_required
def api_get_demande(demande_id):
    demande = db.session.get(DemandeIntervention, demande_id)
    if not demande:
        return jsonify({'success': False, 'error': 'Demande non trouvée'}), 404

    # Adaptez les champs selon votre modèle
    demande_data = {
        'id': demande.id,
        'nom_client': demande.nom_client,
        'prenom_client': demande.prenom_client,
        'nd': demande.nd,
        'type_techno': demande.type_techno,
        'service': demande.service,
        'zone': demande.zone,
        # Ajoutez d'autres champs si nécessaire
    }
    return jsonify({'success': True, 'demande': demande_data})


# Team management routes moved to routes/teams.py (blueprint 'teams')
# See routes/teams.py for implementation and registration via register_blueprints(app)

@app.route('/add-membre-equipe/<int:equipe_id>', methods=['POST'])
@login_required
def add_membre_equipe(equipe_id):
    if current_user.role not in ['chef_zone', 'chef_pur']:
        return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403

    # Vérification du token CSRF
    from flask_wtf.csrf import validate_csrf
    from wtforms import ValidationError
    
    try:
        # Vérifier si la requête est en JSON
        if request.is_json:
            data = request.get_json()
            csrf_token = data.get('csrf_token')
        else:
            data = request.form.to_dict()
            csrf_token = request.form.get('csrf_token')
            
        # Valider le token CSRF
        validate_csrf(csrf_token)
    except ValidationError as e:
        current_app.logger.error(f'Erreur de validation CSRF: {str(e)}')
        return jsonify({'success': False, 'error': 'Token CSRF invalide ou expiré'}), 403
    except Exception as e:
        current_app.logger.error(f'Erreur lors de la vérification CSRF: {str(e)}')
        return jsonify({'success': False, 'error': 'Erreur lors de la vérification CSRF'}), 400

    try:
        equipe = db.session.get(Equipe, equipe_id)
        
        # Vérification des permissions
        if not equipe:
            return jsonify({
                'success': False,
                'error': 'Équipe non trouvée'
            }), 404
            
        # Chef zone : ne peut ajouter que sur ses propres équipes
        # Chef PUR : peut ajouter sur toutes les équipes
        if current_user.role == 'chef_zone' and equipe.chef_zone_id != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Vous ne pouvez pas ajouter de membre à cette équipe'
            }), 403

        # Essayer de récupérer les données JSON
        try:
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()
        except Exception as e:
            return jsonify({
                'success': False,
                'error': 'Format de données invalide',
                'details': str(e)
            }), 400

        nom = (data.get('nom') or '').strip()
        prenom = (data.get('prenom') or '').strip()
        telephone = (data.get('telephone') or '').strip()
        type_membre = (data.get('type_membre') or '').strip()
        technicien_id = data.get('technicien_id')

        # Vérification des champs obligatoires
        if not nom or not prenom or not telephone or not type_membre:
            return jsonify({
                'success': False,
                'error': 'Tous les champs sont obligatoires.',
                'missing_fields': [
                    field for field, value in {
                        'nom': nom,
                        'prenom': prenom,
                        'telephone': telephone,
                        'type_membre': type_membre
                    }.items() if not value
                ]
            }), 400

        # Vérifier si le technicien existe et est actif
        if technicien_id:
            try:
                technicien_id = int(technicien_id)
                technicien = User.query.filter_by(id=technicien_id, role='technicien', actif=True).first()
                if not technicien:
                    return jsonify({
                        'success': False,
                        'error': 'Technicien non valide ou inactif'
                    }), 400
            except (ValueError, TypeError):
                technicien_id = None

        # Création du membre
        membre = MembreEquipe(
            equipe_id=equipe_id,
            nom=nom,
            prenom=prenom,
            telephone=telephone,
            type_membre=type_membre,
            technicien_id=technicien_id if technicien_id else None
        )

        db.session.add(membre)
        db.session.commit()
        
        # Journalisation de l'action
        log_activity(
            user_id=current_user.id,
            action='add_member',
            module='teams',
            entity_id=membre.id,
            entity_name=f"Membre {membre.nom} {membre.prenom}",
            details={
                'equipe_id': equipe.id,
                'equipe_nom': equipe.nom_equipe,
                'type_membre': membre.type_membre,
                'technicien_id': membre.technicien_id
            }
        )
        
        # Préparation de la réponse
        response_data = {
            'success': True,
            'message': 'Membre ajouté avec succès',
            'membre': {
                'id': membre.id,
                'nom': membre.nom,
                'prenom': membre.prenom,
                'telephone': membre.telephone,
                'type_membre': membre.type_membre,
                'technicien_id': membre.technicien_id
            }
        }
        
        return jsonify(response_data)

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erreur lors de l\'ajout du membre: {str(e)}')
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Une erreur est survenue lors de l\'ajout du membre',
            'details': str(e)
        }), 500

@app.route('/remove-membre-equipe/<int:membre_id>', methods=['DELETE'])
@login_required
def remove_membre_equipe(membre_id):
    # Vérification du token CSRF
    from flask_wtf.csrf import validate_csrf
    from wtforms import ValidationError
    
    try:
        # Vérifier si la requête est en JSON
        if request.is_json:
            data = request.get_json()
            csrf_token = data.get('csrf_token')
        else:
            data = request.form.to_dict()
            csrf_token = request.form.get('csrf_token')
            
        # Valider le token CSRF
        validate_csrf(csrf_token)
    except ValidationError as e:
        current_app.logger.error(f'Erreur de validation CSRF: {str(e)}')
        return jsonify({'success': False, 'error': 'Token CSRF invalide ou expiré'}), 403
    except Exception as e:
        current_app.logger.error(f'Erreur lors de la vérification CSRF: {str(e)}')
        return jsonify({'success': False, 'error': 'Erreur de vérification CSRF'}), 400
    
    # Récupération du membre
    membre = db.session.get(MembreEquipe, membre_id)
    if not membre:
        return jsonify({'success': False, 'error': 'Membre introuvable'}), 404
        
    # Vérification des permissions
    equipe = db.session.get(Equipe, membre.equipe_id)
    if not equipe:
        return jsonify({'success': False, 'error': 'Équipe non trouvée'}), 404
        
    # Vérifier que l'utilisateur a le droit de modifier cette équipe
    if current_user.role == 'chef_zone' and equipe.chef_zone_id != current_user.id:
        return jsonify({'success': False, 'error': 'Non autorisé à modifier cette équipe'}), 403
    
    try:
        # Journalisation de l'action
        log_activity(
            user_id=current_user.id,
            action='remove_member',
            module='teams',
            entity_id=membre.id,
            entity_name=f"Membre {membre.nom} {membre.prenom}",
            details={
                'equipe_id': equipe.id,
                'equipe_nom': equipe.nom_equipe,
                'type_membre': membre.type_membre,
                'technicien_id': membre.technicien_id
            }
        )
        
        # Suppression du membre
        db.session.delete(membre)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Membre supprimé avec succès',
            'membre_id': membre_id
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erreur lors de la suppression du membre: {str(e)}')
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False, 
            'error': 'Une erreur est survenue lors de la suppression du membre',
            'details': str(e)
        }), 500


@app.route('/api/check-team-name', methods=['POST'])
def check_team_name():
    data = request.get_json()
    nom_equipe = data.get('nom_equipe', '').strip()
    if not nom_equipe:
        return jsonify({'available': False, 'error': 'Nom manquant'}), 400

    # Vérifie si une équipe avec ce nom existe déjà aujourd'hui
    existe = Equipe.query.filter_by(nom_equipe=nom_equipe,
                                    date_creation=date.today()).first()
    return jsonify({'available': not bool(existe)})


@app.route('/intervention/<int:demande_id>')
@login_required
def intervention_form(demande_id):
    if current_user.role != 'technicien':
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('dashboard'))

    demande = db.session.get(DemandeIntervention, demande_id)
    if not demande:
        abort(404)
    if demande.technicien_id != current_user.id:
        flash('Cette intervention ne vous est pas affectée.', 'error')
        return redirect(url_for('dashboard'))

    # Vérifier si une intervention existe déjà
    intervention = Intervention.query.filter_by(demande_id=demande_id).first()
    if not intervention:
        intervention = Intervention(demande_id=demande_id,
                                    technicien_id=current_user.id)
        db.session.add(intervention)
        db.session.commit()

    # Initialiser les formulaires
    form = InterventionForm(obj=intervention)
    survey_form = None
    fiche_technique_form = None

    # Charger le survey existant s'il existe
    survey = Survey.query.filter_by(intervention_id=intervention.id).first()

    if demande.service == 'Production':
        survey_form = SurveyForm(obj=survey) if survey else SurveyForm()
        survey_form.n_demande.data = demande.nd
        survey_form.nom_raison_sociale.data = f"{demande.nom_client} {demande.prenom_client}"
        survey_form.adresse_demande.data = demande.libelle_commune
        survey_form.service_demande.data = demande.type_techno

        fiche_technique_form = FicheTechniqueForm()
        if intervention.fichier_technique_accessible:
            fiche_technique_form.adresse_demandee.data = demande.libelle_commune
            fiche_technique_form.nom_raison_sociale.data = f"{demande.nom_client} {demande.prenom_client}"
            fiche_technique_form.date_installation.data = survey.date_survey if survey and survey.date_survey else date.today(
            )
            fiche_technique_form.tel1.data = survey.tel1 if survey else ''
            fiche_technique_form.tel2.data = survey.tel2 if survey else ''
            fiche_technique_form.etage.data = survey.etage if survey else ''
            fiche_technique_form.contact.data = survey.contact if survey else ''
            fiche_technique_form.represente_par.data = survey.represente_par if survey else ''
            fiche_technique_form.adresse_demandee.data = survey.adresse_demande if survey else ''

    return render_template('intervention_form.html',
                           form=form,
                           survey_form=survey_form,
                           fiche_technique_form=fiche_technique_form,
                           demande=demande,
                           intervention=intervention,
                           survey=survey)


@app.route('/auto-save-intervention/<int:intervention_id>', methods=['POST'])
@login_required
def auto_save_intervention(intervention_id):
    if current_user.role != 'technicien':
        return jsonify({'success': False, 'error': 'Accès non autorisé'})

    try:
        intervention = db.session.get(Intervention, intervention_id)
        if not intervention or intervention.technicien_id != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Intervention non trouvée'
            })

        form = InterventionForm()
        if form.validate_on_submit():
            # Sauvegarder tous les champs du formulaire
            for field_name in form._fields:
                if hasattr(intervention, field_name):
                    setattr(intervention, field_name,
                            getattr(form, field_name).data)

            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Sauvegarde automatique réussie'
            })
        else:
            return jsonify({'success': False, 'errors': form.errors})

    except Exception as e:
        db.session.rollback()
        print('Erreur lors de la sauvegarde automatique:', str(e))
        return jsonify({'success': False, 'error': str(e)})


@app.route('/save-intervention/<int:intervention_id>', methods=['POST'])
@login_required
def save_intervention(intervention_id):
    if current_user.role != 'technicien':
        return jsonify({'success': False, 'error': 'Accès non autorisé'})

    try:
        intervention = db.session.get(Intervention, intervention_id)
        if not intervention or intervention.technicien_id != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Intervention non trouvée'
            })

        form = InterventionForm()
        if form.validate_on_submit():
            # Sauvegarder tous les champs du formulaire avec conversion de type
            for field_name, field in form._fields.items():
                if hasattr(intervention, field_name):
                    field_data = field.data
                    # Conversion des champs numériques si nécessaire
                    if field_name in ['lc_metre', 'bti_metre', 'kitpto_metre'
                                      ]:  # Exemple de champs numériques
                        try:
                            field_data = float(
                                field_data) if field_data else None
                        except (ValueError, TypeError):
                            field_data = None
                    setattr(intervention, field_name, field_data)

            # Gestion des photos uploadées
            uploaded_files = request.files.getlist('photos')
            photo_paths = []

            for file in uploaded_files:
                if file and file.filename != '':
                    filename = secure_filename(file.filename)
                    unique_filename = f"{datetime.now().timestamp()}_{filename}"
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'],
                                             unique_filename)
                    file.save(save_path)
                    photo_paths.append(
                        unique_filename
                    )  # Stocker uniquement le nom du fichier

            if photo_paths:
                intervention.photos = json.dumps(photo_paths)

            intervention.date_fin = datetime.now(timezone.utc)
            intervention.statut = 'termine'

            if intervention.demande:
                intervention.demande.statut = 'termine'
                intervention.demande.date_completion = datetime.now(timezone.utc)

            db.session.commit()
    
            # Post-commit actions (logging and notifications) should not crash the main flow
            try:
                # Créer notification pour validation
                create_sms_notification(intervention.technicien_id , intervention.demande_id, 'validation', notify_managers=True)
        
                # Envoi mail pour validation
                destinataires = []
                demande = intervention.demande
        
                if demande:
                    # Chef PUR
                    chef_pur = User.query.filter_by(role='chef_pur').first()
                    if chef_pur and chef_pur.email:
                        destinataires.append(chef_pur.email)
                    # Chef Zone
                    if demande.zone:
                        chef_zone = User.query.filter_by(
                            role='chef_zone', zone=demande.zone).first()
                        if chef_zone and chef_zone.email:
                            destinataires.append(chef_zone.email)
                    # Chef Pilote
                    if demande.service:
                        chef_pilote = User.query.filter_by(
                            role='chef_pilote', service=demande.service).first()
                        if chef_pilote and chef_pilote.email:
                            destinataires.append(chef_pilote.email)
                    # Récupérer le nom du technicien
                    technicien_nom = f"{intervention.technicien.nom} {intervention.technicien.prenom}" if intervention.technicien else "N/A"
                    # Récupérer le nom de l'équipe liée
                    equipe_nom = ""
                    if intervention.equipe_id:
                        equipe = db.session.get(Equipe, intervention.equipe_id)
                        equipe_nom = equipe.nom_equipe if equipe else ""
        
                    subject = "Intervention à valider"
                    body = f"""Bonjour,\n\nUne intervention vient d'être terminée et nécessite votre validation.\n
                    ND : {demande.nd}\nClient : {demande.nom_client} {demande.prenom_client}\nZone : {demande.zone}\nService : {demande.service}\n
                    Technicien : {technicien_nom}\nÉquipe : {equipe_nom}\n
                    Merci de vous connecter à Sofatelcom pour valider ou rejeter cette intervention."""
                    if destinataires:
                        send_email(subject, destinataires, body=body)
                log_activity(
                    user_id=current_user.id,
                    action='complete',
                    module='interventions',
                    entity_id=intervention.id,
                    entity_name=f"Intervention {intervention.demande.nd if intervention.demande else 'N/A'}",
                    details={
                        'statut': 'termine',
                        'technicien': f"{intervention.technicien.prenom} {intervention.technicien.nom}" if intervention.technicien else 'N/A',
                        'demande_nd': intervention.demande.nd if intervention.demande else 'N/A',
                        'service': intervention.demande.service if intervention.demande else 'N/A'
                    }
                )
            except Exception as post_e:
                current_app.logger.warning(f"Post-completion background tasks failed for intervention {intervention.id}: {str(post_e)}")
            return redirect(url_for('dashboard'))

        else:
            errors = {
                field: errors[0]
                for field, errors in form.errors.items()
            }
            return jsonify({'success': False, 'errors': errors})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Erreur lors de la sauvegarde: {str(e)}",
                         exc_info=True)
        return jsonify({
            'success': False,
            'error': "Une erreur est survenue lors de la sauvegarde"
        })


@app.route('/validate-intervention/<int:intervention_id>', methods=['POST'])
@login_required
def validate_intervention(intervention_id):
    if current_user.role not in ['chef_pur', 'chef_pilote', 'chef_zone']:
        return jsonify({'success': False, 'error': 'Accès non autorisé'})

    try:
        intervention = db.session.get(Intervention, intervention_id)
        if not intervention:
            return jsonify({
                'success': False,
                'error': 'Intervention non trouvée'
            })

        if current_user.role == 'chef_zone':
            if not intervention.demande or intervention.demande.zone != current_user.zone:
                return jsonify({
                    'success': False,
                    'error': 'Accès non autorisé'
                })

        action = request.json.get('action')  # 'valider' ou 'rejeter'
        commentaire = request.json.get('commentaire', '')

        if action == 'valider':
            intervention.statut = 'valide'
            intervention.demande.statut = 'valide'
        else:
            intervention.statut = 'rejete'
            intervention.demande.statut = 'affecte'  # Retour en affectation

        intervention.date_validation = datetime.now(timezone.utc)
        intervention.valide_par = current_user.id
        intervention.commentaire_validation = commentaire

        db.session.commit()

        return jsonify({
            'success':
            True,
            'message':
            f'Intervention {intervention.statut}e avec succès'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})


""" @app.route('/api/intervention/<int:intervention_id>')
@login_required
def api_get_intervention(intervention_id):
    intervention = db.session.get(Intervention, intervention_id)
    if not intervention:
        abort(404)

    # Vérifier les permissions selon le rôle
    if current_user.role == 'technicien' and intervention.technicien_id != current_user.id:
        return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403
    elif current_user.role == 'chef_pilote':
        if intervention.demande and intervention.demande.service != current_user.service:
            return jsonify({
                'success': False,
                'error': 'Accès non autorisé'
            }), 403
    elif current_user.role == 'chef_zone':
        technicien = db.session.get(User, intervention.technicien_id)
        if not technicien or technicien.zone != current_user.zone:
            return jsonify({
                'success': False,
                'error': 'Accès non autorisé'
            }), 403

    # Préparer les données de l'intervention
    intervention_data = {
        'id':
        intervention.id,
        'date_debut':
        intervention.date_debut.strftime('%d/%m/%Y %H:%M')
        if intervention.date_debut else None,
        'date_fin':
        intervention.date_fin.strftime('%d/%m/%Y %H:%M')
        if intervention.date_fin else None,
        'statut':
        intervention.statut,
        'diagnostic_technicien':
        intervention.diagnostic_technicien,
        'nature_signalisation':
        intervention.nature_signalisation,
        'cause_derangement':
        intervention.cause_derangement,
        'action_releve':
        intervention.action_releve,
        'constitutions':
        intervention.constitutions,
        'valeur_pB0':
        intervention.valeur_pB0,
        'materiel_livre':
        intervention.materiel_livre,
        'numero_serie_livre':
        intervention.numero_serie_livre,
        'materiel_recup':
        intervention.materiel_recup,
        'numero_serie_recup':
        intervention.numero_serie_recup,
        'jarretiere':
        intervention.jarretiere,
        'nombre_type_bpe':
        intervention.nombre_type_bpe,
        'coupleur_c1':
        intervention.coupleur_c1,
        'coupleur_c2':
        intervention.coupleur_c2,
        'arobase':
        intervention.arobase,
        'malico':
        intervention.malico,
        'type_cable':
        intervention.type_cable,
        'lc_metre':
        intervention.lc_metre,
        'bti_metre':
        intervention.bti_metre,
        'pto_one':
        intervention.pto_one,
        'kitpto_metre':
        intervention.kitpto_metre,
        'piton':
        intervention.piton,
        'ds6':
        intervention.ds6,
        'autres_accessoires':
        intervention.autres_accessoires,
        'appel_sortant':
        intervention.appel_sortant,
        'envoi_numero':
        intervention.envoi_numero,
        'appel_entrant':
        intervention.appel_entrant,
        'affichage_numero':
        intervention.affichage_numero,
        'tvo_mono_ok':
        intervention.tvo_mono_ok,
        'debit_cable_montant':
        intervention.debit_cable_montant,
        'debit_mbs_descendant':
        intervention.debit_mbs_descendant,
        'debit_mbs_ping':
        intervention.debit_mbs_ping,
        'debit_ms':
        intervention.debit_ms,
        'pieces':
        intervention.pieces,
        'communes':
        intervention.communes,
        'chambres':
        intervention.chambres,
        'bureau':
        intervention.bureau,
        'wifi_extender':
        intervention.wifi_extender,
        'mesure_dbm':
        intervention.mesure_dbm,
        'satisfaction':
        intervention.satisfaction,
        'signature_equipe':
        intervention.signature_equipe,
        'signature_client':
        intervention.signature_client,
        'photos_list':
        json.loads(intervention.photos) if intervention.photos else [],
        'technicien': {
            'id':
            intervention.technicien_id,
            'nom':
            intervention.technicien.nom if intervention.technicien else 'N/A',
            'prenom':
            intervention.technicien.prenom
            if intervention.technicien else 'N/A'
        },
        'demande': {
            'id':
            intervention.demande_id,
            'nom_client':
            intervention.demande.nom_client if intervention.demande else 'N/A',
            'prenom_client':
            intervention.demande.prenom_client
            if intervention.demande else 'N/A',
            'nd':
            intervention.demande.nd if intervention.demande else 'N/A',
            'type_techno':
            intervention.demande.type_techno
            if intervention.demande else 'N/A',
            'service':
            intervention.demande.service if intervention.demande else 'N/A',
            'libelle_commune':
            intervention.demande.libelle_commune
            if intervention.demande else 'N/A',
            'libelle_quartier':
            intervention.demande.libelle_quartier
            if intervention.demande else ''
        } if intervention.demande else None
    }

    return jsonify({'success': True, 'intervention': intervention_data})

 """

@app.route('/api/intervention/<int:intervention_id>')
@login_required
def api_get_intervention(intervention_id):
    try:
        intervention = db.session.get(Intervention, intervention_id)
        if not intervention:
            abort(404)

        # Vérifier les permissions selon le rôle
        if current_user.role == 'technicien' and intervention.technicien_id != current_user.id:
            return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403
        elif current_user.role == 'chef_pilote':
            if intervention.demande and intervention.demande.service != current_user.service:
                return jsonify({
                    'success': False,
                    'error': 'Accès non autorisé'
                }), 403
        elif current_user.role == 'chef_zone':
            technicien = db.session.get(User, intervention.technicien_id)
            if not technicien or technicien.zone != current_user.zone:
                return jsonify({
                    'success': False,
                    'error': 'Accès non autorisé'
                }), 403

        # Vérifier si c'est une fiche technique ou SAV
        is_fiche_technique = FicheTechnique.query.filter_by(intervention_id=intervention_id).first() is not None
        intervention_type = 'fiche_technique' if is_fiche_technique else 'sav'

        # Préparer les données de l'intervention avec gestion des None
        # Gérer le parsing JSON des photos de manière sécurisée
        photos_list = []
        if intervention.photos:
            try:
                if isinstance(intervention.photos, str) and intervention.photos.strip():
                    photos_list = json.loads(intervention.photos)
            except (json.JSONDecodeError, ValueError, TypeError):
                photos_list = []
        
        intervention_data = {
            'id': intervention.id,
            'valide_par': intervention.valide_par,
            'fichier_technique_accessible': intervention.fichier_technique_accessible,
            'date_debut': intervention.date_debut.strftime('%d/%m/%Y %H:%M') if intervention.date_debut else None,
            'date_fin': intervention.date_fin.strftime('%d/%m/%Y %H:%M') if intervention.date_fin else None,
            'statut': intervention.statut,
            'diagnostic_technicien': intervention.diagnostic_technicien or '',
            'nature_signalisation': intervention.nature_signalisation or '',
            'cause_derangement': intervention.cause_derangement or '',
            'action_releve': intervention.action_releve or '',
            'gps_lat': intervention.gps_lat,
            'gps_long': intervention.gps_long,
            'constitutions': intervention.constitutions or '',
            'valeur_pB0': intervention.valeur_pB0 or '',
            'materiel_livre': intervention.materiel_livre or '',
            'numero_serie_livre': intervention.numero_serie_livre or '',
            'materiel_recup': intervention.materiel_recup or '',
            'numero_serie_recup': intervention.numero_serie_recup or '',
            'jarretiere': intervention.jarretiere or '',
            'nombre_type_bpe': intervention.nombre_type_bpe or '',
            'coupleur_c1': intervention.coupleur_c1 or '',
            'coupleur_c2': intervention.coupleur_c2 or '',
            'arobase': intervention.arobase or '',
            'malico': intervention.malico or '',
            'type_cable': intervention.type_cable or '',
            'lc_metre': intervention.lc_metre or '',
            'bti_metre': intervention.bti_metre or '',
            'pto_one': intervention.pto_one or '',
            'kitpto_metre': intervention.kitpto_metre or '',
            'piton': intervention.piton or '',
            'ds6': intervention.ds6 or '',
            'autres_accessoires': intervention.autres_accessoires or '',
            'appel_sortant': bool(intervention.appel_sortant),
            'envoi_numero': intervention.envoi_numero or '',
            'appel_entrant': bool(intervention.appel_entrant),
            'affichage_numero': intervention.affichage_numero or '',
            'tvo_mono_ok': bool(intervention.tvo_mono_ok),
            'debit_cable_montant': intervention.debit_cable_montant or '',
            'debit_mbs_descendant': intervention.debit_mbs_descendant or '',
            'debit_mbs_ping': intervention.debit_mbs_ping or '',
            'debit_ms': intervention.debit_ms or '',
            'pieces': intervention.pieces or '',
            'communes': intervention.communes or '',
            'chambres': intervention.chambres or 0,
            'bureau': intervention.bureau or 0,
            'wifi_extender': bool(intervention.wifi_extender),
            'mesure_dbm': intervention.mesure_dbm or '',
            'satisfaction': intervention.satisfaction or '',
            'signature_equipe': intervention.signature_equipe or '',
            'signature_client': intervention.signature_client or '',
            'photos_list': photos_list,
            'type': intervention_type,
            'has_fiche_technique': is_fiche_technique,
            'technicien': {
                'id': intervention.technicien_id,
                'nom': intervention.technicien.nom if intervention.technicien else 'N/A',
                'prenom': intervention.technicien.prenom if intervention.technicien else 'N/A'
            } if intervention.technicien else None,
            'valideur': {
                'id': intervention.valideur.id if intervention.valideur else None,
                'nom': intervention.valideur.nom if intervention.valideur else None,
                'prenom': intervention.valideur.prenom if intervention.valideur else None
            } if intervention.valideur else None,
            'demande': {
                'id': intervention.demande_id,
                'nom_client': intervention.demande.nom_client if intervention.demande else 'N/A',
                'prenom_client': intervention.demande.prenom_client if intervention.demande else 'N/A',
                'nd': intervention.demande.nd if intervention.demande else 'N/A',
                'type_techno': intervention.demande.type_techno if intervention.demande else 'N/A',
                'service': intervention.demande.service if intervention.demande else 'N/A',
                'libelle_commune': intervention.demande.libelle_commune if intervention.demande else 'N/A',
                'libelle_quartier': intervention.demande.libelle_quartier if intervention.demande else ''
            } if intervention.demande else None
        }

        return jsonify({'success': True, 'intervention': intervention_data})

    except Exception as e:
        app.logger.error(f"Erreur dans api_get_intervention: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': 'Erreur interne du serveur'}), 500

""" @app.route('/intervention-history')
@login_required
def intervention_history():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 25, type=int),
                   100)  # Limite à 100

    # Filtrer selon le rôle - requêtes simplifiées pour éviter les erreurs de join
    if current_user.role == 'chef_pur':
        query = Intervention.query.order_by(Intervention.date_debut.desc())
    elif current_user.role == 'chef_pilote':
        # Déterminer le filtre de service selon le profil de l'utilisateur
        if current_user.service == 'SAV,Production':
            # Chef pilote principal - récupérer les IDs des deux services
            demande_ids = [
                d.id for d in DemandeIntervention.query.filter(
                    DemandeIntervention.service.in_(['SAV', 'Production'])
                ).all()
            ]
        else:
            # Chef pilote normal - récupérer les IDs de son service seulement
            demande_ids = [
                d.id for d in DemandeIntervention.query.filter_by(
                    service=current_user.service).all()
            ]
        query = Intervention.query.filter(
            Intervention.demande_id.in_(demande_ids)).order_by(
                Intervention.date_debut.desc())
    elif current_user.role == 'chef_zone':
        # Récupérer les IDs des techniciens de la zone
        technicien_ids = [
            u.id for u in User.query.filter_by(role='technicien',
                                               zone=current_user.zone).all()
        ]
        query = Intervention.query.filter(
            Intervention.technicien_id.in_(technicien_ids)).order_by(
                Intervention.date_debut.desc())
    elif current_user.role == 'technicien':
        query = Intervention.query.filter_by(
            technicien_id=current_user.id).order_by(
                Intervention.date_debut.desc())
    else:
        query = Intervention.query.filter(
            Intervention.id == -1)  # Aucun résultat

    interventions = query.paginate(page=page,
                                   per_page=per_page,
                                   error_out=False)

    # Ajoute photos_list à chaque intervention
    for intervention in interventions.items:
        try:
            intervention.photos_list = json.loads(
                intervention.photos) if intervention.photos else []
        except Exception:
            intervention.photos_list = []

    return render_template('intervention_history.html',
                           interventions=interventions)

"""


@app.route('/intervention-history')
@login_required
def intervention_history():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 5, type=int), 100)  # Limite à 100

    # Récupérer les paramètres de filtre
    statut = request.args.get('statut')
    technologie = request.args.get('technologie')
    service_filter = request.args.get('service')  # Renommé pour éviter conflit avec current_user.service
    zone_filter = request.args.get('zone')
    date_debut = request.args.get('date_debut')
    date_fin = request.args.get('date_fin')
    search_text = request.args.get('search_text')

    # Classe pagination vide pour le fallback erreur
    class _EmptyPagination:
        items = []
        total = 0
        pages = 0
        page = 1
        has_prev = False
        has_next = False

    current_filters = {
        'statut': statut,
        'technologie': technologie,
        'service': service_filter,
        'zone': zone_filter,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'search_text': search_text,
        'per_page': per_page
    }

    try:
        # Filtrer selon le rôle - requêtes simplifiées pour éviter les erreurs de join
        if current_user.role == 'chef_pur':
            query = Intervention.query.order_by(Intervention.date_debut.desc())
        elif current_user.role == 'chef_pilote':
            if current_user.service == 'SAV,Production':
                demande_ids = [
                    d.id for d in DemandeIntervention.query.filter(
                        DemandeIntervention.service.in_(['SAV', 'Production'])
                    ).all()
                ]
            else:
                demande_ids = [
                    d.id for d in DemandeIntervention.query.filter_by(
                        service=current_user.service).all()
                ]
            query = Intervention.query.filter(
                Intervention.demande_id.in_(demande_ids)).order_by(
                    Intervention.date_debut.desc())
        elif current_user.role == 'chef_zone':
            technicien_ids = [
                u.id for u in User.query.filter_by(role='technicien',
                                                   zone=current_user.zone).all()
            ]
            query = Intervention.query.filter(
                Intervention.technicien_id.in_(technicien_ids)).order_by(
                    Intervention.date_debut.desc())
        elif current_user.role == 'technicien':
            query = Intervention.query.filter_by(
                technicien_id=current_user.id).order_by(
                    Intervention.date_debut.desc())
        else:
            query = Intervention.query.filter(Intervention.id == -1)  # Aucun résultat

        # Appliquer les filtres supplémentaires
        # On track les tables déjà jointes pour éviter les doublons de JOIN
        demande_joined = False
        user_joined = False

        if statut:
            query = query.filter(Intervention.statut == statut)

        if technologie:
            if not demande_joined:
                query = query.join(DemandeIntervention, Intervention.demande_id == DemandeIntervention.id)
                demande_joined = True
            query = query.filter(DemandeIntervention.type_techno == technologie)

        if service_filter:
            if not demande_joined:
                query = query.join(DemandeIntervention, Intervention.demande_id == DemandeIntervention.id)
                demande_joined = True
            query = query.filter(DemandeIntervention.service == service_filter)

        if zone_filter:
            if not user_joined:
                query = query.join(User, Intervention.technicien_id == User.id)
                user_joined = True
            query = query.filter(User.zone == zone_filter)

        if date_debut:
            try:
                query = query.filter(Intervention.date_debut >= datetime.strptime(date_debut, '%Y-%m-%d'))
            except ValueError:
                pass

        if date_fin:
            try:
                query = query.filter(Intervention.date_debut <= datetime.strptime(date_fin, '%Y-%m-%d'))
            except ValueError:
                pass

        if search_text:
            from sqlalchemy import or_
            if not demande_joined:
                query = query.join(DemandeIntervention, Intervention.demande_id == DemandeIntervention.id)
                demande_joined = True
            if not user_joined:
                query = query.join(User, Intervention.technicien_id == User.id)
                user_joined = True
            query = query.filter(
                or_(
                    DemandeIntervention.nd.contains(search_text),
                    DemandeIntervention.nom_client.contains(search_text),
                    DemandeIntervention.prenom_client.contains(search_text),
                    User.prenom.contains(search_text),
                    User.nom.contains(search_text)
                )
            )

        interventions = query.paginate(page=page, per_page=per_page, error_out=False)

        # Ajoute photos_list à chaque intervention de façon sécurisée
        for intervention in interventions.items:
            try:
                intervention.photos_list = json.loads(
                    intervention.photos) if intervention.photos else []
            except Exception:
                intervention.photos_list = []

        return render_template('intervention_history.html',
                               interventions=interventions,
                               current_filters=current_filters)

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"[intervention_history] {type(e).__name__}: {e}")
        app.logger.error(traceback.format_exc())
        err_lower = str(e).lower()
        if 'no such column' in err_lower or 'unknown column' in err_lower or 'operational' in err_lower:
            flash('⚠️ Erreur de base de données : schéma incomplet ou migration manquante.', 'danger')
        elif 'ambiguous' in err_lower:
            flash('⚠️ Erreur de requête SQL (jointure ambiguë). Signalez ce problème.', 'danger')
        else:
            flash(f'⚠️ Erreur inattendue ({type(e).__name__}). Réessayez ou contactez l\'administrateur.', 'danger')
        return render_template('intervention_history.html',
                               interventions=_EmptyPagination(),
                               current_filters=current_filters)




@app.route('/api/stats')
@login_required
def api_stats():
    """API pour les statistiques temps réel"""
    if current_user.role == 'chef_pur':
        stats = get_chef_pur_stats()
    elif current_user.role == 'chef_pilote':
        stats = get_chef_pilote_stats(current_user.service)
    elif current_user.role == 'chef_zone':
        stats = get_chef_zone_stats(current_user.zone)
    else:
        stats = {}

    return jsonify(stats)


# Route pour gérer les erreurs
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


@app.route('/api/equipes-jour')
@login_required
def api_equipes_jour():
    today = date.today()
    equipes = Equipe.query.filter_by(publie=True,
                                     date_publication=date.today(),
                                     actif=True,
                                     zone=current_user.zone).all()
    equipes_data = []
    for equipe in equipes:
        equipes_data.append({
            'id':
            equipe.id,
            'zone':
            equipe.zone,
            'nom_equipe':
            equipe.nom_equipe,
            'service':
            equipe.service,
            'technologies':
            equipe.technologies,
            'nb_membres':
            len(equipe.membres) if hasattr(equipe, 'membres') else 0
        })
    return jsonify({'success': True, 'equipes': equipes_data})


@app.route('/intervention/<int:intervention_id>/fiche_technique',
           methods=['GET', 'POST'])
@login_required
def fiche_technique(intervention_id):
    intervention = db.session.get(Intervention, intervention_id)
    if not intervention:
        abort(404)
    form = FicheTechniqueForm()

    if request.method == 'POST' and form.validate_on_submit():
        fiche = FicheTechnique(
            intervention_id=intervention_id,
            nom_raison_sociale=form.nom_raison_sociale.data,
            contact=form.contact.data,
            represente_par=form.represente_par.data,
            date_installation=form.date_installation.data,
            tel1=form.tel1.data,
            tel2=form.tel2.data,
            adresse_demandee=form.adresse_demandee.data,
            etage=form.etage.data,
            gps_lat=form.gps_lat.data,
            gps_long=form.gps_long.data,
            type_logement_avec_bpi=form.type_logement_avec_bpi.data,
            type_logement_sans_bpi=form.type_logement_sans_bpi.data,
            h_arrivee=form.h_arrivee.data,
            h_depart=form.h_depart.data,

            # Informations techniques
            n_ligne=form.n_ligne.data,
            n_demande=form.n_demande.data,
            technicien_structure=form.technicien_structure.data,
            pilote_structure=form.pilote_structure.data,
            offre=form.offre.data,
            debit=form.debit.data,
            type_mc=form.type_mc.data,
            type_na=form.type_na.data,
            type_transfert=form.type_transfert.data,
            type_autre=form.type_autre.data,
            backoffice_structure=form.backoffice_structure.data,

            # Matériels
            type_ont=form.type_ont.data,
            nature_ont=form.nature_ont.data,
            numero_serie_ont=form.numero_serie_ont.data,
            type_decodeur=form.type_decodeur.data,
            nature_decodeur=form.nature_decodeur.data,
            numero_serie_decodeur=form.numero_serie_decodeur.data,
            disque_dur=form.disque_dur.data,
            telephone=form.telephone.data,
            recepteur_wifi=form.recepteur_wifi.data,
            cpl=form.cpl.data,
            carte_vaccess=form.carte_vaccess.data,

            # Accessoires
            type_cable_lc=form.type_cable_lc.data,
            type_cable_bti=form.type_cable_bti.data,
            type_cable_pto_one=form.type_cable_pto_one.data,
            kit_pto=form.kit_pto.data,
            piton=form.piton.data,
            arobase=form.arobase.data,
            malico=form.malico.data,
            ds6=form.ds6.data,
            autre_accessoire=form.autre_accessoire.data,

            # Tests de services
            appel_sortant_ok=form.appel_sortant_ok.data,
            appel_sortant_nok=form.appel_sortant_nok.data,
            appel_entrant_ok=form.appel_entrant_ok.data,
            appel_entrant_nok=form.appel_entrant_nok.data,
            tvo_mono_ok=form.tvo_mono_ok.data,
            tvo_mono_nok=form.tvo_mono_nok.data,
            tvo_multi_ok=form.tvo_multi_ok.data,
            tvo_multi_nok=form.tvo_multi_nok.data,
            enregistreur_dd_ok=form.enregistreur_dd_ok.data,
            enregistreur_dd_nok=form.enregistreur_dd_nok.data,

            # Tests de débits
            par_cable_salon=form.par_cable_salon.data,
            par_cable_chambres=form.par_cable_chambres.data,
            par_cable_bureau=form.par_cable_bureau.data,
            par_cable_autres=form.par_cable_autres.data,
            par_cable_vitesse_wifi=form.par_cable_vitesse_wifi.data,
            par_cable_mesure_mbps=form.par_cable_mesure_mbps.data,
            par_wifi_salon=form.par_wifi_salon.data,
            par_wifi_chambres=form.par_wifi_chambres.data,
            par_wifi_bureau=form.par_wifi_bureau.data,
            par_wifi_autres=form.par_wifi_autres.data,
            par_wifi_vitesse_wifi=form.par_wifi_vitesse_wifi.data,
            par_wifi_mesure_mbps=form.par_wifi_mesure_mbps.data,

            # Etiquetages et Nettoyage
            etiquetage_colliers_serres=form.etiquetage_colliers_serres.data,
            etiquetage_pbo_normalise=form.etiquetage_pbo_normalise.data,
            nettoyage_depose=form.nettoyage_depose.data,
            nettoyage_tutorat=form.nettoyage_tutorat.data,

            # Rattachement
            rattachement_nro=form.rattachement_nro.data,
            rattachement_type=form.rattachement_type.data,
            rattachement_num_carte=form.rattachement_num_carte.data,
            rattachement_num_port=form.rattachement_num_port.data,
            rattachement_plaque=form.rattachement_plaque.data,
            rattachement_bpi_pbo=form.rattachement_bpi_pbo.data,
            rattachement_coupleur=form.rattachement_coupleur.data,
            rattachement_fibre=form.rattachement_fibre.data,
            rattachement_ref_dbm=form.rattachement_ref_dbm.data,
            rattachement_mesure_dbm=form.rattachement_mesure_dbm.data,

            # Commentaires
            commentaires=form.commentaires.data,

            # Signatures et satisfaction client
            signature_equipe=form.signature_equipe.data,
            signature_client=form.signature_client.data,
            client_tres_satisfait=form.client_tres_satisfait.data,
            client_satisfait=form.client_satisfait.data,
            client_pas_satisfait=form.client_pas_satisfait.data)

        db.session.add(fiche)
        db.session.commit()
        # Log de création de fiche technique
        log_activity(
            user_id=current_user.id,
            action='create',
            module='fiches_techniques',
            entity_id=fiche.id,
            entity_name=f"Fiche Technique {fiche.n_demande}",
            details={
                'intervention_id': intervention_id,
                'client': fiche.nom_raison_sociale,
                'technicien': f"{current_user.prenom} {current_user.nom}"
            }
        )
        flash('La fiche technique a été enregistrée avec succès.', 'success')
        return redirect(
            url_for('intervention_details', intervention_id=intervention_id))

    # Si une fiche technique existe déjà, on charge ses données
    if intervention.fiche_technique:
        for field in form:
            if hasattr(intervention.fiche_technique, field.name):
                field.data = getattr(intervention.fiche_technique, field.name)

    return render_template('fiche_technique_form.html',
                           form=form,
                           intervention=intervention)


""" @app.route('/save-survey/<int:intervention_id>', methods=['POST'])
@login_required
def save_survey(intervention_id):
    import sys
    print(f"[DEBUG] Appel de save_survey pour intervention_id={intervention_id}", file=sys.stderr)
    print(f"[DEBUG] request.form: {request.form}", file=sys.stderr)
    print(f"[DEBUG] request.files: {request.files}", file=sys.stderr)
    print(f"[DEBUG] request.headers: {dict(request.headers)}", file=sys.stderr)

    intervention = db.session.get(Intervention, intervention_id)
    if not intervention:
        abort(404)
    form = SurveyForm(request.form)
    action = request.form.get('action', 'save_and_continue')

    if form.validate_on_submit():
        try:
            # Créer un nouveau survey ou mettre à jour l'existant
            survey = Survey.query.filter_by(
                intervention_id=intervention_id).first()
            if not survey:
                survey = Survey(intervention_id=intervention_id)
                db.session.add(survey)

            # Mettre à jour les champs du survey
            survey.date_survey = form.date_survey.data
            survey.nom_raison_sociale = form.nom_raison_sociale.data
            survey.contact = form.contact.data
            survey.represente_par = form.represente_par.data
            survey.tel1 = form.tel1.data
            survey.tel2 = form.tel2.data
            survey.adresse_demande = form.adresse_demande.data
            survey.etage = form.etage.data
            survey.gps_lat = form.gps_lat.data
            survey.gps_long = form.gps_long.data
            survey.h_debut = form.h_debut.data
            survey.h_fin = form.h_fin.data
            survey.n_ligne = form.n_ligne.data
            survey.n_demande = form.n_demande.data
            survey.service_demande = form.service_demande.data
            survey.etat_client = form.etat_client.data
            survey.nature_local = form.nature_local.data
            survey.type_logement = form.type_logement.data
            survey.fibre_dispo = form.fibre_dispo.data
            survey.cuivre_dispo = form.cuivre_dispo.data
            survey.gpon_olt = form.gpon_olt.data
            survey.splitter = form.splitter.data
            survey.distance_fibre = form.distance_fibre.data
            survey.etat_fibre = form.etat_fibre.data
            survey.sr = form.sr.data
            survey.pc = form.pc.data
            survey.distance_cuivre = form.distance_cuivre.data
            survey.etat_cuivre = form.etat_cuivre.data
            survey.modem = form.modem.data
            survey.ont = form.ont.data
            survey.nb_prises = form.nb_prises.data
            survey.quantite_cable = form.quantite_cable.data
            survey.observation_tech = form.observation_tech.data
            survey.observation_client = form.observation_client.data
            survey.conclusion = form.conclusion.data
            survey.photo_batiment = form.photo_batiment.data
            survey.photo_environ = form.photo_environ.data
            survey.technicien_structure = form.technicien_structure.data
            survey.backoffice_structure = form.backoffice_structure.data
            survey.offre = form.offre.data
            survey.debit = form.debit.data
            survey.type_mi = form.type_mi.data
            survey.type_na = form.type_na.data
            survey.type_transfer = form.type_transfer.data
            survey.type_autre = form.type_autre.data
            survey.nro = form.nro.data
            survey.type_reseau = form.type_reseau.data
            survey.plaque = form.plaque.data
            survey.bpi = form.bpi.data
            survey.pbo = form.pbo.data
            survey.coupleur = form.coupleur.data
            survey.fibre = form.fibre.data
            survey.nb_clients = form.nb_clients.data
            survey.valeur_pbo_dbm = form.valeur_pbo_dbm.data
            survey.bpi_b1 = form.bpi_b1.data
            survey.pbo_b1 = form.pbo_b1.data
            survey.coupleur_b1 = form.coupleur_b1.data
            survey.nb_clients_b1 = form.nb_clients_b1.data
            survey.valeur_pbo_dbm_b1 = form.valeur_pbo_dbm_b1.data
            survey.description_logement_avec_bpi = form.description_logement_avec_bpi.data
            survey.description_logement_sans_bpi = form.description_logement_sans_bpi.data
            survey.emplacement_pto = form.emplacement_pto.data
            survey.passage_cable = form.passage_cable.data
            survey.longueur_tirage_pbo_bti = form.longueur_tirage_pbo_bti.data
            survey.longueur_tirage_bti_pto = form.longueur_tirage_bti_pto.data
            survey.materiel_existant_decodeur_carte = form.materiel_existant_decodeur_carte.data
            survey.materiel_existant_wifi_extender = form.materiel_existant_wifi_extender.data
            survey.materiel_existant_fax = form.materiel_existant_fax.data
            survey.materiel_existant_videosurveillance = form.materiel_existant_videosurveillance.data
            survey.qualite_ligne_adsl_defaut_couverture = form.qualite_ligne_adsl_defaut_couverture.data
            survey.qualite_ligne_adsl_lenteurs = form.qualite_ligne_adsl_lenteurs.data
            survey.qualite_ligne_adsl_deconnexions = form.qualite_ligne_adsl_deconnexions.data
            survey.qualite_ligne_adsl_ras = form.qualite_ligne_adsl_ras.data
            survey.niveau_wifi_salon = form.niveau_wifi_salon.data
            survey.niveau_wifi_chambre1 = form.niveau_wifi_chambre1.data
            survey.niveau_wifi_bureau1 = form.niveau_wifi_bureau1.data
            survey.niveau_wifi_autres_pieces = form.niveau_wifi_autres_pieces.data
            survey.choix_bf_hall = form.choix_bf_hall.data
            survey.choix_bf_chambre2 = form.choix_bf_chambre2.data
            survey.choix_bf_bureau2 = form.choix_bf_bureau2.data
            survey.choix_bf_mesure_dbm = form.choix_bf_mesure_dbm.data
            survey.cuisine_chambre3 = form.cuisine_chambre3.data
            survey.cuisine_bureau3 = form.cuisine_bureau3.data
            survey.cuisine_mesure_dbm = form.cuisine_mesure_dbm.data
            survey.repeteur_wifi_oui = form.repeteur_wifi_oui.data
            survey.repeteur_wifi_non = form.repeteur_wifi_non.data
            survey.repeteur_wifi_quantite = form.repeteur_wifi_quantite.data
            survey.repeteur_wifi_emplacement = form.repeteur_wifi_emplacement.data
            survey.cpl_oui = form.cpl_oui.data
            survey.cpl_non = form.cpl_non.data
            survey.cpl_quantite = form.cpl_quantite.data
            survey.cpl_emplacement = form.cpl_emplacement.data
            survey.cable_local_type = form.cable_local_type.data
            survey.cable_local_longueur = form.cable_local_longueur.data
            survey.cable_local_connecteurs = form.cable_local_connecteurs.data
            survey.goulottes_oui = form.goulottes_oui.data
            survey.goulottes_non = form.goulottes_non.data
            survey.goulottes_quantite = form.goulottes_quantite.data
            survey.goulottes_nombre_x2m = form.goulottes_nombre_x2m.data
            survey.survey_ok = form.survey_ok.data
            survey.survey_nok = form.survey_nok.data
            survey.motif = form.motif.data
            survey.commentaires = form.commentaires.data
            survey.signature_equipe = form.signature_equipe.data
            survey.signature_client = form.signature_client.data
            survey.client_tres_satisfait = form.client_tres_satisfait.data
            survey.client_satisfait = form.client_satisfait.data
            survey.client_pas_satisfait = form.client_pas_satisfait.data

            # Mettre à jour l'intervention
            intervention.survey_ok = form.survey_ok.data
            intervention.survey_date = datetime.now(timezone.utc)
            intervention.fichier_technique_accessible = 1 if form.survey_ok.data else 0

            db.session.commit()

            print("[DEBUG] Commit DB effectué", file=sys.stderr)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                print("[DEBUG] Requête AJAX détectée, retour JSON", file=sys.stderr)
                return jsonify({
                    'success': True,
                    'message': 'Survey enregistré avec succès',
                    'redirect': url_for('intervention_form', demande_id=intervention.demande_id)
                })

            flash(f'[DEBUG] Survey enregistré avec succès (action={action})', 'success')
            if action == 'save_only':
                print("[DEBUG] Redirection vers intervention_history", file=sys.stderr)
                return redirect(url_for('intervention_history'))
            else:
                print("[DEBUG] Redirection vers intervention_form", file=sys.stderr)
                return redirect(url_for('intervention_form', demande_id=intervention.demande_id))
        except Exception as e:
            db.session.rollback()
            print(f"[DEBUG] Exception: {str(e)}", file=sys.stderr)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'message': f"Erreur lors de l'enregistrement: {str(e)}"
                }), 500

            flash(f"[DEBUG] Erreur lors de l'enregistrement: {str(e)}", 'error')
            return redirect(
                url_for('intervention_form',
                        demande_id=intervention.demande_id))

    else:
        print("[DEBUG] Formulaire non validé, erreurs:", form.errors, file=sys.stderr)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'errors': form.errors,
                'message': 'Veuillez corriger les erreurs du formulaire'
            }), 400

        demande = db.session.get(DemandeIntervention, intervention.demande_id)
    if not demandeintervention:
        abort(404)
        flash(f"[DEBUG] Erreurs formulaire: {form.errors}", 'error')
        return render_template('intervention_form.html',
                               form=InterventionForm(obj=intervention),
                               survey_form=form,
                               demande=demande,
                               intervention=intervention)
"""

@app.route('/save-survey/<int:intervention_id>', methods=['POST'])
@login_required
def save_survey(intervention_id):
    try:
        # Vérification de base
        intervention = db.session.get(Intervention, intervention_id)
        if not intervention:
            abort(404)
        if intervention.technicien_id != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Accès non autorisé'
            }), 403

        # Initialisation du formulaire
        form = SurveyForm(request.form)
        action = request.form.get('action', 'save_and_continue')  # save_only ou save_and_continue

        # Validation du formulaire
        if not form.validate_on_submit():
            return jsonify({
                'success': False,
                'errors': form.errors,
                'message': 'Veuillez corriger les erreurs du formulaire'
            }), 400

        # Démarrer une transaction
        db.session.begin_nested()

        # Récupérer ou créer le survey
        survey = Survey.query.filter_by(intervention_id=intervention_id).first()
        if not survey:
            survey = Survey(intervention_id=intervention_id)
            db.session.add(survey)

        # Mise à jour des champs du survey
        for field in form:
            if hasattr(Survey, field.name):
                try:
                    column_type = getattr(Survey, field.name).type
                    if isinstance(column_type, db.Boolean):
                        setattr(survey, field.name, bool(field.data))
                    else:
                        setattr(survey, field.name, field.data)
                except Exception as e:
                    db.session.rollback()
                    return jsonify({
                        'success': False,
                        'message': f"Erreur dans le champ {field.name}: {str(e)}",
                        'field': field.name,
                        'error_type': str(type(e))
                    }), 400

        # Gestion des photos
        uploaded_files = request.files.getlist('photos[]')
        photo_paths = []
        for file in uploaded_files:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                unique_filename = f"{datetime.now().timestamp()}_{filename}"
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                file.save(save_path)
                photo_paths.append(unique_filename)

        if photo_paths:
            existing_photos = []
            if survey.photos:
                try:
                    existing_photos = json.loads(survey.photos)
                except json.JSONDecodeError:
                    existing_photos = survey.photos.split(',') if isinstance(survey.photos, str) else []
            all_photos = existing_photos + photo_paths
            survey.photos = json.dumps(all_photos)

        # Mise à jour des timestamps
        survey.updated_at = datetime.now(timezone.utc)

        #  Logique différente selon l’action
        if action == 'save_only':
            # On clôture directement l’intervention
            intervention.fichier_technique_accessible = 0
            intervention.date_fin = datetime.now(timezone.utc)
            intervention.statut = 'termine'

            if intervention.demande:
                intervention.demande.statut = 'termine'
                intervention.demande.date_completion = datetime.now(timezone.utc)

        else:
            intervention.survey_ok = form.survey_ok.data
            intervention.survey_date = datetime.now(timezone.utc)
            intervention.fichier_technique_accessible = 1 if form.survey_ok.data else 0

        db.session.commit()


        # Envoi du mail si survey validé
        if survey.survey_ok:
            create_sms_notification(current_user.id, intervention.demande_id, 'validation', notify_managers=True)
            destinataires = []
            demande = intervention.demande
            if demande:
                chef_pur = User.query.filter_by(role='chef_pur').first()
                if chef_pur and chef_pur.email:
                    destinataires.append(chef_pur.email)
                if demande.zone:
                    chef_zone = User.query.filter_by(role='chef_zone', zone=demande.zone).first()
                    if chef_zone and chef_zone.email:
                        destinataires.append(chef_zone.email)
                if demande.service:
                    chef_pilote = User.query.filter_by(role='chef_pilote', service=demande.service).first()
                    if chef_pilote and chef_pilote.email:
                        destinataires.append(chef_pilote.email)

            technicien_nom = f"{intervention.technicien.nom} {intervention.technicien.prenom}" if intervention.technicien else "N/A"
            equipe_nom = ""
            if intervention.equipe_id:
                equipe = db.session.get(Equipe, intervention.equipe_id)
                equipe_nom = equipe.nom_equipe if equipe else ""

            # Envoi mail notification validation
            try:
                if destinataires:
                    subject = "Survey à valider"
                    body = f"""Bonjour,

Un survey vient d'être enregistré et nécessite votre validation.

ND : {demande.nd if demande else 'N/A'}
Client : {demande.nom_client if demande else ''} {demande.prenom_client if demande else ''}
Zone : {demande.zone if demande else ''}
Service : {demande.service if demande else ''}
Technicien : {technicien_nom}
Équipe : {equipe_nom}

Merci de vous connecter à Sofatelcom pour valider ou rejeter ce survey.
"""
                    send_email(subject, destinataires, body=body)
            except Exception as post_e:
                current_app.logger.warning(f"Failed to send survey validation email: {str(post_e)}")

        # Réponse AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': 'Survey enregistré avec succès',
                'redirect': url_for('intervention_history') if action == 'save_only' else url_for('intervention_form', demande_id=intervention.demande_id)
            })

        # Redirection classique (fallback)
        if action == 'save_only':
            flash('Survey enregistré et intervention clôturée', 'success')
            return redirect(url_for('intervention_history'))
        else:
            flash('Survey enregistré avec succès', 'success')
            return redirect(url_for('intervention_form', demande_id=intervention.demande_id))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur inattendue: {traceback.format_exc()}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': f"Erreur technique lors de la sauvegarde: {str(e)}",
                'traceback': traceback.format_exc()
            }), 500

        flash(f"Erreur technique lors de la sauvegarde: {str(e)}", 'error')
        return redirect(url_for('intervention_form', demande_id=intervention.demande_id))


@app.route('/save-fiche-technique/<int:intervention_id>', methods=['POST'])
@login_required
def save_fiche_technique(intervention_id):
    try:
        # Vérification de base
        intervention = db.session.get(Intervention, intervention_id)
        if not intervention:
            abort(404)
        if intervention.technicien_id != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Accès non autorisé'
            }), 403

        # Initialisation du formulaire
        form = FicheTechniqueForm(request.form)

        # Validation du formulaire
        if not form.validate_on_submit():
            return jsonify({
                'success':
                False,
                'errors':
                form.errors,
                'message':
                'Veuillez corriger les erreurs du formulaire'
            }), 400

        # Démarrer une transaction
        db.session.begin_nested()

        # Gestion de la fiche technique
        fiche = FicheTechnique.query.filter_by(
            intervention_id=intervention_id).first()

        if not fiche:
            fiche = FicheTechnique(intervention_id=intervention_id,
                                   technicien_id=current_user.id,
                                   date_creation=datetime.now(timezone.utc))
            db.session.add(fiche)

        # Mise à jour des champs avec gestion des erreurs
        for field in form:
            if hasattr(fiche, field.name):
                try:
                    # Conversion spéciale pour les champs booléens
                    if isinstance(
                            getattr(FicheTechnique, field.name).type,
                            db.Boolean):
                        setattr(fiche, field.name, bool(field.data))
                    else:
                        setattr(fiche, field.name, field.data)
                except Exception as e:
                    db.session.rollback()
                    return jsonify({
                        'success': False,
                        'message':
                        f"Erreur dans le champ {field.name}: {str(e)}",
                        'field': field.name,
                        'error_type': str(type(e))
                    }), 400
        # Gestion des photos uploadées
        uploaded_files = request.files.getlist('photos[]')
        photo_paths = []

        for file in uploaded_files:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                unique_filename = f"{datetime.now().timestamp()}_{filename}"
                save_path = os.path.join(app.config['UPLOAD_FOLDER'],
                                         unique_filename)
                
                # Créer le dossier s'il n'existe pas
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                
                file.save(save_path)
                photo_paths.append(unique_filename)  # Stocker uniquement le nom du fichier

        # Si des photos ont été uploadées, les sauvegarder dans la fiche technique
        if photo_paths:
            # Si des photos existent déjà, les fusionner avec les nouvelles
            existing_photos = []
            if fiche.photos:
                try:
                    existing_photos = json.loads(fiche.photos)
                except json.JSONDecodeError:
                    existing_photos = fiche.photos.split(',') if isinstance(fiche.photos, str) else []
            
            # Ajouter les nouvelles photos aux existantes
            all_photos = existing_photos + photo_paths
            fiche.photos = json.dumps(all_photos)

        # Mise à jour des timestamps
        fiche.updated_at = datetime.now(timezone.utc)

        # Mise à jour de l'intervention associée
        intervention.date_fin = datetime.now(timezone.utc)
        intervention.statut = 'termine'

        # Mise à jour de la demande
        if intervention.demande:
            intervention.demande.statut = 'termine'
            intervention.demande.date_completion = datetime.now(timezone.utc)

        # Créer notification de fiche technique terminée
        create_sms_notification(current_user.id, intervention.demande_id, 'validation', notify_managers=True)
        # Validation finale
        try:
            db.session.commit()

            # Envoi mail pour validation fiche technique
            destinataires = []
            demande = intervention.demande

            if demande:
                # Chef PUR
                chef_pur = User.query.filter_by(role='chef_pur').first()
                if chef_pur and chef_pur.email:
                    destinataires.append(chef_pur.email)
                # Chef Zone
                if demande.zone:
                    chef_zone = User.query.filter_by(
                        role='chef_zone', zone=demande.zone).first()
                    if chef_zone and chef_zone.email:
                        destinataires.append(chef_zone.email)
                # Chef Pilote
                if demande.service:
                    chef_pilote = User.query.filter_by(
                        role='chef_pilote', service=demande.service).first()
                    if chef_pilote and chef_pilote.email:
                        destinataires.append(chef_pilote.email)
                # Récupérer le nom du technicien
                technicien_nom = f"{intervention.technicien.nom} {intervention.technicien.prenom}" if intervention.technicien else "N/A"
                # Récupérer le nom de l'équipe liée
                equipe_nom = ""
                if intervention.equipe_id:
                    equipe = db.session.get(Equipe, intervention.equipe_id)
                    equipe_nom = equipe.nom_equipe if equipe else ""

                subject = "Fiche technique à valider"
                body = f"""Bonjour,\n\nUne fiche technique vient d'être enregistrée et nécessite votre validation.\n
                ND : {demande.nd}\nClient : {demande.nom_client} {demande.prenom_client}\nZone : {demande.zone}\nService : {demande.service}\n
                Technicien : {technicien_nom}\nÉquipe : {equipe_nom}\n
                Merci de vous connecter à Sofatelcom pour valider ou rejeter cette fiche technique."""
                if destinataires:
                    send_email(subject, destinataires, body=body)

            return jsonify({
                'success': True,
                'message':
                'Fiche technique et intervention enregistrées avec succès',
                'redirect': url_for('dashboard')
            })
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur d'intégrité: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Erreur de cohérence dans la base de données',
                'error': str(e.orig)
            }), 500

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erreur inattendue: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': 'Erreur technique lors de la sauvegarde',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/toggle-equipe-status/<int:equipe_id>', methods=['POST'])
@login_required
def toggle_equipe_status(equipe_id):
    equipe = db.session.get(Equipe, equipe_id)
    if not equipe:
        abort(404)
    # Optionnel : vérifier que seul le chef_zone de l’équipe peut changer le statut
    if current_user.role != 'chef_zone' or equipe.chef_zone_id != current_user.id:
        return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403
    try:
        data = request.get_json() or {}
        actif = data.get('actif')
        if actif is None:
            return jsonify({
                'success': False,
                'error': 'Valeur du statut manquante'
            }), 400
        equipe.actif = bool(actif)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/equipes-inactives')
@login_required
def api_equipes_inactives():
    if current_user.role != 'chef_zone':
        return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403
    equipes = Equipe.query.filter_by(actif=False, zone=current_user.zone).all()
    equipes_data = []
    for equipe in equipes:
        equipes_data.append({
            'id':
            equipe.id,
            'zone':
            equipe.zone,
            'nom_equipe':
            equipe.nom_equipe,
            'service':
            equipe.service,
            'technologies':
            equipe.technologies,
            'nb_membres':
            len(equipe.membres) if hasattr(equipe, 'membres') else 0
        })
    return jsonify({'success': True, 'equipes': equipes_data})


# API endpoints for detailed statistics
@app.route('/api/stats/details/<stats_type>')
@login_required
def get_stats_details(stats_type):
    """Get detailed data for statistics cards"""
    if current_user.role != 'chef_pur':
        return jsonify({'error': 'Access denied'}), 403

    today = datetime.now().date()
    limit = request.args.get('limit', 20, type=int)

    try:
        if stats_type == 'total_demandes':
            demandes = DemandeIntervention.query.order_by(
                DemandeIntervention.date_creation.desc()).limit(limit).all()
            items = []
            for d in demandes:
                items.append({
                    'numero_demande':
                    d.nd,
                    'nom_client':
                    d.nom_client,
                    'service_demande':
                    d.service,
                    'zone':
                    d.zone,
                    'date_creation':
                    d.date_creation.isoformat() if d.date_creation else None,
                    'statut':
                    d.statut
                })
            total = DemandeIntervention.query.count()
            
            # --- AJOUT DU DÉTAIL PAR SERVICE ET TECHNOLOGIE ---
            detail_service_tech = {}
            for service in ['SAV', 'Production']:
                detail_service_tech[service] = {}
                for tech in ['Fibre', 'Cuivre', '5G']:
                    count = DemandeIntervention.query.filter_by(service=service, type_techno=tech).count()
                    detail_service_tech[service][tech] = count

            details = {
                'service_tech': detail_service_tech
            }

        elif stats_type in ['demande_jour','demandes_jour_sav', 'demandes_jour_production']:
            service = 'SAV' if stats_type == 'demandes_jour_sav' else 'Production'
            demandes = DemandeIntervention.query.filter(
                db.func.date(DemandeIntervention.date_creation) == today,
                DemandeIntervention.service == service
            ).order_by(
                DemandeIntervention.date_creation.desc()
            ).limit(limit).all()
            items = []
            for d in demandes:
                items.append({
                    'id': d.id,
                    'numero_demande': d.nd,
                    'age': d.age,
                    'priorite_traitement': d.priorite_traitement,
                    'offre': d.offre,
                    'nom_client': d.nom_client,
                    'service_demande': d.service,
                    'zone': d.zone,
                    'date_creation': d.date_creation.isoformat() if d.date_creation else None,
                    'statut': d.statut
                })
            total = DemandeIntervention.query.filter(
                db.func.date(DemandeIntervention.date_creation) == today,
                DemandeIntervention.service == service
            ).count()
            # Détail par âge, priorité, offre
            demandes_jour_query = DemandeIntervention.query.filter(
                db.func.date(DemandeIntervention.date_creation) == today,
                DemandeIntervention.service == service,
                DemandeIntervention.statut.in_(['nouveau', 'a_reaffecter'])
            )
            age_ids, priorite_ids, offre_ids = {}, {}, {}
            for d in demandes_jour_query.all():
                age_val = d.age if d.age is not None else ''
                age_ids.setdefault(age_val, []).append(d.id)
                priorite_val = d.priorite_traitement if d.priorite_traitement is not None else ''
                priorite_ids.setdefault(priorite_val, []).append(d.id)
                offre_val = d.offre if d.offre is not None else ''
                offre_ids.setdefault(offre_val, []).append(d.id)
            age_stats = demandes_jour_query.with_entities(
                DemandeIntervention.age, db.func.count()).group_by(DemandeIntervention.age).all()
            priorite_stats = demandes_jour_query.with_entities(
                DemandeIntervention.priorite_traitement, db.func.count()).group_by(DemandeIntervention.priorite_traitement).all()
            offre_stats = demandes_jour_query.with_entities(
                DemandeIntervention.offre, db.func.count()).group_by(DemandeIntervention.offre).all()
            details = {
                'age': dict(age_stats),
                'priorite_traitement': dict(priorite_stats),
                'offre': dict(offre_stats),
                'age_ids': age_ids,
                'priorite_ids': priorite_ids,
                'offre_ids': offre_ids
            }
        
        elif stats_type == 'interventions_cours':
            interventions = Intervention.query.filter_by(
                statut='en_cours').limit(limit).all()
            items = []
            for i in interventions:
                items.append({
                    'numero_intervention':
                    i.demande.nd,
                    'nom_client':
                    i.demande.nom_client if i.demande else '',
                    'technicien_nom':
                    f"{i.technicien_user.nom} {i.technicien_user.prenom}"
                    if i.technicien_user else '',
                    'zone':
                    i.demande.zone if i.demande else '',
                    'date_planifiee':
                    i.date_debut.isoformat() if i.date_debut else None,
                    'statut':
                    i.statut
                })
            total = Intervention.query.filter_by(statut='en_cours').count()

        elif stats_type in ['interventions_validees', 'interventions_validees_sav', 'interventions_validees_production']:
            service = 'SAV' if stats_type == 'interventions_validees_sav' else 'Production'
            interventions = Intervention.query.join(DemandeIntervention).filter(
                Intervention.statut == 'valide',
                db.func.date(Intervention.date_validation) == today,
                DemandeIntervention.service == service
            ).order_by(
                Intervention.date_validation.desc()
            ).limit(limit).all()
            items = []
            for i in interventions:
                items.append({
                    'numero_intervention':
                    i.demande.nd,
                    'nom_client':
                    i.demande.nom_client if i.demande else '',
                    'technicien_nom':
                    f"{i.technicien_user.nom} {i.technicien_user.prenom}"
                    if i.technicien_user else '',
                    'zone':
                    i.demande.zone if i.demande else '',
                    'date_planifiee':
                    i.date_debut.isoformat() if i.date_debut else None,
                    'statut':
                    i.statut
                })
            total = Intervention.query.join(DemandeIntervention).filter(
                Intervention.statut == 'valide',
                db.func.date(Intervention.date_validation) == today,
                DemandeIntervention.service == service
            ).count()

        elif stats_type == 'attente_validation':
            interventions = Intervention.query.filter_by(
                statut='termine').order_by(
                    Intervention.date_validation.desc()).limit(limit).all()
            items = []
            for i in interventions:
                items.append({
                    'numero_intervention':
                    i.demande.nd,
                    'nom_client':
                    i.demande.nom_client if i.demande else '',
                    'technicien_nom':
                    f"{i.technicien_user.nom} {i.technicien_user.prenom}"
                    if i.technicien_user else '',
                    'zone':
                    i.demande.zone if i.demande else '',
                    'date_planifiee':
                    i.date_debut.isoformat() if i.date_debut else None,
                    'statut':
                    i.statut
                })
            total = Intervention.query.filter_by(statut='termine').count()

        elif stats_type == 'interventions_rejetees':
            interventions = Intervention.query.filter_by(
                statut='rejete').order_by(
                    Intervention.date_validation.desc()).limit(limit).all()
            items = []
            for i in interventions:
                items.append({
                    'numero_intervention':
                    i.demande.nd,
                    'nom_client':
                    i.demande.nom_client if i.demande else '',
                    'technicien_nom':
                    f"{i.technicien_user.nom} {i.technicien_user.prenom}"
                    if i.technicien_user else '',
                    'zone':
                    i.demande.zone if i.demande else '',
                    'date_planifiee':
                    i.date_debut.isoformat() if i.date_debut else None,
                    'statut':
                    i.statut
                })
            total = Intervention.query.filter_by(statut='rejete').count()

        else:
            return jsonify({'error': 'Invalid stats type'}), 400
        if 'details' not in locals():
            details = {}
        return jsonify({'items': items, 'total': total, 'showing': len(items), 'details': details})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/zone_stats/details/<stats_type>')
@login_required
def get_zone_stats_details(stats_type):
    zone = current_user.zone
    today = datetime.now().date()
    limit = request.args.get('limit', 20, type=int)
    items = []
    total = 0

    try:
        if stats_type == 'equipes_jour':
            equipes = Equipe.query.filter_by(zone=zone).filter(
                db.func.date(Equipe.date_publication) == today).order_by(
                    Equipe.date_publication.desc()).limit(limit).all()
            for e in equipes:
                items.append({
                    'nom_equipe': e.nom_equipe,
                    'zone': e.zone,
                    'service': e.service,
                    'technologies': e.technologies,
                    'nb_membres': len(e.membres),
                    'publie': e.publie
                })
            total = Equipe.query.filter_by(zone=zone).filter(
                db.func.date(Equipe.date_publication) == today).count()

        elif stats_type == 'techniciens_zone':
            techniciens = User.query.filter_by(zone=zone,
                                               role='technicien',
                                               actif=True).limit(limit).all()
            for t in techniciens:
                items.append({
                    'nom': f"{t.prenom} {t.nom}",
                    'zone': t.zone,
                    'technologies': t.technologies,
                })
            total = User.query.filter_by(zone=zone,
                                         role='technicien',
                                         actif=True).count()

        elif stats_type == 'interventions_cours':
            interventions = Intervention.query.join(User, Intervention.technicien_id == User.id)\
                .filter(User.zone == zone, Intervention.statut == 'en_cours')\
                .order_by(Intervention.date_debut.desc()).limit(limit).all()
            for i in interventions:
                items.append({
                    'numero_intervention':
                    i.numero,
                    'nom_client':
                    i.demande.nom_client if i.demande else '',
                    'technicien_nom':
                    f"{i.technicien.prenom} {i.technicien.nom}"
                    if i.technicien else '',
                    'zone':
                    i.demande.zone if i.demande else zone,
                    'date_planifiee':
                    i.date_debut.isoformat() if i.date_debut else None,
                    'statut':
                    i.statut
                })
            total = Intervention.query.join(User, Intervention.technicien_id == User.id)\
                .filter(User.zone == zone, Intervention.statut == 'en_cours').count()

        elif stats_type == 'interventions_terminees_jour':
            interventions = Intervention.query.join(User, Intervention.technicien_id == User.id)\
                .filter(
                    User.zone == zone,
                    Intervention.statut == 'termine',
                    db.func.date(Intervention.date_fin) == today
                ).order_by(Intervention.date_fin.desc()).limit(limit).all()
            for i in interventions:
                items.append({
                    'numero_intervention':
                    i.numero,
                    'nom_client':
                    i.demande.nom_client if i.demande else '',
                    'technicien_nom':
                    f"{i.technicien.prenom} {i.technicien.nom}"
                    if i.technicien else '',
                    'zone':
                    i.demande.zone if i.demande else zone,
                    'date_planifiee':
                    i.date_fin.isoformat() if i.date_fin else None,
                    'statut':
                    i.statut
                })
            total = Intervention.query.join(User, Intervention.technicien_id == User.id)\
                .filter(
                    User.zone == zone,
                    Intervention.statut == 'termine',
                    db.func.date(Intervention.date_fin) == today
                ).count()

        else:
            return jsonify({'error': 'Invalid stats type'}), 400

        return jsonify({'items': items, 'total': total, 'showing': len(items)})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# API routes for daily team publication
@app.route('/api/publication-stats')
@login_required
def get_publication_stats():
    """Get daily team publication statistics"""
    if current_user.role not in ['chef_zone', 'chef_pur']:
        return jsonify({'error': 'Access denied'}), 403

    today = datetime.now().date()

    # Get teams created today by this chef zone
    teams_created = Equipe.query.filter_by(chef_zone_id=current_user.id,
                                           date_creation=today).count()

    teams_published = Equipe.query.filter_by(chef_zone_id=current_user.id,
                                             zone=current_user.zone,
                                             actif=True,
                                             date_publication=today,
                                             publie=True).count()

    teams_draft = teams_created - teams_published

    # Get last publication time
    last_published = Equipe.query.filter_by(chef_zone_id=current_user.id,
                                            zone=current_user.zone,
                                            date_publication=today,
                                            publie=True).order_by(
                                                Equipe.id.desc()).first()

    last_publication = None
    if last_published:
        last_publication = last_published.date_publication.strftime(
            '%H:%M') if last_published.date_publication else None
    # Get all unpublished teams by this chef zone
    unpublished_teams = Equipe.query.filter_by(chef_zone_id=current_user.id,
                                               zone=current_user.zone,
                                               actif=True,
                                               publie=False).count()
    total_teams = Equipe.query.filter_by(
        chef_zone_id=current_user.id,
        zone=current_user.zone,
    ).count()
    return jsonify({
        'success': True,
        'stats': {
            'created': teams_created,
            'published': teams_published,
            'unpublished': unpublished_teams,
            'total': total_teams,
            'draft': teams_draft,
            'last_publication': last_publication
        }
    })


@app.route('/api/publish-daily-teams', methods=['POST'])
@login_required
def publish_daily_teams():
    """Publish all unpublished teams for this chef zone"""
    if current_user.role not in ['chef_zone', 'chef_pur']:
        return jsonify({'error': 'Access denied'}), 403

    now = datetime.now()
    today = now.date()

    try:
        # Get all unpublished teams by this chef zone
        unpublished_teams = Equipe.query.filter_by(
            chef_zone_id=current_user.id,
            zone=current_user.zone,
            actif=True,
            publie=False).all()

        published_count = 0
        for team in unpublished_teams:
            team.publie = True
            team.date_publication = today
            published_count += 1

        db.session.commit()

        return jsonify({
            'success':
            True,
            'published_count':
            published_count,
            'message':
            f'{published_count} équipe(s) publiée(s) avec succès'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/preview-teams')
@login_required
def preview_teams():
    """Preview teams created today for publication"""
    if current_user.role != 'chef_zone':
        return jsonify({'error': 'Access denied'}), 403

    today = datetime.now().date()

    try:
        teams = Equipe.query.filter_by(chef_zone_id=current_user.id,
                                       zone=current_user.zone,
                                       actif=True,
                                       date_creation=today).all()

        teams_data = []
        for team in teams:
            teams_data.append({
                'id':
                team.id,
                'nom_equipe':
                team.nom_equipe,
                'zone':
                team.zone,
                'service':
                team.service,
                'technologies':
                team.technologies,
                'nb_membres':
                len(team.membres) if hasattr(team, 'membres') else 0,
                'publie':
                team.publie,
                'date_creation':
                team.date_creation.isoformat(),
                'date_publication':
                team.date_publication.isoformat()
                if team.date_publication else None
            })

        return jsonify({'success': True, 'teams': teams_data})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/publish-selected-teams', methods=['POST'])
@login_required
def publish_selected_teams():
    """Publish specific selected teams"""
    if current_user.role not in ['chef_zone', 'chef_pur']:
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    team_ids = data.get('team_ids', [])

    if not team_ids:
        return jsonify({
            'success': False,
            'error': 'Aucune équipe sélectionnée'
        }), 400

    today = datetime.now().date()

    try:
        if current_user.role == 'chef_pur':
            # Chef PUR peut publier n'importe quelle équipe active non publiée
            teams_to_publish = Equipe.query.filter(
                Equipe.id.in_(team_ids),
                Equipe.actif == True,
                Equipe.publie == False
            ).all()
        else:
            # Chef Zone ne publie que ses propres équipes
            teams_to_publish = Equipe.query.filter(
                Equipe.id.in_(team_ids),
                Equipe.chef_zone_id == current_user.id,
                Equipe.zone == current_user.zone,
                Equipe.actif == True,
                Equipe.publie == False
            ).all()

        published_count = 0
        for team in teams_to_publish:
            team.publie = True
            team.date_publication = today
            published_count += 1

        db.session.commit()

        return jsonify({
            'success': True,
            'published_count': published_count,
            'message': f'{published_count} équipe(s) sélectionnée(s) publiée(s) avec succès'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500



@app.route('/intervention/reject', methods=['POST'])
@login_required
def reject_intervention():
    data = request.get_json()
    intervention_id = data.get('intervention_id')
    motif = data.get('motif', '').strip()

    if not intervention_id or not motif:
        return jsonify({
            'success': False,
            'message': 'Motif obligatoire.'
        }), 400

    intervention = db.session.get(Intervention, intervention_id)
    if not intervention:
        return jsonify({
            'success': False,
            'message': 'Intervention introuvable.'
        }), 404

    # Vérifie que l'utilisateur est bien le technicien affecté
    if intervention.technicien_id != current_user.id:
        return jsonify({'success': False, 'message': 'Non autorisé.'}), 403

    # Met à jour le statut et le motif
    intervention.statut = 'rejete'
    intervention.motif_rejet = motif
    # Mettre à jour le statut de la demande liée
    if intervention.demande:
        intervention.demande.statut = 'a_reaffecter'
    db.session.commit()

    # Créer notification de rejet
    #create_sms_notification(current_user.id, intervention.demande_id, 'rejet')
    create_sms_notification(current_user.id, intervention.demande_id, 'urgence', notify_managers=True)
    # Notifie le chef pilote (exemple simple, adapte selon ton système)
    """ notif = NotificationSMS(
        technicien_id=intervention.technicien_id,
        message=
        f"Intervention #{intervention.id} rejetée par {current_user.prenom} : {motif}",
        type_notification='urgent')
    db.session.add(notif)"""
    db.session.commit() 
    log_activity(
        user_id=current_user.id,
        action='reject',
        module='interventions',
        entity_id=intervention.id,
        entity_name=f"Intervention {intervention.demande.nd if intervention.demande else 'N/A'}",
        details={
            'motif': motif,
            'technicien': f"{intervention.technicien.prenom} {intervention.technicien.nom}" if intervention.technicien else 'N/A'
        }
    )
    # Envoi mail au chef_pur, chef_zone et chef_pilote
    destinataires = []
    demande = intervention.demande
    if demande:
        chef_pur = User.query.filter_by(role='chef_pur').first()
        if chef_pur and chef_pur.email:
            destinataires.append(chef_pur.email)
        if demande.zone:
            chef_zone = User.query.filter_by(role='chef_zone',
                                             zone=demande.zone).first()
            if chef_zone and chef_zone.email:
                destinataires.append(chef_zone.email)
        if demande.service:
            chef_pilote = User.query.filter_by(
                role='chef_pilote', service=demande.service).first()
            if chef_pilote and chef_pilote.email:
                destinataires.append(chef_pilote.email)
        technicien_nom = f"{current_user.nom} {current_user.prenom}"
        equipe_nom = ""
        if intervention.equipe_id:
            equipe = db.session.get(Equipe, intervention.equipe_id)
            equipe_nom = equipe.nom_equipe if equipe else ""
        # Envoi mail notification rejet
        try:
            if destinataires:
                subject = "Intervention rejetée"
                body = f"""Bonjour,\n\nL'intervention #{intervention.id} a été rejetée par le technicien.\n
                ND : {demande.nd}\nClient : {demande.nom_client} {demande.prenom_client}\nZone : {demande.zone}\nService : {demande.service}\n
                Technicien : {technicien_nom}\nÉquipe : {equipe_nom}\nMotif du rejet : {motif}\n
                Merci de vous connecter à Sofatelcom pour réaffecter la demande."""
                send_email(subject, destinataires, body=body)
        except Exception as post_e:
            current_app.logger.warning(f"Failed to send rejection email: {str(post_e)}")
    return jsonify({'success': True})


@app.route('/api/stats/performance')
@login_required
def api_stats_performance():
    """
    API pour récupérer les données de performance:
    - Teams (équipes avec leurs interventions validées)
    - Zones (chefs zone avec leurs statistiques)
    - Pilots (chefs pilote avec leurs statistiques)
    
    Accès restreint aux chefs PUR uniquement.
    """
    if current_user.role != 'chef_pur':
        return jsonify({'error': 'Accès refusé'}), 403

    try:
        # Utilisation de la fonction unifiée et optimisée
        perf_data = get_unified_performance_data(period=request.args.get('period', 'day'))
        
        return jsonify({
            'teams': perf_data.get('equipes', []),
            'zones': perf_data.get('zones', []),
            'pilots': perf_data.get('pilots', []),
            'technicians': perf_data.get('techniciens', []),
            'metadata': {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': 'unified_kpi_engine'
            }
        })

    except Exception as e:
        logger.error(f"[ERROR] API stats/performance failed: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Erreur lors du calcul des statistiques',
            'teams': [],
            'zones': [],
            'pilots': []
        }), 500


@app.route('/validate_interventions')
@login_required
def validate_interventions():
    if current_user.role not in ['chef_pur', 'chef_pilote', 'chef_zone']:
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('dashboard'))

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 25, type=int),
                   100)  # Limite à 100

    # Filtrer les interventions selon le rôle de l'utilisateur
    query = Intervention.query.filter_by(statut='termine')

    if current_user.role == 'chef_pilote' and current_user.service:
        # Filtrer par service via la demande d'intervention
        query = query.join(DemandeIntervention).filter_by(
            service=current_user.service)
    elif current_user.role == 'chef_zone' and current_user.zone:
        # Filtrer par zone via le technicien
        query = query.join(User,
                           Intervention.technicien_id == User.id).filter_by(
                               zone=current_user.zone)

    interventions = query.order_by(Intervention.date_fin.desc()).paginate(
        page=page, per_page=per_page, error_out=False)

    return render_template('validate_interventions.html',
                           interventions=interventions)


@app.route('/validate_intervention_action/<int:intervention_id>',
           methods=['POST'])
@login_required
def validate_intervention_action(intervention_id):
    if current_user.role not in ['chef_pur', 'chef_pilote', 'chef_zone']:
        return jsonify({'success': False, 'error': 'Accès non autorisé'})

    intervention = db.session.get(Intervention, intervention_id)
    if not intervention:
        abort(404)

    # Vérifications d'autorisation selon le rôle
    if current_user.role == 'chef_pilote' and current_user.service:
        if not intervention.demande or intervention.demande.service != current_user.service:
            return jsonify({
                'success': False,
                'error': 'Intervention hors de votre service'
            })
    elif current_user.role == 'chef_zone' and current_user.zone:
        if not intervention.technicien_user or intervention.technicien_user.zone != current_user.zone:
            return jsonify({
                'success': False,
                'error': 'Intervention hors de votre zone'
            })

    try:
        data = request.get_json()
        action = data.get('action')  # 'validate' ou 'reject'
        commentaire = data.get('commentaire', '')

        if action == 'validate':
            intervention.statut = 'valide'
            intervention.date_validation = datetime.now()
            intervention.valide_par = current_user.id
            intervention.commentaire_validation = commentaire
            # Créer notification de validation pour le technicien
            create_sms_notification(intervention.technicien_id, intervention.demande_id, 'validation', notify_managers=True)
            # Log de validation
            log_activity(
                user_id=current_user.id,
                action='validate',
                module='interventions',
                entity_id=intervention.id,
                entity_name=f"Intervention {intervention.demande.nd if intervention.demande else 'N/A'}",
                details={
                    'statut': 'valide',
                    'technicien': f"{intervention.technicien.prenom} {intervention.technicien.nom}" if intervention.technicien else 'N/A',
                    'demande_nd': intervention.demande.nd if intervention.demande else 'N/A'
                }
            )
        elif action == 'reject':
            intervention.statut = 'rejete'
            intervention.date_validation = datetime.now()
            intervention.valide_par = current_user.id
            intervention.motif_rejet = commentaire
            # Remettre la demande en statut à réaffecter
            if intervention.demande:
                intervention.demande.statut = 'a_reaffecter'
            # Créer notification de rejet pour le technicien
            create_sms_notification(intervention.technicien_id, intervention.demande_id, 'rejet', notify_managers=True)
            # Log de rejet
            log_activity(
                user_id=current_user.id,
                action='reject',
                module='interventions',
                entity_id=intervention.id,
                entity_name=f"Intervention {intervention.demande.nd if intervention.demande else 'N/A'}",
                details={
                    'statut': 'rejete',
                    'commentaire': commentaire,
                    'technicien': f"{intervention.technicien.prenom} {intervention.technicien.nom}" if intervention.technicien else 'N/A'
                }
            )
        else:
            return jsonify({'success': False, 'error': 'Action non reconnue'})

        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Intervention traitée avec succès'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})


# Routes pour la gestion des utilisateurs
@app.route('/create-user', methods=['GET', 'POST'])
@login_required
def create_user():
    if current_user.role != 'chef_pur':
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('dashboard'))

    form = CreateUserForm()
    if form.validate_on_submit():
        try:
            # Debug: Afficher les données du formulaire
            print(f"DEBUG: Données formulaire - Zone: {form.zone.data}, Type: {type(form.zone.data)}, Rôle: {form.role.data}")
            print(f"DEBUG: Erreurs de validation: {form.errors}")
            
            # Vérifier si l'utilisateur existe déjà
            existing_user = User.query.filter(
                (User.username == form.username.data)
                | (User.email == form.email.data)).first()

            if existing_user:
                flash(
                    'Un utilisateur avec ce nom d\'utilisateur ou cette adresse email existe déjà.',
                    'error')
                return render_template('create_user.html', form=form)

            # Debug: Afficher toutes les données du formulaire
            print(f"DEBUG: Form data - {form.data}")
            print(f"DEBUG: Zone brute: {form.zone.data}, Type: {type(form.zone.data)}")
            print(f"DEBUG: Zone raw_data: {form.zone.raw_data if hasattr(form.zone, 'raw_data') else 'No raw_data'}")
            
            # ========== ZONE ASSIGNMENT FOR ROLE-BASED USERS ==========
            # Gestion spécifique de l'affectation de zone selon le rôle
            zone_id = None
            zone_name = None  # Pour le champ legacy 'zone'
            if form.role.data in ['chef_zone', 'magasinier', 'technicien']:
                # Ces rôles nécessitent une zone obligatoire
                if form.zone.data and form.zone.data != 0 and str(form.zone.data) != '0':
                    try:
                        zone_id = int(form.zone.data)
                        # Vérifier que la zone existe
                        zone = Zone.query.get(zone_id)
                        if not zone:
                            flash(f'La zone sélectionnée (ID: {zone_id}) n\'existe pas.', 'error')
                            return render_template('create_user.html', form=form)
                        # Pour les rôles legacy, assigner aussi le nom de la zone
                        zone_name = zone.nom  # Utiliser le nom de la zone pour le champ legacy
                        print(f"DEBUG: Zone assignée - ID: {zone_id}, Nom: {zone.nom}, Rôle: {form.role.data}")
                    except (ValueError, TypeError):
                        print(f"DEBUG: Erreur conversion zone - Valeur: {form.zone.data}, Type: {type(form.zone.data)}")
                        flash('Erreur de conversion de la zone. Veuillez réessayer.', 'error')
                        return render_template('create_user.html', form=form)
                else:
                    # La zone est obligatoire pour ces rôles
                    role_display = {'chef_zone': 'Chef de zone', 'magasinier': 'Magasinier', 'technicien': 'Technicien'}.get(form.role.data, form.role.data)
                    flash(f'Une zone doit être affectée pour un {role_display}.', 'error')
                    return render_template('create_user.html', form=form)
            
            # Créer le nouvel utilisateur
            new_user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=generate_password_hash(form.password.data),
                role=form.role.data,
                nom=form.nom.data,
                prenom=form.prenom.data,
                telephone=form.telephone.data,
                zone=zone_name,  # Champ legacy pour chef_zone et technicien
                zone_id=zone_id,  # FK vers la table zone
                commune=form.commune.data if form.commune.data else None,
                quartier=form.quartier.data if form.quartier.data else None,
                service=form.service.data if form.service.data else None,
                technologies=form.technologies.data
                if form.technologies.data else None)

            db.session.add(new_user)
            db.session.commit()
            
            # Post-commit actions (logging and email) should not crash the main flow
            # since the user is already successfully created in the database.
            try:
                # Log de création d'utilisateur
                log_activity(
                    user_id=current_user.id,
                    action='create',
                    module='users',
                    entity_id=new_user.id,
                    entity_name=f"{new_user.prenom} {new_user.nom}",
                    details={
                        'username': new_user.username,
                        'role': new_user.role,
                        'zone_id': new_user.zone_id
                    }
                )
                
                if new_user.email:
                    subject = "Bienvenue sur Sofatelcom"
                    body = f"""Bonjour {new_user.nom},

            Votre compte Sofatelcom a été créé.

            Identifiant : {new_user.username}
            Mot de passe : passer (à réinitialiser)

            Connectez-vous sur : https://sofatelcom.louvrier.sn/login

            Merci,
            L'équipe Sofatelcom
            """
                    send_email(subject, [new_user.email], body=body)
            except Exception as post_e:
                current_app.logger.error(f"Post-creation background task failed for user {new_user.username}: {str(post_e)}")
                # We don't flash an error here to not confuse the user, 
                # but we could add a subtle info flash if email failing is important.
            
            flash(f"Utilisateur {new_user.username} créé avec succès !", 'success')
            return redirect(url_for('manage_users'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.exception('Erreur lors de la création d\'utilisateur')
            
            # Provide user-friendly error messages
            error_msg = str(e).lower()
            if 'unique constraint' in error_msg or 'duplicate' in error_msg:
                user_msg = 'Un utilisateur avec ce nom d\'utilisateur ou cette adresse email existe déjà.'
            elif 'field' in error_msg or 'column' in error_msg:
                user_msg = 'Erreur de configuration de la base de données. Contactez l\'administrateur.'
            else:
                user_msg = 'Une erreur est survenue lors de la création de l\'utilisateur. Réessayez ou contactez l\'administrateur.'
            
            flash(user_msg, 'error')

    else:
        # Debug: Afficher les erreurs si le formulaire n'est pas valide
        print(f"DEBUG: Formulaire non valide - Erreurs: {form.errors}")
        if request.method == 'POST':
            print(f"DEBUG: POST data - {request.form}")

    return render_template('create_user.html', form=form)


@app.route('/manage-users')
@app.route('/manage_users')
@login_required
def manage_users():
    if current_user.role != 'chef_pur':
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('dashboard'))

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    search = request.args.get('search', '').strip()
    role = request.args.get('role', '')
    status = request.args.get('status', '')

    query = User.query

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            db.or_(
                User.username.ilike(search_filter),
                User.email.ilike(search_filter),
                User.nom.ilike(search_filter),
                User.prenom.ilike(search_filter),
                User.telephone.ilike(search_filter)
            )
        )
    
    if role:
        query = query.filter(User.role == role)
    
    if status:
        query = query.filter(User.actif == (status == 'actif'))

    users = query.order_by(User.date_creation.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return render_template('manage_users.html', users=users, search=search, current_role=role, current_status=status)


@app.route('/edit-user/<int:user_id>', methods=['GET', 'POST'])
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'chef_pur':
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('dashboard'))

    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    form = EditUserForm(obj=user)
    
    # 🔴 PHASE 2 FIX: Pré-remplir le champ zone à partir de zone_id (car obj=user utilise le champ legacy zone string)
    if request.method == 'GET' and user.zone_id:
        form.zone.data = user.zone_id

    if form.validate_on_submit():
        try:
            user.username = form.username.data
            user.email = form.email.data
            user.role = form.role.data
            user.nom = form.nom.data
            user.prenom = form.prenom.data
            user.telephone = form.telephone.data
            user.zone_id = int(form.zone.data) if form.zone.data and int(form.zone.data) != 0 else None
            
            # 🔴 PHASE 2 FIX: Synchroniser le champ legacy zone (string) pour compatibilité
            if user.zone_id:
                zone_obj = db.session.get(Zone, user.zone_id)
                user.zone = zone_obj.nom if zone_obj else None
            else:
                user.zone = None

            user.commune = form.commune.data if form.commune.data else None
            user.quartier = form.quartier.data if form.quartier.data else None
            user.service = form.service.data if form.service.data else None
            user.technologies = form.technologies.data if form.technologies.data else None
            user.actif = True if form.actif.data else False
            if form.new_password.data:
                user.password_hash = generate_password_hash(form.new_password.data)
            db.session.commit()
            flash('Utilisateur mis à jour avec succès!', 'success')
            return redirect(url_for('manage_users'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception('Erreur lors de la mise à jour d\'utilisateur')
            
            # Provide user-friendly error messages
            error_msg = str(e).lower()
            if 'unique constraint' in error_msg or 'duplicate' in error_msg:
                user_msg = 'Ce nom d\'utilisateur ou cette adresse email est déjà utilisé.'
            elif 'field' in error_msg or 'column' in error_msg:
                user_msg = 'Erreur de configuration de la base de données. Contactez l\'administrateur.'
            else:
                user_msg = 'Une erreur est survenue lors de la mise à jour. Réessayez ou contactez l\'administrateur.'
            
            flash(user_msg, 'error')

    return render_template('edit_user.html', user=user, form=form)


@app.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'chef_pur':
        return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403

    if user_id == current_user.id:
        return jsonify({'success': False, 'error': 'Vous ne pouvez pas supprimer votre propre compte'}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'success': False, 'error': 'Utilisateur non trouvé'}), 404

    # Vérifier les dépendances empêchant la suppression
    from models import Intervention, DemandeIntervention, FichierImport, Equipe, MembreEquipe

    deps = {}
    deps['interventions_as_technician'] = Intervention.query.filter_by(technicien_id=user.id).count()
    deps['interventions_as_validator'] = Intervention.query.filter_by(valide_par=user.id).count()
    deps['demandes_as_technician'] = DemandeIntervention.query.filter_by(technicien_id=user.id).count()
    deps['imports'] = FichierImport.query.filter_by(importe_par=user.id).count()
    deps['equipes_as_chef'] = Equipe.query.filter_by(chef_zone_id=user.id).count()
    deps['membre_equipe'] = MembreEquipe.query.filter_by(technicien_id=user.id).count()

    blocking = {k: v for k, v in deps.items() if v > 0}
    if blocking:
        # Construire un message lisible
        parts = []
        if blocking.get('interventions_as_technician'):
            parts.append(f"{blocking['interventions_as_technician']} intervention(s) assignée(s)")
        if blocking.get('interventions_as_validator'):
            parts.append(f"{blocking['interventions_as_validator']} validation(s) enregistrée(s)")
        if blocking.get('demandes_as_technician'):
            parts.append(f"{blocking['demandes_as_technician']} demande(s) liées")
        if blocking.get('imports'):
            parts.append(f"{blocking['imports']} import(s) faits par cet utilisateur")
        if blocking.get('equipes_as_chef'):
            parts.append(f"{blocking['equipes_as_chef']} équipe(s) dont il est chef")
        if blocking.get('membre_equipe'):
            parts.append(f"{blocking['membre_equipe']} participation(s) à des équipes")

        msg = 'Impossible de supprimer l\'utilisateur car il existe des dépendances: ' + '; '.join(parts)
        return jsonify({'success': False, 'error': msg}), 400

    try:
        # Delete related activity logs first (to avoid foreign key constraint violation)
        ActivityLog.query.filter_by(user_id=user.id).delete()
        
        db.session.delete(user)
        db.session.commit()
        log_activity(user_id=current_user.id, action='delete', module='users', entity_id=user.id, entity_name=f"{user.prenom} {user.nom}")
        return jsonify({'success': True, 'message': 'Utilisateur supprimé avec succès'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception('Erreur lors de la suppression d\'un utilisateur')
        
        # Provide user-friendly error messages
        error_msg = str(e).lower()
        if 'foreign key constraint' in error_msg:
            user_friendly_msg = 'Impossible de supprimer cet utilisateur. Des données y sont liées (interventions, demandes, équipes, etc.). Supprimez-les d\'abord.'
        elif 'field' in error_msg and 'inconnu' in error_msg:
            user_friendly_msg = 'Erreur technique : schéma de base de données incomplet. Contactez l\'administrateur.'
        elif 'operational error' in error_msg or 'integrity error' in error_msg:
            user_friendly_msg = 'Erreur lors de l\'accès à la base de données. Vérifiez que toutes les données associées peuvent être chargées.'
        else:
            user_friendly_msg = 'Une erreur est survenue lors de la suppression. Contactez l\'administrateur si le problème persiste.'
        
        return jsonify({'success': False, 'error': user_friendly_msg}), 500


# Team APIs moved to routes/teams.py (blueprint 'teams')
# See routes/teams.py for implementation and registration via register_blueprints(app)


@app.route('/toggle-user-status/<int:user_id>', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    if current_user.role != 'chef_pur':
        return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403

    if user_id == current_user.id:
        return jsonify({
            'success':
            False,
            'error':
            'Vous ne pouvez pas désactiver votre propre compte'
        }), 400

    try:
        user = db.session.get(User, user_id)
        if not user:
            abort(404)
        data = request.get_json() or {}
        actif = data.get('actif')

        if actif is None:
            return jsonify({'success': False, 'error': 'Statut manquant'}), 400

        user.actif = bool(actif)
        db.session.commit()

        status_text = "activé" if user.actif else "désactivé"
        log_activity(
            user_id=current_user.id,
            action='toggle_status',
            module='users',
            entity_id=user.id,
            entity_name=f"{user.prenom} {user.nom}",
            details={
                'status': status_text,
                'username': user.username,
                'role': user.role
            }
        )
        return jsonify({
            'success': True,
            'message': f'Utilisateur {status_text} avec succès'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/intervention/confirm-reception', methods=['POST'])
@login_required
def confirm_reception():
    data = request.get_json()
    intervention_id = data.get('intervention_id')
    intervention = db.session.get(Intervention, intervention_id)
    if intervention:
        intervention.accuse_reception = True
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Intervention introuvable'})


@app.route('/intervention/<int:intervention_id>/reserver-pieces', methods=['GET'])
@login_required
def reserver_pieces(intervention_id):
    # Vérifier que l'intervention existe et appartient à l'utilisateur
    intervention = db.session.get(Intervention, intervention_id)
    if not intervention:
        abort(404)
    if intervention.technicien_id != current_user.id:
        flash('Accès non autorisé à cette intervention.', 'error')
        return redirect(url_for('dashboard'))
    
    # Vérifier que l'accusé de réception a été effectué
    if not intervention.accuse_reception:
        flash('Veuillez d\'abord confirmer la réception de l\'intervention.', 'warning')
        return redirect(url_for('intervention_form', demande_id=intervention.demande_id))
    
    # Récupérer les pièces disponibles en stock
    # Utilisation d'une sous-requête pour calculer la quantité disponible
    from sqlalchemy import func, case, select, and_
    from models import MouvementStock
    
    # Sous-requête pour calculer la quantité disponible par produit
    quantite_sq = select(
        MouvementStock.produit_id,
        func.sum(
            case(
                (MouvementStock.type_mouvement == 'entree', MouvementStock.quantite),
                else_=-MouvementStock.quantite
            )
        ).label('quantite_totale')
    ).group_by(MouvementStock.produit_id).subquery()
    
    # Requête principale pour récupérer les produits avec une quantité > 0
    pieces_disponibles = db.session.query(Produit).join(
        quantite_sq,
        and_(
            Produit.id == quantite_sq.c.produit_id,
            quantite_sq.c.quantite_totale > 0
        )
    ).all()
    
    # Récupérer les réservations existantes pour cette intervention
    reservations = ReservationPiece.query.filter_by(intervention_id=intervention_id).all()
    
    return render_template('reserver_pieces.html',
                         intervention=intervention,
                         pieces=pieces_disponibles,
                         reservations=reservations)


@app.route('/intervention/<int:intervention_id>/save-reservation', methods=['POST'])
@login_required
def save_reservation(intervention_id):
    # Vérifier que l'intervention existe et appartient à l'utilisateur
    intervention = db.session.get(Intervention, intervention_id)
    if not intervention:
        abort(404)
    if intervention.technicien_id != current_user.id:
        flash('Accès non autorisé à cette intervention.', 'error')
        return redirect(url_for('dashboard'))
    
    # Vérifier que l'accusé de réception a été effectué
    if not intervention.accuse_reception:
        flash('Veuillez d\'abord confirmer la réception de l\'intervention.', 'warning')
        return redirect(url_for('intervention_form', demande_id=intervention.demande_id))
    
    try:
        # Récupérer les données du formulaire
        commentaire = request.form.get('commentaire', '')
        
        # Parcourir les champs du formulaire pour trouver les pièces sélectionnées
        for key, value in request.form.items():
            if key.startswith('piece_') and value.isdigit():
                piece_id = int(key.replace('piece_', ''))
                quantite = float(value)
                
                # Vérifier que la pièce existe et qu'il y a suffisamment de stock
                piece = db.session.get(Produit, piece_id)
                if not piece:
                    flash(f'Pièce avec l\'ID {piece_id} introuvable.', 'error')
                    continue
                    
                if piece.quantite < quantite:
                    flash(f'Stock insuffisant pour la pièce {piece.nom}. Quantité disponible: {piece.quantite}', 'error')
                    continue
                
                # Vérifier si une réservation existe déjà pour cette pièce et cette intervention
                reservation = ReservationPiece.query.filter_by(
                    intervention_id=intervention_id,
                    produit_id=piece_id
                ).first()
                
                if reservation:
                    # Mettre à jour la réservation existante
                    reservation.quantite = quantite
                    reservation.commentaire = commentaire
                    reservation.date_maj = datetime.now(timezone.utc)
                else:
                    # Créer une nouvelle réservation
                    reservation = ReservationPiece(
                        intervention_id=intervention_id,
                        produit_id=piece_id,
                        quantite=quantite,
                        commentaire=commentaire,
                        statut=ReservationPiece.STATUT_EN_ATTENTE,
                        utilisateur_id=current_user.id
                    )
                    db.session.add(reservation)
                
                # Mettre à jour le stock (à confirmer plus tard par un responsable)
                # piece.quantite -= quantite
                
        # Enregistrer les modifications
        db.session.commit()
        
        flash('Réservation enregistrée avec succès. En attente de validation.', 'success')
        return redirect(url_for('legacy.reserver_pieces', intervention_id=intervention_id))
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Erreur lors de l\'enregistrement de la réservation: {str(e)}')
        flash('Une erreur est survenue lors de l\'enregistrement de la réservation.', 'error')
        return redirect(url_for('legacy.reserver_pieces', intervention_id=intervention_id))


def generate_reset_token(user, expires_sec=3600):
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return s.dumps(user.email, salt='password-reset-salt')


def verify_reset_token(token, expires_sec=3600):
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=expires_sec)
    except Exception:
        return None
    return User.query.filter_by(email=email).first()


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = generate_reset_token(user)
            reset_url = url_for('reset_password', token=token, _external=True)
            # Envoie l'email
            try:
                send_email(
                    "Réinitialisation de mot de passe", [user.email],
                    body=f"Pour réinitialiser votre mot de passe, cliquez ici : {reset_url}"
                )
            except Exception as e:
                current_app.logger.error(f"Failed to send reset password email to {user.email}: {str(e)}")
                # On ne lève pas d'exception pour garder la sécurité par obscurité : 
                # l'utilisateur voit le même message qu'il ait reçu l'email ou non.
        flash('Si cet email existe, un lien de réinitialisation a été envoyé.',
              'info')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', form=form)


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = verify_reset_token(token)
    if not user:
        flash('Lien invalide ou expiré.', 'danger')
        return redirect(url_for('reset_password_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password_hash = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Mot de passe réinitialisé avec succès.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

@app.route('/api/fiche-technique/<int:intervention_id>')
@login_required
def api_fiche_technique_details(intervention_id):
    # Vérifier les permissions (même logique que pour l'intervention)
    intervention = db.session.get(Intervention, intervention_id)
    if not intervention:
        abort(404)
    
    if current_user.role == 'technicien' and intervention.technicien_id != current_user.id:
        return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403
    elif current_user.role == 'chef_pilote':
        if intervention.demande and intervention.demande.service != current_user.service:
            return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403
    elif current_user.role == 'chef_zone':
        technicien = db.session.get(User, intervention.technicien_id)
        if not technicien or technicien.zone != current_user.zone:
            return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403

    fiche_technique = FicheTechnique.query.filter_by(intervention_id=intervention_id).first()
    
    if not fiche_technique:
        return jsonify({'success': False, 'error': 'Fiche technique non trouvée'}), 404

    fiche_data = {
        # Informations générales
        'nom_raison_sociale': fiche_technique.nom_raison_sociale,
        'contact': fiche_technique.contact,
        'represente_par': fiche_technique.represente_par,
        'date_installation': fiche_technique.date_installation.strftime('%Y-%m-%d') if fiche_technique.date_installation else None,
        'tel1': fiche_technique.tel1,
        'tel2': fiche_technique.tel2,
        'adresse_demandee': fiche_technique.adresse_demandee,
        'etage': fiche_technique.etage,
        'gps_lat': fiche_technique.gps_lat,
        'gps_long': fiche_technique.gps_long,
        'type_logement_avec_bpi': fiche_technique.type_logement_avec_bpi,
        'type_logement_sans_bpi': fiche_technique.type_logement_sans_bpi,
        'h_arrivee': fiche_technique.h_arrivee.strftime('%H:%M') if fiche_technique.h_arrivee else None,
        'h_depart': fiche_technique.h_depart.strftime('%H:%M') if fiche_technique.h_depart else None,
        
        # Informations techniques
        'n_ligne': fiche_technique.n_ligne,
        'n_demande': fiche_technique.n_demande,
        'technicien_structure': fiche_technique.technicien_structure,
        'pilote_structure': fiche_technique.pilote_structure,
        'offre': fiche_technique.offre,
        'debit': fiche_technique.debit,
        'type_mc': fiche_technique.type_mc,
        'type_na': fiche_technique.type_na,
        'type_transfert': fiche_technique.type_transfert,
        'type_autre': fiche_technique.type_autre,
        'backoffice_structure': fiche_technique.backoffice_structure,
        
        # Matériels
        'type_ont': fiche_technique.type_ont,
        'nature_ont': fiche_technique.nature_ont,
        'numero_serie_ont': fiche_technique.numero_serie_ont,
        'type_decodeur': fiche_technique.type_decodeur,
        'nature_decodeur': fiche_technique.nature_decodeur,
        'numero_serie_decodeur': fiche_technique.numero_serie_decodeur,
        'disque_dur': fiche_technique.disque_dur,
        'telephone': fiche_technique.telephone,
        'recepteur_wifi': fiche_technique.recepteur_wifi,
        'cpl': fiche_technique.cpl,
        'carte_vaccess': fiche_technique.carte_vaccess,
        
        # Accessoires
        'type_cable_lc': fiche_technique.type_cable_lc,
        'type_cable_bti': fiche_technique.type_cable_bti,
        'type_cable_pto_one': fiche_technique.type_cable_pto_one,
        'kit_pto': fiche_technique.kit_pto,
        'piton': fiche_technique.piton,
        'arobase': fiche_technique.arobase,
        'malico': fiche_technique.malico,
        'ds6': fiche_technique.ds6,
        'autre_accessoire': fiche_technique.autre_accessoire,
        
        # Tests de services
        'appel_sortant_ok': fiche_technique.appel_sortant_ok,
        'appel_sortant_nok': fiche_technique.appel_sortant_nok,
        'appel_entrant_ok': fiche_technique.appel_entrant_ok,
        'appel_entrant_nok': fiche_technique.appel_entrant_nok,
        'tvo_mono_ok': fiche_technique.tvo_mono_ok,
        'tvo_mono_nok': fiche_technique.tvo_mono_nok,
        'tvo_multi_ok': fiche_technique.tvo_multi_ok,
        'tvo_multi_nok': fiche_technique.tvo_multi_nok,
        'enregistreur_dd_ok': fiche_technique.enregistreur_dd_ok,
        'enregistreur_dd_nok': fiche_technique.enregistreur_dd_nok,
        
        # Tests de débits
        'par_cable_salon': fiche_technique.par_cable_salon,
        'par_cable_chambres': fiche_technique.par_cable_chambres,
        'par_cable_bureau': fiche_technique.par_cable_bureau,
        'par_cable_autres': fiche_technique.par_cable_autres,
        'par_cable_vitesse_wifi': fiche_technique.par_cable_vitesse_wifi,
        'par_cable_mesure_mbps': fiche_technique.par_cable_mesure_mbps,
        'par_wifi_salon': fiche_technique.par_wifi_salon,
        'par_wifi_chambres': fiche_technique.par_wifi_chambres,
        'par_wifi_bureau': fiche_technique.par_wifi_bureau,
        'par_wifi_autres': fiche_technique.par_wifi_autres,
        'par_wifi_vitesse_wifi': fiche_technique.par_wifi_vitesse_wifi,
        'par_wifi_mesure_mbps': fiche_technique.par_wifi_mesure_mbps,
        
        # Etiquetages et Nettoyage
        'etiquetage_colliers_serres': fiche_technique.etiquetage_colliers_serres,
        'etiquetage_pbo_normalise': fiche_technique.etiquetage_pbo_normalise,
        'nettoyage_depose': fiche_technique.nettoyage_depose,
        'nettoyage_tutorat': fiche_technique.nettoyage_tutorat,
        
        # Rattachement
        'rattachement_nro': fiche_technique.rattachement_nro,
        'rattachement_type': fiche_technique.rattachement_type,
        'rattachement_num_carte': fiche_technique.rattachement_num_carte,
        'rattachement_num_port': fiche_technique.rattachement_num_port,
        'rattachement_plaque': fiche_technique.rattachement_plaque,
        'rattachement_bpi_pbo': fiche_technique.rattachement_bpi_pbo,
        'rattachement_coupleur': fiche_technique.rattachement_coupleur,
        'rattachement_fibre': fiche_technique.rattachement_fibre,
        'rattachement_ref_dbm': fiche_technique.rattachement_ref_dbm,
        'rattachement_mesure_dbm': fiche_technique.rattachement_mesure_dbm,
        
        # Commentaires
        'commentaires': fiche_technique.commentaires,
        'photos_list': json.loads(fiche_technique.photos) if fiche_technique.photos and fiche_technique.photos.strip() else [],
        # Signatures et satisfaction client
        'signature_equipe': fiche_technique.signature_equipe,
        'signature_client': fiche_technique.signature_client,
        'client_tres_satisfait': fiche_technique.client_tres_satisfait,
        'client_satisfait': fiche_technique.client_satisfait,
        'client_pas_satisfait': fiche_technique.client_pas_satisfait,
        
        # Métadonnées
        'date_creation': fiche_technique.date_creation.strftime('%Y-%m-%d %H:%M:%S') if fiche_technique.date_creation else None,
        'updated_at': fiche_technique.updated_at.strftime('%Y-%m-%d %H:%M:%S') if fiche_technique.updated_at else None,
        
        # Relations
        'technicien_id': fiche_technique.technicien_id,
        'intervention_id': fiche_technique.intervention_id
    }

    return jsonify({
        'success': True,
        'fiche_technique': fiche_data,
        'intervention': {
            'id': intervention.id,
            'valide_par': intervention.valide_par,
            'fichier_technique_accessible': intervention.fichier_technique_accessible,
            'demande': {
                'nd': intervention.demande.nd if intervention.demande else 'N/A',
                'nom_client': intervention.demande.nom_client if intervention.demande else 'N/A',
                'prenom_client': intervention.demande.prenom_client if intervention.demande else 'N/A',
                'service': intervention.demande.service if intervention.demande else 'N/A',
                'type_techno': intervention.demande.type_techno if intervention.demande else 'N/A',
                'libelle_commune': intervention.demande.libelle_commune if intervention.demande else 'N/A'
            } if intervention.demande else None,
            'valideur': {
                'id': intervention.valideur.id if intervention.valideur else None,
                'nom': intervention.valideur.nom if intervention.valideur else None,
                'prenom': intervention.valideur.prenom if intervention.valideur else None
            } if intervention.valideur else None,
            'technicien': {
                'nom': intervention.technicien.nom if intervention.technicien else 'N/A',
                'prenom': intervention.technicien.prenom if intervention.technicien else 'N/A'
            } if intervention.technicien else None
        }
    })

@app.route('/import-demandes/delete/<int:import_id>', methods=['POST'])
@login_required
def delete_import(import_id):
    """
    ✅ SOFT DELETE + Vérification FK (Solutions 1 + 3)
    - Vérifie présence interventions liées
    - Marque import comme inactif (pas de DELETE physique)
    - Gère proprement les erreurs FK
    """
    if current_user.role not in ['chef_pur', 'chef_pilote', 'chef_zone']:
        flash('❌ Accès non autorisé.', 'error')
        return redirect(url_for('dashboard'))
    
    fichier_import = db.session.get(FichierImport, import_id)
    if not fichier_import:
        abort(404)
    
    # Vérification modifiée : chef_pur peut tout supprimer, les autres seulement leurs propres imports
    if current_user.role != 'chef_pur' and fichier_import.importe_par != current_user.id:
        flash('❌ Vous ne pouvez pas supprimer cet import.', 'error')
        return redirect(url_for('import_demandes'))
    
    try:
        # ✅ SOLUTION 1: Vérifier avant suppression
        demandes = DemandeIntervention.query.filter_by(fichier_importe_id=import_id).all()
        demande_ids = [demande.id for demande in demandes]
        
        # 🔴 CRITIQUE: Vérifier les interventions liées
        interventions_count = 0
        if demande_ids:
            interventions_count = Intervention.query.filter(
                Intervention.demande_id.in_(demande_ids)
            ).count()
        
        # Si interventions existent → refuser suppression
        if interventions_count > 0:
            flash(
                f'❌ Impossible de supprimer: {interventions_count} intervention(s) '
                f'liée(s) à cet import. Supprimez d\'abord les interventions associées.',
                'error'
            )
            current_app.logger.warning(
                f"Tentative suppression import {import_id} avec {interventions_count} interventions liées"
            )
            return redirect(url_for('import_demandes'))
        
        # ✅ SOLUTION 3: Soft Delete (marquer comme inactif)
        fichier_import.actif = False
        fichier_import.date_suppression = datetime.utcnow()
        
        # Supprimer d'abord toutes les notifications SMS liées à ces demandes
        if demande_ids:
            NotificationSMS.query.filter(NotificationSMS.demande_id.in_(demande_ids)).delete(
                synchronize_session=False
            )
        
        # Supprimer les demandes liées (mais pas l'import lui-même)
        for demande in demandes:
            db.session.delete(demande)
        
        db.session.commit()
        
        # 📝 Logger l'action
        log_activity(
            current_user.id, 
            'soft_delete_import', 
            'demandes', 
            import_id, 
            f'Import marqué comme supprimé: {fichier_import.nom_fichier}', 
            {
                'filename': fichier_import.nom_fichier,
                'import_date': fichier_import.date_import.isoformat() if fichier_import.date_import else None,
                'deleted_by': current_user.username,
                'records_deleted': len(demandes),
                'imported_by': db.session.get(User, fichier_import.importe_par).username if fichier_import.importe_par else None,
                'soft_delete': True,
                'date_suppression': datetime.utcnow().isoformat()
            }
        )

        # 💬 Message adapté
        if current_user.role == 'chef_pur' and fichier_import.importe_par != current_user.id:
            importeur = db.session.get(User, fichier_import.importe_par)
            nom_importeur = importeur.nom if importeur else "Utilisateur inconnu"
            flash(
                f"✅ Import '{fichier_import.nom_fichier}' (de {nom_importeur}) "
                f"et {len(demandes)} demandes associées supprimés avec succès.",
                'success'
            )
        else:
            flash(
                f"✅ Import '{fichier_import.nom_fichier}' "
                f"et {len(demandes)} demandes associées supprimés avec succès.",
                'success'
            )
        
        current_app.logger.info(
            f"✅ Import {import_id} soft-deleted (actif=False) avec {len(demandes)} demandes"
        )
    
    except IntegrityError as e:
        """Gère les erreurs de contrainte FK"""
        db.session.rollback()
        current_app.logger.error(
            f"❌ Erreur FK lors suppression import {import_id}: {str(e)}"
        )
        flash(
            '❌ Erreur: Impossible de supprimer cet import (données liées). '
            'Contactez l\'administrateur si le problème persiste.',
            'error'
        )
    
    except Exception as e:
        """Gère les autres erreurs"""
        db.session.rollback()
        current_app.logger.error(
            f"❌ Erreur suppression import {import_id}: {str(e)}\n{traceback.format_exc()}"
        )
        flash(
            f'❌ Erreur système: Impossible de supprimer l\'import. '
            f'Details: {str(e)}',
            'error'
        )
    
    return redirect(url_for('import_demandes'))


@app.route('/api/demandes/preview')
@login_required
def demandes_preview():
    ids_param = request.args.get('ids')
    if not ids_param:
        return {'items': []}
    ids_list = [int(i) for i in ids_param.split(',') if i.isdigit()]
    demandes = DemandeIntervention.query.filter(DemandeIntervention.id.in_(ids_list)).all()
    items = [{
        'id': d.id,
        'numero_demande': d.nd,
        'age': d.age,
        'priorite': d.priorite_traitement,
        'offre': d.offre,
        'nom_client': d.nom_client,
        'prenom_client': d.prenom_client,
        'type_techno': d.type_techno,
        'commune': d.libelle_commune,
        'service_demande': d.service,
        'zone': d.zone,
        'date_creation': d.date_creation.isoformat() if d.date_creation else None,
        'statut': d.statut
    } for d in demandes]
    return {'items': items}    

@app.route('/api/survey/<int:intervention_id>')
@login_required
def api_survey_details(intervention_id):
    # Vérifier les permissions (même logique que pour l'intervention)
    intervention = db.session.get(Intervention, intervention_id)
    if not intervention:
        abort(404)
    
    if current_user.role == 'technicien' and intervention.technicien_id != current_user.id:
        return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403
    elif current_user.role == 'chef_pilote':
        if intervention.demande and intervention.demande.service != current_user.service:
            return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403
    elif current_user.role == 'chef_zone':
        technicien = db.session.get(User, intervention.technicien_id)
        if not technicien or technicien.zone != current_user.zone:
            return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403

    survey = Survey.query.filter_by(intervention_id=intervention_id).first()
    
    if not survey:
        return jsonify({'success': False, 'error': 'Fiche survey non trouvée'}), 404

    survey_data = {
        # Informations générales
        'date_survey': survey.date_survey.strftime('%Y-%m-%d') if survey.date_survey else None,
        'nom_raison_sociale': survey.nom_raison_sociale,
        'contact': survey.contact,
        'tel1': survey.tel1,
        'tel2': survey.tel2,
        'represente_par': survey.represente_par,
        'adresse_demande': survey.adresse_demande,
        'etage': survey.etage,
        'h_debut': survey.h_debut if survey.h_debut else None,
        'h_fin': survey.h_fin if survey.h_fin else None,
        'gps_lat': survey.gps_lat,
        'gps_long': survey.gps_long,
        
        # Informations techniques
        'n_ligne': survey.n_ligne,
        'n_demande': survey.n_demande,
        'service_demande': survey.service_demande,
        'technicien_structure': survey.technicien_structure,
        'backoffice_structure': survey.backoffice_structure,
        'offre': survey.offre,
        'debit': survey.debit,
        'type_mi': survey.type_mi,
        'type_na': survey.type_na,
        'type_transfer': survey.type_transfer,
        'type_autre': survey.type_autre,
        
        # État du client et localisation
        'etat_client': survey.etat_client,
        'nature_local': survey.nature_local,
        'type_logement': survey.type_logement,
        
        # Réseaux Fibre
        'fibre_dispo': survey.fibre_dispo,
        'gpon_olt': survey.gpon_olt,
        'splitter': survey.splitter,
        'distance_fibre': survey.distance_fibre,
        'etat_fibre': survey.etat_fibre,
        
        # Réseaux Cuivre
        'cuivre_dispo': survey.cuivre_dispo,
        'sr': survey.sr,
        'pc': survey.pc,
        'distance_cuivre': survey.distance_cuivre,
        'etat_cuivre': survey.etat_cuivre,
        
        # Données réseaux détaillées
        'nro': survey.nro,
        'type_reseau': survey.type_reseau,
        'plaque': survey.plaque,
        'bpi': survey.bpi,
        'pbo': survey.pbo,
        'coupleur': survey.coupleur,
        'fibre': survey.fibre,
        
        # Mesures WiFi
        'niveau_wifi_salon': survey.niveau_wifi_salon,
        'niveau_wifi_chambre1': survey.niveau_wifi_chambre1,
        'niveau_wifi_bureau1': survey.niveau_wifi_bureau1,
        'niveau_wifi_autres_pieces': survey.niveau_wifi_autres_pieces,
        
        # Accessoires recommandés - Répéteur WiFi
        'repeteur_wifi_oui': survey.repeteur_wifi_oui,
        'repeteur_wifi_non': survey.repeteur_wifi_non,
        'repeteur_wifi_quantite': survey.repeteur_wifi_quantite,
        'repeteur_wifi_emplacement': survey.repeteur_wifi_emplacement,
        
        # Accessoires recommandés - CPL
        'cpl_oui': survey.cpl_oui,
        'cpl_non': survey.cpl_non,
        'cpl_quantite': survey.cpl_quantite,
        'cpl_emplacement': survey.cpl_emplacement,
        
        # Accessoires recommandés - Câble local
        'cable_local_type': survey.cable_local_type,
        'cable_local_longueur': survey.cable_local_longueur,
        'cable_local_connecteurs': survey.cable_local_connecteurs,
        
        # Accessoires recommandés - Goulottes
        'goulottes_oui': survey.goulottes_oui,
        'goulottes_non': survey.goulottes_non,
        'goulottes_quantite': survey.goulottes_quantite,
        'goulottes_nombre_x2m': survey.goulottes_nombre_x2m,
        
        # Conclusion
        'conclusion': survey.conclusion,
        'observation_tech': survey.observation_tech,
        'observation_client': survey.observation_client,
        'survey_ok': survey.survey_ok,
        'survey_nok': survey.survey_nok,
        'motif': survey.motif,
        
        # Satisfaction client
        'client_tres_satisfait': survey.client_tres_satisfait,
        'client_satisfait': survey.client_satisfait,
        'client_pas_satisfait': survey.client_pas_satisfait,
        'commentaires': survey.commentaires,
        
        # Photos et signatures
        'photos_list': json.loads(survey.photos) if survey.photos and survey.photos.strip() else [],
        'signature_equipe': survey.signature_equipe,
        'signature_client': survey.signature_client,
        
        # Métadonnées
        'created_at': survey.created_at.strftime('%Y-%m-%d %H:%M:%S') if survey.created_at else None,
        'updated_at': survey.updated_at.strftime('%Y-%m-%d %H:%M:%S') if survey.updated_at else None,
        
        # Relations
        'intervention_id': survey.intervention_id
    }

    return jsonify({
        'success': True,
        'survey': survey_data,
        'intervention': {
            'id': intervention.id,
            'valide_par': intervention.valide_par,
            'fichier_technique_accessible': intervention.fichier_technique_accessible,
            'demande': {
                'nd': intervention.demande.nd if intervention.demande else 'N/A',
                'nom_client': intervention.demande.nom_client if intervention.demande else 'N/A',
                'prenom_client': intervention.demande.prenom_client if intervention.demande else 'N/A',
                'service': intervention.demande.service if intervention.demande else 'N/A',
                'type_techno': intervention.demande.type_techno if intervention.demande else 'N/A',
                'libelle_commune': intervention.demande.libelle_commune if intervention.demande else 'N/A',
                'libelle_quartier': intervention.demande.libelle_quartier if intervention.demande else 'N/A',
                'tel_client': intervention.demande.contact_client if intervention.demande else 'N/A'
            } if intervention.demande else None,
            'valideur': {
                'id': intervention.valideur.id if intervention.valideur else None,
                'nom': intervention.valideur.nom if intervention.valideur else None,
                'prenom': intervention.valideur.prenom if intervention.valideur else None
            } if intervention.valideur else None,
            'technicien': {
                'id': intervention.technicien.id if intervention.technicien else None,
                'nom': intervention.technicien.nom if intervention.technicien else 'N/A',
                'prenom': intervention.technicien.prenom if intervention.technicien else 'N/A',
                'zone': intervention.technicien.zone if intervention.technicien else 'N/A'
            } if intervention.technicien else None
        }
    })

@app.route('/api/notifications')
@login_required
def get_notifications():
    """API pour récupérer les notifications de l'utilisateur connecté"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Récupérer les notifications non lues en premier, puis les lues
    notifications = NotificationSMS.query.filter_by(
        technicien_id=current_user.id
    ).order_by(
        NotificationSMS.envoye.asc(),  # Non lues d'abord (envoye=False)
        NotificationSMS.date_creation.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    notifications_data = []
    for notif in notifications.items:
        notifications_data.append({
            'id': notif.id,
            'message': notif.message,
            'type_notification': notif.type_notification,
            'envoye': notif.envoye,
            'date_creation': notif.date_creation.strftime('%d/%m/%Y %H:%M'),
            'demande_id': notif.demande_id,
            'demande_nd': notif.demande.nd if notif.demande else None
        })

    return jsonify({
        'success': True,
        'notifications': notifications_data,
        'total': notifications.total,
        'pages': notifications.pages,
        'current_page': notifications.page
    })


@app.route('/api/notifications/<int:notification_id>/mark-read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Marquer une notification comme lue"""
    notification = db.session.get(NotificationSMS, notification_id)
    if not notification:
        abort(404)

    # Vérifier que la notification appartient à l'utilisateur
    if notification.technicien_id != current_user.id:
        return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403

    notification.envoye = True
    db.session.commit()

    return jsonify({'success': True})


@app.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Marquer toutes les notifications comme lues"""
    NotificationSMS.query.filter_by(
        technicien_id=current_user.id,
        envoye=False
    ).update({'envoye': True})

    db.session.commit()

    return jsonify({'success': True})


@app.route('/connection-history')
@login_required
def connection_history():
    if current_user.role != 'chef_pur':
        flash('Accès non autorisé', 'error')
        return redirect(url_for('dashboard'))
        
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    logs = ActivityLog.query.join(User).order_by(
        ActivityLog.timestamp.desc()
    ).paginate(page=page, per_page=per_page)
    
    return render_template('connection_history.html', logs=logs) 

def check_interventions_delayed():
    """Vérifie les interventions en retard toutes les heures"""
    demandes = DemandeIntervention.query.filter(
        DemandeIntervention.statut == 'affecte',
        DemandeIntervention.date_affectation <= datetime.now(timezone.utc) - timedelta(hours=2)
    ).all()
    
    for demande in demandes:
        # Vérifier si un rappel n'a pas déjà été envoyé récemment
        recent_notification = NotificationSMS.query.filter(
            NotificationSMS.technicien_id == demande.technicien_id,
            NotificationSMS.demande_id == demande.id,
            NotificationSMS.type_notification == 'rappel',
            NotificationSMS.date_creation >= datetime.now(timezone.utc) - timedelta(hours=1)
        ).first()
        
        if not recent_notification:
            create_sms_notification(demande.technicien_id, demande.id, 'rappel')

def check_interventions_deadline():
    """Vérifie les échéances des interventions"""
    demandes = DemandeIntervention.query.filter(
        DemandeIntervention.date_echeance == date.today(),
        DemandeIntervention.statut.in_(['affecte', 'en_cours'])
    ).all()
    
    for demande in demandes:
        # Vérifier si une notification d'échéance n'a pas déjà été envoyée aujourd'hui
        today_notification = NotificationSMS.query.filter(
            NotificationSMS.technicien_id == demande.technicien_id,
            NotificationSMS.demande_id == demande.id,
            NotificationSMS.type_notification == 'echeance',
            NotificationSMS.date_creation >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        ).first()
        
        if not today_notification:
            create_sms_notification(demande.technicien_id, demande.id, 'echeance')  

@app.route('/cloturer-demande', methods=['POST'])
@login_required
def cloturer_demande():
    if current_user.role not in ['chef_pur', 'chef_pilote']:
        return jsonify({'success': False, 'error': 'Accès non autorisé'})
    
    try:
        data = request.get_json()
        demande_id = data.get('demande_id')
        commentaire = data.get('commentaire', '').strip()
        
        if not demande_id or not commentaire:
            return jsonify({'success': False, 'error': 'Données manquantes'})
        
        demande = db.session.get(DemandeIntervention, demande_id)
        if not demande or demande.statut not in ['nouveau', 'a_reaffecter']:
            return jsonify({'success': False, 'error': 'Demande non valide'})
        
        # Vérification des permissions selon le service
        if current_user.role == 'chef_pilote' and current_user.service != 'SAV,Production':
            if demande.service != current_user.service:
                return jsonify({'success': False, 'error': 'Service non autorisé'})
        
        demande.statut = 'cloture'
        demande.commentaire_interv = commentaire
        demande.date_completion = datetime.now(timezone.utc)
        
        db.session.commit()
        
        log_activity(
            user_id=current_user.id,
            action='cloture',
            module='demandes',
            entity_id=demande.id,
            entity_name=f"Demande {demande.nd}",
            details={'commentaire': commentaire}
        )
        
        return jsonify({'success': True, 'message': 'Demande clôturée avec succès'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/reporter-demande', methods=['POST'])
@login_required
def reporter_demande():
    if current_user.role not in ['chef_pur', 'chef_pilote']:
        return jsonify({'success': False, 'error': 'Accès non autorisé'})
    
    try:
        data = request.get_json()
        demande_id = data.get('demande_id')
        commentaire = data.get('commentaire', '').strip()
        date_report = data.get('date_report')
        
        if not demande_id or not commentaire:
            return jsonify({'success': False, 'error': 'Données manquantes'})
        
        demande = db.session.get(DemandeIntervention, demande_id)
        if not demande or demande.statut not in ['nouveau', 'a_reaffecter']:
            return jsonify({'success': False, 'error': 'Demande non valide'})
        
        # Vérification des permissions selon le service
        if current_user.role == 'chef_pilote' and current_user.service != 'SAV,Production':
            if demande.service != current_user.service:
                return jsonify({'success': False, 'error': 'Service non autorisé'})
        
        demande.statut = 'reporte'
        demande.commentaire_interv = commentaire
        if date_report:
            demande.date_echeance = datetime.strptime(date_report, '%Y-%m-%d').date()
        
        db.session.commit()
        
        log_activity(
            user_id=current_user.id,
            action='report',
            module='demandes',
            entity_id=demande.id,
            entity_name=f"Demande {demande.nd}",
            details={'commentaire': commentaire, 'date_report': date_report}
        )
        
        return jsonify({'success': True, 'message': 'Demande reportée avec succès'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})
