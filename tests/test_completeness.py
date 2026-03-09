from app import app, db
from models import User, Intervention
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


def test_compute_intervention_completeness():
    from completeness_utils import compute_intervention_completeness

    it = Intervention(
        demande_id=1,
        technicien_id=1,
        photos='["/a.jpg"]',
        signature_client='sigdata',
        date_debut=datetime.utcnow(),
        date_fin=datetime.utcnow() + timedelta(hours=1),
        diagnostic_technicien='diagnostic ok',
    )

    res = compute_intervention_completeness(it)
    assert res['score'] == 100
    assert all(res['details'].values())


def test_completude_endpoints(client):
    with app.app_context():
        # create an admin and a tech user
        admin = User(username='admin_comp', email='a@a', password_hash=generate_password_hash('p'), role='chef_pur', nom='A', prenom='A', telephone='000')
        tech = User(username='tech_comp', email='t@t', password_hash=generate_password_hash('p'), role='technicien', nom='T', prenom='T', telephone='000')
        db.session.add(admin)
        db.session.add(tech)
        db.session.commit()

        # create an intervention with full completeness for today
        it1 = Intervention(demande_id=1, technicien_id=tech.id, photos='["/a.jpg"]', signature_client='s', date_debut=datetime.utcnow(), date_fin=datetime.utcnow() + timedelta(hours=1), diagnostic_technicien='d', date_creation=datetime.utcnow())
        # partial intervention for same day
        it2 = Intervention(demande_id=1, technicien_id=tech.id, photos=None, signature_client=None, date_creation=datetime.utcnow())
        db.session.add(it1)
        db.session.add(it2)
        db.session.commit()

        it1_id = it1.id
        it2_id = it2.id

    # login as admin
    client.post('/login', data={'username': 'admin_comp', 'password': 'p'})

    # test individual intervention completude
    r = client.get(f'/api/intervention/{it1_id}/completude')
    assert r.status_code == 200
    d = r.get_json()
    assert 'score' in d
    assert d['score'] == 100

    # test average endpoint
    date_str = datetime.utcnow().strftime('%Y-%m-%d')
    r2 = client.get(f'/api/interventions/completude?date={date_str}')
    assert r2.status_code == 200
    j = r2.get_json()
    assert j['date'] == date_str
    assert j['count'] >= 2
    assert 0.0 <= j['average_score'] <= 100.0
