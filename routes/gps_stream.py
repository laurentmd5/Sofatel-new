"""
📍 REAL-TIME GPS STREAMING MODULE
Server-Sent Events (SSE) for live technician location tracking

Features:
- Real-time technician position updates
- Geofence entry/exit events
- Movement tracking
- Client-side filtering by zone/team
"""

from flask import Blueprint, Response, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json
import time
import threading
from collections import defaultdict
from models import (
    db, Intervention, User, ActivityLog, DemandeIntervention
)

gps_stream_bp = Blueprint('gps_stream', __name__)


class TechnicianLocationCache:
    """Cache latest position for each technician."""
    
    def __init__(self):
        self.positions = {}  # technicien_id -> {lat, lon, timestamp, status, intervention_id}
        self.lock = threading.RLock()
    
    def update_position(self, technicien_id: int, latitude: float, longitude: float, 
                       status: str = 'en_route', accuracy: float = None,
                       intervention_id: int = None):
        """Update technician position."""
        with self.lock:
            self.positions[technicien_id] = {
                'technicien_id': technicien_id,
                'latitude': float(latitude),
                'longitude': float(longitude),
                'status': status,
                'accuracy': float(accuracy) if accuracy else None,
                'intervention_id': intervention_id,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_position(self, technicien_id: int):
        """Get latest position for technician."""
        with self.lock:
            return self.positions.get(technicien_id)
    
    def get_all_positions(self, zone_id: int = None) -> list:
        """Get all technician positions, optionally filtered by zone."""
        with self.lock:
            positions = list(self.positions.values())
        
        # Filter by zone if needed
        if zone_id:
            # TODO: Filter by zone membership if available
            pass
        
        return positions
    
    def refresh_from_db(self):
        """Load latest positions from database activity logs."""
        with self.lock:
            # Get latest tracking for each technician (last 30 minutes)
            cutoff = datetime.utcnow() - timedelta(minutes=30)
            
            latest_logs = db.session.query(
                ActivityLog.user_id,
                ActivityLog.details,
                ActivityLog.timestamp
            ).filter(
                ActivityLog.action == 'location_update',
                ActivityLog.module == 'tracking',
                ActivityLog.timestamp >= cutoff
            ).order_by(ActivityLog.user_id, ActivityLog.timestamp.desc()).all()
            
            if not latest_logs:
                return

            # OPTIMISATION: Récupérer toutes les interventions en cours en une seule requête bulk
            # pour éviter le N+1 query pattern (1 query par technicien dans la boucle)
            user_ids = list(set([log.user_id for log in latest_logs]))
            active_interv_query = Intervention.query.filter(
                Intervention.technicien_id.in_(user_ids),
                Intervention.statut == 'en_cours'
            ).all()
            
            # Mapper tech_id -> intervention_id
            tech_to_interv = {it.technicien_id: it.id for it in active_interv_query}
            
            seen_users = set()
            for log in latest_logs:
                if log.user_id in seen_users:
                    continue
                
                seen_users.add(log.user_id)
                
                try:
                    details = json.loads(log.details)
                    interv_id = tech_to_interv.get(log.user_id) or details.get('intervention_id')
                    
                    self.positions[log.user_id] = {
                        'technicien_id': log.user_id,
                        'latitude': details.get('latitude'),
                        'longitude': details.get('longitude'),
                        'status': details.get('status', 'en_route'),
                        'accuracy': details.get('accuracy'),
                        'intervention_id': interv_id,
                        'timestamp': log.timestamp.isoformat()
                    }
                except Exception as e:
                    current_app.logger.error(f"Error parsing tracking log: {str(e)}")



# Global location cache
_location_cache = TechnicianLocationCache()


# ============================================================
# GPS STREAMING ENDPOINT
# ============================================================

@gps_stream_bp.route('/api/stream/gps', methods=['GET'])
@login_required
def stream_gps_locations():
    """
    Server-Sent Events stream for real-time technician locations.
    
    Query params:
      - interval (seconds between updates, default 5)
      - once (1|true for single snapshot)
      - zone_id (filter by zone)
      - limit (max technicians, default 100)
    """
    try:
        interval = int(request.args.get('interval', 5))
        interval = max(3, min(60, interval))  # Clamp 3-60 seconds
    except:
        interval = 5
    
    once = str(request.args.get('once', '0')).lower() in ('1', 'true')
    zone_id = request.args.get('zone_id', type=int)
    
    try:
        limit = int(request.args.get('limit', 100))
    except:
        limit = 100
    
    app = current_app._get_current_object()
    
    def generate_events():
        """Generate GPS stream events."""
        with app.app_context():
            # Initial load from database
            _location_cache.refresh_from_db()
            
            while True:
                try:
                    # Get all technician positions
                    positions = _location_cache.get_all_positions(zone_id)
                    
                    # Filter by current user's visibility
                    # (This is simplified - in production, add proper RBAC)
                    if current_user.role == 'technicien':
                        # Technician sees only their own position
                        positions = [p for p in positions if p['technicien_id'] == current_user.id]
                    elif current_user.role == 'chef_zone':
                        # Chef de zone sees their zone's technicians
                        # (TODO: implement zone membership check)
                        pass
                    
                    # Limit results
                    positions = positions[:limit]
                    
                    # Payload
                    payload = {
                        'type': 'gps_update',
                        'timestamp': datetime.utcnow().isoformat(),
                        'count': len(positions),
                        'positions': positions
                    }
                    
                    # SSE frame
                    yield f"data: {json.dumps(payload, default=str)}\n\n"
                    
                    if once:
                        break
                    
                    time.sleep(interval)
                
                except Exception as e:
                    current_app.logger.exception(f"Error in GPS stream: {str(e)}")
                    time.sleep(interval)
    
    return Response(generate_events(), mimetype='text/event-stream')


# ============================================================
# GPS SNAPSHOT ENDPOINT (Polling alternative)
# ============================================================

@gps_stream_bp.route('/api/gps/positions', methods=['GET'])
@login_required
def get_gps_positions():
    """
    Get current technician positions (polling alternative to SSE).
    
    Query params:
      - zone_id (optional filter)
      - include_inactive (true to include technicians not tracked recently)
    """
    _location_cache.refresh_from_db()
    
    zone_id = request.args.get('zone_id', type=int)
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    
    positions = _location_cache.get_all_positions(zone_id)
    
    # Filter out inactive if needed
    if not include_inactive:
        cutoff = datetime.utcnow() - timedelta(minutes=15)
        positions = [p for p in positions if p['timestamp'] > cutoff.isoformat()]
    
    # Apply visibility rules
    if current_user.role == 'technicien':
        positions = [p for p in positions if p['technicien_id'] == current_user.id]
    
    return jsonify({
        'success': True,
        'timestamp': datetime.utcnow().isoformat(),
        'count': len(positions),
        'positions': positions
    })


# ============================================================
# GPS HISTORY ENDPOINT
# ============================================================

@gps_stream_bp.route('/api/gps/history/<int:technicien_id>', methods=['GET'])
@login_required
def get_gps_history(technicien_id):
    """
    Get GPS history for a technician.
    
    Query params:
      - minutes (lookback window, default 60)
      - limit (max results, default 100)
    """
    # Permission check
    if current_user.role == 'technicien' and current_user.id != technicien_id:
        return jsonify({'success': False, 'error': 'Accès refusé'}), 403
    
    try:
        minutes = int(request.args.get('minutes', 60))
    except:
        minutes = 60
    
    try:
        limit = int(request.args.get('limit', 100))
    except:
        limit = 100
    
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    
    # Query activity logs for tracking
    logs = ActivityLog.query.filter(
        ActivityLog.user_id == technicien_id,
        ActivityLog.action == 'location_update',
        ActivityLog.module == 'tracking',
        ActivityLog.timestamp >= cutoff
    ).order_by(ActivityLog.timestamp.desc()).limit(limit).all()
    
    positions = []
    for log in logs:
        try:
            details = json.loads(log.details)
            positions.append({
                'timestamp': log.timestamp.isoformat(),
                'latitude': details.get('latitude'),
                'longitude': details.get('longitude'),
                'accuracy': details.get('accuracy'),
                'status': details.get('status', 'en_route'),
                'intervention_id': details.get('intervention_id'),
                'speed': details.get('speed')
            })
        except:
            pass
    
    return jsonify({
        'success': True,
        'technicien_id': technicien_id,
        'count': len(positions),
        'positions': positions
    })


# ============================================================
# TECHNICIAN STATUS UPDATE (For mobile client)
# ============================================================

@gps_stream_bp.route('/api/gps/update-status', methods=['POST'])
@login_required
def update_technician_status():
    """
    Mobile client updates technician status + position.
    Also updates position cache for SSE stream.
    """
    data = request.get_json() or {}
    
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    status = data.get('status', 'en_route')  # en_route, on_site, pause
    accuracy = data.get('accuracy')
    
    if not latitude or not longitude:
        return jsonify({'success': False, 'error': 'Coordonnées manquantes'}), 400
    
    try:
        # Get current intervention
        intervention = Intervention.query.filter_by(
            technicien_id=current_user.id,
            statut='en_cours'
        ).first()
        
        # Update position cache for SSE
        _location_cache.update_position(
            current_user.id,
            latitude, longitude,
            status=status,
            accuracy=accuracy,
            intervention_id=intervention.id if intervention else None
        )
        
        return jsonify({
            'success': True,
            'status': status,
            'intervention_id': intervention.id if intervention else None
        })
    
    except Exception as e:
        current_app.logger.exception('Error updating technician status')
        return jsonify({'success': False, 'error': str(e)}), 500
