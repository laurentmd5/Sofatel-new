"""
Event Bus for Real-Time System Updates

Provides a publish-subscribe mechanism for intervention state changes, SLA violations,
and other system events. Supports both in-memory and Redis backends.

Architecture:
- Publishers: Routes/services emit events (state change, SLA violation, etc.)
- Subscribers: Dashboard/stream endpoints consume events
- Backend: In-memory (default) or Redis (scalable production)
"""

import json
import threading
from datetime import datetime
from typing import Callable, Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod


class EventType(Enum):
    """Event types emitted by the system."""
    INTERVENTION_CREATED = "intervention.created"
    INTERVENTION_STATE_CHANGED = "intervention.state_changed"
    INTERVENTION_ASSIGNED = "intervention.assigned"
    INTERVENTION_STARTED = "intervention.started"
    INTERVENTION_COMPLETED = "intervention.completed"
    INTERVENTION_VALIDATED = "intervention.validated"
    INTERVENTION_CLOSED = "intervention.closed"
    SLA_VIOLATION = "sla.violation"
    SLA_RESOLVED = "sla.resolved"
    STOCK_ALERT = "stock.alert"
    USER_ASSIGNED = "user.assigned"


@dataclass
class Event:
    """Represents a system event."""
    type: EventType
    entity_id: int
    entity_type: str
    user_id: Optional[int] = None
    timestamp: datetime = None
    data: Dict[str, Any] = None
    zone_id: Optional[int] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.data is None:
            self.data = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary (JSON-serializable)."""
        return {
            'type': self.type.value,
            'entity_id': self.entity_id,
            'entity_type': self.entity_type,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'zone_id': self.zone_id,
        }

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class EventSubscription:
    """Represents a subscription to events."""

    def __init__(self, event_types: List[EventType], callback: Callable, filter_fn: Optional[Callable] = None):
        """
        Args:
            event_types: List of EventType to subscribe to
            callback: Function called with Event when event occurs
            filter_fn: Optional filter function(event) -> bool
        """
        self.event_types = event_types
        self.callback = callback
        self.filter_fn = filter_fn or (lambda e: True)

    def matches(self, event: Event) -> bool:
        """Check if event matches subscription."""
        return event.type in self.event_types and self.filter_fn(event)


class EventBusBackend(ABC):
    """Abstract base for event bus backends."""

    @abstractmethod
    def publish(self, event: Event):
        """Publish an event."""
        pass

    @abstractmethod
    def subscribe(self, event_types: List[EventType], callback: Callable, filter_fn: Optional[Callable] = None):
        """Subscribe to events."""
        pass

    @abstractmethod
    def get_recent_events(self, limit: int = 100) -> List[Event]:
        """Get recent events (for dashboard initialization)."""
        pass


class InMemoryEventBus(EventBusBackend):
    """In-memory event bus for development/single-instance deployments."""

    def __init__(self, max_history: int = 10000):
        self.subscriptions: List[EventSubscription] = []
        self.event_history: List[Event] = []
        self.max_history = max_history
        self._lock = threading.RLock()

    def publish(self, event: Event):
        """Publish event to all matching subscribers."""
        with self._lock:
            # Store in history
            self.event_history.append(event)
            if len(self.event_history) > self.max_history:
                self.event_history = self.event_history[-self.max_history:]

            # Notify subscribers
            for sub in self.subscriptions:
                if sub.matches(event):
                    try:
                        sub.callback(event)
                    except Exception as e:
                        # Log but don't break other subscribers
                        import logging
                        logging.exception(f"Error in event callback: {e}")

    def subscribe(self, event_types: List[EventType], callback: Callable, filter_fn: Optional[Callable] = None):
        """Add a subscription."""
        with self._lock:
            sub = EventSubscription(event_types, callback, filter_fn)
            self.subscriptions.append(sub)

    def get_recent_events(self, limit: int = 100) -> List[Event]:
        """Get recent events."""
        with self._lock:
            return self.event_history[-limit:]

    def clear_history(self):
        """Clear event history (useful for tests)."""
        with self._lock:
            self.event_history.clear()


# Global event bus instance
_event_bus: Optional[InMemoryEventBus] = None


def get_event_bus() -> EventBusBackend:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = InMemoryEventBus()
    return _event_bus


def publish_event(event_type: EventType, entity_id: int, entity_type: str = "intervention",
                  user_id: Optional[int] = None, zone_id: Optional[int] = None, data: Optional[Dict] = None):
    """Convenience function to publish an event."""
    event = Event(
        type=event_type,
        entity_id=entity_id,
        entity_type=entity_type,
        user_id=user_id,
        zone_id=zone_id,
        data=data or {}
    )
    get_event_bus().publish(event)


def subscribe_to_events(event_types: List[EventType], callback: Callable, filter_fn: Optional[Callable] = None):
    """Convenience function to subscribe to events."""
    get_event_bus().subscribe(event_types, callback, filter_fn)
