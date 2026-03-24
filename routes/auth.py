"""
Module d'authentification et session — routes auth, dashboard, vérification session.
"""

from flask import render_template, request, redirect, session, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from datetime import datetime, timezone, timedelta

from app import db
from forms import LoginForm
from models import User, Produit, MouvementStock, ReservationPiece, Intervention, Equipe
from utils import log_activity, get_chef_pur_stats, get_chef_pilote_stats, get_chef_zone_stats, get_technicien_interventions, get_performance_data, build_stats_by_zone_tech
from extensions import csrf  # needed to exempt login in tests
from cache_decorators import cache_kpi_data


def register_auth_blueprint(app):
    """Enregistre les routes d'authentification directement sur l'app (pas de blueprint)."""
    
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.password_hash and user.actif and check_password_hash(
                    user.password_hash, form.password.data):
                login_user(user)
                session.permanent = True
                log_activity(
                    user_id=user.id,
                    action='login',
                    module='auth',
                    entity_name=f"{user.prenom} {user.nom}",
                    details={'username': user.username}
                )

                flash('Connexion réussie!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(
                    url_for('dashboard'))
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'error')

        return render_template('login.html', form=form)

    @app.route('/reset-password', methods=['GET', 'POST'])
    def reset_password_request():
        """Minimal reset password endpoint kept for compatibility with templates.
        In the real app this should send a password reset email; for tests it
        simply redirects back to the login page with an informational flash.
        """
        flash('Password reset not configured in test environment.', 'info')
        return redirect(url_for('login'))

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
        if current_user.role == 'chef_pur':
            performance_data = get_performance_data()
            stats_by_zone_tech = build_stats_by_zone_tech()
            last_update = datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')
            techniciens = User.query.filter_by(role='technicien', actif=True).all()
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
            stats = get_chef_zone_stats(current_user.zone)
            stats_pur = get_chef_pur_stats(zone=current_user.zone)
            stats_pur['performance_data'] = get_performance_data(
                zone=current_user.zone)
            return render_template('dashboard_chef_zone.html',
                                   stats=stats,
                                   stats_pur=stats_pur)
        elif current_user.role == 'technicien':
            return render_template('dashboard_technicien.html',
                                   interventions=get_technicien_interventions(
                                       current_user.id))
        elif current_user.role == 'gestionnaire_stock':
            return redirect(url_for('stock.gestion_stock'))
        elif current_user.role == 'magasinier':
            # PHASE 1 FIX: Dashboard spécialisé pour magasinier
            # Vérifier que magasinier a une zone assignée
            if not current_user.zone_id:
                flash('⚠️ Erreur: Vous n\'êtes pas assigné à une zone. Contactez votre administrateur.', 'error')
                return redirect(url_for('logout'))
            
            from zone_rbac import filter_produit_by_emplacement_zone, filter_mouvement_by_zone
            
            # Stats zone magasinier - FIXED: Use zone_relation (FK object) not legacy zone string
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
            total_value = sum([p.quantite * (float(p.prix_vente) if p.prix_vente else 0) for p in produits_zone])
            articles_low_stock = len([p for p in produits_zone if p.quantite and p.quantite < 10])
            
            # Mouvements par type
            entrees = len([m for m in mouvements_zone if m.type_mouvement == 'entree'])
            sorties = len([m for m in mouvements_zone if m.type_mouvement == 'sortie'])
            
            # NOUVEAU: Réservations techniciens en attente
            nb_reservations_attente = ReservationPiece.query.join(
                Intervention, ReservationPiece.intervention_id == Intervention.id
            ).join(
                User, Intervention.technicien_id == User.id
            ).filter(
                User.zone_id == current_user.zone_id,
                ReservationPiece.statut == ReservationPiece.STATUT_EN_ATTENTE
            ).count()
            
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
        elif current_user.role == 'rh':
            return redirect(url_for('dashboard_rh'))
        else:
            flash('Rôle utilisateur non reconnu.', 'error')
            return redirect(url_for('logout'))
    
    @app.route('/magasinier/tableau-de-bord')
    @login_required
    def dashboard_magasinier():
        """Dashboard spécialisé pour magasinier - POINT D'ENTRÉE PRINCIPAL"""
        if current_user.role != 'magasinier':
            flash('❌ Accès refusé: cette page est réservée aux magasins.', 'error')
            return redirect(url_for('dashboard'))
        
        # Vérifier que magasinier a une zone assignée
        if not current_user.zone_id:
            flash('⚠️ Erreur: Vous n\'êtes pas assigné à une zone. Contactez votre administrateur.', 'error')
            return redirect(url_for('logout'))
        
        from zone_rbac import filter_produit_by_emplacement_zone, filter_mouvement_by_zone
        
        # Stats zone magasinier
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
        total_value = sum([p.quantite * (float(p.prix_vente) if p.prix_vente else 0) for p in produits_zone])
        articles_low_stock = len([p for p in produits_zone if p.quantite and p.quantite < 10])
        
        # Mouvements par type
        entrees = len([m for m in mouvements_zone if m.type_mouvement == 'entree'])
        sorties = len([m for m in mouvements_zone if m.type_mouvement == 'sortie'])
        
        # NOUVEAU: Réservations techniciens en attente
        nb_reservations_attente = ReservationPiece.query.join(
            Intervention, ReservationPiece.intervention_id == Intervention.id
        ).join(
            User, Intervention.technicien_id == User.id
        ).filter(
            User.zone_id == current_user.zone_id,
            ReservationPiece.statut == ReservationPiece.STATUT_EN_ATTENTE
        ).count()
        
        # Log activity
        log_activity(
            user_id=current_user.id,
            action='view_dashboard',
            module='magasinier',
            entity_name=f"{current_user.prenom} {current_user.nom}",
            details={'zone_id': current_user.zone_id, 'produits_count': total_articles}
        )
        
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
    
    @app.route('/dashboard/rh')
    @login_required
    def dashboard_rh():
        """
        RH Module Dashboard - Congé management, heures d'intervention, team management
        ✅ Phase 4: Main entry point for RH managers
        """
        allowed_roles = ['rh', 'chef_pur']
        if current_user.role not in allowed_roles:
            flash('❌ Accès refusé: cette page est réservée aux gestionnaires RH et Chef PUR.', 'error')
            return redirect(url_for('dashboard'))
        
        # Get summary statistics for RH dashboard
        year = request.args.get('year', datetime.now(timezone.utc).year, type=int)
        month = request.args.get('month', datetime.now(timezone.utc).month, type=int)
        
        # Stats for leave requests
        from models import LeaveRequest
        pending_count = LeaveRequest.query.filter_by(statut='pending').count()
        approved_count = LeaveRequest.query.filter_by(statut='approved').count()
        rejected_count = LeaveRequest.query.filter_by(statut='rejected').count()
        total_count = LeaveRequest.query.count()
        
        # Log activity
        from utils import log_activity
        log_activity(
            user_id=current_user.id,
            action='view_dashboard',
            module='rh',
            entity_name=f"{current_user.prenom} {current_user.nom}",
            details={'year': year, 'month': month}
        )
        
        return render_template('dashboard_rh.html',
                             year=year,
                             month=month,
                             pending_count=pending_count,
                             approved_count=approved_count,
                             rejected_count=rejected_count,
                             total_count=total_count)
    
    @app.route('/dashboard/kpi')
    @login_required
    @cache_kpi_data(timeout=300)  # Cache for 5 minutes
    def dashboard_kpi():
        """
        KPI Dashboard - Performance metrics and scoring
        Enhanced with KPI data sourcing + fallback + Redis caching
        """
        # Check if user has access to KPI dashboard
        allowed_roles = ['chef_pur', 'chef_zone', 'admin']
        if current_user.role not in allowed_roles:
            flash('Accès refusé: seuls les chefs peuvent accéder au dashboard KPI', 'danger')
            return redirect(url_for('dashboard'))
        
        try:
            # Get enhanced performance data with KPI sourcing
            from utils import get_performance_data
            perf_data = get_performance_data()
            
            # Get KPI scores with filtering
            from datetime import date
            from kpi_models import KpiScore, KpiAlerte
            
            period = request.args.get('period', 'month')
            sort_by = request.args.get('sort', 'score')
            
            # Determine date range
            today = date.today()
            if period == 'day':
                period_start = today
            elif period == 'week':
                from datetime import timedelta
                period_start = today - timedelta(days=7)
            elif period == 'month':
                from dateutil.relativedelta import relativedelta
                period_start = today - relativedelta(months=1)
            else:  # year
                from dateutil.relativedelta import relativedelta
                period_start = today - relativedelta(years=1)
            
            # Fetch KPI scores
            query = KpiScore.query.filter(
                KpiScore.periode_fin >= period_start,
                KpiScore.periode_fin <= today,
                KpiScore.score_total != None
            )
            
            # Apply sorting
            if sort_by == 'tendance':
                query = query.order_by(KpiScore.tendance.desc())
            elif sort_by == 'anomalie':
                query = query.order_by(KpiScore.anomalie_detectee.desc())
            else:  # score
                query = query.order_by(KpiScore.score_total.desc())
            
            scores = query.limit(100).all()
            
            # Get active alerts
            active_alerts = KpiAlerte.query.filter(
                KpiAlerte.date_resolution == None
            ).all()
            
            # Calculate stats
            total_scores = len(scores)
            avg_score = sum(s.score_total for s in scores) / total_scores if scores else 0
            alerts_count = len(active_alerts)
            
            return render_template('dashboard_kpi.html',
                                 scores=scores,
                                 active_alerts=active_alerts,
                                 perf_data=perf_data,
                                 period=period,
                                 period_start=period_start.isoformat(),
                                 period_end=today.isoformat(),
                                 total_scores=total_scores,
                                 avg_score=round(avg_score, 2),
                                 alerts_count=alerts_count,
                                 sort_by=sort_by)
        
        except Exception as e:
            # Fallback if KPI system fails
            current_app.logger.error(f"KPI dashboard error: {str(e)}")
            flash(f'Erreur lors du chargement du KPI: {str(e)}', 'warning')
            return render_template('dashboard_kpi.html')
