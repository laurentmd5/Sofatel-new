#!/usr/bin/env python3
"""
Test script to verify user deletion fix
Tests that users can be deleted without foreign key constraint violation
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, ActivityLog
from datetime import datetime

def test_user_deletion():
    """Test that user deletion works without FK constraint errors"""
    
    with app.app_context():
        print("=" * 60)
        print("USER DELETION TEST")
        print("=" * 60)
        
        # Create a test user
        test_user = User(
            username='test_delete_user_999',
            email='testdeleteuser999@example.com',
            password_hash='hashed_password_placeholder',
            role='magasinier',
            nom='DeleteTest',
            prenom='User',
            telephone='+221771234567'
        )
        
        db.session.add(test_user)
        db.session.commit()
        user_id = test_user.id
        print(f"✅ Test user created: ID={user_id}")
        
        # Add some activity logs for this user
        for i in range(3):
            log = ActivityLog(
                user_id=user_id,
                action='test_action',
                module='test',
                entity_id=None,
                entity_name=f'Test entity {i+1}',
                details='Test details',
                ip_address='127.0.0.1',
                timestamp=datetime.utcnow()
            )
            db.session.add(log)
        
        db.session.commit()
        
        log_count = ActivityLog.query.filter_by(user_id=user_id).count()
        print(f"✅ Created {log_count} activity logs for test user")
        
        # Now test deletion
        try:
            # Delete activity logs first (as per fix)
            ActivityLog.query.filter_by(user_id=user_id).delete()
            
            # Delete the user
            user_to_delete = User.query.get(user_id)
            db.session.delete(user_to_delete)
            db.session.commit()
            
            print(f"✅ User {user_id} deleted successfully")
            
            # Verify deletion
            remaining_user = User.query.get(user_id)
            if remaining_user is None:
                print("✅ Verified: User no longer exists in database")
                return True
            else:
                print("❌ ERROR: User still exists after deletion!")
                return False
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ ERROR during deletion: {str(e)}")
            print(f"   Exception type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = test_user_deletion()
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED: User deletion works correctly")
        sys.exit(0)
    else:
        print("❌ TEST FAILED: User deletion has issues")
        sys.exit(1)
