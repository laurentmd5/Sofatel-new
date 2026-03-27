"""
KPI Utilities Module - Reusable KPI queries and calculations
Separates concerns: data retrieval, aggregation, and error handling
"""

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from app import db
from models import User, Equipe, MembreEquipe, Intervention, DemandeIntervention, FichierImport
from kpi_models import KpiScore, KpiAlerte
from extensions import cache
from sqlalchemy import func
import logging
import json

logger = logging.getLogger(__name__)


# ============================================================================
# PHASE 1: UNIFIED PERFORMANCE DATA WITH REDIS CACHING & KPI CONSOLIDATION
# ============================================================================

def get_unified_performance_data(zone=None, period='day', sort_by='kpi'):
    """
    🎯 UNIFIED PERFORMANCE DATA - CONSOLIDATION OF TWO SYSTEMS
    
    Replaces both:
    - Old System: utils.get_performance_data() with simple taux_reussite
    - New System: kpi_utils.get_performance_data_with_fallback() with KPI scores
    
    Features:
    ✅ Returns BOTH old fields (backward compatibility) + new KPI fields
    ✅ Single source of truth for performance data
    ✅ Redis cached (5 min TTL)
    ✅ Graceful fallback if KPI unavailable
    ✅ Color-coded performance (red <60, yellow 60-80, green >80)
    ✅ Trend detection (↑↓→)
    
    Args:
        zone (str): Optional zone filter
        period (str): 'day', 'week', 'month'
        sort_by (str): 'score' (default), 'taux', 'anomalie'
        
    Returns:
        dict: {
            'equipes': [{
                'nom_equipe': str,
                'zone': str,
                'taux_reussite': float,  # OLD FIELD (backward compat)
                'kpi_score_total': float,  # NEW: 0-100 weighted KPI score
                'kpi_resolution_1ere_visite': float,  # NEW: 30% weight
                'kpi_sla': float,  # NEW: 25% weight
                'kpi_qualite': float,  # NEW: 20% weight
                'kpi_satisfaction': float,  # NEW: 15% weight
                'kpi_stock': float,  # NEW: 10% weight
                'tendance': str,  # NEW: ↑ ↓ → 
                'variation': float,  # NEW: % change from previous period
                'performance_level': str,  # NEW: 'green'|'yellow'|'red'
            }],
            'techniciens': [...same structure...],
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
    # Generate cache key
    cache_key = f"perf_data:{zone}:{period}:{sort_by}"
    
    try:
        # Try to get from Redis cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info(f"[CACHE HIT] {cache_key}")
            return json.loads(cached_data)
    except Exception as e:
        logger.warning(f"[CACHE WARNING] Cache read failed: {e}")
    
    # Cache miss or error - compute fresh data
    try:
        today = date.today()
        
        # Determine period dates
        if period == 'week':
            period_start = today - timedelta(days=7)
        elif period == 'month':
            period_start = today - relativedelta(months=1)
        else:  # day
            period_start = today
        
        # ===== EQUIPES =====
        equipes_data = []
        equipes_query = Equipe.query.filter_by(actif=True)
        if zone:
            equipes_query = equipes_query.filter_by(zone=zone)
        
        # ===== PRÉ-CHARGEMENT DES DONNÉES (OPTIMISATION) =====
        equipes = equipes_query.all()
        equipe_ids = [e.id for e in equipes]
        
        # Définition de la requête pour les techniciens (manquait dans l'optimisation précédente)
        techniciens_query = User.query.filter_by(role='technicien', actif=True)
        if zone:
            techniciens_query = techniciens_query.filter_by(zone=zone)
            
        techniciens = techniciens_query.all()

        tech_ids = [t.id for t in techniciens]
        
        # Charger tous les membres d'équipe en une fois
        all_members = MembreEquipe.query.filter(MembreEquipe.equipe_id.in_(equipe_ids)).all() if equipe_ids else []
        equipe_to_techs = {}
        tech_to_equipe_id = {}
        for m in all_members:
            if m.technicien_id:
                if m.equipe_id not in equipe_to_techs:
                    equipe_to_techs[m.equipe_id] = []
                equipe_to_techs[m.equipe_id].append(m.technicien_id)
                tech_to_equipe_id[m.technicien_id] = m.equipe_id
        
        # Mapping equipe ID -> nom
        equipe_id_to_nom = {e.id: e.nom_equipe for e in equipes}
        
        # Liste de tous les techniciens impliqués (ceux filtrés + membres des équipes filtrées)
        involved_tech_ids = list(set(tech_ids + [m.technicien_id for m in all_members if m.technicien_id]))
        
        # Charger TOUS les KPI scores en une seule requête
        all_kpis = KpiScore.query.filter(
            KpiScore.technicien_id.in_(involved_tech_ids),
            KpiScore.periode_fin >= period_start,
            KpiScore.periode_fin <= today
        ).all() if involved_tech_ids else []
        
        # Organiser les KPI par technicien_id
        tech_kpi_map = {}
        for s in all_kpis:
            if s.technicien_id not in tech_kpi_map:
                tech_kpi_map[s.technicien_id] = []
            tech_kpi_map[s.technicien_id].append(s)
            
        # Pré-calculer les counts d'interventions pour le fallback (si KPI manquants)
        # Pour les équipes
        eq_interv_counts = {}
        if equipe_ids:
            counts = db.session.query(
                Intervention.equipe_id, 
                Intervention.statut, 
                func.count(Intervention.id)
            ).filter(Intervention.equipe_id.in_(equipe_ids)).group_by(Intervention.equipe_id, Intervention.statut).all()
            for eid, status, count in counts:
                if eid not in eq_interv_counts: eq_interv_counts[eid] = {'total': 0, 'valide': 0}
                eq_interv_counts[eid]['total'] += count
                if status == 'valide': eq_interv_counts[eid]['valide'] = count

        # Pour les techniciens
        tech_interv_counts = {}
        if tech_ids:
            counts = db.session.query(
                Intervention.technicien_id, 
                Intervention.statut, 
                func.count(Intervention.id)
            ).filter(Intervention.technicien_id.in_(tech_ids)).group_by(Intervention.technicien_id, Intervention.statut).all()
            for tid, status, count in counts:
                if tid not in tech_interv_counts: tech_interv_counts[tid] = {'total': 0, 'valide': 0}
                tech_interv_counts[tid]['total'] += count
                if status == 'valide': tech_interv_counts[tid]['valide'] = count

        # ===== EQUIPES - CONSTRUCTION =====
        equipes_data = []
        for equipe in equipes:
            member_ids = equipe_to_techs.get(equipe.id, [])
            
            # Récupérer les KPI pour cette équipe si possible
            kpi_scores = []
            if member_ids:
                for mid in member_ids:
                    kpi_scores.extend(tech_kpi_map.get(mid, []))

            
            if kpi_scores:
                valid_scores = [s for s in kpi_scores if s.score_total is not None]
                n = len(valid_scores) if valid_scores else 1
                avg_kpi_total = sum(s.score_total for s in valid_scores) / n if valid_scores else 0
                avg_kpi_1ere = sum(s.score_resolution_1ere_visite for s in valid_scores if s.score_resolution_1ere_visite) / n if valid_scores else 0
                avg_kpi_sla = sum(s.score_respect_sla for s in valid_scores if s.score_respect_sla) / n if valid_scores else 0
                avg_kpi_qualite = sum(s.score_qualite_rapports for s in valid_scores if s.score_qualite_rapports) / n if valid_scores else 0
                avg_kpi_satisfaction = sum(s.score_satisfaction_client for s in valid_scores if s.score_satisfaction_client) / n if valid_scores else 0
                avg_kpi_stock = sum(s.score_consommation_stock for s in valid_scores if s.score_consommation_stock) / n if valid_scores else 0
                
                latest_score = sorted(kpi_scores, key=lambda x: x.periode_fin)[-1] if kpi_scores else None
                tendance = latest_score.tendance if latest_score else '→'
                variation = latest_score.variation_periode_precedente if latest_score else 0
            else:
                # Fallback optimisé
                stats = eq_interv_counts.get(equipe.id, {'total': 0, 'valide': 0})
                taux = (stats['valide'] / stats['total'] * 100) if stats['total'] > 0 else 0
                avg_kpi_total = taux
                avg_kpi_1ere, avg_kpi_sla, avg_kpi_qualite, avg_kpi_satisfaction, avg_kpi_stock = taux, 0, 0, 0, 0
                tendance, variation = '→', 0
            
            perf_level = 'green' if avg_kpi_total >= 80 else ('yellow' if avg_kpi_total >= 60 else 'red')
            
            # Trouver le principal pour cette équipe
            principal_name = "N/A"
            nb_membres = 0
            accompagnant_names = []
            
            # Recherche optimisée des membres
            team_members = [m for m in all_members if m.equipe_id == equipe.id]
            nb_membres = len(team_members)
            for m in team_members:
                if m.type_membre == 'technicien':
                    principal_name = f"{m.prenom} {m.nom}"
                elif m.type_membre == 'accompagnant':
                    accompagnant_names.append(f"{m.prenom} {m.nom}")
            
            equipes_data.append({
                'id': equipe.id,
                'name': equipe.nom_equipe,
                'nom_equipe': equipe.nom_equipe,
                'principal': principal_name,
                'validated': eq_interv_counts.get(equipe.id, {}).get('valide', 0),
                'nb_membres': nb_membres,
                'accompagnants': len(accompagnant_names),
                'accompagnant_names': ', '.join(accompagnant_names) if accompagnant_names else 'Aucun',
                'zone': equipe.zone,
                'prestataire': equipe.prestataire or '',
                'technologies': equipe.technologies,
                'taux_reussite': round(avg_kpi_total, 1),
                'kpi_score_total': round(avg_kpi_total, 2),
                'kpi_resolution_1ere_visite': round(avg_kpi_1ere, 1),
                'kpi_sla': round(avg_kpi_sla, 1),
                'kpi_qualite': round(avg_kpi_qualite, 1),
                'kpi_satisfaction': round(avg_kpi_satisfaction, 1),
                'kpi_stock': round(avg_kpi_stock, 1),
                'tendance': tendance,
                'variation': round(variation, 1) if variation else 0,
                'performance_level': perf_level,
                'interventions_realisees': eq_interv_counts.get(equipe.id, {}).get('valide', 0)
            })
        
        # Sort équipes
        equipes_data.sort(key=lambda x: x['kpi_score_total'], reverse=True)
        
        # ===== TECHNICIENS - CONSTRUCTION =====
        techniciens_data = []
        for tech in techniciens:
            kpi_scores = tech_kpi_map.get(tech.id, [])
            
            if kpi_scores:
                valid_scores = [s for s in kpi_scores if s.score_total is not None]
                n = len(valid_scores) if valid_scores else 1
                avg_kpi_total = sum(s.score_total for s in valid_scores) / n if valid_scores else 0
                avg_kpi_1ere = sum(s.score_resolution_1ere_visite for s in valid_scores if s.score_resolution_1ere_visite) / n if valid_scores else 0
                avg_kpi_sla = sum(s.score_respect_sla for s in valid_scores if s.score_respect_sla) / n if valid_scores else 0
                avg_kpi_qualite = sum(s.score_qualite_rapports for s in valid_scores if s.score_qualite_rapports) / n if valid_scores else 0
                avg_kpi_satisfaction = sum(s.score_satisfaction_client for s in valid_scores if s.score_satisfaction_client) / n if valid_scores else 0
                avg_kpi_stock = sum(s.score_consommation_stock for s in valid_scores if s.score_consommation_stock) / n if valid_scores else 0
                
                latest_score = sorted(kpi_scores, key=lambda x: x.periode_fin)[-1] if kpi_scores else None
                tendance = latest_score.tendance if latest_score else '→'
                variation = latest_score.variation_periode_precedente if latest_score else 0
            else:
                stats = tech_interv_counts.get(tech.id, {'total': 0, 'valide': 0})
                taux = (stats['valide'] / stats['total'] * 100) if stats['total'] > 0 else 0
                avg_kpi_total = taux
                avg_kpi_1ere, avg_kpi_sla, avg_kpi_qualite, avg_kpi_satisfaction, avg_kpi_stock = taux, 0, 0, 0, 0
                tendance, variation = '→', 0
            
            perf_level = 'green' if avg_kpi_total >= 80 else ('yellow' if avg_kpi_total >= 60 else 'red')
            
            techniciens_data.append({
                'id': tech.id,
                'name': f"{tech.prenom} {tech.nom}",
                'nom': tech.nom,
                'prenom': tech.prenom,
                'equipe_nom': equipe_id_to_nom.get(tech_to_equipe_id.get(tech.id)),
                'zone': tech.zone,
                'technologies': tech.technologies,
                'taux_reussite': round(avg_kpi_total, 1),
                'kpi_score_total': round(avg_kpi_total, 2),
                'kpi_resolution_1ere_visite': round(avg_kpi_1ere, 1),
                'kpi_sla': round(avg_kpi_sla, 1),
                'kpi_qualite': round(avg_kpi_qualite, 1),
                'kpi_satisfaction': round(avg_kpi_satisfaction, 1),
                'kpi_stock': round(avg_kpi_stock, 1),
                'tendance': tendance,
                'variation': round(variation, 1) if variation else 0,
                'performance_level': perf_level,
                'interventions_realisees': tech_interv_counts.get(tech.id, {}).get('valide', 0)
            })
        
        techniciens_data.sort(key=lambda x: x['kpi_score_total'], reverse=True)

        
        # ===== ZONES =====
        zones_data = []
        for chef_zone in User.query.filter_by(role='chef_zone', actif=True).all():
            # Équipes gérées par ce chef_zone
            equipes_creees = Equipe.query.filter_by(
                chef_zone_id=chef_zone.id, actif=True).count()
            
            equipes_publiees = Equipe.query.filter_by(
                chef_zone_id=chef_zone.id, 
                publie=True, 
                actif=True).count()
            
            # Demandes affectées dans cette zone
            demandes_affectees = Intervention.query.join(
                User, Intervention.technicien_id == User.id).filter(
                User.zone == chef_zone.zone,
                Intervention.statut.in_(['en_cours', 'termine', 'valide'])).count()
            
            # Demandes validées dans cette zone
            demandes_validees = Intervention.query.join(
                User, Intervention.technicien_id == User.id).filter(
                User.zone == chef_zone.zone,
                Intervention.statut == 'valide').count()
            
            zones_data.append({
                'name': chef_zone.zone,
                'chef_zone': f"{chef_zone.nom} {chef_zone.prenom}",
                'created': equipes_creees,
                'published': equipes_publiees,
                'affected': demandes_affectees,
                'validated': demandes_validees
            })
        
        # ===== PILOTS =====
        pilots_data = []
        for chef_pilote in User.query.filter_by(role='chef_pilote', actif=True).all():
            # Demandes importées par ce chef
            demandes_importees = FichierImport.query.filter_by(
                importe_par=chef_pilote.id).count()
            
            # Demandes dispatchées
            demandes_dispatch = DemandeIntervention.query.filter_by(
                service=chef_pilote.service).filter(
                DemandeIntervention.statut.in_(['affecte', 'en_cours', 'valide'])).count()
            
            # Interventions validées pour ce service
            demande_ids = [d.id for d in DemandeIntervention.query.filter_by(
                service=chef_pilote.service).all()]
            
            interventions_validees = 0
            if demande_ids:
                interventions_validees = Intervention.query.filter(
                    Intervention.demande_id.in_(demande_ids),
                    Intervention.statut == 'valide').count()
            
            pilots_data.append({
                'name': f"{chef_pilote.nom} {chef_pilote.prenom}",
                'service': chef_pilote.service or 'N/A',
                'imported': demandes_importees,
                'dispatched': demandes_dispatch,
                'validated': interventions_validees
            })
        
        result = {
            'equipes': equipes_data,
            'techniciens': techniciens_data,
            'zones': zones_data,
            'pilots': pilots_data,
            'metadata': {
                'source': 'unified_kpi',
                'cached': False,
                'period': period,
                'timestamp': str(today),
                'fallback_used': False
            }
        }
        
        # Cache the result for 5 minutes (300 seconds)
        try:
            cache.set(cache_key, json.dumps(result, default=str), timeout=300)
            logger.info(f"[CACHE SET] {cache_key} (TTL=5min)")
        except Exception as e:
            logger.warning(f"[CACHE WARNING] Cache write failed: {e}")
        
        logger.info(f"[SUCCESS] Unified performance data computed: {len(equipes_data)} teams, {len(techniciens_data)} techniciens")
        return result
        
    except Exception as e:
        logger.error(f"[ERROR] Unified performance data failed: {str(e)}", exc_info=True)
        return {
            'equipes': [],
            'techniciens': [],
            'zones': [],
            'pilots': [],
            'metadata': {
                'source': 'error',
                'cached': False,
                'period': period,
                'timestamp': str(date.today()),
                'fallback_used': False,
                'error': str(e)
            }
        }



    """
    Fetch KPI scores for a given period with optional filtering.
    
    Args:
        period (str): 'day', 'week', 'month', 'year'
        zone (str): Optional zone filter
        equipe_id (int): Optional team filter
        sort_by (str): 'score', 'tendance', 'anomalie'
        limit (int): Max results
        
    Returns:
        list: KpiScore objects
    """
    try:
        today = date.today()
        
        # Determine date range
        if period == 'day':
            period_start = today
        elif period == 'week':
            period_start = today - timedelta(days=7)
        elif period == 'month':
            period_start = today - relativedelta(months=1)
        else:  # year
            period_start = today - relativedelta(years=1)
        
        # Build query
        query = KpiScore.query.filter(
            KpiScore.periode_fin >= period_start,
            KpiScore.periode_fin <= today,
            KpiScore.score_total != None
        )
        
        # Apply filters
        if zone:
            query = query.join(User).filter(User.zone == zone)
        
        if equipe_id:
            query = query.filter(KpiScore.equipe_id == equipe_id)
        
        # Apply sorting
        if sort_by == 'tendance':
            query = query.order_by(KpiScore.tendance.desc())
        elif sort_by == 'anomalie':
            query = query.order_by(KpiScore.anomalie_detectee.desc())
        else:  # score (default)
            query = query.order_by(KpiScore.score_total.desc())
        
        results = query.limit(limit).all()
        logger.info(f"✅ Retrieved {len(results)} KPI scores for period={period}, zone={zone}")
        return results
        
    except Exception as e:
        logger.error(f"❌ Error fetching KPI scores: {str(e)}")
        return []


def get_active_alerts(unresolved_only=True):
    """
    Fetch active KPI alerts.
    
    Args:
        unresolved_only (bool): If True, only unresolved alerts
        
    Returns:
        list: KpiAlerte objects
    """
    try:
        query = KpiAlerte.query
        
        if unresolved_only:
            query = query.filter(KpiAlerte.date_resolution == None)
        
        alerts = query.order_by(KpiAlerte.date_creation.desc()).all()
        logger.info(f"✅ Retrieved {len(alerts)} active alerts")
        return alerts
        
    except Exception as e:
        logger.error(f"❌ Error fetching alerts: {str(e)}")
        return []


def calculate_kpi_stats(scores=None, period='day', zone=None):
    """
    Calculate aggregate KPI statistics.
    
    Args:
        scores (list): Optional pre-fetched KpiScore list (for efficiency)
        period (str): 'day', 'week', 'month', 'year'
        zone (str): Optional zone filter
        
    Returns:
        dict: Stats including avg_score, min/max, anomalies count, etc.
    """
    try:
        # Fetch scores if not provided
        if scores is None:
            scores = get_kpi_scores_by_period(period=period, zone=zone, limit=1000)
        
        if not scores:
            return {
                'total_scores': 0,
                'avg_score': 0,
                'min_score': 0,
                'max_score': 0,
                'anomalies_count': 0,
                'alerts_count': 0,
                'teams_count': 0,
                'period': period,
                'zone': zone
            }
        
        # Calculate stats
        total = len(scores)
        scores_list = [s.score_total for s in scores if s.score_total is not None]
        avg_score = sum(scores_list) / len(scores_list) if scores_list else 0
        min_score = min(scores_list) if scores_list else 0
        max_score = max(scores_list) if scores_list else 0
        
        anomalies_count = sum(1 for s in scores if s.anomalie_detectee)
        alerts_count = sum(1 for s in scores if s.alerte_active)
        
        # Count unique teams
        teams = set(s.equipe_id for s in scores if s.equipe_id)
        teams_count = len(teams)
        
        stats = {
            'total_scores': total,
            'avg_score': round(avg_score, 2),
            'min_score': round(min_score, 2),
            'max_score': round(max_score, 2),
            'anomalies_count': anomalies_count,
            'alerts_count': alerts_count,
            'teams_count': teams_count,
            'period': period,
            'zone': zone
        }
        
        logger.info(f"✅ Calculated stats: avg={stats['avg_score']}, anomalies={anomalies_count}")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error calculating KPI stats: {str(e)}")
        return {}


def get_kpi_score_detail(score_id):
    """
    Fetch detailed KPI score with related data.
    
    Args:
        score_id (int): KpiScore ID
        
    Returns:
        dict: Score details with technicien, equipe, etc.
    """
    try:
        score = KpiScore.query.get(score_id)
        if not score:
            return None
        
        technicien = db.session.get(User, score.technicien_id)
        equipe = db.session.get(Equipe, score.equipe_id) if score.equipe_id else None
        
        return {
            'score': score,
            'technicien': technicien,
            'equipe': equipe,
            'period': f"{score.periode_debut} à {score.periode_fin}",
            'has_alert': score.alerte_active,
            'has_anomaly': score.anomalie_detectee
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching KPI score detail: {str(e)}")
        return None


def export_kpi_scores_to_dict(scores, format='dict'):
    """
    Convert KpiScore objects to exportable format.
    
    Args:
        scores (list): KpiScore objects
        format (str): 'dict' or 'csv_rows'
        
    Returns:
        list: Formatted data ready for export
    """
    try:
        exported = []
        
        for score in scores:
            technicien = db.session.get(User, score.technicien_id)
            equipe = db.session.get(Equipe, score.equipe_id) if score.equipe_id else None
            
            if format == 'csv_rows':
                row = [
                    f"{technicien.prenom} {technicien.nom}" if technicien else "N/A",
                    equipe.nom_equipe if equipe else "N/A",
                    f"{score.periode_debut} à {score.periode_fin}",
                    round(score.score_total, 2) if score.score_total else "",
                    round(score.score_resolution_1ere_visite, 1) if score.score_resolution_1ere_visite else "",
                    round(score.score_respect_sla, 1) if score.score_respect_sla else "",
                    round(score.score_qualite_rapports, 1) if score.score_qualite_rapports else "",
                    round(score.score_satisfaction_client, 1) if score.score_satisfaction_client else "",
                    round(score.score_consommation_stock, 1) if score.score_consommation_stock else "",
                    score.rang_equipe or "",
                    score.rang_global or "",
                    score.tendance or "",
                    round(score.variation_periode_precedente, 1) if score.variation_periode_precedente else "",
                    "🚨 ALERTE" if score.alerte_active else "✅ OK"
                ]
                exported.append(row)
            else:  # dict
                item = {
                    'technicien': f"{technicien.prenom} {technicien.nom}" if technicien else "N/A",
                    'zone': technicien.zone if technicien else "N/A",
                    'equipe': equipe.nom_equipe if equipe else "N/A",
                    'score_total': round(score.score_total, 2) if score.score_total else None,
                    'resolution_1ere_visite': round(score.score_resolution_1ere_visite, 1) if score.score_resolution_1ere_visite else None,
                    'sla': round(score.score_respect_sla, 1) if score.score_respect_sla else None,
                    'qualite': round(score.score_qualite_rapports, 1) if score.score_qualite_rapports else None,
                    'satisfaction': round(score.score_satisfaction_client, 1) if score.score_satisfaction_client else None,
                    'stock': round(score.score_consommation_stock, 1) if score.score_consommation_stock else None,
                    'rang_equipe': score.rang_equipe,
                    'rang_global': score.rang_global,
                    'tendance': score.tendance,
                    'variation': round(score.variation_periode_precedente, 1) if score.variation_periode_precedente else None,
                    'statut': 'ALERTE' if score.alerte_active else 'OK'
                }
                exported.append(item)
        
        logger.info(f"✅ Exported {len(exported)} KPI scores to {format}")
        return exported
        
    except Exception as e:
        logger.error(f"❌ Error exporting KPI scores: {str(e)}")
        return []


def get_performance_data_with_fallback(zone=None):
    """
    Enhanced get_performance_data with KPI source + graceful fallback.
    
    This wraps the main get_performance_data() with error handling.
    If KPI system fails, falls back to simple Intervention-based calculation.
    
    Args:
        zone (str): Optional zone filter
        
    Returns:
        dict: Performance data (same format as original)
    """
    try:
        # Try to use KPI system directly (NOT via utils.get_performance_data - would cause recursion!)
        today = date.today()
        equipes_data = []
        
        # Query KPI scores for today
        equipes_query = Equipe.query.filter_by(actif=True)
        if zone:
            equipes_query = equipes_query.filter_by(zone=zone)
        
        for equipe in equipes_query.all():
            members = MembreEquipe.query.filter_by(equipe_id=equipe.id).all()
            member_ids = [m.technicien_id for m in members if m.technicien_id]
            
            if not member_ids:
                continue
            
            # Get today's KPI scores for this team
            kpi_scores = KpiScore.query.filter(
                KpiScore.technicien_id.in_(member_ids),
                KpiScore.periode_fin == today,
                KpiScore.score_total != None
            ).all()
            
            if kpi_scores:
                avg_score = sum(s.score_total for s in kpi_scores) / len(kpi_scores)
                taux = avg_score  # KPI score is already 0-100
            else:
                avg_score = 0
                taux = 0
            
            total_int = sum(
                s.details_json.get('total', 0) 
                for s in kpi_scores 
                if s.details_json
            ) if kpi_scores else 0
            
            equipes_data.append({
                'nom_equipe': equipe.nom_equipe,
                'prestataire': equipe.prestataire or '',
                'zone': equipe.zone,
                'technologies': equipe.technologies,
                'interventions_realisees': total_int,
                'taux_reussite': round(taux, 1),
                'kpi_score': round(avg_score, 2)
            })
        
        # Similar queries for techniciens, zones, pilots
        techniciens_query = User.query.filter_by(role='technicien', actif=True)
        if zone:
            techniciens_query = techniciens_query.filter_by(zone=zone)
        
        techniciens_data = []
        for tech in techniciens_query.all():
            kpi_score = KpiScore.query.filter(
                KpiScore.technicien_id == tech.id,
                KpiScore.periode_fin == today,
                KpiScore.score_total != None
            ).order_by(KpiScore.date_calcul.desc()).first()
            
            if not kpi_score:
                continue
            
            techniciens_data.append({
                'id': tech.id,
                'nom': tech.nom,
                'prenom': tech.prenom,
                'zone': tech.zone,
                'technologies': tech.technologies,
                'interventions_realisees': kpi_score.details_json.get('total', 0) if kpi_score.details_json else 0,
                'taux_reussite': round(kpi_score.score_resolution_1ere_visite, 1),
                'kpi_score_total': round(kpi_score.score_total, 2)
            })
        
        # Zones and pilots
        zones_data = []
        zone_list = db.session.query(Equipe.zone).distinct().filter_by(actif=True).all()
        for z in zone_list:
            zone_name = z[0]
            zones_data.append({'name': zone_name, 'created': 0, 'published': 0})
        
        pilots_data = []
        service_list = db.session.query(Equipe.service).distinct().filter_by(actif=True).all()
        for s in service_list:
            pilots_data.append({'name': s[0], 'service': s[0], 'imported': 0, 'dispatched': 0, 'validated': 0})
        
        data = {
            'equipes': equipes_data,
            'techniciens': techniciens_data,
            'zones': zones_data,
            'pilots': pilots_data
        }
        logger.info(f"✅ get_performance_data() succeeded (KPI-sourced)")
        return data
        
    except Exception as e:
        logger.warning(f"⚠️  KPI system failed, falling back to simple calculation: {str(e)}")
        
        try:
            # Fallback: simple Intervention-based calculation
            equipes_data = []
            equipes_query = Equipe.query.filter_by(actif=True)
            if zone:
                equipes_query = equipes_query.filter_by(zone=zone)
            
            for equipe in equipes_query.all():
                total = Intervention.query.filter_by(equipe_id=equipe.id).count()
                success = Intervention.query.filter_by(equipe_id=equipe.id, statut='valide').count()
                taux = (success / total * 100) if total > 0 else 0
                
                equipes_data.append({
                    'nom_equipe': equipe.nom_equipe,
                    'prestataire': equipe.prestataire or '',
                    'zone': equipe.zone,
                    'technologies': equipe.technologies,
                    'interventions_realisees': total,
                    'taux_reussite': round(taux, 1)
                })
            
            # Similar for techniciens, zones, pilots...
            logger.info(f"✅ Fallback calculation succeeded (simple-sourced)")
            
            return {
                'equipes': equipes_data,
                'techniciens': [],
                'zones': [],
                'pilots': [],
                '_fallback_used': True
            }
            
        except Exception as fallback_e:
            logger.error(f"❌ Both KPI and fallback systems failed: {str(fallback_e)}")
            return {
                'equipes': [],
                'techniciens': [],
                'zones': [],
                'pilots': [],
                '_error': str(fallback_e)
            }
