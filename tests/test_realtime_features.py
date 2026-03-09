"""
Tests for real-time features: event bus, state change notifications, and streaming.
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from app import app, db
from models import User, Intervention, DemandeIntervention
from event_bus import (
    get_event_bus, EventType, Event, InMemoryEventBus,
    publish_event, subscribe_to_events
)
from werkzeug.security import generate_password_hash


@pytest.fixture
def client():
    """Test client with in-memory database."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def auth_user(client):
    """Create and authenticate a test user."""
    with app.app_context():
        admin = User(
            username='admin_test',
            email='admin@test.com',
            password_hash=generate_password_hash('password'),
            role='chef_pur',
            nom='Admin',
            prenom='Test',
            telephone='000'
        )
        db.session.add(admin)
        db.session.commit()
        admin_id = admin.id

    client.post('/login', data={'username': 'admin_test', 'password': 'password'})
    return admin_id


@pytest.fixture
def intervention(client):
    """Create a test intervention."""
    with app.app_context():
        tech = User(
            username='tech_test',
            email='tech@test.com',
            password_hash=generate_password_hash('p'),
            role='technicien',
            nom='Tech',
            prenom='Test',
            telephone='000'
        )
        demand = DemandeIntervention(
            nd='ND001',
            zone='zone1',
            nom_client='Test Client',
            type_techno='Fibre',
            service='Production',
            priorite_traitement='NORMALE',
            date_demande_intervention=datetime.utcnow()
        )
        db.session.add(tech)
        db.session.add(demand)
        db.session.commit()

        it = Intervention(
            demande_id=demand.id,
            technicien_id=tech.id,
            statut='nouveau'
        )
        db.session.add(it)
        db.session.commit()
        
        return it.id, tech.id


# --- Event Bus Tests ---

class TestEventBus:
    """Tests for the event bus infrastructure."""

    def test_event_creation(self):
        """Test Event dataclass creation."""
        event = Event(
            type=EventType.INTERVENTION_CREATED,
            entity_id=1,
            entity_type='intervention',
            user_id=5,
            zone_id=3,
            data={'key': 'value'}
        )
        assert event.type == EventType.INTERVENTION_CREATED
        assert event.entity_id == 1
        assert event.entity_type == 'intervention'
        assert event.user_id == 5
        assert event.zone_id == 3
        assert event.data == {'key': 'value'}
        assert event.timestamp is not None

    def test_event_to_dict(self):
        """Test Event serialization to dict."""
        event = Event(
            type=EventType.INTERVENTION_STARTED,
            entity_id=42,
            entity_type='intervention',
            data={'old_state': 'ASSIGNED', 'new_state': 'IN_PROGRESS'}
        )
        d = event.to_dict()
        assert d['type'] == 'intervention.started'
        assert d['entity_id'] == 42
        assert d['entity_type'] == 'intervention'
        assert 'timestamp' in d
        assert d['data']['old_state'] == 'ASSIGNED'

    def test_event_to_json(self):
        """Test Event serialization to JSON."""
        event = Event(
            type=EventType.INTERVENTION_COMPLETED,
            entity_id=7,
            entity_type='intervention'
        )
        json_str = event.to_json()
        parsed = json.loads(json_str)
        assert parsed['type'] == 'intervention.completed'
        assert parsed['entity_id'] == 7

    def test_in_memory_bus_publish_subscribe(self):
        """Test event pub/sub."""
        bus = InMemoryEventBus()
        received_events = []

        def callback(event):
            received_events.append(event)

        bus.subscribe([EventType.INTERVENTION_CREATED], callback)

        event = Event(
            type=EventType.INTERVENTION_CREATED,
            entity_id=1,
            entity_type='intervention'
        )
        bus.publish(event)

        assert len(received_events) == 1
        assert received_events[0].entity_id == 1

    def test_bus_filters_events(self):
        """Test that bus only notifies matching subscriptions."""
        bus = InMemoryEventBus()
        created_events = []
        completed_events = []

        bus.subscribe([EventType.INTERVENTION_CREATED], lambda e: created_events.append(e))
        bus.subscribe([EventType.INTERVENTION_COMPLETED], lambda e: completed_events.append(e))

        bus.publish(Event(type=EventType.INTERVENTION_CREATED, entity_id=1, entity_type='intervention'))
        bus.publish(Event(type=EventType.INTERVENTION_COMPLETED, entity_id=2, entity_type='intervention'))

        assert len(created_events) == 1
        assert len(completed_events) == 1

    def test_subscription_with_filter_function(self):
        """Test that subscriptions can filter by custom function."""
        bus = InMemoryEventBus()
        zone3_events = []

        # Subscribe to INTERVENTION_STARTED events only for zone_id=3
        bus.subscribe(
            [EventType.INTERVENTION_STARTED],
            lambda e: zone3_events.append(e),
            filter_fn=lambda e: e.zone_id == 3
        )

        bus.publish(Event(type=EventType.INTERVENTION_STARTED, entity_id=1, entity_type='intervention', zone_id=2))
        bus.publish(Event(type=EventType.INTERVENTION_STARTED, entity_id=2, entity_type='intervention', zone_id=3))
        bus.publish(Event(type=EventType.INTERVENTION_STARTED, entity_id=3, entity_type='intervention', zone_id=3))

        assert len(zone3_events) == 2

    def test_event_history_retention(self):
        """Test that event bus keeps history."""
        bus = InMemoryEventBus(max_history=10)

        for i in range(15):
            bus.publish(Event(type=EventType.INTERVENTION_CREATED, entity_id=i, entity_type='intervention'))

        history = bus.get_recent_events(limit=100)
        assert len(history) == 10  # Only last 10 retained

    def test_publish_event_convenience_function(self):
        """Test the publish_event convenience function."""
        bus = get_event_bus()
        bus.clear_history()

        received = []
        subscribe_to_events([EventType.SLA_VIOLATION], lambda e: received.append(e))

        publish_event(
            event_type=EventType.SLA_VIOLATION,
            entity_id=99,
            entity_type='intervention',
            user_id=5,
            zone_id=2,
            data={'hours_overdue': 5}
        )

        assert len(received) == 1
        assert received[0].entity_id == 99
        assert received[0].data['hours_overdue'] == 5


# --- State Machine & Event Integration Tests ---

class TestStateChangeEvents:
    """Tests for state transitions publishing events."""

    def test_intervention_state_change_publishes_event(self, client, auth_user, intervention):
        """Test that changing intervention state publishes event."""
        it_id, tech_id = intervention
        
        with app.app_context():
            bus = get_event_bus()
            bus.clear_history()

            it = Intervention.query.get(it_id)
            user = User.query.get(auth_user)

            # Transition from CREATED to ASSIGNED
            it.transition_state(Intervention.STATE_ASSIGNED, user=user)
            db.session.commit()

            # Check event was published
            history = bus.get_recent_events(limit=100)
            assert len(history) > 0
            
            # Find the INTERVENTION_ASSIGNED event
            assigned_event = next((e for e in history if e.type == EventType.INTERVENTION_ASSIGNED), None)
            assert assigned_event is not None
            assert assigned_event.entity_id == it_id
            assert assigned_event.data['old_state'] == Intervention.STATE_CREATED
            assert assigned_event.data['new_state'] == Intervention.STATE_ASSIGNED

    def test_full_state_machine_publishes_events(self, client, auth_user, intervention):
        """Test that full state transitions publish appropriate events."""
        it_id, tech_id = intervention

        with app.app_context():
            bus = get_event_bus()
            bus.clear_history()

            it = Intervention.query.get(it_id)
            user = User.query.get(auth_user)
            tech = User.query.get(tech_id)

            # CREATED -> ASSIGNED
            it.transition_state(Intervention.STATE_ASSIGNED, user=user)
            db.session.commit()

            # ASSIGNED -> IN_PROGRESS
            it.transition_state(Intervention.STATE_IN_PROGRESS, user=tech)
            db.session.commit()

            # IN_PROGRESS -> COMPLETED
            it.transition_state(Intervention.STATE_COMPLETED, user=tech)
            db.session.commit()

            # Check events
            history = bus.get_recent_events(limit=100)
            event_types = [e.type for e in history]

            assert EventType.INTERVENTION_ASSIGNED in event_types
            assert EventType.INTERVENTION_STARTED in event_types
            assert EventType.INTERVENTION_COMPLETED in event_types


# --- Streaming API Tests ---

class TestStreamingEndpoints:
    """Tests for SSE streaming endpoints."""

    def test_stream_interventions_returns_sse(self, client, auth_user, intervention):
        """Test that stream endpoint returns SSE format."""
        response = client.get('/api/stream/interventions?once=1&interval=0')
        assert response.status_code == 200
        assert response.mimetype == 'text/event-stream'
        
        data = response.get_data(as_text=True)
        assert 'data:' in data

    def test_stream_interventions_includes_counters(self, client, auth_user, intervention):
        """Test that stream response includes counters."""
        it_id, _ = intervention

        response = client.get('/api/stream/interventions?once=1&interval=0')
        data = response.get_data(as_text=True)
        
        # Parse SSE frame
        part = data.split('data:', 1)[1].strip()
        part = part.split('\n\n', 1)[0]
        payload = json.loads(part)

        assert 'counters' in payload
        assert isinstance(payload['counters'], dict)
        assert 'count' in payload

    def test_stream_with_state_filter(self, client, auth_user, intervention):
        """Test streaming with state filter."""
        it_id, tech_id = intervention

        with app.app_context():
            it = Intervention.query.get(it_id)
            user = User.query.get(auth_user)
            it.transition_state(Intervention.STATE_ASSIGNED, user=user)
            db.session.commit()

        response = client.get('/api/stream/interventions?once=1&state=ASSIGNED')
        data = response.get_data(as_text=True)
        
        part = data.split('data:', 1)[1].strip()
        part = part.split('\n\n', 1)[0]
        payload = json.loads(part)

        # Should have interventions in ASSIGNED state
        for it in payload['interventions']:
            assert it['state'] == 'ASSIGNED' or it['statut'] == 'affecte'

    def test_dashboard_summary_endpoint(self, client, auth_user, intervention):
        """Test instant dashboard summary endpoint."""
        response = client.get('/api/stream/dashboard-summary')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert 'summary' in data
        assert 'counters' in data['summary']
        assert 'timestamp' in data['summary']

    def test_recent_events_endpoint(self, client, auth_user, intervention):
        """Test recent events retrieval."""
        it_id, tech_id = intervention

        with app.app_context():
            it = Intervention.query.get(it_id)
            user = User.query.get(auth_user)
            it.transition_state(Intervention.STATE_ASSIGNED, user=user)
            db.session.commit()

        response = client.get('/api/stream/events/recent')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert 'events' in data
        assert len(data['events']) > 0

    def test_recent_events_by_type(self, client, auth_user, intervention):
        """Test filtering recent events by type."""
        it_id, tech_id = intervention

        with app.app_context():
            it = Intervention.query.get(it_id)
            user = User.query.get(auth_user)
            it.transition_state(Intervention.STATE_ASSIGNED, user=user)
            db.session.commit()

        response = client.get('/api/stream/events/recent?type=intervention.assigned')
        data = response.get_json()
        
        # All events should be INTERVENTION_ASSIGNED
        for event in data['events']:
            assert event['type'] == 'intervention.assigned'


# --- Concurrency Tests ---

class TestConcurrencyAndStability:
    """Tests for concurrent access and state machine stability."""

    def test_concurrent_state_transitions_blocked_correctly(self, client, auth_user, intervention):
        """Test that invalid concurrent transitions are prevented."""
        it_id, tech_id = intervention

        with app.app_context():
            it = Intervention.query.get(it_id)
            user = User.query.get(auth_user)

            # First transition
            it.transition_state(Intervention.STATE_ASSIGNED, user=user)
            db.session.commit()

            # Try invalid transition (should fail)
            it2 = Intervention.query.get(it_id)
            with pytest.raises(Exception):  # Should raise InvalidStateTransition
                it2.transition_state(Intervention.STATE_CLOSED, user=user)

    def test_terminal_state_immutability(self, client, auth_user, intervention):
        """Test that CLOSED state is immutable."""
        it_id, tech_id = intervention

        with app.app_context():
            it = Intervention.query.get(it_id)
            user = User.query.get(auth_user)
            tech = User.query.get(tech_id)

            # Transition through states to CLOSED
            it.transition_state(Intervention.STATE_ASSIGNED, user=user)
            it.transition_state(Intervention.STATE_IN_PROGRESS, user=tech)
            it.transition_state(Intervention.STATE_COMPLETED, user=tech)
            
            # Set completeness fields to 100% for validation to succeed
            it.photos = "some_photo_data"
            it.signature_client = "signature_data"
            it.date_debut = datetime.utcnow()
            it.date_fin = datetime.utcnow()
            it.diagnostic_technicien = "Diagnostic complete"
            
            it.transition_state(Intervention.STATE_VALIDATED, user=user)
            it.transition_state(Intervention.STATE_CLOSED, user=user)
            db.session.commit()

            # Try to modify CLOSED intervention
            it2 = Intervention.query.get(it_id)
            from models import ImmutableStateError
            with pytest.raises(ImmutableStateError):
                it2.transition_state(Intervention.STATE_IN_PROGRESS, user=user)

    def test_event_bus_thread_safety(self):
        """Test that event bus is thread-safe."""
        bus = InMemoryEventBus()
        received = []

        bus.subscribe([EventType.INTERVENTION_CREATED], lambda e: received.append(e))

        # Publish from multiple threads
        import threading
        threads = []
        for i in range(10):
            t = threading.Thread(
                target=lambda idx=i: bus.publish(
                    Event(type=EventType.INTERVENTION_CREATED, entity_id=idx, entity_type='intervention')
                )
            )
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(received) == 10


class TestRealTimeStressScenarios:
    """Stress tests for real-time features."""

    def test_high_frequency_events(self):
        """Test handling many events in short time."""
        bus = InMemoryEventBus()
        received = []

        bus.subscribe([EventType.INTERVENTION_CREATED], lambda e: received.append(e))

        # Simulate 100 rapid interventions
        for i in range(100):
            bus.publish(Event(type=EventType.INTERVENTION_CREATED, entity_id=i, entity_type='intervention'))

        assert len(received) == 100
        assert len(bus.get_recent_events(limit=200)) == 100

    def test_high_frequency_state_changes(self, client, auth_user):
        """Test rapid state changes don't break system."""
        with app.app_context():
            # Create multiple interventions
            tech = User.query.first()
            user = User.query.filter_by(role='chef_pur').first()
            
            for i in range(10):
                demand = DemandeIntervention(
                    nd=f'ND{i}',
                    zone=f'zone{i}',
                    nom_client=f'Client {i}',
                    type_techno='Fibre',
                    service='Production',
                    priorite_traitement='NORMALE',
                    date_demande_intervention=datetime.utcnow()
                )
                it = Intervention(
                    demande_id=None,  # Will be set after commit
                    technicien_id=tech.id,
                    statut='nouveau'
                )
                db.session.add(demand)
                db.session.flush()
                
                it.demande_id = demand.id
                db.session.add(it)

            db.session.commit()

            # Rapid transitions
            for it in Intervention.query.limit(10):
                try:
                    it.transition_state(Intervention.STATE_ASSIGNED, user=user)
                    it.transition_state(Intervention.STATE_IN_PROGRESS, user=tech)
                    it.transition_state(Intervention.STATE_COMPLETED, user=tech)
                    db.session.commit()
                except Exception as e:
                    pytest.fail(f"Rapid transition failed: {e}")
