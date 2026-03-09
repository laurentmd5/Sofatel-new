"""
RH Module - Human Resources workflows
- Leave request management (pending → approved/rejected)
- Leave validation (overlap detection, business days calculation)
- Manager approval workflow
- Hours tracking and reporting
- Audit trail integration
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from models import db, User, Intervention, LeaveRequest, AuditLog, NoteRH
from datetime import datetime, timedelta, timezone
from sqlalchemy import desc
from dateutil import parser as date_parser
import json
from math import ceil

rh_bp = Blueprint('rh', __name__)

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def log_audit(action, entity_type, entity_id, old_value=None, new_value=None, details=None):
    """
    Create audit log entry for compliance and debugging.
    """
    try:
        audit = AuditLog(
            actor_id=current_user.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=json.dumps(old_value) if old_value else None,
            new_value=json.dumps(new_value) if new_value else None,
            details=json.dumps(details) if details else None,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:255]
        )
        db.session.add(audit)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"[AUDIT] Failed to log {action}: {str(e)}")


def calculate_business_days(start_date, end_date):
    """
    Calculate business days (Monday-Friday) between two dates.
    Excludes weekends.
    """
    business_days = 0
    current = start_date
    while current <= end_date:
        # Monday = 0, Friday = 4, Saturday = 5, Sunday = 6
        if current.weekday() < 5:
            business_days += 1
        current += timedelta(days=1)
    return business_days


def check_leave_overlap(technicien_id, date_debut, date_fin, exclude_id=None):
    """
    Check if requested leave overlaps with approved leaves.
    Returns: (has_overlap, overlapping_leaves)
    """
    query = LeaveRequest.query.filter(
        LeaveRequest.technicien_id == technicien_id,
        LeaveRequest.statut == 'approved'
    )
    
    if exclude_id:
        query = query.filter(LeaveRequest.id != exclude_id)
    
    overlapping = []
    for leave in query.all():
        # Check if dates overlap
        if not (date_fin < leave.date_debut or date_debut > leave.date_fin):
            overlapping.append(leave)
    
    return len(overlapping) > 0, overlapping


# ============================================================
# LEAVE REQUEST ENDPOINTS
# ============================================================

@rh_bp.route('/conges', methods=['POST'])
@login_required
def create_leave():
    """
    Create a new leave request.
    
    ✅ NOUVEAU: SEULS les techniciens peuvent créer une demande de congé
    pour eux-mêmes. Les gestionnaires RH ne peuvent QUE valider/approuver.
    
    Request JSON:
    {
        "date_debut": "2026-02-01",
        "date_fin": "2026-02-05",
        "type": "conge_paye",  // conge_paye, conge_sans_solde, absence, maladie
        "reason": "Vacation"
    }
    
    Validates:
    - Only 'technicien' role can create
    - Dates are valid and in future
    - No overlap with existing approved leaves
    """
    # ✅ NOUVEAU: Vérification stricte des rôles - SEULS technicien peuvent créer
    if current_user.role != 'technicien':
        return jsonify({
            'success': False,
            'error': 'Seuls les techniciens peuvent soumettre une demande de congé. ' \
                     'Les gestionnaires RH doivent valider les demandes existantes.'
        }), 403
    
    data = request.get_json() or {}
    # ✅ NOUVEAU: Force technicien_id = current_user.id, ignore le paramètre
    technicien_id = current_user.id  # Toujours l'utilisateur courant
    
    start_str = data.get('date_debut')
    end_str = data.get('date_fin')
    leave_type = data.get('type', 'conge_paye')
    reason = data.get('reason', '')
    
    # Validation: required fields
    if not start_str or not end_str:
        return jsonify({'success': False, 'error': 'Missing required fields: date_debut, date_fin'}), 400
    
    # Validation: date format
    try:
        start_date = datetime.fromisoformat(start_str).date()
        end_date = datetime.fromisoformat(end_str).date()
    except Exception:
        return jsonify({'success': False, 'error': 'Invalid date format, use YYYY-MM-DD'}), 400
    
    # Validation: date order
    if start_date > end_date:
        return jsonify({'success': False, 'error': 'Start date must be before end date'}), 400
    
    # Validation: dates in future
    if start_date < datetime.utcnow().date():
        return jsonify({'success': False, 'error': 'Leave request must be for future dates'}), 400
    
    # Validation: no overlap with approved leaves
    has_overlap, overlapping = check_leave_overlap(technicien_id, start_date, end_date)
    if has_overlap:
        return jsonify({
            'success': False,
            'error': 'Leave overlaps with existing approved leave',
            'conflicting_dates': [
                {
                    'id': l.id,
                    'date_debut': l.date_debut.isoformat(),
                    'date_fin': l.date_fin.isoformat()
                }
                for l in overlapping
            ]
        }), 409
    
    try:
        # Calculate business days
        business_days = calculate_business_days(start_date, end_date)
        
        # Create leave request
        leave_request = LeaveRequest(
            technicien_id=technicien_id,
            date_debut=start_date,
            date_fin=end_date,
            type=leave_type,
            reason=reason,
            statut='pending',
            business_days_count=business_days,
            created_at=datetime.utcnow()
        )
        db.session.add(leave_request)
        db.session.flush()  # Get ID before commit
        db.session.commit()
        
        # Log audit
        log_audit(
            action='leave_request_created',
            entity_type='leave_request',
            entity_id=leave_request.id,
            new_value={
                'technicien_id': technicien_id,
                'date_debut': start_date.isoformat(),
                'date_fin': end_date.isoformat(),
                'type': leave_type,
                'business_days': business_days
            },
            details={'reason': reason}
        )
        
        return jsonify({
            'success': True,
            'id': leave_request.id,
            'statut': leave_request.statut,
            'business_days': business_days,
            'message': 'Leave request submitted successfully'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception('Error creating leave request')
        
        # Provide user-friendly error messages
        error_msg = str(e).lower()
        if 'field' in error_msg or 'column' in error_msg:
            user_msg = 'Erreur technique de base de données. Contactez l\'administrateur.'
        elif 'operational error' in error_msg or 'integrity error' in error_msg:
            user_msg = 'Erreur lors de l\'enregistrement de la demande de congé. Réessayez.'
        else:
            user_msg = 'Une erreur est survenue lors de la création de la demande. Contactez l\'administrateur.'
        
        return jsonify({'success': False, 'error': user_msg}), 500


@rh_bp.route('/conges', methods=['GET'])
@login_required
def list_leaves():
    """
    List leave requests with filtering.
    
    Query params:
    - statut: pending|approved|rejected|cancelled
    - technicien_id: Filter by employee
    - page: Pagination
    - per_page: Results per page
    """
    statut = request.args.get('statut', '')
    technicien_id = request.args.get('technicien_id', type=int)
    page = max(1, request.args.get('page', 1, type=int))
    per_page = min(100, max(5, request.args.get('per_page', 20, type=int)))
    
    query = LeaveRequest.query
    
    # Filter by status if provided
    if statut:
        query = query.filter(LeaveRequest.statut == statut)
    
    # Filter by technicien
    if technicien_id:
        query = query.filter(LeaveRequest.technicien_id == technicien_id)
    elif current_user.role == 'technicien':
        # Technicians can only see their own leaves
        query = query.filter(LeaveRequest.technicien_id == current_user.id)
    
    total = query.count()
    total_pages = ceil(total / per_page) if per_page else 1
    
    leaves = query.order_by(LeaveRequest.created_at.desc()) \
                  .offset((page - 1) * per_page) \
                  .limit(per_page) \
                  .all()
    
    result = []
    for l in leaves:
        result.append({
            'id': l.id,
            'technicien_id': l.technicien_id,
            'technicien': {
                'id': l.technicien.id,
                'username': l.technicien.username,
                'nom': l.technicien.nom,
                'prenom': l.technicien.prenom
            },
            'date_debut': l.date_debut.isoformat(),
            'date_fin': l.date_fin.isoformat(),
            'type': l.type,
            'reason': l.reason,
            'statut': l.statut,
            'business_days': l.business_days_count,
            'created_at': l.created_at.isoformat(),
            'approved_at': l.approved_at.isoformat() if l.approved_at else None,
            'manager': {
                'id': l.manager.id,
                'username': l.manager.username
            } if l.manager else None,
            'manager_comment': l.manager_comment
        })
    
    return jsonify({
        'success': True,
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'leaves': result
    })


@rh_bp.route('/conges/<int:leave_id>', methods=['GET'])
@login_required
def get_leave(leave_id):
    """Get leave request details."""
    leave = db.session.get(LeaveRequest, leave_id)
    if not leave:
        return jsonify({'success': False, 'error': 'Leave request not found'}), 404
    
    # Permission check
    if current_user.role == 'technicien' and leave.technicien_id != current_user.id:
        return jsonify({'success': False, 'error': 'You cannot view other employees\' leave requests'}), 403
    
    return jsonify({
        'success': True,
        'leave': {
            'id': leave.id,
            'technicien': {
                'id': leave.technicien.id,
                'username': leave.technicien.username,
                'nom': leave.technicien.nom,
                'prenom': leave.technicien.prenom
            },
            'date_debut': leave.date_debut.isoformat(),
            'date_fin': leave.date_fin.isoformat(),
            'type': leave.type,
            'reason': leave.reason,
            'business_days': leave.business_days_count,
            'statut': leave.statut,
            'created_at': leave.created_at.isoformat(),
            'updated_at': leave.updated_at.isoformat(),
            'approved_at': leave.approved_at.isoformat() if leave.approved_at else None,
            'manager': {
                'id': leave.manager.id,
                'username': leave.manager.username,
                'nom': leave.manager.nom,
                'prenom': leave.manager.prenom
            } if leave.manager else None,
            'manager_comment': leave.manager_comment
        }
    })


@rh_bp.route('/conges/<int:leave_id>', methods=['PUT'])
@login_required
def approve_leave(leave_id):
    """
    Approve or reject a leave request.
    Only managers/admins allowed.
    
    Request JSON:
    {
        "statut": "approved" or "rejected",
        "comment": "Optional comment from manager"
    }
    """
    # Permission check
    if current_user.role not in ['rh', 'chef_pur', 'chef_pilote', 'admin']:
        return jsonify({'success': False, 'error': 'Only managers can approve leave'}), 403
    
    leave = db.session.get(LeaveRequest, leave_id)
    if not leave:
        return jsonify({'success': False, 'error': 'Leave request not found'}), 404
    
    # Validation: only pending requests can be approved
    if leave.statut != 'pending':
        return jsonify({'success': False, 'error': f'Cannot approve {leave.statut} request'}), 409
    
    data = request.get_json() or {}
    new_status = data.get('statut', '').lower()
    manager_comment = data.get('comment', '')
    
    if new_status not in ['approved', 'rejected']:
        return jsonify({'success': False, 'error': 'Status must be "approved" or "rejected"'}), 400
    
    try:
        # For approval, re-validate overlap (in case other leaves were approved in the meantime)
        if new_status == 'approved':
            has_overlap, overlapping = check_leave_overlap(
                leave.technicien_id,
                leave.date_debut,
                leave.date_fin,
                exclude_id=leave.id
            )
            if has_overlap:
                return jsonify({
                    'success': False,
                    'error': 'Cannot approve: leave overlaps with other approved leave',
                    'conflicting_dates': [
                        {
                            'id': l.id,
                            'date_debut': l.date_debut.isoformat(),
                            'date_fin': l.date_fin.isoformat()
                        }
                        for l in overlapping
                    ]
                }), 409
        
        # Store old value for audit
        old_value = {
            'statut': leave.statut,
            'manager_id': leave.manager_id,
            'manager_comment': leave.manager_comment
        }
        
        # Update leave request
        leave.statut = new_status
        leave.manager_id = current_user.id
        leave.manager_comment = manager_comment
        leave.approved_at = datetime.utcnow()
        leave.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Log audit
        log_audit(
            action=f'leave_{new_status}',
            entity_type='leave_request',
            entity_id=leave.id,
            old_value=old_value,
            new_value={
                'statut': new_status,
                'manager_id': current_user.id,
                'manager_comment': manager_comment,
                'approved_at': datetime.utcnow().isoformat()
            }
        )
        
        return jsonify({
            'success': True,
            'id': leave.id,
            'statut': leave.statut,
            'message': f'Leave request {new_status} successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception('Error approving leave')
        
        # Provide user-friendly error messages
        error_msg = str(e).lower()
        if 'field' in error_msg or 'column' in error_msg:
            user_msg = 'Erreur technique de base de données. Contactez l\'administrateur.'
        elif 'operational error' in error_msg or 'integrity error' in error_msg:
            user_msg = 'Erreur lors de la validation de la demande. Réessayez.'
        else:
            user_msg = 'Une erreur est survenue lors de la validation. Contactez l\'administrateur.'
        
        return jsonify({'success': False, 'error': user_msg}), 500


# ============================================================
# LEAVE CONFLICT CHECKING
# ============================================================

@rh_bp.route('/leave/check-conflicts', methods=['POST'])
@login_required
def check_conflicts():
    """
    Check if requested leave dates conflict with:
    1. Other approved leaves for the user
    2. Scheduled interventions
    
    Request JSON:
    {
        "date_debut": "2026-02-18",
        "date_fin": "2026-02-22"
    }
    
    Response:
    {
        "success": true,
        "conflicts": [
            {
                "id": 1,
                "type": "leave",
                "date_debut": "2026-02-20",
                "date_fin": "2026-02-25",
                "technicien": "John Doe"
            }
        ],
        "interventions": [
            {
                "id": 5,
                "date": "2026-02-20",
                "description": "Intervention Site X",
                "numero": "INT-001"
            }
        ]
    }
    """
    # ✅ Only technicians check their own conflicts
    # Manager/RH can also call this to verify before approving
    
    try:
        data = request.get_json() or {}
        start_str = data.get('date_debut')
        end_str = data.get('date_fin')
        
        # Validation: required fields
        if not start_str or not end_str:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: date_debut, date_fin'
            }), 400
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(start_str).date()
            end_date = datetime.fromisoformat(end_str).date()
        except Exception:
            return jsonify({
                'success': False,
                'error': 'Invalid date format, use YYYY-MM-DD'
            }), 400
        
        # Default to current user (technician)
        # But allow queries for verification purposes
        technicien_id = request.args.get('technicien_id', current_user.id, type=int)
        
        # Permission: only your own or if manager
        if technicien_id != current_user.id:
            if current_user.role not in ['rh', 'chef_pur', 'chef_pilote', 'admin']:
                return jsonify({
                    'success': False,
                    'error': 'You can only check your own leave conflicts'
                }), 403
        
        # ============= FIND CONFLICTING APPROVED LEAVES =============
        conflicting_leaves = LeaveRequest.query.filter(
            LeaveRequest.technicien_id == technicien_id,
            LeaveRequest.statut == 'approved'
        ).all()
        
        conflicts = []
        for leave in conflicting_leaves:
            # Check if dates overlap
            if not (end_date < leave.date_debut or start_date > leave.date_fin):
                conflicts.append({
                    'id': leave.id,
                    'type': 'leave',
                    'date_debut': leave.date_debut.isoformat(),
                    'date_fin': leave.date_fin.isoformat(),
                    'technicien': f"{leave.technicien.prenom} {leave.technicien.nom}",
                    'reason': leave.reason
                })
        
        # ============= FIND CONFLICTING INTERVENTIONS =============
        # Interventions have date_debut and date_fin (datetime, not date)
        conflicting_interventions = Intervention.query.filter(
            Intervention.technicien_id == technicien_id,
            Intervention.date_debut != None,
            Intervention.date_fin != None,
            Intervention.statut.in_(['affecte', 'en_cours', 'termine'])  # Active states
        ).all()
        
        interventions = []
        for intervention in conflicting_interventions:
            # Convert datetime to date for comparison
            int_start = intervention.date_debut.date() if isinstance(intervention.date_debut, datetime) else intervention.date_debut
            int_end = intervention.date_fin.date() if isinstance(intervention.date_fin, datetime) else intervention.date_fin
            
            # Check if dates overlap
            if not (end_date < int_start or start_date > int_end):
                interventions.append({
                    'id': intervention.id,
                    'date_debut': intervention.date_debut.isoformat(),
                    'date_fin': intervention.date_fin.isoformat(),
                    'numero': intervention.numero or 'N/A',
                    'statut': intervention.statut
                })
        
        return jsonify({
            'success': True,
            'conflicts': conflicts,
            'interventions': interventions,
            'has_conflicts': len(conflicts) > 0 or len(interventions) > 0
        }), 200
    
    except Exception as e:
        current_app.logger.exception('Error checking leave conflicts')
        return jsonify({
            'success': False,
            'error': 'Error checking conflicts: ' + str(e)
        }), 500


# ============================================================
# BATCH APPROVAL/REJECTION
# ============================================================

@rh_bp.route('/leave/bulk-approve', methods=['POST'])
@login_required
def bulk_approve_leaves():
    """
    Approve multiple leave requests in batch.
    Only managers can approve.
    
    Request JSON:
    {
        "leave_ids": [1, 2, 5, 7],
        "comment": "Approuvé en batch"  // Optional
    }
    
    Response:
    {
        "success": true,
        "approved": 4,
        "failed": 0,
        "errors": [],
        "message": "4 demandes approuvées avec succès"
    }
    """
    # Permission check: only managers
    if current_user.role not in ['rh', 'chef_pur', 'chef_pilote', 'admin']:
        return jsonify({
            'success': False,
            'error': 'Only managers can approve leave requests'
        }), 403
    
    try:
        data = request.get_json() or {}
        leave_ids = data.get('leave_ids', [])
        comment = data.get('comment', '')
        
        # Validation
        if not leave_ids:
            return jsonify({
                'success': False,
                'error': 'Missing required field: leave_ids'
            }), 400
        
        if not isinstance(leave_ids, list):
            return jsonify({
                'success': False,
                'error': 'leave_ids must be an array'
            }), 400
        
        # Process each leave
        approved_count = 0
        failed_count = 0
        errors = []
        approved_ids = []
        
        for leave_id in leave_ids:
            try:
                leave = db.session.get(LeaveRequest, leave_id)
                
                if not leave:
                    errors.append(f"Leave {leave_id}: not found")
                    failed_count += 1
                    continue
                
                if leave.statut != 'pending':
                    errors.append(f"Leave {leave_id}: status is {leave.statut} (not pending)")
                    failed_count += 1
                    continue
                
                # Re-validate overlap (in case other leaves were approved)
                has_overlap, overlapping = check_leave_overlap(
                    leave.technicien_id,
                    leave.date_debut,
                    leave.date_fin,
                    exclude_id=leave.id
                )
                
                if has_overlap:
                    errors.append(f"Leave {leave_id}: overlaps with other approved leaves")
                    failed_count += 1
                    continue
                
                # Approve
                leave.statut = 'approved'
                leave.manager_id = current_user.id
                leave.manager_comment = comment
                leave.approved_at = datetime.utcnow()
                leave.updated_at = datetime.utcnow()
                db.session.add(leave)
                
                # Log audit
                log_audit(
                    action='leave_approved_bulk',
                    entity_type='leave_request',
                    entity_id=leave.id,
                    old_value={'statut': 'pending'},
                    new_value={'statut': 'approved', 'manager_comment': comment}
                )
                
                approved_count += 1
                approved_ids.append(leave_id)
            
            except Exception as e:
                current_app.logger.exception(f'Error approving leave {leave_id}')
                errors.append(f"Leave {leave_id}: {str(e)}")
                failed_count += 1
        
        # Commit all changes
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception('Error committing bulk approval')
            return jsonify({
                'success': False,
                'error': f'Database error: {str(e)}',
                'approved': approved_count,
                'failed': failed_count
            }), 500
        
        return jsonify({
            'success': True,
            'approved': approved_count,
            'failed': failed_count,
            'approved_ids': approved_ids,
            'errors': errors,
            'message': f'{approved_count} demande(s) approuvée(s)' + (
                f' ({failed_count} failed)' if failed_count > 0 else ''
            )
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception('Error in bulk approve')
        return jsonify({
            'success': False,
            'error': f'Error: {str(e)}'
        }), 500


@rh_bp.route('/leave/bulk-reject', methods=['POST'])
@login_required
def bulk_reject_leaves():
    """
    Reject multiple leave requests in batch.
    Only managers can reject.
    
    Request JSON:
    {
        "leave_ids": [1, 2, 5],
        "comment": "Rejeté pour raison X"  // Required
    }
    
    Response:
    {
        "success": true,
        "rejected": 3,
        "failed": 0,
        "errors": [],
        "message": "3 demandes rejetées"
    }
    """
    # Permission check: only managers
    if current_user.role not in ['rh', 'chef_pur', 'chef_pilote', 'admin']:
        return jsonify({
            'success': False,
            'error': 'Only managers can reject leave requests'
        }), 403
    
    try:
        data = request.get_json() or {}
        leave_ids = data.get('leave_ids', [])
        comment = data.get('comment', '')
        
        # Validation
        if not leave_ids:
            return jsonify({
                'success': False,
                'error': 'Missing required field: leave_ids'
            }), 400
        
        if not isinstance(leave_ids, list):
            return jsonify({
                'success': False,
                'error': 'leave_ids must be an array'
            }), 400
        
        if not comment or len(comment.strip()) == 0:
            return jsonify({
                'success': False,
                'error': 'Rejection reason (comment) is required'
            }), 400
        
        # Process each leave
        rejected_count = 0
        failed_count = 0
        errors = []
        rejected_ids = []
        
        for leave_id in leave_ids:
            try:
                leave = db.session.get(LeaveRequest, leave_id)
                
                if not leave:
                    errors.append(f"Leave {leave_id}: not found")
                    failed_count += 1
                    continue
                
                if leave.statut != 'pending':
                    errors.append(f"Leave {leave_id}: status is {leave.statut} (not pending)")
                    failed_count += 1
                    continue
                
                # Reject
                leave.statut = 'rejected'
                leave.manager_id = current_user.id
                leave.manager_comment = comment
                leave.approved_at = datetime.utcnow()  # Track when decision was made
                leave.updated_at = datetime.utcnow()
                db.session.add(leave)
                
                # Log audit
                log_audit(
                    action='leave_rejected_bulk',
                    entity_type='leave_request',
                    entity_id=leave.id,
                    old_value={'statut': 'pending'},
                    new_value={'statut': 'rejected', 'manager_comment': comment}
                )
                
                rejected_count += 1
                rejected_ids.append(leave_id)
            
            except Exception as e:
                current_app.logger.exception(f'Error rejecting leave {leave_id}')
                errors.append(f"Leave {leave_id}: {str(e)}")
                failed_count += 1
        
        # Commit all changes
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception('Error committing bulk rejection')
            return jsonify({
                'success': False,
                'error': f'Database error: {str(e)}',
                'rejected': rejected_count,
                'failed': failed_count
            }), 500
        
        return jsonify({
            'success': True,
            'rejected': rejected_count,
            'failed': failed_count,
            'rejected_ids': rejected_ids,
            'errors': errors,
            'message': f'{rejected_count} demande(s) rejetée(s)' + (
                f' ({failed_count} failed)' if failed_count > 0 else ''
            )
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception('Error in bulk reject')
        return jsonify({
            'success': False,
            'error': f'Error: {str(e)}'
        }), 500


@rh_bp.route('/conges/<int:leave_id>', methods=['DELETE'])
@login_required
def cancel_leave(leave_id):
    """
    Cancel a leave request (only if pending or own request).
    """
    leave = db.session.get(LeaveRequest, leave_id)
    if not leave:
        return jsonify({'success': False, 'error': 'Leave request not found'}), 404
    
    # Permission check
    is_own = leave.technicien_id == current_user.id
    is_manager = current_user.role in ['rh', 'chef_pur', 'chef_pilote', 'admin']
    
    if not (is_own or is_manager):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    # Can only cancel pending requests
    if leave.statut != 'pending':
        return jsonify({'success': False, 'error': 'Can only cancel pending requests'}), 409
    
    try:
        leave.statut = 'cancelled'
        leave.updated_at = datetime.utcnow()
        db.session.commit()
        
        log_audit(
            action='leave_cancelled',
            entity_type='leave_request',
            entity_id=leave.id,
            old_value={'statut': 'pending'},
            new_value={'statut': 'cancelled'}
        )
        
        return jsonify({'success': True, 'message': 'Leave request cancelled'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# HOURS TRACKING
# ============================================================

@rh_bp.route('/heures', methods=['GET'])
@login_required
def get_hours():
    """
    Calculate worked hours for a technician.
    
    Query params:
    - technicien_id: Employee ID (required for non-technicians)
    - debut: Start date (YYYY-MM-DD)
    - fin: End date (YYYY-MM-DD)
    """
    tech_id = request.args.get('technicien_id', type=int)
    debut = request.args.get('debut')
    fin = request.args.get('fin')
    
    # Permission: technicians can only see their own, managers can see any
    if current_user.role == 'technicien':
        tech_id = current_user.id
    elif not tech_id:
        return jsonify({'success': False, 'error': 'technicien_id required'}), 400
    
    query = Intervention.query.filter(Intervention.technicien_id == tech_id)
    
    try:
        if debut:
            d = datetime.fromisoformat(debut)
            query = query.filter(Intervention.date_debut >= d)
        if fin:
            f = datetime.fromisoformat(fin)
            query = query.filter(Intervention.date_fin <= f)
    except Exception:
        return jsonify({'success': False, 'error': 'Invalid date format, use YYYY-MM-DD'}), 400
    
    items = query.filter(
        Intervention.date_debut != None,
        Intervention.date_fin != None
    ).all()
    
    total_seconds = 0
    for item in items:
        try:
            total_seconds += (item.date_fin - item.date_debut).total_seconds()
        except Exception:
            pass
    
    total_hours = round(total_seconds / 3600.0, 2)
    
    return jsonify({
        'success': True,
        'technicien_id': tech_id,
        'total_hours': total_hours,
        'intervention_count': len(items),
        'period': {
            'start': debut or 'all-time',
            'end': fin or 'all-time'
        }
    })


@rh_bp.route('/heures/tous', methods=['GET'])
@login_required
def get_all_hours():
    """
    Get worked hours for ALL technicians.
    RH role only.
    
    Query params:
    - debut: Start date (YYYY-MM-DD)
    - fin: End date (YYYY-MM-DD)
    - limit: Max results (default: 100)
    """
    allowed_roles = ['rh', 'chef_pur']
    if current_user.role not in allowed_roles:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    debut = request.args.get('debut')
    fin = request.args.get('fin')
    limit = request.args.get('limit', 100, type=int)
    
    # Get all technicians
    techniciens = User.query.filter(User.role == 'technicien').limit(limit).all()
    
    result = []
    for tech in techniciens:
        query = Intervention.query.filter(Intervention.technicien_id == tech.id)
        
        try:
            if debut:
                d = datetime.fromisoformat(debut)
                query = query.filter(Intervention.date_debut >= d)
            if fin:
                f = datetime.fromisoformat(fin)
                query = query.filter(Intervention.date_fin <= f)
        except Exception:
            continue
        
        items = query.filter(
            Intervention.date_debut != None,
            Intervention.date_fin != None
        ).all()
        
        total_seconds = 0
        for item in items:
            try:
                total_seconds += (item.date_fin - item.date_debut).total_seconds()
            except Exception:
                pass
        
        total_hours = round(total_seconds / 3600.0, 2)
        
        if total_hours > 0 or len(items) > 0:  # Only include technicians with hours
            result.append({
                'technicien_id': tech.id,
                'technicien_nom': f"{tech.prenom} {tech.nom}",
                'total_hours': total_hours,
                'intervention_count': len(items),
                'moyenne_par_intervention': round(total_hours / len(items), 2) if items else 0
            })
    
    # Sort by hours descending
    result.sort(key=lambda x: x['total_hours'], reverse=True)
    
    return jsonify({
        'success': True,
        'total_techniciens': len(result),
        'period': {
            'start': debut or 'all-time',
            'end': fin or 'all-time'
        },
        'heures': result
    }), 200


# ============================================================
# EXPORT & REPORTING
# ============================================================

@rh_bp.route('/export', methods=['GET'])
@login_required
def export_rh():
    """
    Export leave requests and hours data.
    Admins only.
    """
    if current_user.role not in ['admin', 'manager', 'chef_pur']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    leaves = LeaveRequest.query.all()
    result = []
    for l in leaves:
        result.append({
            'id': l.id,
            'technicien': l.technicien.username,
            'date_debut': l.date_debut.isoformat(),
            'date_fin': l.date_fin.isoformat(),
            'type': l.type,
            'business_days': l.business_days_count,
            'statut': l.statut,
            'created_at': l.created_at.isoformat(),
            'approved_by': l.manager.username if l.manager else None
        })
    
    return jsonify({'success': True, 'export': result})


# ============================================================
# NOTES RH - Service communications
# ============================================================

@rh_bp.route('/notes', methods=['POST'])
@login_required
def create_note():
    """
    Create a new RH service note.
    
    Request JSON:
    {
        "titre": "Note title",
        "contenu": "Note content",
        "destinataires": "tous",  // 'tous', 'zone', 'service'
        "zone_cible": "DAKAR",  // optional, if destinataires='zone'
        "service_cible": "Production"  // optional, if destinataires='service'
    }
    """
    allowed_roles = ['rh', 'chef_pur']
    if current_user.role not in allowed_roles:
        return jsonify({'error': 'Unauthorized. RH or Chef PUR role required.'}), 403
    
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('titre') or len(data['titre']) > 200:
            return jsonify({'error': 'titre: required, max 200 chars'}), 400
        if not data.get('contenu'):
            return jsonify({'error': 'contenu: required'}), 400
        if data.get('destinataires') not in ['tous', 'zone', 'service']:
            return jsonify({'error': 'destinataires: invalid value'}), 400
        
        # Create note
        note = NoteRH(
            titre=data.get('titre'),
            contenu=data.get('contenu'),
            author_id=current_user.id,
            destinataires=data.get('destinataires', 'tous'),
            zone_cible=data.get('zone_cible'),
            service_cible=data.get('service_cible')
        )
        
        # Auto-publish if publish flag is set
        if data.get('publish'):
            note.publish()
        
        db.session.add(note)
        db.session.commit()
        
        # Audit log
        log_audit('create', 'note_rh', note.id, None, {
            'titre': note.titre,
            'author_id': note.author_id,
            'destinataires': note.destinataires
        })
        
        return jsonify({
            'success': True,
            'message': 'Note created successfully',
            'note_id': note.id,
            'date_creation': note.date_creation.isoformat()
        }), 201
    
    except Exception as e:
        current_app.logger.error(f"[RH] Error creating note: {str(e)}")
        return jsonify({'error': f'Internal error: {str(e)}'}), 500


@rh_bp.route('/notes', methods=['GET'])
@login_required
def list_notes():
    """
    List RH service notes (published only for non-RH users)
    
    Query params:
    - published_only: true (default for non-RH)
    - limit: 50 (default)
    - offset: 0 (default)
    """
    try:
        # Filter by role
        published_only = request.args.get('published_only', 'true' if current_user.role != 'rh' else 'false') == 'true'
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        query = NoteRH.query.filter_by(actif=True)
        
        if published_only:
            # For non-RH users, show only published notes
            query = query.filter(NoteRH.date_publication.isnot(None))
            query = query.filter(NoteRH.date_publication <= datetime.utcnow())
            # Order by date descending (no NULL values)
            query = query.order_by(NoteRH.date_publication.desc())
        else:
            # RH sees all notes - show published first, then drafts by creation date
            query = query.order_by(
                desc(NoteRH.date_publication.isnot(None)),  # Published notes first
                NoteRH.date_publication.desc()  # Then by publication date
            )
        
        # Total count
        total = query.count()
        
        # Paginate
        notes = query.limit(limit).offset(offset).all()
        
        result = []
        for note in notes:
            # Safe author access - handle orphaned notes
            author_name = "RH"
            if note.author:
                author_name = f"{note.author.prenom} {note.author.nom}"
            
            result.append({
                'id': note.id,
                'titre': note.titre,
                'contenu': note.contenu,
                'author': author_name,
                'author_nom': author_name,  # Compatibility with frontend
                'date_creation': note.date_creation.isoformat(),
                'date_publication': note.date_publication.isoformat() if note.date_publication else None,
                'is_published': note.is_published(),
                'destinataires': note.destinataires
            })
        
        return jsonify({
            'success': True,
            'total': total,
            'limit': limit,
            'offset': offset,
            'notes': result
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"[RH] Error listing notes: {str(e)}")
        return jsonify({'error': f'Internal error: {str(e)}'}), 500


@rh_bp.route('/notes/<int:note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    """
    Delete (archive) an RH service note.
    """
    allowed_roles = ['rh', 'chef_pur']
    if current_user.role not in allowed_roles:
        return jsonify({'error': 'Unauthorized. RH or Chef PUR role required.'}), 403
    
    try:
        note = db.session.get(NoteRH, note_id)
        if not note:
            return jsonify({'error': 'Note not found'}), 404
        
        # Soft delete
        note.archive()
        db.session.commit()
        
        # Audit log
        log_audit('delete', 'note_rh', note_id, {'actif': True}, {'actif': False})
        
        return jsonify({
            'success': True,
            'message': 'Note archived successfully'
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"[RH] Error deleting note: {str(e)}")
        return jsonify({'error': f'Internal error: {str(e)}'}), 500


# ============================================================
# LEAVE STATISTICS
# ============================================================

@rh_bp.route('/leave/stats', methods=['GET'])
@login_required
def get_leave_stats():
    """
    Get leave request statistics for a given year.
    
    Query params:
    - year: 2026 (default: current year)
    
    Returns:
    {
        "year": 2026,
        "total": 45,
        "approved": 30,
        "pending": 10,
        "rejected": 5,
        "by_technicien": [...]
    }
    """
    allowed_roles = ['rh', 'chef_pur']
    if current_user.role not in allowed_roles:
        return jsonify({'error': 'Unauthorized. RH or Chef PUR role required.'}), 403
    
    try:
        year = request.args.get('year', datetime.now(timezone.utc).year, type=int)
        
        # Get all leave requests for the year
        from models import LeaveRequest
        leaves = LeaveRequest.query.filter(
            db.extract('year', LeaveRequest.date_debut) == year
        ).all()
        
        # Calculate statistics
        total = len(leaves)
        approved = len([l for l in leaves if l.statut == 'approved'])
        pending = len([l for l in leaves if l.statut == 'pending'])
        rejected = len([l for l in leaves if l.statut == 'rejected'])
        
        # Group by technicien
        by_technicien = {}
        for leave in leaves:
            tech_id = leave.technicien_id
            if tech_id not in by_technicien:
                by_technicien[tech_id] = {
                    'technicien_id': tech_id,
                    'technicien_name': f"{leave.technicien.prenom} {leave.technicien.nom}",
                    'total': 0,
                    'approved': 0,
                    'pending': 0,
                    'rejected': 0,
                    'business_days': 0
                }
            
            by_technicien[tech_id]['total'] += 1
            if leave.statut == 'approved':
                by_technicien[tech_id]['approved'] += 1
            elif leave.statut == 'pending':
                by_technicien[tech_id]['pending'] += 1
            elif leave.statut == 'rejected':
                by_technicien[tech_id]['rejected'] += 1
            
            by_technicien[tech_id]['business_days'] += leave.business_days_count
        
        return jsonify({
            'success': True,
            'year': year,
            'total': total,
            'approved': approved,
            'pending': pending,
            'rejected': rejected,
            'by_technicien': list(by_technicien.values())
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"[RH] Error getting leave stats: {str(e)}")
        return jsonify({'error': f'Internal error: {str(e)}'}), 500


# ============================================================
# TEAM CALENDAR
# ============================================================

@rh_bp.route('/calendar/team', methods=['GET'])
@login_required
def get_team_calendar():
    """
    Get team calendar view showing approved leaves in a given month.
    
    Query params:
    - year: 2026 (default: current year)
    - month: 2 (default: current month)
    
    Returns:
    {
        "year": 2026,
        "month": 2,
        "calendar": {
            "2026-02-01": [{"technicien": "John Doe", "type": "conge_paye", ...}],
            ...
        }
    }
    """
    allowed_roles = ['rh', 'chef_pur']
    if current_user.role not in allowed_roles:
        return jsonify({'error': 'Unauthorized. RH or Chef PUR role required.'}), 403
    
    try:
        from models import LeaveRequest
        
        year = request.args.get('year', datetime.now(timezone.utc).year, type=int)
        month = request.args.get('month', datetime.now(timezone.utc).month, type=int)
        
        # Get all approved leaves that overlap with the month
        leaves = LeaveRequest.query.filter(
            LeaveRequest.statut == 'approved',
            db.extract('year', LeaveRequest.date_debut) == year
        ).all()
        
        # Build calendar
        from calendar import monthrange
        calendar = {}
        
        for leave in leaves:
            current_date = leave.date_debut
            # Only include dates in this month
            while current_date <= leave.date_fin:
                if current_date.year == year and current_date.month == month:
                    date_str = current_date.strftime('%Y-%m-%d')
                    if date_str not in calendar:
                        calendar[date_str] = []
                    
                    calendar[date_str].append({
                        'technicien': f"{leave.technicien.prenom} {leave.technicien.nom}",
                        'technicien_id': leave.technicien_id,
                        'type': leave.type,
                        'leave_id': leave.id,
                        'date_fin': leave.date_fin.isoformat()
                    })
                
                current_date += timedelta(days=1)
        
        return jsonify({
            'success': True,
            'year': year,
            'month': month,
            'calendar': calendar
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"[RH] Error getting team calendar: {str(e)}")
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

