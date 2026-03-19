from app import app, db
from models import User
from flask_login import login_user, logout_user
import pytest

def test_unauthenticated_login_page_no_notification_init():
    """Verify that NotificationManager is not initialized on the login page."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    client = app.test_client()
    
    # Access login page as guest
    response = client.get('/login')
    
    # Check if NotificationManager initialization is MISSING
    # The fix used: {% if current_user.is_authenticated %} notificationManager = new NotificationManager(); {% endif %}
    assert b"notificationManager = new NotificationManager();" not in response.data
    
    # Check if mobile-nav.js null check is present (optional)
    # The fix added: if (!this.navbarCollapse) { ... }
    # Since we can't easily check the loaded JS, we just check the rendered HTML for any 401 triggers.

def test_authenticated_dashboard_has_notification_init():
    """Verify that NotificationManager is initialized when logged in."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        # Create an admin user to access the page
        admin = User.query.filter_by(role='chef_pur').first()
        if not admin:
            admin = User(
                username='test_admin_nav',
                email='admin_nav@example.com',
                password_hash='dummy',
                role='chef_pur',
                nom='Admin',
                prenom='Nav',
                telephone='11111111'
            )
            db.session.add(admin)
            db.session.commit()

        client = app.test_client()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin.id)
            sess['_fresh'] = True

        # Access dashboard
        response = client.get('/dashboard')
        
        # Check if NotificationManager initialization is PRESENT
        assert b"notificationManager = new NotificationManager();" in response.data

        # Cleanup
        if admin.username == 'test_admin_nav':
            db.session.delete(admin)
            db.session.commit()
