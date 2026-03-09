"""SLA enforcement helpers (moved to top-level module to avoid package name conflicts).

Same API as utils/sla.py but accessible as `sla_utils` to avoid the existing `utils.py` module shadowing a `utils` package.

Improvements:
- Use timezone-aware UTC datetimes.
- Respect `DemandeIntervention.sla_hours_override` when present.
- Provide `run_sla_check()` orchestration and backoff/escalation when sending alerts.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple

from models import db, Intervention, DemandeIntervention, User
from utils import create_sms_notification, send_email
from utils_audit import log_sla_escalation


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def get_sla_hours(priorite: str) -> int:
    if not priorite:
        return 72
    p = priorite.strip().lower()
    if p == 'urgent':
        return 24
    if p in ('haute', 'elevee', 'élevée'):
        return 48
    return 72


def check_intervention_sla(intervention: Intervention) -> bool:
    """Return True if the intervention violates SLA (timezone-aware)."""
    if not intervention:
        return False
    if intervention.statut in ('termine', 'valide'):
        return False

    created = intervention.date_creation or _now_utc()
    # Normalize naive datetimes to UTC-aware
    if isinstance(created, datetime) and created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)

    sla_hours = None
    priorite = None
    if intervention.demande_id:
        demande = db.session.get(DemandeIntervention, intervention.demande_id)
        if demande:
            priorite = getattr(demande, 'priorite_traitement', None)
            # Respect explicit override when present
            override = getattr(demande, 'sla_hours_override', None)
            if override is not None:
                sla_hours = int(override)

    if sla_hours is None:
        sla_hours = get_sla_hours(priorite)

    deadline = created + timedelta(hours=sla_hours)
    return _now_utc() > deadline


def get_violations() -> List[Dict]:
    violations: List[Dict] = []
    candidates = Intervention.query.filter(Intervention.statut != 'termine').all()
    for it in candidates:
        try:
            if check_intervention_sla(it):
                priorite = None
                sla_hours = None
                if it.demande_id:
                    d = db.session.get(DemandeIntervention, it.demande_id)
                    priorite = getattr(d, 'priorite_traitement', None) if d else None
                    if d:
                        sla_hours = getattr(d, 'sla_hours_override', None)
                if sla_hours is None:
                    sla_hours = get_sla_hours(priorite)

                created = it.date_creation or _now_utc()
                if isinstance(created, datetime) and created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                overdue = (_now_utc() - (created + timedelta(hours=int(sla_hours)))).total_seconds()
                violations.append({
                    'intervention_id': it.id,
                    'demande_id': it.demande_id,
                    'technicien_id': it.technicien_id,
                    'priorite': priorite,
                    'date_creation': created.isoformat(),
                    'sla_hours': int(sla_hours),
                    'overdue_seconds': int(max(0, overdue))
                })
        except Exception:
            continue
    return violations


def _should_send_for_intervention(intervention: Intervention) -> Tuple[bool, str]:
    """Return (should_send, reason). Uses escalation/backoff logic."""
    last = getattr(intervention, 'sla_last_alerted_at', None)
    level = getattr(intervention, 'sla_escalation_level', 0) or 0
    if not last:
        return True, 'never_alerted'
    try:
        last_dt = last if isinstance(last, datetime) and last.tzinfo else last.replace(tzinfo=timezone.utc)
    except Exception:
        last_dt = last
    backoff_hours = min(24, (level + 1))  # simple backoff in hours, capped at 24
    if _now_utc() - last_dt < timedelta(hours=backoff_hours):
        return False, f'backoff_{backoff_hours}h'
    return True, 'ok'


def send_sla_alert(violation: Dict, notify_sms: bool = True, notify_email: bool = False) -> bool:
    """Send alerts if allowed; update intervention sla_last_alerted_at and sla_escalation_level on success."""
    try:
        inter_id = violation.get('intervention_id')
        intervention = db.session.get(Intervention, inter_id)
        if not intervention:
            return False

        should_send, reason = _should_send_for_intervention(intervention)
        if not should_send:
            return False

        tech_id = violation.get('technicien_id')
        demande_id = violation.get('demande_id')

        sent_any = False

        if notify_sms and tech_id and demande_id:
            try:
                create_sms_notification(technicien_id=tech_id, demande_id=demande_id, type_notification='echeance', notify_managers=True)
                sent_any = True
            except Exception:
                sent_any = sent_any or False

        if notify_email:
            managers = User.query.filter(User.role.in_(['admin', 'chef_pilote', 'chef_zone']), User.actif == True).all()
            emails = [m.email for m in managers if getattr(m, 'email', None)]
            if emails:
                subject = f"SLA Violation: Intervention {intervention.id}"
                body = (f"Intervention {intervention.id} (Demande {demande_id}) is overdue by {violation.get('overdue_seconds')} seconds. "
                        f"Priority: {violation.get('priorite')}.\n\nThis is an automated alert.")
                try:
                    send_email(subject, recipients=emails, body=body)
                    sent_any = True
                except Exception:
                    sent_any = sent_any or False

        # Update alert metadata when we attempted to send
        if sent_any:
            old_level = getattr(intervention, 'sla_escalation_level', 0) or 0
            new_level = old_level + 1
            intervention.sla_last_alerted_at = _now_utc()
            intervention.sla_escalation_level = new_level
            db.session.add(intervention)
            
            # Log escalation to audit trail (use admin user ID if available)
            try:
                admin_user = User.query.filter_by(est_admin=True).first()
                actor_id = admin_user.id if admin_user else 1
                log_sla_escalation(
                    intervention_id=inter_id,
                    actor_id=actor_id,
                    priority=violation.get('priorite'),
                    reason=f'SLA escalated from level {old_level} to {new_level} seconds overdue: {violation.get("overdue_seconds")}'
                )
            except Exception:
                pass  # Don't break SLA alert if audit logging fails
            
            db.session.commit()
            return True
    except Exception:
        db.session.rollback()
        return False
    return False


def run_sla_check(send_alerts: bool = False, send_email: bool = False) -> Tuple[int, int]:
    """Run SLA check and optionally send alerts.

    Returns (alerted_count, violations_count).
    """
    violations = get_violations()
    alerted = 0
    if send_alerts:
        for v in violations:
            ok = send_sla_alert(v, notify_sms=True, notify_email=send_email)
            if ok:
                alerted += 1
    return alerted, len(violations)

