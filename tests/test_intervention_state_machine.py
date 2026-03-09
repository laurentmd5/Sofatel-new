import pytest
from app import app, db
from models import User, DemandeIntervention, Intervention, InterventionHistory
from werkzeug.security import generate_password_hash


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def users(client):
    # Use the existing app context provided by the `client` fixture so instances remain bound
    manager = User(username='manager', email='m@example.com', password_hash=generate_password_hash('pass'), role='chef_pur', nom='M', prenom='An', telephone='000')
    chef_zone = User(username='chef', email='c@example.com', password_hash=generate_password_hash('pass'), role='chef_zone', nom='C', prenom='Z', telephone='000')
    tech = User(username='tech', email='t@example.com', password_hash=generate_password_hash('pass'), role='technicien', nom='T', prenom='E', telephone='000')
    db.session.add_all([manager, chef_zone, tech])
    db.session.commit()
    return {'manager': manager, 'chef': chef_zone, 'tech': tech}


@pytest.fixture
def intervention(client, users):
    # Use existing app context from `client` fixture
    # Required 'service' per model constraints
    dem = DemandeIntervention(nd='ND1', zone='DAKAR', type_techno='Fibre', nom_client='X', date_demande_intervention='2026-01-01', service='SAV')
    db.session.add(dem)
    db.session.commit()
    interv = Intervention(demande_id=dem.id, technicien_id=users['tech'].id)
    # initially db 'statut' default 'nouveau' maps to CREATED
    db.session.add(interv)
    db.session.commit()
    return interv


def test_full_valid_transition_sequence(client, users, intervention):
    with app.app_context():
        m = users['manager']
        t = users['tech']
        # CREATED -> ASSIGNED (manager)
        intervention.transition_state(Intervention.STATE_ASSIGNED, user=m)
        db.session.commit()
        assert intervention.state == Intervention.STATE_ASSIGNED

        # ASSIGNED -> IN_PROGRESS (technician owner)
        intervention.transition_state(Intervention.STATE_IN_PROGRESS, user=t)
        db.session.commit()
        assert intervention.state == Intervention.STATE_IN_PROGRESS

        # IN_PROGRESS -> COMPLETED (technician)
        intervention.transition_state(Intervention.STATE_COMPLETED, user=t)
        db.session.commit()
        assert intervention.state == Intervention.STATE_COMPLETED

        # COMPLETED -> VALIDATED (manager)
        # Fill required fields so completeness is 100%
        intervention.numero = 'N123'
        intervention.diagnostic_technicien = 'OK'
        intervention.pieces = 'OK'
        intervention.debit_cable_montant = '100Mbps'
        intervention.update_completeness()
        db.session.commit()
        intervention.transition_state(Intervention.STATE_VALIDATED, user=m)
        db.session.commit()
        assert intervention.state == Intervention.STATE_VALIDATED

        # VALIDATED -> CLOSED (manager)
        intervention.transition_state(Intervention.STATE_CLOSED, user=m)
        db.session.commit()
        assert intervention.state == Intervention.STATE_CLOSED


def test_invalid_transitions_raise(client, users, intervention):
    with app.app_context():
        chef = users['chef']
        tech = users['tech']
        # CREATED -> IN_PROGRESS is invalid
        with pytest.raises(Exception) as exc:
            intervention.transition_state(Intervention.STATE_IN_PROGRESS, user=tech)
        assert 'Invalid transition' in str(exc.value) or 'not allowed' in str(exc.value) or isinstance(exc.value.value, Exception)

        # tech trying to assign -> should raise PermissionError
        with pytest.raises(Exception) as exc2:
            intervention.transition_state(Intervention.STATE_ASSIGNED, user=tech)
        assert 'assign' in str(exc2.value) or 'Only' in str(exc2.value)

        # Manager assigns
        intervention.transition_state(Intervention.STATE_ASSIGNED, user=chef)
        db.session.commit()
        assert intervention.state == Intervention.STATE_ASSIGNED

        # Another tech (not owner) tries to start
        other = User(username='other', email='o@example.com', password_hash=generate_password_hash('p'), role='technicien', nom='O', prenom='T', telephone='000')
        db.session.add(other)
        db.session.commit()
        with pytest.raises(Exception) as exc3:
            intervention.transition_state(Intervention.STATE_IN_PROGRESS, user=other)
        assert 'only start their own' in str(exc3.value) or 'Technician' in str(exc3.value)


def test_immutable_after_validated(client, users, intervention):
    with app.app_context():
        m = users['manager']
        t = users['tech']
        # Move to VALIDATED state
        intervention.transition_state(Intervention.STATE_ASSIGNED, user=m)
        intervention.transition_state(Intervention.STATE_IN_PROGRESS, user=t)
        intervention.transition_state(Intervention.STATE_COMPLETED, user=t)
        # ensure completeness before validating
        intervention.numero = 'N123'
        intervention.diagnostic_technicien = 'OK'
        intervention.pieces = 'OK'
        intervention.debit_cable_montant = '100Mbps'
        intervention.update_completeness()
        db.session.commit()
        intervention.transition_state(Intervention.STATE_VALIDATED, user=m)
        db.session.commit()

        assert intervention.state == Intervention.STATE_VALIDATED
        # Trying to change after VALIDATED should raise ImmutableStateError
        with pytest.raises(Exception) as exc:
            intervention.transition_state(Intervention.STATE_CLOSED, user=t)
        assert 'immutable' in str(exc.value) or 'Cannot modify' in str(exc.value) or 'Only managers' in str(exc.value)


def test_closed_is_terminal(client, users, intervention):
    with app.app_context():
        m = users['manager']
        t = users['tech']
        intervention.transition_state(Intervention.STATE_ASSIGNED, user=m)
        intervention.transition_state(Intervention.STATE_IN_PROGRESS, user=t)
        intervention.transition_state(Intervention.STATE_COMPLETED, user=t)
        # ensure completeness before validating
        intervention.numero = 'N123'
        intervention.diagnostic_technicien = 'OK'
        intervention.pieces = 'OK'
        intervention.debit_cable_montant = '100Mbps'
        intervention.update_completeness()
        db.session.commit()
        intervention.transition_state(Intervention.STATE_VALIDATED, user=m)
        intervention.transition_state(Intervention.STATE_CLOSED, user=m)
        db.session.commit()
        assert intervention.state == Intervention.STATE_CLOSED
        # Any further transition is forbidden
        with pytest.raises(Exception):
            intervention.transition_state(Intervention.STATE_ASSIGNED, user=m)
