"""Intervention completeness (simple scoring)

Rules (fixed weights):
- photos present -> +30
- signature_client present -> +30
- date_debut and date_fin present -> +20
- diagnostic_technicien present -> +20

Functions:
- compute_intervention_completeness(intervention) -> dict(score:int, details:dict)
- average_completeness_for_date(date_str) -> dict(avg_score: float, count: int)
"""
from datetime import datetime
from typing import Dict, Tuple, Optional
import json

from models import db, Intervention


def _has_photos(intervention: Intervention) -> bool:
    if not intervention or not getattr(intervention, 'photos', None):
        return False
    try:
        data = json.loads(intervention.photos)
        return isinstance(data, (list, tuple)) and len(data) > 0
    except Exception:
        # Could be stored as comma-separated string
        val = intervention.photos
        if isinstance(val, str) and val.strip():
            return True
        return False


def _has_signature(intervention: Intervention) -> bool:
    sig = getattr(intervention, 'signature_client', None)
    return bool(sig and str(sig).strip())


def _has_dates(intervention: Intervention) -> bool:
    return bool(getattr(intervention, 'date_debut', None) and getattr(intervention, 'date_fin', None))


def _has_diagnostic(intervention: Intervention) -> bool:
    diag = getattr(intervention, 'diagnostic_technicien', None)
    return bool(diag and str(diag).strip())


def compute_intervention_completeness(intervention: Intervention) -> Dict:
    """Compute completeness score and return details.

    Returns:
        { 'score': int, 'details': { 'photos': bool, 'signature_client': bool, 'dates': bool, 'diagnostic': bool } }
    """
    if not intervention:
        return {'score': 0, 'details': {'photos': False, 'signature_client': False, 'dates': False, 'diagnostic': False}}

    weights = {'photos': 30, 'signature_client': 30, 'dates': 20, 'diagnostic': 20}

    photos_ok = _has_photos(intervention)
    sig_ok = _has_signature(intervention)
    dates_ok = _has_dates(intervention)
    diag_ok = _has_diagnostic(intervention)

    score = 0
    if photos_ok:
        score += weights['photos']
    if sig_ok:
        score += weights['signature_client']
    if dates_ok:
        score += weights['dates']
    if diag_ok:
        score += weights['diagnostic']

    return {
        'score': int(score),
        'details': {
            'photos': photos_ok,
            'signature_client': sig_ok,
            'dates': dates_ok,
            'diagnostic': diag_ok
        }
    }


def average_completeness_for_date(date_str: str) -> Dict:
    """Compute average completeness for interventions created on the given date (YYYY-MM-DD).

    Returns: {'date': date_str, 'average_score': float, 'count': int}
    If no interventions found, returns {'date': date_str, 'average_score': 0.0, 'count': 0}
    """
    try:
        d = datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception:
        return {'date': date_str, 'average_score': 0.0, 'count': 0}

    q = Intervention.query.filter(db.func.date(Intervention.date_creation) == d).all()
    if not q:
        return {'date': date_str, 'average_score': 0.0, 'count': 0}

    total = 0
    count = 0
    for it in q:
        res = compute_intervention_completeness(it)
        total += res.get('score', 0)
        count += 1

    avg = total / count if count else 0.0
    return {'date': date_str, 'average_score': round(avg, 2), 'count': count}
