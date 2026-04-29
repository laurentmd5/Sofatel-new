"""
Initialisation du package routes/ — crée et enregistre les blueprints et routes.
"""

from .auth import register_auth_blueprint
from .surveys import surveys_bp
from .dispatch import dispatch_bp
from .teams import teams_bp
from flask import redirect, url_for, jsonify, current_app, request
import os


def register_blueprints(app):
    """
    Enregistre tous les blueprints et routes sur l'application.
    Appel simple et explicite — pas d'import dynamique.
    """
    # Enregistrer les routes d'authentification
    register_auth_blueprint(app)
    
    # Enregistrer les blueprints
    app.register_blueprint(surveys_bp)
    app.register_blueprint(dispatch_bp)
    app.register_blueprint(teams_bp)

    # Mobile API blueprint (JWT auth + mobile endpoints)
    try:
        from .mobile import mobile_bp
        app.register_blueprint(mobile_bp)
    except Exception:
        # If mobile module is missing or has import errors, skip registration to allow legacy tests to run
        current_app.logger.exception('Failed to register mobile blueprint')

    # SLA enforcement API
    try:
        from .sla import sla_bp
        app.register_blueprint(sla_bp)
    except Exception:
        current_app.logger.exception('Failed to register sla blueprint')

    # Completeness API (intervention completeness KPI)
    try:
        from .completeness import bp as completeness_bp
        app.register_blueprint(completeness_bp)
    except Exception:
        current_app.logger.exception('Failed to register completeness blueprint')

    # Stream (SSE) API for real-time dashboard updates
    try:
        from .stream import stream_bp
        app.register_blueprint(stream_bp)
    except Exception:
        current_app.logger.exception('Failed to register stream blueprint')
    
    # Audit admin interface (compliance and debugging)
    try:
        from .audit_admin import audit_admin_bp
        app.register_blueprint(audit_admin_bp)
    except Exception:
        current_app.logger.exception('Failed to register audit admin blueprint')

    # Compatibilité : exposer quelques endpoints top-level anciens (facilite templates existants)
    @app.route('/import-demandes')
    def import_demandes():
        # Redirige vers l'implémentation dans le blueprint dispatch
        return redirect(url_for('dispatch.import_demandes'))

    @app.route('/dispatching')
    def dispatching():
        # Redirige vers le blueprint dispatch
        return redirect(url_for('dispatch.dispatching'))

    @app.route('/intervention-history')
    @app.route('/intervention_history')
    def intervention_history():
        # Prefer the legacy implementation if present to keep existing behaviour.
        view = app.view_functions.get('legacy.intervention_history')
        if view:
            return view()
        return redirect(url_for('dashboard'))

    # Minimal notifications endpoint for compatibility / smoke tests
    from flask_login import current_user

    @app.route('/api/notifications')
    def api_notifications():
        # Check authentication without redirect - return JSON 401 instead
        if not current_user.is_authenticated:
            return jsonify({'error': 'Unauthorized', 'notifications': []}), 401
        
        # If a legacy implementation exists, delegate to it
        view = app.view_functions.get('legacy.api_notifications') or app.view_functions.get('api_notifications')
        if view and view is not api_notifications:
            return view()
        # Default: return empty list for authenticated users
        return jsonify({'notifications': []})

    @app.route('/create-team')
    @app.route('/create_team')
    def create_team():
        return redirect(url_for('teams.create_team'))

    # Les autres blueprints (stock, interventions, reservations, categories, api_docs)
    # sont déjà enregistrés dans app.py — cette fonction complète avec auth et les trois modules.

    # Charger le module legacy `routes.py` pour enregistrer les anciennes routes
    # qui n'ont pas été extraites dans des blueprints. Cela permet de garder
    # la compatibilité avec les templates existants sans dupliquer le code.
    try:
        import importlib.util
        legacy_path = os.path.join(os.path.dirname(__file__), '..', 'routes.py')
        legacy_path = os.path.abspath(legacy_path)
        if os.path.exists(legacy_path):
            # To avoid endpoint name collisions (e.g., `index`), temporarily wrap
            # `app.route` so legacy routes register with a `legacy.` endpoint prefix.
            real_route = app.route

            def make_route_wrapper(real_route):
                def route_wrapper(rule, **options):
                    def decorator(f):
                        endpoint = options.get('endpoint', f.__name__)
                        options2 = dict(options)
                        options2['endpoint'] = f'legacy.{endpoint}'
                        return real_route(rule, **options2)(f)
                    return decorator
                return route_wrapper

            app.route = make_route_wrapper(real_route)
            try:
                spec = importlib.util.spec_from_file_location('legacy_routes', legacy_path)
                legacy = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(legacy)
            finally:
                # restore original app.route
                app.route = real_route
            
            # Créer des wrappers simples qui redirigent vers les endpoints legacy pour les 3 routes d'administration
            @app.route('/create-user')
            @app.route('/create_user')
            def create_user():
                return redirect(url_for('legacy.create_user'))
            
            @app.route('/manage-users')
            @app.route('/manage_users')
            def manage_users():
                return redirect(url_for('legacy.manage_users', **request.args))
            
            @app.route('/edit-user/<int:user_id>', methods=['GET', 'POST'])
            @app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
            def edit_user(user_id):
                return redirect(url_for('legacy.edit_user', user_id=user_id))
            
            @app.route('/connection-history')
            @app.route('/connection_history')
            def connection_history():
                return redirect(url_for('legacy.connection_history', **request.args))
    except Exception as e:
        app.logger.warning(f'Impossible de charger legacy routes: {e}')
