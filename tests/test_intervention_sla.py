import pytest
from app import app, db
from models import User, Intervention, InterventionHistory
from werkzeug.security import generate_password_hash
from datetime import datetime


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
def manager_user(client):
    with app.app_context():
        user = User(
            username='manager',
            email='manager@example.com',
            password_hash=generate_password_hash('pwd'),
            role='chef_pur',
            nom='Manager',
            prenom='User',
            telephone='000'
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def tech_user(client):
    with app.app_context():
        user = User(
            username='tech',
            email='tech@example.com',
            password_hash=generate_password_hash('pwd'),
            role='technicien',
            nom='Tech',
            prenom='User',
            telephone='111'
        )
        db.session.add(user)
        db.session.commit()
        return user


def login(client, username, password='pwd'):
    # Do not follow redirects to avoid triggering dashboard rendering during tests
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=False)


def test_ack_sla_sets_fields_and_history(client, tech_user):
    with app.app_context():
        tech = User.query.filter_by(username='tech').first()
        # Create an intervention for this tech
        inter = Intervention(demande_id=1, technicien_id=tech.id, statut='en_cours', date_debut=datetime.utcnow())
        db.session.add(inter)
        db.session.commit()
        inter_id = inter.id

    # login as tech
    resp = login(client, 'tech')
    assert resp.status_code in [200, 302]

    # Call ack_sla (blueprint is mounted under /interventions)
    r = client.post(f'/interventions/api/intervention/{inter_id}/ack_sla')
    assert r.status_code == 200
    data = r.get_json()
    assert data.get('success') is True

    with app.app_context():
        i = db.session.get(Intervention, inter_id)
        tech = User.query.filter_by(username='tech').first()
        assert i.sla_acknowledged_by == tech.id
        assert i.sla_acknowledged_at is not None
        h = InterventionHistory.query.filter_by(intervention_id=inter_id, action='ack_sla').first()
        assert h is not None
        assert h.user_id == tech.id


def test_manager_approve_sets_validation_and_history(client, manager_user, tech_user):
    with app.app_context():
        tech = User.query.filter_by(username='tech').first()
        inter = Intervention(demande_id=1, technicien_id=tech.id, statut='en_cours', date_debut=datetime.utcnow())
        db.session.add(inter)
        db.session.commit()
        inter_id = inter.id

    # login as manager
    resp = login(client, 'manager')
    assert resp.status_code in [200, 302]

    r = client.post(f'/interventions/api/intervention/{inter_id}/manager_approve')
    assert r.status_code == 200
    data = r.get_json()
    assert data.get('success') is True

    with app.app_context():
        i = db.session.get(Intervention, inter_id)
        manager = User.query.filter_by(username='manager').first()
        assert i.valide_par == manager.id
        assert i.date_validation is not None
        assert i.statut == 'valide'
        h = InterventionHistory.query.filter_by(intervention_id=inter_id, action='manager_approve').first()
        assert h is not None
        assert h.user_id == manager.id
