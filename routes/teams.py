"""
Module teams — gestion des équipes, publication/dépublication, gestion des membres.
Routes : /create-team, /manage_team/*, /edit-team/*, /add-membre-equipe/*, /api/publish-selected-teams, /api/unpublish-selected-teams, /api/all-teams
"""

from datetime import datetime, date
from flask import render_template, request, redirect, url_for, flash, jsonify, Blueprint, current_app, abort
from flask_login import login_required, current_user

from app import db
from models import Equipe, MembreEquipe, User
from utils import log_activity
from extensions import csrf


teams_bp = Blueprint('teams', __name__)


@teams_bp.route('/create-team', methods=['GET', 'POST'])
@login_required
def create_team():
    """Créer une nouvelle équipe"""
    print(f"DEBUG: Début de create_team - Utilisateur: {current_user.username}, Rôle: {current_user.role}")
    
    try:
        # Vérifier si l'utilisateur a le droit de créer une équipe
        if current_user.role not in ['admin', 'chef_pur', 'chef_pilote', 'chef_zone']:
            print(f"DEBUG: Utilisateur {current_user.username} avec rôle {current_user.role} n'a pas le droit de créer une équipe")
            flash(' Accès refusé: Seuls les administrateurs, chefs PUR, pilotes et chefs de zone peuvent créer des équipes.', 'error')
            return redirect(url_for('dashboard'))
        
        from forms import TeamForm
        form = TeamForm()
        print(f"DEBUG: Formulaire créé: {form}")
        
        # Pré-remplir le formulaire avec la zone de l'utilisateur (Récupération auto)
        user_zone_id = None
        if hasattr(current_user, 'zone_id') and current_user.zone_id:
            user_zone_id = current_user.zone_id
        elif hasattr(current_user, 'zone_relation') and current_user.zone_relation:
            user_zone_id = current_user.zone_relation.id
        elif hasattr(current_user, 'zone') and current_user.zone:
            from models import Zone
            # Recherche de l'objet Zone par nom exact ou contenu
            zone_obj = Zone.query.filter(
                (Zone.nom.ilike(current_user.zone.strip())) | 
                (Zone.nom.contains(current_user.zone.strip())) |
                (Zone.code.ilike(current_user.zone.strip()))
            ).first()
            if zone_obj:
                user_zone_id = zone_obj.id
        
        if user_zone_id:
            print(f"DEBUG: Zone trouvée pour {current_user.username}: {user_zone_id}")
            form.zone.data = user_zone_id
            
        # SÉCURITÉ & VALIDATION : Forcer la donnée si chef de zone (même en POST)
        if current_user.role == 'chef_zone' and user_zone_id:
            form.zone.data = user_zone_id
        
        if form.validate_on_submit():
            print(f"DEBUG: Formulaire soumis et validé")
            
            try:
                # Récupérer les données du formulaire
                nom_equipe = form.nom_equipe.data
                date_creation = form.date_creation.data
                technologies = form.technologies.data
                service = form.service.data
                prestataire = form.prestataire.data
                zone_id = form.zone.data
                
                # SÉCURITÉ BACKEND : Forcer la zone si chef de zone
                if current_user.role == 'chef_zone' and current_user.zone_id:
                    zone_id = current_user.zone_id
                    print(f"DEBUG: Zone forcée pour chef de zone: {zone_id}")
                
                # Gérer la zone selon le cas
                zone_text = None
                if zone_id and zone_id != 0:
                    # Récupérer la zone depuis l'ID
                    from models import Zone
                    zone_obj = Zone.query.get(zone_id)
                    if zone_obj:
                        zone_text = f"{zone_obj.nom} ({zone_obj.code})"
                        print(f"DEBUG: Zone depuis ID {zone_id}: {zone_text}")
                    else:
                        print(f"DEBUG: Zone ID {zone_id} non trouvée")
                        zone_text = "Non spécifiée"
                elif current_user.zone_relation:
                    zone_text = f"{current_user.zone_relation.nom} ({current_user.zone_relation.code})"
                    print(f"DEBUG: Zone depuis zone_relation: {zone_text}")
                elif current_user.zone:
                    zone_text = current_user.zone
                    print(f"DEBUG: Zone depuis zone (ancienne méthode): {zone_text}")
                else:
                    print("DEBUG: Aucune zone définie")
                    zone_text = "Non spécifiée"
                
                print(f"DEBUG: Zone finale pour équipe: {zone_text}")
                
                # Créer l'équipe
                equipe = Equipe(
                    nom_equipe=nom_equipe,
                    date_creation=date_creation,
                    chef_zone_id=current_user.id,
                    zone=zone_text,
                    technologies=technologies,
                    service=service,
                    prestataire=prestataire,
                    actif=True,
                    publie=False
                )
                
                print(f"DEBUG: Équipe créée - ID: {equipe.id}, Nom: {equipe.nom_equipe}, Zone: {equipe.zone}")
                
                db.session.add(equipe)
                db.session.commit()
                
                print(f"DEBUG: Équipe sauvegardée en base")
                
                # Log l'activité
                log_activity(
                    user_id=current_user.id,
                    action='create',
                    module='teams',
                    entity_id=equipe.id,
                    entity_name=f"Équipe {equipe.nom_equipe}",
                    details={'zone': zone_text, 'service': service, 'technologies': technologies}
                )
                
                print(f"DEBUG: Activité loggée")
                
                flash('Équipe créée avec succès!', 'success')
                return redirect(url_for('teams.manage_team', equipe_id=equipe.id))
                
            except Exception as e:
                print(f"DEBUG: Exception lors de la création: {e}")
                db.session.rollback()
                flash(f'Erreur lors de la création de l\'équipe: {str(e)}', 'error')
                
        else:
            print(f"DEBUG: Formulaire non valide - Erreurs: {form.errors}")
            if request.method == 'POST':
                for field_name, field_errors in form.errors.items():
                    for error in field_errors:
                        print(f"DEBUG: Erreur {field_name}: {error}")
        
        return render_template('create_team.html', form=form)
        
    except Exception as e:
        print(f"DEBUG: Exception générale dans create_team: {e}")
        flash(f'Erreur lors du chargement de la page: {str(e)}', 'error')
        return render_template('create_team.html', form=form)


@teams_bp.route('/manage_team/<int:equipe_id>', methods=['GET', 'POST'])
@login_required
def manage_team(equipe_id):
    """Gérer les membres d'une équipe."""
    equipe = db.session.get(Equipe, equipe_id)
    if not equipe:
        abort(404)
    
    if current_user.role == 'chef_zone':
        # Vérifier si l'équipe appartient à la zone du chef de zone
        # On accepte si c'est le créateur OU si c'est dans sa zone
        user_zone = current_user.zone
        user_zone_formatted = None
        if current_user.zone_relation:
            user_zone_formatted = f"{current_user.zone_relation.nom} ({current_user.zone_relation.code})"
        
        is_in_zone = (equipe.zone == user_zone or 
                     (user_zone_formatted and equipe.zone == user_zone_formatted) or
                     (current_user.zone_relation and equipe.zone == current_user.zone_relation.nom) or
                     (current_user.zone_relation and equipe.zone == current_user.zone_relation.code) or
                     equipe.chef_zone_id == current_user.id)
        
        if not is_in_zone:
            flash('Accès non autorisé : cette équipe n\'appartient pas à votre zone.', 'error')
            return redirect(url_for('dashboard'))

    # Récupérer la liste des techniciens pour le SelectField
    techniciens = User.query.filter_by(role='technicien', actif=True).all()
    
    return render_template('manage_teams.html', equipe=equipe, techniciens=techniciens)


@teams_bp.route('/edit-team/<int:equipe_id>', methods=['GET', 'POST'])
@login_required
def edit_team(equipe_id):
    """Éditer les détails d'une équipe."""
    equipe = db.session.get(Equipe, equipe_id)
    if not equipe:
        abort(404)
    
    if current_user.role == 'chef_zone':
        # Vérifier si l'équipe appartient à la zone du chef de zone
        user_zone = current_user.zone
        user_zone_formatted = None
        if current_user.zone_relation:
            user_zone_formatted = f"{current_user.zone_relation.nom} ({current_user.zone_relation.code})"
        
        is_in_zone = (equipe.zone == user_zone or 
                     (user_zone_formatted and equipe.zone == user_zone_formatted) or
                     (current_user.zone_relation and equipe.zone == current_user.zone_relation.nom) or
                     (current_user.zone_relation and equipe.zone == current_user.zone_relation.code) or
                     equipe.chef_zone_id == current_user.id)
        
        if not is_in_zone:
            flash('Accès non autorisé : cette équipe n\'appartient pas à votre zone.', 'error')
            return redirect(url_for('dashboard'))

    from forms import TeamForm
    form = TeamForm()
    
    # Préremplir le formulaire avec les données de l'équipe (GET uniquement)
    if request.method == 'GET':
        form.nom_equipe.data = equipe.nom_equipe
        form.date_creation.data = equipe.date_creation
        form.zone.data = equipe.zone
        form.service.data = equipe.service
        form.technologies.data = equipe.technologies
        form.prestataire.data = equipe.prestataire if equipe.prestataire else ''

    if form.validate_on_submit():
        try:
            equipe.nom_equipe = form.nom_equipe.data
            equipe.technologies = form.technologies.data
            equipe.service = form.service.data
            equipe.zone = form.zone.data
            equipe.prestataire = form.prestataire.data if form.prestataire.data else None
            db.session.commit()
            flash('Équipe modifiée avec succès!', 'success')
            return redirect(url_for('teams.manage_team', equipe_id=equipe.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception('Error updating team')
            
            # Provide user-friendly error message
            error_msg = str(e).lower()
            if 'unique constraint' in error_msg or 'duplicate' in error_msg:
                user_msg = 'Une équipe avec ce nom existe déjà.'
            elif 'field' in error_msg or 'column' in error_msg:
                user_msg = 'Erreur technique de base de données. Contactez l\'administrateur.'
            else:
                user_msg = 'Une erreur est survenue lors de la modification. Réessayez ou contactez l\'administrateur.'
            
            flash(user_msg, 'error')

    return render_template('edit_team.html', form=form, equipe=equipe)


@teams_bp.route('/api/publish-selected-teams', methods=['POST'])
@login_required
@csrf.exempt
def publish_selected_teams():
    """API — Publier des équipes sélectionnées."""
    if current_user.role not in ['chef_zone', 'chef_pur']:
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    team_ids = data.get('team_ids', [])

    if not team_ids:
        return jsonify({'success': False, 'error': 'Aucune équipe sélectionnée'}), 400

    today = date.today()

    try:
        if current_user.role == 'chef_pur':
            teams_to_publish = Equipe.query.filter(
                Equipe.id.in_(team_ids),
                Equipe.actif == True,
                Equipe.publie == False
            ).all()
        else:
            # Pour les chefs de zone, trouver les équipes de la zone (pas seulement créateur)
            user_zone = current_user.zone
            teams_to_publish = Equipe.query.filter(
                Equipe.id.in_(team_ids),
                Equipe.zone == user_zone,
                Equipe.actif == True,
                Equipe.publie == False
            ).all()
            
            # Si rien trouvé et qu'on peut formater la zone, essayer aussi
            if not teams_to_publish and user_zone:
                from models import Zone
                zone_obj = Zone.query.filter_by(nom=user_zone).first()
                if zone_obj:
                    user_zone_formatted = f"{zone_obj.nom} ({zone_obj.code})"
                    if user_zone_formatted != user_zone:
                        teams_formatted = Equipe.query.filter(
                            Equipe.id.in_(team_ids),
                            Equipe.zone == user_zone_formatted,
                            Equipe.actif == True,
                            Equipe.publie == False
                        ).all()
                        teams_to_publish = teams_formatted

        published_count = 0
        for team in teams_to_publish:
            team.publie = True
            team.date_publication = today
            published_count += 1

        db.session.commit()

        return jsonify({
            'success': True,
            'published_count': published_count,
            'message': f'{published_count} équipe(s) publiée(s) avec succès'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception('Error publishing teams')
        
        # Provide user-friendly error message
        error_msg = str(e).lower()
        if 'field' in error_msg or 'column' in error_msg:
            user_msg = 'Erreur technique de base de données. Contactez l\'administrateur.'
        elif 'operational error' in error_msg or 'integrity error' in error_msg:
            user_msg = 'Erreur lors de la publication des équipes. Réessayez.'
        else:
            user_msg = 'Une erreur est survenue. Contactez l\'administrateur.'
        
        return jsonify({'success': False, 'error': user_msg}), 500


@teams_bp.route('/api/unpublish-selected-teams', methods=['POST'])
@login_required
@csrf.exempt
def unpublish_selected_teams():
    """API — Dé-publier des équipes sélectionnées."""
    if current_user.role not in ['chef_zone', 'chef_pur']:
        return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403

    try:
        if request.is_json:
            data = request.get_json()
            team_ids = data.get('team_ids', [])
        else:
            data = request.form.to_dict()
            team_ids = data.get('team_ids', [])
            if isinstance(team_ids, str):
                team_ids = [int(id.strip()) for id in team_ids.split(',') if id.strip().isdigit()]
        
        if not team_ids:
            return jsonify({'success': False, 'error': 'Aucune équipe sélectionnée'}), 400

        if current_user.role == 'chef_pur':
            teams = Equipe.query.filter(Equipe.id.in_(team_ids), Equipe.publie == True).all()
        else:
            teams = Equipe.query.filter(
                Equipe.id.in_(team_ids),
                Equipe.zone == current_user.zone,
                Equipe.publie == True
            ).all()

        unpublished_count = 0
        for team in teams:
            team.publie = False
            unpublished_count += 1

        db.session.commit()

        return jsonify({
            'success': True,
            'unpublished_count': unpublished_count,
            'message': f'{unpublished_count} équipe(s) dé-publiée(s) avec succès'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@teams_bp.route('/api/all-teams')
@login_required
def get_all_teams():
    """API — Récupérer toutes les équipes (filtrées selon rôle)."""
    if current_user.role not in ['chef_zone', 'chef_pur']:
        return jsonify({'error': 'Access denied'}), 403

    try:
        if current_user.role == 'chef_pur':
            teams = Equipe.query.filter_by(actif=True).all()
        else:
            # Pour les chefs de zone, essayer plusieurs formats de zone
            user_zone = current_user.zone
            teams = Equipe.query.filter_by(
                zone=user_zone,
                actif=True
            ).all()
            
            # Si rien trouvé et qu'on peut formater la zone, essayer aussi
            if not teams and user_zone:
                from models import Zone
                zone_obj = Zone.query.filter_by(nom=user_zone).first()
                if zone_obj:
                    user_zone_formatted = f"{zone_obj.nom} ({zone_obj.code})"
                    if user_zone_formatted != user_zone:
                        teams_formatted = Equipe.query.filter_by(
                            zone=user_zone_formatted,
                            actif=True
                        ).all()
                        teams = teams_formatted

        teams_data = []
        for team in teams:
            teams_data.append({
                'id': team.id,
                'nom_equipe': team.nom_equipe,
                'zone': team.zone,
                'service': team.service,
                'technologies': team.technologies,
                'nb_membres': len(team.membres) if hasattr(team, 'membres') else 0,
                'publie': team.publie,
                'date_creation': team.date_creation.isoformat(),
                'date_publication': team.date_publication.isoformat() if team.date_publication else None
            })

        return jsonify({'success': True, 'teams': teams_data})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@teams_bp.route('/api/equipes-jour')
@login_required
def get_equipes_jour():
    """API — Récupérer les équipes du jour (publiées aujourd'hui)."""
    if current_user.role not in ['chef_zone', 'chef_pur']:
        return jsonify({'error': 'Access denied'}), 403

    try:
        today = date.today()
        
        # Déterminer la zone de l'utilisateur
        user_zone = None
        user_zone_formatted = None
        if current_user.zone_relation:
            user_zone = f"{current_user.zone_relation.nom} ({current_user.zone_relation.code})"
            user_zone_formatted = user_zone
            print(f"DEBUG: get_equipes_jour - Zone depuis zone_relation: {user_zone}")
        elif current_user.zone:
            user_zone = current_user.zone
            # Essayer aussi le format avec code si possible
            from models import Zone
            zone_obj = Zone.query.filter_by(nom=current_user.zone).first()
            if zone_obj:
                user_zone_formatted = f"{zone_obj.nom} ({zone_obj.code})"
            print(f"DEBUG: get_equipes_jour - Zone depuis zone texte: {user_zone}, formatée: {user_zone_formatted}")
        else:
            print(f"DEBUG: get_equipes_jour - Aucune zone définie pour l'utilisateur")
        
        print(f"DEBUG: get_equipes_jour - User: {current_user.username}, Zone finale: {user_zone}")
        
        if current_user.role == 'chef_pur':
            # Le chef PUR voit toutes les équipes publiées aujourd'hui
            equipes = Equipe.query.filter_by(
                publie=True, 
                date_publication=today,
                actif=True
            ).all()
        else:
            # Le chef de zone voit uniquement les équipes de sa zone publiées aujourd'hui
            if not user_zone:
                print(f"DEBUG: get_equipes_jour - Pas de zone, retour vide")
                return jsonify({'success': True, 'equipes': []})
            
            print(f"DEBUG: get_equipes_jour - Filtre: zone='{user_zone}', publie=True, date_publication={today}, actif=True")
            
            # Essayer d'abord avec la zone principale
            equipes = Equipe.query.filter_by(
                zone=user_zone,
                publie=True,
                date_publication=today,
                actif=True
            ).all()
            
            print(f"DEBUG: get_equipes_jour - Recherche 1 avec zone '{user_zone}': {len(equipes)} équipes trouvées")
            if equipes:
                for e in equipes:
                    print(f"  - {e.nom_equipe} (zone={repr(e.zone)}, publie={e.publie}, date={e.date_publication})")
            
            # Si rien trouvé et qu'on a une zone formatée différente, essayer aussi
            if not equipes and user_zone_formatted and user_zone_formatted != user_zone:
                print(f"DEBUG: get_equipes_jour - Filtre 2: zone='{user_zone_formatted}', publie=True, date_publication={today}, actif=True")
                equipes_formatted = Equipe.query.filter_by(
                    zone=user_zone_formatted,
                    publie=True,
                    date_publication=today,
                    actif=True
                ).all()
                print(f"DEBUG: get_equipes_jour - Recherche 2 avec zone formatée '{user_zone_formatted}': {len(equipes_formatted)} équipes trouvées")
                equipes = equipes_formatted
            
            # Si toujours rien et qu'on a une zone_relation, essayer avec le nom simple
            if not equipes and current_user.zone_relation:
                zone_simple = current_user.zone_relation.nom
                if zone_simple != user_zone:
                    print(f"DEBUG: get_equipes_jour - Filtre 3: zone='{zone_simple}', publie=True, date_publication={today}, actif=True")
                    equipes_simple = Equipe.query.filter_by(
                        zone=zone_simple,
                        publie=True,
                        date_publication=today,
                        actif=True
                    ).all()
                    print(f"DEBUG: get_equipes_jour - Recherche 3 avec zone simple '{zone_simple}': {len(equipes_simple)} équipes trouvées")
                    equipes = equipes_simple
            
            # Debug: voir TOUTES les équipes de cette zone (peu importe publie/date)
            all_equipes_for_zone = Equipe.query.filter_by(zone=user_zone).all()
            print(f"DEBUG: get_equipes_jour - TOUTES équipes de la zone '{user_zone}': {len(all_equipes_for_zone)}")
            for e in all_equipes_for_zone:
                print(f"  - {e.nom_equipe} (zone={repr(e.zone)}, publie={e.publie}, date={e.date_publication}, actif={e.actif})")
        
        print(f"DEBUG: get_equipes_jour - {len(equipes)} équipes trouvées")
        
        equipes_data = []
        for equipe in equipes:
            # Compter les membres
            nb_membres = MembreEquipe.query.filter_by(equipe_id=equipe.id).count()
            
            equipes_data.append({
                'id': equipe.id,
                'nom_equipe': equipe.nom_equipe,
                'zone': equipe.zone,
                'service': equipe.service,
                'technologies': equipe.technologies,
                'prestataire': equipe.prestataire,
                'nb_membres': nb_membres,
                'date_creation': equipe.date_creation.isoformat(),
                'date_publication': equipe.date_publication.isoformat() if equipe.date_publication else None
            })

        return jsonify({'success': True, 'equipes': equipes_data})

    except Exception as e:
        print(f"DEBUG: get_equipes_jour - Erreur: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@teams_bp.route('/api/equipes-inactives')
@login_required
def get_equipes_inactives():
    """API — Récupérer les équipes inactives (non publiées)."""
    if current_user.role not in ['chef_zone', 'chef_pur']:
        return jsonify({'error': 'Access denied'}), 403

    try:
        # Déterminer la zone de l'utilisateur
        user_zone = None
        if current_user.zone_relation:
            user_zone = f"{current_user.zone_relation.nom} ({current_user.zone_relation.code})"
            print(f"DEBUG: get_equipes_inactives - Zone depuis zone_relation: {user_zone}")
        elif current_user.zone:
            user_zone = current_user.zone
            print(f"DEBUG: get_equipes_inactives - Zone depuis zone texte: {user_zone}")
        else:
            print(f"DEBUG: get_equipes_inactives - Aucune zone définie pour l'utilisateur")
            print(f"DEBUG: get_equipes_inactives - zone_id: {current_user.zone_id}, zone: {repr(current_user.zone)}")
            if current_user.zone_relation:
                print(f"DEBUG: get_equipes_inactives - zone_relation existe: {current_user.zone_relation}")
            else:
                print(f"DEBUG: get_equipes_inactives - zone_relation est None")
        
        print(f"DEBUG: get_equipes_inactives - User: {current_user.username}, Zone finale: {user_zone}")
        
        if current_user.role == 'chef_pur':
            # Le chef PUR voit toutes les équipes non publiées
            equipes = Equipe.query.filter_by(
                publie=False,
                actif=True
            ).all()
        else:
            # Le chef de zone voit uniquement les équipes de sa zone non publiées
            if not user_zone:
                print(f"DEBUG: get_equipes_inactives - Pas de zone, retour vide")
                return jsonify({'success': True, 'equipes': []})
            
            # D'abord essayer avec la zone formatée
            equipes = Equipe.query.filter_by(
                zone=user_zone,
                publie=False,
                actif=True
            ).all()
            
            print(f"DEBUG: get_equipes_inactives - Recherche avec zone formatée '{user_zone}': {len(equipes)} équipes")
            
            # Si rien trouvé, essayer avec juste le nom de la zone
            if not equipes and current_user.zone_relation:
                zone_simple = current_user.zone_relation.nom
                equipes_simple = Equipe.query.filter_by(
                    zone=zone_simple,
                    publie=False,
                    actif=True
                ).all()
                print(f"DEBUG: get_equipes_inactives - Recherche avec zone simple '{zone_simple}': {len(equipes_simple)} équipes")
                equipes = equipes_simple
            
            # Si toujours rien, essayer avec le code
            if not equipes and current_user.zone_relation:
                zone_code = current_user.zone_relation.code
                equipes_code = Equipe.query.filter_by(
                    zone=zone_code,
                    publie=False,
                    actif=True
                ).all()
                print(f"DEBUG: get_equipes_inactives - Recherche avec zone code '{zone_code}': {len(equipes_code)} équipes")
                equipes = equipes_code
            
            # Si toujours rien, vérifier toutes les équipes de l'utilisateur pour debug
            if not equipes:
                all_equipes_user = Equipe.query.filter_by(
                    chef_zone_id=current_user.id,
                    actif=True
                ).all()
                print(f"DEBUG: get_equipes_inactives - Toutes les équipes de l'utilisateur {current_user.id}: {len(all_equipes_user)}")
                for eq in all_equipes_user:
                    print(f"  - {eq.nom_equipe} (zone: {repr(eq.zone)}, publie: {eq.publie})")
                
                # Filtrer manuellement pour debug
                manual_equipes = []
                for eq in all_equipes_user:
                    if eq.publie == False:  # Équipes non publiées
                        if (eq.zone == user_zone or 
                            (current_user.zone_relation and eq.zone == current_user.zone_relation.nom) or
                            (current_user.zone_relation and eq.zone == current_user.zone_relation.code)):
                            manual_equipes.append(eq)
                            print(f"DEBUG: get_equipes_inactives - Équipe trouvée manuellement: {eq.nom_equipe}")
                
                if manual_equipes:
                    equipes = manual_equipes
                    print(f"DEBUG: get_equipes_inactives - {len(manual_equipes)} équipes trouvées manuellement")
        
        print(f"DEBUG: get_equipes_inactives - {len(equipes)} équipes trouvées")
        
        equipes_data = []
        for equipe in equipes:
            # Compter les membres
            nb_membres = MembreEquipe.query.filter_by(equipe_id=equipe.id).count()
            
            equipes_data.append({
                'id': equipe.id,
                'nom_equipe': equipe.nom_equipe,
                'zone': equipe.zone,
                'service': equipe.service,
                'technologies': equipe.technologies,
                'prestataire': equipe.prestataire,
                'nb_membres': nb_membres,
                'date_creation': equipe.date_creation.isoformat(),
                'date_publication': equipe.date_publication.isoformat() if equipe.date_publication else None
            })

        return jsonify({'success': True, 'equipes': equipes_data})

    except Exception as e:
        print(f"DEBUG: get_equipes_inactives - Erreur: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
