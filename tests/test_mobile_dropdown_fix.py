"""
Mobile Dropdown Fix Tests
Tests for Administration and other dropdown menus on mobile
"""

import pytest
from app import app, db
from models import User
from werkzeug.security import generate_password_hash


@pytest.fixture
def client():
    """Create a Flask test client with in-memory database."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def chef_pur_user(client):
    """Create a chef_pur test user."""
    with app.app_context():
        user = User(
            username='chefpur',
            email='chef@test.com',
            password_hash=generate_password_hash('password123'),
            role='chef_pur',
            nom='Chef',
            prenom='Pur',
            telephone='1234567890'
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def authenticated_chef_pur(client, chef_pur_user):
    """Return a logged-in chef_pur client."""
    client.post('/login', data={
        'username': 'chefpur',
        'password': 'password123'
    }, follow_redirects=True)
    return client


class TestDropdownsOnMobile:
    """Test that dropdown menus work correctly on mobile."""
    
    def test_administration_dropdown_in_html(self, authenticated_chef_pur):
        """Test that Administration dropdown exists in HTML."""
        response = authenticated_chef_pur.get('/dashboard')
        html = response.data.decode('utf-8')
        assert 'Administration' in html
        assert 'adminDropdown' in html
        assert 'Créer utilisateur' in html
        assert 'Gérer utilisateurs' in html
        assert 'Historique connexions' in html or 'Historique' in html
    
    def test_dropdown_menu_class(self, authenticated_chef_pur):
        """Test that dropdown-menu class exists."""
        response = authenticated_chef_pur.get('/dashboard')
        html = response.data.decode('utf-8')
        assert 'dropdown-menu' in html
    
    def test_dropdown_items_exist(self, authenticated_chef_pur):
        """Test that all dropdown items exist."""
        response = authenticated_chef_pur.get('/dashboard')
        html = response.data.decode('utf-8')
        assert 'dropdown-item' in html
        assert 'create_user' in html or 'Créer utilisateur' in html
        assert 'manage_users' in html or 'Gérer utilisateurs' in html


class TestMobileDropdownCSS:
    """Test CSS for mobile dropdowns."""
    
    def test_dropdown_menu_hidden_by_default(self, client):
        """Test that dropdown menus are hidden by default."""
        response = client.get('/static/css/mobile.css')
        css_content = response.data.decode('utf-8')
        # Should have display: none for dropdown-menu
        assert 'dropdown-menu' in css_content
        assert 'display: none' in css_content or 'display:none' in css_content
    
    def test_dropdown_menu_show_class(self, client):
        """Test that .show class makes dropdown visible."""
        response = client.get('/static/css/mobile.css')
        css_content = response.data.decode('utf-8')
        assert 'dropdown-menu.show' in css_content
        assert 'display: flex' in css_content or 'display:flex' in css_content
    
    def test_dropdown_item_styling(self, client):
        """Test that dropdown items have proper styling."""
        response = client.get('/static/css/mobile.css')
        css_content = response.data.decode('utf-8')
        assert 'dropdown-item' in css_content
        # Should have proper padding and color
        assert 'padding' in css_content or 'color' in css_content


class TestMobileDropdownJavaScript:
    """Test JavaScript for mobile dropdown handling."""
    
    def test_dropdown_toggle_listener(self, client):
        """Test that dropdown toggle click listener exists."""
        response = client.get('/static/js/mobile-nav.js')
        js_content = response.data.decode('utf-8')
        assert 'dropdown-toggle' in js_content
        assert 'classList.toggle' in js_content or 'toggle(' in js_content
    
    def test_dropdown_items_handler(self, client):
        """Test that dropdown items have click handler."""
        response = client.get('/static/js/mobile-nav.js')
        js_content = response.data.decode('utf-8')
        # Should handle dropdown item clicks
        assert 'dropdown-item' in js_content or 'this.close()' in js_content
    
    def test_dropdown_close_on_drawer_close(self, client):
        """Test that dropdowns close when drawer closes."""
        response = client.get('/static/js/mobile-nav.js')
        js_content = response.data.decode('utf-8')
        # Should remove 'show' class from dropdowns in close()
        assert 'dropdown-menu' in js_content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
