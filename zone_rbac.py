"""
Zone Isolation RBAC - Contrôle d'accès basé sur les zones géographiques
Module pour implémenter l'isolation des zones dans le système stock
"""

from functools import wraps
from flask import flash, redirect, url_for, abort, current_app, request
from flask_login import current_user, login_required
from extensions import db
from sqlalchemy import or_, and_, select
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# RÔLES AVEC ACCÈS MULTI-ZONE VS ZONE-SPÉCIFIQUE
# ============================================================================

# Rôles qui peuvent accéder à TOUTES les zones (pas de restriction)
GLOBAL_ROLES = [
    'chef_pur',           # Chef PUR - Responsable principal, accès global
    'gestionnaire_stock', # Gestionnaire central
    'direction',          # Direction
    'admin',              # Admin système
]

# Rôles restreints à une zone spécifique
ZONE_RESTRICTED_ROLES = [
    'magasinier',         # Magasinier local à une zone
    'chef_zone',          # Chef de zone (ancien rôle)
]

# Rôles avec accès terrain mais variable
TECH_ROLES = [
    'technicien',         # Technicien - peut être affecté à zones
]


# ============================================================================
# FONCTIONS DE VÉRIFICATION DES PERMISSIONS ZONES
# ============================================================================

def user_has_global_access():
    """
    Vérifie si l'utilisateur a accès global (pas de restriction de zone)
    
    Returns:
        bool: True si accès global
    """
    if not current_user.is_authenticated:
        return False
    
    return current_user.role.lower() in GLOBAL_ROLES


def user_has_zone_access(zone_id):
    """
    Vérifie si l'utilisateur a accès à une zone spécifique
    
    Args:
        zone_id: ID de la zone à vérifier
        
    Returns:
        bool: True si accès autorisé
    """
    if not current_user.is_authenticated:
        return False
    
    # Les rôles globaux peuvent accéder à tout
    if user_has_global_access():
        return True
    
    # Les rôles restreints ne peuvent accéder qu'à leur zone
    if current_user.role.lower() in ZONE_RESTRICTED_ROLES:
        return current_user.zone_id == zone_id
    
    # Les techniciens peuvent accéder à leur zone
    if current_user.role.lower() == 'technicien':
        return current_user.zone_id == zone_id
    
    return False


def filter_by_user_zones(query, model_zone_id_col):
    """
    Filtre une requête pour inclure uniquement les zones accessibles à l'utilisateur
    
    Args:
        query: Requête SQLAlchemy à filtrer
        model_zone_id_col: Colonne de zone du modèle (ex: Stock.zone_id)
        
    Returns:
        Query: Requête filtrée
    """
    if not current_user.is_authenticated:
        return query.filter(model_zone_id_col == -1)  # Aucun résultat
    
    # Les rôles globaux voient tout
    if user_has_global_access():
        return query
    
    # Les autres ne voient que leur zone
    if current_user.zone_id:
        return query.filter(model_zone_id_col == current_user.zone_id)
    
    # Si pas de zone assignée, aucun accès
    return query.filter(model_zone_id_col == -1)


def filter_by_user_zones_with_parent(query, model, parent_attr='zone'):
    """
    Filtre une requête basée sur une relation parent à une zone
    
    Args:
        query: Requête SQLAlchemy à filtrer
        model: Modèle à filtrer
        parent_attr: Attribut parent contenant la zone (ex: 'stock')
        
    Returns:
        Query: Requête filtrée
    """
    if not current_user.is_authenticated:
        return query.filter(False)  # Aucun résultat
    
    # Les rôles globaux voient tout
    if user_has_global_access():
        return query
    
    # Les autres ne voient que leur zone
    if current_user.zone_id:
        # Implémentation dépend du schéma réel
        # À adapter selon les relations du modèle
        return query.filter(getattr(model, 'zone_id') == current_user.zone_id)
    
    return query.filter(False)


# ============================================================================
# DÉCORATEURS DE PROTECTION D'ACCÈS AUX ZONES
# ============================================================================

def zone_required(f):
    """
    Décorateur: Vérifie que l'utilisateur a une zone assignée
    Redirection vers login si non authentifié
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.zone_id and current_user.role.lower() in ZONE_RESTRICTED_ROLES:
            flash('Vous n\'avez pas de zone assignée.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def zone_access_required(f):
    """
    Décorateur: Vérifie l'authentification et les droits d'accès aux zones
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        # Extraction de zone_id depuis les arguments de route si présent
        zone_id = kwargs.get('zone_id')
        
        if zone_id and not user_has_zone_access(int(zone_id)):
            logger.warning(
                f"Accès refusé à zone {zone_id} pour utilisateur {current_user.username} "
                f"(rôle: {current_user.role}, zone_id: {current_user.zone_id})"
            )
            flash('Vous n\'avez pas accès à cette zone.', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    
    return decorated_function


def zone_isolation_required(zone_id_param='zone_id'):
    """
    Décorateur paramétrable: Isolation stricte des zones
    
    Args:
        zone_id_param: Nom du paramètre contenant l'ID de zone dans la route
        
    Exemple d'usage:
        @zone_isolation_required('zone_id')
        def view_zone_stock(zone_id):
            ...
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            zone_id = kwargs.get(zone_id_param)
            
            if zone_id:
                zone_id = int(zone_id)
                if not user_has_zone_access(zone_id):
                    logger.warning(
                        f"Tentative d'accès non autorisé à zone {zone_id} "
                        f"par {current_user.username}"
                    )
                    abort(403)
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


# ============================================================================
# VALIDATEURS POUR LES OPÉRATIONS DE STOCK PAR ZONE
# ============================================================================

def validate_stock_operation_zone(stock, operation_type='view'):
    """
    Valide qu'un utilisateur peut effectuer une opération sur un stock
    
    Args:
        stock: Objet Stock
        operation_type: Type d'opération ('view', 'edit', 'delete')
        
    Returns:
        bool: True si opération autorisée
        
    Raises:
        Exception: Si opération non autorisée
    """
    if not current_user.is_authenticated:
        raise PermissionError("Non authentifié")
    
    # Accès global
    if user_has_global_access():
        return True
    
    # Vérification de zone
    if stock.zone_id != current_user.zone_id:
        raise PermissionError(
            f"Accès refusé: Stock zone {stock.zone_id}, "
            f"utilisateur zone {current_user.zone_id}"
        )
    
    # Vérifications spécifiques selon le type d'opération
    if operation_type == 'edit':
        if current_user.role.lower() == 'magasinier':
            if not current_user.zone_id:
                raise PermissionError("Magasinier sans zone assignée")
        elif current_user.role.lower() not in ZONE_RESTRICTED_ROLES + GLOBAL_ROLES:
            raise PermissionError(f"Rôle {current_user.role} ne peut pas éditer")
    
    elif operation_type == 'delete':
        if current_user.role.lower() not in GLOBAL_ROLES:
            raise PermissionError("Suppression réservée aux rôles globaux")
    
    return True


def validate_zone_transition(from_zone_id, to_zone_id):
    """
    Valide qu'un utilisateur peut déplacer un stock d'une zone à une autre
    
    Args:
        from_zone_id: Zone source
        to_zone_id: Zone destination
        
    Returns:
        bool: True si transition autorisée
        
    Raises:
        PermissionError: Si transition non autorisée
    """
    if not current_user.is_authenticated:
        raise PermissionError("Non authentifié")
    
    # Accès global
    if user_has_global_access():
        return True
    
    # Les magasins locaux ne peuvent pas transférer entre zones
    if current_user.role.lower() in ZONE_RESTRICTED_ROLES:
        if from_zone_id != current_user.zone_id:
            raise PermissionError(
                f"Impossible de transférer: zone source {from_zone_id} "
                f"!= zone utilisateur {current_user.zone_id}"
            )
        # Interdiction de transfer inter-zones pour magasins locaux
        if to_zone_id != from_zone_id:
            raise PermissionError(
                f"Magasinier ne peut transférer qu'au sein de sa zone"
            )
    
    return True


# ============================================================================
# HELPERS POUR LES RAPPORTS ET STATISTIQUES
# ============================================================================

def get_user_zone_ids():
    """
    Retourne liste des IDs de zones accessibles par l'utilisateur
    
    Returns:
        list: Liste des zone_id accessibles
    """
    if not current_user.is_authenticated:
        return []
    
    # Accès global: retourner None (pas de filtre)
    if user_has_global_access():
        return None
    
    # Sinon retourner sa zone
    if current_user.zone_id:
        return [current_user.zone_id]
    
    return []


def get_user_zone_name():
    """
    Retourne le nom de la zone de l'utilisateur
    
    Returns:
        str: Nom de la zone
    """
    if not current_user.is_authenticated:
        return "N/A"
    
    if user_has_global_access():
        return "GLOBAL"
    
    if current_user.zone_relation:
        return current_user.zone_relation.nom
    
    return f"Zone {current_user.zone_id}" if current_user.zone_id else "N/A"


# ============================================================================
# AUDIT DE L'ACCÈS AUX ZONES
# ============================================================================

def log_zone_access(action, zone_id, resource_type, resource_id, success=True, error_msg=None):
    """
    Enregistre un accès à une zone (pour audit trail)
    
    Args:
        action: Type d'action (view, edit, delete, etc.)
        zone_id: Zone accédée
        resource_type: Type de ressource (stock, emplacement, etc.)
        resource_id: ID de la ressource
        success: Si opération réussie
        error_msg: Message d'erreur si non réussie
    """
    if not current_user.is_authenticated:
        return
    
    status = "SUCCESS" if success else "FAILED"
    msg = (
        f"[ZONE_ACCESS] {status} - User: {current_user.username}, "
        f"Action: {action}, Zone: {zone_id}, "
        f"Resource: {resource_type}/{resource_id}"
    )
    
    if error_msg:
        msg += f", Error: {error_msg}"
    
    logger.info(msg)


# ============================================================================
# VALIDATIONS MAGASINIER — FILTRAGE STRICT PAR ZONE
# ============================================================================

def validate_magasinier_zone_access():
    """
    Valide que l'utilisateur magasinier a une zone assignée.
    À appeler au début de chaque requête magasinier.
    
    Returns:
        bool: True si valide
        
    Raises:
        abort(403): Si magasinier sans zone ou zone invalide
    """
    if not current_user.is_authenticated:
        abort(403, "Authentification requise")
    
    # Magasinier DOIT avoir une zone
    if current_user.role.lower() == 'magasinier':
        if not current_user.zone_id:
            abort(403, "Magasinier sans zone assignée")
        
        # Vérifier que la zone existe
        from models import Zone
        zone = Zone.query.get(current_user.zone_id)
        if not zone:
            abort(403, "Zone invalide ou supprimée")
    
    return True


def validate_emplacement_zone(emplacement_id):
    """
    Valide qu'un emplacement appartient à la zone du magasinier.
    À appeler avant toute opération mouvement.
    
    Args:
        emplacement_id: ID de l'emplacement à vérifier
        
    Returns:
        dict: L'emplacement validé
        
    Raises:
        abort(400): Si emplacement n'existe pas
        abort(403): Si emplacement n'est pas dans la zone magasinier
    """
    from models import EmplacementStock
    
    emplacement = EmplacementStock.query.get(emplacement_id)
    if not emplacement:
        abort(400, f"Emplacement {emplacement_id} introuvable")
    
    # Si magasinier, vérifier zone
    if current_user.role.lower() == 'magasinier':
        if emplacement.zone_id != current_user.zone_id:
            abort(403, f"Emplacement {emplacement.designation} (Zone {emplacement.zone_relation.nom if emplacement.zone_relation else 'N/A'}) " 
                        f"non autorisé pour Zone {current_user.zone_relation.nom if current_user.zone_relation else 'N/A'}")
    
    return emplacement


def filter_produit_by_emplacement_zone(query):
    """
    Filtre une requête Produit pour n'inclure que les produits
    avec des emplacements accessibles au magasinier.
    
    Utilise le lien Produit → EmplacementStock → Zone
    
    Args:
        query: Requête SQLAlchemy sur Produit
        
    Returns:
        Query: Requête filtrée
    """
    from models import Produit, EmplacementStock, Zone, MouvementStock
    
    if user_has_global_access():
        return query  # Chef/Gestionnaire: pas de filtre
    
    if not current_user.zone_id:
        return query.filter(False)  # Aucun résultat
    
    # Stratégie: Inclure les produits qui:
    # 1. Ont leur emplacement principal dans la zone
    # 2. OU ont au moins un mouvement dans la zone (indiquant une présence de stock passée ou présente)
    
    # On utilise un alias pour éviter les conflits de join si la query a déjà des joins
    from sqlalchemy import or_
    
    # Sous-requête des produits ayant des mouvements dans la zone
    subq_mouv = select(MouvementStock.produit_id)\
        .join(EmplacementStock)\
        .filter(EmplacementStock.zone_id == current_user.zone_id)
        
    # Sous-requête des entrepôts de la zone
    subq_emp = select(EmplacementStock.id).filter(EmplacementStock.zone_id == current_user.zone_id)
    
    # Filtrer par emplacement principal OU par présence de mouvements
    query = query.filter(
        or_(
            Produit.emplacement_id.in_(subq_emp),
            Produit.id.in_(subq_mouv)
        )
    )
    
    return query.distinct()


def filter_mouvement_by_zone(query):
    """
    Filtre une requête MouvementStock pour n'inclure que les mouvements
    dans la zone du magasinier.
    
    Utilise le lien MouvementStock → EmplacementStock → Zone
    
    Args:
        query: Requête SQLAlchemy sur MouvementStock
        
    Returns:
        Query: Requête filtrée
    """
    from models import MouvementStock, EmplacementStock, Zone
    
    if user_has_global_access():
        return query  # Chef/Gestionnaire: pas de filtre
    
    if not current_user.zone_id:
        return query.filter(False)  # Aucun résultat
    
    # Join MouvementStock → EmplacementStock → Zone
    query = query.join(EmplacementStock)\
        .join(Zone)\
        .filter(Zone.id == current_user.zone_id)\
        .distinct()
    
    return query
