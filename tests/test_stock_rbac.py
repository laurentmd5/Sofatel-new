"""
UNIT TEST SUITE: Stock Management RBAC (Role-Based Access Control)
Tests for permission enforcement, role authorization, privilege escalation prevention
"""

import pytest
import uuid
from datetime import datetime
from app import app, db
from models import User, Produit, MouvementStock
from rbac_stock import (
    get_user_stock_permissions,
    has_stock_permission,
    require_stock_permission,
    require_stock_role,
    STOCK_PERMISSIONS
)
from werkzeug.security import generate_password_hash


def generate_unique_code(prefix="TEST"):
    """Generate unique code to avoid duplicates"""
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"


@pytest.fixture
def app_context():
    """App context for testing"""
    with app.app_context():
        yield


@pytest.fixture
def client():
    """Test client with authentication"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        yield app.test_client()


def create_user(username=None, role='chef_pur'):
    """Helper to create user with role and unique username"""
    if username is None:
        username = generate_unique_code("USER")
    
    user = User(
        username=username,
        email=f'{uuid.uuid4()}@test.com',
        password_hash=generate_password_hash('password'),
        role=role,
        nom='Test',
        prenom='User',
        telephone='1234567890'
    )
    db.session.add(user)
    db.session.commit()
    return user


# ============================================================================
# TEST SUITE: Permission Configuration
# ============================================================================

class TestPermissionConfiguration:
    """Tests for permission configuration by role"""
    
    def test_all_roles_defined(self):
        """✅ All required roles have permission definitions"""
        required_roles = ['chef_pur', 'gestionnaire_stock', 'magasinier', 'technicien', 'direction', 'admin']
        
        for role in required_roles:
            assert role in STOCK_PERMISSIONS, f"Role {role} not defined in STOCK_PERMISSIONS"
    
    def test_chef_pur_permissions(self):
        """✅ Chef PUR has full permissions"""
        perms = STOCK_PERMISSIONS['chef_pur']
        
        assert perms['can_view_global_stock'] is True
        assert perms['can_create_produit'] is True
        assert perms['can_modify_produit'] is True
        assert perms['can_delete_produit'] is True
        assert perms['can_receive_stock'] is True
        assert perms['can_dispatch_stock'] is True
        assert perms['can_approve_stock_movement'] is True
        assert perms['max_edit_distance'] is None
    
    def test_gestionnaire_stock_permissions(self):
        """✅ Gestionnaire Stock has limited modify/delete"""
        perms = STOCK_PERMISSIONS['gestionnaire_stock']
        
        assert perms['can_view_global_stock'] is True
        assert perms['can_create_produit'] is True
        assert perms['can_modify_produit'] is False
        assert perms['can_delete_produit'] is False
        assert perms['can_approve_stock_movement'] is False
    
    def test_magasinier_permissions(self):
        """✅ Magasinier has local zone permissions only"""
        perms = STOCK_PERMISSIONS['magasinier']
        
        assert perms['can_view_global_stock'] is False
        assert perms['can_create_produit'] is False
        assert perms['can_receive_stock'] is True
        assert perms['can_dispatch_stock'] is True
        assert perms['max_edit_distance'] == 'zone'
    
    def test_technicien_permissions(self):
        """✅ Technicien has minimal permissions (terrain only)"""
        perms = STOCK_PERMISSIONS['technicien']
        
        assert perms['can_view_global_stock'] is False
        assert perms['can_create_produit'] is False
        assert perms['can_modify_produit'] is False
        assert perms['can_receive_stock'] is False
    
    def test_direction_permissions(self):
        """✅ Direction has read-only global view"""
        perms = STOCK_PERMISSIONS['direction']
        
        assert perms['can_view_global_stock'] is True
        assert perms['can_view_reports'] is True
        assert perms['can_create_produit'] is False
        assert perms['can_modify_produit'] is False
    
    def test_admin_permissions(self):
        """✅ Admin has full permissions"""
        perms = STOCK_PERMISSIONS['admin']
        
        assert perms['can_view_global_stock'] is True
        assert perms['can_create_produit'] is True
        assert perms['can_modify_produit'] is True
        assert perms['can_delete_produit'] is True
        assert perms['can_approve_stock_movement'] is True


# ============================================================================
# TEST SUITE: Permission Retrieval
# ============================================================================

class TestPermissionRetrieval:
    """Tests for retrieving user permissions"""
    
    def test_get_chef_pur_permissions(self, app_context):
        """✅ get_user_stock_permissions returns correct dict for chef_pur"""
        user = create_user(role='chef_pur')
        perms = get_user_stock_permissions(user)
        
        assert perms['can_view_global_stock'] is True
        assert perms['can_approve_stock_movement'] is True
    
    def test_get_gestionnaire_permissions(self, app_context):
        """✅ get_user_stock_permissions returns correct dict for gestionnaire"""
        user = create_user(role='gestionnaire_stock')
        perms = get_user_stock_permissions(user)
        
        assert perms['can_view_global_stock'] is True
        assert perms['can_modify_produit'] is False
    
    def test_get_magasinier_permissions(self, app_context):
        """✅ get_user_stock_permissions returns correct dict for magasinier"""
        user = create_user(role='magasinier')
        perms = get_user_stock_permissions(user)
        
        assert perms['can_view_global_stock'] is False
        assert perms['max_edit_distance'] == 'zone'
    
    def test_get_permissions_none_user(self, app_context):
        """✅ get_user_stock_permissions returns empty dict for None user"""
        perms = get_user_stock_permissions(None)
        assert perms == {}
    
    def test_get_permissions_no_role(self, app_context):
        """✅ get_user_stock_permissions returns empty dict for user without role"""
        user = User(
            username='no_role',
            email='no@test.com',
            password_hash=generate_password_hash('pwd'),
            nom='No',
            prenom='Role',
            telephone='123'
        )
        db.session.add(user)
        db.session.commit()
        
        perms = get_user_stock_permissions(user)
        assert perms == {}


# ============================================================================
# TEST SUITE: Permission Checking
# ============================================================================

class TestPermissionChecking:
    """Tests for checking specific permissions"""
    
    def test_has_permission_chef_pur_view_global(self, app_context):
        """✅ Chef PUR has can_view_global_stock permission"""
        user = create_user(role='chef_pur')
        
        assert has_stock_permission(user, 'can_view_global_stock') is True
    
    def test_has_permission_chef_pur_delete(self, app_context):
        """✅ Chef PUR has can_delete_produit permission"""
        user = create_user(role='chef_pur')
        
        assert has_stock_permission(user, 'can_delete_produit') is True
    
    def test_has_permission_gestionnaire_cannot_delete(self, app_context):
        """❌ Gestionnaire does NOT have can_delete_produit permission"""
        user = create_user(role='gestionnaire_stock')
        
        assert has_stock_permission(user, 'can_delete_produit') is False
    
    def test_has_permission_gestionnaire_cannot_approve(self, app_context):
        """❌ Gestionnaire does NOT have can_approve_stock_movement permission"""
        user = create_user(role='gestionnaire_stock')
        
        assert has_stock_permission(user, 'can_approve_stock_movement') is False
    
    def test_has_permission_magasinier_cannot_view_global(self, app_context):
        """❌ Magasinier does NOT have can_view_global_stock permission"""
        user = create_user(role='magasinier')
        
        assert has_stock_permission(user, 'can_view_global_stock') is False
    
    def test_has_permission_magasinier_can_receive(self, app_context):
        """✅ Magasinier has can_receive_stock permission"""
        user = create_user(role='magasinier')
        
        assert has_stock_permission(user, 'can_receive_stock') is True
    
    def test_has_permission_technicien_limited(self, app_context):
        """✅ Technicien has very limited permissions"""
        user = create_user(role='technicien')
        
        assert has_stock_permission(user, 'can_create_produit') is False
        assert has_stock_permission(user, 'can_receive_stock') is False
        assert has_stock_permission(user, 'can_approve_stock_movement') is False
    
    def test_has_permission_direction_readonly(self, app_context):
        """✅ Direction can only view reports"""
        user = create_user(role='direction')
        
        assert has_stock_permission(user, 'can_view_global_stock') is True
        assert has_stock_permission(user, 'can_view_reports') is True
        assert has_stock_permission(user, 'can_create_produit') is False
    
    def test_has_permission_admin_full_access(self, app_context):
        """✅ Admin has all permissions"""
        user = create_user(role='admin')
        
        all_perms = ['can_view_global_stock', 'can_create_produit', 'can_modify_produit',
                     'can_delete_produit', 'can_receive_stock', 'can_dispatch_stock',
                     'can_approve_stock_movement', 'can_view_reports']
        
        for perm in all_perms:
            assert has_stock_permission(user, perm) is True
    
    def test_has_permission_none_user(self, app_context):
        """❌ None user has no permissions"""
        assert has_stock_permission(None, 'can_view_global_stock') is False


# ============================================================================
# TEST SUITE: Privilege Escalation Prevention
# ============================================================================

class TestPrivilegeEscalationPrevention:
    """Tests for preventing unauthorized privilege elevation"""
    
    def test_technicien_cannot_create_produit(self, app_context):
        """❌ Technicien cannot create products (privilege escalation)"""
        user = create_user(role='technicien')
        
        # Even if they somehow get the permission, roles should be strictly enforced
        assert has_stock_permission(user, 'can_create_produit') is False
    
    def test_magasinier_cannot_approve_movements(self, app_context):
        """❌ Magasinier cannot approve stock movements"""
        user = create_user(role='magasinier')
        
        assert has_stock_permission(user, 'can_approve_stock_movement') is False
    
    def test_technicien_cannot_delete_produit(self, app_context):
        """❌ Technicien cannot delete products"""
        user = create_user(role='technicien')
        
        assert has_stock_permission(user, 'can_delete_produit') is False
    
    def test_direction_cannot_modify_stock(self, app_context):
        """❌ Direction cannot modify stock (read-only role)"""
        user = create_user(role='direction')
        
        assert has_stock_permission(user, 'can_create_produit') is False
        assert has_stock_permission(user, 'can_modify_produit') is False
        assert has_stock_permission(user, 'can_delete_produit') is False
    
    def test_gestionnaire_cannot_modify_produit(self, app_context):
        """❌ Gestionnaire cannot modify existing products"""
        user = create_user(role='gestionnaire_stock')
        
        assert has_stock_permission(user, 'can_modify_produit') is False


# ============================================================================
# TEST SUITE: Role-Specific Restrictions
# ============================================================================

class TestRoleSpecificRestrictions:
    """Tests for role-specific business logic restrictions"""
    
    def test_magasinier_zone_restriction(self, app_context):
        """✅ Magasinier has max_edit_distance='zone' restriction"""
        user = create_user(role='magasinier')
        perms = get_user_stock_permissions(user)
        
        assert perms['max_edit_distance'] == 'zone'
    
    def test_chef_pur_no_distance_restriction(self, app_context):
        """✅ Chef PUR has max_edit_distance=None (no restriction)"""
        user = create_user(role='chef_pur')
        perms = get_user_stock_permissions(user)
        
        assert perms['max_edit_distance'] is None
    
    def test_gestionnaire_no_distance_restriction(self, app_context):
        """✅ Gestionnaire has max_edit_distance=None (global scope)"""
        user = create_user(role='gestionnaire_stock')
        perms = get_user_stock_permissions(user)
        
        assert perms['max_edit_distance'] is None


# ============================================================================
# TEST SUITE: Permission Matrix Completeness
# ============================================================================

class TestPermissionMatrixCompleteness:
    """Tests for completeness and consistency of permission matrix"""
    
    def test_all_permissions_have_definitions(self):
        """✅ Every permission key is defined for each role"""
        required_perms = [
            'can_view_global_stock', 'can_create_produit', 'can_modify_produit',
            'can_delete_produit', 'can_receive_stock', 'can_dispatch_stock',
            'can_adjust_stock', 'can_approve_stock_movement', 'can_manage_fournisseurs',
            'can_import_articles', 'can_view_reports', 'can_manage_emplacements',
            'max_edit_distance'
        ]
        
        for role, perms in STOCK_PERMISSIONS.items():
            for req_perm in required_perms:
                assert req_perm in perms, f"Role {role} missing permission {req_perm}"
    
    def test_permission_values_are_boolean_or_none(self):
        """✅ Permission values are either bool or None/string for max_edit_distance"""
        for role, perms in STOCK_PERMISSIONS.items():
            for perm_key, perm_value in perms.items():
                if perm_key == 'max_edit_distance':
                    # This can be None or a string
                    assert perm_value is None or isinstance(perm_value, str)
                else:
                    # Other permissions must be boolean
                    assert isinstance(perm_value, bool), \
                        f"Role {role}, permission {perm_key} has non-boolean value: {perm_value}"
    
    def test_admin_has_all_true_permissions(self):
        """✅ Admin role has all permissions set to True"""
        admin_perms = STOCK_PERMISSIONS['admin']
        
        for perm_key, perm_value in admin_perms.items():
            if perm_key != 'max_edit_distance':
                assert perm_value is True, f"Admin missing permission {perm_key}"


# ============================================================================
# TEST SUITE: Cross-Role Scenarios
# ============================================================================

class TestCrossRoleScenarios:
    """Tests for multi-user scenarios and role interactions"""
    
    def test_chef_can_approve_all_movement_types(self, app_context):
        """✅ Chef PUR can approve all types of stock movements"""
        user = create_user(role='chef_pur')
        
        assert has_stock_permission(user, 'can_receive_stock') is True
        assert has_stock_permission(user, 'can_dispatch_stock') is True
        assert has_stock_permission(user, 'can_adjust_stock') is True
        assert has_stock_permission(user, 'can_approve_stock_movement') is True
    
    def test_gestionnaire_cannot_approve_but_can_create(self, app_context):
        """✅ Gestionnaire can create movements but not approve"""
        user = create_user(role='gestionnaire_stock')
        
        assert has_stock_permission(user, 'can_receive_stock') is True
        assert has_stock_permission(user, 'can_dispatch_stock') is True
        assert has_stock_permission(user, 'can_approve_stock_movement') is False
    
    def test_multiple_users_different_permissions(self, app_context):
        """✅ Multiple users can have different permission levels"""
        chef = create_user('chef', 'chef_pur')
        gest = create_user('gest', 'gestionnaire_stock')
        mag = create_user('mag', 'magasinier')
        
        # Chef can do everything
        assert has_stock_permission(chef, 'can_approve_stock_movement') is True
        
        # Gestionnaire cannot approve
        assert has_stock_permission(gest, 'can_approve_stock_movement') is False
        
        # Magasinier is zone-restricted
        assert has_stock_permission(mag, 'can_view_global_stock') is False
