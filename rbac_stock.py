"""
Système de contrôle d'accès basé sur les rôles (RBAC) pour le module Gestion de Stock
Détermine les permissions par rôle utilisateur
"""

from functools import wraps
from flask import flash, redirect, url_for, abort, current_app
from flask_login import current_user

# Définition des rôles et permissions pour le stock
STOCK_PERMISSIONS = {
    # Chef PUR (Responsable Principal Stock)
    'chef_pur': {
        'can_view_global_stock': True,
        'can_create_produit': True,
        'can_modify_produit': True,
        'can_delete_produit': True,
        'can_receive_stock': True,  # Réception
        'can_dispatch_stock': True,  # Distribution
        'can_adjust_stock': True,  # Ajustement
        'can_approve_stock_movement': True,  # Approbation
        'can_manage_fournisseurs': True,
        'can_import_articles': True,
        'can_view_reports': True,
        'can_manage_emplacements': True,
        'max_edit_distance': None,  # Peut éditer partout
    },
    
    # Gestionnaire Stock (Central)
    'gestionnaire_stock': {
        'can_view_global_stock': True,
        'can_create_produit': True,
        'can_modify_produit': False,  # Modification limitée
        'can_delete_produit': False,
        'can_receive_stock': True,
        'can_dispatch_stock': True,
        'can_adjust_stock': False,  # Nécessite approbation
        'can_approve_stock_movement': False,
        'can_manage_fournisseurs': True,
        'can_import_articles': True,
        'can_view_reports': True,
        'can_manage_emplacements': False,
        'max_edit_distance': None,
    },
    
    # Magasinier Local (par Zone)
    'magasinier': {
        'can_view_global_stock': False,  # ✅ PHASE 1 FIX: Vue locale seulement (zone)
        'can_create_produit': False,
        'can_modify_produit': False,
        'can_delete_produit': False,
        'can_receive_stock': True,  # ✅ Réception locale sa zone
        'can_dispatch_stock': True,  # ✅ Distribution zone
        'can_adjust_stock': False,
        'can_approve_stock_movement': False,  # ⚠️ Note: Can approve OWN movements in same zone only
        'can_manage_fournisseurs': False,
        'can_import_articles': False,
        'can_view_reports': False,  # Rapports zone seulement
        'can_manage_emplacements': False,
        'max_edit_distance': 'zone',  # ✅ Éditer sa zone seulement — CRITICAL CONSTRAINT
    },
    
    # Technicien (Terrain)
    'technicien': {
        'can_view_global_stock': False,
        'can_create_produit': False,
        'can_modify_produit': False,
        'can_delete_produit': False,
        'can_receive_stock': False,
        'can_dispatch_stock': False,  # Peut consommer pour intervention
        'can_adjust_stock': False,
        'can_approve_stock_movement': False,
        'can_manage_fournisseurs': False,
        'can_import_articles': False,
        'can_view_reports': False,
        'can_manage_emplacements': False,
        'max_edit_distance': None,
    },
    
    # Direction (DG/DT) - Lecture seule
    'direction': {
        'can_view_global_stock': True,  # Vue complète mais read-only
        'can_create_produit': False,
        'can_modify_produit': False,
        'can_delete_produit': False,
        'can_receive_stock': False,
        'can_dispatch_stock': False,
        'can_adjust_stock': False,
        'can_approve_stock_movement': False,
        'can_manage_fournisseurs': False,
        'can_import_articles': False,
        'can_view_reports': True,  # Tous les rapports
        'can_manage_emplacements': False,
        'max_edit_distance': None,
    },
    
    # Admin système
    'admin': {
        'can_view_global_stock': True,
        'can_create_produit': True,
        'can_modify_produit': True,
        'can_delete_produit': True,
        'can_receive_stock': True,
        'can_dispatch_stock': True,
        'can_adjust_stock': True,
        'can_approve_stock_movement': True,
        'can_manage_fournisseurs': True,
        'can_import_articles': True,
        'can_view_reports': True,
        'can_manage_emplacements': True,
        'max_edit_distance': None,
    },
}


def get_user_stock_permissions(user):
    """
    Récupère les permissions de stock pour un utilisateur
    
    Args:
        user: Objet User
        
    Returns:
        dict: Permissions de l'utilisateur
    """
    if not user or not user.role:
        return {}
    
    role = user.role.lower()
    return STOCK_PERMISSIONS.get(role, {})


def has_stock_permission(user, permission_key):
    """
    Vérifie si un utilisateur a une permission stock spécifique
    
    Args:
        user: Objet User
        permission_key: Clé permission (ex: 'can_receive_stock')
        
    Returns:
        bool: True si utilisateur a permission
    """
    perms = get_user_stock_permissions(user)
    return perms.get(permission_key, False)


def require_stock_permission(permission_key, redirect_to_dashboard=True):
    """
    Décorateur pour protéger les routes par permission stock
    
    Args:
        permission_key: Clé permission à vérifier
        redirect_to_dashboard: Si True, rediriger vers dashboard si accès refusé
        
    Returns:
        Décorateur de fonction
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Veuillez vous connecter', 'danger')
                return redirect(url_for('login'))
            
            if not has_stock_permission(current_user, permission_key):
                flash(f'⛔ Accès refusé. Permission requise: {permission_key}', 'danger')
                current_app.logger.warning(
                    f'Accès refusé pour utilisateur {current_user.username} '
                    f'(rôle: {current_user.role}) à permission: {permission_key}'
                )
                
                if redirect_to_dashboard:
                    # For magasiniers, redirect to their zone view instead of global view
                    if current_user.role == 'magasinier':
                        return redirect(url_for('stock.liste_produits_zone'))
                    else:
                        return redirect(url_for('stock.liste_produits'))
                else:
                    abort(403)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_stock_role(*roles):
    """
    Décorateur pour protéger les routes par rôle stock spécifique
    
    Args:
        *roles: Rôles autorisés (ex: 'chef_pur', 'gestionnaire_stock')
        
    Returns:
        Décorateur de fonction
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Veuillez vous connecter', 'danger')
                return redirect(url_for('login'))
            
            user_role = current_user.role.lower() if current_user.role else None
            
            if user_role not in [r.lower() for r in roles]:
                allowed_roles = ', '.join(roles)
                flash(
                    f'⛔ Accès refusé. Rôles autorisés: {allowed_roles}. Votre rôle: {current_user.role}',
                    'danger'
                )
                current_app.logger.warning(
                    f'Accès refusé pour utilisateur {current_user.username} '
                    f'(rôle: {current_user.role}) à ressource requise: {", ".join(roles)}'
                )
                return redirect(url_for('stock.liste_produits'))
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def can_modify_produit(produit):
    """
    Vérifie si utilisateur peut modifier un produit
    
    Args:
        produit: Objet Produit
        
    Returns:
        bool: True si modification autorisée
    """
    if not current_user.is_authenticated:
        return False
    
    user_role = current_user.role.lower() if current_user.role else None
    
    # Admin et chef_pur toujours peuvent
    if user_role in ['admin', 'chef_pur']:
        return True
    
    # Gestionnaire stock peut créer/modifier produits
    if user_role == 'gestionnaire_stock':
        return True
    
    # Autres rôles: non
    return False


def can_delete_produit(produit):
    """
    Vérifie si utilisateur peut supprimer un produit
    
    Args:
        produit: Objet Produit
        
    Returns:
        bool: True si suppression autorisée
    """
    if not current_user.is_authenticated:
        return False
    
    user_role = current_user.role.lower() if current_user.role else None
    
    # Seuls admin et chef_pur peuvent supprimer
    return user_role in ['admin', 'chef_pur']


def can_access_stock_for_zone(zone):
    """
    Vérifie si utilisateur peut accéder stock d'une zone
    
    Args:
        zone: Code zone (ex: 'NORD')
        
    Returns:
        bool: True si accès autorisé
    """
    if not current_user.is_authenticated:
        return False
    
    user_role = current_user.role.lower() if current_user.role else None
    
    # Admin, chef_pur, direction: accès tous
    if user_role in ['admin', 'chef_pur', 'direction', 'gestionnaire_stock']:
        return True
    
    # Chef zone: sa zone seulement
    if user_role == 'chef_zone':
        return current_user.zone == zone
    
    # Magasinier: sa zone seulement
    if user_role == 'magasinier':
        return current_user.zone == zone
    
    # Technicien: sa zone seulement
    if user_role == 'technicien':
        return current_user.zone == zone
    
    return False


# ============================================================================
# ZONE FILTERING - JOUR 3 IMPLEMENTATION
# ============================================================================

def filter_produits_by_zone(produits_query, user):
    """
    Filtre les produits accessibles par zone de l'utilisateur
    
    Args:
        produits_query: SQLAlchemy query de Produit
        user: Objet User
        
    Returns:
        query: Produits filtrés par zone de l'utilisateur
    """
    from models import Produit, EmplacementStock, Zone
    
    # Rôles avec accès global: pas de filtrage
    if not user or user.role.lower() in ['chef_pur', 'admin', 'direction', 'gestionnaire_stock']:
        return produits_query
    
    # Magasinier: filtre par sa zone uniquement
    if user.role.lower() == 'magasinier':
        if not user.zone_id:
            # Magasinier sans zone assignée = pas d'accès
            return produits_query.filter(False)  # Retourne 0 résultats
        
        # Joindre via emplacement → zone
        from sqlalchemy import and_
        return produits_query.join(
            EmplacementStock, Produit.emplacement_id == EmplacementStock.id
        ).filter(
            EmplacementStock.zone_id == user.zone_id
        ).distinct()
    
    # Autres rôles: pas de filtrage
    return produits_query


def filter_mouvements_by_zone(mouvements_query, user):
    """
    Filtre les mouvements de stock accessibles par zone de l'utilisateur
    
    Args:
        mouvements_query: SQLAlchemy query de MouvementStock
        user: Objet User
        
    Returns:
        query: Mouvements filtrés par zone de l'utilisateur
    """
    from models import MouvementStock, EmplacementStock
    
    # Rôles avec accès global: pas de filtrage
    if not user or user.role.lower() in ['chef_pur', 'admin', 'direction', 'gestionnaire_stock']:
        return mouvements_query
    
    # Magasinier: filtre par sa zone uniquement
    if user.role.lower() == 'magasinier':
        if not user.zone_id:
            # Magasinier sans zone = pas d'accès
            return mouvements_query.filter(False)
        
        # Filtre via emplacement_id du mouvement
        return mouvements_query.join(
            EmplacementStock, MouvementStock.emplacement_id == EmplacementStock.id
        ).filter(
            EmplacementStock.zone_id == user.zone_id
        ).distinct()
    
    # Autres rôles: pas de filtrage
    return mouvements_query


def get_role_description(role):
    """
    Retourne description lisible d'un rôle stock
    
    Args:
        role: Code rôle
        
    Returns:
        str: Description
    """
    descriptions = {
        'chef_pur': 'Responsable Principal Stock',
        'gestionnaire_stock': 'Gestionnaire Stock',
        'magasinier': 'Magasinier Local',
        'technicien': 'Technicien',
        'direction': 'Direction',
        'admin': 'Administrateur',
    }
    return descriptions.get(role, role)
