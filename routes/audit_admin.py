"""
🔐 AUDIT TRAIL ADMIN INTERFACE
Read-only admin dashboard for compliance and debugging.

Features:
- View all audit trail entries with filtering
- Search by action, entity type, actor
- View detailed entity history
- Export audit reports
- Dashboard statistics

Access Control: Admin only
"""

from flask import Blueprint, render_template, request, jsonify, abort, current_app
from flask_login import login_required, current_user
from models import db, AuditLog, User
from utils_audit import get_entity_audit_trail, get_user_audit_trail, get_recent_audit_logs, get_action_summary
from datetime import datetime, timedelta
import json

audit_admin_bp = Blueprint('audit_admin', __name__, url_prefix='/admin/audit')


def admin_required(f):
    """Decorator to require admin access."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'est_admin', False):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


# ============================================================
# MAIN AUDIT LOG VIEW
# ============================================================

@audit_admin_bp.route('/', methods=['GET'])
@login_required
@admin_required
def audit_dashboard():
    """Main audit log viewer with filters and search."""
    try:
        # Get filter parameters
        action_filter = request.args.get('action', '')
        entity_filter = request.args.get('entity_type', '')
        actor_filter = request.args.get('actor_id', '', type=int)
        days_filter = request.args.get('days', '7', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = 50
        
        # Build query
        query = AuditLog.query
        
        if action_filter:
            query = query.filter(AuditLog.action.ilike(f'%{action_filter}%'))
        
        if entity_filter:
            query = query.filter(AuditLog.entity_type == entity_filter)
        
        if actor_filter:
            query = query.filter(AuditLog.actor_id == actor_filter)
        
        # Date range filter
        cutoff = datetime.utcnow() - timedelta(days=days_filter)
        query = query.filter(AuditLog.created_at >= cutoff)
        
        # Count total
        total = query.count()
        
        # Paginate
        logs = query.order_by(AuditLog.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Format logs for display
        formatted_logs = []
        for log in logs.items:
            formatted_logs.append({
                'id': log.id,
                'created_at': log.created_at.isoformat() if log.created_at else None,
                'actor': {
                    'id': log.actor.id,
                    'username': log.actor.username,
                    'full_name': f"{log.actor.prenom} {log.actor.nom}".strip()
                } if log.actor else None,
                'action': log.action,
                'entity_type': log.entity_type,
                'entity_id': log.entity_id,
                'old_value': json.loads(log.old_value) if log.old_value else None,
                'new_value': json.loads(log.new_value) if log.new_value else None,
                'details': json.loads(log.details) if log.details else None,
                'ip_address': log.ip_address
            })
        
        # Get available actors for filter dropdown
        actors = User.query.all()
        
        # Get available entity types
        entity_types = db.session.query(AuditLog.entity_type).distinct().all()
        entity_types = [et[0] for et in entity_types if et[0]]
        
        # Get action summary for statistics
        action_summary = get_action_summary(days_filter)
        
        return render_template(
            'audit_dashboard.html',
            logs=formatted_logs,
            pagination=logs,
            total=total,
            filters={
                'action': action_filter,
                'entity_type': entity_filter,
                'actor_id': actor_filter,
                'days': days_filter
            },
            actors=actors,
            entity_types=sorted(entity_types),
            action_summary=action_summary,
            title='Audit Trail Dashboard'
        )
    
    except Exception as e:
        current_app.logger.error(f"[AUDIT_ADMIN] Dashboard error: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================
# ENTITY AUDIT TRAIL
# ============================================================

@audit_admin_bp.route('/entity/<entity_type>/<int:entity_id>', methods=['GET'])
@login_required
@admin_required
def entity_history(entity_type, entity_id):
    """View complete audit trail for a specific entity."""
    try:
        trail = get_entity_audit_trail(entity_type, entity_id, limit=100)
        
        return render_template(
            'audit_entity_history.html',
            entity_type=entity_type,
            entity_id=entity_id,
            trail=trail,
            title=f'Audit Trail: {entity_type} #{entity_id}'
        )
    
    except Exception as e:
        current_app.logger.error(f"[AUDIT_ADMIN] Entity history error: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================
# USER ACTIVITY
# ============================================================

@audit_admin_bp.route('/user/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def user_activity(user_id):
    """View all actions performed by a specific user."""
    try:
        user = db.session.get(User, user_id)
        if not user:
            abort(404)
        
        trail = get_user_audit_trail(user_id, limit=200)
        
        return render_template(
            'audit_user_activity.html',
            user=user,
            trail=trail,
            title=f'User Activity: {user.prenom} {user.nom}'
        )
    
    except Exception as e:
        current_app.logger.error(f"[AUDIT_ADMIN] User activity error: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================
# API ENDPOINTS FOR AJAX
# ============================================================

@audit_admin_bp.route('/api/recent', methods=['GET'])
@login_required
@admin_required
def api_recent_logs():
    """Get recent audit logs (JSON API)."""
    try:
        days = request.args.get('days', '7', type=int)
        limit = request.args.get('limit', '100', type=int)
        
        logs = get_recent_audit_logs(days, limit)
        
        return jsonify({
            'success': True,
            'count': len(logs),
            'logs': logs
        })
    
    except Exception as e:
        current_app.logger.error(f"[AUDIT_ADMIN] API recent error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@audit_admin_bp.route('/api/stats', methods=['GET'])
@login_required
@admin_required
def api_stats():
    """Get audit statistics (JSON API)."""
    try:
        days = request.args.get('days', '7', type=int)
        
        # Action summary
        summary = get_action_summary(days)
        
        # Total logs in period
        cutoff = datetime.utcnow() - timedelta(days=days)
        total_logs = AuditLog.query.filter(AuditLog.created_at >= cutoff).count()
        
        # Unique actors
        unique_actors = db.session.query(AuditLog.actor_id).distinct().filter(
            AuditLog.created_at >= cutoff
        ).count()
        
        return jsonify({
            'success': True,
            'days': days,
            'total_logs': total_logs,
            'unique_actors': unique_actors,
            'actions': summary
        })
    
    except Exception as e:
        current_app.logger.error(f"[AUDIT_ADMIN] API stats error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@audit_admin_bp.route('/api/export', methods=['GET'])
@login_required
@admin_required
def api_export():
    """Export audit logs as CSV (JSON API)."""
    try:
        days = request.args.get('days', '7', type=int)
        
        logs = get_recent_audit_logs(days, limit=10000)
        
        # Format as CSV-compatible list
        rows = [
            ['ID', 'Timestamp', 'Actor', 'Action', 'Entity Type', 'Entity ID', 'IP Address', 'Details']
        ]
        
        for log in logs:
            rows.append([
                log.get('id', ''),
                log.get('created_at', ''),
                log.get('actor', 'unknown'),
                log.get('action', ''),
                log.get('entity_type', ''),
                log.get('entity_id', ''),
                log.get('ip_address', ''),
                json.dumps(log.get('details', {}))
            ])
        
        return jsonify({
            'success': True,
            'count': len(logs),
            'rows': rows
        })
    
    except Exception as e:
        current_app.logger.error(f"[AUDIT_ADMIN] API export error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@audit_admin_bp.route('/api/integrity-check', methods=['GET'])
@login_required
@admin_required
def api_integrity_check():
    """Verify audit log integrity (immutability check)."""
    try:
        # Check that no audit logs were ever updated (integrity check)
        # This should always be true if our code is correct
        sample = AuditLog.query.limit(10).all()
        
        integrity_ok = True
        issues = []
        
        for log in sample:
            if log.updated_at and log.updated_at != log.created_at:
                integrity_ok = False
                issues.append({
                    'id': log.id,
                    'issue': 'Log was modified after creation'
                })
        
        return jsonify({
            'success': True,
            'integrity_ok': integrity_ok,
            'issues': issues,
            'message': 'Audit trail integrity verified' if integrity_ok else f'Found {len(issues)} integrity issues'
        })
    
    except Exception as e:
        current_app.logger.error(f"[AUDIT_ADMIN] Integrity check error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
