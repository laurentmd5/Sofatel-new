"""
Module d'Audit Trail Immutable - Enregistrement immuable de toutes les opérations
Chaque opération est enregistrée avec timestamp, utilisateur, zone, et détails
"""

from datetime import datetime, timezone
from extensions import db
from sqlalchemy import Index, func
import json
import logging
import hashlib

logger = logging.getLogger(__name__)


def utcnow():
    """Return timezone-aware UTC datetime"""
    return datetime.now(timezone.utc)


# ============================================================================
# AUDIT TRAIL - Enregistrement immutable des opérations
# ============================================================================

class AuditAction(db.Model):
    """
    Enregistrement immuable d'une action utilisateur
    Une fois créée, cette entrée ne doit JAMAIS être modifiée ou supprimée
    """
    __tablename__ = 'audit_action'
    
    # Identifiant unique
    id = db.Column(db.Integer, primary_key=True)
    
    # ========== IDENTITÉ UTILISATEUR ==========
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('audit_actions', lazy='dynamic'))
    username = db.Column(db.String(100), nullable=False, index=True)  # Snapshot du username
    
    # ========== CONTEXTE ZONE ==========
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'), nullable=True, index=True)
    zone = db.relationship('Zone', foreign_keys=[zone_id])
    zone_name = db.Column(db.String(100), nullable=True)  # Snapshot du nom de zone
    
    # ========== ACTION ==========
    action_type = db.Column(db.String(50), nullable=False, index=True)  # create, update, delete, view, export, etc.
    module = db.Column(db.String(50), nullable=False, index=True)  # stock, emplacement, numeroserie, etc.
    resource_type = db.Column(db.String(50), nullable=False)  # Stock, Emplacement, NumeroSerie, etc.
    resource_id = db.Column(db.Integer, nullable=True)
    resource_code = db.Column(db.String(100), nullable=True)  # Code unique du resource (référence stock, etc.)
    
    # ========== DÉTAILS DE L'OPÉRATION ==========
    description = db.Column(db.String(255), nullable=False)
    before_state = db.Column(db.JSON, nullable=True)  # État avant modification (pour update/delete)
    after_state = db.Column(db.JSON, nullable=True)   # État après modification (pour create/update)
    changes = db.Column(db.JSON, nullable=True)       # Delta des changements {field: {old: x, new: y}}
    
    # ========== MÉTADONNÉES DE LA REQUÊTE ==========
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 ou IPv6
    user_agent = db.Column(db.Text, nullable=True)
    endpoint = db.Column(db.String(255), nullable=True)   # Route/endpoint appelé
    http_method = db.Column(db.String(10), nullable=True)
    
    # ========== RÉSULTAT ==========
    success = db.Column(db.Boolean, nullable=False, default=True)
    status_code = db.Column(db.Integer, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    # ========== HORODATAGE IMMUTABLE ==========
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)
    # Pas de date de modification - l'enregistrement est immuable!
    
    # ========== INTÉGRITÉ ==========
    checksum = db.Column(db.String(64), nullable=True)  # SHA256 du contenu pour vérifier intégrité
    previous_checksum = db.Column(db.String(64), nullable=True)  # Chaîne de hash pour validation
    
    # Indices pour les requêtes courantes
    __table_args__ = (
        Index('idx_audit_user_date', 'user_id', 'created_at'),
        Index('idx_audit_zone_date', 'zone_id', 'created_at'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_action_module', 'action_type', 'module'),
    )
    
    def compute_checksum(self):
        """
        Calcule le checksum SHA256 de cet enregistrement
        Pour garantir l'intégrité (détection de modifications)
        """
        data = {
            'user_id': self.user_id,
            'zone_id': self.zone_id,
            'action_type': self.action_type,
            'module': self.module,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'created_at': str(self.created_at),
            'changes': json.dumps(self.changes, sort_keys=True, default=str),
            'previous_checksum': self.previous_checksum,
        }
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def verify_integrity(self):
        """
        Vérifie l'intégrité du record audit (détecte les modifications post-création)
        """
        return self.checksum == self.compute_checksum()
    
    def __repr__(self):
        return f'<AuditAction {self.id}: {self.action_type} {self.resource_type}/{self.resource_id}>'


# ============================================================================
# AUDIT TRAIL - Raccordements de données sensibles
# ============================================================================

class AuditAccessLog(db.Model):
    """
    Enregistre chaque accès à des données sensibles (lecture)
    Important pour tracker qui a consulté quelles données
    """
    __tablename__ = 'audit_access_log'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Utilisateur
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', foreign_keys=[user_id])
    username = db.Column(db.String(100), nullable=False, index=True)
    
    # Zone
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'), nullable=True, index=True)
    zone = db.relationship('Zone')
    
    # Ressource accédée
    resource_type = db.Column(db.String(50), nullable=False)  # Stock, Emplacement, etc.
    resource_id = db.Column(db.Integer, nullable=True)
    
    # Contexte
    endpoint = db.Column(db.String(255), nullable=False)
    query_params = db.Column(db.JSON, nullable=True)  # Paramètres de recherche
    ip_address = db.Column(db.String(45), nullable=True)
    
    # Horodatage
    accessed_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_access_user_date', 'user_id', 'accessed_at'),
        Index('idx_access_resource', 'resource_type', 'resource_id'),
    )
    
    def __repr__(self):
        return f'<AuditAccessLog {self.username} -> {self.resource_type}/{self.resource_id}>'


# ============================================================================
# ENREGISTREURS D'AUDIT - Fonctions pour créer les enregistrements
# ============================================================================

class AuditLogger:
    """
    Service centralisé pour enregistrer les actions d'audit
    S'assure que chaque action est correctement enregistrée et immuable
    """
    
    @staticmethod
    def log_action(
        action_type,
        module,
        resource_type,
        description,
        resource_id=None,
        resource_code=None,
        before_state=None,
        after_state=None,
        changes=None,
        zone_id=None,
        success=True,
        status_code=None,
        error_message=None,
        ip_address=None,
        user_agent=None,
        endpoint=None,
        http_method=None,
        user=None,
    ):
        """
        Enregistre une action dans l'audit trail immuable
        
        Args:
            action_type: create, update, delete, view, export, etc.
            module: stock, emplacement, numeroserie, etc.
            resource_type: Nom du type de ressource
            description: Description lisible de l'action
            resource_id: ID de la ressource affectée
            resource_code: Code unique de la ressource
            before_state: État avant (dict)
            after_state: État après (dict)
            changes: Changements spécifiques (dict)
            zone_id: ID de la zone concernée
            success: Si l'action a réussi
            status_code: Code HTTP
            error_message: Message d'erreur si échoué
            ip_address: Adresse IP du client
            user_agent: User agent du navigateur
            endpoint: Endpoint appelé
            http_method: Méthode HTTP
            user: Utilisateur (par défaut current_user)
            
        Returns:
            AuditAction: L'enregistrement créé
        """
        from flask_login import current_user
        from flask import request
        
        if user is None:
            user = current_user if current_user.is_authenticated else None
        
        # Extraire info du request si pas fournies
        if ip_address is None:
            ip_address = request.remote_addr if request else None
        
        if user_agent is None:
            user_agent = request.headers.get('User-Agent') if request else None
        
        if endpoint is None:
            endpoint = request.endpoint if request else None
        
        if http_method is None:
            http_method = request.method if request else None
        
        # Créer l'enregistrement
        audit = AuditAction(
            user_id=user.id if user else None,
            username=user.username if user else 'ANONYMOUS',
            zone_id=zone_id if zone_id else (user.zone_id if user else None),
            zone_name=user.zone_relation.nom if user and user.zone_relation else None,
            action_type=action_type,
            module=module,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_code=resource_code,
            description=description,
            before_state=before_state,
            after_state=after_state,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            http_method=http_method,
            success=success,
            status_code=status_code,
            error_message=error_message,
        )
        
        # Calculer et enregistrer les checksums pour l'intégrité
        audit.checksum = audit.compute_checksum()
        
        try:
            db.session.add(audit)
            db.session.commit()
            logger.info(f"Audit logged: {audit}")
            return audit
        except Exception as e:
            logger.error(f"Failed to log audit action: {str(e)}")
            db.session.rollback()
            # Ne pas lever l'exception pour ne pas bloquer l'opération
            return None
    
    @staticmethod
    def log_access(
        resource_type,
        resource_id,
        zone_id=None,
        query_params=None,
        ip_address=None,
        user=None,
    ):
        """
        Enregistre un accès (lecture) à une ressource sensible
        
        Args:
            resource_type: Type de ressource
            resource_id: ID de la ressource
            zone_id: Zone concernée
            query_params: Paramètres de recherche
            ip_address: IP du client
            user: Utilisateur (par défaut current_user)
        """
        from flask_login import current_user
        from flask import request
        
        if user is None:
            user = current_user if current_user.is_authenticated else None
        
        if ip_address is None:
            ip_address = request.remote_addr if request else None
        
        access_log = AuditAccessLog(
            user_id=user.id if user else None,
            username=user.username if user else 'ANONYMOUS',
            zone_id=zone_id if zone_id else (user.zone_id if user else None),
            resource_type=resource_type,
            resource_id=resource_id,
            endpoint=request.endpoint if request else None,
            query_params=query_params,
            ip_address=ip_address,
        )
        
        try:
            db.session.add(access_log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to log access: {str(e)}")
            db.session.rollback()


# ============================================================================
# HELPERS POUR REQUÊTES AUDIT
# ============================================================================

def get_audit_trail(resource_type, resource_id):
    """
    Récupère l'historique complet d'une ressource
    
    Args:
        resource_type: Type de ressource
        resource_id: ID de la ressource
        
    Returns:
        list: Enregistrements d'audit pour cette ressource
    """
    return AuditAction.query.filter_by(
        resource_type=resource_type,
        resource_id=resource_id
    ).order_by(AuditAction.created_at.asc()).all()


def get_user_audit_trail(user_id, days=30):
    """
    Récupère les actions d'un utilisateur
    
    Args:
        user_id: ID de l'utilisateur
        days: Nombre de jours à retourner
        
    Returns:
        list: Actions de cet utilisateur
    """
    from datetime import timedelta
    cutoff = utcnow() - timedelta(days=days)
    
    return AuditAction.query.filter(
        AuditAction.user_id == user_id,
        AuditAction.created_at >= cutoff
    ).order_by(AuditAction.created_at.desc()).all()


def verify_audit_integrity():
    """
    Vérifie l'intégrité de l'audit trail complet
    Détecte les modifications non autorisées
    
    Returns:
        dict: {total_records, valid_records, corrupted_records, corruption_details}
    """
    audits = AuditAction.query.all()
    
    corrupted = []
    valid_count = 0
    
    for audit in audits:
        if not audit.verify_integrity():
            corrupted.append({
                'id': audit.id,
                'created_at': audit.created_at,
                'user': audit.username,
                'action': audit.action_type,
            })
        else:
            valid_count += 1
    
    return {
        'total_records': len(audits),
        'valid_records': valid_count,
        'corrupted_records': len(corrupted),
        'corruption_details': corrupted,
    }
