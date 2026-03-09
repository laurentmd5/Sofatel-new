import pytest
from app import app, db
from models import User, DemandeIntervention, Intervention
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
def admin_user(client):
    with app.app_context():
        user = User(username='admin2', email='admin2@example.com', password_hash=generate_password_hash('admin'), role='chef_pur', nom='Admin', prenom='User', telephone='000')
        db.session.add(user)
        db.session.commit()
        return user


def test_creer_intervention_web_uses_mobile_handler(client, admin_user):
    # Create a demande
    with app.app_context():
        demande = DemandeIntervention(
            nd='ND1', zone='Z1', type_techno='Fibre', nom_client='Client', date_demande_intervention=datetime.utcnow(), service='Production'
        )
        db.session.add(demande)
        db.session.commit()
        demande_id = demande.id

    # Login
    resp = client.post('/login', data={'username': 'admin2', 'password': 'admin'}, follow_redirects=True)
    assert resp.status_code == 200

    # Post form to create intervention
    resp2 = client.post('/interventions/creer', data={'demande_id': str(demande_id)}, follow_redirects=True)
    assert resp2.status_code == 200

    # Check intervention created
    with app.app_context():
        it = Intervention.query.filter_by(demande_id=demande_id).first()
        assert it is not None
        assert it.demande_id == demande_id
