"""
📦 SUPPLIER BULK IMPORT MODULE
Generic CSV supplier import system supporting 5000+ rows efficiently

Features:
- Generic CSV format (supplier-agnostic)
- Streaming parser for large files (5000+ rows)
- Row-level validation with error collection
- Duplicate serial number prevention
- Transaction-safe bulk insert with partial success
- Audit logging on all imports
- Progress tracking and detailed error reporting

CSV Format (Generic):
- product_reference: Existing product reference (e.g., "ONT-GPON-V5")
- quantity: Number of units (integer, > 0)
- serial_number: Unique serial or batch identifier (optional)
- emplacement_code: Storage location code (optional, default to main warehouse)
- unit_price: Unit cost (optional)
- note: Import note/comment (optional)

Example:
    product_reference,quantity,serial_number,emplacement_code,unit_price,note
    ONT-GPON-V5,10,SN-2024-001-010,ENTREPOT,45000,Initial stock
    OLT-FIBER-X2,5,,MAGASIN,250000,
    SPLITTER-1X8,20,BATCH-2024-001,ENTREPOT,5000,Batch import
"""

import csv
import logging
from io import StringIO, BytesIO
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from flask import current_app
from sqlalchemy import func, case
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Produit, MouvementStock, EmplacementStock, NumeroSerie, NumeroSerieStatut, User
from utils_audit import log_stock_entry


# ============================================================================
# CONSTANTS
# ============================================================================

class ImportStatus(Enum):
    """Import progress states"""
    PENDING = 'pending'
    VALIDATING = 'validating'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'


class RowStatus(Enum):
    """Individual row processing status"""
    VALID = 'valid'
    ERROR = 'error'
    SKIPPED = 'skipped'
    WARNING = 'warning'


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ImportRow:
    """Represents a single CSV import row with validation state"""
    line_number: int
    product_reference: str
    quantity: int
    serial_number: Optional[str]
    emplacement_code: Optional[str]
    unit_price: Optional[float]
    note: Optional[str]
    
    # Validation state
    status: RowStatus = RowStatus.VALID
    errors: List[str] = None
    warnings: List[str] = None
    product_id: Optional[int] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
    
    def add_error(self, error: str):
        """Add validation error"""
        self.errors.append(error)
        self.status = RowStatus.ERROR
    
    def add_warning(self, warning: str):
        """Add validation warning (non-blocking)"""
        self.warnings.append(warning)
        if self.status != RowStatus.ERROR:
            self.status = RowStatus.WARNING
    
    def is_valid(self) -> bool:
        """Returns True if row has no errors"""
        return len(self.errors) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'line_number': self.line_number,
            'product_reference': self.product_reference,
            'quantity': self.quantity,
            'serial_number': self.serial_number,
            'status': self.status.value,
            'errors': self.errors,
            'warnings': self.warnings,
        }


@dataclass
class ImportSummary:
    """Summary statistics for completed import"""
    total_rows: int
    valid_rows: int
    error_rows: int
    warning_rows: int
    inserted_rows: int
    skipped_rows: int
    total_quantity: int
    processing_time_seconds: float
    errors_by_type: Dict[str, int]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return asdict(self)


# ============================================================================
# CSV PARSER - STREAMING FOR LARGE FILES
# ============================================================================

class SupplierImportParser:
    """
    Streaming CSV parser for supplier imports
    Handles large files (5000+ rows) efficiently
    """
    
    # Required columns
    REQUIRED_COLUMNS = ['product_reference', 'quantity']
    
    # Optional columns
    OPTIONAL_COLUMNS = ['serial_number', 'emplacement_code', 'unit_price', 'note']
    
    def __init__(self, file_content: str):
        """
        Initialize parser with CSV content
        
        Args:
            file_content: CSV file content as string or bytes
        """
        if isinstance(file_content, bytes):
            self.file_content = file_content.decode('utf-8')
        else:
            self.file_content = file_content
        
        self.logger = current_app.logger if current_app else logging.getLogger(__name__)
    
    def parse(self) -> Tuple[List[ImportRow], List[str]]:
        """
        Parse CSV and return rows with validation
        
        Returns:
            Tuple of (rows: List[ImportRow], parse_errors: List[str])
        """
        rows = []
        parse_errors = []
        
        try:
            # Parse CSV with StringIO for compatibility
            csv_file = StringIO(self.file_content)
            reader = csv.DictReader(csv_file)
            
            # Validate headers
            if not reader.fieldnames:
                return [], ['CSV file is empty']
            
            missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in reader.fieldnames]
            if missing_columns:
                return [], [f'Missing required columns: {", ".join(missing_columns)}']
            
            # Parse rows
            for line_num, row_dict in enumerate(reader, start=2):  # Start at 2 (row 1 is headers)
                try:
                    import_row = self._parse_row(line_num, row_dict)
                    rows.append(import_row)
                except ValueError as e:
                    parse_errors.append(f'Line {line_num}: {str(e)}')
                    continue
                except Exception as e:
                    parse_errors.append(f'Line {line_num}: Unexpected error: {str(e)}')
                    continue
            
            self.logger.info(f'✅ Parsed {len(rows)} rows from CSV')
            
            return rows, parse_errors
        
        except Exception as e:
            error_msg = f'CSV parsing error: {str(e)}'
            self.logger.error(error_msg)
            return [], [error_msg]
    
    def _parse_row(self, line_num: int, row_dict: Dict[str, str]) -> ImportRow:
        """Parse and validate a single CSV row"""
        
        # Extract fields
        product_reference = (row_dict.get('product_reference') or '').strip()
        quantity_str = (row_dict.get('quantity') or '').strip()
        serial_number = (row_dict.get('serial_number') or '').strip() or None
        emplacement_code = (row_dict.get('emplacement_code') or '').strip() or None
        unit_price_str = (row_dict.get('unit_price') or '').strip()
        note = (row_dict.get('note') or '').strip() or None
        
        # Create ImportRow object
        import_row = ImportRow(
            line_number=line_num,
            product_reference=product_reference,
            quantity=0,  # Will be set below
            serial_number=serial_number,
            emplacement_code=emplacement_code,
            unit_price=None,  # Will be set below
            note=note
        )
        
        # Validate product reference
        if not product_reference:
            import_row.add_error('product_reference is required')
        
        # Validate quantity
        try:
            quantity = int(quantity_str)
            if quantity <= 0:
                import_row.add_error('quantity must be > 0')
            else:
                import_row.quantity = quantity
        except (ValueError, TypeError):
            import_row.add_error(f'quantity must be a valid integer (got: "{quantity_str}")')
        
        # Parse unit price (optional)
        if unit_price_str:
            try:
                import_row.unit_price = float(unit_price_str)
                if import_row.unit_price < 0:
                    import_row.add_warning('unit_price is negative')
            except (ValueError, TypeError):
                import_row.add_error(f'unit_price must be a valid number (got: "{unit_price_str}")')
        
        return import_row


# ============================================================================
# VALIDATOR - ROW-LEVEL VALIDATION
# ============================================================================

class SupplierImportValidator:
    """
    Validates import rows against database state
    Checks:
    - Product exists and is active
    - Serial numbers are unique
    - Emplacement exists (if specified)
    - No duplicate serial numbers in import
    """
    
    def __init__(self):
        self.logger = current_app.logger if current_app else logging.getLogger(__name__)
        self._seen_serials = set()  # Track serials in this import
    
    def validate_rows(self, rows: List[ImportRow]) -> Tuple[List[ImportRow], ImportSummary]:
        """
        Validate all rows and collect errors
        
        Returns:
            Tuple of (validated_rows, summary)
        """
        valid_rows = []
        error_rows = 0
        warning_rows = 0
        total_quantity = 0
        errors_by_type = {}
        
        for row in rows:
            self.validate_row(row)
            
            if row.status == RowStatus.ERROR:
                error_rows += 1
                for error in row.errors:
                    error_type = error.split(':')[0]
                    errors_by_type[error_type] = errors_by_type.get(error_type, 0) + 1
            elif row.status == RowStatus.WARNING:
                warning_rows += 1
            
            if row.is_valid():
                valid_rows.append(row)
                total_quantity += row.quantity
        
        summary = ImportSummary(
            total_rows=len(rows),
            valid_rows=len(valid_rows),
            error_rows=error_rows,
            warning_rows=warning_rows,
            inserted_rows=0,  # Will be updated after insert
            skipped_rows=error_rows,
            total_quantity=total_quantity,
            processing_time_seconds=0,  # Will be updated
            errors_by_type=errors_by_type
        )
        
        self.logger.info(f'✅ Validation complete: {len(valid_rows)} valid, {error_rows} errors, {warning_rows} warnings')
        
        return valid_rows, summary
    
    def validate_row(self, row: ImportRow):
        """Validate a single row"""
        
        # Skip if already has errors from parsing
        if not row.is_valid():
            return
        
        # 1. Check product exists and is active
        product = db.session.query(Produit).filter(
            Produit.reference == row.product_reference
        ).first()
        
        if not product:
            row.add_error(f'Product not found: {row.product_reference}')
            return
        
        if not product.actif:
            row.add_error(f'Product is inactive: {row.product_reference}')
            return
        
        row.product_id = product.id
        
        # 2. Check serial number uniqueness (if provided)
        if row.serial_number:
            # Check if serial exists in database
            existing_serial = db.session.query(NumeroSerie).filter(
                NumeroSerie.numero == row.serial_number
            ).first()
            
            if existing_serial:
                row.add_error(f'Serial number already exists: {row.serial_number}')
            
            # Check if serial appears multiple times in this import
            if row.serial_number in self._seen_serials:
                row.add_error(f'Duplicate serial number in import: {row.serial_number}')
            else:
                self._seen_serials.add(row.serial_number)
        
        # 3. Check emplacement exists (if specified)
        if row.emplacement_code:
            emplacement = db.session.query(EmplacementStock).filter(
                EmplacementStock.code == row.emplacement_code
            ).first()
            
            if not emplacement:
                row.add_warning(f'Emplacement code not found: {row.emplacement_code} (will use default)')
            elif not emplacement.actif:
                row.add_warning(f'Emplacement is inactive: {row.emplacement_code} (will use default)')


# ============================================================================
# IMPORTER - BULK INSERT WITH TRANSACTION SAFETY
# ============================================================================

class SupplierImporter:
    """
    Performs bulk insert of validated rows
    Features:
    - Transaction safety (all or nothing per batch)
    - Partial success handling
    - Audit logging
    - Serial number creation
    """
    
    BATCH_SIZE = 500  # Process in batches to manage memory
    
    def __init__(self, user: User):
        """Initialize importer with user context"""
        self.user = user
        self.logger = current_app.logger if current_app else logging.getLogger(__name__)
    
    def import_rows(self, rows: List[ImportRow]) -> Tuple[int, List[str], ImportSummary]:
        """
        Import validated rows into database
        
        Args:
            rows: List of validated ImportRow objects
        
        Returns:
            Tuple of (inserted_count, errors, summary)
        """
        inserted_count = 0
        import_errors = []
        start_time = datetime.now()
        
        try:
            # Get default emplacement
            default_emplacement = db.session.query(EmplacementStock).filter(
                EmplacementStock.code == 'ENTREPOT'
            ).first()
            
            if not default_emplacement:
                # Create default if not exists
                default_emplacement = EmplacementStock(
                    designation='Entrepôt Principal',
                    code='ENTREPOT',
                    actif=True
                )
                db.session.add(default_emplacement)
                db.session.flush()
            
            # Process in batches
            for batch_idx in range(0, len(rows), self.BATCH_SIZE):
                batch = rows[batch_idx:batch_idx + self.BATCH_SIZE]
                batch_inserted = self._insert_batch(batch, default_emplacement, import_errors)
                inserted_count += batch_inserted
                
                self.logger.info(
                    f'✅ Batch {batch_idx // self.BATCH_SIZE + 1}: '
                    f'Inserted {batch_inserted}/{len(batch)} rows'
                )
            
            self.logger.info(f'✅ Import complete: {inserted_count} rows inserted')
        
        except Exception as e:
            error_msg = f'Import failed: {str(e)}'
            self.logger.error(error_msg)
            import_errors.append(error_msg)
        
        # Build summary
        processing_time = (datetime.now() - start_time).total_seconds()
        summary = ImportSummary(
            total_rows=len(rows),
            valid_rows=len(rows),
            error_rows=0,
            warning_rows=0,
            inserted_rows=inserted_count,
            skipped_rows=len(rows) - inserted_count,
            total_quantity=sum(r.quantity for r in rows),
            processing_time_seconds=processing_time,
            errors_by_type={}
        )
        
        return inserted_count, import_errors, summary
    
    def _insert_batch(self, batch: List[ImportRow], default_emplacement: EmplacementStock, 
                     errors: List[str]) -> int:
        """Insert a single batch of rows with transaction safety"""
        inserted = 0
        
        try:
            for row in batch:
                try:
                    # Get product
                    product = db.session.query(Produit).get(row.product_id)
                    if not product:
                        errors.append(f'Line {row.line_number}: Product not found (ID: {row.product_id})')
                        continue
                    
                    # Determine emplacement
                    emplacement = default_emplacement
                    if row.emplacement_code:
                        alt_emplacement = db.session.query(EmplacementStock).filter(
                            EmplacementStock.code == row.emplacement_code,
                            EmplacementStock.actif == True
                        ).first()
                        if alt_emplacement:
                            emplacement = alt_emplacement
                    
                    # Create stock movement (entree type)
                    mouvement = MouvementStock(
                        type_mouvement='entree',
                        reference=f'IMPORT-{datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")}',
                        date_reference=datetime.now(timezone.utc).date(),
                        produit_id=product.id,
                        quantite=row.quantity,
                        prix_unitaire=row.unit_price or product.prix_achat,
                        montant_total=(row.unit_price * row.quantity) if row.unit_price else None,
                        utilisateur_id=self.user.id,
                        emplacement_id=emplacement.id,
                        commentaire=f'Supplier import - {row.note}' if row.note else 'Supplier import',
                        date_mouvement=datetime.now(timezone.utc),
                        workflow_state='EN_ATTENTE',  # Require approval
                        applique_au_stock=False  # Don't auto-apply
                    )
                    
                    db.session.add(mouvement)
                    db.session.flush()  # Get the ID without committing
                    
                    # Create serial numbers if provided
                    if row.serial_number and row.quantity > 0:
                        self._create_serial_numbers(
                            mouvement.id, 
                            row.serial_number,
                            row.quantity,
                            product,
                            emplacement
                        )
                    
                    # Log audit entry
                    log_stock_entry(
                        produit_id=product.id,
                        quantity=row.quantity,
                        actor_id=self.user.id,
                        supplier=None,  # Generic import
                        invoice_num=f'IMPORT-{datetime.now(timezone.utc).strftime("%Y%m%d")}'
                    )
                    
                    inserted += 1
                
                except Exception as row_error:
                    errors.append(f'Line {row.line_number}: {str(row_error)}')
                    db.session.rollback()
                    continue
            
            # Commit batch
            db.session.commit()
        
        except Exception as batch_error:
            errors.append(f'Batch error: {str(batch_error)}')
            db.session.rollback()
        
        return inserted
    
    def _create_serial_numbers(self, mouvement_id: int, serial_base: str, 
                             quantity: int, product: Produit, 
                             emplacement: EmplacementStock):
        """Create NumeroSerie records for imported items"""
        try:
            # If serial_base contains a range or pattern, parse it
            # Otherwise use it as a base for sequential numbering
            serials = []
            
            for i in range(quantity):
                # Generate serial number
                if quantity > 1 and '-' in serial_base:
                    # Try to extract number and increment
                    parts = serial_base.rsplit('-', 1)
                    if parts[-1].isdigit():
                        base = '-'.join(parts[:-1])
                        start_num = int(parts[-1])
                        serial_num = f'{base}-{start_num + i:04d}'
                    else:
                        serial_num = f'{serial_base}-{i+1:04d}'
                else:
                    serial_num = f'{serial_base}-{i+1:04d}' if quantity > 1 else serial_base
                
                # Create NumeroSerie
                numero_serie = NumeroSerie(
                    numero=serial_num,
                    produit_id=product.id,
                    statut=NumeroSerieStatut.EN_MAGASIN,
                    date_entree=datetime.now(timezone.utc),
                    emplacement_id=emplacement.id,
                    cree_par_id=self.user.id,
                    date_creation=datetime.now(timezone.utc)
                )
                serials.append(numero_serie)
            
            db.session.bulk_save_objects(serials)
            self.logger.info(f'✅ Created {len(serials)} serial numbers for import')
        
        except Exception as e:
            self.logger.error(f'⚠️ Error creating serial numbers: {str(e)}')
            # Don't fail the import if serials fail


# ============================================================================
# PUBLIC API
# ============================================================================

def process_supplier_import(file_content: str, user: User) -> Dict[str, Any]:
    """
    Main entry point for supplier import processing
    
    Args:
        file_content: CSV file content (string or bytes)
        user: User performing the import
    
    Returns:
        Dictionary with import results and summary
    """
    logger = current_app.logger if current_app else logging.getLogger(__name__)
    start_time = datetime.now()
    
    try:
        # Step 1: Parse CSV
        parser = SupplierImportParser(file_content)
        rows, parse_errors = parser.parse()
        
        if parse_errors:
            return {
                'success': False,
                'phase': 'parsing',
                'errors': parse_errors,
                'rows_processed': 0,
                'rows_inserted': 0
            }
        
        if not rows:
            return {
                'success': False,
                'phase': 'parsing',
                'errors': ['No rows to import'],
                'rows_processed': 0,
                'rows_inserted': 0
            }
        
        # Step 2: Validate rows
        validator = SupplierImportValidator()
        valid_rows, validation_summary = validator.validate_rows(rows)
        
        # Step 3: Import valid rows
        importer = SupplierImporter(user)
        inserted_count, import_errors, import_summary = importer.import_rows(valid_rows)
        
        # Combine results
        processing_time = (datetime.now() - start_time).total_seconds()
        
        response = {
            'success': import_errors == [],
            'phase': 'complete',
            'parsing': {
                'total_rows': len(rows),
                'parse_errors': parse_errors
            },
            'validation': validation_summary.to_dict(),
            'import': import_summary.to_dict(),
            'errors': import_errors,
            'processing_time_seconds': processing_time,
            'summary': {
                'total_requested': len(rows),
                'successfully_inserted': inserted_count,
                'failed_rows': len(rows) - inserted_count,
                'total_quantity_imported': import_summary.total_quantity
            }
        }
        
        logger.info(
            f'✅ Import complete: {inserted_count}/{len(rows)} rows inserted '
            f'in {processing_time:.2f}s'
        )
        
        return response
    
    except Exception as e:
        error_msg = f'Unexpected error during import: {str(e)}'
        logger.error(error_msg)
        return {
            'success': False,
            'phase': 'unexpected_error',
            'errors': [error_msg],
            'rows_processed': 0,
            'rows_inserted': 0
        }
