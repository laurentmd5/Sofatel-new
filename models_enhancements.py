# models_enhancements.py
"""
ENHANCED DATA MODELS: Stock-HR-Interventions Integration
Implements mandatory user attribution, intervention references, and complete audit trails

Business Rules:
- ✅ Every MouvementStock sortie MUST have intervention_id
- ✅ Every consumption action MUST be audited
- ✅ Serial numbers MUST be linked to interventions
- ✅ Intervention closure MUST validate stock checkpoint
"""

from extensions import db
from datetime import datetime
from sqlalchemy import func
from models import utcnow
import enum


# ============================================================================
# ENUMS
# ============================================================================

class NumeroSerieStatut(enum.Enum):
    """Status progression for serialized items"""
    EN_MAGASIN = 'en_magasin'
    ALLOUE_ZONE = 'alloue_zone'
    ALLOUE_TECHNICIEN = 'alloue_technicien'
    INSTALLEE = 'installee'
    RETOURNEE = 'retournee'
    REBUT = 'rebut'


# ============================================================================
# NEW MODELS: Audit & Traceability
# ============================================================================

class NumeroSerieTransition(db.Model):
    """
    AUDIT TRAIL for serial number state changes
    
    Tracks: EVERY transition of serial numbers
    Includes: WHO changed it, WHEN, WHY, and CONTEXT (which intervention)
    
    Purpose: Complete lifecycle visibility of hardware components
    """
    __tablename__ = 'numero_serie_transition'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # WHAT changed
    numero_serie_id = db.Column(
        db.Integer,
        db.ForeignKey('numero_serie.id'),
        nullable=False,
        index=True
    )
    numero_serie = db.relationship(
        'NumeroSerie',
        foreign_keys=[numero_serie_id],
        backref=db.backref('transitions_history', lazy=True, cascade='all, delete-orphan')
    )
    
    # STATE TRANSITION
    from_status = db.Column(db.String(50))
    to_status = db.Column(db.String(50), nullable=False)
    reason = db.Column(db.String(255))
    
    # WHO changed it (MANDATORY: accountability)
    changed_by_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )
    changed_by = db.relationship(
        'User',
        foreign_keys=[changed_by_id],
        backref=db.backref('serial_transitions_made', lazy=True)
    )
    
    # WHEN (UTC, immutable)
    timestamp = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)
    
    # CONTEXT: Which intervention triggered this?
    intervention_id = db.Column(
        db.Integer,
        db.ForeignKey('intervention.id'),
        nullable=True
    )
    intervention = db.relationship(
        'Intervention',
        foreign_keys=[intervention_id],
        backref=db.backref('serial_transitions', lazy=True)
    )
    
    # RELATED ACTION: Which stock movement triggered this?
    mouvement_stock_id = db.Column(
        db.Integer,
        db.ForeignKey('mouvement_stock.id'),
        nullable=True
    )
    mouvement_stock = db.relationship(
        'MouvementStock',
        foreign_keys=[mouvement_stock_id],
        backref=db.backref('serial_transitions_linked', lazy=True)
    )
    
    def __repr__(self):
        return f'<NumeroSerieTransition {self.numero_serie_id}: {self.from_status}→{self.to_status} @{self.timestamp}>'


class InterventionStockCheckpoint(db.Model):
    """
    CLOSURE VALIDATION: Stock consistency check before intervention closes
    
    When: Intervention transitions to VALIDATED/CLOSED state
    Verify: All reserved stock is accounted for (consumed + returned + damaged + missing)
    
    Purpose: Prevent closing interventions with unaccounted stock
    """
    __tablename__ = 'intervention_stock_checkpoint'
    
    # Status constants
    CHECKPOINT_PENDING = 'pending'
    CHECKPOINT_VALIDATED = 'validated'
    CHECKPOINT_FAILED = 'failed'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # WHICH INTERVENTION
    intervention_id = db.Column(
        db.Integer,
        db.ForeignKey('intervention.id'),
        unique=True,
        nullable=False
    )
    intervention = db.relationship(
        'Intervention',
        foreign_keys=[intervention_id],
        backref=db.backref('stock_checkpoint', uselist=False)
    )
    
    # CHECKPOINT STATE
    status = db.Column(
        db.String(20),
        default=CHECKPOINT_PENDING,
        nullable=False
    )
    
    # STOCK RECONCILIATION (accounts for all reserved items)
    reserved_count = db.Column(db.Integer, default=0)        # Total reserved at start
    consumed_count = db.Column(db.Integer, default=0)        # Actually used
    returned_count = db.Column(db.Integer, default=0)        # Returned to stock
    damaged_count = db.Column(db.Integer, default=0)         # Damaged/scrapped
    missing_count = db.Column(db.Integer, default=0)         # Not accounted for
    
    # WHO validated
    validated_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    validated_by = db.relationship(
        'User',
        foreign_keys=[validated_by_id],
        backref=db.backref('interventions_stock_validated', lazy=True)
    )
    validated_at = db.Column(db.DateTime, nullable=True)
    
    # DETAILS
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<InterventionStockCheckpoint intervention={self.intervention_id} status={self.status}>'
    
    def calculate_status(self):
        """
        VERIFY: All reserved items accounted for
        Returns: VALIDATED if accounts match, FAILED if missing items
        """
        accounted = (self.consumed_count + 
                    self.returned_count + 
                    self.damaged_count)
        
        if accounted >= self.reserved_count:
            return self.CHECKPOINT_VALIDATED
        return self.CHECKPOINT_FAILED
    
    def get_reconciliation_report(self):
        """Generate readable reconciliation summary"""
        return {
            'reserved': self.reserved_count,
            'accounted': self.consumed_count + self.returned_count + self.damaged_count,
            'consumed': self.consumed_count,
            'returned': self.returned_count,
            'damaged': self.damaged_count,
            'missing': max(0, self.reserved_count - 
                          (self.consumed_count + self.returned_count + self.damaged_count)),
            'status': self.status,
            'validated': 'Yes' if self.status == self.CHECKPOINT_VALIDATED else 'No'
        }


class StockConsumptionAudit(db.Model):
    """
    ACCOUNTABILITY TRAIL: Complete record of stock consumption
    
    Per-action audit: WHO did WHAT, WHEN, WHY, FOR WHOM
    Links: Technician, Intervention, User action, Serial (if applicable)
    
    Purpose: Complete audit trail for management, compliance, and accountability
    """
    __tablename__ = 'stock_consumption_audit'
    
    # Action types (business events)
    ACTION_RESERVE = 'reserve'
    ACTION_CONSUME = 'consume'
    ACTION_RETURN = 'return'
    ACTION_DAMAGE = 'damage'
    ACTION_REJECT = 'reject'
    ACTION_ADJUST = 'adjust'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # === WHAT MOVED ===
    mouvement_stock_id = db.Column(
        db.Integer,
        db.ForeignKey('mouvement_stock.id'),
        nullable=False
    )
    mouvement_stock = db.relationship(
        'MouvementStock',
        foreign_keys=[mouvement_stock_id],
        backref=db.backref('audit_trail', lazy=True, cascade='all, delete-orphan')
    )
    
    # === WHICH INTERVENTION ===
    intervention_id = db.Column(
        db.Integer,
        db.ForeignKey('intervention.id'),
        nullable=False,
        index=True
    )
    intervention = db.relationship(
        'Intervention',
        foreign_keys=[intervention_id],
        backref=db.backref('stock_audit_trail', lazy=True)
    )
    
    # === WHO DID IT (the actor) ===
    actor_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )
    actor = db.relationship(
        'User',
        foreign_keys=[actor_id],
        backref=db.backref('stock_actions_performed', lazy=True)
    )
    
    # === WHICH TECHNICIAN BENEFITS (if applicable) ===
    technicien_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=True
    )
    technicien = db.relationship(
        'User',
        foreign_keys=[technicien_id],
        backref=db.backref('stock_consumed_for_me', lazy=True)
    )
    
    # === BUSINESS ACTION ===
    action = db.Column(
        db.Enum(
            ACTION_RESERVE,
            ACTION_CONSUME,
            ACTION_RETURN,
            ACTION_DAMAGE,
            ACTION_REJECT,
            ACTION_ADJUST
        ),
        nullable=False
    )
    
    # === WHEN (UTC, immutable) ===
    timestamp = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)
    
    # === WHY (justification) ===
    justification = db.Column(db.Text)
    
    # === OPTIONAL: Serial if hardware involved ===
    numero_serie_id = db.Column(
        db.Integer,
        db.ForeignKey('numero_serie.id'),
        nullable=True
    )
    numero_serie = db.relationship(
        'NumeroSerie',
        foreign_keys=[numero_serie_id],
        backref=db.backref('consumption_audit', lazy=True)
    )
    
    def __repr__(self):
        return f'<StockConsumptionAudit {self.action} by {self.actor_id} @{self.timestamp}>'
    
    @staticmethod
    def create_from_movement(mouvement, actor_id, action, justification=''):
        """
        FACTORY: Create audit entry from stock movement
        """
        audit = StockConsumptionAudit(
            mouvement_stock_id=mouvement.id,
            intervention_id=mouvement.intervention_id,
            actor_id=actor_id,
            technicien_id=mouvement.utilisateur_id,
            action=action,
            justification=justification,
            numero_serie_id=None,
            timestamp=datetime.utcnow()
        )
        return audit


# ============================================================================
# MODEL ENHANCEMENTS: Add to existing models
# ============================================================================

def enhance_mouvement_stock():
    """
    ENHANCEMENTS to MouvementStock model:
    
    ADD TO models.py MouvementStock class:
    """
    
    code = '''
    # ===== MANDATORY INTERVENTION LINK (NEW) =====
    # For sortie/retour/rebut: MANDATORY
    # For entree: optional (from supplier)
    intervention_id = db.Column(
        db.Integer,
        db.ForeignKey('intervention.id'),
        nullable=True,  # Allow NULL for entree, enforce later for sortie
        index=True
    )
    intervention = db.relationship(
        'Intervention',
        foreign_keys=[intervention_id],
        backref=db.backref('mouvements_stock_all', lazy=True)
    )
    
    # ===== REASON FOR CONSUMPTION (NEW) =====
    raison_sortie = db.Column(
        db.Enum('intervention', 'retour', 'rebut', 'inventaire', 'autre'),
        nullable=True
    )
    
    # ===== AUDIT TRAIL (NEW) =====
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    
    # ===== VALIDATION BEFORE INSERT =====
    def validate_for_intervention(self):
        """
        CRITICAL: Ensure movement is properly linked if type is sortie
        Called before INSERT
        """
        if self.type_mouvement in ['sortie', 'retour', 'rebut']:
            if not self.intervention_id:
                raise ValueError(
                    f"❌ {self.type_mouvement.upper()} de stock doit être liée à une intervention.\\n"
                    f"Produit: {self.produit_relation.nom if self.produit_relation else 'N/A'}\\n"
                    f"Quantité: {self.quantite}"
                )
        
        if self.type_mouvement == 'sortie':
            if not self.raison_sortie:
                raise ValueError("❌ Raison de sortie est obligatoire")
        
        if not self.utilisateur_id:
            raise ValueError("❌ L'utilisateur est obligatoire pour tout mouvement")
    
    @property
    def get_auditeurs(self):
        """Get list of audit entries for this movement"""
        return StockConsumptionAudit.query.filter_by(
            mouvement_stock_id=self.id
        ).order_by(StockConsumptionAudit.timestamp).all()
    '''
    
    return code


def enhance_numero_serie():
    """
    ENHANCEMENTS to NumeroSerie model:
    
    ADD TO models.py NumeroSerie class:
    """
    
    code = '''
    # ===== MANDATORY INTERVENTION LINK (NEW) =====
    # Link to intervention where this serial is being used
    intervention_id = db.Column(
        db.Integer,
        db.ForeignKey('intervention.id'),
        nullable=True
    )
    intervention = db.relationship(
        'Intervention',
        foreign_keys=[intervention_id],
        backref=db.backref('numeros_serie_utilises', lazy=True)
    )
    
    # ===== EXISTING: Keep these! =====
    # technicien_id ✅ Already exists - who has it
    # date_affectation_tech ✅ Already exists - when allocated
    # statut ✅ Already exists - current state
    
    # ===== TRANSITION HISTORY (NEW) =====
    # Already defined as relationship in NumeroSerieTransition model
    # transitions_history = db.relationship('NumeroSerieTransition', ...)
    
    # ===== METHODS =====
    def get_usage_history(self):
        """Complete usage history with technician and intervention details"""
        return db.session.query(NumeroSerieTransition).filter_by(
            numero_serie_id=self.id
        ).order_by(NumeroSerieTransition.timestamp).all()
    
    def get_lifecycle_summary(self):
        """Summary: creation → technician → intervention → final state"""
        return {
            'numero': self.numero,
            'product': self.produit.nom if self.produit else 'N/A',
            'current_status': self.get_statut_display(),
            'current_technician': self.technicien.prenom + ' ' + self.technicien.nom if self.technicien else None,
            'current_intervention': self.intervention_id,
            'date_received': self.date_entree.isoformat() if self.date_entree else None,
            'date_allocated': self.date_affectation_tech.isoformat() if self.date_affectation_tech else None,
            'date_installed': self.date_installation.isoformat() if self.date_installation else None,
            'transitions_count': len(self.transitions_history)
        }
    '''
    
    return code


def enhance_intervention():
    """
    ENHANCEMENTS to Intervention model:
    
    ADD TO models.py Intervention class:
    """
    
    code = '''
    # ===== STOCK CHECKPOINT (NEW) =====
    # Already defined as relationship in InterventionStockCheckpoint model
    # stock_checkpoint = db.relationship('InterventionStockCheckpoint', ...)
    
    # ===== VALIDATION BEFORE CLOSURE =====
    def validate_stock_before_closure(self):
        """
        CRITICAL: Before closing intervention, validate stock consistency
        
        Ensures:
        - All reserved stock is accounted for
        - All serials in final state
        - No missing items
        """
        
        # Get or create checkpoint
        checkpoint = self.stock_checkpoint
        if not checkpoint:
            checkpoint = InterventionStockCheckpoint(intervention_id=self.id)
            db.session.add(checkpoint)
        
        # COUNT: Reservations
        reservations = ReservationPiece.query.filter_by(
            intervention_id=self.id
        ).all()
        checkpoint.reserved_count = len(reservations)
        
        # COUNT: Consumptions (sortie)
        mouvements = MouvementStock.query.filter_by(
            intervention_id=self.id,
            type_mouvement='sortie'
        ).all()
        checkpoint.consumed_count = len(mouvements)
        
        # COUNT: Returns (retour)
        returns = MouvementStock.query.filter_by(
            intervention_id=self.id,
            type_mouvement='retour'
        ).all()
        checkpoint.returned_count = len(returns)
        
        # COUNT: Damaged (rebut)
        damaged = MouvementStock.query.filter(
            MouvementStock.intervention_id == self.id,
            MouvementStock.raison_sortie == 'rebut'
        ).all()
        checkpoint.damaged_count = len(damaged)
        
        # CALCULATE: Missing
        checkpoint.missing_count = max(
            0,
            checkpoint.reserved_count - 
            (checkpoint.consumed_count + 
             checkpoint.returned_count + 
             checkpoint.damaged_count)
        )
        
        # VALIDATE: Serial numbers
        serials_used = NumeroSerie.query.filter_by(
            intervention_id=self.id
        ).all()
        
        for serial in serials_used:
            if serial.statut not in [
                NumeroSerieStatut.INSTALLEE,
                NumeroSerieStatut.RETOURNEE,
                NumeroSerieStatut.REBUT
            ]:
                raise ValueError(
                    f"❌ Série {serial.numero} n'est pas en état final.\\n"
                    f"État actuel: {serial.get_statut_display()}\\n"
                    f"Impossible de fermer intervention.\\n"
                    f"Veuillez finaliser l'état de la série."
                )
        
        # DETERMINE: Overall status
        checkpoint.status = checkpoint.calculate_status()
        
        if checkpoint.status == InterventionStockCheckpoint.CHECKPOINT_FAILED:
            report = checkpoint.get_reconciliation_report()
            raise ValueError(
                f"❌ VÉRIFICATION STOCK ÉCHOUÉE:\\n\\n"
                f"Réservées:   {report['reserved']}\\n"
                f"Consommées:  {report['consumed']}\\n"
                f"Retournées:  {report['returned']}\\n"
                f"Endommagées: {report['damaged']}\\n"
                f"Manquantes:  {report['missing']}\\n\\n"
                f"⚠️ Veuillez documenter les items manquants avant de fermer."
            )
        
        checkpoint.validated_at = datetime.utcnow()
        checkpoint.validated_by_id = current_user.id if 'current_user' in globals() else None
        
        db.session.commit()
        return checkpoint
    
    def can_close(self):
        """Check if intervention can transition to closed state"""
        try:
            self.validate_stock_before_closure()
            return True, "✅ Vérification stock réussie"
        except ValueError as e:
            return False, str(e)
    '''
    
    return code


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

class StockValidationRules:
    """
    Centralized business rules for stock-HR-intervention integration
    """
    
    @staticmethod
    def validate_mouvement_creation(mouvement_dict):
        """
        Validate mouvement creation parameters
        Raises: ValueError with clear message if validation fails
        """
        
        # Rule 1: utilisateur_id is MANDATORY
        if not mouvement_dict.get('utilisateur_id'):
            raise ValueError(
                "❌ ERREUR: utilisateur_id obligatoire pour tout mouvement"
            )
        
        # Rule 2: type_mouvement is MANDATORY
        if not mouvement_dict.get('type_mouvement'):
            raise ValueError(
                "❌ ERREUR: type_mouvement obligatoire (entree/sortie/inventaire/ajustement/retour)"
            )
        
        mouvement_type = mouvement_dict['type_mouvement']
        
        # Rule 3: For SORTIE/RETOUR/REBUT: intervention_id is MANDATORY
        if mouvement_type in ['sortie', 'retour', 'rebut']:
            if not mouvement_dict.get('intervention_id'):
                raise ValueError(
                    f"❌ ERREUR: {mouvement_type.upper()} doit avoir une intervention\\n"
                    f"Intervention ID manquante"
                )
        
        # Rule 4: For SORTIE: raison_sortie is MANDATORY
        if mouvement_type == 'sortie':
            if not mouvement_dict.get('raison_sortie'):
                raise ValueError(
                    "❌ ERREUR: Raison de sortie obligatoire\\n"
                    "Valeurs: intervention, retour, rebut, inventaire, autre"
                )
        
        # Rule 5: For ENTREE: reference is MANDATORY
        if mouvement_type == 'entree':
            if not mouvement_dict.get('reference'):
                raise ValueError(
                    "❌ ERREUR: Entrée doit avoir référence (BL, facture)"
                )
        
        # Rule 6: quantite is MANDATORY and > 0
        quantite = mouvement_dict.get('quantite', 0)
        if not quantite or quantite <= 0:
            raise ValueError(
                "❌ ERREUR: Quantité obligatoire et doit être > 0"
            )
        
        return True  # All validations passed
    
    @staticmethod
    def validate_serial_allocation(serial_dict):
        """
        Validate serial number allocation parameters
        """
        
        # Serial must be allocated FOR AN INTERVENTION
        if not serial_dict.get('intervention_id'):
            raise ValueError(
                "❌ Série doit être allouée pour une intervention\\n"
                "Intervention ID manquée"
            )
        
        # Technician is MANDATORY
        if not serial_dict.get('technicien_id'):
            raise ValueError(
                "❌ Technician obligatoire pour allocation de série"
            )
        
        return True


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'NumeroSerieTransition',
    'InterventionStockCheckpoint',
    'StockConsumptionAudit',
    'StockValidationRules',
    'enhance_mouvement_stock',
    'enhance_numero_serie',
    'enhance_intervention',
]

