import pytest
from app import app, db
from models import User, DemandeIntervention, Intervention, InvalidStateTransition
from werkzeug.security import generate_password_hash


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        # Re-create engine for the test app so we don't talk to the real DB
        try:
            eng = db.get_engine(app)
            eng.dispose()
        except Exception:
            pass
        db.session.remove()
        db.drop_all()
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def users(client):
    manager = User(username='manager', email='m@example.com', password_hash=generate_password_hash('pass'), role='chef_pur', nom='M', prenom='An', telephone='000')
    chef_zone = User(username='chef', email='c@example.com', password_hash=generate_password_hash('pass'), role='chef_zone', nom='C', prenom='Z', telephone='000')
    tech = User(username='tech', email='t@example.com', password_hash=generate_password_hash('pass'), role='technicien', nom='T', prenom='E', telephone='000')
    db.session.add_all([manager, chef_zone, tech])
    db.session.commit()
    return {'manager': manager, 'chef': chef_zone, 'tech': tech}


@pytest.fixture
def intervention(client, users):
    dem = DemandeIntervention(nd='ND1', zone='DAKAR', type_techno='Fibre', nom_client='X', date_demande_intervention='2026-01-01', service='SAV')
    db.session.add(dem)
    db.session.commit()
    interv = Intervention(demande_id=dem.id, technicien_id=users['tech'].id)
    db.session.add(interv)
    db.session.commit()
    return interv


@pytest.fixture
def manager_client(client, users):
    return users['manager']


def test_compute_completeness_percentage(client, users, intervention):
    with app.app_context():
        # Initially required fields are empty -> score 0
        intervention.update_completeness()
        db.session.commit()
        assert intervention.completeness_score == 0

        # Fill 2 of 4 fields -> 50%
        intervention.numero = '123'
        intervention.diagnostic_technicien = 'checked'
        intervention.update_completeness()
        db.session.commit()
        assert intervention.completeness_score == 50

        # Fill all required -> 100%
        intervention.pieces = 'OK'
        intervention.debit_cable_montant = '100Mbps'
        intervention.update_completeness()
        db.session.commit()
        assert intervention.completeness_score == 100


def test_block_validation_if_incomplete(client, users, intervention):
    with app.app_context():
        m = users['manager']
        # ensure incomplete
        intervention.numero = 'ABC'
        intervention.update_completeness()
        db.session.commit()
        assert intervention.completeness_score < 100

        # Attempt to validate should raise InvalidStateTransition
        intervention._set_state(Intervention.STATE_COMPLETED)
        db.session.commit()
        with pytest.raises(InvalidStateTransition) as exc:
            intervention.transition_state(Intervention.STATE_VALIDATED, user=m)
        assert 'Completeness' in str(exc.value) or 'required fields' in str(exc.value)


def test_allow_validation_when_complete(client, users, intervention):
    with app.app_context():
        m = users['manager']
        # fill required
        intervention.numero = 'N'
        intervention.diagnostic_technicien = 'D'
        intervention.pieces = 'P'
        intervention.debit_cable_montant = '100Mbps'
        intervention.update_completeness()
        db.session.commit()
        assert intervention.completeness_score == 100

        # Move to completed then validate
        intervention._set_state(Intervention.STATE_COMPLETED)
        intervention.transition_state(Intervention.STATE_VALIDATED, user=m)
        db.session.commit()
        assert intervention.state == Intervention.STATE_VALIDATED
        # Score persisted
        assert intervention.completeness_score == 100
