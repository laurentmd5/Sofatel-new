from unittest.mock import patch
from sqlalchemy.exc import OperationalError
from models import DemandeIntervention
from app import app, db
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


def test_dispatching_handles_operational_error(client):
    # create a chef_pur user to allow accessing dispatching
    with app.app_context():
        from werkzeug.security import generate_password_hash
        admin = db.session.execute(db.insert.__self__.bind.table_names) if False else None
        # Create a simple chef_pur user
        from models import User
        admin = User(username='admin', email='a@a', password_hash=generate_password_hash('pass'), role='chef_pur', nom='A', prenom='A', telephone='000')
        db.session.add(admin)
        db.session.commit()

    client.post('/login', data={'username': 'admin', 'password': 'pass'})

    # Simulate OperationalError during paginate/order_by
    with patch.object(DemandeIntervention.query, 'order_by', side_effect=OperationalError('stmt', None, None)):
        resp = client.get('/dispatching')
        # we expect the view to handle the DB error and return a 200 page with a friendly message (avoid 500)
        assert resp.status_code == 200
        # Ensure we don't get an HTML error page (500) - basic check: content-length > 0
        assert len(resp.data) > 0

