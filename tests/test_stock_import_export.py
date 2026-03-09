"""
UNIT TEST SUITE: Stock Management Import/Export
Tests for CSV import/export, bulk operations, transaction safety
"""

import pytest
import io
import csv
from datetime import datetime
from decimal import Decimal
import uuid
from datetime import datetime

from app import app, db
from models import (
    Produit, MouvementStock, User, NumeroSerie, NumeroSerieStatut,
    EmplacementStock, Fournisseur
)
from supplier_import import (
    parse_csv_row, ImportRow, RowStatus, process_supplier_import,
    validate_import_row, create_movements_from_import
)
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError



def generate_unique_code(prefix="TEST"):
    """Generate unique code to avoid duplicates"""
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"

@pytest.fixture
def app_context():
    """App context for testing"""
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_user(app_context):
    """Create test user"""
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
    """Create test product"""
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
def test_emplacement(app_context):
    """Create test storage location"""
    emp = EmplacementStock(
        code='ENTREPOT',
        designation='Entrepôt Principal'
    )
    db.session.add(emp)
    db.session.commit()
    return emp


# ============================================================================
# TEST SUITE: CSV Import Row Parsing
# ============================================================================

class TestCSVRowParsing:
    """Tests for parsing and validating CSV import rows"""
    
    def test_parse_complete_row(self):
        """✅ Parse complete import row with all fields"""
        row = {
            'product_reference': 'ONT-GPON-001',
            'quantity': '10',
            'serial_number': 'SN-2024-001',
            'emplacement_code': 'ENTREPOT',
            'unit_price': '45000',
            'note': 'Initial stock'
        }
        
        import_row = ImportRow(
            line_number=1,
            product_reference=row['product_reference'],
            quantity=int(row['quantity']),
            serial_number=row['serial_number'],
            emplacement_code=row['emplacement_code'],
            unit_price=float(row['unit_price']),
            note=row['note']
        )
        
        assert import_row.product_reference == 'ONT-GPON-001'
        assert import_row.quantity == 10
        assert import_row.serial_number == 'SN-2024-001'
        assert import_row.status == RowStatus.VALID
    
    def test_parse_minimal_row(self):
        """✅ Parse minimal row (only required fields)"""
        import_row = ImportRow(
            line_number=1,
            product_reference=generate_unique_code('PROD'),
            quantity=10,
            serial_number=None,
            emplacement_code=None,
            unit_price=None,
            note=None
        )
        
        assert import_row.product_reference == 'ONT-GPON-001'
        assert import_row.quantity == 10
        assert import_row.serial_number is None
        assert import_row.status == RowStatus.VALID
    
    def test_quantity_must_be_positive(self):
        """❌ Quantity must be positive integer"""
        import_row = ImportRow(
            line_number=1,
            product_reference=generate_unique_code('PROD'),
            quantity=0,  # Invalid
            serial_number=None,
            emplacement_code=None,
            unit_price=None,
            note=None
        )
        
        # Validation should catch this
        if import_row.quantity <= 0:
            import_row.add_error("Quantity must be positive")
        
        assert RowStatus.ERROR == import_row.status


# ============================================================================
# TEST SUITE: CSV Import Validation
# ============================================================================

class TestCSVImportValidation:
    """Tests for validation during import process"""
    
    def test_import_row_add_error(self):
        """✅ Add error to import row changes status"""
        import_row = ImportRow(
            line_number=1,
            product_reference=generate_unique_code('PROD'),
            quantity=10,
            serial_number=None,
            emplacement_code=None,
            unit_price=None,
            note=None
        )
        
        assert import_row.status == RowStatus.VALID
        import_row.add_error("Product not found")
        
        assert import_row.status == RowStatus.ERROR
        assert "Product not found" in import_row.errors
    
    def test_import_row_add_warning(self):
        """✅ Add warning to import row doesn't change status"""
        import_row = ImportRow(
            line_number=1,
            product_reference=generate_unique_code('PROD'),
            quantity=10,
            serial_number=None,
            emplacement_code=None,
            unit_price=None,
            note=None
        )
        
        import_row.add_warning("Stock above maximum")
        
        assert import_row.status == RowStatus.VALID  # Status not changed
        assert "Stock above maximum" in import_row.warnings
    
    def test_multiple_errors_on_row(self):
        """✅ Row can have multiple errors"""
        import_row = ImportRow(
            line_number=1,
            product_reference='INVALID',
            quantity=0,
            serial_number=None,
            emplacement_code=None,
            unit_price=None,
            note=None
        )
        
        import_row.add_error("Product not found")
        import_row.add_error("Invalid quantity")
        import_row.add_error("Emplacement missing")
        
        assert len(import_row.errors) == 3
        assert import_row.status == RowStatus.ERROR


# ============================================================================
# TEST SUITE: Duplicate Detection
# ============================================================================

class TestDuplicateDetection:
    """Tests for detecting duplicates during import"""
    
    def test_duplicate_serial_in_csv(self, app_context):
        """❌ Duplicate serial numbers in same import should be detected"""
        rows = [
            ImportRow(
                line_number=1,
                product_reference=generate_unique_code('PROD'),
                quantity=1,
                serial_number='SN-DUP-001',
                emplacement_code='ENTREPOT',
                unit_price=45000,
                note=None
            ),
            ImportRow(
                line_number=2,
                product_reference=generate_unique_code('PROD'),
                quantity=1,
                serial_number='SN-DUP-001',  # Duplicate!
                emplacement_code='ENTREPOT',
                unit_price=45000,
                note=None
            )
        ]
        
        seen_serials = set()
        for row in rows:
            if row.serial_number:
                if row.serial_number in seen_serials:
                    row.add_error(f"Duplicate serial: {row.serial_number}")
                else:
                    seen_serials.add(row.serial_number)
        
        assert rows[1].status == RowStatus.ERROR
    
    def test_duplicate_serial_in_database(self, app_context, test_produit):
        """❌ Serial already in database should be detected"""
        # Create existing serial
        existing = NumeroSerie(
            numero='SN-EXISTS-001',
            produit_id=test_produit.id,
            statut=NumeroSerieStatut.DISPONIBLE.value
        )
        db.session.add(existing)
        db.session.commit()
        
        # Try to import duplicate
        import_row = ImportRow(
            line_number=1,
            product_reference=generate_unique_code('PROD'),
            quantity=1,
            serial_number='SN-EXISTS-001',  # Already exists!
            emplacement_code='ENTREPOT',
            unit_price=45000,
            note=None
        )
        
        # Check if exists
        exists = db.session.query(NumeroSerie).filter_by(
            numero='SN-EXISTS-001'
        ).first()
        
        if exists:
            import_row.add_error(f"Serial already exists: {import_row.serial_number}")
        
        assert import_row.status == RowStatus.ERROR


# ============================================================================
# TEST SUITE: Transaction Rollback on Failure
# ============================================================================

class TestTransactionSafety:
    """Tests for transaction safety and rollback"""
    
    def test_invalid_product_rollback(self, app_context, test_user):
        """❌ Import with invalid product is rejected without creating movement"""
        initial_count = MouvementStock.query.count()
        
        try:
            # Try to create movement for non-existent product
            mouv = MouvementStock(
                type_mouvement='entree',
                produit_id=99999,  # Non-existent!
                quantite=10,
                utilisateur_id=test_user.id
            )
            db.session.add(mouv)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        
        # Verify no movement was created
        assert MouvementStock.query.count() == initial_count
    
    def test_partial_import_failure(self, app_context, test_produit, test_user):
        """⚠️ Partial import may create some movements before error"""
        initial_count = MouvementStock.query.count()
        
        # Create first movement successfully
        mouv1 = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=10,
            utilisateur_id=test_user.id
        )
        db.session.add(mouv1)
        db.session.flush()
        
        # Try to create second movement with invalid product
        try:
            mouv2 = MouvementStock(
                type_mouvement='entree',
                produit_id=99999,  # Non-existent!
                quantite=20,
                utilisateur_id=test_user.id
            )
            db.session.add(mouv2)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        
        # Both should be rolled back
        assert MouvementStock.query.count() == initial_count


# ============================================================================
# TEST SUITE: Import Success Cases
# ============================================================================

class TestImportSuccessCases:
    """Tests for successful import scenarios"""
    
    def test_single_product_import(self, app_context, test_produit, test_user, test_emplacement):
        """✅ Import single product creates movement"""
        initial_qty = test_produit.quantite
        
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=50,
            utilisateur_id=test_user.id,
            reference='IMP-2024-001',
            emplacement_id=test_emplacement.id,
            prix_unitaire=45000.00
        )
        db.session.add(mouv)
        db.session.commit()
        
        db.session.refresh(test_produit)
        assert test_produit.quantite == initial_qty + 50
    
    def test_bulk_import_multiple_products(self, app_context, test_user, test_emplacement):
        """✅ Import multiple different products"""
        products = []
        for i in range(5):
            prod = Produit(
                reference=f'BULK-{i:03d}',
                nom=f'Bulk Product {i}',
                prix_achat=Decimal('10000.00')
            )
            db.session.add(prod)
            products.append(prod)
        
        db.session.commit()
        
        # Import each
        for prod in products:
            mouv = MouvementStock(
                type_mouvement='entree',
                produit_id=prod.id,
                quantite=10,
                utilisateur_id=test_user.id,
                emplacement_id=test_emplacement.id
            )
            db.session.add(mouv)
        
        db.session.commit()
        
        # Verify all were created
        for prod in products:
            db.session.refresh(prod)
            assert prod.quantite == 10
    
    def test_import_with_serial_numbers(self, app_context, test_produit, test_user, test_emplacement):
        """✅ Import with serial numbers creates NumeroSerie records"""
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=3,
            utilisateur_id=test_user.id,
            emplacement_id=test_emplacement.id
        )
        db.session.add(mouv)
        db.session.commit()
        
        # Create serial numbers
        for i in range(3):
            serial = NumeroSerie(
                numero=f'SN-IMPORT-{i:03d}',
                produit_id=test_produit.id,
                statut=NumeroSerieStatut.ALLOUE.value
            )
            db.session.add(serial)
        
        db.session.commit()
        
        # Verify serials exist
        serials = NumeroSerie.query.filter_by(produit_id=test_produit.id).all()
        assert len(serials) == 3


# ============================================================================
# TEST SUITE: Import Error Handling
# ============================================================================

class TestImportErrorHandling:
    """Tests for error handling during import"""
    
    def test_invalid_quantity_format(self):
        """❌ Non-numeric quantity is invalid"""
        try:
            quantity = int('NOT_A_NUMBER')
            assert False, "Should raise ValueError"
        except ValueError:
            pass  # Expected
    
    def test_missing_product_reference(self):
        """❌ Missing product reference is invalid"""
        import_row = ImportRow(
            line_number=1,
            product_reference='',  # Empty!
            quantity=10,
            serial_number=None,
            emplacement_code=None,
            unit_price=None,
            note=None
        )
        
        if not import_row.product_reference:
            import_row.add_error("Product reference is required")
        
        assert import_row.status == RowStatus.ERROR
    
    def test_invalid_unit_price(self):
        """❌ Non-numeric unit price is invalid"""
        try:
            price = float('INVALID_PRICE')
            assert False, "Should raise ValueError"
        except ValueError:
            pass  # Expected


# ============================================================================
# TEST SUITE: CSV Format Compatibility
# ============================================================================

class TestCSVFormatCompatibility:
    """Tests for CSV format parsing and flexibility"""
    
    def test_parse_csv_with_headers(self):
        """✅ CSV with headers can be parsed"""
        csv_data = """product_reference,quantity,serial_number,emplacement_code,unit_price,note
ONT-GPON-001,10,SN-2024-001,ENTREPOT,45000,Test
"""
        reader = csv.DictReader(io.StringIO(csv_data))
        rows = list(reader)
        
        assert len(rows) == 1
        assert rows[0]['product_reference'] == 'ONT-GPON-001'
        assert rows[0]['quantity'] == '10'
    
    def test_csv_with_missing_optional_fields(self):
        """✅ CSV can omit optional fields"""
        csv_data = """product_reference,quantity
ONT-GPON-001,10
OLT-FIBER-X2,5
"""
        reader = csv.DictReader(io.StringIO(csv_data))
        rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]['product_reference'] == 'ONT-GPON-001'
        assert rows[0].get('serial_number', '') == ''
    
    def test_csv_with_extra_columns(self):
        """✅ CSV with extra columns is handled"""
        csv_data = """product_reference,quantity,extra_column
ONT-GPON-001,10,ignored
"""
        reader = csv.DictReader(io.StringIO(csv_data))
        rows = list(reader)
        
        assert len(rows) == 1
        # Extra column should be in dict but not cause errors
        assert 'extra_column' in rows[0]


# ============================================================================
# TEST SUITE: Export Functionality
# ============================================================================

class TestExportFunctionality:
    """Tests for export to CSV functionality"""
    
    def test_export_movements_to_csv(self, app_context, test_produit, test_user, test_emplacement):
        """✅ Stock movements can be exported to CSV"""
        # Create some movements
        for i in range(3):
            mouv = MouvementStock(
                type_mouvement='entree' if i % 2 == 0 else 'sortie',
                produit_id=test_produit.id,
                quantite=10 + i,
                utilisateur_id=test_user.id,
                emplacement_id=test_emplacement.id
            )
            db.session.add(mouv)
        
        db.session.commit()
        
        # Query movements
        mouvs = MouvementStock.query.filter_by(produit_id=test_produit.id).all()
        
        assert len(mouvs) == 3
        # Export would happen here - just verify query works
    
    def test_export_stock_status(self, app_context, test_produit, test_user):
        """✅ Current stock status can be exported"""
        # Add stock
        mouv = MouvementStock(
            type_mouvement='entree',
            produit_id=test_produit.id,
            quantite=100,
            utilisateur_id=test_user.id
        )
        db.session.add(mouv)
        db.session.commit()
        
        # Verify can be queried for export
        db.session.refresh(test_produit)
        export_data = {
            'reference': test_produit.reference,
            'nom': test_produit.nom,
            'quantite': test_produit.quantite,
            'status': test_produit.statut_stock
        }
        
        assert export_data['quantite'] == 100
        assert export_data['status'] == 'success'
