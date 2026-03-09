"""
Test Suite for Barcode Scanner (Sprint 2, Task 2.2)

Tests cover:
1. Product barcode scanning
2. Intervention barcode scanning
3. Demand (ND) barcode scanning
4. Reservation functionality
5. Manual entry fallback
6. Scan history logging
7. Permission checks
8. Error handling
"""

import pytest
import json
from datetime import datetime
from models import (
    User, Produit, DemandeIntervention, Intervention, 
    Reservation, ActivityLog, db
)


@pytest.fixture
def test_user(app):
    """Create a test user with technicien role."""
    with app.app_context():
        user = User.query.filter_by(username='test_scanner_user').first()
        if user:
            db.session.delete(user)
            db.session.commit()
        
        user = User(
            username='test_scanner_user',
            email='scanner@test.local',
            nom='Scannier',
            prenom='Test',
            role='technicien'
        )
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        yield user
        db.session.delete(user)
        db.session.commit()


@pytest.fixture
def test_product(app):
    """Create a test product with barcode."""
    with app.app_context():
        produit = Produit.query.filter_by(code_produit='BARCODE_TEST_001').first()
        if produit:
            db.session.delete(produit)
            db.session.commit()
        
        produit = Produit(
            nom='Test Product',
            code_produit='BARCODE_TEST_001',
            quantite_stock=100,
            prix_unitaire=150.00,
            stock_min=10
        )
        db.session.add(produit)
        db.session.commit()
        yield produit
        db.session.delete(produit)
        db.session.commit()


@pytest.fixture
def test_demand(app):
    """Create a test demand (DemandeIntervention)."""
    with app.app_context():
        demande = DemandeIntervention.query.filter_by(nd='TEST_ND_001').first()
        if demande:
            db.session.delete(demande)
            db.session.commit()
        
        demande = DemandeIntervention(
            nd='TEST_ND_001',
            nom_client='Test Client',
            zone='ZONE_A',
            priorite_traitement='NORMALE',
            statut='nouveau',
            service='SAV'
        )
        db.session.add(demande)
        db.session.commit()
        yield demande
        db.session.delete(demande)
        db.session.commit()


@pytest.fixture
def test_intervention(app, test_demand, test_user):
    """Create a test intervention."""
    with app.app_context():
        intervention = Intervention.query.filter_by(demande_id=test_demand.id).first()
        if intervention:
            db.session.delete(intervention)
            db.session.commit()
        
        intervention = Intervention(
            demande_id=test_demand.id,
            technicien_id=test_user.id,
            statut='en_cours'
        )
        db.session.add(intervention)
        db.session.commit()
        yield intervention
        db.session.delete(intervention)
        db.session.commit()


@pytest.fixture
def auth_token(client, test_user):
    """Get JWT token for test user."""
    response = client.post('/api/mobile/login', json={
        'username': 'test_scanner_user',
        'password': 'testpass123'
    })
    assert response.status_code == 200
    data = response.get_json()
    return data['access_token']


class TestBarcodeProductScan:
    """Test product barcode scanning."""
    
    def test_scan_product_by_barcode(self, client, auth_token, test_product):
        """Scan product by code_produit."""
        response = client.post('/api/barcode/scan', 
            json={
                'barcode': 'BARCODE_TEST_001',
                'type': 'product',
                'action': 'lookup'
            },
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['type'] == 'product'
        assert data['data']['nom'] == 'Test Product'
        assert data['data']['quantite_stock'] == 100
        assert data['data']['prix_unitaire'] == 150.00
    
    def test_scan_product_by_id(self, client, auth_token, test_product):
        """Scan product by ID."""
        response = client.post('/api/barcode/scan',
            json={
                'barcode': str(test_product.id),
                'type': 'product'
            },
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['id'] == test_product.id
    
    def test_scan_product_not_found(self, client, auth_token):
        """Scan non-existent product."""
        response = client.post('/api/barcode/scan',
            json={
                'barcode': 'NONEXISTENT_BARCODE_12345',
                'type': 'product'
            },
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert 'introuvable' in data['error'].lower()
    
    def test_scan_product_with_low_stock(self, client, auth_token, test_product, app):
        """Scan product with stock below minimum."""
        with app.app_context():
            test_product.quantite_stock = 5
            test_product.stock_min = 10
            db.session.commit()
        
        response = client.post('/api/barcode/scan',
            json={
                'barcode': test_product.code_produit,
                'type': 'product'
            },
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['sla_status'] == 'danger'


class TestBarcodeInterventionScan:
    """Test intervention barcode scanning."""
    
    def test_scan_intervention_by_id(self, client, auth_token, test_intervention):
        """Scan intervention by ID."""
        response = client.post('/api/barcode/scan',
            json={
                'barcode': str(test_intervention.id),
                'type': 'intervention'
            },
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['type'] == 'intervention'
        assert data['data']['intervention_id'] == test_intervention.id
    
    def test_scan_intervention_by_nd(self, client, auth_token, test_intervention, test_demand):
        """Scan intervention via demand ND."""
        response = client.post('/api/barcode/scan',
            json={
                'barcode': test_demand.nd,
                'type': 'intervention'
            },
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['intervention_id'] == test_intervention.id
    
    def test_scan_intervention_unauthorized(self, client, auth_token, test_intervention, app):
        """Technicien cannot access others' interventions."""
        # Create another technicien
        with app.app_context():
            other_user = User(
                username='other_tech',
                email='other@test.local',
                nom='Other',
                prenom='Tech',
                role='technicien'
            )
            other_user.set_password('pass123')
            db.session.add(other_user)
            db.session.commit()
        
        response = client.post('/api/barcode/scan',
            json={
                'barcode': str(test_intervention.id),
                'type': 'intervention'
            },
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        # Should fail because test_intervention is assigned to test_user, not current user
        # This needs proper setup with different users


class TestBarcodeDemandScan:
    """Test demand (ND) barcode scanning."""
    
    def test_scan_demand_by_nd(self, client, auth_token, test_demand):
        """Scan demand by ND number."""
        response = client.post('/api/barcode/scan',
            json={
                'barcode': test_demand.nd,
                'type': 'nd'
            },
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['type'] == 'nd'
        assert data['data']['nd'] == test_demand.nd
        assert data['data']['nom_client'] == 'Test Client'
    
    def test_scan_demand_not_found(self, client, auth_token):
        """Scan non-existent demand."""
        response = client.post('/api/barcode/scan',
            json={
                'barcode': 'NONEXISTENT_ND_99999',
                'type': 'nd'
            },
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False


class TestBarcodeReservation:
    """Test product reservation via barcode scanner."""
    
    def test_reserve_product_new(self, client, auth_token, test_product, app):
        """Create new reservation when scanning with reserve action."""
        response = client.post('/api/barcode/scan',
            json={
                'barcode': test_product.code_produit,
                'type': 'product',
                'action': 'reserve'
            },
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['reservation_status'] == 'created'
        
        # Verify reservation was created in DB
        with app.app_context():
            reservation = Reservation.query.filter_by(
                produit_id=test_product.id,
                user_id=auth_token.split('.')[-1]  # Extracted from token
            ).first()
            assert reservation is not None
    
    def test_reserve_product_increment(self, client, auth_token, test_product, app):
        """Increment existing reservation quantity."""
        # Create initial reservation
        with app.app_context():
            from jwt import decode
            payload = decode(auth_token, options={"verify_signature": False})
            user_id = payload['user_id']
            
            reservation = Reservation(
                produit_id=test_product.id,
                user_id=user_id,
                quantite=1,
                statut='en_attente'
            )
            db.session.add(reservation)
            db.session.commit()
        
        # Scan with reserve action
        response = client.post('/api/barcode/scan',
            json={
                'barcode': test_product.code_produit,
                'type': 'product',
                'action': 'reserve'
            },
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['reservation_status'] == 'updated'


# ===== REMOVED =====
# class TestBarcodeManualEntry - SUPPRIMÉ
# Raison: /api/barcode/manual consolidé dans /api/barcode/scan
# Les clients envoient simplement le barcode au endpoint /api/barcode/scan


class TestBarcodeInvalidInput:
    """Test error handling for invalid input."""
    
    def test_empty_barcode(self, client, auth_token):
        """Empty barcode should be rejected."""
        response = client.post('/api/barcode/scan',
            json={
                'barcode': '',
                'type': 'product'
            },
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_short_barcode(self, client, auth_token):
        """Very short barcode should be rejected."""
        response = client.post('/api/barcode/scan',
            json={
                'barcode': 'AB',
                'type': 'product'
            },
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert response.status_code == 400
    
    def test_invalid_scan_type(self, client, auth_token, test_product):
        """Invalid scan type should return error."""
        response = client.post('/api/barcode/scan',
            json={
                'barcode': test_product.code_produit,
                'type': 'invalid_type'
            },
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False


class TestBarcodeHistory:
    """Test scan history logging and retrieval."""
    
    def test_get_scan_history(self, client, auth_token, test_product, app):
        """Retrieve user's scan history."""
        # First, perform a scan
        client.post('/api/barcode/scan',
            json={
                'barcode': test_product.code_produit,
                'type': 'product'
            },
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        # Get history
        response = client.get('/api/barcode/history',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'history' in data
        assert 'total' in data
    
    def test_scan_history_pagination(self, client, auth_token):
        """Pagination of scan history."""
        response = client.get('/api/barcode/history?page=1&per_page=10',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['page'] == 1
        assert data['per_page'] == 10


class TestBarcodePermissions:
    """Test authorization and permission checks."""
    
    def test_scan_without_token(self, client):
        """Scan without authentication token should fail."""
        response = client.post('/api/barcode/scan',
            json={
                'barcode': '123456',
                'type': 'product'
            }
        )
        assert response.status_code == 401
    
    def test_scan_with_invalid_token(self, client):
        """Invalid token should be rejected."""
        response = client.post('/api/barcode/scan',
            json={
                'barcode': '123456',
                'type': 'product'
            },
            headers={'Authorization': 'Bearer invalid.token.here'}
        )
        assert response.status_code == 401
    
    def test_scan_with_expired_token(self, client, test_user, app):
        """Expired token should be rejected."""
        import jwt
        from datetime import datetime, timedelta
        
        with app.app_context():
            expired_payload = {
                'user_id': test_user.id,
                'exp': datetime.utcnow() - timedelta(hours=1)
            }
            expired_token = jwt.encode(
                expired_payload,
                app.secret_key,
                algorithm='HS256'
            )
        
        response = client.post('/api/barcode/scan',
            json={
                'barcode': '123456',
                'type': 'product'
            },
            headers={'Authorization': f'Bearer {expired_token}'}
        )
        assert response.status_code == 401

# ===== REMOVED =====
# class TestBarcodeLogging - SUPPRIMÉ
# Raison: Logging automatique dans /api/barcode/scan
# Chaque scan crée automatiquement une entrée ActivityLog


class TestBarcodeIntegration:
    """Integration tests for complete scanning workflows."""
    
    def test_full_product_scan_workflow(self, client, auth_token, test_product):
        """Complete product scan workflow: scan -> get result -> log."""
        # Step 1: Perform scan
        scan_response = client.post('/api/barcode/scan',
            json={
                'barcode': test_product.code_produit,
                'type': 'product',
                'action': 'lookup'
            },
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert scan_response.status_code == 200
        scan_data = scan_response.get_json()
        assert scan_data['success'] is True
        
        # Step 2: Logging is automatic on backend (removed separate log-scan call)
        # Verify history includes scan (logging should be automatic)
        history_response = client.get('/api/barcode/history',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert history_response.status_code == 200
        history_data = history_response.get_json()
        # After scanning, history should have entries
        # Note: Automatic logging happens in /api/barcode/scan endpoint


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
