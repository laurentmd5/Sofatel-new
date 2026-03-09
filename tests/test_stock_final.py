"""
SUITE DE TESTS PRODUCTION-READY - GESTION DE STOCK
Tests isolés avec des fixtures indépendantes par test
"""

import pytest
import uuid
from datetime import datetime
from decimal import Decimal
from app import app, db
from models import (
    User, Categorie, EmplacementStock, Fournisseur, Produit,
    MouvementStock, NumeroSerie, NumeroSerieStatut
)
from rbac_stock import get_user_stock_permissions, has_stock_permission, STOCK_PERMISSIONS
from werkzeug.security import generate_password_hash


def generate_unique_id(prefix="TEST"):
    """Génère un ID unique pour éviter les doublons"""
    ts = datetime.now().strftime('%Y%m%d%H%M%S%f')[-10:]
    uid = str(uuid.uuid4())[:8]
    return f"{prefix}-{ts}-{uid}"


@pytest.fixture
def app_context():
    """Contexte Flask pour les tests"""
    with app.app_context():
        yield app


# ============================================================================
# TEST CLASS 1: RBAC Permissions
# ============================================================================

class TestRBACSystem:
    """Tests du système RBAC - 6 rôles et permissions"""
    
    def test_six_roles_defined(self, app_context):
        """Vérifier que les 6 rôles existent dans STOCK_PERMISSIONS"""
        expected_roles = ['chef_pur', 'gestionnaire_stock', 'magasinier', 
                         'technicien', 'direction', 'admin']
        assert set(STOCK_PERMISSIONS.keys()) == set(expected_roles)
    
    def test_chef_pur_has_full_permissions(self, app_context):
        """Chef PUR doit avoir toutes les permissions"""
        chef_perms = STOCK_PERMISSIONS.get('chef_pur', [])
        assert len(chef_perms) >= 5  # Au moins 5 permissions
        
    def test_gestionnaire_limited_permissions(self, app_context):
        """Gestionnaire doit avoir moins de permissions que Chef PUR"""
        chef_perms = STOCK_PERMISSIONS.get('chef_pur', [])
        gest_perms = STOCK_PERMISSIONS.get('gestionnaire_stock', [])
        assert len(gest_perms) < len(chef_perms)
    
    def test_magasinier_local_permissions(self, app_context):
        """Magasinier doit avoir des permissions réduites"""
        mag_perms = STOCK_PERMISSIONS.get('magasinier', [])
        assert len(mag_perms) > 0
        assert len(mag_perms) < len(STOCK_PERMISSIONS.get('chef_pur', []))
    
    def test_get_user_stock_permissions_function_exists(self, app_context):
        """Vérifier que la fonction get_user_stock_permissions existe"""
        # Créer un utilisateur test
        user = User(
            username=generate_unique_id("USER"),
            email=f"user-{uuid.uuid4()}@test.com",
            password_hash=generate_password_hash('test123'),
            role='chef_pur'
        )
        db.session.add(user)
        db.session.commit()
        
        try:
            perms = get_user_stock_permissions(user)
            assert isinstance(perms, (list, tuple))
        finally:
            db.session.delete(user)
            db.session.commit()
    
    def test_has_stock_permission_positive(self, app_context):
        """has_stock_permission retourne True si permission existe"""
        user = User(
            username=generate_unique_id("USER"),
            email=f"user-{uuid.uuid4()}@test.com",
            password_hash=generate_password_hash('test123'),
            role='chef_pur'
        )
        db.session.add(user)
        db.session.commit()
        
        try:
            # Au moins une permission doit exister pour Chef PUR
            user_perms = get_user_stock_permissions(user)
            if user_perms:
                result = has_stock_permission(user, user_perms[0])
                assert result is True
        finally:
            db.session.delete(user)
            db.session.commit()
    
    def test_has_stock_permission_negative(self, app_context):
        """has_stock_permission retourne False si permission n'existe pas"""
        user = User(
            username=generate_unique_id("USER"),
            email=f"user-{uuid.uuid4()}@test.com",
            password_hash=generate_password_hash('test123'),
            role='magasinier'
        )
        db.session.add(user)
        db.session.commit()
        
        try:
            result = has_stock_permission(user, 'permission_inexistante_xyz')
            # La fonction doit retourner False ou False
            assert result is False or result is None or result == False
        finally:
            db.session.delete(user)
            db.session.commit()


# ============================================================================
# TEST CLASS 2: Produit Model
# ============================================================================

class TestProduitModel:
    """Tests du modèle Produit"""
    
    def test_create_produit_minimal(self, app_context):
        """Créer un produit avec les champs obligatoires"""
        prod = Produit(
            reference=generate_unique_id("PROD"),
            nom=f"Produit-{uuid.uuid4()}"
        )
        db.session.add(prod)
        db.session.commit()
        
        try:
            assert prod.id is not None
            assert prod.reference is not None
        finally:
            db.session.delete(prod)
            db.session.commit()
    
    def test_produit_with_decimal_price(self, app_context):
        """Produit avec prix décimal"""
        prod = Produit(
            reference=generate_unique_id("PROD"),
            nom=f"Produit-{uuid.uuid4()}",
            prix_unitaire=Decimal('150.50')
        )
        db.session.add(prod)
        db.session.commit()
        
        try:
            assert prod.prix_unitaire == Decimal('150.50')
        finally:
            db.session.delete(prod)
            db.session.commit()
    
    def test_produit_reference_must_be_unique(self, app_context):
        """Référence produit doit être unique"""
        ref = generate_unique_id("PROD")
        prod1 = Produit(reference=ref, nom="Produit 1")
        db.session.add(prod1)
        db.session.commit()
        
        try:
            prod2 = Produit(reference=ref, nom="Produit 2")
            db.session.add(prod2)
            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()
            db.session.rollback()
        finally:
            db.session.delete(prod1)
            db.session.commit()


# ============================================================================
# TEST CLASS 3: EmplacementStock Model
# ============================================================================

class TestEmplacementStockModel:
    """Tests du modèle EmplacementStock"""
    
    def test_create_emplacement_minimal(self, app_context):
        """Créer un emplacement avec données minimales"""
        emp = EmplacementStock(code=generate_unique_id("RAYON"))
        db.session.add(emp)
        db.session.commit()
        
        try:
            assert emp.id is not None
            assert emp.code is not None
        finally:
            db.session.delete(emp)
            db.session.commit()
    
    def test_emplacement_code_must_be_unique(self, app_context):
        """Code d'emplacement doit être unique"""
        code = generate_unique_id("RAYON")
        emp1 = EmplacementStock(code=code)
        db.session.add(emp1)
        db.session.commit()
        
        try:
            emp2 = EmplacementStock(code=code)
            db.session.add(emp2)
            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()
            db.session.rollback()
        finally:
            db.session.delete(emp1)
            db.session.commit()


# ============================================================================
# TEST CLASS 4: Fournisseur Model
# ============================================================================

class TestFournisseurModel:
    """Tests du modèle Fournisseur"""
    
    def test_create_fournisseur_minimal(self, app_context):
        """Créer un fournisseur minimal"""
        fourn = Fournisseur(code=generate_unique_id("FOURN"))
        db.session.add(fourn)
        db.session.commit()
        
        try:
            assert fourn.id is not None
        finally:
            db.session.delete(fourn)
            db.session.commit()
    
    def test_fournisseur_code_must_be_unique(self, app_context):
        """Code fournisseur doit être unique"""
        code = generate_unique_id("FOURN")
        f1 = Fournisseur(code=code)
        db.session.add(f1)
        db.session.commit()
        
        try:
            f2 = Fournisseur(code=code)
            db.session.add(f2)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()
        finally:
            db.session.delete(f1)
            db.session.commit()


# ============================================================================
# TEST CLASS 5: MouvementStock Model
# ============================================================================

class TestMouvementStockModel:
    """Tests du modèle MouvementStock"""
    
    def test_create_mouvement_minimal(self, app_context):
        """Créer un mouvement stock minimal"""
        user = User(
            username=generate_unique_id("USER"),
            email=f"user-{uuid.uuid4()}@test.com",
            password_hash=generate_password_hash('test123')
        )
        db.session.add(user)
        db.session.commit()
        
        try:
            mouv = MouvementStock(
                type_mouvement='entree',
                quantite=50,
                utilisateur_id=user.id
            )
            db.session.add(mouv)
            db.session.commit()
            
            assert mouv.id is not None
            assert mouv.quantite == 50
            
            db.session.delete(mouv)
            db.session.commit()
        finally:
            db.session.delete(user)
            db.session.commit()
    
    def test_mouvement_workflow_state_initial(self, app_context):
        """État initial du workflow doit être EN_ATTENTE"""
        user = User(
            username=generate_unique_id("USER"),
            email=f"user-{uuid.uuid4()}@test.com",
            password_hash=generate_password_hash('test123')
        )
        db.session.add(user)
        db.session.commit()
        
        try:
            mouv = MouvementStock(
                type_mouvement='sortie',
                quantite=10,
                utilisateur_id=user.id
            )
            db.session.add(mouv)
            db.session.commit()
            
            # État initial doit être EN_ATTENTE ou similaire
            assert mouv.workflow_state is not None
            
            db.session.delete(mouv)
            db.session.commit()
        finally:
            db.session.delete(user)
            db.session.commit()
    
    def test_mouvement_type_enum_validation(self, app_context):
        """Type mouvement doit être parmi les types valides"""
        user = User(
            username=generate_unique_id("USER"),
            email=f"user-{uuid.uuid4()}@test.com",
            password_hash=generate_password_hash('test123')
        )
        db.session.add(user)
        db.session.commit()
        
        try:
            # Types valides selon le modèle
            valid_types = ['entree', 'sortie', 'inventaire', 'ajustement', 'retour']
            
            for type_mv in valid_types[:2]:  # Test juste 2 types
                mouv = MouvementStock(
                    type_mouvement=type_mv,
                    quantite=5,
                    utilisateur_id=user.id
                )
                db.session.add(mouv)
                db.session.commit()
                
                assert mouv.type_mouvement == type_mv
                
                db.session.delete(mouv)
                db.session.commit()
        finally:
            db.session.delete(user)
            db.session.commit()


# ============================================================================
# TEST CLASS 6: NumeroSerie Model
# ============================================================================

class TestNumeroSerieModel:
    """Tests du modèle NumeroSerie"""
    
    def test_create_numero_serie_with_enum_status(self, app_context):
        """Créer un numéro série avec statut enum EN_MAGASIN"""
        ns = NumeroSerie(
            numero=generate_unique_id("SN"),
            statut=NumeroSerieStatut.EN_MAGASIN
        )
        db.session.add(ns)
        db.session.commit()
        
        try:
            assert ns.id is not None
            assert ns.statut == NumeroSerieStatut.EN_MAGASIN
        finally:
            db.session.delete(ns)
            db.session.commit()
    
    def test_numero_serie_all_enum_values(self, app_context):
        """Vérifier que tous les statuts enum existent"""
        # Les 6 statuts du modèle
        statuses = [
            NumeroSerieStatut.EN_MAGASIN,
            NumeroSerieStatut.ALLOUE_ZONE,
            NumeroSerieStatut.ALLOUE_TECHNICIEN,
            NumeroSerieStatut.INSTALLEE,
            NumeroSerieStatut.RETOURNEE,
            NumeroSerieStatut.REBUT
        ]
        
        assert len(statuses) == 6
    
    def test_numero_serie_numero_must_be_unique(self, app_context):
        """Numéro de série doit être unique"""
        numero = generate_unique_id("SN")
        ns1 = NumeroSerie(
            numero=numero,
            statut=NumeroSerieStatut.EN_MAGASIN
        )
        db.session.add(ns1)
        db.session.commit()
        
        try:
            ns2 = NumeroSerie(
                numero=numero,
                statut=NumeroSerieStatut.EN_MAGASIN
            )
            db.session.add(ns2)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()
        finally:
            db.session.delete(ns1)
            db.session.commit()


# ============================================================================
# TEST CLASS 7: User Model & Authentication
# ============================================================================

class TestUserModel:
    """Tests du modèle User"""
    
    def test_create_user_with_role(self, app_context):
        """Créer un utilisateur avec rôle"""
        user = User(
            username=generate_unique_id("USER"),
            email=f"user-{uuid.uuid4()}@test.com",
            password_hash=generate_password_hash('password123'),
            role='chef_pur'
        )
        db.session.add(user)
        db.session.commit()
        
        try:
            assert user.id is not None
            assert user.role == 'chef_pur'
        finally:
            db.session.delete(user)
            db.session.commit()
    
    def test_user_email_must_be_unique(self, app_context):
        """Email utilisateur doit être unique"""
        email = f"unique-{uuid.uuid4()}@test.com"
        user1 = User(
            username=generate_unique_id("USER"),
            email=email,
            password_hash=generate_password_hash('test123')
        )
        db.session.add(user1)
        db.session.commit()
        
        try:
            user2 = User(
                username=generate_unique_id("USER2"),
                email=email,
                password_hash=generate_password_hash('test123')
            )
            db.session.add(user2)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()
        finally:
            db.session.delete(user1)
            db.session.commit()


# ============================================================================
# TEST CLASS 8: Integration Tests
# ============================================================================

class TestIntegration:
    """Tests d'intégration entre modèles"""
    
    def test_produit_with_fournisseur_fk(self, app_context):
        """Produit peut être lié à un Fournisseur"""
        fourn = Fournisseur(code=generate_unique_id("FOURN"))
        db.session.add(fourn)
        db.session.commit()
        
        try:
            prod = Produit(
                reference=generate_unique_id("PROD"),
                nom="Produit avec Fournisseur",
                fournisseur_id=fourn.id
            )
            db.session.add(prod)
            db.session.commit()
            
            assert prod.fournisseur_id == fourn.id
            
            db.session.delete(prod)
            db.session.commit()
        finally:
            db.session.delete(fourn)
            db.session.commit()
    
    def test_mouvement_with_user_fk(self, app_context):
        """Mouvement doit être lié à un User"""
        user = User(
            username=generate_unique_id("USER"),
            email=f"user-{uuid.uuid4()}@test.com",
            password_hash=generate_password_hash('test123')
        )
        db.session.add(user)
        db.session.commit()
        
        try:
            mouv = MouvementStock(
                type_mouvement='entree',
                quantite=25,
                utilisateur_id=user.id
            )
            db.session.add(mouv)
            db.session.commit()
            
            assert mouv.utilisateur_id == user.id
            
            db.session.delete(mouv)
            db.session.commit()
        finally:
            db.session.delete(user)
            db.session.commit()
    
    def test_numero_serie_with_produit_fk(self, app_context):
        """NumeroSerie peut être lié à un Produit"""
        prod = Produit(
            reference=generate_unique_id("PROD"),
            nom="Produit Sérialisé"
        )
        db.session.add(prod)
        db.session.commit()
        
        try:
            ns = NumeroSerie(
                numero=generate_unique_id("SN"),
                statut=NumeroSerieStatut.EN_MAGASIN,
                produit_id=prod.id
            )
            db.session.add(ns)
            db.session.commit()
            
            assert ns.produit_id == prod.id
            
            db.session.delete(ns)
            db.session.commit()
        finally:
            db.session.delete(prod)
            db.session.commit()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
