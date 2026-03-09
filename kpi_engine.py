"""
KPI Scoring Engine - Calcul des scores et métriques de performance
"""

from datetime import datetime, timedelta, timezone, date
from flask import current_app
from extensions import db
from models import User, DemandeIntervention, Intervention, Equipe, MembreEquipe
from kpi_models import KpiScore, KpiMetric, KpiAlerte, KpiHistorique, KpiObjectif
import json
import logging

logger = logging.getLogger(__name__)


class KpiScoringEngine:
    """Moteur de calcul des scores KPI avec pondérations configurables"""
    
    # Poids par défaut (%)
    WEIGHTS = {
        'resolution_1ere_visite': 0.30,    # 30%
        'respect_sla': 0.25,               # 25%
        'qualite_rapports': 0.20,          # 20%
        'satisfaction_client': 0.15,       # 15%
        'consommation_stock': 0.10         # 10%
    }
    
    def __init__(self, technicien_id, period_start, period_end):
        """Initialise le moteur pour un technicien et une période"""
        self.technicien_id = technicien_id
        self.period_start = period_start
        self.period_end = period_end
        self.technicien = User.query.get(technicien_id)
        
        if not self.technicien:
            raise ValueError(f"Technicien {technicien_id} not found")
    
    def calculate_resolution_1ere_visite(self):
        """
        Taux de résolution à la 1ère visite
        = (interventions résolues en 1 visite / total interventions) * 100
        Score: 100% si >= 80%, linéaire sinon
        """
        total = Intervention.query.filter(
            Intervention.technicien_id == self.technicien_id,
            Intervention.date_debut >= self.period_start,
            Intervention.date_debut <= self.period_end,
            Intervention.statut.in_(['termine', 'valide'])
        ).count()
        
        if total == 0:
            return 0.0, {'total': 0, 'resolved_first_visit': 0, 'rate': 0}
        
        # Interventions résolues en une seule visite
        resolved_first_visit = Intervention.query.filter(
            Intervention.technicien_id == self.technicien_id,
            Intervention.date_debut >= self.period_start,
            Intervention.date_debut <= self.period_end,
            Intervention.statut.in_(['termine', 'valide']),
            Intervention.nombre_visites == 1
        ).count()
        
        rate = (resolved_first_visit / total * 100) if total > 0 else 0
        
        # Scoring: 100 si >= 80%, sinon linéaire
        score = min(100, (rate / 80) * 100) if rate <= 80 else 100
        
        return round(score, 2), {
            'total': total,
            'resolved_first_visit': resolved_first_visit,
            'rate': round(rate, 2),
            'threshold': 80
        }
    
    def calculate_respect_sla(self):
        """
        Respect des SLA
        = (interventions dans les SLA / total interventions) * 100
        """
        from sla_utils import check_intervention_sla_violation
        
        interventions = Intervention.query.filter(
            Intervention.technicien_id == self.technicien_id,
            Intervention.date_debut >= self.period_start,
            Intervention.date_debut <= self.period_end,
            Intervention.statut.in_(['termine', 'valide'])
        ).all()
        
        if not interventions:
            return 0.0, {'total': 0, 'respected': 0, 'rate': 0}
        
        respected = 0
        for intervention in interventions:
            violation = check_intervention_sla_violation(intervention)
            if not violation:
                respected += 1
        
        rate = (respected / len(interventions) * 100)
        score = min(100, (rate / 95) * 100) if rate <= 95 else 100
        
        return round(score, 2), {
            'total': len(interventions),
            'respected': respected,
            'violated': len(interventions) - respected,
            'rate': round(rate, 2),
            'threshold': 95
        }
    
    def calculate_qualite_rapports(self):
        """
        Qualité des rapports (intervention)
        Critères:
        - Rapport complet (> 150 caractères)
        - Sans fautes (pas de pattern de faute)
        - Avec solution détaillée
        """
        interventions = Intervention.query.filter(
            Intervention.technicien_id == self.technicien_id,
            Intervention.date_debut >= self.period_start,
            Intervention.date_debut <= self.period_end,
            Intervention.statut.in_(['termine', 'valide'])
        ).all()
        
        if not interventions:
            return 0.0, {'total': 0, 'quality_good': 0, 'rate': 0}
        
        quality_good = 0
        for intervention in interventions:
            rapport = intervention.rapport or ""
            
            # Critères de qualité
            has_content = len(rapport.strip()) > 150
            has_solution = any(keyword in rapport.lower() for keyword in [
                'résolu', 'solution', 'réparation', 'correction', 'remplacé'
            ])
            
            if has_content and has_solution:
                quality_good += 1
        
        rate = (quality_good / len(interventions) * 100)
        score = min(100, (rate / 85) * 100) if rate <= 85 else 100
        
        return round(score, 2), {
            'total': len(interventions),
            'quality_good': quality_good,
            'rate': round(rate, 2),
            'threshold': 85
        }
    
    def calculate_satisfaction_client(self):
        """
        Satisfaction client (moyenne des ratings si disponibles)
        Fallback: estimation basée sur résolution et SLA
        """
        interventions = Intervention.query.filter(
            Intervention.technicien_id == self.technicien_id,
            Intervention.date_debut >= self.period_start,
            Intervention.date_debut <= self.period_end,
            Intervention.statut.in_(['termine', 'valide'])
        ).all()
        
        if not interventions:
            return 0.0, {'total': 0, 'average_rating': 0, 'feedback_count': 0}
        
        # Essayer de trouver des ratings
        ratings = []
        feedback_count = 0
        
        for intervention in interventions:
            if hasattr(intervention, 'client_feedback_rating') and intervention.client_feedback_rating:
                ratings.append(intervention.client_feedback_rating)
                feedback_count += 1
        
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            # Converter sur 100
            satisfaction_score = (avg_rating / 5.0) * 100
        else:
            # Fallback: basé sur résolution + SLA
            from sla_utils import check_intervention_sla_violation
            
            resolved = sum(1 for i in interventions if i.nombre_visites == 1)
            sla_respected = sum(1 for i in interventions if not check_intervention_sla_violation(i))
            
            satisfaction_score = ((resolved / len(interventions) * 0.5) + 
                                (sla_respected / len(interventions) * 0.5)) * 100
        
        return round(satisfaction_score, 2), {
            'total': len(interventions),
            'average_rating': round(sum(ratings) / len(ratings), 2) if ratings else None,
            'feedback_count': feedback_count,
            'calculated_from': 'ratings' if ratings else 'resolution_and_sla'
        }
    
    def calculate_consommation_stock(self):
        """
        Consommation de stock vs budget
        Score élevé = consommation maîtrisée
        Basé sur les réservations de pièces
        """
        from models import StockPiece, ReservationPiece
        
        # Récupérer les consommations de ce technicien sur la période
        consommations = db.session.query(
            ReservationPiece.quantite,
            StockPiece.prix_unitaire
        ).filter(
            ReservationPiece.technicien_id == self.technicien_id,
            ReservationPiece.date_reservation >= self.period_start,
            ReservationPiece.date_reservation <= self.period_end
        ).all()
        
        if not consommations:
            return 100.0, {'total_cost': 0, 'budget': 0, 'efficiency': 100}
        
        total_cost = sum(qty * (price or 0) for qty, price in consommations)
        
        # Budget mensuel par technicien (estimé à 1000€)
        monthly_budget = 1000
        days_in_period = (self.period_end - self.period_start).days + 1
        budget_allocated = monthly_budget * (days_in_period / 30)
        
        if total_cost == 0:
            efficiency = 100
        elif total_cost <= budget_allocated:
            efficiency = 100
        else:
            # Pénalité progressive pour dépassement
            overage_percent = ((total_cost - budget_allocated) / budget_allocated) * 100
            efficiency = max(0, 100 - min(50, overage_percent))
        
        return round(efficiency, 2), {
            'total_cost': round(total_cost, 2),
            'budget_allocated': round(budget_allocated, 2),
            'efficiency_rate': round(efficiency, 2)
        }
    
    def detect_anomalies(self):
        """Détecte les anomalies de performance"""
        anomalies = []
        
        # Récupérer le score de la période précédente
        period_duration = (self.period_end - self.period_start).days
        prev_period_start = self.period_start - timedelta(days=period_duration)
        prev_period_end = self.period_start - timedelta(days=1)
        
        try:
            prev_score = KpiScore.query.filter_by(
                technicien_id=self.technicien_id,
                periode_debut=prev_period_start.date(),
                periode_fin=prev_period_end.date()
            ).first()
            
            if prev_score and hasattr(prev_score, 'score_total') and prev_score.score_total:
                current_total = getattr(self, 'score_total', None)
                if current_total and (prev_score.score_total - current_total) > 15:
                    anomalies.append({
                        'type': 'chute_performance',
                        'severity': 'high',
                        'description': f"Chute de {round(prev_score.score_total - current_total, 2)} points",
                        'previous_score': prev_score.score_total,
                        'current_score': current_total
                    })
        except Exception as e:
            logger.warning(f"Could not detect anomalies: {e}")
        
        return anomalies
    
    def calculate_all_scores(self):
        """Calcule tous les scores"""
        scores = {}
        details = {}
        
        # Calculer chaque métrique
        score_1ere, details_1ere = self.calculate_resolution_1ere_visite()
        scores['resolution_1ere_visite'] = score_1ere
        details['resolution_1ere_visite'] = details_1ere
        
        score_sla, details_sla = self.calculate_respect_sla()
        scores['respect_sla'] = score_sla
        details['respect_sla'] = details_sla
        
        score_qualite, details_qualite = self.calculate_qualite_rapports()
        scores['qualite_rapports'] = score_qualite
        details['qualite_rapports'] = details_qualite
        
        score_satisfaction, details_satisfaction = self.calculate_satisfaction_client()
        scores['satisfaction_client'] = score_satisfaction
        details['satisfaction_client'] = details_satisfaction
        
        score_stock, details_stock = self.calculate_consommation_stock()
        scores['consommation_stock'] = score_stock
        details['consommation_stock'] = details_stock
        
        # Calculer le score total pondéré
        total_score = sum(scores[key] * self.WEIGHTS[key] for key in scores)
        total_score = min(100, max(0, total_score))
        
        return {
            'score_total': round(total_score, 2),
            'scores': {f'score_{k}': v for k, v in scores.items()},
            'details': details,
            'anomalies': self.detect_anomalies()
        }


def calculate_daily_kpi(date=None):
    """
    Cron job: Calcule les KPI pour tous les techniciens au quotidien
    Crée un enregistrement KpiHistorique par technicien/jour
    """
    if date is None:
        date = datetime.now(timezone.utc).date()
    
    logger.info(f"Starting daily KPI calculation for {date}")
    
    # Calculer pour les 30 derniers jours (sliding window)
    period_start = date - timedelta(days=30)
    period_end = date
    
    # Techniciens actifs
    technicians = User.query.filter_by(role='technicien', actif=True).all()
    
    for tech in technicians:
        try:
            engine = KpiScoringEngine(tech.id, period_start, period_end)
            result = engine.calculate_all_scores()
            
            # Créer enregistrement historique
            history = KpiHistorique(
                technicien_id=tech.id,
                date=date,
                score_total=result['score_total'],
                score_resolution_1ere_visite=result['scores'].get('score_resolution_1ere_visite'),
                score_respect_sla=result['scores'].get('score_respect_sla'),
                score_qualite_rapports=result['scores'].get('score_qualite_rapports'),
                score_satisfaction_client=result['scores'].get('score_satisfaction_client'),
                score_consommation_stock=result['scores'].get('score_consommation_stock')
            )
            
            db.session.add(history)
            
            # Déterminer les alertes
            check_and_create_alerts(tech.id, result)
            
        except Exception as e:
            logger.error(f"Error calculating KPI for technicien {tech.id}: {e}")
    
    db.session.commit()
    logger.info(f"Daily KPI calculation completed for {date}")


def calculate_monthly_kpi(technicien_id, year, month):
    """
    Calcule les KPI mensuels pour un technicien
    Crée un enregistrement KpiScore
    """
    from calendar import monthrange
    
    days_in_month = monthrange(year, month)[1]
    period_start = date(year, month, 1)
    period_end = date(year, month, days_in_month)
    
    engine = KpiScoringEngine(technicien_id, period_start, period_end)
    result = engine.calculate_all_scores()
    
    # Déterminer l'équipe du technicien
    membre = MembreEquipe.query.filter_by(
        technicien_id=technicien_id,
        type_membre='technicien'
    ).first()
    equipe_id = membre.equipe_id if membre else None
    
    # Créer/mettre à jour le score mensuel
    existing_score = KpiScore.query.filter_by(
        technicien_id=technicien_id,
        periode_debut=period_start,
        periode_fin=period_end
    ).first()
    
    if existing_score:
        kpi_score = existing_score
    else:
        kpi_score = KpiScore(
            technicien_id=technicien_id,
            equipe_id=equipe_id,
            periode_debut=period_start,
            periode_fin=period_end,
            periode_type='monthly'
        )
        db.session.add(kpi_score)
    
    # Mettre à jour les scores
    kpi_score.score_total = result['score_total']
    kpi_score.score_resolution_1ere_visite = result['scores'].get('score_resolution_1ere_visite')
    kpi_score.score_respect_sla = result['scores'].get('score_respect_sla')
    kpi_score.score_qualite_rapports = result['scores'].get('score_qualite_rapports')
    kpi_score.score_satisfaction_client = result['scores'].get('score_satisfaction_client')
    kpi_score.score_consommation_stock = result['scores'].get('score_consommation_stock')
    kpi_score.details_json = result['details']
    
    # Déterminer la tendance
    determine_trend_and_ranking(kpi_score)
    
    # Vérifier les seuils d'alerte
    check_and_create_alerts(technicien_id, result, kpi_score)
    
    db.session.commit()
    return kpi_score


def determine_trend_and_ranking(kpi_score):
    """Détermine la tendance et le classement du score"""
    
    # Récupérer le score de la période précédente
    from dateutil.relativedelta import relativedelta
    
    prev_start = kpi_score.periode_debut - relativedelta(months=1)
    prev_end = kpi_score.periode_fin - relativedelta(months=1)
    
    prev_score = KpiScore.query.filter_by(
        technicien_id=kpi_score.technicien_id,
        periode_debut=prev_start,
        periode_fin=prev_end
    ).first()
    
    if prev_score and prev_score.score_total:
        variation = kpi_score.score_total - prev_score.score_total
        kpi_score.variation_periode_precedente = variation
        
        if variation > 2:
            kpi_score.tendance = 'hausse'
        elif variation < -2:
            kpi_score.tendance = 'baisse'
        else:
            kpi_score.tendance = 'stable'
    else:
        kpi_score.tendance = 'nouveau'
    
    # Classement dans l'équipe
    if kpi_score.equipe_id:
        team_scores = KpiScore.query.filter(
            KpiScore.equipe_id == kpi_score.equipe_id,
            KpiScore.periode_debut == kpi_score.periode_debut,
            KpiScore.score_total != None
        ).order_by(KpiScore.score_total.desc()).all()
        
        for i, score in enumerate(team_scores, 1):
            if score.id == kpi_score.id:
                kpi_score.rang_equipe = i
                break
    
    # Classement global
    global_scores = KpiScore.query.filter(
        KpiScore.periode_debut == kpi_score.periode_debut,
        KpiScore.score_total != None
    ).order_by(KpiScore.score_total.desc()).all()
    
    for i, score in enumerate(global_scores, 1):
        if score.id == kpi_score.id:
            kpi_score.rang_global = i
            break


def check_and_create_alerts(technicien_id, result, kpi_score=None):
    """Crée les alertes intelligentes basées sur les seuils"""
    
    tech = User.query.get(technicien_id)
    if not tech:
        return
    
    # Récupérer les objectifs du technicien
    objectifs = KpiObjectif.query.filter_by(
        technicien_id=technicien_id,
        annee=datetime.now().year
    ).first()
    
    if not objectifs:
        return  # Pas d'objectifs configurés
    
    # Vérifier chaque métrique
    metrics_to_check = [
        ('resolution_1ere_visite', 'objectif_resolution_1ere_visite', 'Résolution 1ère visite'),
        ('respect_sla', 'objectif_respect_sla', 'Respect SLA'),
        ('qualite_rapports', 'objectif_qualite_rapports', 'Qualité rapports'),
        ('satisfaction_client', 'objectif_satisfaction_client', 'Satisfaction client'),
        ('consommation_stock', 'objectif_consommation_stock', 'Consommation stock')
    ]
    
    for metric_key, objectif_attr, metric_name in metrics_to_check:
        score_key = f'score_{metric_key}'
        if score_key in result['scores']:
            actual_score = result['scores'][score_key]
            objectif_score = getattr(objectifs, objectif_attr, 75)
            
            if actual_score < objectif_score:
                # Créer une alerte
                alerte = KpiAlerte(
                    technicien_id=technicien_id,
                    kpi_score_id=kpi_score.id if kpi_score else None,
                    type_alerte='seuil',
                    metrique=metric_key,
                    severite='eleve' if actual_score < (objectif_score * 0.8) else 'moyen',
                    titre=f"Métrique sous objectif: {metric_name}",
                    description=f"{metric_name} = {actual_score:.2f}% (objectif: {objectif_score}%)",
                    valeur_actuelle=actual_score,
                    valeur_seuil=objectif_score,
                    recommandations=generate_recommendations(metric_key, actual_score),
                    active=True
                )
                
                db.session.add(alerte)
    
    # Vérifier les anomalies
    for anomaly in result.get('anomalies', []):
        alerte = KpiAlerte(
            technicien_id=technicien_id,
            kpi_score_id=kpi_score.id if kpi_score else None,
            type_alerte='anomalie',
            severite='critique',
            titre=f"Anomalie détectée: {anomaly.get('description')}",
            description=anomaly.get('description'),
            active=True,
            recommandations=['Examiner les changements récents', 'Vérifier la charge de travail', 'Consulter le manager']
        )
        
        db.session.add(alerte)
    
    db.session.commit()


def generate_recommendations(metric_key, actual_score):
    """Génère des recommandations d'amélioration basées sur la métrique"""
    
    recommendations_map = {
        'resolution_1ere_visite': [
            'Améliorer le diagnostic initial',
            'Vérifier l\'équipement apporté',
            'Renforcer la formation technique',
            'Consulter les clients avant de partir'
        ],
        'respect_sla': [
            'Optimiser les trajets',
            'Réduire le temps d\'intervention',
            'Améliorer la planification',
            'Communiquer les délais aux clients'
        ],
        'qualite_rapports': [
            'Documenter plus complètement les interventions',
            'Améliorer la clarté des rapports',
            'Détailler les solutions apportées',
            'Réviser les rapports avant soumission'
        ],
        'satisfaction_client': [
            'Améliorer la communication client',
            'Vérifier la satisfaction avant départ',
            'Traiter les problèmes complètement',
            'Proposer des solutions préventives'
        ],
        'consommation_stock': [
            'Optimiser la consommation de pièces',
            'Prévenir les gaspillages',
            'Utiliser les bonnes pièces',
            'Planifier les stocks nécessaires'
        ]
    }
    
    return recommendations_map.get(metric_key, ['Améliorer les performances'])
