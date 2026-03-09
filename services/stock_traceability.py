# services/stock_traceability.py
"""
STOCK TRACEABILITY SERVICE LAYER
Central service for stock-user-intervention integration

Responsibilities:
- Enforce mandatory fields & business rules
- Create movements WITH automatic audit trail
- Generate traceability reports
- Provide accountability data for management

Usage:
    from services.stock_traceability import StockTraceabilityService
    
    # Create consumption with full audit
    mouvement, audit = StockTraceabilityService.create_movement_with_audit(
        mouvement_type='sortie',
        produit_id=123,
        quantite=2,
        intervention_id=456,
        utilisateur_id=789,
        raison_sortie='intervention',
        justification='Used for fiber installation'
    )
"""

from extensions import db
from models import (
    MouvementStock, ReservationPiece, NumeroSerie, Intervention,
    User, Produit
)
from models_enhancements import (
    NumeroSerieTransition, InterventionStockCheckpoint,
    StockConsumptionAudit, StockValidationRules, NumeroSerieStatut
)
from datetime import datetime
from flask import current_app
import logging

logger = logging.getLogger(__name__)


class StockTraceabilityService:
    """
    Service for complete stock-HR-intervention traceability
    
    ✅ Ensures:
    - Every movement has responsible user
    - Every sortie linked to intervention
    - Every action audited
    - Accountability trail for management
    """
    
    # =========================================================================
    # CORE: Create Movement with Audit Trail
    # =========================================================================
    
    @staticmethod
    def create_movement_with_audit(
        mouvement_type,
        produit_id,
        quantite,
        intervention_id=None,
        utilisateur_id=None,
        raison_sortie=None,
        reference=None,
        prix_unitaire=None,
        justification='',
        numero_serie_id=None,
        emplacement_id=None,
        commentaire=None
    ):
        """
        CREATE stock movement with MANDATORY audit trail
        
        ✅ Validates all business rules
        ✅ Creates movement + audit entry automatically
        ✅ Links serial if applicable
        ✅ Raises ValueError if validation fails
        
        Args:
            mouvement_type (str): entree|sortie|inventaire|ajustement|retour
            produit_id (int): Product ID
            quantite (float): Quantity > 0
            intervention_id (int): MANDATORY for sortie/retour/rebut
            utilisateur_id (int): MANDATORY - who performs action
            raison_sortie (str): MANDATORY for sortie
            reference (str): MANDATORY for entree
            prix_unitaire (float): Unit price
            justification (str): Why this action
            numero_serie_id (int): If hardware with serial
            emplacement_id (int): Storage location
            commentaire (str): Additional notes
        
        Returns:
            tuple: (mouvement, audit_entry)
        
        Raises:
            ValueError: If any business rule violated
        
        Example:
            mouvement, audit = StockTraceabilityService.create_movement_with_audit(
                mouvement_type='sortie',
                produit_id=123,
                quantite=1,
                intervention_id=456,
                utilisateur_id=789,
                raison_sortie='intervention',
                numero_serie_id=999,
                justification='Installed ONT at client'
            )
        """
        
        try:
            # Build validation dict
            mouvement_dict = {
                'type_mouvement': mouvement_type,
                'produit_id': produit_id,
                'quantite': quantite,
                'intervention_id': intervention_id,
                'utilisateur_id': utilisateur_id,
                'raison_sortie': raison_sortie,
                'reference': reference
            }
            
            # ✅ VALIDATE all business rules
            StockValidationRules.validate_mouvement_creation(mouvement_dict)
            
            # ✅ Verify context (intervention, user, product exist)
            product = Produit.query.get(produit_id)
            if not product:
                raise ValueError(f"❌ Produit {produit_id} n'existe pas")
            
            user = User.query.get(utilisateur_id)
            if not user:
                raise ValueError(f"❌ Utilisateur {utilisateur_id} n'existe pas")
            
            # For consumption types, verify intervention
            if mouvement_type in ['sortie', 'retour', 'rebut']:
                intervention = Intervention.query.get(intervention_id)
                if not intervention:
                    raise ValueError(
                        f"❌ Intervention {intervention_id} n'existe pas"
                    )
            
            # ✅ CREATE movement with validated data
            mouvement = MouvementStock(
                type_mouvement=mouvement_type,
                produit_id=produit_id,
                quantite=quantite,
                intervention_id=intervention_id,
                utilisateur_id=utilisateur_id,
                raison_sortie=raison_sortie,
                reference=reference or f'{mouvement_type.upper()}-{datetime.utcnow().timestamp()}',
                prix_unitaire=prix_unitaire,
                commentaire=commentaire or justification,
                emplacement_id=emplacement_id,
                date_mouvement=datetime.utcnow()
            )
            
            db.session.add(mouvement)
            db.session.flush()  # Get ID without committing
            
            # ✅ CREATE audit entry (MANDATORY)
            audit = StockConsumptionAudit(
                mouvement_stock_id=mouvement.id,
                intervention_id=intervention_id,
                actor_id=utilisateur_id,
                technicien_id=intervention.technicien_id if intervention_id else utilisateur_id,
                action=StockTraceabilityService._map_action_type(mouvement_type, raison_sortie),
                justification=justification,
                numero_serie_id=numero_serie_id,
                timestamp=datetime.utcnow()
            )
            db.session.add(audit)
            
            # ✅ LINK serial if applicable
            if numero_serie_id:
                serial = NumeroSerie.query.get(numero_serie_id)
                if serial:
                    # Create transition record
                    transition = NumeroSerieTransition(
                        numero_serie_id=numero_serie_id,
                        from_status=serial.statut.value if serial.statut else 'inconnu',
                        to_status=serial.statut.value if serial.statut else 'inconnu',
                        changed_by_id=utilisateur_id,
                        intervention_id=intervention_id,
                        mouvement_stock_id=mouvement.id,
                        reason=f'Used in {mouvement_type}: {justification}'
                    )
                    db.session.add(transition)
                    
                    # Update serial's intervention link if consumption
                    if mouvement_type in ['sortie', 'retour']:
                        serial.intervention_id = intervention_id
            
            # ✅ COMMIT all changes
            db.session.commit()
            
            logger.info(
                f"✅ Movement created: {mouvement_type} x{quantite} "
                f"(Prod:{produit_id}, Interv:{intervention_id}, "
                f"User:{utilisateur_id})"
            )
            
            return mouvement, audit
            
        except ValueError as ve:
            db.session.rollback()
            logger.error(f"❌ Validation error: {str(ve)}")
            raise
        except Exception as e:
            db.session.rollback()
            logger.exception(f"❌ Error creating movement: {str(e)}")
            raise ValueError(f"Erreur créant mouvement: {str(e)}")
    
    # =========================================================================
    # AUDIT REPORTS: Traceability Queries
    # =========================================================================
    
    @staticmethod
    def get_consumption_by_technician(
        technicien_id,
        start_date=None,
        end_date=None,
        intervention_id=None
    ):
        """
        ✅ AUDIT REPORT: What did this technician use?
        
        Returns complete consumption history with details
        
        Args:
            technicien_id (int): Technician User ID
            start_date (datetime): Filter from date
            end_date (datetime): Filter to date
            intervention_id (int): Optional - specific intervention
        
        Returns:
            list: StockConsumptionAudit entries with full details
        
        Example:
            consumptions = StockTraceabilityService.get_consumption_by_technician(
                technicien_id=123,
                start_date=datetime(2026, 1, 1),
                end_date=datetime(2026, 1, 31)
            )
            for c in consumptions:
                print(f"{c.actor.prenom}: Used {c.mouvement_stock.produit_relation.nom}")
        """
        
        query = StockConsumptionAudit.query.filter(
            StockConsumptionAudit.technicien_id == technicien_id,
            StockConsumptionAudit.action.in_([
                StockConsumptionAudit.ACTION_CONSUME,
                StockConsumptionAudit.ACTION_DAMAGE
            ])
        )
        
        if start_date:
            query = query.filter(StockConsumptionAudit.timestamp >= start_date)
        if end_date:
            query = query.filter(StockConsumptionAudit.timestamp <= end_date)
        if intervention_id:
            query = query.filter(StockConsumptionAudit.intervention_id == intervention_id)
        
        return query.order_by(StockConsumptionAudit.timestamp.desc()).all()
    
    @staticmethod
    def get_intervention_stock_summary(intervention_id):
        """
        ✅ AUDIT REPORT: Stock usage in this intervention
        
        Returns complete stock picture: reservations, consumptions, returns, damage
        
        Args:
            intervention_id (int): Intervention ID
        
        Returns:
            dict: Summary with counts and audit trail
        
        Example:
            summary = StockTraceabilityService.get_intervention_stock_summary(456)
            print(f"Reserved: {summary['reserved_count']}")
            print(f"Consumed: {summary['consumed_count']}")
            print(f"Checkpoint: {summary['checkpoint']['status']}")
        """
        
        # Get checkpoint
        checkpoint = InterventionStockCheckpoint.query.filter_by(
            intervention_id=intervention_id
        ).first()
        
        return {
            'intervention_id': intervention_id,
            'reserved_count': len(ReservationPiece.query.filter_by(
                intervention_id=intervention_id
            ).all()),
            'consumed_count': len(MouvementStock.query.filter_by(
                intervention_id=intervention_id,
                type_mouvement='sortie'
            ).all()),
            'returned_count': len(MouvementStock.query.filter_by(
                intervention_id=intervention_id,
                type_mouvement='retour'
            ).all()),
            'damaged_count': len(MouvementStock.query.filter(
                MouvementStock.intervention_id == intervention_id,
                MouvementStock.raison_sortie == 'rebut'
            ).all()),
            'serials_used': NumeroSerie.query.filter_by(
                intervention_id=intervention_id
            ).all(),
            'checkpoint': checkpoint.get_reconciliation_report() if checkpoint else None,
            'audit_trail': [
                {
                    'action': a.action,
                    'actor': f"{a.actor.prenom} {a.actor.nom}" if a.actor else 'N/A',
                    'product': a.mouvement_stock.produit_relation.nom if a.mouvement_stock else 'N/A',
                    'quantity': a.mouvement_stock.quantite if a.mouvement_stock else 0,
                    'timestamp': a.timestamp.isoformat(),
                    'justification': a.justification
                }
                for a in StockConsumptionAudit.query.filter_by(
                    intervention_id=intervention_id
                ).order_by(StockConsumptionAudit.timestamp).all()
            ]
        }
    
    @staticmethod
    def get_serial_complete_history(numero_serie_id):
        """
        ✅ AUDIT REPORT: Complete lifecycle of serialized item
        
        From creation → technician → intervention → final state
        
        Args:
            numero_serie_id (int): Serial number ID
        
        Returns:
            dict: Complete lifecycle with all transitions
        
        Example:
            history = StockTraceabilityService.get_serial_complete_history(999)
            print(f"Serial: {history['numero']}")
            print(f"Current tech: {history['current_technician']}")
            for trans in history['transitions']:
                print(f"  {trans['from']} → {trans['to']} by {trans['by']} @ {trans['at']}")
        """
        
        serial = NumeroSerie.query.get(numero_serie_id)
        if not serial:
            raise ValueError(f"Serial {numero_serie_id} not found")
        
        return {
            'numero': serial.numero,
            'product': serial.produit.nom if serial.produit else 'N/A',
            'current_status': serial.get_statut_display(),
            'current_technician': (
                f"{serial.technicien.prenom} {serial.technicien.nom}"
                if serial.technicien else None
            ),
            'current_intervention': serial.intervention_id,
            'date_received': serial.date_entree.isoformat() if serial.date_entree else None,
            'date_allocated': (
                serial.date_affectation_tech.isoformat()
                if serial.date_affectation_tech else None
            ),
            'date_installed': (
                serial.date_installation.isoformat()
                if serial.date_installation else None
            ),
            'date_returned': (
                serial.date_retour.isoformat()
                if serial.date_retour else None
            ),
            'transitions': [
                {
                    'from': t.from_status,
                    'to': t.to_status,
                    'by': f"{t.changed_by.prenom} {t.changed_by.nom}" if t.changed_by else 'N/A',
                    'at': t.timestamp.isoformat(),
                    'reason': t.reason,
                    'intervention_id': t.intervention_id,
                    'movement_id': t.mouvement_stock_id
                }
                for t in serial.transitions_history
            ],
            'consumption_events': [
                {
                    'action': a.action,
                    'actor': f"{a.actor.prenom} {a.actor.nom}" if a.actor else 'N/A',
                    'at': a.timestamp.isoformat(),
                    'intervention_id': a.intervention_id,
                    'justification': a.justification
                }
                for a in serial.consumption_audit
            ]
        }
    
    @staticmethod
    def get_user_accountability_report(utilisateur_id, start_date=None, end_date=None):
        """
        ✅ ACCOUNTABILITY REPORT: What did this user do to stock?
        
        Complete actions: who created movements, who approved, who consumed
        
        Args:
            utilisateur_id (int): User ID
            start_date (datetime): Filter from date
            end_date (datetime): Filter to date
        
        Returns:
            dict: Actions performed by user
        """
        
        user = User.query.get(utilisateur_id)
        if not user:
            raise ValueError(f"User {utilisateur_id} not found")
        
        # Actions WHERE this user is the ACTOR
        actor_actions = StockConsumptionAudit.query.filter(
            StockConsumptionAudit.actor_id == utilisateur_id
        )
        
        if start_date:
            actor_actions = actor_actions.filter(
                StockConsumptionAudit.timestamp >= start_date
            )
        if end_date:
            actor_actions = actor_actions.filter(
                StockConsumptionAudit.timestamp <= end_date
            )
        
        actor_actions = actor_actions.all()
        
        # Movements created by this user
        created_movements = MouvementStock.query.filter(
            MouvementStock.utilisateur_id == utilisateur_id
        )
        
        if start_date:
            created_movements = created_movements.filter(
                MouvementStock.date_mouvement >= start_date
            )
        if end_date:
            created_movements = created_movements.filter(
                MouvementStock.date_mouvement <= end_date
            )
        
        created_movements = created_movements.all()
        
        # Serial transitions triggered by this user
        serial_transitions = NumeroSerieTransition.query.filter(
            NumeroSerieTransition.changed_by_id == utilisateur_id
        )
        
        if start_date:
            serial_transitions = serial_transitions.filter(
                NumeroSerieTransition.timestamp >= start_date
            )
        if end_date:
            serial_transitions = serial_transitions.filter(
                NumeroSerieTransition.timestamp <= end_date
            )
        
        serial_transitions = serial_transitions.all()
        
        return {
            'user': f"{user.prenom} {user.nom}",
            'user_id': utilisateur_id,
            'user_role': user.role,
            'period': {
                'start': start_date.isoformat() if start_date else 'N/A',
                'end': end_date.isoformat() if end_date else 'N/A'
            },
            'actions_as_actor': {
                'total': len(actor_actions),
                'items': [
                    {
                        'action': a.action,
                        'intervention_id': a.intervention_id,
                        'product': a.mouvement_stock.produit_relation.nom if a.mouvement_stock else 'N/A',
                        'quantity': a.mouvement_stock.quantite if a.mouvement_stock else 0,
                        'timestamp': a.timestamp.isoformat(),
                        'justification': a.justification
                    }
                    for a in actor_actions
                ]
            },
            'movements_created': {
                'total': len(created_movements),
                'items': [
                    {
                        'type': m.type_mouvement,
                        'product': m.produit_relation.nom if m.produit_relation else 'N/A',
                        'quantity': m.quantite,
                        'intervention_id': m.intervention_id,
                        'reference': m.reference,
                        'timestamp': m.date_mouvement.isoformat()
                    }
                    for m in created_movements
                ]
            },
            'serial_transitions': {
                'total': len(serial_transitions),
                'items': [
                    {
                        'serial': t.numero_serie.numero if t.numero_serie else 'N/A',
                        'transition': f"{t.from_status} → {t.to_status}",
                        'reason': t.reason,
                        'timestamp': t.timestamp.isoformat()
                    }
                    for t in serial_transitions
                ]
            }
        }
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    @staticmethod
    def _map_action_type(mouvement_type, raison_sortie=None):
        """Map mouvement type to audit action"""
        if mouvement_type == 'sortie':
            return StockConsumptionAudit.ACTION_CONSUME
        elif mouvement_type == 'retour':
            return StockConsumptionAudit.ACTION_RETURN
        elif raison_sortie == 'rebut':
            return StockConsumptionAudit.ACTION_DAMAGE
        elif mouvement_type == 'inventaire':
            return StockConsumptionAudit.ACTION_ADJUST
        elif mouvement_type == 'ajustement':
            return StockConsumptionAudit.ACTION_ADJUST
        else:
            return StockConsumptionAudit.ACTION_ADJUST


__all__ = ['StockTraceabilityService']

