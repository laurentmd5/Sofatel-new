import pytest
from app import app, db
from models import User, Produit, MouvementStock
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


def login(client, username, password='pwd'):
    rv = client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)
    # Ensure session is authenticated in test environment by setting flask-login session keys
    from models import User
    with client.session_transaction() as sess:
        user = User.query.filter_by(username=username).first()
        if user:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return rv


def test_get_by_barcode(client):
    with app.app_context():
        user = User(username='user1', email='u1@example.com', password_hash=generate_password_hash('pwd'), role='gestionnaire_stock', nom='U', prenom='One', telephone='000')
        db.session.add(user)
        db.session.commit()

        p = Produit(reference='PR1', nom='Produit 1', code_barres='CB123')
        db.session.add(p)
        db.session.commit()
        pid = p.id

    # login
    resp = login(client, 'user1')
    assert resp.status_code in (200, 302)
    sess = client.get('/api/check-session').get_json()
    if not sess.get('authenticated'):
        print('LOGIN RESPONSE:', resp.status_code, resp.data[:500])
        print('CHECK-SESSION RESPONSE:', sess)
    assert sess.get('authenticated') is True

    r = client.get(f'/gestion-stock/api/produits/by-barcode/CB123')
    assert r.status_code == 200
    data = r.get_json()
    assert data.get('success') is True
    assert data['produit']['id'] == pid


def test_ajuster_stock_endpoint(client):
    with app.app_context():
        user = User(username='user2', email='u2@example.com', password_hash=generate_password_hash('pwd'), role='gestionnaire_stock', nom='U', prenom='Two', telephone='000')
        db.session.add(user)
        db.session.commit()

        p = Produit(reference='PR2', nom='Produit 2')
        db.session.add(p)
        db.session.flush()
        # initial entry 10
        m = MouvementStock(type_mouvement='entree', produit_id=p.id, quantite=10, utilisateur_id=user.id, date_mouvement=datetime.utcnow())
        db.session.add(m)
        db.session.commit()
        pid = p.id

    resp = login(client, 'user2')
    assert resp.status_code in (200, 302)
    sess = client.get('/api/check-session').get_json()
    assert sess.get('authenticated') is True

    r = client.post(f'/gestion-stock/produit/ajuster/{pid}', json={'stock_reel': 8, 'motif': 'Audit'})
    assert r.status_code == 200
    data = r.get_json()
    assert data['success'] is True
    assert abs(data['difference'] + 2) < 1e-6  # difference = 8 - 10 = -2

    with app.app_context():
        # newest mouvement should be inventory adjustment recorded as sortie of 2
        m_new = MouvementStock.query.filter_by(produit_id=pid).order_by(MouvementStock.id.desc()).first()
        assert m_new is not None
        assert m_new.type_mouvement == 'sortie'
        assert abs(m_new.quantite - 2.0) < 1e-6
        assert abs(m_new.quantite_reelle - 8.0) < 1e-6
        assert abs(m_new.ecart + 2.0) < 1e-6
        # computed stock now should be 8
        p = db.session.get(Produit, pid)
        assert abs(p.quantite - 8.0) < 1e-6


def test_api_inventaire_bulk(client):
    with app.app_context():
        user = User(username='user3', email='u3@example.com', password_hash=generate_password_hash('pwd'), role='gestionnaire_stock', nom='U', prenom='Three', telephone='000')
        db.session.add(user)
        db.session.commit()

        p1 = Produit(reference='PR3', nom='Produit 3')
        p2 = Produit(reference='PR4', nom='Produit 4')
        db.session.add_all([p1, p2])
        db.session.flush()
        # initial stocks
        m1 = MouvementStock(type_mouvement='entree', produit_id=p1.id, quantite=5, utilisateur_id=user.id, date_mouvement=datetime.utcnow())
        m2 = MouvementStock(type_mouvement='entree', produit_id=p2.id, quantite=0, utilisateur_id=user.id, date_mouvement=datetime.utcnow())
        db.session.add_all([m1, m2])
        db.session.commit()
        pid1 = p1.id
        pid2 = p2.id

    resp = login(client, 'user3')
    assert resp.status_code in (200, 302)
    sess = client.get('/api/check-session').get_json()
    assert sess.get('authenticated') is True

    payload = {
        'items': [
            {'produit_id': pid1, 'stock_reel': 7},
            {'produit_id': pid2, 'stock_reel': 3}
        ],
        'commentaire': 'Audit mois'
    }
    r = client.post('/gestion-stock/api/inventaire', json=payload)
    assert r.status_code == 200
    data = r.get_json()
    assert data.get('success') is True
    results = data.get('results')
    assert any(res['produit_id'] == pid1 and res['success'] for res in results)
    assert any(res['produit_id'] == pid2 and res['success'] for res in results)

    with app.app_context():
        p1 = db.session.get(Produit, pid1)
        p2 = db.session.get(Produit, pid2)
        assert abs(p1.quantite - 7.0) < 1e-6
        assert abs(p2.quantite - 3.0) < 1e-6