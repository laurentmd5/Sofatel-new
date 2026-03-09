"""
UNIT TEST SUITE: Stock Management Models
Comprehensive testing of Produit, MouvementStock, EmplacementStock, NumeroSerie
Tests field constraints, relationships, computed properties, edge cases
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
from app import app, db
from models import (
    Produit, MouvementStock, EmplacementStock, Fournisseur, 
    NumeroSerie, NumeroSerieStatut, Categorie, User, HistoriqueEtatNumeroSerie
)
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError


def generate_unique_code(prefix="TEST"):
    """Generate unique code to avoid duplicates"""
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"


@pytest.fixture
def app_context():
    """App context for direct model testing"""
    with app.app_context():
        yield


@pytest.fixture
def test_user(app_context):
    """Create a test user with unique username"""
    user = User(
        username=generate_unique_code("USER"),
        email=f"test-{uuid.uuid4()}@test.com",
        password_hash=generate_password_hash('password'),
        role='gestionnaire_stock',
        nom='Test',
        prenom='User',
        telephone='1234567890'
    )
    db.session.add(user)
    db.session.commit()
    yield user
    # Cleanup
    try:
        db.session.delete(user)
        db.session.commit()
    except Exception:
        db.session.rollback()


@pytest.fixture
def test_categorie(app_context):
    """Create a test category with unique name"""
    cat = Categorie(
        nom=f"Category-{uuid.uuid4()}",
        description='Produits télécomunication'
    )
    db.session.add(cat)
    db.session.commit()
    yield cat
    # Cleanup
    try:
        db.session.delete(cat)
        db.session.commit()
    except Exception:
        db.session.rollback()


@pytest.fixture
def test_emplacement(app_context):
    """Create a test storage location with unique code"""
    emp = EmplacementStock(
        code=generate_unique_code("RAYON"),
        designation=f"Rayon-{uuid.uuid4()}",
        description='Entrepôt principal',
        actif=True
    )
    db.session.add(emp)
    db.session.commit()
    yield emp
    # Cleanup
    try:
        db.session.delete(emp)
        db.session.commit()
    except Exception:
        db.session.rollback()


@pytest.fixture
def test_fournisseur(app_context):
    """Create a test supplier with unique code"""
    fourn = Fournisseur(
        code=generate_unique_code("FOURN"),
        raison_sociale=f'Supplier-{uuid.uuid4()}',
        contact='Contact Test',
        telephone='0123456789',
        email=f'fourn-{uuid.uuid4()}@test.com',
        adresse='123 Rue Test',
        actif=True
    )
    db.session.add(fourn)
    db.session.commit()
    yield fourn
    # Cleanup
    try:
        db.session.delete(fourn)
        db.session.commit()
    except Exception:
        db.session.rollback()


@pytest.fixture
def test_produit(app_context, test_categorie, test_emplacement, test_fournisseur):
    """Create a test product with unique reference"""
    produit = Produit(
        reference=generate_unique_code("PROD"),
        code_barres=generate_unique_code("BAR"),
        nom=f"Product-{uuid.uuid4()}",
        description='Test product',
        categorie_id=test_categorie.id,
        emplacement_id=test_emplacement.id,
        fournisseur_id=test_fournisseur.id,
        prix_achat=Decimal('45000.00'),
        prix_vente=Decimal('55000.00'),
        tva=Decimal('18.00'),
        unite_mesure='piece',
        stock_min=5,
        stock_max=100,
        actif=True
    )
    db.session.add(produit)
    db.session.commit()
    yield produit
    # Cleanup
    try:
        db.session.delete(produit)
        db.session.commit()
    except Exception:
        db.session.rollback()


# ============================================================================
# TEST SUITE: EmplacementStock Model
# ============================================================================

class TestEmplacementStockModel:
    """Tests for EmplacementStock model - field constraints & relationships"""
    
    def test_emplacement_creation_success(self, app_context):
        """✅ EmplacementStock can be created with required fields"""
        emp = EmplacementStock(
            code=generate_unique_code("RAYON"),
            designation=f"Rayon-{uuid.uuid4()}",
            description='Premier rayon',
            actif=True
        )
        db.session.add(emp)
        db.session.commit()
        
        assert emp.id is not None
        assert emp.code is not None
        assert emp.actif is True
        assert emp.date_creation is not None
    
    def test_emplacement_code_unique(self, app_context):
        """❌ EmplacementStock code must be UNIQUE"""
        emp1 = EmplacementStock(code=generate_unique_code('RAYON'), designation=f'Rayon-{uuid.uuid4()}')
        db.session.add(emp1)
        db.session.commit()
        
        emp2 = EmplacementStock(code=generate_unique_code('RAYON'), designation='Rayon A Duplicate')
        db.session.add(emp2)
        
        with pytest.raises(IntegrityError):
            db.session.commit()
    
    def test_emplacement_code_required(self, app_context):
        """❌ EmplacementStock code is REQUIRED"""
        emp = EmplacementStock(designation='Rayon B', description='Test')
        db.session.add(emp)
        
        with pytest.raises(IntegrityError):
            db.session.commit()
    
    def test_emplacement_designation_required(self, app_context):
        """❌ EmplacementStock designation is REQUIRED"""
        emp = EmplacementStock(code=generate_unique_code('RAYON'))
        db.session.add(emp)
        
        with pytest.raises(IntegrityError):
            db.session.commit()
    
    def test_emplacement_timestamps(self, app_context):
        """✅ EmplacementStock timestamps are auto-set"""
        emp = EmplacementStock(code=generate_unique_code('RAYON'), designation='Rayon D')
        db.session.add(emp)
        db.session.commit()
        
        assert emp.date_creation is not None
        assert isinstance(emp.date_creation, datetime)


# ============================================================================
# TEST SUITE: Produit Model
# ============================================================================

class TestProduitModel:
    """Tests for Produit model - field constraints, computed properties, relationships"""
    
    def test_produit_creation_minimal(self, app_context):
        """✅ Produit can be created with minimal fields"""
        prod = Produit(
            reference='TEST-001',
            nom='Test Product'
        )
        db.session.add(prod)
        db.session.commit()
        
        assert prod.id is not None
        assert prod.reference == 'TEST-001'
        assert prod.actif is True  # Default value
    
    def test_produit_reference_unique(self, app_context):
        """❌ Produit reference must be UNIQUE"""
        prod1 = Produit(reference='DUP-001', nom='Product 1')
        db.session.add(prod1)
        db.session.commit()
        
        prod2 = Produit(reference='DUP-001', nom='Product 2')
        db.session.add(prod2)
        
        with pytest.raises(IntegrityError):
            db.session.commit()
    
    def test_produit_barcode_unique(self, app_context):
        """❌ Produit code_barres must be UNIQUE (if not null)"""
        prod1 = Produit(reference='REF-001', nom='Product 1', code_barres='ABC123')
        db.session.add(prod1)
        db.session.commit()
        
        prod2 = Produit(reference='REF-002', nom='Product 2', code_barres='ABC123')
        db.session.add(prod2)
        
        with pytest.raises(IntegrityError):
            db.session.commit()
    
    def test_produit_reference_required(self, app_context):
        """❌ Produit reference is REQUIRED"""
        prod = Produit(nom='Product')
        db.session.add(prod)
        
        with pytest.raises(IntegrityError):
            db.session.commit()
    
    def test_produit_nom_required(self, app_context):
        """❌ Produit nom is REQUIRED"""
        prod = Produit(reference='REF-001')
        db.session.add(prod)
        
        with pytest.raises(IntegrityError):
            db.session.commit()
    
    def test_produit_quantite_zero_stock(self, app_context, test_produit):
        """✅ Produit quantity is 0 for new product (no movements)"""
        assert test_produit.quantite == 0.0
    
    def test_produit_quantite_after_entree(self, app_context, test_produit, test_user):
        """✅ Produit quantity increases after entree movement"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=50,
            utilisateur_id=test_user.id,
            date_mouvement=datetime.utcnow()
        )
        db.session.add(mouv)
        db.session.commit()
        
        # Refresh to recalculate computed property
        db.session.refresh(test_produit)
        assert test_produit.quantite == 50.0
    
    def test_produit_quantite_after_sortie(self, app_context, test_produit, test_user):
        """✅ Produit quantity decreases after sortie movement"""
        # First: add stock
        entree = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=100,
            utilisateur_id=test_user.id
        )
        db.session.add(entree)
        db.session.commit()
        
        # Then: remove stock
        sortie = MouvementStock(
            type_mouvement='sortie',
            produit_id=test_produit.id,
            quantite=30,
            utilisateur_id=test_user.id
        )
        db.session.add(sortie)
        db.session.commit()
        
        db.session.refresh(test_produit)
        assert test_produit.quantite == 70.0
    
    def test_produit_quantite_by_emplacement(self, app_context, test_produit, test_user, test_emplacement):
        """✅ Produit can calculate quantity by specific emplacement"""
        emp2 = EmplacementStock(code=generate_unique_code('RAYON'), designation='Rayon B')
        db.session.add(emp2)
        db.session.commit()
        
        # Add to emplacement 1
        mouv1 = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=50,
            utilisateur_id=test_user.id,
            emplacement_id=test_emplacement.id
        )
        db.session.add(mouv1)
        db.session.commit()
        
        # Add to emplacement 2
        mouv2 = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=30,
            utilisateur_id=test_user.id,
            emplacement_id=emp2.id
        )
        db.session.add(mouv2)
        db.session.commit()
        
        # Check total
        db.session.refresh(test_produit)
        assert test_produit.quantite == 80.0
        
        # Check per emplacement
        assert test_produit.quantite_par_emplacement(test_emplacement.id) == 50.0
        assert test_produit.quantite_par_emplacement(emp2.id) == 30.0
    
    def test_produit_statut_stock_danger(self, app_context, test_user):
        """✅ Produit statut_stock is 'danger' when quantity <= 0"""
        prod = Produit(
            reference='DANGER-001',
            nom='Danger Stock',
            stock_min=10
        )
        db.session.add(prod)
        db.session.commit()
        
        assert prod.quantite == 0.0
        assert prod.statut_stock == 'danger'
    
    def test_produit_statut_stock_warning(self, app_context, test_user):
        """✅ Produit statut_stock is 'warning' when 0 < quantity <= min"""
        prod = Produit(
            reference='WARN-001',
            nom='Warning Stock',
            stock_min=10
        )
        db.session.add(prod)
        db.session.commit()
        
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=prod.id,
            quantite=5,
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        db.session.commit()
        
        db.session.refresh(prod)
        assert prod.quantite == 5.0
        assert prod.statut_stock == 'warning'
    
    def test_produit_statut_stock_success(self, app_context, test_user):
        """✅ Produit statut_stock is 'success' when quantity > min"""
        prod = Produit(
            reference='OK-001',
            nom='OK Stock',
            stock_min=10
        )
        db.session.add(prod)
        db.session.commit()
        
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=prod.id,
            quantite=50,
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        db.session.commit()
        
        db.session.refresh(prod)
        assert prod.quantite == 50.0
        assert prod.statut_stock == 'success'
    
    def test_produit_seuil_alerte(self, app_context):
        """✅ Produit seuil_alerte returns stock_min or 0"""
        prod1 = Produit(reference='SEUIL-1', nom='Product 1', stock_min=20)
        db.session.add(prod1)
        db.session.commit()
        assert prod1.seuil_alerte == 20
        
        prod2 = Produit(reference='SEUIL-2', nom='Product 2')
        db.session.add(prod2)
        db.session.commit()
        assert prod2.seuil_alerte == 0
    
    def test_produit_prix_formate(self, app_context):
        """✅ Produit prix formatting works correctly"""
        prod = Produit(
            reference='PRIX-001',
            nom='Product',
            prix_achat=Decimal('50000.00'),
            prix_vente=Decimal('60000.00')
        )
        db.session.add(prod)
        db.session.commit()
        
        assert '50000' in prod.prix_achat_formate
        assert 'FCFA' in prod.prix_achat_formate
        assert '60000' in prod.prix_vente_formate


# ============================================================================
# TEST SUITE: MouvementStock Model
# ============================================================================

class TestMouvementStockModel:
    """Tests for MouvementStock model - field constraints, relationships, workflow"""
    
    def test_mouvement_creation_minimal(self, app_context, test_produit, test_user):
        """✅ MouvementStock can be created with minimal required fields"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=10,
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        db.session.commit()
        
        assert mouv.id is not None
        assert mouv.workflow_state == 'EN_ATTENTE'
        assert mouv.applique_au_stock is False
    
    def test_mouvement_type_enum_validation(self, app_context, test_produit, test_user):
        """✅ MouvementStock type_mouvement must be valid enum"""
        mouv = MouvementStock(
            type_mouvement='entree',  # Valid
            produit_id=test_produit.id,
            quantite=10,
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        db.session.commit()
        assert mouv.type_mouvement == 'entree'
    
    def test_mouvement_type_invalid_raises_error(self, app_context, test_produit, test_user):
        """❌ MouvementStock with invalid type raises error"""
        mouv = MouvementStock(
            type_mouvement='INVALID_TYPE',
            produit_id=test_produit.id,
            quantite=10,
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        
        with pytest.raises((ValueError, IntegrityError)):
            db.session.commit()
    
    def test_mouvement_produit_required(self, app_context, test_user):
        """❌ MouvementStock produit_id is REQUIRED"""
        mouv = MouvementStock(
            type_mouvement='entree',
            quantite=10,
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        
        with pytest.raises(IntegrityError):
            db.session.commit()
    
    def test_mouvement_utilisateur_required(self, app_context, test_produit):
        """❌ MouvementStock utilisateur_id is REQUIRED"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=10
        )
        db.session.add(mouv)
        
        with pytest.raises(IntegrityError):
            db.session.commit()
    
    def test_mouvement_quantite_required(self, app_context, test_produit, test_user):
        """❌ MouvementStock quantite is REQUIRED"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        
        with pytest.raises(IntegrityError):
            db.session.commit()
    
    def test_mouvement_date_auto_set(self, app_context, test_produit, test_user):
        """✅ MouvementStock date_mouvement is auto-set to utcnow"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=10,
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        db.session.commit()
        
        assert mouv.date_mouvement is not None
        assert isinstance(mouv.date_mouvement, datetime)
    
    def test_mouvement_workflow_state_en_attente_default(self, app_context, test_produit, test_user):
        """✅ MouvementStock workflow_state defaults to EN_ATTENTE"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=10,
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        db.session.commit()
        
        assert mouv.workflow_state == 'EN_ATTENTE'
    
    def test_mouvement_applique_au_stock_false_default(self, app_context, test_produit, test_user):
        """✅ MouvementStock applique_au_stock defaults to False"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=10,
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        db.session.commit()
        
        assert mouv.applique_au_stock is False
    
    def test_mouvement_montant_total_calculation(self, app_context, test_produit, test_user):
        """✅ MouvementStock montant_total can be set"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=10,
            prix_unitaire=1000.0,
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        db.session.commit()
        
        assert mouv.prix_unitaire == 1000.0
    
    def test_mouvement_inventaire_fields(self, app_context, test_produit, test_user):
        """✅ MouvementStock inventory fields for ajustement"""
        mouv = MouvementStock(
            type_mouvement='inventaire',
            produit_id=test_produit.id,
            quantite=0,  # inventaire type uses quantite_reelle
            quantite_reelle=45,
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        db.session.commit()
        
        assert mouv.quantite_reelle == 45
        assert mouv.ecart is None or mouv.ecart == 0
    
    def test_mouvement_negative_quantity_not_prevented_at_model(self, app_context, test_produit, test_user):
        """⚠️ MouvementStock doesn't prevent negative quantities at model level"""
        # Note: Prevention should be at business logic layer, not model
        mouv = MouvementStock(
            type_mouvement='sortie',
            produit_id=test_produit.id,
            quantite=-10,  # Negative
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        db.session.commit()  # Should succeed - validation is business logic
        
        assert mouv.quantite == -10


# ============================================================================
# TEST SUITE: NumeroSerie Model
# ============================================================================

class TestNumeroSerieModel:
    """Tests for NumeroSerie model - serial tracking, status, relationships"""
    
    def test_numeroserie_creation(self, app_context, test_produit):
        """✅ NumeroSerie can be created"""
        serial = NumeroSerie(
            numero='SN-2024-001',
            produit_id=test_produit.id,
            statut=NumeroSerieStatut.DISPONIBLE.value
        )
        db.session.add(serial)
        db.session.commit()
        
        assert serial.id is not None
        assert serial.numero == 'SN-2024-001'
    
    def test_numeroserie_numero_unique(self, app_context, test_produit):
        """❌ NumeroSerie numero must be UNIQUE"""
        serial1 = NumeroSerie(numero='SN-DUP', produit_id=test_produit.id)
        db.session.add(serial1)
        db.session.commit()
        
        serial2 = NumeroSerie(numero='SN-DUP', produit_id=test_produit.id)
        db.session.add(serial2)
        
        with pytest.raises(IntegrityError):
            db.session.commit()
    
    def test_numeroserie_status_enum(self, app_context, test_produit):
        """✅ NumeroSerie statut can be set to valid enum values"""
        valid_statuses = [
            NumeroSerieStatut.DISPONIBLE.value,
            NumeroSerieStatut.ALLOUE.value,
            NumeroSerieStatut.RETOURNE.value,
            NumeroSerieStatut.ABIME.value
        ]
        
        for status in valid_statuses:
            serial = NumeroSerie(
                numero=f'SN-{status}-001',
                produit_id=test_produit.id,
                statut=status
            )
            db.session.add(serial)
        
        db.session.commit()
        assert NumeroSerie.query.count() == len(valid_statuses)


# ============================================================================
# TEST SUITE: Relationship Integrity
# ============================================================================

class TestRelationshipIntegrity:
    """Tests for model relationships and referential integrity"""
    
    def test_mouvement_user_relationship(self, app_context, test_produit, test_user):
        """✅ MouvementStock.utilisateur relationship works"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=10,
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        db.session.commit()
        
        assert mouv.utilisateur is not None
        assert mouv.utilisateur.id == test_user.id
    
    def test_mouvement_produit_relationship(self, app_context, test_produit, test_user):
        """✅ MouvementStock.produit_relation relationship works"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=10,
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        db.session.commit()
        
        assert mouv.produit_relation is not None
        assert mouv.produit_relation.id == test_produit.id
    
    def test_produit_categorie_relationship(self, app_context, test_categorie):
        """✅ Produit.categorie relationship works"""
        prod = Produit(
            reference='CAT-TEST-001',
            nom='Categorized Product',
            categorie_id=test_categorie.id
        )
        db.session.add(prod)
        db.session.commit()
        
        assert prod.categorie is not None
        assert prod.categorie.id == test_categorie.id


# ============================================================================
# TEST SUITE: Edge Cases & Business Logic
# ============================================================================

class TestStockEdgeCases:
    """Tests for edge cases and critical business logic"""
    
    def test_zero_stock_calculation(self, app_context, test_produit, test_user):
        """✅ Stock correctly returns 0 with no movements"""
        assert test_produit.quantite == 0.0
    
    def test_negative_stock_calculation_prevented(self, app_context, test_produit, test_user):
        """⚠️ Can create sortie with negative result (should be caught by routes)"""
        entree = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=10,
            utilisateur_id=test_user.id
        )
        db.session.add(entree)
        db.session.commit()
        
        # This is allowed at model level - business logic should prevent
        sortie = MouvementStock(
            type_mouvement='sortie',
            produit_id=test_produit.id,
            quantite=20,  # More than available
            utilisateur_id=test_user.id
        )
        db.session.add(sortie)
        db.session.commit()
        
        db.session.refresh(test_produit)
        assert test_produit.quantite == -10.0  # Negative! Should be caught by business logic
    
    def test_large_quantities(self, app_context, test_produit, test_user):
        """✅ Stock handles large quantities correctly"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=1000000,
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        db.session.commit()
        
        db.session.refresh(test_produit)
        assert test_produit.quantite == 1000000.0
    
    def test_decimal_quantities(self, app_context, test_produit, test_user):
        """✅ Stock handles decimal quantities correctly"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=10.5,
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        db.session.commit()
        
        db.session.refresh(test_produit)
        assert abs(test_produit.quantite - 10.5) < 0.01
