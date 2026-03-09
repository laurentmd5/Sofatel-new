from app import app, db
from models import User, DemandeIntervention, Intervention
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

import pytest


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


def test_get_sla_hours_mapping():
    from sla_utils import get_sla_hours
    assert get_sla_hours('urgent') == 24
    assert get_sla_hours('haute') == 48
    assert get_sla_hours('anythingelse') == 72


def test_violations_endpoint_and_check(client):
    with app.app_context():
        # create a technician and a demande
        tech = User(username='tech_sla', email='t_sla@example.com', password_hash=generate_password_hash('p'), role='technicien', nom='T', prenom='T', telephone='000')
        db.session.add(tech)
        db.session.commit()

        demande = DemandeIntervention(nd='ND1', zone='Z', type_techno='Fibre', nom_client='C', date_demande_intervention=datetime.utcnow() - timedelta(days=10), service='SAV', priorite_traitement='urgent')
        db.session.add(demande)
        db.session.commit()

        it = Intervention(demande_id=demande.id, technicien_id=tech.id, statut='en_cours', date_creation=datetime.utcnow() - timedelta(hours=48))
        db.session.add(it)
        db.session.commit()

    # login as admin-like user
    with app.app_context():
        admin = User(username='admin_sla', email='a@a', password_hash=generate_password_hash('p'), role='chef_pur', nom='A', prenom='A', telephone='000')
        db.session.add(admin)
        db.session.commit()

    client.post('/login', data={'username': 'admin_sla', 'password': 'p'})

    r = client.get('/api/sla/violations')
    assert r.status_code == 200
    data = r.get_json()
    assert data['success'] is True
    assert isinstance(data['violations'], list)
    assert len(data['violations']) >= 1

    r2 = client.post('/api/sla/check', json={'send_alerts': False})
    assert r2.status_code == 200
    d2 = r2.get_json()
    assert d2['success'] is True
    assert d2['violations_count'] >= 1
    assert d2['alerted'] == 0
