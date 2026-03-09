"""SLA enforcement helpers (minimal)

Functions:
- get_sla_hours(priorite)
- check_intervention_sla(intervention)
- get_violations()
- send_sla_alert(violation, notify_sms=True, notify_email=False)

This module intentionally keeps logic simple and synchronous (no scheduler).
"""
from datetime import datetime, timedelta
from typing import List, Dict

from models import db, Intervention, DemandeIntervention, User
from utils import create_sms_notification, send_email


def get_sla_hours(priorite: str) -> int:
    """Map a priority string to SLA hours. Simple rules:
    - 'urgent' -> 24
    - 'haute'  -> 48
    - else     -> 72
    Returns hours as int.
    """
    if not priorite:
        return 72
    p = priorite.strip().lower()
    if p == 'urgent':
        return 24
    if p in ('haute', 'elevee', 'élevée'):
        return 48
    return 72


def check_intervention_sla(intervention: Intervention) -> bool:
    """Return True if the intervention violates SLA (i.e., older than allowed and not finished).
    We use the linked DemandeIntervention.priorite_traitement when available.
    """
    if not intervention:
        return False
    if intervention.statut == 'termine' or intervention.statut == 'valide':
        return False

    # Use Intervention.date_creation where possible, fallback to now if missing
    created = intervention.date_creation or datetime.utcnow()

    # Try to load the demande and its priority
    priorite = None
    if intervention.demande_id:
        demande = db.session.get(DemandeIntervention, intervention.demande_id)
        if demande:
            priorite = getattr(demande, 'priorite_traitement', None)

    sla_hours = get_sla_hours(priorite)
    deadline = created + timedelta(hours=sla_hours)
    return datetime.utcnow() > deadline


def get_violations() -> List[Dict]:
    """Return a list of violation dicts for all interventions currently violating SLA.
    Each dict contains: intervention_id, demande_id, technicien_id, priorite, date_creation, sla_hours, overdue_seconds
    """
    violations = []
    # Query interventions that are not finished
    candidates = Intervention.query.filter(Intervention.statut != 'termine').all()
    for it in candidates:
        try:
            if check_intervention_sla(it):
                priorite = None
                if it.demande_id:
                    d = db.session.get(DemandeIntervention, it.demande_id)
                    priorite = getattr(d, 'priorite_traitement', None) if d else None
                sla_hours = get_sla_hours(priorite)
                created = it.date_creation or datetime.utcnow()
                overdue = (datetime.utcnow() - (created + timedelta(hours=sla_hours))).total_seconds()
                violations.append({
                    'intervention_id': it.id,
                    'demande_id': it.demande_id,
                    'technicien_id': it.technicien_id,
                    'priorite': priorite,
                    'date_creation': created.isoformat(),
                    'sla_hours': sla_hours,
                    'overdue_seconds': int(max(0, overdue))
                })
        except Exception:
            # Defensive: skip problematic record
            continue
    return violations


def send_sla_alert(violation: Dict, notify_sms: bool = True, notify_email: bool = False):
    """Send a basic alert for a single violation.
    - SMS: uses create_sms_notification(technicien_id, demande_id, type_notification='echeance')
    - Email: send_email(subject, [manager_emails], body)

    This function is intentionally conservative and will not raise on errors.
    """
    try:
        tech_id = violation.get('technicien_id')
        demande_id = violation.get('demande_id')

        if notify_sms and tech_id and demande_id:
            try:
                create_sms_notification(technicien_id=tech_id, demande_id=demande_id, type_notification='echeance', notify_managers=True)
            except Exception:
                # best-effort
                pass

        if notify_email:
            # Send email to managers and admins if configured
            managers = User.query.filter(User.role.in_(['admin', 'chef_pilote', 'chef_zone']), User.actif == True).all()
            emails = [m.email for m in managers if getattr(m, 'email', None)]
            if emails:
                subject = f"SLA Violation: Intervention {violation.get('intervention_id')}"
                body = f"Intervention {violation.get('intervention_id')} (Demande {violation.get('demande_id')}) is overdue by {violation.get('overdue_seconds')} seconds. Priority: {violation.get('priorite')}."
                try:
                    send_email(subject, recipients=emails, body=body)
                except Exception:
                    pass
    except Exception:
        return False
    return True
