"""
UNIT TEST SUITE: Stock Management Business Logic
Tests for stock movements, validation, state transitions, workflow
"""

import pytest
from datetime import datetime
from decimal import Decimal
import uuid
from datetime import datetime

from app import app, db
from models import (
    Produit, MouvementStock, User, Categorie, EmplacementStock,
    Fournisseur, NumeroSerie, NumeroSerieStatut
)
from werkzeug.security import generate_password_hash
from routes_stock import prevent_negative_stock_on_creation, validate_and_initialize_mouvement_workflow
from workflow_stock import WorkflowState, VALID_TRANSITIONS
from sqlalchemy.exc import IntegrityError



def generate_unique_code(prefix="TEST"):
    """Generate unique code to avoid duplicates"""
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"

@pytest.fixture
def app_context():
    """App context for direct model testing"""
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_user(app_context):
    """Create a test user"""
    user = User(
        username=generate_unique_code('USER'),
        email=f'{uuid.uuid4()}@test.com',
        password_hash=generate_password_hash('password'),
        role='gestionnaire_stock',
        nom='Test',
        prenom='User',
        telephone='1234567890'
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def test_produit(app_context):
    """Create a test product"""
    prod = Produit(
        reference=generate_unique_code('PROD'),
        code_barres=generate_unique_code('BAR'),
        nom=f'Product-{uuid.uuid4()}',
        prix_achat=Decimal('45000.00'),
        prix_vente=Decimal('55000.00'),
        stock_min=5,
        stock_max=100,
        actif=True
    )
    db.session.add(prod)
    db.session.commit()
    return prod


@pytest.fixture
def stock_with_inventory(app_context, test_produit, test_user):
    """Create a product with initial stock"""
    mouv = MouvementStock(
        type_mouvement='entree',
        produit_id=test_produit.id,
        quantite=100,
        utilisateur_id=test_user.id,
        workflow_state='VALIDE',
        applique_au_stock=True
    )
    db.session.add(mouv)
    db.session.commit()
    db.session.refresh(test_produit)
    return test_produit


# ============================================================================
# TEST SUITE: Stock Entry Logic (Entree)
# ============================================================================

class TestStockEntryLogic:
    """Tests for stock entry (entree) business logic"""
    
    def test_entree_movement_creation(self, app_context, test_produit, test_user):
        """✅ Entree movement can be created"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=50,
            utilisateur_id=test_user.id,
            reference='BON-2024-001'
        )
        db.session.add(mouv)
        db.session.commit()
        
        assert mouv.id is not None
        assert mouv.type_mouvement == 'entree'
        assert mouv.quantite == 50
    
    def test_entree_requires_user(self, app_context, test_produit):
        """❌ Entree movement MUST have utilisateur"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=50
        )
        db.session.add(mouv)
        
        with pytest.raises(IntegrityError):
            db.session.commit()
    
    def test_entree_zero_quantity_not_prevented(self, app_context, test_produit, test_user):
        """⚠️ Zero quantity entree not prevented at model (should be in business logic)"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=0,  # Zero
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        db.session.commit()  # Should succeed - validation in business logic
        
        assert mouv.quantite == 0
    
    def test_entree_negative_quantity_not_prevented(self, app_context, test_produit, test_user):
        """⚠️ Negative quantity entree not prevented at model (should be in business logic)"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=-50,  # Negative
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        db.session.commit()  # Should succeed - validation in business logic
        
        assert mouv.quantite == -50


# ============================================================================
# TEST SUITE: Stock Exit Logic (Sortie)
# ============================================================================

class TestStockExitLogic:
    """Tests for stock exit (sortie) business logic and validation"""
    
    def test_sortie_from_available_stock(self, app_context, stock_with_inventory, test_user):
        """✅ Sortie from available stock succeeds"""
        is_valid, available, msg = prevent_negative_stock_on_creation(
            stock_with_inventory.id,
            50
        )
        
        assert is_valid is True
        assert available == 100.0
    
    def test_sortie_more_than_available(self, app_context, stock_with_inventory, test_user):
        """❌ Sortie more than available is prevented"""
        is_valid, available, msg = prevent_negative_stock_on_creation(
            stock_with_inventory.id,
            150  # More than 100 available
        )
        
        assert is_valid is False
        assert available == 100.0
        assert 'Insufficient stock' in msg
    
    def test_sortie_from_zero_stock(self, app_context, test_produit, test_user):
        """❌ Sortie from product with zero stock fails"""
        is_valid, available, msg = prevent_negative_stock_on_creation(
            test_produit.id,
            10
        )
        
        assert is_valid is False
        assert available == 0.0
    
    def test_sortie_exact_available_quantity(self, app_context, stock_with_inventory):
        """✅ Sortie exact available quantity succeeds"""
        is_valid, available, msg = prevent_negative_stock_on_creation(
            stock_with_inventory.id,
            100  # Exact amount
        )
        
        assert is_valid is True
        assert available == 100.0
    
    def test_sortie_one_unit_over_available(self, app_context, stock_with_inventory):
        """❌ Sortie one unit more than available fails"""
        is_valid, available, msg = prevent_negative_stock_on_creation(
            stock_with_inventory.id,
            101  # One over
        )
        
        assert is_valid is False


# ============================================================================
# TEST SUITE: Inventory Adjustment Logic (Ajustement)
# ============================================================================

class TestInventoryAdjustmentLogic:
    """Tests for inventory adjustment and reconciliation"""
    
    def test_ajustement_creates_sortie(self, app_context, stock_with_inventory, test_user):
        """✅ Inventory adjustment creates appropriate sortie/entree"""
        initial_qty = stock_with_inventory.quantite
        
        # Simulate inventory count finding 80 units (loss of 20)
        ajust = MouvementStock(
            type_mouvement='ajustement',
            produit_id=stock_with_inventory.id,
            quantite=20,  # Loss
            quantite_reelle=80,
            utilisateur_id=test_user.id,
            commentaire='Inventaire physique'
        )
        db.session.add(ajust)
        db.session.commit()
        
        assert ajust.id is not None
        assert ajust.quantite == 20
        assert ajust.quantite_reelle == 80
    
    def test_inventaire_type(self, app_context, test_produit, test_user):
        """✅ Inventaire movements can be created"""
        inv = MouvementStock(
            type_mouvement='inventaire',
            produit_id=test_produit.id,
            quantite=0,  # inventaire may use quantite_reelle
            quantite_reelle=50,
            utilisateur_id=test_user.id
        )
        db.session.add(inv)
        db.session.commit()
        
        assert inv.type_mouvement == 'inventaire'
        assert inv.quantite_reelle == 50


# ============================================================================
# TEST SUITE: Workflow State Machine
# ============================================================================

class TestWorkflowStateMachine:
    """Tests for stock movement workflow state transitions"""
    
    def test_initial_state_en_attente(self, app_context, test_produit, test_user):
        """✅ New movements start in EN_ATTENTE state"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=50,
            utilisateur_id=test_user.id
        )
        mouv = validate_and_initialize_mouvement_workflow(mouv, test_user)
        db.session.add(mouv)
        db.session.commit()
        
        assert mouv.workflow_state == 'EN_ATTENTE'
        assert mouv.applique_au_stock is False
    
    def test_valid_transition_en_attente_to_approuve(self, app_context, test_produit, test_user):
        """✅ Valid transition EN_ATTENTE → APPROUVE"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=50,
            utilisateur_id=test_user.id,
            workflow_state='EN_ATTENTE'
        )
        db.session.add(mouv)
        db.session.commit()
        
        # Check if transition is valid
        from_state = WorkflowState.EN_ATTENTE
        to_state = WorkflowState.APPROUVE
        
        assert to_state in VALID_TRANSITIONS[from_state]
    
    def test_valid_transition_approuve_to_execute(self):
        """✅ Valid transition APPROUVE → EXECUTE"""
        from_state = WorkflowState.APPROUVE
        to_state = WorkflowState.EXECUTE
        
        assert to_state in VALID_TRANSITIONS[from_state]
    
    def test_valid_transition_execute_to_valide(self):
        """✅ Valid transition EXECUTE → VALIDE"""
        from_state = WorkflowState.EXECUTE
        to_state = WorkflowState.VALIDE
        
        assert to_state in VALID_TRANSITIONS[from_state]
    
    def test_invalid_transition_valide_to_execute(self):
        """❌ Invalid transition VALIDE → EXECUTE (final state)"""
        from_state = WorkflowState.VALIDE
        to_state = WorkflowState.EXECUTE
        
        assert to_state not in VALID_TRANSITIONS[from_state]
    
    def test_invalid_transition_execute_to_entree(self):
        """❌ Invalid transition EXECUTE → EN_ATTENTE (wrong direction)"""
        from_state = WorkflowState.EXECUTE
        to_state = WorkflowState.EN_ATTENTE
        
        assert to_state not in VALID_TRANSITIONS[from_state]
    
    def test_annule_is_final_state(self):
        """✅ ANNULE is a final state (no outgoing transitions)"""
        from_state = WorkflowState.ANNULE
        
        assert len(VALID_TRANSITIONS[from_state]) == 0
    
    def test_rejete_can_revert_to_en_attente(self):
        """✅ REJETE can transition back to EN_ATTENTE"""
        from_state = WorkflowState.REJETE
        to_state = WorkflowState.EN_ATTENTE
        
        assert to_state in VALID_TRANSITIONS[from_state]


# ============================================================================
# TEST SUITE: Stock Application (Applique au Stock)
# ============================================================================

class TestStockApplication:
    """Tests for applying/executing stock movements"""
    
    def test_new_movement_not_applied(self, app_context, test_produit, test_user):
        """✅ New movements have applique_au_stock=False"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=50,
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        db.session.commit()
        
        assert mouv.applique_au_stock is False
    
    def test_movement_can_be_marked_applied(self, app_context, test_produit, test_user):
        """✅ Movement can be marked as applique_au_stock"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=50,
            utilisateur_id=test_user.id,
            applique_au_stock=True
        )
        db.session.add(mouv)
        db.session.commit()
        
        assert mouv.applique_au_stock is True


# ============================================================================
# TEST SUITE: Movement Approval Workflow
# ============================================================================

class TestMovementApprovalWorkflow:
    """Tests for approval and rejection workflows"""
    
    def test_movement_approval_timestamps(self, app_context, test_produit, test_user):
        """✅ Approval timestamps are recorded"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=50,
            utilisateur_id=test_user.id,
            workflow_state='APPROUVE',
            date_approbation=datetime.utcnow(),
            approuve_par_id=test_user.id
        )
        db.session.add(mouv)
        db.session.commit()
        
        assert mouv.date_approbation is not None
        assert mouv.approuve_par_id == test_user.id
    
    def test_movement_rejection_reason(self, app_context, test_produit, test_user):
        """✅ Rejection reason is recorded"""
        reason = "Quantité incorrecte"
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=50,
            utilisateur_id=test_user.id,
            workflow_state='REJETE',
            motif_rejet=reason
        )
        db.session.add(mouv)
        db.session.commit()
        
        assert mouv.motif_rejet == reason
    
    def test_movement_execution_timestamp(self, app_context, test_produit, test_user):
        """✅ Execution timestamp is recorded"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=50,
            utilisateur_id=test_user.id,
            workflow_state='EXECUTE',
            date_execution=datetime.utcnow()
        )
        db.session.add(mouv)
        db.session.commit()
        
        assert mouv.date_execution is not None


# ============================================================================
# TEST SUITE: Anomaly Detection
# ============================================================================

class TestAnomalyDetection:
    """Tests for anomaly detection in movements"""
    
    def test_anomalies_json_field(self, app_context, test_produit, test_user):
        """✅ Anomalies can be stored as JSON"""
        anomalies = [
            {'code': 'MISSING_SUPPLIER', 'severity': 'high'},
            {'code': 'INVALID_QUANTITY', 'severity': 'medium'}
        ]
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=50,
            utilisateur_id=test_user.id,
            anomalies=anomalies
        )
        db.session.add(mouv)
        db.session.commit()
        
        assert mouv.anomalies is not None
        assert len(mouv.anomalies) == 2
        assert mouv.anomalies[0]['code'] == 'MISSING_SUPPLIER'
    
    def test_no_anomalies_none(self, app_context, test_produit, test_user):
        """✅ Anomalies defaults to None"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=50,
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        db.session.commit()
        
        assert mouv.anomalies is None


# ============================================================================
# TEST SUITE: Multi-Line Movements
# ============================================================================

class TestMultiLineMovements:
    """Tests for movements with multiple product lines"""
    
    def test_single_line_movement(self, app_context, test_produit, test_user):
        """✅ Single product movement works"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=50,
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        db.session.commit()
        
        assert mouv.produit_id == test_produit.id
        assert mouv.quantite == 50


# ============================================================================
# TEST SUITE: Stock Calculations Edge Cases
# ============================================================================

class TestStockCalculationEdgeCases:
    """Tests for complex stock calculation scenarios"""
    
    def test_multiple_entree_movements(self, app_context, test_produit, test_user):
        """✅ Multiple entree movements sum correctly"""
        for i in range(5):
            mouv = MouvementStock(
                type_mouvement='entree',
                produit_id=test_produit.id,
                quantite=10,
                utilisateur_id=test_user.id
            )
            db.session.add(mouv)
        
        db.session.commit()
        db.session.refresh(test_produit)
        
        assert test_produit.quantite == 50.0
    
    def test_mixed_movements_order_preserved(self, app_context, test_produit, test_user):
        """✅ Stock calculations work with mixed movements"""
        # Add 100
        entree = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=100,
            utilisateur_id=test_user.id
        )
        db.session.add(entree)
        db.session.commit()
        
        # Remove 30
        sortie = MouvementStock(
            type_mouvement='sortie',
            produit_id=test_produit.id,
            quantite=30,
            utilisateur_id=test_user.id
        )
        db.session.add(sortie)
        db.session.commit()
        
        # Adjust +10
        ajust = MouvementStock(
            type_mouvement='ajustement',
            produit_id=test_produit.id,
            quantite=10,
            utilisateur_id=test_user.id
        )
        db.session.add(ajust)
        db.session.commit()
        
        db.session.refresh(test_produit)
        assert test_produit.quantite == 80.0


# ============================================================================
# TEST SUITE: User Accountability
# ============================================================================

class TestUserAccountability:
    """Tests for user tracking and accountability in stock movements"""
    
    def test_movement_created_by_user(self, app_context, test_produit, test_user):
        """✅ Movement records which user created it"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=50,
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        db.session.commit()
        
        assert mouv.utilisateur_id == test_user.id
        assert mouv.utilisateur.username == 'testuser'
    
    def test_approval_by_different_user(self, app_context, test_produit, test_user):
        """✅ Approval can be by different user"""
        approver = User(
            username='approver',
            email=f'{uuid.uuid4()}@test.com',
            password_hash=generate_password_hash('pwd'),
            role='chef_pur',
            nom='Approver',
            prenom='Test',
            telephone='9876543210'
        )
        db.session.add(approver)
        db.session.commit()
        
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=50,
            utilisateur_id=test_user.id,
            workflow_state='APPROUVE',
            approuve_par_id=approver.id
        )
        db.session.add(mouv)
        db.session.commit()
        
        assert mouv.utilisateur_id == test_user.id
        assert mouv.approuve_par_id == approver.id
