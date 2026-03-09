from app import app, db
from models import User, Intervention
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import pytest
import json


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


def test_sse_stream_returns_data_once(client):
    with app.app_context():
        admin = User(username='admin_stream', email='a@a', password_hash=generate_password_hash('p'), role='chef_pur', nom='A', prenom='A', telephone='000')
        tech = User(username='tech_stream', email='t_stream@example.com', password_hash=generate_password_hash('p'), role='technicien', nom='T', prenom='T', telephone='000')
        db.session.add(admin)
        db.session.add(tech)
        db.session.commit()

        # interventions: one recent, one older than 40 days (should be filtered out)
        it1 = Intervention(demande_id=1, technicien_id=tech.id, statut='en_cours', date_creation=datetime.utcnow())
        it2 = Intervention(demande_id=1, technicien_id=tech.id, statut='termine', date_creation=datetime.utcnow() - timedelta(days=40))
        db.session.add(it1)
        db.session.add(it2)
        db.session.commit()

        it1_id = it1.id

        # login
        client.post('/login', data={'username': 'admin_stream', 'password': 'p'})

        # request once=1 so the generator emits only once and finishes     
        r = client.get('/api/stream/interventions?once=1&interval=0')      
        assert r.status_code == 200
        body = r.get_data(as_text=True)
        assert 'data:' in body

        # extract JSON after 'data: '
        part = body.split('data:', 1)[1].strip()
        # remove any trailing separators
        part = part.split('\n\n', 1)[0]
        payload = json.loads(part)

        assert payload['count'] == 1
        assert isinstance(payload['interventions'], list)
        assert payload['interventions'][0]['id'] == it1_id
