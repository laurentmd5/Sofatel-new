from flask import Blueprint, Response, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json
import time
from collections import defaultdict
import threading

from models import Intervention, User
from extensions import db
from event_bus import get_event_bus, EventType, Event, subscribe_to_events

stream_bp = Blueprint('stream', __name__)


def _serialize_intervention(it: Intervention):
    """Serialize intervention to JSON-safe dict (including GPS for map)."""
    try:
        technicien_nom = it.technicien.username if it.technicien else None
    except Exception:
        technicien_nom = None
    
    try:
        client_nom = it.demande.nom_raison_sociale if it.demande else None
        adresse = it.demande.adresse_demande if it.demande else None
    except Exception:
        client_nom = None
        adresse = None
    
    return {
        'id': it.id,
        'demande_id': it.demande_id,
        'technicien_id': it.technicien_id,
        'technicien_nom': technicien_nom,
        'client_nom': client_nom,
        'adresse': adresse,
        'statut': it.statut,
        'state': it.state,
        'date_creation': it.date_creation.isoformat() if it.date_creation else None,
        'date_debut': it.date_debut.isoformat() if it.date_debut else None,
        'date_fin': it.date_fin.isoformat() if it.date_fin else None,
        'zone_id': it.equipe_id,
        'gps_lat': it.gps_lat,
        'gps_long': it.gps_long,
    }


class DashboardState:
    """Tracks dashboard counters for real-time updates."""

    def __init__(self):
        self.counters = defaultdict(int)
        self.lock = threading.RLock()

    def update_from_interventions(self, interventions):
        """Update counters from intervention list."""
        with self.lock:
            self.counters.clear()
            for it in interventions:
                state = it.state or it.statut
                self.counters[state] += 1

    def apply_event(self, event: Event):
        """Apply event to counters (for real-time updates)."""
        if event.entity_type != 'intervention':
            return

        with self.lock:
            if event.type in (
                EventType.INTERVENTION_CREATED,
                EventType.INTERVENTION_STATE_CHANGED,
                EventType.INTERVENTION_ASSIGNED,
                EventType.INTERVENTION_STARTED,
                EventType.INTERVENTION_COMPLETED,
                EventType.INTERVENTION_VALIDATED,
                EventType.INTERVENTION_CLOSED,
            ):
                old_state = event.data.get('old_state')
                new_state = event.data.get('new_state')
                
                if old_state:
                    self.counters[old_state] = max(0, self.counters[old_state] - 1)
                if new_state:
                    self.counters[new_state] += 1

    def get_counters(self):
        """Get current counters."""
        with self.lock:
            return dict(self.counters)


# Global dashboard state
_dashboard_state = DashboardState()


@stream_bp.route('/api/stream/interventions', methods=['GET'])
@login_required
def stream_interventions():
    """Enhanced SSE endpoint streaming interventions with real-time updates.

    Query params:
      - interval (seconds, default 10)
      - once (1|true to emit once and finish, useful for tests)
      - limit (max interventions returned, default 50)
      - days (lookback window in days, default 30)
      - zone_id (filter by zone, optional)
      - state (filter by state, optional - canonical state like 'ASSIGNED')
    """
    try:
        interval = int(request.args.get('interval', 10))
    except Exception:
        interval = 10

    once = str(request.args.get('once', '0')).lower() in ('1', 'true', 'yes')
    
    try:
        limit = int(request.args.get('limit', 50))
    except Exception:
        limit = 50

    try:
        days = int(request.args.get('days', 30))
    except Exception:
        days = 30

    zone_id = request.args.get('zone_id')
    if zone_id:
        try:
            zone_id = int(zone_id)
        except Exception:
            zone_id = None

    state_filter = request.args.get('state')

    # Capture app object in request context to use in generator
    app = current_app._get_current_object()

    def generate_events():
        """Generate SSE events with application context."""
        with app.app_context():
            # Initialize counters from database
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = db.session.query(Intervention).filter(Intervention.date_creation >= cutoff)
            
            if zone_id:
                query = query.filter(Intervention.equipe_id == zone_id)
            
            intervs = query.order_by(Intervention.date_creation.desc()).limit(limit).all()
            
            # Apply state filter if provided
            if state_filter:
                intervs = [it for it in intervs if (it.state or it.statut) == state_filter]
            
            _dashboard_state.update_from_interventions(intervs)

            # Event queue for this connection
            event_queue = []
            queue_lock = threading.Lock()

            def on_event(event: Event):
                """Called when any event occurs."""
                # Apply to our counters
                _dashboard_state.apply_event(event)
                
                # Queue for streaming
                with queue_lock:
                    event_queue.append(event)

            # Subscribe to relevant events
            subscribe_to_events(
                [
                    EventType.INTERVENTION_CREATED,
                    EventType.INTERVENTION_ASSIGNED,
                    EventType.INTERVENTION_STARTED,
                    EventType.INTERVENTION_COMPLETED,
                    EventType.INTERVENTION_VALIDATED,
                    EventType.INTERVENTION_CLOSED,
                ],
                callback=on_event
            )

            while True:
                # Re-establish app context for each iteration
                with app.app_context():
                    # Send counters
                    counters = _dashboard_state.get_counters()
                    payload = {
                        'interventions': [_serialize_intervention(it) for it in intervs],
                        'count': len(intervs),
                        'counters': counters,
                        'timestamp': datetime.utcnow().isoformat(),
                    }

                    # Include queued events if any
                    with queue_lock:
                        if event_queue:
                            payload['events'] = [e.to_dict() for e in event_queue]
                            event_queue.clear()

                # SSE frame
                yield f"data: {json.dumps(payload, default=str)}\n\n"

                if once:
                    break

                time.sleep(interval)

    return Response(generate_events(), mimetype='text/event-stream')


from extensions import cache
from sqlalchemy import func

@stream_bp.route('/api/stream/dashboard-summary', methods=['GET'])
@login_required
@cache.cached(timeout=60, query_string=True)
def get_dashboard_summary():
    """Get current dashboard summary (instant snapshot, not streaming).
    
    Used for initial page load and periodic polling.
    Optimised for performance with SQL aggregation and Redis caching.
    """
    try:
        days = int(request.args.get('days', 30))
    except Exception:
        days = 30

    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # OPTIMISATION: Utiliser une agrégation SQL au lieu de récupérer tous les objets
    counts_query = db.session.query(
        Intervention.statut, 
        func.count(Intervention.id)
    ).filter(
        Intervention.date_creation >= cutoff
    ).group_by(Intervention.statut).all()

    counters = {status: count for status, count in counts_query}
    total = sum(counters.values())

    return jsonify({
        'success': True,
        'summary': {
            'total': total,
            'counters': counters,
            'timestamp': datetime.utcnow().isoformat(),
            'current_user_id': current_user.id,
        }
    })



@stream_bp.route('/api/stream/events/recent', methods=['GET'])
@login_required
def get_recent_events():
    """Get recent system events for audit/debugging.
    
    Query params:
      - limit (max events, default 100)
      - type (filter by event type, optional)
    """
    try:
        limit = int(request.args.get('limit', 100))
    except Exception:
        limit = 100

    event_type_filter = request.args.get('type')

    bus = get_event_bus()
    events = bus.get_recent_events(limit=limit * 2)  # Get more than needed to filter

    if event_type_filter:
        events = [e for e in events if e.type.value == event_type_filter]

    events = events[-limit:]  # Keep most recent

    return jsonify({
        'success': True,
        'events': [e.to_dict() for e in events],
    })

