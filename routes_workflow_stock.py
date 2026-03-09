# routes_workflow_stock.py
"""
Routes de gestion du workflow des mouvements de stock

Endpoints:
  GET  /api/mouvements/pending          - Lister mouvements en attente
  POST /api/mouvement/<id>/approve      - Approuver un mouvement
  POST /api/mouvement/<id>/reject       - Rejeter un mouvement
  POST /api/mouvement/<id>/validate     - Valider un mouvement
  POST /api/mouvement/<id>/execute      - Exécuter un mouvement
  GET  /api/mouvement/<id>/history      - Historique du mouvement
  GET  /gestion-stock/approvals         - Page d'approbation (HTML)
"""

from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime

from models import db, User, MouvementStock, Produit, AuditLog
from rbac_stock import require_stock_permission
from workflow_stock import (
    WorkflowState,
    WorkflowValidator,
    WorkflowRules,
    get_pending_by_role,
    get_pending_approvals,
    log_workflow_action,
    format_workflow_response,
    auto_execute_mouvement,
    APPROVAL_ROLES,
    WORKFLOW_RULES
)

# Créer blueprint
workflow_bp = Blueprint('workflow', __name__, url_prefix='/api')


# ============================================================================
# DÉCORATEURS
# ============================================================================

def require_approval_permission(type_mouvement=None):
    """Vérifie que l'utilisateur peut approuver ce type de mouvement"""
    def decorator(f):
        def decorated_function(*args, mouvement_id, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentification requise'}), 401

            mouvement = MouvementStock.query.get(mouvement_id)
            if not mouvement:
                return jsonify({'error': 'Mouvement non trouvé'}), 404

            # Vérifier les permissions
            approval_roles = APPROVAL_ROLES.get(mouvement.type_mouvement, [])
            if current_user.role not in approval_roles:
                return jsonify({'error': f"Rôle {current_user.role} ne peut pas approuver"}), 403

            return f(*args, mouvement_id=mouvement_id, **kwargs)
        return decorated_function
    return decorator


# ============================================================================
# ENDPOINTS - CONSULTATION
# ============================================================================

@workflow_bp.route('/mouvements/pending', methods=['GET'])
@login_required
@require_stock_permission('can_view_global_stock')
def get_pending_mouvements():
    """
    Récupère les mouvements en attente d'approbation
    
    Filtres disponibles:
      ?role=chef_pur          - Mouvements que le rôle peut approuver
      ?type=entree            - Filtrer par type de mouvement
      ?limit=20               - Limiter résultats
    """
    try:
        role = request.args.get('role', current_user.role)
        mov_type = request.args.get('type')
        limit = request.args.get('limit', type=int, default=50)

        # Récupérer mouvements en attente pour ce rôle
        mouvements = get_pending_by_role(current_user.role, limit=limit)

        # Filtrer par type si spécifié
        if mov_type:
            mouvements = [m for m in mouvements if m.type_mouvement == mov_type]

        # Formater réponse
        data = {
            'total': len(mouvements),
            'user_role': current_user.role,
            'mouvements': [format_workflow_response(m, include_details=True) for m in mouvements],
            'stats': {
                'en_attente': sum(1 for m in mouvements if m.workflow_state == 'EN_ATTENTE'),
                'en_attente_docs': sum(1 for m in mouvements if m.workflow_state == 'EN_ATTENTE_DOCS'),
                'rejete': sum(1 for m in mouvements if m.workflow_state == 'REJETE'),
            }
        }

        return jsonify(data), 200

    except Exception as e:
        current_app.logger.error(f"Erreur get_pending_mouvements: {str(e)}")
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/mouvement/<int:mouvement_id>/status', methods=['GET'])
@login_required
def get_mouvement_status(mouvement_id):
    """Récupère le statut du workflow d'un mouvement"""
    try:
        mouvement = MouvementStock.query.get_or_404(mouvement_id)

        data = {
            'id': mouvement.id,
            'type': mouvement.type_mouvement,
            'state': mouvement.workflow_state,
            'display_state': WorkflowState(mouvement.workflow_state).get_display(),
            'color': WorkflowState(mouvement.workflow_state).get_color(),
            'quantite': float(mouvement.quantite),
            'date_mouvement': mouvement.date_mouvement.isoformat(),
            'cree_par': mouvement.cree_par.username if mouvement.cree_par else None,
            'approuve_par': mouvement.approuve_par.username if mouvement.approuve_par else None,
            'date_approbation': mouvement.date_approbation.isoformat() if mouvement.date_approbation else None,
            'motif_rejet': mouvement.motif_rejet,
            'anomalies': mouvement.anomalies,
            'applique_au_stock': mouvement.applique_au_stock
        }

        return jsonify(data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/mouvement/<int:mouvement_id>/history', methods=['GET'])
@login_required
def get_mouvement_history(mouvement_id):
    """Récupère l'historique du workflow"""
    try:
        mouvement = MouvementStock.query.get_or_404(mouvement_id)

        # Récupérer les logs
        logs = AuditLog.query.filter_by(
            entity_type='MouvementStock',
            entity_id=mouvement_id
        ).order_by(AuditLog.timestamp.desc()).all()

        history = []
        for log in logs:
            history.append({
                'action': log.action,
                'user': log.user.username if log.user else 'System',
                'timestamp': log.timestamp.isoformat(),
                'details': log.details
            })

        return jsonify({
            'mouvement_id': mouvement_id,
            'history': history,
            'total_events': len(history)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ENDPOINTS - ACTIONS
# ============================================================================

@workflow_bp.route('/mouvement/<int:mouvement_id>/approve', methods=['POST'])
@login_required
@require_approval_permission()
def approve_mouvement(mouvement_id):
    """
    Approuve un mouvement de stock
    
    Body JSON:
      {
        'reason': 'Conforme bon livraison Sonatel',  # Optional
        'auto_execute': true                          # Optional - exécuter immédiatement si possible
      }
    """
    try:
        mouvement = MouvementStock.query.get_or_404(mouvement_id)
        data = request.get_json() or {}

        # Vérifier état actuel
        current_state = WorkflowState(mouvement.workflow_state)
        if current_state not in [WorkflowState.EN_ATTENTE, WorkflowState.EN_ATTENTE_DOCS]:
            return jsonify({
                'error': f"Mouvement en état {current_state.value}, ne peut pas être approuvé"
            }), 400

        # Déterminer nouvel état
        # Si en attente de docs et on a maintenant docs → passer à APPROUVE
        # Si en attente → passer à APPROUVE
        new_state = WorkflowState.APPROUVE

        # Valider transition
        is_valid, error_msg = WorkflowValidator.validate_state_transition(
            mouvement, new_state, current_user
        )
        if not is_valid:
            return jsonify({'error': error_msg}), 400

        # Appliquer la transition
        old_state, new_state_result = mouvement.change_state(new_state, current_user, data.get('reason', ''))

        # Log
        log_workflow_action(
            mouvement_id,
            'approved',
            current_user.id,
            data.get('reason', ''),
            new_state_result
        )

        db.session.commit()

        response = {
            'success': True,
            'mouvement_id': mouvement_id,
            'old_state': old_state,
            'new_state': new_state_result.value,
            'message': f"Mouvement approuvé par {current_user.username}",
            'approuve_par': current_user.username,
            'date_approbation': mouvement.date_approbation.isoformat() if mouvement.date_approbation else None
        }

        # Auto-exécuter si demandé
        if data.get('auto_execute', False):
            try:
                auto_execute_mouvement(mouvement)
                db.session.commit()
                response['auto_executed'] = True
                response['new_state'] = mouvement.workflow_state
                response['message'] += ' et exécuté'
                
                # Log
                log_workflow_action(mouvement_id, 'auto_executed', current_user.id, '', WorkflowState.EXECUTE)
            except Exception as e:
                response['auto_execute_error'] = str(e)

        return jsonify(response), 200

    except Exception as e:
        current_app.logger.error(f"Erreur approve_mouvement: {str(e)}")
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/mouvement/<int:mouvement_id>/reject', methods=['POST'])
@login_required
@require_approval_permission()
def reject_mouvement(mouvement_id):
    """
    Rejette un mouvement de stock
    
    Body JSON (required):
      {
        'reason': 'Quantité ne correspond pas au bon de livraison'
      }
    """
    try:
        mouvement = MouvementStock.query.get_or_404(mouvement_id)
        data = request.get_json() or {}

        if not data.get('reason'):
            return jsonify({'error': 'Raison du rejet requise'}), 400

        # Vérifier état actuel
        current_state = WorkflowState(mouvement.workflow_state)
        if current_state == WorkflowState.REJETE:
            return jsonify({'error': 'Mouvement déjà rejeté'}), 400

        # Passer à REJETE
        new_state = WorkflowState.REJETE

        is_valid, error_msg = WorkflowValidator.validate_state_transition(
            mouvement, new_state, current_user
        )
        if not is_valid:
            return jsonify({'error': error_msg}), 400

        # Appliquer la transition
        old_state, new_state_result = mouvement.change_state(new_state, current_user, data.get('reason'))

        # Log
        log_workflow_action(
            mouvement_id,
            'rejected',
            current_user.id,
            data.get('reason'),
            new_state_result
        )

        db.session.commit()

        return jsonify({
            'success': True,
            'mouvement_id': mouvement_id,
            'old_state': old_state,
            'new_state': new_state_result.value,
            'reason': data.get('reason'),
            'message': f"Mouvement rejeté par {current_user.username}",
            'rejeté_par': current_user.username
        }), 200

    except Exception as e:
        current_app.logger.error(f"Erreur reject_mouvement: {str(e)}")
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/mouvement/<int:mouvement_id>/validate', methods=['POST'])
@login_required
def validate_mouvement(mouvement_id):
    """
    Valide un mouvement (après vérification physique)
    
    Body JSON:
      {
        'quantite_reelle': 100,  # Quantité comptée physiquement
        'reason': 'Inventaire validé'  # Optional
      }
    """
    try:
        mouvement = MouvementStock.query.get_or_404(mouvement_id)
        data = request.get_json() or {}

        # Vérifier permissions (gestionnaire ou chef_pur)
        if current_user.role not in ['gestionnaire_stock', 'chef_pur', 'admin']:
            return jsonify({'error': 'Permissions insuffisantes'}), 403

        # Vérifier état actuel - doit être EXECUTE
        current_state = WorkflowState(mouvement.workflow_state)
        if current_state != WorkflowState.EXECUTE:
            return jsonify({'error': f"Mouvement doit être en état EXECUTE, actuellement {current_state.value}"}), 400

        # Déterminer nouvel état
        new_state = WorkflowState.VALIDE

        is_valid, error_msg = WorkflowValidator.validate_state_transition(
            mouvement, new_state, current_user
        )
        if not is_valid:
            return jsonify({'error': error_msg}), 400

        # Pour inventaire: mettre à jour quantité_reelle
        if mouvement.type_mouvement == 'inventaire' and data.get('quantite_reelle') is not None:
            mouvement.quantite_reelle = data.get('quantite_reelle')
            mouvement.ecart = mouvement.quantite_reelle - mouvement.quantite

        # Appliquer transition
        old_state, new_state_result = mouvement.change_state(new_state, current_user, data.get('reason', ''))

        # Log
        log_workflow_action(
            mouvement_id,
            'validated',
            current_user.id,
            data.get('reason', ''),
            new_state_result
        )

        db.session.commit()

        return jsonify({
            'success': True,
            'mouvement_id': mouvement_id,
            'old_state': old_state,
            'new_state': new_state_result.value,
            'message': 'Mouvement validé',
            'valide_par': current_user.username
        }), 200

    except Exception as e:
        current_app.logger.error(f"Erreur validate_mouvement: {str(e)}")
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/mouvement/<int:mouvement_id>/execute', methods=['POST'])
@login_required
def execute_mouvement(mouvement_id):
    """
    Exécute un mouvement (applique au stock)
    """
    try:
        mouvement = MouvementStock.query.get_or_404(mouvement_id)

        # Vérifier permissions
        if current_user.role not in ['gestionnaire_stock', 'chef_pur', 'admin']:
            return jsonify({'error': 'Permissions insuffisantes'}), 403

        # Vérifier état - doit être APPROUVE
        current_state = WorkflowState(mouvement.workflow_state)
        if current_state != WorkflowState.APPROUVE:
            return jsonify({'error': f"Mouvement doit être APPROUVE, actuellement {current_state.value}"}), 400

        # Exécuter le mouvement
        try:
            auto_execute_mouvement(mouvement)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        # Log
        log_workflow_action(
            mouvement_id,
            'executed',
            current_user.id,
            '',
            WorkflowState.EXECUTE
        )

        db.session.commit()

        return jsonify({
            'success': True,
            'mouvement_id': mouvement_id,
            'new_state': mouvement.workflow_state,
            'message': 'Mouvement exécuté - stock appliqué',
            'executed_by': current_user.username,
            'execution_date': mouvement.date_execution.isoformat() if mouvement.date_execution else None
        }), 200

    except Exception as e:
        current_app.logger.error(f"Erreur execute_mouvement: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# PAGES HTML
# ============================================================================

@workflow_bp.route('/gestion-stock/approvals', methods=['GET'])
@login_required
@require_stock_permission('can_view_global_stock')
def page_approvals():
    """Page de dashboard d'approbation"""
    try:
        # Récupérer mouvements en attente pour ce rôle
        pending = get_pending_by_role(current_user.role, limit=100)

        # Grouper par type
        by_type = {}
        for m in pending:
            if m.type_mouvement not in by_type:
                by_type[m.type_mouvement] = []
            by_type[m.type_mouvement].append(m)

        # Statistiques
        stats = {
            'total_pending': len(pending),
            'by_type': {k: len(v) for k, v in by_type.items()},
            'high_priority': sum(1 for m in pending if m.quantite > WORKFLOW_RULES.get(m.type_mouvement, {}).get('seuil_approbation', 0))
        }

        return render_template(
            'workflow/approvals.html',
            mouvements=pending,
            stats=stats,
            by_type=by_type
        ), 200

    except Exception as e:
        current_app.logger.error(f"Erreur page_approvals: {str(e)}")
        return jsonify({'error': str(e)}), 500
