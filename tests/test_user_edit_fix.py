from app import app, db
from models import User
from flask_login import current_user
import pytest
from datetime import datetime

def test_user_model_has_last_login():
    """Verify that the User model has the last_login field."""
    assert hasattr(User, 'last_login')

def test_edit_user_page_renders_successfully():
    """Verify that the edit user page renders without 500 error."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        # Create a test user if not exists
        user = User.query.filter_by(username='test_fix_user').first()
        if not user:
            user = User(
                username='test_fix_user',
                email='test_fix@example.com',
                password_hash='dummy',
                role='technicien',
                nom='Test',
                prenom='Fix',
                telephone='00000000'
            )
            db.session.add(user)
            db.session.commit()

        # Create an admin user to access the page
        admin = User.query.filter_by(role='chef_pur').first()
        if not admin:
            admin = User(
                username='test_admin',
                email='admin_fix@example.com',
                password_hash='dummy',
                role='chef_pur',
                nom='Admin',
                prenom='Fix',
                telephone='11111111'
            )
            db.session.add(admin)
            db.session.commit()

        client = app.test_client()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin.id)
            sess['_fresh'] = True

        # Try to access the edit page for the test user
        response = client.get(f'/edit-user/{user.id}')
        
        # Check if it returns 200 OK (no 500 error)
        assert response.status_code == 200
        # Check if the "Dernière connexion" label is present in the rendered HTML
        assert b"Derni\xc3\xa8re connexion" in response.data or b"Derniere connexion" in response.data

        # Cleanup
        db.session.delete(user)
        if admin.username == 'test_admin':
            db.session.delete(admin)
        db.session.commit()
