import pytest
from app import app, db
from models import User, LeaveRequest, Intervention, DemandeIntervention
from werkzeug.security import generate_password_hash
from datetime import datetime


def setup_app_client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app.test_client()


def test_create_and_list_leave():
    client = setup_app_client()
    with app.app_context():
        db.create_all()
        user = User(username='tech', email='t@t', password_hash=generate_password_hash('p'), role='technicien', nom='T', prenom='T', telephone='000')
        db.session.add(user)
        db.session.commit()
        uid = user.id

    # login
    client.post('/login', data={'username': 'tech', 'password': 'p'})

    # create leave
    resp = client.post('/api/rh/conges', json={'technicien_id': uid, 'date_debut': '2026-01-01', 'date_fin': '2026-01-02', 'type': 'conge'})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['success'] is True

    # list leaves
    resp2 = client.get('/api/rh/conges')
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert data2['success'] is True
    assert len(data2['leaves']) == 1


def test_get_hours_from_interventions():
    client = setup_app_client()
    with app.app_context():
        db.create_all()
        user = User(username='tech2', email='t2@t', password_hash=generate_password_hash('p'), role='technicien', nom='T2', prenom='T2', telephone='000')
        db.session.add(user)
        db.session.commit()
        uid = user.id
        demande = DemandeIntervention(nd='NDX', zone='Z', type_techno='Fibre', nom_client='ClientX', date_demande_intervention=datetime.utcnow(), service='Production')
        db.session.add(demande)
        db.session.commit()
        it = Intervention(demande_id=demande.id, technicien_id=uid, statut='termine', date_debut=datetime(2026,1,1,8,0), date_fin=datetime(2026,1,1,12,0))
        db.session.add(it)
        db.session.commit()

    client.post('/login', data={'username': 'tech2', 'password': 'p'})
    resp = client.get(f'/api/rh/heures?technicien_id={uid}&debut=2026-01-01&fin=2026-01-02')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['total_hours'] >= 4.0
