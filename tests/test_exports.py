"""
📊 COMPREHENSIVE EXPORT FUNCTIONALITY TESTS
Tests for CSV/PDF export endpoints for interventions, stock, and SLA violations

Test Coverage:
- Intervention export (CSV/PDF) with filtering
- Stock movement export (CSV/PDF) with filtering
- SLA violations export (CSV/PDF) with severity filtering
- Error handling and validation
- Data integrity and completeness
"""

import pytest
import json
import csv
from io import BytesIO, StringIO
from datetime import datetime, timedelta
from flask import current_app
from models import db, Intervention, DemandeIntervention, MouvementStock, Produit, Categorie, User, Equipe
from utils_export import generate_csv, PDFReport, format_datetime, format_status


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def auth_headers(client, app):
    """Get authentication headers"""
    with app.app_context():
        # Create test user
        user = User.query.filter_by(email='testuser@test.com').first()
        if not user:
            user = User(
                email='testuser@test.com',
                nom='Test',
                prenom='User',
                role='admin'
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
        
        # Login
        response = client.post('/login', data={
            'email': 'testuser@test.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        return user


@pytest.fixture
def sample_intervention(app, auth_headers):
    """Create sample intervention for testing"""
    with app.app_context():
        # Create demande
        demande = DemandeIntervention(
            nd='DEM-001',
            nom_client='Test Client',
            telephone='0123456789',
            adresse='123 Rue Test',
            service='SAV',
            technologie='Fibre',
            priorite_traitement='Normal',
            description='Test intervention'
        )
        db.session.add(demande)
        db.session.flush()
        
        # Create user (technicien)
        technicien = User.query.filter_by(role='technicien').first()
        if not technicien:
            technicien = User(
                email='tech@test.com',
                nom='Tech',
                prenom='User',
                role='technicien'
            )
            technicien.set_password('password123')
            db.session.add(technicien)
            db.session.flush()
        
        # Create intervention
        intervention = Intervention(
            demande_id=demande.id,
            technicien_id=technicien.id,
            statut='en_cours',
            date_creation=datetime.utcnow()
        )
        db.session.add(intervention)
        db.session.commit()
        
        return intervention


@pytest.fixture
def sample_stock_movement(app, auth_headers):
    """Create sample stock movement for testing"""
    with app.app_context():
        # Create category
        categorie = Categorie.query.first()
        if not categorie:
            categorie = Categorie(nom='Test Category')
            db.session.add(categorie)
            db.session.flush()
        
        # Create product
        produit = Produit(
            designation='Test Product',
            categorie_id=categorie.id,
            quantite=100,
            prix_unitaire=50.0
        )
        db.session.add(produit)
        db.session.flush()
        
        # Create movement
        mouvement = MouvementStock(
            produit_id=produit.id,
            type_mouvement='entree',
            quantite=10,
            prix_unitaire=50.0,
            utilisateur_id=auth_headers.id,
            date_mouvement=datetime.utcnow(),
            commentaire='Test entry'
        )
        db.session.add(mouvement)
        db.session.commit()
        
        return mouvement


class TestInterventionExport:
    """Test intervention export endpoints"""
    
    def test_export_interventions_csv(self, client, auth_headers, sample_intervention):
        """Test CSV export of interventions"""
        response = client.get('/interventions/api/export/interventions?format=csv')
        
        assert response.status_code == 200
        assert response.content_type == 'text/csv; charset=utf-8'
        assert 'Content-Disposition' in response.headers
        
        # Parse CSV content
        csv_content = response.get_data(as_text=True)
        csv_reader = csv.DictReader(StringIO(csv_content))
        rows = list(csv_reader)
        
        assert len(rows) > 0
        assert 'Client' in csv_reader.fieldnames
        assert 'Statut' in csv_reader.fieldnames
    
    def test_export_interventions_pdf(self, client, auth_headers, sample_intervention):
        """Test PDF export of interventions"""
        response = client.get('/interventions/api/export/interventions?format=pdf')
        
        assert response.status_code == 200
        assert response.content_type == 'application/pdf'
        assert 'Content-Disposition' in response.headers
        assert response.get_data().startswith(b'%PDF')
    
    def test_export_interventions_with_date_filter(self, client, auth_headers, sample_intervention):
        """Test intervention export with date filtering"""
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        response = client.get(
            f'/interventions/api/export/interventions?format=csv&date_debut={today}&date_fin={tomorrow}'
        )
        
        assert response.status_code == 200
        csv_content = response.get_data(as_text=True)
        assert 'Client' in csv_content
    
    def test_export_interventions_with_status_filter(self, client, auth_headers, sample_intervention):
        """Test intervention export with status filtering"""
        response = client.get(
            '/interventions/api/export/interventions?format=csv&statut=en_cours'
        )
        
        assert response.status_code == 200
        csv_content = response.get_data(as_text=True)
        assert len(csv_content) > 0
    
    def test_export_interventions_invalid_format(self, client, auth_headers):
        """Test export with invalid format"""
        response = client.get('/interventions/api/export/interventions?format=invalid')
        
        assert response.status_code == 400
        data = json.loads(response.get_data(as_text=True))
        assert 'error' in data


class TestStockMovementExport:
    """Test stock movement export endpoints"""
    
    def test_export_mouvements_csv(self, client, auth_headers, sample_stock_movement):
        """Test CSV export of stock movements"""
        response = client.get('/gestion-stock/api/export/mouvements?format=csv')
        
        assert response.status_code == 200
        assert response.content_type == 'text/csv; charset=utf-8'
        
        csv_content = response.get_data(as_text=True)
        csv_reader = csv.DictReader(StringIO(csv_content))
        rows = list(csv_reader)
        
        assert len(rows) > 0
        assert 'Produit' in csv_reader.fieldnames
        assert 'Type' in csv_reader.fieldnames
    
    def test_export_mouvements_pdf(self, client, auth_headers, sample_stock_movement):
        """Test PDF export of stock movements"""
        response = client.get('/gestion-stock/api/export/mouvements?format=pdf')
        
        assert response.status_code == 200
        assert response.content_type == 'application/pdf'
        assert response.get_data().startswith(b'%PDF')
    
    def test_export_mouvements_with_type_filter(self, client, auth_headers, sample_stock_movement):
        """Test stock export with type filtering"""
        response = client.get(
            '/gestion-stock/api/export/mouvements?format=csv&type_mouvement=entree'
        )
        
        assert response.status_code == 200
        csv_content = response.get_data(as_text=True)
        assert 'Produit' in csv_content
    
    def test_export_mouvements_with_date_filter(self, client, auth_headers, sample_stock_movement):
        """Test stock export with date filtering"""
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        response = client.get(
            f'/gestion-stock/api/export/mouvements?format=csv&date_debut={today}&date_fin={tomorrow}'
        )
        
        assert response.status_code == 200
        csv_content = response.get_data(as_text=True)
        assert len(csv_content) > 0
    
    def test_export_mouvements_invalid_format(self, client, auth_headers):
        """Test export with invalid format"""
        response = client.get('/gestion-stock/api/export/mouvements?format=invalid')
        
        assert response.status_code == 400
        data = json.loads(response.get_data(as_text=True))
        assert 'error' in data


class TestSLAViolationExport:
    """Test SLA violation export endpoints"""
    
    def test_export_sla_violations_csv(self, client, auth_headers):
        """Test CSV export of SLA violations"""
        response = client.get('/api/sla/export/violations?format=csv')
        
        assert response.status_code == 200
        assert response.content_type == 'text/csv; charset=utf-8'
        
        csv_content = response.get_data(as_text=True)
        # Should have headers at minimum
        assert 'Intervention' in csv_content or len(csv_content) > 0
    
    def test_export_sla_violations_pdf(self, client, auth_headers):
        """Test PDF export of SLA violations"""
        response = client.get('/api/sla/export/violations?format=pdf')
        
        assert response.status_code == 200
        assert response.content_type == 'application/pdf'
        assert response.get_data().startswith(b'%PDF')
    
    def test_export_sla_violations_with_severity_filter(self, client, auth_headers):
        """Test SLA export with severity filtering"""
        response = client.get(
            '/api/sla/export/violations?format=csv&severity=critical'
        )
        
        assert response.status_code == 200
        csv_content = response.get_data(as_text=True)
        assert len(csv_content) > 0
    
    def test_export_sla_violations_invalid_format(self, client, auth_headers):
        """Test export with invalid format"""
        response = client.get('/api/sla/export/violations?format=invalid')
        
        assert response.status_code == 400
        data = json.loads(response.get_data(as_text=True))
        assert 'error' in data


class TestExportUtilities:
    """Test export utility functions"""
    
    def test_generate_csv(self):
        """Test CSV generation from data"""
        data = [
            {'id': 1, 'name': 'Item 1', 'value': 100},
            {'id': 2, 'name': 'Item 2', 'value': 200}
        ]
        headers = ['id', 'name', 'value']
        
        csv_bytes, filename = generate_csv(data, headers)
        
        # Verify CSV content
        csv_text = csv_bytes.decode('utf-8-sig')
        assert 'id,name,value' in csv_text
        assert 'Item 1' in csv_text
        assert 'Item 2' in csv_text
        assert filename.endswith('.csv')
    
    def test_pdf_report_generation(self):
        """Test PDF report generation"""
        report = PDFReport('Test Report', 'test.pdf')
        report.add_title('Test Title')
        report.add_heading('Test Heading')
        report.add_paragraph('Test paragraph content')
        
        table_data = [
            ['Col1', 'Col2', 'Col3'],
            ['Data1', 'Data2', 'Data3']
        ]
        report.add_table(table_data, headers=['Col1', 'Col2', 'Col3'])
        
        pdf_bytes = report.build()
        
        # Verify PDF structure
        assert pdf_bytes.startswith(b'%PDF')
        assert len(pdf_bytes) > 1000
    
    def test_format_datetime(self):
        """Test datetime formatting"""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        formatted = format_datetime(dt)
        
        assert '15/01/2024' in formatted
        assert '10:30' in formatted
    
    def test_format_status(self):
        """Test status formatting"""
        assert format_status('en_cours') == 'En cours'
        assert format_status('valide') == 'Validée'
        assert format_status('termine') == 'Terminée'
        assert format_status('annulee') == 'Annulée'
    
    def test_format_status_unknown(self):
        """Test formatting of unknown status"""
        result = format_status('unknown_status')
        assert result == 'unknown_status'


class TestExportAuthentication:
    """Test authentication for export endpoints"""
    
    def test_export_requires_login_interventions(self, client):
        """Test that intervention export requires login"""
        response = client.get('/interventions/api/export/interventions?format=csv')
        
        # Should redirect to login
        assert response.status_code in [302, 401, 403]
    
    def test_export_requires_login_stock(self, client):
        """Test that stock export requires login"""
        response = client.get('/gestion-stock/api/export/mouvements?format=csv')
        
        # Should redirect to login
        assert response.status_code in [302, 401, 403]
    
    def test_export_requires_login_sla(self, client):
        """Test that SLA export requires login"""
        response = client.get('/api/sla/export/violations?format=csv')
        
        # Should redirect to login
        assert response.status_code in [302, 401, 403]


class TestExportDataIntegrity:
    """Test data integrity in exports"""
    
    def test_csv_encoding(self, client, auth_headers, sample_intervention):
        """Test CSV uses proper UTF-8 encoding"""
        response = client.get('/interventions/api/export/interventions?format=csv')
        
        assert response.status_code == 200
        # Check for UTF-8 BOM
        data = response.get_data()
        assert data.startswith(b'\xef\xbb\xbf')  # UTF-8 BOM for Excel compatibility
    
    def test_pdf_contains_data(self, client, auth_headers, sample_intervention):
        """Test PDF contains exported data"""
        response = client.get('/interventions/api/export/interventions?format=pdf')
        
        assert response.status_code == 200
        pdf_data = response.get_data()
        assert len(pdf_data) > 5000  # PDF should have reasonable size
    
    def test_csv_special_characters(self, app, auth_headers):
        """Test CSV handles special characters correctly"""
        with app.app_context():
            data = [
                {'name': 'John "Doe"', 'city': 'New York, USA', 'note': 'Has, special; characters'},
                {'name': 'Jane O\'Brien', 'city': 'Los Angeles', 'note': 'Normal'}
            ]
            headers = ['name', 'city', 'note']
            
            csv_bytes, _ = generate_csv(data, headers)
            csv_text = csv_bytes.decode('utf-8-sig')
            
            # Verify proper quoting
            assert 'John "Doe"' in csv_text
            assert 'New York, USA' in csv_text


class TestExportFilenames:
    """Test export filename generation"""
    
    def test_csv_filename_format(self, client, auth_headers):
        """Test CSV filename has correct format"""
        response = client.get('/interventions/api/export/interventions?format=csv')
        
        assert response.status_code == 200
        disposition = response.headers.get('Content-Disposition', '')
        assert '.csv' in disposition
    
    def test_pdf_filename_format(self, client, auth_headers):
        """Test PDF filename has correct format"""
        response = client.get('/interventions/api/export/interventions?format=pdf')
        
        assert response.status_code == 200
        disposition = response.headers.get('Content-Disposition', '')
        assert '.pdf' in disposition


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
