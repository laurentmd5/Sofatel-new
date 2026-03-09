"""
Tests smoke pour valider les endpoints auth et import Excel après refactorisation.
Exécution : python -m pytest tests/test_smoke.py -v
"""

import pytest
from app import app, db
from models import User
from werkzeug.security import generate_password_hash
import io


@pytest.fixture
def client():
    """Crée un client Flask pour tester."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF in tests to simplify form submissions
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_user(client):
    """Crée un utilisateur test."""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=generate_password_hash('password123'),
            role='chef_pur',
            nom='Test',
            prenom='User',
            telephone='1234567890'
        )
        db.session.add(user)
        db.session.commit()
        return user


def test_login_page_loads(client):
    """Test que la page de login charge."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data or b'login' in response.data or b'Connexion' in response.data


def test_login_with_valid_credentials(client, test_user):
    """Test la connexion avec identifiants valides."""
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    # Vérifier qu'on est redirigé vers le dashboard
    assert b'dashboard' in response.data or b'Dashboard' in response.data or response.request.path == '/dashboard'


def test_login_with_invalid_credentials(client, test_user):
    """Test la connexion avec identifiants invalides."""
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    # Vérifier le message d'erreur
    assert b'incorrect' in response.data or b'Erreur' in response.data


def test_check_session_unauthenticated(client):
    """Test que check_session retourne False pour utilisateur non auth."""
    response = client.get('/api/check-session')
    assert response.status_code == 200
    data = response.get_json()
    assert data['authenticated'] == False


def test_index_redirects_to_login(client):
    """Test que / redirige vers login si non authentifié."""
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302
    assert 'login' in response.location


def test_logout(client, test_user):
    """Test la déconnexion."""
    # Simuler une connexion d'abord (login)
    with client.session_transaction() as sess:
        # Ajouter manuellement l'utilisateur à la session pour ce test
        pass
    response = client.get('/logout', follow_redirects=False)
    # Devrait être autorisé mais redirigé vers login
    assert response.status_code in [302, 401]  # Redirection ou non auth


def test_import_demandes_smoke(client, test_user):
    """Test smoke basique : vérifier que la page d'import Excel charge."""
    # Se connecter d'abord
    client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    })
    # Accéder à la page d'import
    response = client.get('/import-demandes')
    assert response.status_code in [200, 302]  # 200 si autorisé, 302 si redirection


def test_api_notifications_endpoint_present(client):
    """Vérifier que l'endpoint /api/notifications est exposé (au moins redirige vers login)."""
    response = client.get('/api/notifications', follow_redirects=False)
    # Doit exister et rediriger vers /login si non authentifié
    assert response.status_code in [302, 401]
    if response.status_code == 302:
        assert 'login' in response.location


def test_dispatching_page_loads(client, test_user):
    """Vérifie que /dispatching est accessible pour un utilisateur chef_pur."""
    # S'assurer que l'utilisateur de test est chef_pur
    with app.app_context():
        test_user.role = 'chef_pur'
        from app import db as _db
        _db.session.add(test_user)
        _db.session.commit()

    # Se connecter
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200

    # Accéder à la page de dispatching
    response2 = client.get('/dispatching')
    assert response2.status_code == 200


def test_admin_pages_accessible_for_chef_pur(client, test_user):
    """Vérifie que les pages d'administration sont accessibles pour un utilisateur chef_pur (évite les boucles de redirection)."""
    # S'assurer que l'utilisateur de test est chef_pur
    with app.app_context():
        test_user.role = 'chef_pur'
        from app import db as _db
        _db.session.add(test_user)
        _db.session.commit()

    # Se connecter
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200

    # Accéder aux pages d'administration — on attend 200 (page rendue) ou 302 si la logique interne redirige (mais pas en boucle)
    for path in ['/create-user', '/manage-users', '/connection-history']:
        resp = client.get(path, follow_redirects=False)
        assert resp.status_code in [200, 302]
        # If redirected, ensure it's not redirecting back to the same path (prevent loop)
        if resp.status_code == 302:
            assert not resp.location.endswith(path)

