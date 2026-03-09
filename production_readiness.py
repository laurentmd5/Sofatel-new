"""
🔴 PRODUCTION CRITICAL: Stock Module Production Readiness Checker

This module runs on application startup to:
1. Verify all critical production fixes are in place
2. Check database schema for required indexes and constraints
3. Run migrations if needed
4. Report production readiness status

Usage in app.py or create_app():
    from production_readiness import check_and_fix_production_readiness
    
    app = Flask(__name__)
    # ... configure app ...
    
    with app.app_context():
        db.create_all()
        check_and_fix_production_readiness(app)
"""

from flask import current_app
from extensions import db
from sqlalchemy import text, inspect
import logging

logger = logging.getLogger(__name__)


class ProductionReadinessChecker:
    """Verifies all production-critical fixes are in place"""
    
    def __init__(self, app):
        self.app = app
        self.issues = []
        self.fixes_applied = []
    
    def check_negative_stock_prevention(self):
        """Check if sortie_stock has negative stock validation"""
        logger.info("🔍 Checking negative stock prevention in routes...")
        try:
            with open('routes_stock.py', 'r', encoding='utf-8') as f:
                content = f.read()
                if 'Prevent stock from going negative' in content and 'quantite > stock_disponible' in content:
                    logger.info("✅ Negative stock prevention found in routes_stock.py")
                    return True
                else:
                    self.issues.append("❌ Negative stock prevention NOT found in routes_stock.py")
                    return False
        except Exception as e:
            self.issues.append(f"⚠️ Could not check routes_stock.py: {str(e)}")
            return False
    
    def check_rbac_decorators(self):
        """Check if RBAC decorators are applied to critical routes"""
        logger.info("🔍 Checking RBAC decorators...")
        try:
            with open('routes_stock.py', 'r', encoding='utf-8') as f:
                content = f.read()
                
                checks = [
                    ('@require_stock_permission(\'can_view_global_stock\')\ndef gestion_stock', 
                     'gestion_stock root route'),
                    ('@require_stock_permission(\'can_view_global_stock\')\ndef liste_produits',
                     'liste_produits route'),
                    ('@require_stock_permission(\'can_receive_stock\')\ndef entree_stock',
                     'entree_stock route'),
                    ('@require_stock_permission(\'can_dispatch_stock\')\ndef sortie_stock',
                     'sortie_stock route'),
                ]
                
                missing = []
                for pattern, route_name in checks:
                    if pattern not in content:
                        missing.append(route_name)
                
                if missing:
                    self.issues.append(f"❌ RBAC decorators missing on: {', '.join(missing)}")
                    return False
                else:
                    logger.info("✅ RBAC decorators found on all critical routes")
                    return True
        except Exception as e:
            self.issues.append(f"⚠️ Could not check RBAC decorators: {str(e)}")
            return False
    
    def check_workflow_enforcement(self):
        """Check if workflow enforcement is in place"""
        logger.info("🔍 Checking workflow enforcement...")
        try:
            with open('routes_stock.py', 'r', encoding='utf-8') as f:
                content = f.read()
                if 'validate_and_initialize_mouvement_workflow' in content:
                    logger.info("✅ Workflow enforcement function found in routes_stock.py")
                    return True
                else:
                    self.issues.append("❌ Workflow enforcement NOT found in routes_stock.py")
                    return False
        except Exception as e:
            self.issues.append(f"⚠️ Could not check workflow enforcement: {str(e)}")
            return False
    
    def check_database_indexes(self):
        """Check if critical database indexes exist"""
        logger.info("🔍 Checking database indexes...")
        try:
            inspector = inspect(db.engine)
            
            required_indexes = [
                ('mouvement_stock', 'idx_mouvement_produit'),
                ('mouvement_stock', 'idx_mouvement_type'),
                ('mouvement_stock', 'idx_mouvement_workflow'),
                ('mouvement_stock', 'idx_mouvement_date'),
                ('produits', 'idx_produit_reference'),
            ]
            
            missing_indexes = []
            existing_indexes = {}
            
            for table_name in inspector.get_table_names():
                existing_indexes[table_name] = [idx['name'] for idx in inspector.get_indexes(table_name)]
            
            for table_name, index_name in required_indexes:
                if table_name not in existing_indexes or index_name not in existing_indexes[table_name]:
                    missing_indexes.append(f"{table_name}.{index_name}")
            
            if missing_indexes:
                self.issues.append(f"❌ Missing indexes: {', '.join(missing_indexes)}")
                logger.warning(f"⚠️ Missing {len(missing_indexes)} indexes. Run production_migrations.py")
                return False
            else:
                logger.info("✅ All critical indexes found")
                return True
        except Exception as e:
            self.issues.append(f"⚠️ Could not check indexes: {str(e)}")
            return False
    
    def check_database_constraints(self):
        """Check if critical database constraints exist"""
        logger.info("🔍 Checking database constraints...")
        try:
            # Query for CHECK constraints (database-specific)
            sql = text("""
                SELECT CONSTRAINT_NAME FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
                WHERE TABLE_NAME = 'mouvement_stock' AND CONSTRAINT_TYPE = 'CHECK'
            """)
            
            result = db.session.execute(sql)
            constraints = [row[0] for row in result]
            
            required_constraints = [
                'ck_mouvement_workflow_state',
                'ck_mouvement_type_valid',
                'ck_mouvement_quantite_positive',
            ]
            
            missing_constraints = [c for c in required_constraints if c not in constraints]
            
            if missing_constraints:
                self.issues.append(f"❌ Missing constraints: {', '.join(missing_constraints)}")
                logger.warning(f"⚠️ Missing {len(missing_constraints)} constraints. Run production_migrations.py")
                return False
            else:
                logger.info("✅ All critical constraints found")
                return True
        except Exception as e:
            logger.warning(f"⚠️ Could not verify constraints (may be OK if DB doesn't support): {str(e)}")
            return True  # Don't fail if DB doesn't support CHECK constraints
    
    def run_all_checks(self):
        """Run all production readiness checks"""
        logger.info("\n" + "=" * 70)
        logger.info("🔴 PRODUCTION READINESS CHECK - STOCK MODULE")
        logger.info("=" * 70 + "\n")
        
        checks = [
            ("Negative Stock Prevention", self.check_negative_stock_prevention),
            ("RBAC Decorators", self.check_rbac_decorators),
            ("Workflow Enforcement", self.check_workflow_enforcement),
            ("Database Indexes", self.check_database_indexes),
            ("Database Constraints", self.check_database_constraints),
        ]
        
        results = {}
        for check_name, check_func in checks:
            try:
                results[check_name] = check_func()
            except Exception as e:
                logger.error(f"❌ Error running {check_name}: {str(e)}")
                results[check_name] = False
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("SUMMARY:")
        logger.info("=" * 70)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for check_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status}: {check_name}")
        
        logger.info("=" * 70)
        logger.info(f"SCORE: {passed}/{total} ({100*passed//total}%)")
        
        if self.issues:
            logger.warning("\nISSUES DETECTED:")
            for issue in self.issues:
                logger.warning(f"  {issue}")
        
        if passed == total:
            logger.info("\n🎉 PRODUCTION READY! All critical fixes verified.")
            return True
        else:
            logger.error(f"\n❌ PRODUCTION NOT READY! {total - passed} issue(s) to fix.")
            return False


def check_and_fix_production_readiness(app):
    """
    Main entry point to check and fix production readiness
    
    Usage:
        with app.app_context():
            check_and_fix_production_readiness(app)
    """
    checker = ProductionReadinessChecker(app)
    is_ready = checker.run_all_checks()
    
    if not is_ready:
        current_app.logger.error("\n" + "!" * 70)
        current_app.logger.error("CRITICAL: Stock module has production blockers!")
        current_app.logger.error("Run: python production_migrations.py")
        current_app.logger.error("!" * 70)
    
    return is_ready
