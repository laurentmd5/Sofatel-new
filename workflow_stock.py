# workflow_stock.py
"""
Système de Workflow Validation pour les Mouvements de Stock

Ce module implémente un workflow d'approbation complet pour tous les mouvements
de stock, avec validation métier et audit trail.

États du Workflow:
  EN_ATTENTE        → Mouvement créé, en attente de validation
  EN_ATTENTE_DOCS   → Attente documentation (bon livraison, etc)
  REJETE            → Mouvement rejeté par superviseur
  APPROUVE          → Validé et prêt à appliquer
  EXECUTE           → Mouvement appliqué au stock
  VALIDE            → Validé physiquement (inventaire)
  ANNULE            → Mouvement annulé après exécution
"""

from datetime import datetime
from enum import Enum
from functools import wraps
from flask import current_app, abort, jsonify
from sqlalchemy import func
from sqlalchemy.orm import validates


# ============================================================================
# ÉNUMÉRATION DES ÉTATS
# ============================================================================

class WorkflowState(Enum):
    """États possibles d'un mouvement de stock"""
    EN_ATTENTE = 'EN_ATTENTE'
    EN_ATTENTE_DOCS = 'EN_ATTENTE_DOCS'
    REJETE = 'REJETE'
    APPROUVE = 'APPROUVE'
    EXECUTE = 'EXECUTE'
    VALIDE = 'VALIDE'
    ANNULE = 'ANNULE'

    def __str__(self):
        return self.value

    def get_display(self):
        """Affichage utilisateur convivial"""
        display_map = {
            'EN_ATTENTE': 'En attente',
            'EN_ATTENTE_DOCS': 'En attente de documentation',
            'REJETE': 'Rejeté',
            'APPROUVE': 'Approuvé',
            'EXECUTE': 'Exécuté',
            'VALIDE': 'Validé',
            'ANNULE': 'Annulé'
        }
        return display_map.get(self.value, self.value)

    def get_color(self):
        """Couleur Bootstrap pour UI"""
        color_map = {
            'EN_ATTENTE': 'warning',      # Jaune
            'EN_ATTENTE_DOCS': 'info',    # Bleu
            'REJETE': 'danger',           # Rouge
            'APPROUVE': 'success',        # Vert
            'EXECUTE': 'primary',         # Bleu foncé
            'VALIDE': 'success',          # Vert
            'ANNULE': 'secondary'         # Gris
        }
        return color_map.get(self.value, 'secondary')


# ============================================================================
# CONFIGURATION DES RÈGLES DE WORKFLOW
# ============================================================================

WORKFLOW_RULES = {
    'entree': {
        'seuil_approbation': 1000,      # Quantité → validation automatique < 1000
        'require_supplier': True,        # Bon livraison obligatoire
        'require_approval': True,        # Approbation chef PUR si > seuil
        'can_auto_validate': False,      # Pas de validation automatique (audit Sonatel)
        'audit_priority': 'high',        # Priorité d'audit
        'timeout_days': 3                # Délai avant escalade si en attente
    },
    'sortie': {
        'seuil_approbation': 500,
        'require_supplier': False,
        'require_approval': True,
        'can_auto_validate': False,
        'audit_priority': 'medium',
        'timeout_days': 1
    },
    'ajustement': {
        'seuil_approbation': 200,
        'require_supplier': False,
        'require_approval': True,        # Toujours approuvé (peut camoufler perte)
        'can_auto_validate': False,
        'audit_priority': 'high',
        'timeout_days': 2
    },
    'retour': {
        'seuil_approbation': 100,
        'require_supplier': False,
        'require_approval': True,
        'can_auto_validate': False,
        'audit_priority': 'medium',
        'timeout_days': 2
    },
    'inventaire': {
        'seuil_approbation': float('inf'),  # Toujours approuvé
        'require_supplier': False,
        'require_approval': False,          # Validation automatique inventaire
        'can_auto_validate': True,
        'audit_priority': 'medium',
        'timeout_days': 0
    }
}

# Transitions autorisées entre états
VALID_TRANSITIONS = {
    WorkflowState.EN_ATTENTE: [
        WorkflowState.EN_ATTENTE_DOCS,
        WorkflowState.APPROUVE,
        WorkflowState.REJETE
    ],
    WorkflowState.EN_ATTENTE_DOCS: [
        WorkflowState.APPROUVE,
        WorkflowState.REJETE,
        WorkflowState.EN_ATTENTE
    ],
    WorkflowState.APPROUVE: [
        WorkflowState.EXECUTE,
        WorkflowState.REJETE,
        WorkflowState.ANNULE
    ],
    WorkflowState.EXECUTE: [
        WorkflowState.VALIDE,
        WorkflowState.ANNULE
    ],
    WorkflowState.VALIDE: [
        WorkflowState.ANNULE
    ],
    WorkflowState.REJETE: [
        WorkflowState.EN_ATTENTE
    ],
    WorkflowState.ANNULE: []  # État final
}

# Permissions requises par type de mouvement
WORKFLOW_PERMISSIONS = {
    'entree': ['gestionnaire_stock', 'chef_pur'],
    'sortie': ['gestionnaire_stock', 'magasinier', 'chef_pur'],
    'ajustement': ['gestionnaire_stock', 'chef_pur'],
    'retour': ['gestionnaire_stock', 'magasinier', 'chef_pur'],
    'inventaire': ['gestionnaire_stock', 'chef_pur']
}

# Rôles autorisés à approuver par type de mouvement
APPROVAL_ROLES = {
    'entree': ['chef_pur', 'gestionnaire_stock', 'admin'],
    'sortie': ['chef_pur', 'gestionnaire_stock', 'admin'],
    'ajustement': ['chef_pur', 'gestionnaire_stock', 'admin'],
    'retour': ['chef_pur', 'gestionnaire_stock', 'admin'],
    'inventaire': ['gestionnaire_stock', 'chef_pur', 'admin']
}


# ============================================================================
# CLASSE DE VALIDATEUR
# ============================================================================

class WorkflowValidator:
    """Valide les transitions et règles métier du workflow"""

    @staticmethod
    def can_transition(current_state: WorkflowState, target_state: WorkflowState) -> bool:
        """Vérifie si transition est valide"""
        if current_state not in VALID_TRANSITIONS:
            return False
        return target_state in VALID_TRANSITIONS[current_state]

    @staticmethod
    def get_required_approvals(mouvement) -> int:
        """Retourne nombre d'approbations requises"""
        rules = WORKFLOW_RULES.get(mouvement.type_mouvement, {})
        if mouvement.quantite >= rules.get('seuil_approbation', 0):
            return 1 if rules.get('require_approval') else 0
        return 0

    @staticmethod
    def needs_documentation(mouvement) -> bool:
        """Vérifie si documentation est requise"""
        rules = WORKFLOW_RULES.get(mouvement.type_mouvement, {})
        if mouvement.type_mouvement == 'entree':
            return rules.get('require_supplier', False)
        return False

    @staticmethod
    def can_auto_validate(mouvement) -> bool:
        """Détermine si mouvement peut être auto-validé"""
        rules = WORKFLOW_RULES.get(mouvement.type_mouvement, {})
        return rules.get('can_auto_validate', False)

    @staticmethod
    def validate_state_transition(mouvement, new_state: WorkflowState, user) -> tuple[bool, str]:
        """
        Valide une transition d'état avec contrôles métier
        
        Returns:
            tuple (is_valid, error_message)
        """
        current_state = WorkflowState(mouvement.workflow_state)

        # 1. Vérifier transition validée
        if not WorkflowValidator.can_transition(current_state, new_state):
            return False, f"Transition {current_state.value} → {new_state.value} non autorisée"

        # 2. Si approbation, vérifier permissions
        if new_state == WorkflowState.APPROUVE:
            approval_roles = APPROVAL_ROLES.get(mouvement.type_mouvement, [])
            if user.role not in approval_roles:
                return False, f"Rôle {user.role} ne peut pas approuver"

        # 3. Si rejet, vérifier permissions
        if new_state == WorkflowState.REJETE:
            if user.role not in ['chef_pur', 'gestionnaire_stock', 'admin']:
                return False, "Seul un superviseur peut rejeter"

        # 4. Si exécution, vérifier stock disponible (pour sorties)
        if new_state == WorkflowState.EXECUTE and mouvement.type_mouvement == 'sortie':
            if mouvement.produit.quantite < mouvement.quantite:
                return False, f"Stock insuffisant: {mouvement.produit.quantite} disponible"

        # 5. Si validation, vérifier documentation pour entrées
        if new_state == WorkflowState.VALIDE:
            if WorkflowValidator.needs_documentation(mouvement):
                if not mouvement.reference:
                    return False, "Documentation requise (bon livraison)"

        return True, ""

    @staticmethod
    def check_for_anomalies(mouvement) -> list[dict]:
        """
        Détecte anomalies dans mouvement
        
        Returns:
            Liste de dictionnaires {severity, message, type}
        """
        anomalies = []

        # Vérifier quantité négative
        if mouvement.quantite <= 0:
            anomalies.append({
                'severity': 'critical',
                'message': 'Quantité doit être positive',
                'type': 'qty_negative'
            })

        # Vérifier prix unitaire cohérent (pour entrées)
        if mouvement.type_mouvement == 'entree':
            if mouvement.prix_unitaire and mouvement.prix_unitaire > 10000:
                anomalies.append({
                    'severity': 'warning',
                    'message': f'Prix élevé: {mouvement.prix_unitaire} FCFA',
                    'type': 'high_price'
                })

        # Vérifier stock pour sortie
        if mouvement.type_mouvement == 'sortie':
            if mouvement.produit.quantite < mouvement.quantite:
                anomalies.append({
                    'severity': 'critical',
                    'message': 'Stock insuffisant',
                    'type': 'insufficient_stock'
                })

        # Vérifier délai écart (si inventaire)
        if mouvement.type_mouvement == 'inventaire':
            if abs(mouvement.ecart) > mouvement.quantite_reelle * 0.1:  # >10% écart
                anomalies.append({
                    'severity': 'warning',
                    'message': f'Écart important: {mouvement.ecart} unités',
                    'type': 'large_discrepancy'
                })

        # Vérifier zone autorisée pour magasinier
        if mouvement.cree_par.role == 'magasinier':
            if mouvement.emplacement and mouvement.emplacement.zone != mouvement.cree_par.zone:
                anomalies.append({
                    'severity': 'critical',
                    'message': 'Magasinier hors zone autorisée',
                    'type': 'zone_restriction'
                })

        return anomalies


# ============================================================================
# DÉCORATEURS
# ============================================================================

def require_workflow_state(*allowed_states):
    """Décorateur: vérifie que mouvement est dans l'un des états"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, mouvement_id, **kwargs):
            from models import MouvementStock
            
            mouvement = MouvementStock.query.get(mouvement_id)
            if not mouvement:
                abort(404, "Mouvement non trouvé")

            current_state = WorkflowState(mouvement.workflow_state)
            if current_state not in allowed_states:
                abort(403, f"Mouvement dans état {current_state.value}, attendu: {[s.value for s in allowed_states]}")

            return f(*args, mouvement_id=mouvement_id, **kwargs)
        return decorated_function
    return decorator


def require_approval_permission(f):
    """Décorateur: vérifie que l'utilisateur peut approuver"""
    @wraps(f)
    def decorated_function(*args, mouvement_id, **kwargs):
        from flask_login import current_user
        from models import MouvementStock
        
        if not current_user.is_authenticated:
            abort(401, "Authentification requise")

        mouvement = MouvementStock.query.get(mouvement_id)
        if not mouvement:
            abort(404)

        approval_roles = APPROVAL_ROLES.get(mouvement.type_mouvement, [])
        if current_user.role not in approval_roles:
            abort(403, f"Rôle {current_user.role} ne peut pas approuver ce type de mouvement")

        return f(*args, mouvement_id=mouvement_id, **kwargs)
    return decorated_function


# ============================================================================
# UTILITAIRES
# ============================================================================

def get_pending_approvals(limit=None):
    """Récupère tous les mouvements en attente d'approbation"""
    from models import MouvementStock
    
    query = MouvementStock.query.filter_by(
        workflow_state=WorkflowState.EN_ATTENTE.value
    ).order_by(MouvementStock.date_mouvement.desc())
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


def get_pending_by_role(role, limit=None):
    """Récupère mouvements en attente d'approbation pour un rôle spécifique"""
    from models import MouvementStock
    
    # Déterminer types de mouvement que ce rôle peut approuver
    approvable_types = []
    for mov_type, roles in APPROVAL_ROLES.items():
        if role in roles:
            approvable_types.append(mov_type)
    
    query = MouvementStock.query.filter(
        MouvementStock.workflow_state.in_([
            WorkflowState.EN_ATTENTE.value,
            WorkflowState.EN_ATTENTE_DOCS.value
        ]),
        MouvementStock.type_mouvement.in_(approvable_types)
    ).order_by(MouvementStock.date_mouvement.desc())
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


def log_workflow_action(mouvement_id, action, user_id, reason='', new_state=None):
    """Enregistre une action du workflow dans l'audit trail"""
    from models import AuditLog
    
    try:
        log = AuditLog(
            entity_type='MouvementStock',
            entity_id=mouvement_id,
            action=action,
            user_id=user_id,
            details={
                'action': action,
                'reason': reason,
                'new_state': new_state.value if new_state else None,
                'timestamp': datetime.utcnow().isoformat()
            },
            timestamp=datetime.utcnow()
        )
        from models import db
        db.session.add(log)
        db.session.commit()
        return log
    except Exception as e:
        current_app.logger.error(f"Erreur log workflow: {str(e)}")
        return None


def format_workflow_response(mouvement, include_details=True):
    """Formate réponse JSON d'un mouvement avec état du workflow"""
    data = {
        'id': mouvement.id,
        'type_mouvement': mouvement.type_mouvement,
        'workflow_state': mouvement.workflow_state,
        'workflow_display': WorkflowState(mouvement.workflow_state).get_display(),
        'workflow_color': WorkflowState(mouvement.workflow_state).get_color(),
        'quantite': float(mouvement.quantite),
        'date_mouvement': mouvement.date_mouvement.isoformat(),
        'cree_par': mouvement.cree_par.username if mouvement.cree_par else None
    }
    
    if include_details:
        data.update({
            'produit_id': mouvement.produit_id,
            'produit_nom': mouvement.produit.nom if mouvement.produit else None,
            'prix_unitaire': float(mouvement.prix_unitaire) if mouvement.prix_unitaire else None,
            'montant_total': float(mouvement.montant_total) if mouvement.montant_total else None,
            'reference': mouvement.reference,
            'commentaire': mouvement.commentaire,
            'emplacement_id': mouvement.emplacement_id,
            'anomalies': WorkflowValidator.check_for_anomalies(mouvement)
        })
    
    return data


# ============================================================================
# ÉTATS SPÉCIAUX
# ============================================================================

def init_workflow_state(mouvement, user):
    """Initialise l'état du workflow pour un nouveau mouvement"""
    rules = WORKFLOW_RULES.get(mouvement.type_mouvement, {})
    
    # Pour inventaire, validation automatique
    if mouvement.type_mouvement == 'inventaire':
        mouvement.workflow_state = WorkflowState.APPROUVE.value
        return
    
    # Pour autres mouvements: en attente d'approbation si > seuil
    if mouvement.quantite >= rules.get('seuil_approbation', 0):
        mouvement.workflow_state = WorkflowState.EN_ATTENTE.value
    else:
        # < seuil: approuvé automatiquement pour les mouvements de réception
        if mouvement.type_mouvement == 'inventaire':
            mouvement.workflow_state = WorkflowState.APPROUVE.value
        else:
            mouvement.workflow_state = WorkflowState.EN_ATTENTE.value


def auto_execute_mouvement(mouvement):
    """Applique automatiquement le mouvement au stock si approuvé"""
    from models import Produit
    
    if mouvement.workflow_state != WorkflowState.APPROUVE.value:
        raise ValueError(f"Mouvement doit être APPROUVE, actuellement {mouvement.workflow_state}")
    
    # Application logique selon type
    if mouvement.type_mouvement in ['entree', 'ajustement', 'retour']:
        # Augmente stock
        mouvement.produit.quantite += mouvement.quantite
    elif mouvement.type_mouvement == 'sortie':
        # Réduit stock
        if mouvement.produit.quantite < mouvement.quantite:
            raise ValueError("Stock insuffisant")
        mouvement.produit.quantite -= mouvement.quantite
    
    mouvement.workflow_state = WorkflowState.EXECUTE.value
    mouvement.date_execution = datetime.utcnow()


# ============================================================================
# GESTION DES ÉTATS SPÉCIAUX
# ============================================================================

WORKFLOW_SPECIAL_CASES = {
    'entree_sonatel': {
        'description': 'Entrée de fournisseur avec bon livraison',
        'required_fields': ['reference', 'prix_unitaire', 'emplacement_id'],
        'require_approval': True,
        'audit_required': True
    },
    'sortie_technicien': {
        'description': 'Sortie allocation technicien',
        'required_fields': ['emplacement_id', 'commentaire'],
        'require_approval': False,
        'audit_required': True
    },
    'sortie_zone': {
        'description': 'Sortie transport zone',
        'required_fields': ['emplacement_id', 'commentaire'],
        'require_approval': True,
        'audit_required': True
    }
}
