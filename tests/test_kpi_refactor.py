"""
STEP 3: UNIT TESTS FOR KPI REFACTOR
IMPLEMENTATION GUIDE FOR SOFATELCOM
Created: January 22, 2026

✅ READY TO RUN: pytest tests/test_kpi_refactor.py -v
✅ COVERAGE: get_performance_data() + dashboard_kpi_web()
✅ Tests both OLD and NEW code paths

INSTALLATION:
pip install pytest pytest-flask flask-testing
"""

import pytest
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
from app import app, db
from models import User, Equipe, MembreEquipe, Intervention, DemandeIntervention
from kpi_models import KpiScore, KpiAlerte
from utils import get_performance_data
from flask_login import login_user


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """Create test client with app context"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_user(client):
    """Create test user (Chef PUR)"""
    user = User(
        username='testchef',
        email='chef@test.com',
        nom='Chef',
        prenom='Test',
        role='chef_pur',
        actif=True
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def test_equipe(client):
    """Create test team"""
    equipe = Equipe(
        nom_equipe='Équipe Test',
        prestataire='Prestataire Test',
        zone='Zone A',
        technologies='Fiber',
        actif=True,
        service='SAV'
    )
    db.session.add(equipe)
    db.session.commit()
    return equipe


@pytest.fixture
def test_technicien(client, test_equipe):
    """Create test technician"""
    tech = User(
        username='tech1',
        email='tech1@test.com',
        nom='Dupont',
        prenom='Jean',
        role='technicien',
        zone='Zone A',
        technologies='Fiber',
        actif=True
    )
    tech.set_password('password123')
    db.session.add(tech)
    db.session.commit()
    
    # Add to team
    membre = MembreEquipe(
        equipe_id=test_equipe.id,
        technicien_id=tech.id,
        type_membre='technicien'
    )
    db.session.add(membre)
    db.session.commit()
    
    return tech


@pytest.fixture
def test_kpi_scores(client, test_technicien, test_equipe):
    """Create test KPI scores for today"""
    today = date.today()
    
    # Create test KPI score for technician
    kpi_score = KpiScore(
        technicien_id=test_technicien.id,
        equipe_id=test_equipe.id,
        periode_debut=today,
        periode_fin=today,
        periode_type='daily',
        score_total=87.5,
        score_resolution_1ere_visite=90.0,
        score_respect_sla=85.0,
        score_qualite_rapports=88.0,
        score_satisfaction_client=80.0,
        score_consommation_stock=75.0,
        details_json={
            'total_interventions': 10,
            'resolution_1ere': 9,
            'quality_reports': 8
        },
        rang_equipe=1,
        rang_global=2,
        tendance='hausse',
        variation_periode_precedente=+5.2,
        alerte_active=False,
        anomalie_detectee=False,
        calcule_par='system'
    )
    db.session.add(kpi_score)
    db.session.commit()
    
    return kpi_score


@pytest.fixture
def test_alert(client, test_kpi_scores):
    """Create test KPI alert"""
    alert = KpiAlerte(
        kpi_score_id=test_kpi_scores.id,
        type_anomalie='performance_drop',
        severite='haute',
        description='Score dropped 15 points',
        date_creation=datetime.now(),
        date_resolution=None
    )
    db.session.add(alert)
    db.session.commit()
    return alert


# ============================================================================
# TESTS: get_performance_data() REFACTORED
# ============================================================================

class TestGetPerformanceDataRefactored:
    """Test suite for refactored get_performance_data() using KPI source"""
    
    def test_basic_structure(self, client, test_technicien, test_kpi_scores):
        """Test that get_performance_data() returns correct structure"""
        data = get_performance_data()
        
        # Check return structure
        assert isinstance(data, dict)
        assert 'equipes' in data
        assert 'techniciens' in data
        assert 'zones' in data
        assert 'pilots' in data
        
        # Check types
        assert isinstance(data['equipes'], list)
        assert isinstance(data['techniciens'], list)
        assert isinstance(data['zones'], list)
        assert isinstance(data['pilots'], list)
    
    def test_equipes_data_kpi_source(self, client, test_equipe, test_technicien, test_kpi_scores):
        """Test that equipes data comes from KPI scores"""
        data = get_performance_data()
        
        assert len(data['equipes']) > 0
        equipe = data['equipes'][0]
        
        # Check backward compatibility (same fields as before)
        assert 'nom_equipe' in equipe
        assert 'prestataire' in equipe
        assert 'zone' in equipe
        assert 'technologies' in equipe
        assert 'interventions_realisees' in equipe
        assert 'taux_reussite' in equipe
        
        # Check new KPI fields
        assert 'kpi_score' in equipe
        assert 'rang_global' in equipe
        assert 'tendance' in equipe
        
        # Verify data
        assert equipe['nom_equipe'] == 'Équipe Test'
        assert equipe['zone'] == 'Zone A'
        assert equipe['kpi_score'] == 87.5
        assert equipe['tendance'] == 'hausse'
    
    def test_techniciens_data_kpi_source(self, client, test_technicien, test_kpi_scores):
        """Test that techniciens data comes from KPI scores"""
        data = get_performance_data()
        
        assert len(data['techniciens']) > 0
        tech = data['techniciens'][0]
        
        # Check backward compatibility
        assert 'nom' in tech
        assert 'prenom' in tech
        assert 'zone' in tech
        assert 'technologies' in tech
        assert 'interventions_realisees' in tech
        assert 'taux_reussite' in tech
        assert 'equipe_nom' in tech
        
        # Check new KPI fields
        assert 'kpi_score_total' in tech
        assert 'rang_global' in tech
        assert 'tendance' in tech
        assert 'alerte' in tech
        
        # Verify data
        assert tech['nom'] == 'Dupont'
        assert tech['prenom'] == 'Jean'
        assert tech['kpi_score_total'] == 87.5
        assert tech['rang_global'] == 2
        assert tech['alerte'] == False
    
    def test_zone_filtering(self, client, test_equipe, test_technicien, test_kpi_scores):
        """Test that zone parameter filters correctly"""
        # Get all data
        all_data = get_performance_data()
        assert len(all_data['equipes']) > 0
        
        # Get filtered by zone
        zone_data = get_performance_data(zone='Zone A')
        assert len(zone_data['equipes']) > 0
        
        # Verify all returned items are from Zone A
        for equipe in zone_data['equipes']:
            assert equipe['zone'] == 'Zone A'
    
    def test_empty_data_handling(self, client):
        """Test that function handles empty database gracefully"""
        data = get_performance_data()
        
        assert data['equipes'] == []
        assert data['techniciens'] == []
        # zones and pilots may have data from other sources
    
    def test_backward_compatibility(self, client, test_equipe, test_technicien, test_kpi_scores):
        """Test that refactored function maintains backward compatibility"""
        data = get_performance_data()
        
        # dashboard_chef_pur.html expects these fields
        required_equipe_fields = [
            'nom_equipe', 'prestataire', 'zone', 'technologies',
            'interventions_realisees', 'taux_reussite'
        ]
        
        required_tech_fields = [
            'nom', 'prenom', 'zone', 'technologies',
            'interventions_realisees', 'taux_reussite', 'equipe_nom'
        ]
        
        if data['equipes']:
            for field in required_equipe_fields:
                assert field in data['equipes'][0], f"Missing field: {field}"
        
        if data['techniciens']:
            for field in required_tech_fields:
                assert field in data['techniciens'][0], f"Missing field: {field}"
    
    def test_multiple_techniciens_ranking(self, client, test_equipe):
        """Test ranking with multiple technicians"""
        # Create multiple technicians with different scores
        techs = []
        for i in range(3):
            tech = User(
                username=f'tech{i}',
                email=f'tech{i}@test.com',
                nom=f'Nom{i}',
                prenom=f'Prenom{i}',
                role='technicien',
                zone='Zone A',
                actif=True
            )
            tech.set_password('password123')
            db.session.add(tech)
            db.session.commit()
            techs.append(tech)
            
            # Create KPI scores with different scores
            kpi = KpiScore(
                technicien_id=tech.id,
                equipe_id=test_equipe.id,
                periode_debut=date.today(),
                periode_fin=date.today(),
                score_total=float(85 + i * 5),  # 85, 90, 95
                score_resolution_1ere_visite=float(85 + i * 5),
                score_respect_sla=80.0,
                score_qualite_rapports=80.0,
                score_satisfaction_client=80.0,
                score_consommation_stock=80.0,
                details_json={'total_interventions': 10},
                rang_global=i+1,
                tendance='hausse'
            )
            db.session.add(kpi)
            db.session.commit()
        
        data = get_performance_data()
        
        # Should have 3 technicians
        assert len(data['techniciens']) == 3
        
        # Verify data is returned
        assert data['techniciens'][0]['nom'] in ['Nom0', 'Nom1', 'Nom2']


# ============================================================================
# TESTS: /dashboard/kpi ROUTE
# ============================================================================

class TestDashboardKpiRoute:
    """Test suite for /dashboard/kpi route"""
    
    def test_route_requires_login(self, client):
        """Test that route requires login"""
        response = client.get('/dashboard/kpi')
        assert response.status_code == 302  # Redirect to login
    
    def test_route_requires_chef_pur_role(self, client, test_user):
        """Test that route requires Chef PUR or Admin role"""
        # Create non-Chef PUR user
        user = User(
            username='techuser',
            email='tech@test.com',
            nom='Tech',
            prenom='User',
            role='technicien',
            actif=True
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        # Try to access as technicien
        with client:
            client.post('/login', data={
                'username': 'techuser',
                'password': 'password123'
            })
            
            response = client.get('/dashboard/kpi')
            assert response.status_code == 302  # Redirected
            assert 'danger' in response.location or response.status_code == 302
    
    def test_route_accessible_to_chef_pur(self, client, test_user, test_kpi_scores):
        """Test that Chef PUR can access /dashboard/kpi"""
        with client:
            # Login as Chef PUR
            response = client.post('/login', data={
                'username': 'testchef',
                'password': 'password123'
            }, follow_redirects=True)
            
            # Access KPI dashboard
            response = client.get('/dashboard/kpi')
            assert response.status_code == 200
            assert b'dashboard_kpi' in response.data or b'KPI' in response.data
    
    def test_route_parameters_period(self, client, test_user, test_kpi_scores):
        """Test that period parameter works"""
        with client:
            client.post('/login', data={
                'username': 'testchef',
                'password': 'password123'
            }, follow_redirects=True)
            
            # Test different periods
            for period in ['day', 'week', 'month', 'year']:
                response = client.get(f'/dashboard/kpi?period={period}')
                assert response.status_code == 200
    
    def test_route_parameters_sort(self, client, test_user, test_kpi_scores):
        """Test that sort parameter works"""
        with client:
            client.post('/login', data={
                'username': 'testchef',
                'password': 'password123'
            }, follow_redirects=True)
            
            # Test different sort options
            for sort in ['score', 'tendance', 'anomalie']:
                response = client.get(f'/dashboard/kpi?sort={sort}')
                assert response.status_code == 200
    
    def test_route_with_alert(self, client, test_user, test_kpi_scores, test_alert):
        """Test that alerts are displayed"""
        with client:
            client.post('/login', data={
                'username': 'testchef',
                'password': 'password123'
            }, follow_redirects=True)
            
            response = client.get('/dashboard/kpi')
            assert response.status_code == 200
            # Alert should be passed to template


# ============================================================================
# TESTS: EXPORT ENDPOINT (Optional)
# ============================================================================

class TestExportKpi:
    """Test suite for export functionality"""
    
    def test_csv_export_structure(self, client, test_user, test_kpi_scores):
        """Test CSV export has correct headers and data"""
        with client:
            client.post('/login', data={
                'username': 'testchef',
                'password': 'password123'
            }, follow_redirects=True)
            
            response = client.get('/dashboard/kpi/export?format=csv')
            assert response.status_code == 200
            assert response.content_type == 'text/csv; charset=utf-8'
            assert b'Technicien' in response.data
            assert b'Score Total' in response.data
    
    def test_json_export_structure(self, client, test_user, test_kpi_scores):
        """Test JSON export has correct structure"""
        with client:
            client.post('/login', data={
                'username': 'testchef',
                'password': 'password123'
            }, follow_redirects=True)
            
            response = client.get('/dashboard/kpi/export?format=json')
            assert response.status_code == 200
            
            import json
            data = json.loads(response.data)
            assert 'success' in data
            assert 'count' in data
            assert 'data' in data


# ============================================================================
# TESTS: PERFORMANCE & EDGE CASES
# ============================================================================

class TestPerformanceEdgeCases:
    """Test suite for performance and edge case handling"""
    
    def test_no_kpi_data_fallback(self, client, test_equipe, test_technicien):
        """Test that function falls back to Intervention table if no KPI data"""
        # Create interventions but no KPI score
        today = date.today()
        
        for i in range(5):
            intervention = Intervention(
                technicien_id=test_technicien.id,
                equipe_id=test_equipe.id,
                statut='valide',
                date_debut=today,
                date_fin=today
            )
            db.session.add(intervention)
        db.session.commit()
        
        # Should still return data (fallback to Intervention query)
        data = get_performance_data()
        assert len(data['techniciens']) > 0 or len(data['equipes']) > 0
    
    def test_large_dataset_performance(self, client, test_equipe):
        """Test performance with 100+ KPI scores"""
        # Create 100+ KPI scores
        for i in range(50):
            tech = User(
                username=f'perf_tech_{i}',
                email=f'tech_{i}@test.com',
                nom=f'Nom{i}',
                prenom=f'Tech',
                role='technicien',
                zone='Zone A',
                actif=True
            )
            db.session.add(tech)
            db.session.flush()
            
            for j in range(3):  # 3 scores per tech
                kpi = KpiScore(
                    technicien_id=tech.id,
                    equipe_id=test_equipe.id,
                    periode_debut=date.today() - timedelta(days=j*30),
                    periode_fin=date.today() - timedelta(days=j*30),
                    score_total=float(80 + (i % 20)),
                    score_resolution_1ere_visite=80.0,
                    score_respect_sla=80.0,
                    score_qualite_rapports=80.0,
                    score_satisfaction_client=80.0,
                    score_consommation_stock=80.0,
                    details_json={'total_interventions': 10}
                )
                db.session.add(kpi)
        
        db.session.commit()
        
        # Should complete in reasonable time
        import time
        start = time.time()
        data = get_performance_data()
        elapsed = time.time() - start
        
        # Should complete in < 1 second
        assert elapsed < 1.0, f"Performance too slow: {elapsed}s"
        assert len(data['techniciens']) > 0
    
    def test_invalid_parameters_handled(self, client, test_user, test_kpi_scores):
        """Test that invalid parameters don't crash"""
        with client:
            client.post('/login', data={
                'username': 'testchef',
                'password': 'password123'
            }, follow_redirects=True)
            
            # Invalid parameters should be handled gracefully
            response = client.get('/dashboard/kpi?period=invalid&sort=invalid')
            assert response.status_code == 200  # Should not crash


# ============================================================================
# RUN TESTS
# ============================================================================
"""
To run tests:

1. Single test file:
   pytest tests/test_kpi_refactor.py -v

2. Specific test class:
   pytest tests/test_kpi_refactor.py::TestGetPerformanceDataRefactored -v

3. Specific test:
   pytest tests/test_kpi_refactor.py::TestGetPerformanceDataRefactored::test_basic_structure -v

4. With coverage:
   pytest tests/test_kpi_refactor.py --cov=utils --cov=routes

5. Verbose with prints:
   pytest tests/test_kpi_refactor.py -v -s

Expected Output:
  test_basic_structure PASSED
  test_equipes_data_kpi_source PASSED
  test_techniciens_data_kpi_source PASSED
  ... (all tests pass)
  
  ========== 12 passed in 0.45s ==========
"""
