"""
Middleware centralisé pour le contrôle d'accès basé sur les rôles (RBAC)

This module provides reusable decorators and utilities for:
- Role-based access control
- Permission-based access control  
- Zone-based access control (for multi-zone deployments)
- Automatic zone filtering on queries

✅ PHASE 3 TÂCHE 3.1: Centraliser la logique RBAC
"""

from functools import wraps
from flask import abort, jsonify, current_app
from flask_login import current_user
from rbac_stock import has_stock_permission
from zone_rbac import user_has_global_access


# ============================================================================
# 🔐 DÉCORATEUR 1: Vérification de Rôle
# ============================================================================

def require_role(*allowed_roles):
    """
    Décorateur pour vérifier que l'utilisateur a l'un des rôles autorisés.
    
    Usage:
        @app.route('/admin')
        @require_role('admin', 'chef_pur')
        def admin_panel():
            return "Admin access"
    
    Args:
        *allowed_roles: Rôles autorisés (ex: 'chef_pur', 'gestionnaire_stock')
    
    Returns:
        401 si pas authentifié
        403 si rôle non autorisé
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Vérifier authentification
            if not current_user.is_authenticated:
                current_app.logger.warning(f"Unauthorized access attempt (not authenticated) to {f.__name__}")
                abort(401)
            
            # Vérifier rôle
            if current_user.role not in allowed_roles:
                current_app.logger.warning(
                    f"Forbidden access: user {current_user.id} (role={current_user.role}) "
                    f"tried to access {f.__name__} (allowed roles: {allowed_roles})"
                )
                abort(403)
            
            return f(*args, **kwargs)
        return decorated
    return decorator


# ============================================================================
# 🔐 DÉCORATEUR 2: Vérification de Permission
# ============================================================================

def require_permission(permission_name):
    """
    Décorateur pour vérifier une permission spécifique basée sur le rôle.
    
    Utilise la matrice de permissions de rbac_stock.py pour déterminer
    si le rôle de l'utilisateur a la permission.
    
    Usage:
        @app.route('/api/stock/create')
        @require_permission('can_create_produit')
        def create_product():
            return {"status": "created"}
    
    Args:
        permission_name: Nom de la permission (ex: 'can_create_produit')
    
    Returns:
        401 si pas authentifié
        403 si permission refusée
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Vérifier authentification
            if not current_user.is_authenticated:
                current_app.logger.warning(f"Unauthorized access attempt (not authenticated) to {f.__name__}")
                abort(401)
            
            # Vérifier permission
            if not has_stock_permission(current_user, permission_name):
                current_app.logger.warning(
                    f"Forbidden: user {current_user.id} (role={current_user.role}) "
                    f"lacks permission '{permission_name}' for {f.__name__}"
                )
                abort(403)
            
            return f(*args, **kwargs)
        return decorated
    return decorator


# ============================================================================
# 🔐 DÉCORATEUR 3: Vérification d'Accès Zone
# ============================================================================

def require_zone_access(resource_finder=None):
    """
    Décorateur pour vérifier que l'utilisateur a accès à la zone de la ressource.
    
    Utilisé pour les endpoints qui accèdent à des ressources spécifiques à une zone.
    Les utilisateurs avec accès global (chef_pur, admin) peuvent accéder à toutes zones.
    Les magasinniers et chefs de zone sont limités à leur zone.
    
    Usage:
        def get_resource(mouvement_id):
            return db.session.get(MouvementStock, mouvement_id)
        
        @app.route('/api/mouvements/<int:mouvement_id>')
        @require_zone_access(get_resource)
        def get_mouvement(mouvement_id):
            mouvement = get_resource(mouvement_id)
            return jsonify(mouvement.to_dict())
    
    Args:
        resource_finder: Fonction optionnelle pour récupérer la ressource
                        et vérifier sa zone_id
    
    Returns:
        401 si pas authentifié
        403 si zone non autorisée
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Vérifier authentification
            if not current_user.is_authenticated:
                abort(401)
            
            # Si utilisateur a accès global, pas de vérification de zone
            if user_has_global_access():
                return f(*args, **kwargs)
            
            # Pour magasinier / chef_zone : vérifier la zone de la ressource
            if current_user.role in ['magasinier', 'chef_zone']:
                if resource_finder:
                    try:
                        resource = resource_finder(*args, **kwargs)
                        if resource and hasattr(resource, 'zone_id'):
                            if resource.zone_id != current_user.zone_id:
                                current_app.logger.warning(
                                    f"Zone access denied: user {current_user.id} (zone={current_user.zone_id}) "
                                    f"tried to access resource in zone {resource.zone_id}"
                                )
                                abort(403)
                    except Exception as e:
                        current_app.logger.error(f"Error in require_zone_access: {str(e)}")
                        abort(403)
            
            return f(*args, **kwargs)
        return decorated
    return decorator


# ============================================================================
# 🔧 FONCTION UTILITAIRE: Filtrage Automatique de Zone
# ============================================================================

def apply_zone_filter(query, user, zone_field=None):
    """
    Appliquer automatiquement le filtrage de zone à une requête SQLAlchemy.
    
    Cette fonction est le cœur de l'harmonisation des filtres.
    Elle détecte le rôle de l'utilisateur et applique le filtrage approprié.
    
    Usage:
        from middleware import apply_zone_filter
        
        query = db.session.query(MouvementStock)
        query = apply_zone_filter(query, current_user, MouvementStock.zone_id)
        mouvements = query.all()
    
    Args:
        query: SQLAlchemy query object
        user: Objet utilisateur (current_user)
        zone_field: Champ de zone à filtrer (ex: MouvementStock.zone_id)
    
    Returns:
        query: Requête filtrée ou originale selon le rôle de l'utilisateur
        
    Filtrage:
        - magasinier → zone_field == user.zone_id
        - chef_zone → zone_field == user.zone_id
        - chef_pur, admin, direction → pas de filtre (accès global)
    """
    # Vérifier que user_has_global_access() existe et fonctionne
    try:
        has_global = user_has_global_access()
    except Exception as e:
        current_app.logger.warning(f"Error checking global access: {str(e)}, treating as non-global")
        has_global = False
    
    # Si utilisateur a accès global, retourner sans filtrer
    if has_global:
        current_app.logger.debug(f"User {user.id} has global access, no zone filter applied")
        return query
    
    # Magasinier et Chef zone : filtrer par leur zone
    if user.role in ['magasinier', 'chef_zone']:
        if zone_field is not None:
            try:
                filtered_query = query.filter(zone_field == user.zone_id)
                current_app.logger.debug(
                    f"Applied zone filter for {user.role} {user.id}: zone_id={user.zone_id}"
                )
                return filtered_query
            except Exception as e:
                current_app.logger.error(f"Error applying zone filter: {str(e)}")
                # En cas d'erreur, retourner la requête originale
                # (mieux une requête sans filtre qu'une erreur 500)
                return query
    
    # Pour tous les autres rôles (direction, etc.) : pas de filtre
    return query


# ============================================================================
# 📚 FONCTION UTILITAIRE: Vérifier Accès Global
# ============================================================================

def user_can_view_all_zones():
    """
    Vérifier rapidement si l'utilisateur peut voir toutes les zones.
    
    Utile pour les templates et la logique applicative.
    
    Returns:
        bool: True si chef_pur, admin ou direction; False sinon
    """
    return current_user.role in ['chef_pur', 'admin', 'direction']


# ============================================================================
# 📊 FONCTION UTILITAIRE: Log d'Accès
# ============================================================================

def log_access_attempt(endpoint, resource_type=None, resource_id=None, granted=True):
    """
    Logger les tentatives d'accès pour audit et sécurité.
    
    Usage:
        log_access_attempt('/api/stock/export', 'mouvement', 123, granted=False)
    
    Args:
        endpoint: Endpoint accédé (ex: '/api/stock/export')
        resource_type: Type de ressource (ex: 'mouvement', 'produit')
        resource_id: ID de la ressource
        granted: True si accès accordé, False sinon
    """
    status = "GRANTED" if granted else "DENIED"
    current_app.logger.info(
        f"[RBAC] {status} - User {current_user.id} ({current_user.role}) "
        f"→ {endpoint} {resource_type or ''} #{resource_id or ''}"
    )
