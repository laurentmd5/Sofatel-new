"""
SUITE DE TESTS COMPLÈTE ET VALIDE - STOCK MANAGEMENT
100% compatible avec le modèle réel

Résultat attendu: 15+ tests PASSANTS ✅
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
    """Génère un ID unique"""
    ts = datetime.now().strftime('%Y%m%d%H%M%S%f')[-10:]
    uid = str(uuid.uuid4())[:8]
    return f"{prefix}-{ts}-{uid}"


@pytest.fixture
def app_context():
    """Contexte Flask"""
    with app.app_context():
        yield app


# ============================================================================
# TESTS RBAC
# ============================================================================

class TestRBACSystem:
    """Tests du système RBAC"""
    
    def test_six_roles_exist(self, app_context):
        """Les 6 rôles doivent exister"""
        roles = {'chef_pur', 'gestionnaire_stock', 'magasinier', 
                'technicien', 'direction', 'admin'}
        assert roles == set(STOCK_PERMISSIONS.keys())
    
    def test_chef_pur_has_permissions(self, app_context):
        """Chef PUR doit avoir des permissions"""
        assert len(STOCK_PERMISSIONS['chef_pur']) > 0
    
    def test_gestionnaire_has_permissions(self, app_context):
        """Gestionnaire doit avoir des permissions"""
        assert len(STOCK_PERMISSIONS['gestionnaire_stock']) > 0
    
    def test_magasinier_has_permissions(self, app_context):
        """Magasinier doit avoir des permissions"""
        assert len(STOCK_PERMISSIONS['magasinier']) > 0


# ============================================================================
# TESTS USER
# ============================================================================

class TestUserModel:
    """Tests du modèle User"""
    
    def test_create_user_with_all_required_fields(self, app_context):
        """Créer un utilisateur avec tous les champs requis"""
        user = User(
            username=generate_unique_id("USR"),
            email=f"user-{uuid.uuid4()}@test.local",
            password_hash=generate_password_hash('test123'),
            role='gestionnaire_stock',
            nom='Test User'
        )
        db.session.add(user)
        db.session.commit()
        
        try:
            assert user.id is not None
            assert user.username is not None
            assert user.email is not None
        finally:
            db.session.delete(user)
            db.session.commit()
    
    def test_user_permissions_function(self, app_context):
        """get_user_stock_permissions doit fonctionner"""
        user = User(
            username=generate_unique_id("USR"),
            email=f"user-{uuid.uuid4()}@test.local",
            password_hash=generate_password_hash('test123'),
            role='chef_pur',
            nom='Chef Test'
        )
        db.session.add(user)
        db.session.commit()
        
        try:
            perms = get_user_stock_permissions(user)
            # La fonction doit retourner quelque chose
            assert perms is not None or isinstance(perms, list)
        finally:
            db.session.delete(user)
            db.session.commit()


# ============================================================================
# TESTS EMPLACEMENT STOCK
# ============================================================================

class TestEmplacementStock:
    """Tests du modèle EmplacementStock"""
    
    def test_create_with_code(self, app_context):
        """Créer un emplacement avec code"""
        code = generate_unique_id("RAYON")
        emp = EmplacementStock(
            code=code,
            designation="Rayon Principal"
        )
        db.session.add(emp)
        db.session.commit()
        
        try:
            assert emp.id is not None
            assert emp.code == code
        finally:
            try:
                db.session.delete(emp)
                db.session.commit()
            except:
                db.session.rollback()


# ============================================================================
# TESTS PRODUIT
# ============================================================================

class TestProduitModel:
    """Tests du modèle Produit"""
    
    def test_create_produit(self, app_context):
        """Créer un produit"""
        prod = Produit(
            reference=generate_unique_id("PROD"),
            nom="Produit Test",
            prix_achat=Decimal('100.00'),
            prix_vente=Decimal('150.00')
        )
        db.session.add(prod)
        db.session.commit()
        
        try:
            assert prod.id is not None
            assert prod.reference is not None
        finally:
            try:
                db.session.delete(prod)
                db.session.commit()
            except:
                db.session.rollback()


# ============================================================================
# TESTS FOURNISSEUR
# ============================================================================

class TestFournisseurModel:
    """Tests du modèle Fournisseur"""
    
    def test_create_fournisseur(self, app_context):
        """Créer un fournisseur"""
        fourn = Fournisseur(
            code=generate_unique_id("FOR"),
            raison_sociale="Acme Inc"
        )
        db.session.add(fourn)
        db.session.commit()
        
        try:
            assert fourn.id is not None
        finally:
            try:
                db.session.delete(fourn)
                db.session.commit()
            except:
                db.session.rollback()


# ============================================================================
# TESTS MOUVEMENT STOCK
# ============================================================================

class TestMouvementStock:
    """Tests du modèle MouvementStock"""
    
    def test_create_mouvement(self, app_context):
        """Créer un mouvement stock"""
        user = User(
            username=generate_unique_id("USR"),
            email=f"u-{uuid.uuid4()}@test.local",
            password_hash=generate_password_hash('test'),
            nom='User Test'
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
            
            try:
                assert mouv.id is not None
                assert mouv.quantite == 50
            finally:
                db.session.delete(mouv)
                db.session.commit()
        finally:
            try:
                db.session.delete(user)
                db.session.commit()
            except:
                db.session.rollback()
    
    def test_mouvement_types_valid(self, app_context):
        """Vérifier les types de mouvement valides"""
        user = User(
            username=generate_unique_id("USR"),
            email=f"u-{uuid.uuid4()}@test.local",
            password_hash=generate_password_hash('test'),
            nom='User Test'
        )
        db.session.add(user)
        db.session.commit()
        
        try:
            for type_mv in ['entree', 'sortie']:
                mouv = MouvementStock(
                    type_mouvement=type_mv,
                    quantite=10,
                    utilisateur_id=user.id
                )
                db.session.add(mouv)
                db.session.commit()
                
                try:
                    assert mouv.type_mouvement == type_mv
                finally:
                    db.session.delete(mouv)
                    db.session.commit()
        finally:
            try:
                db.session.delete(user)
                db.session.commit()
            except:
                db.session.rollback()


# ============================================================================
# TESTS NUMERO SERIE
# ============================================================================

class TestNumeroSerie:
    """Tests du modèle NumeroSerie"""
    
    def test_enum_statuses_exist(self, app_context):
        """Les 6 statuts enum doivent exister"""
        statuses = [
            NumeroSerieStatut.EN_MAGASIN,
            NumeroSerieStatut.ALLOUE_ZONE,
            NumeroSerieStatut.ALLOUE_TECHNICIEN,
            NumeroSerieStatut.INSTALLEE,
            NumeroSerieStatut.RETOURNEE,
            NumeroSerieStatut.REBUT
        ]
        assert len(statuses) == 6
    
    def test_create_numero_serie(self, app_context):
        """Créer un numéro de série"""
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
            try:
                db.session.delete(ns)
                db.session.commit()
            except:
                db.session.rollback()


# ============================================================================
# TESTS INTEGRATION
# ============================================================================

class TestIntegration:
    """Tests d'intégration"""
    
    def test_produit_avec_fournisseur(self, app_context):
        """Produit peut être lié à un fournisseur"""
        fourn = Fournisseur(code=generate_unique_id("FOR"))
        db.session.add(fourn)
        db.session.commit()
        
        try:
            prod = Produit(
                reference=generate_unique_id("PROD"),
                fournisseur_id=fourn.id
            )
            db.session.add(prod)
            db.session.commit()
            
            try:
                assert prod.fournisseur_id == fourn.id
            finally:
                db.session.delete(prod)
                db.session.commit()
        finally:
            try:
                db.session.delete(fourn)
                db.session.commit()
            except:
                db.session.rollback()
    
    def test_mouvement_avec_utilisateur(self, app_context):
        """Mouvement doit être lié à un utilisateur"""
        user = User(
            username=generate_unique_id("USR"),
            email=f"u-{uuid.uuid4()}@test.local",
            password_hash=generate_password_hash('test'),
            nom='User Test'
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
            
            try:
                retrieved = MouvementStock.query.get(mouv.id)
                assert retrieved.utilisateur_id == user.id
            finally:
                db.session.delete(mouv)
                db.session.commit()
        finally:
            try:
                db.session.delete(user)
                db.session.commit()
            except:
                db.session.rollback()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
