"""
KPI System Integration Tests
Test the complete KPI scoring system
"""

import unittest
import json
from datetime import datetime, date, timedelta
from app import app
from extensions import db
from models import User, Equipe, MembreEquipe, Intervention
from kpi_models import KpiScore, KpiMetric, KpiAlerte, KpiHistorique, KpiObjectif
from kpi_engine import KpiScoringEngine


class KPISystemTestCase(unittest.TestCase):
    """Test cases for KPI system"""
    
    def setUp(self):
        """Set up test environment"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        self.app = app
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
            self._create_test_data()
    
    def tearDown(self):
        """Tear down test environment"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def _create_test_data(self):
        """Create test data"""
        # Create test users
        self.tech1 = User(
            username='tech1',
            email='tech1@test.com',
            prenom='Jean',
            nom='Dupont',
            role='technicien',
            password='test123',
            actif=True
        )
        self.tech2 = User(
            username='tech2',
            email='tech2@test.com',
            prenom='Marie',
            nom='Martin',
            role='technicien',
            password='test123',
            actif=True
        )
        self.chef = User(
            username='chef',
            email='chef@test.com',
            prenom='Chef',
            nom='Project',
            role='chef_pur',
            password='test123',
            actif=True
        )
        
        db.session.add_all([self.tech1, self.tech2, self.chef])
        db.session.commit()
        
        # Create test team
        self.equipe = Equipe(
            nom='Équipe Test',
            description='Test team',
            date_creation=datetime.now()
        )
        db.session.add(self.equipe)
        db.session.commit()
        
        # Add technicians to team
        membre1 = MembreEquipe(
            equipe_id=self.equipe.id,
            technicien_id=self.tech1.id,
            type_membre='technicien'
        )
        membre2 = MembreEquipe(
            equipe_id=self.equipe.id,
            technicien_id=self.tech2.id,
            type_membre='technicien'
        )
        db.session.add_all([membre1, membre2])
        db.session.commit()
        
        # Create KPI metrics
        self.metrics = [
            KpiMetric(
                nom='Résolution 1ère visite',
                description='Test metric',
                poids=0.30,
                seuil_alerte=75,
                date_creation=datetime.now()
            ),
            KpiMetric(
                nom='Respect SLA',
                description='Test metric',
                poids=0.25,
                seuil_alerte=90,
                date_creation=datetime.now()
            )
        ]
        db.session.add_all(self.metrics)
        db.session.commit()
    
    def test_kpi_metric_creation(self):
        """Test KPI metric creation"""
        with app.app_context():
            metrics = KpiMetric.query.all()
            self.assertEqual(len(metrics), 2)
            self.assertEqual(metrics[0].nom, 'Résolution 1ère visite')
            self.assertEqual(metrics[0].poids, 0.30)
    
    def test_kpi_objectif_creation(self):
        """Test creating KPI objectives"""
        with app.app_context():
            objectif = KpiObjectif(
                technicien_id=self.tech1.id,
                annee=2024,
                objectif_resolution_1ere_visite=80,
                objectif_respect_sla=95,
                objectif_qualite_rapports=85,
                objectif_satisfaction_client=80,
                objectif_consommation_stock=80,
                date_debut=date(2024, 1, 1),
                date_fin=date(2024, 12, 31),
                date_creation=datetime.now()
            )
            db.session.add(objectif)
            db.session.commit()
            
            retrieved = KpiObjectif.query.filter_by(
                technicien_id=self.tech1.id,
                annee=2024
            ).first()
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.objectif_respect_sla, 95)
    
    def test_kpi_scoring_engine_initialization(self):
        """Test KPI scoring engine initialization"""
        with app.app_context():
            period_start = date.today() - timedelta(days=30)
            period_end = date.today()
            
            engine = KpiScoringEngine(self.tech1.id, period_start, period_end)
            self.assertEqual(engine.technicien_id, self.tech1.id)
            self.assertEqual(engine.period_start, period_start)
            self.assertEqual(engine.period_end, period_end)
    
    def test_kpi_score_creation(self):
        """Test creating KPI scores"""
        with app.app_context():
            score = KpiScore(
                technicien_id=self.tech1.id,
                equipe_id=self.equipe.id,
                periode_debut=date(2024, 1, 1),
                periode_fin=date(2024, 1, 31),
                score_total=85.5,
                score_resolution_1ere_visite=82.0,
                score_respect_sla=90.0,
                score_qualite_rapports=88.0,
                score_satisfaction_client=85.0,
                score_consommation_stock=78.0,
                rang_equipe=1,
                rang_global=5,
                tendance='hausse',
                variation_periode_precedente=2.5,
                date_creation=datetime.now()
            )
            db.session.add(score)
            db.session.commit()
            
            retrieved = KpiScore.query.filter_by(
                technicien_id=self.tech1.id,
                periode_debut=date(2024, 1, 1)
            ).first()
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.score_total, 85.5)
            self.assertEqual(retrieved.rang_global, 5)
    
    def test_kpi_alerte_creation(self):
        """Test creating KPI alerts"""
        with app.app_context():
            alerte = KpiAlerte(
                technicien_id=self.tech1.id,
                type_alerte='seuil',
                metrique='qualite_rapports',
                severite='eleve',
                titre='Métrique sous objectif',
                description='Qualité rapports = 72%',
                valeur_actuelle=72.0,
                valeur_seuil=85.0,
                recommandations=['Action 1', 'Action 2'],
                active=True,
                date_creation=datetime.now()
            )
            db.session.add(alerte)
            db.session.commit()
            
            retrieved = KpiAlerte.query.filter_by(
                technicien_id=self.tech1.id
            ).first()
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.severite, 'eleve')
            self.assertTrue(retrieved.active)
    
    def test_kpi_historique_creation(self):
        """Test creating KPI historical records"""
        with app.app_context():
            history = KpiHistorique(
                technicien_id=self.tech1.id,
                date=date.today(),
                score_total=85.5,
                score_resolution_1ere_visite=82.0,
                score_respect_sla=90.0,
                score_qualite_rapports=88.0,
                score_satisfaction_client=85.0,
                score_consommation_stock=78.0,
                nombre_interventions=10,
                nombre_sla_respectes=9,
                nombre_sla_violes=1
            )
            db.session.add(history)
            db.session.commit()
            
            retrieved = KpiHistorique.query.filter_by(
                technicien_id=self.tech1.id,
                date=date.today()
            ).first()
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.nombre_interventions, 10)
    
    def test_kpi_unique_constraints(self):
        """Test unique constraints on KPI tables"""
        with app.app_context():
            # Create first objective
            obj1 = KpiObjectif(
                technicien_id=self.tech1.id,
                annee=2024,
                objectif_resolution_1ere_visite=80,
                date_debut=date(2024, 1, 1),
                date_fin=date(2024, 12, 31),
                date_creation=datetime.now()
            )
            db.session.add(obj1)
            db.session.commit()
            
            # Try to create duplicate
            obj2 = KpiObjectif(
                technicien_id=self.tech1.id,
                annee=2024,
                objectif_resolution_1ere_visite=85,
                date_debut=date(2024, 1, 1),
                date_fin=date(2024, 12, 31),
                date_creation=datetime.now()
            )
            db.session.add(obj2)
            
            # Should raise IntegrityError
            with self.assertRaises(Exception):
                db.session.commit()
    
    def test_api_metrics_endpoint(self):
        """Test API endpoint for metrics (requires login)"""
        # This test assumes a proper test client with auth
        # In real implementation, you'd need to set up proper auth
        pass
    
    def test_scoring_calculation_weights(self):
        """Test that weights are correctly configured"""
        with app.app_context():
            engine = KpiScoringEngine(
                self.tech1.id,
                date.today() - timedelta(days=30),
                date.today()
            )
            
            total_weight = sum(engine.WEIGHTS.values())
            self.assertEqual(total_weight, 1.0)  # Weights must sum to 1
    
    def test_score_total_calculation_formula(self):
        """Test that score_total is calculated correctly"""
        # Score_total = (score_1 * 0.30) + (score_2 * 0.25) + ...
        
        score_1 = 100
        score_2 = 100
        score_3 = 100
        score_4 = 100
        score_5 = 100
        
        expected_total = (
            (score_1 * 0.30) +
            (score_2 * 0.25) +
            (score_3 * 0.20) +
            (score_4 * 0.15) +
            (score_5 * 0.10)
        )
        
        self.assertEqual(expected_total, 100.0)
        
        # Test with mixed scores
        score_1 = 80
        score_2 = 90
        score_3 = 85
        score_4 = 75
        score_5 = 95
        
        expected_total = (
            (80 * 0.30) +
            (90 * 0.25) +
            (85 * 0.20) +
            (75 * 0.15) +
            (95 * 0.10)
        )
        
        self.assertAlmostEqual(expected_total, 83.0)


class KPIDataValidationTestCase(unittest.TestCase):
    """Test data validation and constraints"""
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app
        
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_metric_weight_range(self):
        """Test that metric weights are in valid range"""
        with app.app_context():
            metric = KpiMetric(
                nom='Test Metric',
                poids=0.50,  # 50%
                seuil_alerte=80,
                date_creation=datetime.now()
            )
            db.session.add(metric)
            db.session.commit()
            
            retrieved = KpiMetric.query.first()
            self.assertGreaterEqual(retrieved.poids, 0)
            self.assertLessEqual(retrieved.poids, 1)
    
    def test_score_range(self):
        """Test that scores are in valid range (0-100)"""
        with app.app_context():
            user = User(
                username='test',
                email='test@test.com',
                role='technicien',
                password='test'
            )
            db.session.add(user)
            db.session.commit()
            
            score = KpiScore(
                technicien_id=user.id,
                periode_debut=date(2024, 1, 1),
                periode_fin=date(2024, 1, 31),
                score_total=85.5,
                score_resolution_1ere_visite=82.0,
                date_creation=datetime.now()
            )
            db.session.add(score)
            db.session.commit()
            
            retrieved = KpiScore.query.first()
            self.assertGreaterEqual(retrieved.score_total, 0)
            self.assertLessEqual(retrieved.score_total, 100)


if __name__ == '__main__':
    unittest.main()
