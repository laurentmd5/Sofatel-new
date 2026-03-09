"""
KPI Scoring System Models - Performance metrics and scoring for SOFATELCOM
"""

from extensions import db
from datetime import datetime, timezone
import json


class KpiMetric(db.Model):
    """
    Définition d'une métrique KPI avec ses paramètres de calcul
    """
    __tablename__ = 'kpi_metric'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)  # e.g., "first_visit_resolution"
    description = db.Column(db.String(500))
    poids = db.Column(db.Float, default=1.0)  # Poids dans le scoring (%)
    seuil_min = db.Column(db.Float, default=0.0)  # Seuil minimum acceptable
    seuil_max = db.Column(db.Float, default=100.0)  # Seuil maximum
    seuil_alerte = db.Column(db.Float)  # Seuil déclenchant une alerte
    formule = db.Column(db.String(500))  # Description de la formule de calcul
    unite = db.Column(db.String(50), default='%')  # Unité (%, heures, nombre, etc.)
    actif = db.Column(db.Boolean, default=True)
    date_creation = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    date_modification = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<KpiMetric {self.nom}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'description': self.description,
            'poids': self.poids,
            'seuil_min': self.seuil_min,
            'seuil_max': self.seuil_max,
            'seuil_alerte': self.seuil_alerte,
            'unite': self.unite,
            'actif': self.actif
        }


class KpiScore(db.Model):
    """
    Score KPI global pour un technicien sur une période donnée
    """
    __tablename__ = 'kpi_score'
    
    id = db.Column(db.Integer, primary_key=True)
    technicien_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    equipe_id = db.Column(db.Integer, db.ForeignKey('equipe.id'))
    
    # Période
    periode_debut = db.Column(db.Date, nullable=False)
    periode_fin = db.Column(db.Date, nullable=False)
    periode_type = db.Column(db.String(20), default='monthly')  # daily, weekly, monthly, annual
    
    # Scores
    score_total = db.Column(db.Float)  # Score global pondéré (0-100)
    score_resolution_1ere_visite = db.Column(db.Float)  # 30%
    score_respect_sla = db.Column(db.Float)  # 25%
    score_qualite_rapports = db.Column(db.Float)  # 20%
    score_satisfaction_client = db.Column(db.Float)  # 15%
    score_consommation_stock = db.Column(db.Float)  # 10%
    
    # Détails bruts
    details_json = db.Column(db.JSON)  # Détails de calcul complets
    
    # Classement
    rang_equipe = db.Column(db.Integer)  # Classement dans l'équipe
    rang_global = db.Column(db.Integer)  # Classement global
    tendance = db.Column(db.String(20))  # 'stable', 'hausse', 'baisse'
    variation_periode_precedente = db.Column(db.Float)  # % de variation
    
    # État
    alerte_active = db.Column(db.Boolean, default=False)
    anomalie_detectee = db.Column(db.Boolean, default=False)
    
    # Audit
    date_calcul = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    date_modification = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))
    calcule_par = db.Column(db.String(100), default='system')  # system ou user_id
    
    # Relations
    technicien = db.relationship('User', backref='kpi_scores', foreign_keys=[technicien_id])
    equipe = db.relationship('Equipe', backref='kpi_scores', foreign_keys=[equipe_id])
    alertes = db.relationship('KpiAlerte', back_populates='kpi_score', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<KpiScore tech={self.technicien_id} {self.periode_debut}>"
    
    def to_dict(self, include_details=True):
        data = {
            'id': self.id,
            'technicien_id': self.technicien_id,
            'technicien_nom': f"{self.technicien.prenom} {self.technicien.nom}" if self.technicien else None,
            'equipe_id': self.equipe_id,
            'equipe_nom': self.equipe.nom_equipe if self.equipe else None,
            'periode': {
                'debut': self.periode_debut.isoformat(),
                'fin': self.periode_fin.isoformat(),
                'type': self.periode_type
            },
            'scores': {
                'total': round(self.score_total, 2) if self.score_total else None,
                'resolution_1ere_visite': round(self.score_resolution_1ere_visite, 2) if self.score_resolution_1ere_visite else None,
                'respect_sla': round(self.score_respect_sla, 2) if self.score_respect_sla else None,
                'qualite_rapports': round(self.score_qualite_rapports, 2) if self.score_qualite_rapports else None,
                'satisfaction_client': round(self.score_satisfaction_client, 2) if self.score_satisfaction_client else None,
                'consommation_stock': round(self.score_consommation_stock, 2) if self.score_consommation_stock else None
            },
            'classement': {
                'rang_equipe': self.rang_equipe,
                'rang_global': self.rang_global,
                'tendance': self.tendance,
                'variation': round(self.variation_periode_precedente, 2) if self.variation_periode_precedente else None
            },
            'etat': {
                'alerte': self.alerte_active,
                'anomalie': self.anomalie_detectee
            },
            'date_calcul': self.date_calcul.isoformat() if self.date_calcul else None
        }
        
        if include_details and self.details_json:
            data['details'] = self.details_json
        
        return data
    
    def calculate_total_score(self):
        """Calcule le score total pondéré"""
        weights = {
            'resolution_1ere_visite': 0.30,
            'respect_sla': 0.25,
            'qualite_rapports': 0.20,
            'satisfaction_client': 0.15,
            'consommation_stock': 0.10
        }
        
        total = 0
        for key, weight in weights.items():
            attr_name = f'score_{key}'
            score = getattr(self, attr_name, None)
            if score is not None:
                total += score * weight
        
        self.score_total = min(100, max(0, total))
        return self.score_total


class KpiObjectif(db.Model):
    """
    Objectifs personnalisés par technicien
    """
    __tablename__ = 'kpi_objectif'
    
    id = db.Column(db.Integer, primary_key=True)
    technicien_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Objectifs
    objectif_score_total = db.Column(db.Float, default=85.0)
    objectif_resolution_1ere_visite = db.Column(db.Float, default=80.0)
    objectif_respect_sla = db.Column(db.Float, default=90.0)
    objectif_qualite_rapports = db.Column(db.Float, default=85.0)
    objectif_satisfaction_client = db.Column(db.Float, default=80.0)
    objectif_consommation_stock = db.Column(db.Float, default=75.0)
    
    # Période de validité
    annee = db.Column(db.Integer, nullable=False)
    date_debut = db.Column(db.Date)
    date_fin = db.Column(db.Date)
    
    # Notes et observations
    remarques = db.Column(db.Text)
    
    # Audit
    date_creation = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    date_modification = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))
    modifie_par = db.Column(db.String(100))
    
    # Relations
    technicien = db.relationship('User', backref='kpi_objectifs', foreign_keys=[technicien_id])
    
    def __repr__(self):
        return f"<KpiObjectif tech={self.technicien_id} {self.annee}>"


class KpiAlerte(db.Model):
    """
    Alertes intelligentes basées sur les métriques KPI
    """
    __tablename__ = 'kpi_alerte'
    
    id = db.Column(db.Integer, primary_key=True)
    technicien_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    kpi_score_id = db.Column(db.Integer, db.ForeignKey('kpi_score.id'))
    
    # Type d'alerte
    type_alerte = db.Column(db.String(50), nullable=False)  # 'seuil', 'anomalie', 'tendance', 'chute'
    metrique = db.Column(db.String(100))
    severite = db.Column(db.String(20), default='moyen')  # 'faible', 'moyen', 'eleve', 'critique'
    
    # Détails
    titre = db.Column(db.String(255))
    description = db.Column(db.Text)
    valeur_actuelle = db.Column(db.Float)
    valeur_seuil = db.Column(db.Float)
    recommandations = db.Column(db.JSON)  # Liste de suggestions d'amélioration
    
    # État
    active = db.Column(db.Boolean, default=True)
    date_creation = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    date_resolution = db.Column(db.DateTime)
    resolu_par = db.Column(db.String(100))
    
    # Audit
    date_modification = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))
    
    # Relations
    technicien = db.relationship('User', backref='kpi_alertes', foreign_keys=[technicien_id])
    kpi_score = db.relationship('KpiScore', back_populates='alertes', foreign_keys=[kpi_score_id])
    
    def __repr__(self):
        return f"<KpiAlerte {self.type_alerte} tech={self.technicien_id}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'technicien_id': self.technicien_id,
            'type': self.type_alerte,
            'severite': self.severite,
            'titre': self.titre,
            'description': self.description,
            'metrique': self.metrique,
            'valeur_actuelle': self.valeur_actuelle,
            'valeur_seuil': self.valeur_seuil,
            'recommandations': self.recommandations,
            'active': self.active,
            'date_creation': self.date_creation.isoformat()
        }


class KpiHistorique(db.Model):
    """
    Historique complet des scores pour analyse de tendance
    """
    __tablename__ = 'kpi_historique'
    
    id = db.Column(db.Integer, primary_key=True)
    technicien_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Période
    date = db.Column(db.Date, nullable=False, index=True)
    
    # Scores
    score_total = db.Column(db.Float)
    score_resolution_1ere_visite = db.Column(db.Float)
    score_respect_sla = db.Column(db.Float)
    score_qualite_rapports = db.Column(db.Float)
    score_satisfaction_client = db.Column(db.Float)
    score_consommation_stock = db.Column(db.Float)
    
    # Contexte
    nombre_interventions = db.Column(db.Integer)
    nombre_sla_respectes = db.Column(db.Integer)
    nombre_sla_violes = db.Column(db.Integer)
    satisfaction_moyenne = db.Column(db.Float)
    
    # Relation
    technicien = db.relationship('User', backref='kpi_historique', foreign_keys=[technicien_id])
    
    def __repr__(self):
        return f"<KpiHistorique tech={self.technicien_id} {self.date}>"
