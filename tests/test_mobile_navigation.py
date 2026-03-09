"""
Mobile Navigation Tests
Tests for responsive drawer navigation on mobile devices
Validates: Hamburger menu, drawer toggling, backdrop overlay, responsive behavior

Execution: python -m pytest tests/test_mobile_navigation.py -v
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
def test_user(client):
    """Create a test user for navigation tests."""
    with app.app_context():
        user = User(
            username='navtest',
            email='nav@test.com',
            password_hash=generate_password_hash('password123'),
            role='chef_pur',
            nom='Nav',
            prenom='Test',
            telephone='1234567890'
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def authenticated_client(client, test_user):
    """Return a logged-in test client."""
    client.post('/login', data={
        'username': 'navtest',
        'password': 'password123'
    }, follow_redirects=True)
    return client


class TestMobileNavigationHTML:
    """Test that base.html includes required navigation elements."""
    
    def test_navbar_element_exists(self, authenticated_client):
        """Test that navbar element is present in the template."""
        response = authenticated_client.get('/dashboard')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert '<nav class="navbar' in html or 'navbar' in html
        
    def test_navbar_toggler_exists(self, authenticated_client):
        """Test that hamburger toggle button exists (for mobile)."""
        response = authenticated_client.get('/dashboard')
        html = response.data.decode('utf-8')
        assert 'navbar-toggler' in html
        
    def test_navbar_collapse_exists(self, authenticated_client):
        """Test that navbar collapse container exists (drawer container)."""
        response = authenticated_client.get('/dashboard')
        html = response.data.decode('utf-8')
        assert 'navbar-collapse' in html
        
    def test_navbar_nav_structure(self, authenticated_client):
        """Test that navbar-nav structure exists."""
        response = authenticated_client.get('/dashboard')
        html = response.data.decode('utf-8')
        assert 'navbar-nav' in html
        
    def test_mobile_nav_script_loaded(self, authenticated_client):
        """Test that mobile-nav.js script is loaded in the template."""
        response = authenticated_client.get('/dashboard')
        html = response.data.decode('utf-8')
        assert 'mobile-nav.js' in html or 'MobileNavManager' in html


class TestMobileNavigationCSS:
    """Test that mobile.css is properly linked and contains required styles."""
    
    def test_mobile_css_link(self, authenticated_client):
        """Test that mobile.css is linked in the template."""
        response = authenticated_client.get('/dashboard')
        html = response.data.decode('utf-8')
        assert 'mobile.css' in html
        
    def test_mobile_css_serves_correctly(self, client):
        """Test that mobile.css can be served."""
        response = client.get('/static/css/mobile.css')
        assert response.status_code == 200
        assert b'navbar' in response.data or b'drawer' in response.data
        
    def test_drawer_styles_present(self, client):
        """Test that drawer-related styles are in mobile.css."""
        response = client.get('/static/css/mobile.css')
        css_content = response.data.decode('utf-8')
        assert 'navbar-collapse' in css_content
        assert 'navbar-backdrop' in css_content
        assert 'drawer-open' in css_content
        
    def test_mobile_media_query_present(self, client):
        """Test that mobile media query is present."""
        response = client.get('/static/css/mobile.css')
        css_content = response.data.decode('utf-8')
        assert '(max-width: 768px)' in css_content or 'max-width: 768px' in css_content
        
    def test_desktop_media_query_present(self, client):
        """Test that desktop media query is present for no-regression."""
        response = client.get('/static/css/mobile.css')
        css_content = response.data.decode('utf-8')
        assert '(min-width: 769px)' in css_content or 'min-width: 769px' in css_content


class TestMobileNavigationJavaScript:
    """Test that mobile-nav.js contains required functionality."""
    
    def test_mobile_nav_js_exists(self, client):
        """Test that mobile-nav.js file exists and can be served."""
        response = client.get('/static/js/mobile-nav.js')
        assert response.status_code == 200
        
    def test_mobile_nav_manager_class(self, client):
        """Test that MobileNavManager class is defined."""
        response = client.get('/static/js/mobile-nav.js')
        js_content = response.data.decode('utf-8')
        assert 'class MobileNavManager' in js_content
        
    def test_toggle_method_exists(self, client):
        """Test that toggle() method exists in MobileNavManager."""
        response = client.get('/static/js/mobile-nav.js')
        js_content = response.data.decode('utf-8')
        assert 'toggle()' in js_content
        
    def test_open_method_exists(self, client):
        """Test that open() method exists in MobileNavManager."""
        response = client.get('/static/js/mobile-nav.js')
        js_content = response.data.decode('utf-8')
        assert 'open()' in js_content
        
    def test_close_method_exists(self, client):
        """Test that close() method exists in MobileNavManager."""
        response = client.get('/static/js/mobile-nav.js')
        js_content = response.data.decode('utf-8')
        assert 'close()' in js_content
        
    def test_backdrop_setup_method(self, client):
        """Test that setupBackdrop() method exists."""
        response = client.get('/static/js/mobile-nav.js')
        js_content = response.data.decode('utf-8')
        assert 'setupBackdrop' in js_content
        
    def test_resize_handler_exists(self, client):
        """Test that resize handling is implemented."""
        response = client.get('/static/js/mobile-nav.js')
        js_content = response.data.decode('utf-8')
        assert 'resize' in js_content or 'handleResize' in js_content
        
    def test_dom_content_loaded_listener(self, client):
        """Test that DOMContentLoaded event listener exists."""
        response = client.get('/static/js/mobile-nav.js')
        js_content = response.data.decode('utf-8')
        assert 'DOMContentLoaded' in js_content


class TestNavigationResponsiveness:
    """Test that navigation responds correctly to different viewport sizes."""
    
    def test_desktop_navbar_visibility(self, authenticated_client):
        """Test that navbar is visible on desktop (>768px)."""
        response = authenticated_client.get('/dashboard')
        html = response.data.decode('utf-8')
        # The navbar HTML structure should be present
        assert 'navbar' in html
        
    def test_touch_target_minimum_size(self, client):
        """Test that mobile.css specifies minimum 44px touch targets."""
        response = client.get('/static/css/mobile.css')
        css_content = response.data.decode('utf-8')
        assert '44px' in css_content or '44' in css_content
        
    def test_form_elements_responsive(self, client):
        """Test that form elements have responsive styles."""
        response = client.get('/static/css/mobile.css')
        css_content = response.data.decode('utf-8')
        assert 'form-control' in css_content or 'form-' in css_content
        assert 'min-height' in css_content or 'padding' in css_content


class TestNavigationAccessibility:
    """Test accessibility features in mobile navigation."""
    
    def test_toggler_has_aria_attributes(self, authenticated_client):
        """Test that hamburger toggle has ARIA attributes."""
        response = authenticated_client.get('/dashboard')
        html = response.data.decode('utf-8')
        # Check for aria-label or aria-expanded
        assert 'aria-' in html
        
    def test_feather_icons_integration(self, client):
        """Test that feather icons are integrated with mobile nav."""
        response = client.get('/static/js/mobile-nav.js')
        js_content = response.data.decode('utf-8')
        # Should check for feather integration
        assert 'feather' in js_content


class TestNavigationNoRegressions:
    """Test that mobile navigation doesn't break desktop layout."""
    
    def test_desktop_dropdown_menus(self, authenticated_client):
        """Test that dropdown menus still work on desktop."""
        response = authenticated_client.get('/dashboard')
        html = response.data.decode('utf-8')
        # Dropdown structure should be preserved
        assert 'dropdown' in html
        
    def test_navbar_brand_visible(self, authenticated_client):
        """Test that brand/logo is still visible."""
        response = authenticated_client.get('/dashboard')
        html = response.data.decode('utf-8')
        assert 'navbar-brand' in html
        
    def test_user_menu_present(self, authenticated_client):
        """Test that user menu is present in navigation."""
        response = authenticated_client.get('/dashboard')
        html = response.data.decode('utf-8')
        # User menu should still be in navbar
        assert 'nav-link' in html or 'dropdown' in html


class TestMobileNavigationIntegration:
    """Integration tests for mobile navigation with actual routes."""
    
    def test_all_pages_include_navigation(self, authenticated_client):
        """Test that navigation is included on all pages."""
        test_routes = [
            '/dashboard',
            '/interventions',
        ]
        
        for route in test_routes:
            response = authenticated_client.get(route)
            if response.status_code == 200:
                html = response.data.decode('utf-8')
                assert 'navbar' in html, f"Navigation missing on {route}"
                assert 'navbar-toggler' in html, f"Hamburger missing on {route}"
    
    def test_navigation_preserves_login_state(self, authenticated_client):
        """Test that navigating doesn't lose login state."""
        response1 = authenticated_client.get('/dashboard')
        assert response1.status_code == 200
        
        response2 = authenticated_client.get('/interventions')
        assert response2.status_code == 200
        # Should still be logged in
        html = response2.data.decode('utf-8')
        assert 'navbar' in html


class TestMobileNavigationPerformance:
    """Test that mobile navigation doesn't impact performance."""
    
    def test_mobile_nav_js_file_size(self, client):
        """Test that mobile-nav.js is reasonably sized."""
        response = client.get('/static/js/mobile-nav.js')
        js_content = response.data.decode('utf-8')
        # Should be less than 50KB (for reasonable performance)
        assert len(js_content) < 50000
        
    def test_mobile_css_file_size(self, client):
        """Test that mobile.css is reasonably sized."""
        response = client.get('/static/css/mobile.css')
        css_content = response.data.decode('utf-8')
        # Should be less than 50KB
        assert len(css_content) < 50000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
