"""
Module d'Alertes Stock - Détection et notification des ruptures de stock
Système de ruptures avec seuils configurables par zone et produit
"""

from datetime import datetime, timezone, timedelta
from extensions import db
from sqlalchemy import Index, and_, or_
import logging
import enum

logger = logging.getLogger(__name__)


def utcnow():
    """Return timezone-aware UTC datetime"""
    return datetime.now(timezone.utc)


# ============================================================================
# ÉNUMÉRATION DES ÉTATS D'ALERTE
# ============================================================================

class AlertStatus(enum.Enum):
    """États possibles d'une alerte de stock"""
    PENDING = 'pending'          # Alerte créée, pas encore traitée
    ACKNOWLEDGED = 'acknowledged'  # Chef reconnaît l'alerte
    IN_PROGRESS = 'in_progress'    # Commande passée / restockage en cours
    RESOLVED = 'resolved'          # Rupture résolue
    CANCELLED = 'cancelled'        # Alerte annulée (fausse alerte)


class AlertSeverity(enum.Enum):
    """Niveau de sévérité d'une alerte"""
    LOW = 'low'          # Stock bas mais pas rupture
    MEDIUM = 'medium'    # Stock critique
    HIGH = 'high'        # Rupture imminente
    CRITICAL = 'critical'  # Rupture totale


# ============================================================================
# SEUILS DE RUPTURE - Configuration par zone et produit
# ============================================================================

class StockThreshold(db.Model):
    """
    Seuils d'alerte stock configurables par zone et produit
    Permet une gestion fine des alertes
    """
    __tablename__ = 'stock_threshold'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Ressource
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'), nullable=False, index=True)
    zone = db.relationship('Zone', backref=db.backref('stock_thresholds'))
    
    produit_id = db.Column(db.Integer, db.ForeignKey('produit.id'), nullable=False, index=True)
    produit = db.relationship('Produit', backref=db.backref('stock_thresholds'))
    
    # Seuils (en quantité)
    seuil_critique = db.Column(db.Integer, nullable=False)  # En-dessous = rupture critique
    seuil_alerte = db.Column(db.Integer, nullable=False)    # En-dessous = alerte
    seuil_recommande = db.Column(db.Integer, nullable=False)  # Stock recommandé (cible)
    
    # Configuration
    auto_reorder = db.Column(db.Boolean, default=True)  # Commande automatique au-dessous du seuil?
    auto_reorder_quantity = db.Column(db.Integer, nullable=True)  # Quantité commandée automatiquement
    
    # Audit
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    
    __table_args__ = (
        Index('idx_threshold_zone_produit', 'zone_id', 'produit_id', unique=True),
    )
    
    def __repr__(self):
        return f'<StockThreshold Zone:{self.zone_id} Produit:{self.produit_id}>'


# ============================================================================
# ALERTES DE RUPTURE
# ============================================================================

class StockAlert(db.Model):
    """
    Alerte de rupture ou stock bas
    Généré automatiquement quand stock descend sous les seuils
    """
    __tablename__ = 'stock_alert'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # ========== RESSOURCES CONCERNÉES ==========
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'), nullable=False, index=True)
    zone = db.relationship('Zone', backref=db.backref('stock_alerts'))
    
    produit_id = db.Column(db.Integer, db.ForeignKey('produit.id'), nullable=False, index=True)
    produit = db.relationship('Produit', backref=db.backref('stock_alerts'))
    
    emplacement_id = db.Column(db.Integer, db.ForeignKey('emplacement.id'), nullable=True)
    emplacement = db.relationship('Emplacement', backref=db.backref('stock_alerts'))
    
    # ========== DÉTAILS DE L'ALERTE ==========
    severity = db.Column(db.Enum(AlertSeverity), nullable=False, default=AlertSeverity.MEDIUM)
    status = db.Column(db.Enum(AlertStatus), nullable=False, default=AlertStatus.PENDING, index=True)
    
    current_quantity = db.Column(db.Integer, nullable=False)  # Quantité au moment de l'alerte
    seuil_trigger = db.Column(db.Integer, nullable=False)     # Seuil qui a déclenché l'alerte
    
    description = db.Column(db.String(255), nullable=False)
    reason = db.Column(db.String(100), nullable=True)  # Raison: rupture, perte, consommation rapide, etc.
    
    # ========== ACTIONS PRISES ==========
    acknowledged_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    acknowledged_by = db.relationship('User', foreign_keys=[acknowledged_by_id])
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    acknowledgement_notes = db.Column(db.Text, nullable=True)
    
    # Commande de restockage
    purchase_order_id = db.Column(db.Integer, nullable=True)  # Référence commande externe
    purchase_order_number = db.Column(db.String(50), nullable=True)
    purchase_order_date = db.Column(db.DateTime, nullable=True)
    
    # Résolution
    resolved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    resolved_by = db.relationship('User', foreign_keys=[resolved_by_id])
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)
    resolved_quantity = db.Column(db.Integer, nullable=True)  # Quantité reçue
    
    # ========== NOTIFICATIONS ==========
    notified = db.Column(db.Boolean, default=False)
    notified_at = db.Column(db.DateTime, nullable=True)
    notified_to = db.Column(db.JSON, nullable=True)  # Liste des destinataires notifiés
    
    # ========== HORODATAGE ==========
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    
    # ========== IMPACT ==========
    # Combien d'interventions/projets impactés?
    impacted_tasks_count = db.Column(db.Integer, default=0)
    can_delay_work = db.Column(db.Boolean, default=False)  # Peut impacter le délai de travail?
    
    __table_args__ = (
        Index('idx_alert_zone_date', 'zone_id', 'created_at'),
        Index('idx_alert_produit_date', 'produit_id', 'created_at'),
        Index('idx_alert_status', 'status'),
        Index('idx_alert_severity_status', 'severity', 'status'),
    )
    
    def is_active(self):
        """Alerte non résolue?"""
        return self.status in [AlertStatus.PENDING, AlertStatus.ACKNOWLEDGED, AlertStatus.IN_PROGRESS]
    
    def is_critical(self):
        """Alerte critique ou haute?"""
        return self.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]
    
    def get_display_name(self):
        """Nom lisible de l'alerte"""
        return f"Alerte {self.severity.value.upper()} - {self.produit.code}: {self.current_quantity} en stock"
    
    def __repr__(self):
        return f'<StockAlert Zone:{self.zone_id} Produit:{self.produit_id} Status:{self.status.value}>'


# ============================================================================
# RÈGLES D'ALERTE - Configurations de déclenchement
# ============================================================================

class AlertRule(db.Model):
    """
    Règles pour déclencher automatiquement les alertes
    Détermine quand et comment les alertes doivent être créées
    """
    __tablename__ = 'alert_rule'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identification
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # ========== CONDITIONS DE DÉCLENCHEMENT ==========
    # Si False, règle ne s'applique pas globalement
    enabled = db.Column(db.Boolean, default=True)
    
    # Zones concernées (vides = toutes)
    zones_json = db.Column(db.JSON, nullable=True)  # [zone_id, ...]
    
    # Produits concernés (vides = tous)
    produits_json = db.Column(db.JSON, nullable=True)  # [produit_id, ...]
    
    # ========== PARAMÈTRES D'ALERTE ==========
    # Qui notifier?
    notify_roles = db.Column(db.JSON, nullable=False)  # ['chef_pur', 'gestionnaire_stock', ...]
    notify_zone_chef = db.Column(db.Boolean, default=True)  # Notifier chef de zone?
    
    # Escalade?
    escalate_if_unacknowledged_hours = db.Column(db.Integer, nullable=True)  # Escalader après X heures?
    escalate_to_roles = db.Column(db.JSON, nullable=True)  # Rôles escalade
    
    # Actions automatiques?
    auto_create_purchase_order = db.Column(db.Boolean, default=False)
    auto_disable_sales = db.Column(db.Boolean, default=False)  # Désactiver vente?
    
    # ========== AUDIT ==========
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    updated_by = db.relationship('User', foreign_keys=[updated_by_id])
    
    def applies_to_zone(self, zone_id):
        """Vérifie si règle s'applique à une zone"""
        if not self.enabled:
            return False
        if not self.zones_json:
            return True  # S'applique à toutes les zones
        return zone_id in self.zones_json
    
    def applies_to_produit(self, produit_id):
        """Vérifie si règle s'applique à un produit"""
        if not self.enabled:
            return False
        if not self.produits_json:
            return True  # S'applique à tous les produits
        return produit_id in self.produits_json
    
    def __repr__(self):
        return f'<AlertRule {self.name}>'


# ============================================================================
# ALERTEUR - Service pour détecter et créer les alertes
# ============================================================================

class StockAlerter:
    """
    Service pour détecter les situations de rupture
    et créer les alertes appropriées
    """
    
    @staticmethod
    def check_and_create_alerts(stock, reason='stock_movement'):
        """
        Vérifie si un stock déclenche une alerte et la crée si nécessaire
        
        Args:
            stock: Objet Stock à vérifier
            reason: Raison du changement (stock_movement, consumption, etc.)
            
        Returns:
            StockAlert: Alerte créée si applicable, None sinon
        """
        # Récupérer les seuils de cette zone/produit
        threshold = StockThreshold.query.filter_by(
            zone_id=stock.zone_id,
            produit_id=stock.produit_id
        ).first()
        
        if not threshold:
            # Pas de seuil configuré, pas d'alerte
            return None
        
        # Déterminer la sévérité
        if stock.quantite <= 0:
            severity = AlertSeverity.CRITICAL
            seuil_trigger = threshold.seuil_critique
        elif stock.quantite <= threshold.seuil_critique:
            severity = AlertSeverity.HIGH
            seuil_trigger = threshold.seuil_critique
        elif stock.quantite <= threshold.seuil_alerte:
            severity = AlertSeverity.MEDIUM
            seuil_trigger = threshold.seuil_alerte
        else:
            # Stock au-dessus des seuils
            return None
        
        # Vérifier s'il existe déjà une alerte active
        existing_alert = StockAlert.query.filter(
            StockAlert.zone_id == stock.zone_id,
            StockAlert.produit_id == stock.produit_id,
            StockAlert.status.in_([AlertStatus.PENDING, AlertStatus.ACKNOWLEDGED, AlertStatus.IN_PROGRESS])
        ).first()
        
        if existing_alert:
            # Mettre à jour l'alerte existante
            existing_alert.current_quantity = stock.quantite
            existing_alert.updated_at = utcnow()
            if severity.value > existing_alert.severity.value:
                existing_alert.severity = severity
            db.session.commit()
            return existing_alert
        
        # Créer nouvelle alerte
        alert = StockAlert(
            zone_id=stock.zone_id,
            produit_id=stock.produit_id,
            emplacement_id=stock.emplacement_id,
            severity=severity,
            status=AlertStatus.PENDING,
            current_quantity=stock.quantite,
            seuil_trigger=seuil_trigger,
            description=f"Rupture détectée: {stock.produit.code}",
            reason=reason,
        )
        
        try:
            db.session.add(alert)
            db.session.commit()
            logger.info(f"Stock alert created: {alert}")
            
            # Notifier si applicable
            StockAlerter.notify_alert(alert)
            
            return alert
        except Exception as e:
            logger.error(f"Failed to create alert: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def acknowledge_alert(alert_id, notes=None, user=None):
        """
        Marque une alerte comme reconnue
        
        Args:
            alert_id: ID de l'alerte
            notes: Notes de reconnaissance
            user: Utilisateur qui reconnaît (par défaut current_user)
        """
        from flask_login import current_user
        
        if user is None:
            user = current_user
        
        alert = StockAlert.query.get(alert_id)
        if not alert:
            return False
        
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = user
        alert.acknowledged_at = utcnow()
        alert.acknowledgement_notes = notes
        alert.updated_at = utcnow()
        
        try:
            db.session.commit()
            logger.info(f"Alert {alert_id} acknowledged by {user.username}")
            return True
        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def resolve_alert(alert_id, received_quantity, notes=None, user=None):
        """
        Marque une alerte comme résolue
        
        Args:
            alert_id: ID de l'alerte
            received_quantity: Quantité reçue pour résoudre
            notes: Notes de résolution
            user: Utilisateur qui résout (par défaut current_user)
        """
        from flask_login import current_user
        
        if user is None:
            user = current_user
        
        alert = StockAlert.query.get(alert_id)
        if not alert:
            return False
        
        alert.status = AlertStatus.RESOLVED
        alert.resolved_by = user
        alert.resolved_at = utcnow()
        alert.resolved_quantity = received_quantity
        alert.resolution_notes = notes
        alert.updated_at = utcnow()
        
        try:
            db.session.commit()
            logger.info(f"Alert {alert_id} resolved by {user.username}")
            return True
        except Exception as e:
            logger.error(f"Failed to resolve alert: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def notify_alert(alert):
        """
        Notifie les utilisateurs appropriés d'une alerte
        
        Args:
            alert: Alerte à communiquer
        """
        # TODO: Intégrer avec système de notifications
        # Pour maintenant, juste enregistrer comme notifié
        alert.notified = True
        alert.notified_at = utcnow()
        
        try:
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to mark alert as notified: {str(e)}")
            db.session.rollback()
    
    @staticmethod
    def get_active_alerts(zone_id=None, severity=None):
        """
        Récupère les alertes actives
        
        Args:
            zone_id: Filtrer par zone (optionnel)
            severity: Filtrer par sévérité (optionnel)
            
        Returns:
            list: Alertes actives
        """
        query = StockAlert.query.filter(
            StockAlert.status.in_([
                AlertStatus.PENDING,
                AlertStatus.ACKNOWLEDGED,
                AlertStatus.IN_PROGRESS
            ])
        )
        
        if zone_id:
            query = query.filter(StockAlert.zone_id == zone_id)
        
        if severity:
            query = query.filter(StockAlert.severity == severity)
        
        return query.order_by(StockAlert.created_at.desc()).all()
