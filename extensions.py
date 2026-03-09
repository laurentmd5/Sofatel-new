from datetime import datetime
from flask import current_app
from markupsafe import Markup
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_apscheduler import APScheduler
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from flask_caching import Cache
import re
import os

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
scheduler = APScheduler()
migrate = Migrate()
csrf = CSRFProtect()
cors = CORS()

# Redis Cache Configuration
cache = Cache()
REDIS_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_HOST': os.getenv('REDIS_HOST', 'localhost'),
    'CACHE_REDIS_PORT': int(os.getenv('REDIS_PORT', 6379)),
    'CACHE_REDIS_DB': int(os.getenv('REDIS_DB', 0)),
    'CACHE_REDIS_PASSWORD': os.getenv('REDIS_PASSWORD', None),
    'CACHE_DEFAULT_TIMEOUT': int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300)),  # 5 min default
    'CACHE_KEY_PREFIX': 'sofatelcom_',
}

def format_datetime(value, format='%d/%m/%Y %H:%M'):
    """Format a datetime object to a string.
    
    Args:
        value: The datetime object to format
        format: The format string (default: '%d/%m/%Y %H:%M')
    """
    if value is None:
        return ''
    return value.strftime(format)

def nl2br(value):
    """Convert newlines to <br> tags in template strings.
    
    Args:
        value: The string to convert
    """
    if value is None:
        return ''
    # Échapper le contenu pour éviter les injections XSS
    escaped = str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    # Convertir les retours à la ligne en <br>
    result = re.sub(r'\r\n|\r|\n', '<br>', escaped)
    # Marquer comme sûr pour éviter l'échappement HTML supplémentaire
    return Markup(result)

def init_app(app):
    """Register template filters, CORS and Redis Cache with the Flask app."""
    app.jinja_env.filters['format_datetime'] = format_datetime
    app.jinja_env.filters['nl2br'] = nl2br
    
    # Initialize Redis Cache with fallback to simple cache if Redis unavailable
    try:
        app.config.update(REDIS_CONFIG)
        cache.init_app(app)
        # Test Redis connection
        with app.app_context():
            cache.get('test_connection')
        print("[Cache] Redis cache initialized successfully")
    except Exception as e:
        print(f"[Cache] WARNING - Redis connection failed: {e}")
        print("[Cache] Falling back to simple in-memory cache")
        # Fallback to simple cache
        app.config['CACHE_TYPE'] = 'simple'
        cache.init_app(app)
    
    # Initialiser CORS AVANT tout pour accepter les requêtes cross-origin
    # Configuration CORS très permissive pour le développement
    cors.init_app(app, 
        resources={
            r"/api/*": {
                "origins": "*",
                "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
                "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "X-CSRFToken", "Accept"],
                "expose_headers": ["Content-Type", "X-Total-Count", "X-Page-Count"],
                "max_age": 86400,
                "supports_credentials": True
            }
        },
        intercept_exceptions=False
    )
