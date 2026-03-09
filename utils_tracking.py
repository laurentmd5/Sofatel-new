"""
📍 GEOLOCATION & TRACKING UTILITIES
Real-time GPS tracking and location validation utilities

Features:
- GPS coordinate validation
- Distance calculations
- Location history management
- Geofencing support
- Webhook notifications for location changes
"""

from datetime import datetime, timedelta, timezone
from typing import Tuple, Dict, Any, List, Optional
from math import radians, cos, sin, asin, sqrt
from flask import current_app
import json
import logging

logger = logging.getLogger(__name__)


# ============================================================
# GPS VALIDATION & BOUNDS CHECKING
# ============================================================

class GPSBounds:
    """Define valid GPS boundaries (latitude/longitude ranges)."""
    # Algérie typical bounds
    MIN_LAT = 19.0  # Southernmost point
    MAX_LAT = 37.5  # Northernmost point
    MIN_LON = -8.5  # Westernmost point
    MAX_LON = 12.0  # Easternmost point
    
    # Standard GPS bounds (whole world)
    GLOBAL_MIN_LAT = -90.0
    GLOBAL_MAX_LAT = 90.0
    GLOBAL_MIN_LON = -180.0
    GLOBAL_MAX_LON = 180.0


def validate_gps_coordinates(latitude: float, longitude: float, 
                            use_regional_bounds: bool = True) -> Tuple[bool, str]:
    """
    Validate GPS coordinates format and bounds.
    
    Args:
        latitude: Latitude value (-90 to 90)
        longitude: Longitude value (-180 to 180)
        use_regional_bounds: If True, validate against Algeria bounds only
    
    Returns:
        (is_valid, error_message)
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (ValueError, TypeError):
        return False, "Coordonnées invalides (doivent être numériques)"
    
    # Check global bounds first
    if lat < GPSBounds.GLOBAL_MIN_LAT or lat > GPSBounds.GLOBAL_MAX_LAT:
        return False, f"Latitude invalide: {lat} (doit être entre -90 et 90)"
    
    if lon < GPSBounds.GLOBAL_MIN_LON or lon > GPSBounds.GLOBAL_MAX_LON:
        return False, f"Longitude invalide: {lon} (doit être entre -180 et 180)"
    
    # Check regional bounds if requested
    if use_regional_bounds:
        if lat < GPSBounds.MIN_LAT or lat > GPSBounds.MAX_LAT:
            return False, f"Position hors zone (latitude {lat})"
        if lon < GPSBounds.MIN_LON or lon > GPSBounds.MAX_LON:
            return False, f"Position hors zone (longitude {lon})"
    
    return True, ""


def validate_gps_accuracy(accuracy: Optional[float], max_accuracy: float = 100.0) -> Tuple[bool, str]:
    """
    Validate GPS accuracy in meters.
    
    Args:
        accuracy: Accuracy in meters (from browser Geolocation API)
        max_accuracy: Maximum acceptable accuracy (default 100m)
    
    Returns:
        (is_valid, error_message)
    """
    if accuracy is None:
        return True, ""  # Optional accuracy check
    
    try:
        acc = float(accuracy)
    except (ValueError, TypeError):
        return False, "Précision invalide"
    
    if acc < 0:
        return False, "Précision doit être positive"
    
    if acc > max_accuracy:
        return False, f"Précision insuffisante ({acc:.1f}m > {max_accuracy}m)"
    
    return True, ""


# ============================================================
# DISTANCE CALCULATIONS
# ============================================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance between two points on Earth (in meters).
    
    Uses Haversine formula.
    """
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Earth radius in meters
    r = 6371000
    
    return c * r


def calculate_movement_distance(current_lat: float, current_lon: float,
                               previous_lat: Optional[float],
                               previous_lon: Optional[float]) -> float:
    """
    Calculate distance moved from previous position.
    
    Returns:
        Distance in meters (0 if no previous position)
    """
    if previous_lat is None or previous_lon is None:
        return 0.0
    
    return haversine_distance(previous_lat, previous_lon, current_lat, current_lon)


# ============================================================
# LOCATION HISTORY & TRACKING
# ============================================================

class LocationTracker:
    """Track and analyze location history for a technician."""
    
    def __init__(self, technicien_id: int, max_history: int = 1000):
        self.technicien_id = technicien_id
        self.max_history = max_history
        self.positions: List[Dict[str, Any]] = []
    
    def add_position(self, latitude: float, longitude: float, 
                    timestamp: Optional[datetime] = None,
                    accuracy: Optional[float] = None,
                    speed: Optional[float] = None) -> Dict[str, Any]:
        """
        Add a position to history.
        
        Returns:
            Position entry with distance traveled
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        position = {
            'timestamp': timestamp,
            'latitude': float(latitude),
            'longitude': float(longitude),
            'accuracy': accuracy,
            'speed': speed,
            'distance_since_last': 0.0
        }
        
        # Calculate distance from last position
        if self.positions:
            last_pos = self.positions[-1]
            distance = haversine_distance(
                last_pos['latitude'], last_pos['longitude'],
                latitude, longitude
            )
            position['distance_since_last'] = distance
        
        self.positions.append(position)
        
        # Trim old positions
        if len(self.positions) > self.max_history:
            self.positions = self.positions[-self.max_history:]
        
        return position
    
    def get_total_distance(self) -> float:
        """Calculate total distance traveled."""
        return sum(p['distance_since_last'] for p in self.positions)
    
    def get_average_speed(self) -> float:
        """Calculate average speed (positions per minute)."""
        if len(self.positions) < 2:
            return 0.0
        
        time_span = (self.positions[-1]['timestamp'] - self.positions[0]['timestamp']).total_seconds()
        if time_span == 0:
            return 0.0
        
        distance = self.get_total_distance()  # in meters
        minutes = time_span / 60
        
        return (distance / 1000) / (minutes / 60) if minutes > 0 else 0.0  # km/h
    
    def get_recent_positions(self, minutes: int = 30) -> List[Dict[str, Any]]:
        """Get positions from last N minutes."""
        if not self.positions:
            return []
        
        cutoff = self.positions[-1]['timestamp'] - timedelta(minutes=minutes)
        return [p for p in self.positions if p['timestamp'] >= cutoff]
    
    def get_movement_vector(self) -> Optional[Dict[str, Any]]:
        """Get last movement vector (direction and distance)."""
        if len(self.positions) < 2:
            return None
        
        last = self.positions[-1]
        prev = self.positions[-2]
        
        distance = haversine_distance(
            prev['latitude'], prev['longitude'],
            last['latitude'], last['longitude']
        )
        
        if distance < 1:  # Less than 1m, consider stationary
            return None
        
        return {
            'from': {'lat': prev['latitude'], 'lon': prev['longitude']},
            'to': {'lat': last['latitude'], 'lon': last['longitude']},
            'distance': distance,
            'time_delta_seconds': (last['timestamp'] - prev['timestamp']).total_seconds()
        }


# ============================================================
# GEOFENCING
# ============================================================

class Geofence:
    """Define a circular geofence around coordinates."""
    
    def __init__(self, name: str, latitude: float, longitude: float, radius_meters: float):
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.radius = radius_meters
    
    def is_inside(self, latitude: float, longitude: float) -> bool:
        """Check if coordinates are inside geofence."""
        distance = haversine_distance(self.latitude, self.longitude, latitude, longitude)
        return distance <= self.radius
    
    def distance_to_boundary(self, latitude: float, longitude: float) -> float:
        """Distance from point to geofence boundary (negative if inside)."""
        distance = haversine_distance(self.latitude, self.longitude, latitude, longitude)
        return distance - self.radius


def check_geofence_events(current_pos: Dict[str, float],
                         previous_pos: Optional[Dict[str, float]],
                         geofence: Geofence) -> Optional[str]:
    """
    Check if technician entered or exited geofence.
    
    Returns:
        'entered', 'exited', or None
    """
    current_inside = geofence.is_inside(current_pos['latitude'], current_pos['longitude'])
    
    if previous_pos is None:
        return 'entered' if current_inside else None
    
    previous_inside = geofence.is_inside(previous_pos['latitude'], previous_pos['longitude'])
    
    if previous_inside and not current_inside:
        return 'exited'
    elif not previous_inside and current_inside:
        return 'entered'
    
    return None


# ============================================================
# WEBHOOKS & NOTIFICATIONS
# ============================================================

class LocationWebhook:
    """Manage location change webhooks."""
    
    EVENTS = {
        'position_update': 'Nouvelle position',
        'arrived_at_site': 'Arrivée sur site',
        'departed_site': 'Départ du site',
        'long_pause': 'Pause prolongée (> 30 min)',
        'excessive_distance': 'Distance excessive',
    }
    
    def __init__(self):
        self.webhooks: Dict[str, List[str]] = {}
    
    def register(self, event: str, webhook_url: str):
        """Register webhook for event."""
        if event not in self.EVENTS:
            raise ValueError(f"Unknown event: {event}")
        
        if event not in self.webhooks:
            self.webhooks[event] = []
        
        if webhook_url not in self.webhooks[event]:
            self.webhooks[event].append(webhook_url)
    
    def trigger(self, event: str, payload: Dict[str, Any]):
        """Trigger webhooks for event."""
        if event not in self.webhooks:
            return
        
        for webhook_url in self.webhooks[event]:
            try:
                import requests
                requests.post(webhook_url, json=payload, timeout=5)
                logger.info(f"Webhook triggered: {event} → {webhook_url}")
            except Exception as e:
                logger.error(f"Webhook failed: {event} → {webhook_url}: {str(e)}")


# ============================================================
# RATE LIMITING FOR TRACKING
# ============================================================

class TrackingRateLimiter:
    """Limit tracking update frequency per technician."""
    
    def __init__(self, min_interval_seconds: int = 30):
        self.min_interval = min_interval_seconds
        self.last_update: Dict[int, datetime] = {}
    
    def can_update(self, technicien_id: int) -> bool:
        """Check if technician can send tracking update."""
        now = datetime.now(timezone.utc)
        
        if technicien_id not in self.last_update:
            self.last_update[technicien_id] = now
            return True
        
        time_since_last = (now - self.last_update[technicien_id]).total_seconds()
        
        if time_since_last >= self.min_interval:
            self.last_update[technicien_id] = now
            return True
        
        return False
    
    def get_retry_after(self, technicien_id: int) -> int:
        """Get seconds to wait before next update."""
        if technicien_id not in self.last_update:
            return 0
        
        now = datetime.now(timezone.utc)
        time_since_last = (now - self.last_update[technicien_id]).total_seconds()
        
        return max(0, int(self.min_interval - time_since_last))


# Global rate limiter instance
_rate_limiter = TrackingRateLimiter(min_interval_seconds=30)


def can_track_update(technicien_id: int) -> Tuple[bool, Optional[int]]:
    """
    Check if tracking update is allowed.
    
    Returns:
        (allowed, seconds_to_wait_if_not)
    """
    if _rate_limiter.can_update(technicien_id):
        return True, None
    
    retry_after = _rate_limiter.get_retry_after(technicien_id)
    return False, retry_after
