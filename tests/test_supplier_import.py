"""
📦 SUPPLIER BULK IMPORT - TEST SUITE
Complete tests for CSV parsing, validation, and importing
"""

import pytest
import io
from datetime import datetime, timezone
from supplier_import import (
    SupplierImportParser,
    SupplierImportValidator,
    SupplierImporter,
    ImportRow,
    RowStatus,
    process_supplier_import
)
from models import Produit, MouvementStock, NumeroSerie, User, EmplacementStock
from extensions import db


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def test_user(app):
    """Create test user"""
    user = User(
        username='importer_test',
        email='importer@test.com',
        role='chef_pur'
    )
    user.set_password('test123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def test_products(app):
    """Create test products"""
    products = [
        Produit(
            reference='ONT-GPON-V5',
            nom='ONT GPON V5',
            code_barres='ONT-GPON-V5-001',
            prix_achat=45000,
            prix_vente=52000,
            actif=True
        ),
        Produit(
            reference='OLT-FIBER-X2',
            nom='OLT Fiber X2',
            code_barres='OLT-FIBER-X2-001',
            prix_achat=250000,
            prix_vente=300000,
            actif=True
        ),
        Produit(
            reference='SPLITTER-1X8',
            nom='Splitter 1x8',
            code_barres='SPLITTER-1X8-001',
            prix_achat=5000,
            prix_vente=7000,
            actif=True
        ),
        Produit(
            reference='INACTIVE-PRODUCT',
            nom='Inactive Product',
            code_barres='INACTIVE-001',
            actif=False
        )
    ]
    db.session.bulk_save_objects(products)
    db.session.commit()
    return {p.reference: p for p in products}


@pytest.fixture
def test_emplacement(app):
    """Create test emplacement"""
    emplacements = [
        EmplacementStock(
            code='ENTREPOT',
            designation='Entrepôt Principal',
            actif=True
        ),
        EmplacementStock(
            code='MAGASIN',
            designation='Magasin',
            actif=True
        ),
        EmplacementStock(
            code='ATELIER',
            designation='Atelier',
            actif=True
        )
    ]
    db.session.bulk_save_objects(emplacements)
    db.session.commit()
    return {e.code: e for e in emplacements}


# ============================================================================
# PARSER TESTS
# ============================================================================

class TestSupplierImportParser:
    """Test CSV parsing"""
    
    def test_parse_valid_csv(self):
        """Test parsing valid CSV"""
        csv_content = """product_reference,quantity
ONT-GPON-V5,10
OLT-FIBER-X2,5
"""
        parser = SupplierImportParser(csv_content)
        rows, errors = parser.parse()
        
        assert len(rows) == 2
        assert not errors
        assert rows[0].product_reference == 'ONT-GPON-V5'
        assert rows[0].quantity == 10
        assert rows[1].product_reference == 'OLT-FIBER-X2'
        assert rows[1].quantity == 5
    
    def test_parse_with_optional_columns(self):
        """Test parsing with optional columns"""
        csv_content = """product_reference,quantity,serial_number,unit_price,note
ONT-GPON-V5,10,SN-2024-001-010,45000,Initial stock
OLT-FIBER-X2,5,,250000,Test import
"""
        parser = SupplierImportParser(csv_content)
        rows, errors = parser.parse()
        
        assert len(rows) == 2
        assert not errors
        assert rows[0].serial_number == 'SN-2024-001-010'
        assert rows[0].unit_price == 45000
        assert rows[0].note == 'Initial stock'
        assert rows[1].serial_number is None
        assert rows[1].unit_price == 250000
    
    def test_parse_missing_required_column(self):
        """Test error on missing required column"""
        csv_content = """product_reference
ONT-GPON-V5
"""
        parser = SupplierImportParser(csv_content)
        rows, errors = parser.parse()
        
        assert len(rows) == 0
        assert 'Missing required columns' in errors[0]
        assert 'quantity' in errors[0]
    
    def test_parse_empty_file(self):
        """Test error on empty file"""
        csv_content = ""
        parser = SupplierImportParser(csv_content)
        rows, errors = parser.parse()
        
        assert len(rows) == 0
        assert 'empty' in errors[0].lower()
    
    def test_parse_invalid_quantity(self):
        """Test error on invalid quantity"""
        csv_content = """product_reference,quantity
ONT-GPON-V5,invalid
"""
        parser = SupplierImportParser(csv_content)
        rows, errors = parser.parse()
        
        assert len(rows) == 1
        assert rows[0].status == RowStatus.ERROR
        assert len(rows[0].errors) > 0
        assert 'quantity must be a valid integer' in rows[0].errors[0]
    
    def test_parse_zero_quantity(self):
        """Test error on zero quantity"""
        csv_content = """product_reference,quantity
ONT-GPON-V5,0
"""
        parser = SupplierImportParser(csv_content)
        rows, errors = parser.parse()
        
        assert len(rows) == 1
        assert rows[0].status == RowStatus.ERROR
        assert 'quantity must be > 0' in rows[0].errors[0]
    
    def test_parse_with_bytes_input(self):
        """Test parsing bytes input"""
        csv_content = b"""product_reference,quantity
ONT-GPON-V5,10
"""
        parser = SupplierImportParser(csv_content)
        rows, errors = parser.parse()
        
        assert len(rows) == 1
        assert not errors
        assert rows[0].product_reference == 'ONT-GPON-V5'
    
    def test_parse_large_file(self):
        """Test parsing large file (1000 rows)"""
        lines = ['product_reference,quantity']
        for i in range(1000):
            lines.append(f'ONT-GPON-V5,{i % 100 + 1}')
        csv_content = '\n'.join(lines)
        
        parser = SupplierImportParser(csv_content)
        rows, errors = parser.parse()
        
        assert len(rows) == 1000
        assert not errors


# ============================================================================
# VALIDATOR TESTS
# ============================================================================

class TestSupplierImportValidator:
    """Test row validation"""
    
    def test_validate_product_exists(self, app, test_products):
        """Test validation checks product exists"""
        with app.app_context():
            csv_content = """product_reference,quantity
ONT-GPON-V5,10
"""
            parser = SupplierImportParser(csv_content)
            rows, _ = parser.parse()
            
            validator = SupplierImportValidator()
            valid_rows, summary = validator.validate_rows(rows)
            
            assert summary.valid_rows == 1
            assert summary.error_rows == 0
            assert rows[0].product_id == test_products['ONT-GPON-V5'].id
    
    def test_validate_product_not_found(self, app):
        """Test error when product not found"""
        with app.app_context():
            csv_content = """product_reference,quantity
INVALID-PRODUCT,10
"""
            parser = SupplierImportParser(csv_content)
            rows, _ = parser.parse()
            
            validator = SupplierImportValidator()
            valid_rows, summary = validator.validate_rows(rows)
            
            assert summary.valid_rows == 0
            assert summary.error_rows == 1
            assert 'Product not found' in rows[0].errors[0]
    
    def test_validate_product_inactive(self, app, test_products):
        """Test error when product is inactive"""
        with app.app_context():
            csv_content = """product_reference,quantity
INACTIVE-PRODUCT,10
"""
            parser = SupplierImportParser(csv_content)
            rows, _ = parser.parse()
            
            validator = SupplierImportValidator()
            valid_rows, summary = validator.validate_rows(rows)
            
            assert summary.valid_rows == 0
            assert summary.error_rows == 1
            assert 'inactive' in rows[0].errors[0].lower()
    
    def test_validate_serial_unique(self, app, test_products):
        """Test serial number uniqueness"""
        with app.app_context():
            # Create existing serial
            existing_serial = NumeroSerie(
                numero='SN-2024-001-001',
                produit_id=test_products['ONT-GPON-V5'].id,
                statut='EN_MAGASIN',
                cree_par_id=1
            )
            db.session.add(existing_serial)
            db.session.commit()
            
            csv_content = """product_reference,quantity,serial_number
ONT-GPON-V5,1,SN-2024-001-001
"""
            parser = SupplierImportParser(csv_content)
            rows, _ = parser.parse()
            
            validator = SupplierImportValidator()
            valid_rows, summary = validator.validate_rows(rows)
            
            assert summary.valid_rows == 0
            assert summary.error_rows == 1
            assert 'Serial number already exists' in rows[0].errors[0]
    
    def test_validate_duplicate_serial_in_import(self, app, test_products):
        """Test duplicate serials within import"""
        with app.app_context():
            csv_content = """product_reference,quantity,serial_number
ONT-GPON-V5,1,SN-2024-001-001
OLT-FIBER-X2,1,SN-2024-001-001
"""
            parser = SupplierImportParser(csv_content)
            rows, _ = parser.parse()
            
            validator = SupplierImportValidator()
            valid_rows, summary = validator.validate_rows(rows)
            
            assert summary.valid_rows == 1
            assert summary.error_rows == 1
            assert 'Duplicate serial number in import' in rows[1].errors[0]


# ============================================================================
# IMPORTER TESTS
# ============================================================================

class TestSupplierImporter:
    """Test import execution"""
    
    def test_import_single_row(self, app, test_user, test_products, test_emplacement):
        """Test importing single row"""
        with app.app_context():
            csv_content = """product_reference,quantity
ONT-GPON-V5,10
"""
            parser = SupplierImportParser(csv_content)
            rows, _ = parser.parse()
            
            validator = SupplierImportValidator()
            valid_rows, _ = validator.validate_rows(rows)
            
            importer = SupplierImporter(test_user)
            inserted, errors, summary = importer.import_rows(valid_rows)
            
            assert inserted == 1
            assert not errors
            assert summary.inserted_rows == 1
            assert summary.total_quantity == 10
            
            # Verify MouvementStock created
            mouvement = db.session.query(MouvementStock).filter(
                MouvementStock.type_mouvement == 'entree'
            ).first()
            assert mouvement is not None
            assert mouvement.quantite == 10
            assert mouvement.workflow_state == 'EN_ATTENTE'
            assert mouvement.applique_au_stock == False
    
    def test_import_multiple_rows(self, app, test_user, test_products, test_emplacement):
        """Test importing multiple rows"""
        with app.app_context():
            csv_content = """product_reference,quantity
ONT-GPON-V5,10
OLT-FIBER-X2,5
SPLITTER-1X8,20
"""
            parser = SupplierImportParser(csv_content)
            rows, _ = parser.parse()
            
            validator = SupplierImportValidator()
            valid_rows, _ = validator.validate_rows(rows)
            
            importer = SupplierImporter(test_user)
            inserted, errors, summary = importer.import_rows(valid_rows)
            
            assert inserted == 3
            assert not errors
            assert summary.total_quantity == 35
            
            # Verify all mouvements created
            mouvements = db.session.query(MouvementStock).filter(
                MouvementStock.type_mouvement == 'entree'
            ).all()
            assert len(mouvements) >= 3
    
    def test_import_with_serial_numbers(self, app, test_user, test_products, test_emplacement):
        """Test importing with serial numbers"""
        with app.app_context():
            csv_content = """product_reference,quantity,serial_number
ONT-GPON-V5,3,SN-2024-001-001
"""
            parser = SupplierImportParser(csv_content)
            rows, _ = parser.parse()
            
            validator = SupplierImportValidator()
            valid_rows, _ = validator.validate_rows(rows)
            
            importer = SupplierImporter(test_user)
            inserted, errors, summary = importer.import_rows(valid_rows)
            
            assert inserted == 1
            assert not errors
            
            # Verify NumeroSerie created
            serials = db.session.query(NumeroSerie).all()
            assert len(serials) == 3
            serial_numbers = [s.numero for s in serials]
            assert 'SN-2024-001-0001' in serial_numbers
            assert 'SN-2024-001-0002' in serial_numbers
            assert 'SN-2024-001-0003' in serial_numbers


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestSupplierImportIntegration:
    """End-to-end integration tests"""
    
    def test_full_import_pipeline(self, app, test_user, test_products, test_emplacement):
        """Test complete import pipeline"""
        with app.app_context():
            csv_content = """product_reference,quantity,serial_number,unit_price,note
ONT-GPON-V5,10,SN-2024-001-001,45000,Initial stock
OLT-FIBER-X2,5,,250000,Maintenance
SPLITTER-1X8,20,BATCH-2024-001,5000,Batch order
"""
            
            result = process_supplier_import(csv_content, test_user)
            
            assert result['success'] == True
            assert result['summary']['successfully_inserted'] == 3
            assert result['summary']['total_quantity_imported'] == 35
            assert result['summary']['failed_rows'] == 0
    
    def test_partial_success_import(self, app, test_user, test_products, test_emplacement):
        """Test partial success (some rows fail)"""
        with app.app_context():
            # Create existing serial
            existing_serial = NumeroSerie(
                numero='SN-2024-001-001',
                produit_id=test_products['ONT-GPON-V5'].id,
                statut='EN_MAGASIN',
                cree_par_id=test_user.id
            )
            db.session.add(existing_serial)
            db.session.commit()
            
            csv_content = """product_reference,quantity,serial_number
ONT-GPON-V5,10,SN-2024-001-001
OLT-FIBER-X2,5,
SPLITTER-1X8,20,BATCH-2024-001
"""
            
            result = process_supplier_import(csv_content, test_user)
            
            # First row fails (duplicate serial), others succeed
            assert result['success'] == False  # Has errors
            assert result['summary']['successfully_inserted'] == 2
            assert result['summary']['failed_rows'] == 1
            assert len(result['errors']) > 0
    
    def test_invalid_csv_format(self, app, test_user):
        """Test invalid CSV format"""
        with app.app_context():
            csv_content = "invalid csv content without proper headers"
            
            result = process_supplier_import(csv_content, test_user)
            
            assert result['success'] == False
            assert result['phase'] == 'parsing'
            assert len(result['errors']) > 0


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestSupplierImportPerformance:
    """Performance and scale tests"""
    
    def test_parse_1000_rows(self):
        """Test parsing 1000 rows"""
        lines = ['product_reference,quantity']
        for i in range(1000):
            lines.append(f'ONT-GPON-V5,{i % 100 + 1}')
        csv_content = '\n'.join(lines)
        
        parser = SupplierImportParser(csv_content)
        rows, errors = parser.parse()
        
        assert len(rows) == 1000
        assert not errors
    
    def test_validate_1000_rows(self, app, test_products):
        """Test validating 1000 rows"""
        with app.app_context():
            lines = ['product_reference,quantity']
            for i in range(1000):
                # Alternate between products
                product = ['ONT-GPON-V5', 'OLT-FIBER-X2', 'SPLITTER-1X8'][i % 3]
                lines.append(f'{product},{i % 100 + 1}')
            csv_content = '\n'.join(lines)
            
            parser = SupplierImportParser(csv_content)
            rows, _ = parser.parse()
            
            validator = SupplierImportValidator()
            valid_rows, summary = validator.validate_rows(rows)
            
            assert summary.valid_rows == 1000
            assert summary.error_rows == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
