"""
🔐 AUDIT TRAIL MODULE
Centralized audit logging for compliance and debugging.

Tracks:
- Intervention status changes
- Stock adjustments
- SLA escalations
- Leave approvals
- Critical business operations

Usage:
    from utils_audit import log_intervention_status_change
    log_intervention_status_change(intervention_id, old_status, new_status, actor_id)
"""

import json
from models import db, AuditLog
from datetime import datetime
from flask import request, current_app


def create_audit_log(
    actor_id,
    action,
    entity_type,
    entity_id,
    old_value=None,
    new_value=None,
    details=None
):
    """
    Create an audit log entry (immutable).
    
    Args:
        actor_id: User ID performing the action
        action: Action name (e.g., 'intervention_status_changed')
        entity_type: Type of entity ('intervention', 'stock', 'sla', etc.)
        entity_id: ID of the entity
        old_value: Dict of previous state
        new_value: Dict of new state
        details: Dict of additional context
    
    Returns:
        AuditLog instance or None if error
    """
    try:
        audit = AuditLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=json.dumps(old_value) if old_value else None,
            new_value=json.dumps(new_value) if new_value else None,
            details=json.dumps(details) if details else None,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent', '')[:255] if request else None,
            created_at=datetime.utcnow()
        )
        db.session.add(audit)
        db.session.commit()
        return audit
    except Exception as e:
        db.session.rollback()
        if current_app:
            current_app.logger.error(f"[AUDIT] Failed to log {action}: {str(e)}")
        return None


# ============================================================
# INTERVENTION AUDIT FUNCTIONS
# ============================================================

def log_intervention_status_change(intervention_id, old_status, new_status, actor_id, reason=None):
    """
    Log intervention status change.
    
    Example:
        log_intervention_status_change(42, 'en_cours', 'valide', user_id, 'Completed by tech')
    """
    return create_audit_log(
        actor_id=actor_id,
        action='intervention_status_changed',
        entity_type='intervention',
        entity_id=intervention_id,
        old_value={'statut': old_status},
        new_value={'statut': new_status},
        details={'reason': reason} if reason else None
    )


def log_intervention_assignment(intervention_id, old_tech_id, new_tech_id, actor_id, reason=None):
    """Log intervention assignment to technician."""
    return create_audit_log(
        actor_id=actor_id,
        action='intervention_assigned',
        entity_type='intervention',
        entity_id=intervention_id,
        old_value={'technicien_id': old_tech_id},
        new_value={'technicien_id': new_tech_id},
        details={'reason': reason}
    )


def log_intervention_validation(intervention_id, validator_id, approved=True, comment=None):
    """Log intervention manager approval/rejection."""
    return create_audit_log(
        actor_id=validator_id,
        action='intervention_validated' if approved else 'intervention_rejected',
        entity_type='intervention',
        entity_id=intervention_id,
        new_value={'validated': approved},
        details={'comment': comment} if comment else None
    )


# ============================================================
# STOCK AUDIT FUNCTIONS
# ============================================================

def log_stock_adjustment(produit_id, old_qty, new_qty, actor_id, reason=None):
    """
    Log stock quantity change.
    
    Example:
        log_stock_adjustment(produit_id, 100, 85, user_id, 'Removed for job #42')
    """
    return create_audit_log(
        actor_id=actor_id,
        action='stock_adjusted',
        entity_type='stock',
        entity_id=produit_id,
        old_value={'quantity': old_qty},
        new_value={'quantity': new_qty},
        details={
            'change': new_qty - old_qty,
            'reason': reason
        }
    )


def log_stock_entry(produit_id, quantity, actor_id, supplier=None, invoice_num=None):
    """Log stock entry (purchase/receipt)."""
    return create_audit_log(
        actor_id=actor_id,
        action='stock_entry',
        entity_type='stock',
        entity_id=produit_id,
        new_value={'quantity_added': quantity},
        details={
            'supplier': supplier,
            'invoice': invoice_num
        }
    )


def log_stock_removal(produit_id, quantity, actor_id, reason=None):
    """Log stock removal (usage/loss)."""
    return create_audit_log(
        actor_id=actor_id,
        action='stock_removal',
        entity_type='stock',
        entity_id=produit_id,
        new_value={'quantity_removed': quantity},
        details={'reason': reason}
    )


# ============================================================
# SLA AUDIT FUNCTIONS
# ============================================================

def log_sla_escalation(intervention_id, actor_id, priority=None, reason=None):
    """Log SLA escalation alert."""
    return create_audit_log(
        actor_id=actor_id,
        action='sla_escalated',
        entity_type='sla',
        entity_id=intervention_id,
        new_value={'escalated': True, 'priority': priority},
        details={'reason': reason}
    )


def log_sla_breach(intervention_id, actor_id, sla_hours=None, actual_hours=None):
    """Log SLA breach (deadline missed)."""
    return create_audit_log(
        actor_id=actor_id,
        action='sla_breached',
        entity_type='sla',
        entity_id=intervention_id,
        new_value={
            'sla_hours': sla_hours,
            'actual_hours': actual_hours,
            'breached': True
        }
    )


# ============================================================
# LEAVE AUDIT FUNCTIONS
# ============================================================

def log_leave_request_created(leave_id, technicien_id, actor_id, business_days=None):
    """Log leave request creation."""
    return create_audit_log(
        actor_id=actor_id,
        action='leave_request_created',
        entity_type='leave_request',
        entity_id=leave_id,
        new_value={'technicien_id': technicien_id, 'business_days': business_days}
    )


def log_leave_approval(leave_id, approved=True, actor_id=None, comment=None):
    """Log leave approval/rejection."""
    return create_audit_log(
        actor_id=actor_id,
        action='leave_approved' if approved else 'leave_rejected',
        entity_type='leave_request',
        entity_id=leave_id,
        new_value={'status': 'approved' if approved else 'rejected'},
        details={'comment': comment}
    )


# ============================================================
# AUDIT QUERY FUNCTIONS (Read-Only)
# ============================================================

def get_entity_audit_trail(entity_type, entity_id, limit=100):
    """
    Get complete audit trail for an entity.
    
    Returns: List of audit logs, newest first
    """
    try:
        logs = AuditLog.query.filter_by(
            entity_type=entity_type,
            entity_id=entity_id
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
        
        return [
            {
                'id': log.id,
                'actor': {
                    'id': log.actor.id,
                    'username': log.actor.username,
                    'nom': log.actor.nom,
                    'prenom': log.actor.prenom
                },
                'action': log.action,
                'old_value': json.loads(log.old_value) if log.old_value else None,
                'new_value': json.loads(log.new_value) if log.new_value else None,
                'details': json.loads(log.details) if log.details else None,
                'created_at': log.created_at.isoformat() if log.created_at else None,
                'ip_address': log.ip_address
            }
            for log in logs
        ]
    except Exception as e:
        if current_app:
            current_app.logger.error(f"[AUDIT] Error reading trail: {str(e)}")
        return []


def get_user_audit_trail(user_id, limit=100):
    """Get all audit entries created by a specific user."""
    try:
        logs = AuditLog.query.filter_by(
            actor_id=user_id
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
        
        return [
            {
                'id': log.id,
                'action': log.action,
                'entity_type': log.entity_type,
                'entity_id': log.entity_id,
                'created_at': log.created_at.isoformat(),
                'details': json.loads(log.details) if log.details else None
            }
            for log in logs
        ]
    except Exception as e:
        if current_app:
            current_app.logger.error(f"[AUDIT] Error reading user trail: {str(e)}")
        return []


def get_recent_audit_logs(days=7, limit=500):
    """Get recent audit logs for dashboard/reporting."""
    from datetime import timedelta
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        logs = AuditLog.query.filter(
            AuditLog.created_at >= cutoff
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
        
        return [
            {
                'id': log.id,
                'actor': log.actor.username if log.actor else 'unknown',
                'action': log.action,
                'entity_type': log.entity_type,
                'entity_id': log.entity_id,
                'created_at': log.created_at.isoformat(),
            }
            for log in logs
        ]
    except Exception as e:
        if current_app:
            current_app.logger.error(f"[AUDIT] Error reading recent logs: {str(e)}")
        return []


def get_action_summary(days=7):
    """
    Get summary of actions taken in recent period.
    Returns: Dict with action counts
    """
    from datetime import timedelta
    from sqlalchemy import func
    
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        summary = db.session.query(
            AuditLog.action,
            func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.created_at >= cutoff
        ).group_by(AuditLog.action).all()
        
        return {action: count for action, count in summary}
    except Exception as e:
        if current_app:
            current_app.logger.error(f"[AUDIT] Error calculating summary: {str(e)}")
        return {}
