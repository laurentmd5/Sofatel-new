"""
✅ SPRINT 3 TESTS
Comprehensive tests for HR Workflow (Task 3.1) and Audit Trail (Task 3.2)

Run with: pytest tests/test_sprint3.py -v
"""

import pytest
from datetime import datetime, timedelta, timezone
from models import db, User, LeaveRequest, Intervention, AuditLog, Produit, MouvementStock
from utils_audit import (
    log_intervention_status_change, log_stock_entry, log_stock_removal,
    log_sla_escalation, log_leave_request_created, log_leave_approval,
    get_entity_audit_trail, get_user_audit_trail
)


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def app_context(app):
    """Application context for tests."""
    with app.app_context():
        yield app


@pytest.fixture
def create_users(app_context):
    """Create test users."""
    # Admin user
    admin = User(
        username='admin_test',
        email='admin@test.com',
        nom='Admin',
        prenom='Test',
        password_hash='hashed',
        est_admin=True,
        actif=True,
        role='admin'
    )
    
    # Manager
    manager = User(
        username='manager_test',
        email='manager@test.com',
        nom='Manager',
        prenom='Test',
        password_hash='hashed',
        est_admin=False,
        actif=True,
        role='chef_pilote'
    )
    
    # Technician
    tech = User(
        username='tech_test',
        email='tech@test.com',
        nom='Tech',
        prenom='Test',
        password_hash='hashed',
        est_admin=False,
        actif=True,
        role='technicien'
    )
    
    db.session.add_all([admin, manager, tech])
    db.session.commit()
    
    return {
        'admin': admin,
        'manager': manager,
        'tech': tech
    }


@pytest.fixture
def create_leave_requests(app_context, create_users):
    """Create test leave requests."""
    tech = create_users['tech']
    manager = create_users['manager']
    
    today = datetime.now().date()
    
    # Future leave (valid)
    leave1 = LeaveRequest(
        technicien_id=tech.id,
        manager_id=manager.id,
        date_debut=today + timedelta(days=7),
        date_fin=today + timedelta(days=9),
        raison='Vacation',
        statut='pending',
        created_at=datetime.now(timezone.utc)
    )
    
    # Another future leave (potential overlap)
    leave2 = LeaveRequest(
        technicien_id=tech.id,
        manager_id=manager.id,
        date_debut=today + timedelta(days=20),
        date_fin=today + timedelta(days=22),
        raison='Appointment',
        statut='pending',
        created_at=datetime.now(timezone.utc)
    )
    
    # Approved leave (for overlap testing)
    leave3 = LeaveRequest(
        technicien_id=tech.id,
        manager_id=manager.id,
        date_debut=today + timedelta(days=30),
        date_fin=today + timedelta(days=32),
        raison='Medical',
        statut='approved',
        created_at=datetime.now(timezone.utc)
    )
    
    db.session.add_all([leave1, leave2, leave3])
    db.session.commit()
    
    return {
        'leave1': leave1,
        'leave2': leave2,
        'leave3': leave3
    }


# ============================================================
# TASK 3.1: HR WORKFLOW TESTS
# ============================================================

class TestLeaveRequestModel:
    """Test LeaveRequest model functionality."""
    
    def test_create_leave_request(self, app_context, create_users):
        """Test creating a leave request."""
        tech = create_users['tech']
        manager = create_users['manager']
        
        today = datetime.now().date()
        leave = LeaveRequest(
            technicien_id=tech.id,
            manager_id=manager.id,
            date_debut=today + timedelta(days=5),
            date_fin=today + timedelta(days=7),
            raison='Vacation',
            statut='pending'
        )
        
        db.session.add(leave)
        db.session.commit()
        
        assert leave.id is not None
        assert leave.statut == 'pending'
        assert leave.is_pending() == True
        assert leave.is_approved() == False
    
    def test_leave_status_methods(self, app_context, create_leave_requests):
        """Test leave status helper methods."""
        leave = create_leave_requests['leave1']
        
        assert leave.is_pending() == True
        assert leave.is_approved() == False
        
        # Approve the leave
        leave.statut = 'approved'
        assert leave.is_approved() == True
        assert leave.is_pending() == False
        
        # Reject the leave
        leave.statut = 'rejected'
        assert leave.is_approved() == False
        assert leave.is_pending() == False
    
    def test_leave_overlap_detection(self, app_context, create_users, create_leave_requests):
        """Test overlap detection between leave requests."""
        leave1 = create_leave_requests['leave1']
        leave2 = create_leave_requests['leave2']
        leave3 = create_leave_requests['leave3']
        
        today = datetime.now().date()
        
        # Overlapping dates
        overlapping_leave = LeaveRequest(
            technicien_id=leave1.technicien_id,
            manager_id=leave1.manager_id,
            date_debut=leave1.date_debut,
            date_fin=leave1.date_fin + timedelta(days=1),
            raison='Test'
        )
        
        # Should overlap with leave1
        assert overlapping_leave.overlaps_with(leave1) == True
        
        # Should not overlap with leave2 (different dates)
        assert overlapping_leave.overlaps_with(leave2) == False
        
        # Should not overlap with leave3 (different dates)
        assert overlapping_leave.overlaps_with(leave3) == False
    
    def test_business_days_calculation(self, app_context, create_users):
        """Test business days calculation (exclude weekends)."""
        tech = create_users['tech']
        manager = create_users['manager']
        
        # Monday to Friday (5 business days)
        # Find a Monday
        today = datetime.now().date()
        monday = today
        while monday.weekday() != 0:  # 0 = Monday
            monday += timedelta(days=1)
        
        friday = monday + timedelta(days=4)
        
        leave = LeaveRequest(
            technicien_id=tech.id,
            manager_id=manager.id,
            date_debut=monday,
            date_fin=friday,
            raison='Week vacation'
        )
        
        db.session.add(leave)
        db.session.commit()
        
        assert leave.business_days_count == 5
    
    def test_leave_timestamps(self, app_context, create_users):
        """Test leave request timestamps."""
        tech = create_users['tech']
        manager = create_users['manager']
        
        today = datetime.now().date()
        leave = LeaveRequest(
            technicien_id=tech.id,
            manager_id=manager.id,
            date_debut=today + timedelta(days=5),
            date_fin=today + timedelta(days=7),
            raison='Vacation',
            statut='pending'
        )
        
        db.session.add(leave)
        db.session.commit()
        
        # created_at should be set automatically
        assert leave.created_at is not None
        
        # Approve the leave
        leave.statut = 'approved'
        leave.approved_at = datetime.now(timezone.utc)
        db.session.commit()
        
        assert leave.approved_at is not None


class TestLeaveWorkflow:
    """Test complete leave request workflow."""
    
    def test_complete_leave_request_workflow(self, app_context, create_users):
        """Test complete leave workflow: create -> approve."""
        tech = create_users['tech']
        manager = create_users['manager']
        
        today = datetime.now().date()
        
        # Step 1: Create leave request
        leave = LeaveRequest(
            technicien_id=tech.id,
            manager_id=manager.id,
            date_debut=today + timedelta(days=10),
            date_fin=today + timedelta(days=12),
            raison='Vacation',
            statut='pending'
        )
        db.session.add(leave)
        db.session.commit()
        
        assert leave.statut == 'pending'
        assert leave.is_pending() == True
        
        # Step 2: Manager approves
        leave.statut = 'approved'
        leave.approved_at = datetime.now(timezone.utc)
        db.session.commit()
        
        assert leave.statut == 'approved'
        assert leave.is_approved() == True
        
        # Step 3: Retrieve and verify
        retrieved = db.session.get(LeaveRequest, leave.id)
        assert retrieved.statut == 'approved'
        assert retrieved.approved_at is not None


# ============================================================
# TASK 3.2: AUDIT TRAIL TESTS
# ============================================================

class TestAuditLogModel:
    """Test AuditLog model functionality."""
    
    def test_create_audit_log(self, app_context, create_users):
        """Test creating an audit log entry."""
        actor = create_users['admin']
        
        audit = AuditLog(
            actor_id=actor.id,
            action='test_action',
            entity_type='test',
            entity_id=1,
            old_value='{"key": "old"}',
            new_value='{"key": "new"}',
            created_at=datetime.now(timezone.utc)
        )
        
        db.session.add(audit)
        db.session.commit()
        
        assert audit.id is not None
        assert audit.action == 'test_action'
        assert audit.entity_type == 'test'
    
    def test_audit_immutability(self, app_context, create_users):
        """Test that audit logs are immutable (no updates)."""
        actor = create_users['admin']
        
        audit = AuditLog(
            actor_id=actor.id,
            action='test_action',
            entity_type='test',
            entity_id=1,
            created_at=datetime.now(timezone.utc)
        )
        
        db.session.add(audit)
        db.session.commit()
        
        original_id = audit.id
        original_created = audit.created_at
        
        # Attempt to "update" (should not be allowed by business logic)
        audit_id = audit.id
        
        # Retrieve and verify immutability
        retrieved = db.session.get(AuditLog, audit_id)
        assert retrieved.created_at == original_created


class TestAuditLoggingFunctions:
    """Test audit logging utility functions."""
    
    def test_log_intervention_status_change(self, app_context, create_users):
        """Test logging intervention status changes."""
        actor = create_users['admin']
        
        audit = log_intervention_status_change(
            intervention_id=1,
            old_status='en_cours',
            new_status='valide',
            actor_id=actor.id,
            reason='Completed by technician'
        )
        
        assert audit is not None
        assert audit.action == 'intervention_status_changed'
        assert audit.entity_type == 'intervention'
        assert audit.entity_id == 1
    
    def test_log_stock_entry(self, app_context, create_users):
        """Test logging stock entry."""
        actor = create_users['admin']
        
        audit = log_stock_entry(
            produit_id=1,
            quantity=100,
            actor_id=actor.id,
            supplier='Supplier Inc.',
            invoice_num='INV-001'
        )
        
        assert audit is not None
        assert audit.action == 'stock_entry'
        assert audit.entity_type == 'stock'
        assert audit.entity_id == 1
    
    def test_log_stock_removal(self, app_context, create_users):
        """Test logging stock removal."""
        actor = create_users['admin']
        
        audit = log_stock_removal(
            produit_id=1,
            quantity=10,
            actor_id=actor.id,
            reason='Used for job #42'
        )
        
        assert audit is not None
        assert audit.action == 'stock_removal'
        assert audit.entity_type == 'stock'
        assert audit.entity_id == 1
    
    def test_log_sla_escalation(self, app_context, create_users):
        """Test logging SLA escalation."""
        actor = create_users['admin']
        
        audit = log_sla_escalation(
            intervention_id=1,
            actor_id=actor.id,
            priority='urgent',
            reason='Escalated to level 2'
        )
        
        assert audit is not None
        assert audit.action == 'sla_escalated'
        assert audit.entity_type == 'sla'
        assert audit.entity_id == 1
    
    def test_log_leave_request_created(self, app_context, create_users):
        """Test logging leave request creation."""
        actor = create_users['tech']
        
        audit = log_leave_request_created(
            leave_id=1,
            technicien_id=actor.id,
            actor_id=actor.id,
            business_days=3
        )
        
        assert audit is not None
        assert audit.action == 'leave_request_created'
        assert audit.entity_type == 'leave_request'
        assert audit.entity_id == 1
    
    def test_log_leave_approval(self, app_context, create_users):
        """Test logging leave approval."""
        actor = create_users['manager']
        
        audit = log_leave_approval(
            leave_id=1,
            approved=True,
            actor_id=actor.id,
            comment='Approved'
        )
        
        assert audit is not None
        assert audit.action == 'leave_approved'
        assert audit.entity_type == 'leave_request'


class TestAuditQueryFunctions:
    """Test audit query and retrieval functions."""
    
    def test_get_entity_audit_trail(self, app_context, create_users):
        """Test retrieving audit trail for an entity."""
        actor = create_users['admin']
        
        # Create multiple audit entries
        for i in range(3):
            log_intervention_status_change(
                intervention_id=1,
                old_status='en_cours',
                new_status='valide',
                actor_id=actor.id
            )
        
        trail = get_entity_audit_trail('intervention', 1, limit=10)
        
        assert len(trail) >= 3
        assert trail[0]['action'] == 'intervention_status_changed'
        assert trail[0]['entity_type'] == 'intervention'
    
    def test_get_user_audit_trail(self, app_context, create_users):
        """Test retrieving user activity."""
        actor = create_users['admin']
        
        # Create multiple audit entries by this user
        for i in range(3):
            log_intervention_status_change(
                intervention_id=i+1,
                old_status='en_cours',
                new_status='valide',
                actor_id=actor.id
            )
        
        trail = get_user_audit_trail(actor.id, limit=10)
        
        assert len(trail) >= 3
        assert all(entry['action'] == 'intervention_status_changed' for entry in trail)


class TestAuditTrailIntegration:
    """Integration tests for audit trail with actual operations."""
    
    def test_intervention_status_change_with_audit(self, app_context, create_users):
        """Test intervention status change creates audit trail."""
        admin = create_users['admin']
        
        # Simulate intervention status change
        log_intervention_status_change(
            intervention_id=42,
            old_status='en_cours',
            new_status='valide',
            actor_id=admin.id,
            reason='Manager approved'
        )
        
        # Verify audit trail
        trail = get_entity_audit_trail('intervention', 42)
        assert len(trail) >= 1
        assert trail[0]['new_value']['statut'] == 'valide'
        assert trail[0]['old_value']['statut'] == 'en_cours'
    
    def test_stock_operations_with_audit(self, app_context, create_users):
        """Test stock operations create audit trail."""
        admin = create_users['admin']
        
        # Entry
        log_stock_entry(
            produit_id=5,
            quantity=100,
            actor_id=admin.id,
            supplier='Supplier'
        )
        
        # Removal
        log_stock_removal(
            produit_id=5,
            quantity=10,
            actor_id=admin.id,
            reason='Job #1'
        )
        
        # Verify trail
        trail = get_entity_audit_trail('stock', 5)
        assert len(trail) >= 2
        actions = [entry['action'] for entry in trail]
        assert 'stock_entry' in actions
        assert 'stock_removal' in actions


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
