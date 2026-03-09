"""
Routes API pour le système de KPI
Endpoints pour scores, objectifs, alertes, classements
"""

from flask import Blueprint, request, jsonify, render_template, current_app
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from extensions import db, cache
from models import User, Equipe, MembreEquipe
from kpi_models import KpiScore, KpiMetric, KpiAlerte, KpiHistorique, KpiObjectif
from kpi_engine import KpiScoringEngine, calculate_monthly_kpi, calculate_daily_kpi
from functools import wraps
import json
import logging

logger = logging.getLogger(__name__)

kpi_bp = Blueprint('kpi', __name__, url_prefix='/api/kpi')


def require_kpi_access(f):
    """Décorateur: vérifier l'accès aux KPI (chef_pur ou admin)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentification requise'}), 401
        
        # Accès pour chef_pur et admin
        if current_user.role not in ['chef_pur', 'admin']:
            return jsonify({'error': 'Accès refusé'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


@kpi_bp.route('/performance/unified', methods=['GET'])
@login_required
@require_kpi_access
def get_unified_performance():
    """
    🎯 API Endpoint - UNIFIED PERFORMANCE DATA WITH REDIS CACHING
    
    Returns consolidated performance data from:
    - NEW KPI system (5 metrics with weights)
    - OLD taux_reussite (backward compatibility)
    - Redis cached (5 min TTL)
    
    Query params:
    - zone: Optional zone filter (e.g., 'Dakar', 'Mbour')
    - period: 'day' (default), 'week', 'month'
    - sort: 'score' (default), 'taux', 'anomalie'
    
    Returns:
    {
        'equipes': [...],
        'techniciens': [...],
        'zones': [...],
        'pilots': [...],
        'metadata': {
            'source': 'unified_kpi',
            'cached': bool,
            'period': str,
            'timestamp': str,
            'fallback_used': bool
        }
    }
    """
    zone = request.args.get('zone', None)
    period = request.args.get('period', 'day')
    sort_by = request.args.get('sort', 'score')
    
    # Get unified performance data (with Redis caching built-in)
    from utils import get_performance_data
    data = get_performance_data(zone=zone)
    
    return jsonify(data)



@login_required
@require_kpi_access
def get_scores():
    """
    Récupère les scores KPI (dernier mois ou période spécifiée)
    Query params:
    - period: 'month' (défaut), 'year', 'all'
    - date: date spécifique (YYYY-MM-DD)
    - equipe_id: filtrer par équipe
    """
    period = request.args.get('period', 'month')
    filter_date = request.args.get('date', None)
    equipe_id = request.args.get('equipe_id', None)
    
    query = KpiScore.query.filter(KpiScore.score_total != None)
    
    # Déterminer la période
    today = date.today()
    if period == 'month':
        start_date = today - relativedelta(months=1)
    elif period == 'year':
        start_date = today - relativedelta(years=1)
    else:
        start_date = None
    
    if start_date:
        query = query.filter(KpiScore.periode_debut >= start_date)
    
    # Filtrer par équipe si spécifié
    if equipe_id:
        query = query.filter_by(equipe_id=equipe_id)
    
    # Filtrer par date spécifique si fournie
    if filter_date:
        filter_date = datetime.strptime(filter_date, '%Y-%m-%d').date()
        query = query.filter(
            db.func.date(KpiScore.periode_debut) <= filter_date,
            db.func.date(KpiScore.periode_fin) >= filter_date
        )
    
    scores = query.order_by(KpiScore.score_total.desc()).all()
    
    result = [{
        'id': score.id,
        'technicien': {
            'id': score.technicien.id,
            'nom': score.technicien.nom,
            'prenom': score.technicien.prenom,
            'email': score.technicien.email
        },
        'equipe': {
            'id': score.equipe.id if score.equipe else None,
            'nom': score.equipe.nom if score.equipe else None
        },
        'periode': {
            'debut': score.periode_debut.isoformat(),
            'fin': score.periode_fin.isoformat(),
            'type': score.periode_type
        },
        'scores': {
            'total': score.score_total,
            'resolution_1ere_visite': score.score_resolution_1ere_visite,
            'respect_sla': score.score_respect_sla,
            'qualite_rapports': score.score_qualite_rapports,
            'satisfaction_client': score.score_satisfaction_client,
            'consommation_stock': score.score_consommation_stock
        },
        'classement': {
            'rang_equipe': score.rang_equipe,
            'rang_global': score.rang_global
        },
        'tendance': score.tendance,
        'variation': score.variation_periode_precedente,
        'alerte_active': score.alerte_active,
        'anomalie': score.anomalie_detectee,
        'date_modification': score.date_modification.isoformat() if score.date_modification else None
    } for score in scores]
    
    return jsonify({
        'success': True,
        'count': len(result),
        'data': result
    }), 200


@kpi_bp.route('/scores/<int:technicien_id>', methods=['GET'])
@login_required
@require_kpi_access
def get_technician_scores(technicien_id):
    """Récupère les scores d'un technicien spécifique"""
    
    technicien = User.query.get_or_404(technicien_id)
    
    scores = KpiScore.query.filter_by(
        technicien_id=technicien_id
    ).filter(KpiScore.score_total != None).order_by(
        KpiScore.periode_debut.desc()
    ).limit(12).all()
    
    if not scores:
        return jsonify({'error': 'Aucun score trouvé'}), 404
    
    result = {
        'technicien': {
            'id': technicien.id,
            'nom': technicien.nom,
            'prenom': technicien.prenom,
            'email': technicien.email
        },
        'scores': [{
            'id': score.id,
            'periode': {
                'debut': score.periode_debut.isoformat(),
                'fin': score.periode_fin.isoformat()
            },
            'scores': {
                'total': score.score_total,
                'resolution_1ere_visite': score.score_resolution_1ere_visite,
                'respect_sla': score.score_respect_sla,
                'qualite_rapports': score.score_qualite_rapports,
                'satisfaction_client': score.score_satisfaction_client,
                'consommation_stock': score.score_consommation_stock
            },
            'tendance': score.tendance,
            'variation': score.variation_periode_precedente,
            'rang_equipe': score.rang_equipe,
            'rang_global': score.rang_global,
            'alerte_active': score.alerte_active
        } for score in scores],
        'objectifs_courants': {}
    }
    
    # Récupérer les objectifs courants
    objectifs = KpiObjectif.query.filter_by(
        technicien_id=technicien_id,
        annee=datetime.now().year
    ).first()
    
    if objectifs:
        result['objectifs_courants'] = {
            'resolution_1ere_visite': objectifs.objectif_resolution_1ere_visite,
            'respect_sla': objectifs.objectif_respect_sla,
            'qualite_rapports': objectifs.objectif_qualite_rapports,
            'satisfaction_client': objectifs.objectif_satisfaction_client,
            'consommation_stock': objectifs.objectif_consommation_stock
        }
    
    return jsonify({
        'success': True,
        'data': result
    }), 200


@kpi_bp.route('/scores/<int:technicien_id>/historique', methods=['GET'])
@login_required
@require_kpi_access
def get_technician_history(technicien_id):
    """Récupère l'historique détaillé (KpiHistorique) pour charting"""
    
    technicien = User.query.get_or_404(technicien_id)
    
    # Récupérer les 90 derniers jours
    start_date = date.today() - timedelta(days=90)
    
    history = KpiHistorique.query.filter(
        KpiHistorique.technicien_id == technicien_id,
        KpiHistorique.date >= start_date
    ).order_by(KpiHistorique.date.asc()).all()
    
    if not history:
        return jsonify({'error': 'Aucun historique'}), 404
    
    # Formater pour charting (Chart.js)
    labels = [h.date.isoformat() for h in history]
    
    result = {
        'technicien': {
            'id': technicien.id,
            'nom': f"{technicien.prenom} {technicien.nom}"
        },
        'labels': labels,
        'datasets': [
            {
                'label': 'Score Total',
                'data': [h.score_total for h in history],
                'borderColor': '#2563eb',
                'backgroundColor': 'rgba(37, 99, 235, 0.1)',
                'fill': True
            },
            {
                'label': '1ère Visite',
                'data': [h.score_resolution_1ere_visite for h in history],
                'borderColor': '#059669',
                'backgroundColor': 'rgba(5, 150, 105, 0.1)',
                'fill': False
            },
            {
                'label': 'SLA',
                'data': [h.score_respect_sla for h in history],
                'borderColor': '#dc2626',
                'backgroundColor': 'rgba(220, 38, 38, 0.1)',
                'fill': False
            },
            {
                'label': 'Qualité',
                'data': [h.score_qualite_rapports for h in history],
                'borderColor': '#f59e0b',
                'backgroundColor': 'rgba(245, 158, 11, 0.1)',
                'fill': False
            },
            {
                'label': 'Satisfaction',
                'data': [h.score_satisfaction_client for h in history],
                'borderColor': '#8b5cf6',
                'backgroundColor': 'rgba(139, 92, 246, 0.1)',
                'fill': False
            }
        ]
    }
    
    return jsonify({
        'success': True,
        'data': result
    }), 200


@kpi_bp.route('/ranking', methods=['GET'])
@login_required
@require_kpi_access
def get_ranking():
    """
    Classement des techniciens
    Query params:
    - top: 'top10' (défaut), 'bottom10', 'all'
    - equipe_id: filtrer par équipe
    """
    ranking_type = request.args.get('top', 'top10')
    equipe_id = request.args.get('equipe_id', None)
    
    # Récupérer le dernier mois complètement
    today = date.today()
    first_of_month = date(today.year, today.month, 1)
    
    query = KpiScore.query.filter(
        KpiScore.periode_debut <= first_of_month,
        KpiScore.score_total != None
    ).order_by(KpiScore.score_total.desc())
    
    if equipe_id:
        query = query.filter_by(equipe_id=equipe_id)
    
    if ranking_type == 'top10':
        scores = query.limit(10).all()
    elif ranking_type == 'bottom10':
        scores = query.order_by(KpiScore.score_total.asc()).limit(10).all()
    else:
        scores = query.all()
    
    result = [{
        'rang': i + 1,
        'technicien': {
            'id': score.technicien.id,
            'nom': f"{score.technicien.prenom} {score.technicien.nom}",
            'email': score.technicien.email
        },
        'equipe': {
            'id': score.equipe.id if score.equipe else None,
            'nom': score.equipe.nom if score.equipe else None
        },
        'score_total': score.score_total,
        'tendance': score.tendance,
        'variation': score.variation_periode_precedente,
        'alerte_active': score.alerte_active,
        'scores_detail': {
            'resolution_1ere_visite': score.score_resolution_1ere_visite,
            'respect_sla': score.score_respect_sla,
            'qualite_rapports': score.score_qualite_rapports,
            'satisfaction_client': score.score_satisfaction_client,
            'consommation_stock': score.score_consommation_stock
        }
    } for i, score in enumerate(scores)]
    
    return jsonify({
        'success': True,
        'type': ranking_type,
        'count': len(result),
        'data': result
    }), 200


@kpi_bp.route('/objectifs/<int:technicien_id>', methods=['GET', 'POST', 'PATCH'])
@login_required
@require_kpi_access
def manage_objectifs(technicien_id):
    """Gère les objectifs d'un technicien"""
    
    technicien = User.query.get_or_404(technicien_id)
    
    if request.method == 'GET':
        annee = request.args.get('annee', datetime.now().year, type=int)
        
        objectifs = KpiObjectif.query.filter_by(
            technicien_id=technicien_id,
            annee=annee
        ).first()
        
        if not objectifs:
            return jsonify({'error': 'Pas d\'objectifs pour cette année'}), 404
        
        return jsonify({
            'success': True,
            'data': {
                'id': objectifs.id,
                'technicien': {
                    'id': technicien.id,
                    'nom': f"{technicien.prenom} {technicien.nom}"
                },
                'annee': objectifs.annee,
                'objectifs': {
                    'resolution_1ere_visite': objectifs.objectif_resolution_1ere_visite,
                    'respect_sla': objectifs.objectif_respect_sla,
                    'qualite_rapports': objectifs.objectif_qualite_rapports,
                    'satisfaction_client': objectifs.objectif_satisfaction_client,
                    'consommation_stock': objectifs.objectif_consommation_stock
                },
                'dates': {
                    'debut': objectifs.date_debut.isoformat(),
                    'fin': objectifs.date_fin.isoformat()
                },
                'date_modification': objectifs.date_modification.isoformat() if objectifs.date_modification else None
            }
        }), 200
    
    elif request.method == 'POST':
        data = request.get_json()
        annee = data.get('annee', datetime.now().year)
        
        # Vérifier qu'aucun objectif n'existe pour cette année
        existing = KpiObjectif.query.filter_by(
            technicien_id=technicien_id,
            annee=annee
        ).first()
        
        if existing:
            return jsonify({'error': 'Objectifs déjà existants pour cette année'}), 409
        
        objectifs = KpiObjectif(
            technicien_id=technicien_id,
            annee=annee,
            objectif_resolution_1ere_visite=data.get('objectif_resolution_1ere_visite', 80),
            objectif_respect_sla=data.get('objectif_respect_sla', 95),
            objectif_qualite_rapports=data.get('objectif_qualite_rapports', 85),
            objectif_satisfaction_client=data.get('objectif_satisfaction_client', 80),
            objectif_consommation_stock=data.get('objectif_consommation_stock', 80),
            date_debut=date(annee, 1, 1),
            date_fin=date(annee, 12, 31),
            modifie_par=current_user.id
        )
        
        db.session.add(objectifs)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Objectifs créés',
            'data': {'id': objectifs.id}
        }), 201
    
    elif request.method == 'PATCH':
        annee = request.args.get('annee', datetime.now().year, type=int)
        data = request.get_json()
        
        objectifs = KpiObjectif.query.filter_by(
            technicien_id=technicien_id,
            annee=annee
        ).first_or_404()
        
        if 'objectif_resolution_1ere_visite' in data:
            objectifs.objectif_resolution_1ere_visite = data['objectif_resolution_1ere_visite']
        if 'objectif_respect_sla' in data:
            objectifs.objectif_respect_sla = data['objectif_respect_sla']
        if 'objectif_qualite_rapports' in data:
            objectifs.objectif_qualite_rapports = data['objectif_qualite_rapports']
        if 'objectif_satisfaction_client' in data:
            objectifs.objectif_satisfaction_client = data['objectif_satisfaction_client']
        if 'objectif_consommation_stock' in data:
            objectifs.objectif_consommation_stock = data['objectif_consommation_stock']
        
        objectifs.modifie_par = current_user.id
        objectifs.date_modification = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Objectifs mis à jour'
        }), 200


@kpi_bp.route('/alertes', methods=['GET'])
@login_required
@require_kpi_access
def get_alertes():
    """Récupère les alertes actives"""
    
    statut = request.args.get('statut', 'active')  # 'active' ou 'resolved'
    equipe_id = request.args.get('equipe_id', None)
    severite = request.args.get('severite', None)
    
    query = KpiAlerte.query
    
    if statut == 'active':
        query = query.filter_by(active=True)
    elif statut == 'resolved':
        query = query.filter_by(active=False)
    
    if equipe_id:
        query = query.join(User).join(MembreEquipe).filter(
            MembreEquipe.equipe_id == equipe_id
        )
    
    if severite:
        query = query.filter_by(severite=severite)
    
    alertes = query.order_by(
        KpiAlerte.date_creation.desc()
    ).limit(100).all()
    
    result = [{
        'id': alerte.id,
        'technicien': {
            'id': alerte.technicien.id,
            'nom': f"{alerte.technicien.prenom} {alerte.technicien.nom}"
        },
        'type': alerte.type_alerte,
        'severite': alerte.severite,
        'metrique': alerte.metrique,
        'titre': alerte.titre,
        'description': alerte.description,
        'valeur_actuelle': alerte.valeur_actuelle,
        'valeur_seuil': alerte.valeur_seuil,
        'recommandations': alerte.recommandations,
        'active': alerte.active,
        'date_creation': alerte.date_creation.isoformat(),
        'date_resolution': alerte.date_resolution.isoformat() if alerte.date_resolution else None,
        'resolu_par': {
            'id': alerte.resolu_par_user.id if alerte.resolu_par_user else None,
            'nom': f"{alerte.resolu_par_user.prenom} {alerte.resolu_par_user.nom}" if alerte.resolu_par_user else None
        } if alerte.resolu_par else None
    } for alerte in alertes]
    
    return jsonify({
        'success': True,
        'count': len(result),
        'data': result
    }), 200


@kpi_bp.route('/alertes/<int:alerte_id>/resolve', methods=['PATCH'])
@login_required
@require_kpi_access
def resolve_alerte(alerte_id):
    """Marque une alerte comme résolue"""
    
    alerte = KpiAlerte.query.get_or_404(alerte_id)
    
    data = request.get_json() or {}
    alerte.active = False
    alerte.date_resolution = datetime.now()
    alerte.resolu_par = current_user.id
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Alerte résolue'
    }), 200


@kpi_bp.route('/calculate', methods=['POST'])
@login_required
@require_kpi_access
def trigger_calculation():
    """Déclenche le calcul des KPI (admin uniquement)"""
    
    if current_user.role != 'admin':
        return jsonify({'error': 'Accès refusé'}), 403
    
    try:
        calculate_date = request.json.get('date', None)
        if calculate_date:
            calculate_date = datetime.strptime(calculate_date, '%Y-%m-%d').date()
        
        calculate_daily_kpi(calculate_date)
        
        return jsonify({
            'success': True,
            'message': 'Calcul des KPI complété'
        }), 200
    
    except Exception as e:
        logger.error(f"Error in KPI calculation: {e}")
        return jsonify({'error': str(e)}), 500


@kpi_bp.route('/metrics', methods=['GET'])
@login_required
@require_kpi_access
def get_metrics_config():
    """Récupère la configuration des métriques"""
    
    metrics = KpiMetric.query.all()
    
    result = [{
        'id': metric.id,
        'nom': metric.nom,
        'description': metric.description,
        'poids': metric.poids,
        'seuil_min': metric.seuil_min,
        'seuil_max': metric.seuil_max,
        'seuil_alerte': metric.seuil_alerte,
        'formule': metric.formule,
        'unite': metric.unite
    } for metric in metrics]
    
    return jsonify({
        'success': True,
        'data': result
    }), 200


def register_kpi_routes(app):
    """Enregistre le blueprint KPI"""
    app.register_blueprint(kpi_bp)
