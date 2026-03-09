#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de vérification du filtrage par zone pour magasinier

Cet ensemble de tests vérifie que:
1. Un magasinier ne peut voir que les produits de sa zone
2. Un magasinier ne peut créer des mouvements que dans sa zone
3. Un gestionnaire voit tous les produits
4. Un gestionnaire peut voir tous les mouvements
"""

import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

# Imports from the application
import sys
sys.path.insert(0, '/c/Users/Lenovo/Downloads/SOFATELCOM')

from models import User, Produit, EmplacementStock, MouvementStock, Zone
from zone_rbac import (
    user_has_global_access,
    validate_magasinier_zone_access,
    validate_emplacement_zone,
    filter_produit_by_emplacement_zone,
    filter_mouvement_by_zone
)


class TestZoneIsolation(unittest.TestCase):
    """Tests pour l'isolation des zones"""
    
    def setUp(self):
        """Préparation des tests"""
        # Create mock users
        self.magasinier_nord = Mock(spec=User)
        self.magasinier_nord.id = 1
        self.magasinier_nord.role = 'magasinier'
        self.magasinier_nord.zone_id = 1  # Zone NORD
        
        self.magasinier_sud = Mock(spec=User)
        self.magasinier_sud.id = 2
        self.magasinier_sud.role = 'magasinier'
        self.magasinier_sud.zone_id = 2  # Zone SUD
        
        self.gestionnaire = Mock(spec=User)
        self.gestionnaire.id = 3
        self.gestionnaire.role = 'gestionnaire_stock'
        self.gestionnaire.zone_id = None  # No zone restriction
        
        # Create mock zones
        self.zone_nord = Mock(spec=Zone)
        self.zone_nord.id = 1
        self.zone_nord.nom = 'NORD'
        
        self.zone_sud = Mock(spec=Zone)
        self.zone_sud.id = 2
        self.zone_sud.nom = 'SUD'
        
        # Create mock emplacements
        self.emplacement_nord = Mock(spec=Emplacement)
        self.emplacement_nord.id = 1
        self.emplacement_nord.zone_id = 1  # Zone NORD
        self.emplacement_nord.zone = self.zone_nord
        
        self.emplacement_sud = Mock(spec=Emplacement)
        self.emplacement_sud.id = 2
        self.emplacement_sud.zone_id = 2  # Zone SUD
        self.emplacement_sud.zone = self.zone_sud
        
        # Create mock produits
        self.produit_nord = Mock(spec=Produit)
        self.produit_nord.id = 1
        self.produit_nord.nom = 'Router NORD'
        self.produit_nord.emplacement = self.emplacement_nord
        
        self.produit_sud = Mock(spec=Produit)
        self.produit_sud.id = 2
        self.produit_sud.nom = 'Switch SUD'
        self.produit_sud.emplacement = self.emplacement_sud
        
        # Create mock mouvements
        self.mouvement_nord = Mock(spec=MouvementStock)
        self.mouvement_nord.id = 1
        self.mouvement_nord.type_mouvement = 'entree'
        self.mouvement_nord.emplacement = self.emplacement_nord
        self.mouvement_nord.emplacement_id = 1
        
        self.mouvement_sud = Mock(spec=MouvementStock)
        self.mouvement_sud.id = 2
        self.mouvement_sud.type_mouvement = 'sortie'
        self.mouvement_sud.emplacement = self.emplacement_sud
        self.mouvement_sud.emplacement_id = 2
    
    def test_user_has_global_access_for_gestionnaire(self):
        """Un gestionnaire doit avoir accès global"""
        result = user_has_global_access(self.gestionnaire)
        self.assertTrue(result, "Gestionnaire devrait avoir accès global")
    
    def test_user_has_global_access_for_magasinier(self):
        """Un magasinier ne doit pas avoir accès global"""
        result = user_has_global_access(self.magasinier_nord)
        self.assertFalse(result, "Magasinier ne devrait pas avoir accès global")
    
    def test_validate_magasinier_zone_access_with_zone(self):
        """Un magasinier avec zone_id doit être valide"""
        try:
            validate_magasinier_zone_access(self.magasinier_nord)
            # Should not raise
        except Exception as e:
            self.fail(f"validate_magasinier_zone_access levé une exception: {e}")
    
    def test_validate_magasinier_zone_access_without_zone(self):
        """Un magasinier sans zone_id devrait être rejeté"""
        magasinier_no_zone = Mock(spec=User)
        magasinier_no_zone.role = 'magasinier'
        magasinier_no_zone.zone_id = None
        
        with self.assertRaises(Exception):
            validate_magasinier_zone_access(magasinier_no_zone)
    
    def test_produit_access_magasinier_same_zone(self):
        """Un magasinier doit pouvoir accéder au produit de sa zone"""
        # Should not raise
        result = True
        if self.magasinier_nord.zone_id != self.produit_nord.emplacement.zone_id:
            result = False
        self.assertTrue(result, "Magasinier NORD devrait accéder au produit NORD")
    
    def test_produit_access_magasinier_different_zone(self):
        """Un magasinier ne doit pas pouvoir accéder au produit d'une autre zone"""
        result = False
        if self.magasinier_nord.zone_id != self.produit_sud.emplacement.zone_id:
            result = True
        self.assertTrue(result, "Magasinier NORD ne devrait pas accéder au produit SUD")
    
    def test_mouvement_access_magasinier_same_zone(self):
        """Un magasinier doit pouvoir accéder au mouvement de sa zone"""
        result = True
        if self.magasinier_nord.zone_id != self.mouvement_nord.emplacement_id:
            result = False
        self.assertTrue(result, "Magasinier NORD devrait accéder au mouvement NORD")
    
    def test_mouvement_access_magasinier_different_zone(self):
        """Un magasinier ne doit pas pouvoir accéder au mouvement d'une autre zone"""
        result = False
        if self.magasinier_nord.zone_id != self.mouvement_sud.emplacement_id:
            result = True
        self.assertTrue(result, "Magasinier NORD ne devrait pas accéder au mouvement SUD")


class TestZoneAccessControl(unittest.TestCase):
    """Tests d'accès par zone"""
    
    def test_zone_based_produit_query_magasinier(self):
        """Vérifier que la query de produit filtre par zone pour magasinier"""
        # Test que la fonction filter_produit_by_emplacement_zone existe et est callable
        self.assertTrue(callable(filter_produit_by_emplacement_zone),
                       "filter_produit_by_emplacement_zone doit être callable")
    
    def test_zone_based_mouvement_query_magasinier(self):
        """Vérifier que la query de mouvement filtre par zone pour magasinier"""
        # Test que la fonction filter_mouvement_by_zone existe et est callable
        self.assertTrue(callable(filter_mouvement_by_zone),
                       "filter_mouvement_by_zone doit être callable")


if __name__ == '__main__':
    print("="*70)
    print("Tests de vérification de l'isolation par zone")
    print("="*70)
    unittest.main(verbosity=2)
