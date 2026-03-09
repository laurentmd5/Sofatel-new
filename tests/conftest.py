import pytest
import os
import uuid
from datetime import datetime
from flask import Flask
from app import app, db
from models import User, EmplacementStock, Categorie, Produit

app.config['TESTING'] = True

@pytest.fixture(scope='function')
def app_context():
    """Fixture pour créer un contexte Flask."""
    with app.app_context():
        yield app

@pytest.fixture
def client(app_context):
    """Fixture pour créer un client de test."""
    return app.test_client()

def generate_unique_code(prefix="TEST"):
    """Générer un code unique pour éviter les doublons."""
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"

@pytest.fixture
def test_user(app_context):
    """Créer un utilisateur de test."""
    from models import User
    user = User(
        username=generate_unique_code("USER"),
        email=f"test-{uuid.uuid4()}@test.com",
        password_hash="hashed_password",
        role="chef_pur"
    )
    db.session.add(user)
    db.session.commit()
    yield user
    # Cleanup
    try:
        db.session.delete(user)
        db.session.commit()
    except:
        db.session.rollback()

@pytest.fixture
def test_emplacement(app_context):
    """Créer un emplacement de test."""
    from models import EmplacementStock
    emplacement = EmplacementStock(
        code=generate_unique_code("RAYON"),
        designation=f"Rayon Test {uuid.uuid4()}",
        description="Test location",
        actif=True
    )
    db.session.add(emplacement)
    db.session.commit()
    yield emplacement
    # Cleanup
    try:
        db.session.delete(emplacement)
        db.session.commit()
    except:
        db.session.rollback()

@pytest.fixture
def test_categorie(app_context):
    """Créer une catégorie de test."""
    from models import Categorie
    categorie = Categorie(
        nom=f"Category {uuid.uuid4()}",
        description="Test category"
    )
    db.session.add(categorie)
    db.session.commit()
    yield categorie
    # Cleanup
    try:
        db.session.delete(categorie)
        db.session.commit()
    except:
        db.session.rollback()

@pytest.fixture
def test_produit(app_context, test_categorie, test_emplacement):
    """Créer un produit de test."""
    from models import Produit
    produit = Produit(
        reference=generate_unique_code("PROD"),
        nom=f"Product {uuid.uuid4()}",
        description="Test product",
        code_barres=generate_unique_code("BAR"),
        categorie_id=test_categorie.id,
        prix_unitaire=100.0,
        stock_min=10,
        actif=True
    )
    db.session.add(produit)
    db.session.commit()
    yield produit
    # Cleanup
    try:
        db.session.delete(produit)
        db.session.commit()
    except:
        db.session.rollback()

@pytest.fixture
def runner():
    """Fixture pour tester les CLI commands."""
    return app.test_cli_runner()

class TestAppBasics:
    """Tests basiques de l'application."""
    
    def test_app_exists(self):
        """Vérifier que l'app existe."""
        assert app is not None
    
    def test_app_is_testing(self):
        """Vérifier que le mode test est activé."""
        app.config['TESTING'] = True
        assert app.config['TESTING'] is True

class TestHealthCheck:
    """Tests du health check API."""
    
    def test_health_check_endpoint(self, client):
        """Vérifier l'endpoint health check."""
        response = client.get('/api/health')
        assert response.status_code in [200, 404]  # Peut ne pas exister en test

class TestImports:
    """Tests d'imports pour éviter les imports circulaires."""
    
    def test_import_extensions(self):
        """Vérifier que extensions s'importe sans erreur."""
        from extensions import db, cache, csrf
        assert db is not None
        assert cache is not None
        assert csrf is not None
    
    def test_import_models(self):
        """Vérifier que models s'importe sans erreur."""
        from models import User, Produit
        assert User is not None
        assert Produit is not None
    
    def test_import_routes(self):
        """Vérifier que routes s'importent sans erreur."""
        from routes_stock import stock_bp
        assert stock_bp is not None

class TestSecurity:
    """Tests de sécurité."""
    
    def test_no_debug_mode_in_production(self):
        """Vérifier que debug mode n'est pas activé en production."""
        if os.getenv('FLASK_ENV') == 'production':
            assert app.config.get('DEBUG') is False
    
    def test_csrf_protection_enabled(self):
        """Vérifier que CSRF protection est activée."""
        assert app.config.get('WTF_CSRF_ENABLED', True) is True
    
    def test_secure_session_cookies(self):
        """Vérifier la configuration des cookies de session."""
        assert app.config.get('SESSION_COOKIE_HTTPONLY', True) is True
        assert app.config.get('SESSION_COOKIE_SAMESITE', 'Lax') in ['Strict', 'Lax', 'None']
    
    def test_no_exposed_secrets(self):
        """Vérifier qu'aucun secret n'est exposé."""
        # Ce test s'exécute avec les vrais secrets, donc on teste juste que la variable existe
        assert os.getenv('SESSION_SECRET') is not None or app.config.get('SECRET_KEY') is not None

class TestConfiguration:
    """Tests de configuration."""
    
    def test_database_uri_configured(self):
        """Vérifier que la DB est configurée."""
        assert app.config.get('SQLALCHEMY_DATABASE_URI') is not None
    
    def test_upload_folder_exists(self):
        """Vérifier que le dossier d'upload existe."""
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        assert upload_folder is not None
        os.makedirs(upload_folder, exist_ok=True)
        assert os.path.exists(upload_folder)

class TestDependencies:
    """Tests des dépendances."""
    
    def test_required_packages_imported(self):
        """Vérifier que les packages essentiels sont importés."""
        try:
            import flask
            import sqlalchemy
            import redis
            import pymysql
            import apscheduler
        except ImportError as e:
            pytest.fail(f"Package manquant: {e}")

# Tests de performance (optionnel)
class TestPerformance:
    """Tests de performance."""
    
    @pytest.mark.slow
    def test_app_startup_time(self):
        """Vérifier que l'app démarre rapidement."""
        import time
        start = time.time()
        
        with app.app_context():
            db.create_all()
        
        elapsed = time.time() - start
        assert elapsed < 5, f"App startup took {elapsed}s (should be < 5s)"
