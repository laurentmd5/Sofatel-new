from datetime import datetime, timedelta
import os
import logging
import atexit
from dotenv import load_dotenv
from flask import Flask, session
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_wtf.csrf import CSRFProtect
import sys

# Import des extensions depuis le nouveau fichier (y compris CSRF et Cache)
from extensions import db, login_manager, mail, scheduler, migrate, init_app, csrf, cache
# NOTE: Use the single CSRFProtect instance from `extensions` to avoid duplicate instances which
# can cause @csrf.exempt() in other modules to be ineffective.
# NOTE: Use the single Cache instance for Redis/in-memory caching across the entire app.

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Chargement des variables d'environnement
load_dotenv()

# Create the app
app = Flask(__name__)

# Initialize template filters
init_app(app)
app.secret_key = os.getenv("SESSION_SECRET", "SECRET_KEY")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=6)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# Configuration email
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = os.getenv('MAIL_PORT')
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS')
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

# Configure the database
# When running under pytest, prefer an in-memory SQLite DB to avoid
# connecting to the real MySQL/Postgres instance and to allow tests to
# override config safely.

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

# Configuration de la session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
app.config['SESSION_COOKIE_SECURE'] = False  # Mettre à True en production avec HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Configuration CSRF
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_SECRET_KEY'] = os.getenv('CSRF_SECRET_KEY', os.urandom(24).hex())
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 heure en secondes
app.config['WTF_CSRF_CHECK_DEFAULT'] = False  # Désactive la vérification CSRF par défaut
app.config['WTF_CSRF_SSL_STRICT'] = False  # Désactive la vérification SSL stricte

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
mail.init_app(app)
scheduler.init_app(app)
migrate.init_app(app, db)
Session(app)  # Initialisation de la session

# Initialisation de CSRF avec l'application
csrf.init_app(app)



# Désactiver CSRF pour les routes API
csrf.exempt('publish_selected_teams')
csrf.exempt('unpublish_selected_teams')  # Désactive CSRF pour la fonction de dépublication

# Middleware pour ajouter les en-têtes CORS à TOUTES les réponses
@app.after_request
def add_cors_headers(response):
    """Add CORS headers to all responses for WebView compatibility."""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, X-CSRFToken, Accept'
    response.headers['Access-Control-Expose-Headers'] = 'Content-Type, X-Total-Count, X-Page-Count'
    response.headers['Access-Control-Max-Age'] = '86400'
    
    # Supprimer l'en-tête problématique que chromium n'aime pas
    if 'Content-Length' in response.headers and response.content_type == 'text/html':
        # Pour les pages HTML, recalculer le Content-Length si l'encodage GZIP n'est pas appliqué
        if 'gzip' not in response.headers.get('Content-Encoding', ''):
            try:
                data = response.get_data()
                response.headers['Content-Length'] = len(data)
            except:
                pass
    
    return response

login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return db.session.get(User, int(user_id))

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Import des modèles après la création de l'application
from models import User  # Import ici pour éviter l'importation circulaire

with app.app_context():
    # Créer toutes les tables de la base de données
    db.create_all()
    
    # Importer et enregistrer les routes après la création de l'application (dans app context)
    try:
        # Import blueprints registration from the routes package
        import routes as routes_package
        if hasattr(routes_package, 'register_blueprints'):
            routes_package.register_blueprints(app)
    except Exception as e:
        app.logger.error(f"Failed to register blueprints: {e}")
        import traceback
        traceback.print_exc()
    
    # Importer les autres blueprints
    from routes_stock import stock_bp
    from routes_categories import categories_bp
    # Import des routes de documentation OpenAPI/Swagger
    try:
        from routes_api_docs import api_docs_bp
    except Exception:
        api_docs_bp = None
    # Les blueprints sont importés avec des alias pour éviter les conflits
    from routes_interventions import interventions_bp as interventions_blueprint
    from routes_reservations import reservations_bp as reservations_blueprint
    # RH blueprint (minimal)
    try:
        from routes.rh import rh_bp as rh_blueprint
    except Exception:
        rh_blueprint = None
    # RH Notifications - schedule leave reminders
    try:
        from rh_utils.rh_notifications import schedule_leave_reminders
    except Exception as e:
        app.logger.warning(f"Could not import rh_notifications: {e}")
        schedule_leave_reminders = None
    # Streaming/Real-time blueprint
    try:
        from routes.stream import stream_bp as stream_blueprint
    except Exception as e:
        app.logger.warning(f"Could not import stream_bp: {e}")
        stream_blueprint = None
    # KPI blueprint
    try:
        from routes.kpi_routes import kpi_bp as kpi_blueprint
    except Exception as e:
        app.logger.warning(f"Could not import kpi_blueprint: {e}")
        kpi_blueprint = None
    
    # NumeroSerie blueprint (Phase 3)
    try:
        from routes_numeroserie import numeroserie_bp
    except Exception as e:
        app.logger.warning(f"Could not import numeroserie_bp: {e}")
        numeroserie_bp = None
    
    # Enregistrer les Blueprints
    if 'stock' not in app.blueprints:
        app.register_blueprint(stock_bp, url_prefix='/gestion-stock')
    
    if 'categories' not in app.blueprints:
        app.register_blueprint(categories_bp, url_prefix='/api')
    
    # Vérifier si les blueprints ne sont pas déjà enregistrés
    if 'interventions' not in app.blueprints:
        app.register_blueprint(interventions_blueprint, url_prefix='/interventions')
    if 'reservations' not in app.blueprints:
        app.register_blueprint(reservations_blueprint, url_prefix='/reservations')
    if rh_blueprint and 'rh' not in app.blueprints:
        app.register_blueprint(rh_blueprint, url_prefix='/api/rh')
    if stream_blueprint and 'stream' not in app.blueprints:
        app.register_blueprint(stream_blueprint, url_prefix='/api')
    if kpi_blueprint and 'kpi' not in app.blueprints:
        app.register_blueprint(kpi_blueprint, url_prefix='/api/kpi')
    
    if numeroserie_bp and 'numeroserie' not in app.blueprints:
        app.register_blueprint(numeroserie_bp)

    # Enregistrer le blueprint de la documentation si disponible
    if api_docs_bp and 'api_docs' not in app.blueprints:
        app.register_blueprint(api_docs_bp)

    # Configuration des tâches planifiées
    @scheduler.task('interval', id='check_delays', hours=1)
    def check_delays():
        with app.app_context():
            try:
                from routes import check_interventions_delayed
                check_interventions_delayed()
                app.logger.info("Vérification des interventions en retard terminée")
            except Exception as e:
                app.logger.error(f"Erreur lors de la vérification des retards: {str(e)}")

    @scheduler.task('cron', id='check_deadlines', hour=9, minute=0)
    def check_deadlines():
        with app.app_context():
            try:
                from routes import check_interventions_deadline
                check_interventions_deadline()
                app.logger.info("Vérification des échéances terminée")
            except Exception as e:
                app.logger.error(f"Erreur lors de la vérification des échéances: {str(e)}")

    @scheduler.task('interval', id='sla_check', hours=1)
    def scheduled_sla_check():
        """Hourly job to detect SLA violations and send alerts."""
        with app.app_context():
            try:
                from sla_utils import run_sla_check
                alerted, total = run_sla_check(send_alerts=True, send_email=False)
                app.logger.info(f"SLA check finished: {total} violations found, {alerted} alerts sent")
            except Exception as e:
                app.logger.error(f"Error during scheduled SLA check: {str(e)}")

    @scheduler.task('cron', id='daily_import', 
                    hour=int(os.getenv('IMPORT_SCHEDULE_HOUR', 6)),
                    minute=int(os.getenv('IMPORT_SCHEDULE_MINUTE', 0)))
    def scheduled_daily_import():
        """
        Daily scheduled job to import intervention requests from file.
        
        Runs at configured time (default: 6:00 AM UTC) in production only.
        
        Configuration via environment variables:
        - IMPORT_SCHEDULE_HOUR: Hour to run (0-23, default: 6)
        - IMPORT_SCHEDULE_MINUTE: Minute to run (0-59, default: 0)
        - IMPORT_FILE_PATH: Source file path (default: /uploads/daily_import.xlsx)
        - IMPORT_SERVICE: Service type (SAV/Production, default: SAV)
        
        Only runs in production environment (FLASK_ENV=production).
        """
        # Environment guard: only run in production
        env = os.getenv('FLASK_ENV', 'development')
        if env != 'production':
            app.logger.debug(f"[IMPORT] Skipping daily import in {env} environment")
            return
        
        with app.app_context():
            try:
                from models import User, FichierImport
                from utils import process_excel_file
                
                import_path = os.getenv('IMPORT_FILE_PATH', os.path.join(
                    app.config['UPLOAD_FOLDER'], 'daily_import.xlsx'
                ))
                import_service = os.getenv('IMPORT_SERVICE', 'SAV')
                
                app.logger.info(f"[IMPORT] Starting daily import job at {datetime.now()}")
                
                # Validate file exists
                if not os.path.exists(import_path):
                    app.logger.warning(f"[IMPORT] Import file not found: {import_path}")
                    return
                
                # Get system user (or create if missing)
                system_user = User.query.filter_by(username='system').first()
                if not system_user:
                    app.logger.error("[IMPORT] System user not found - cannot proceed with import")
                    return
                
                # Process the import
                result = process_excel_file(import_path, import_service, system_user.id)
                
                if result['success']:
                    app.logger.info(
                        f"[IMPORT] SUCCESS: {result['nb_lignes']} records processed, "
                        f"{result['nb_erreurs']} errors | Service: {import_service}"
                    )
                    
                    # Log to activity log if applicable
                    try:
                        from utils import log_activity
                        log_activity(
                            user_id=system_user.id,
                            action='import_scheduled',
                            module='demandes',
                            entity_name=f"Scheduled Import ({import_service})",
                            details={
                                'nb_lignes': result['nb_lignes'],
                                'nb_erreurs': result['nb_erreurs'],
                                'service': import_service,
                                'source': import_path
                            }
                        )
                    except Exception as log_err:
                        app.logger.warning(f"[IMPORT] Could not log activity: {str(log_err)}")
                else:
                    app.logger.error(f"[IMPORT] FAILED: {result['error']}")
                    # Log failure
                    try:
                        from utils import log_activity
                        log_activity(
                            user_id=system_user.id,
                            action='import_failed',
                            module='demandes',
                            entity_name=f"Scheduled Import ({import_service})",
                            details={'error': result['error']}
                        )
                    except Exception as log_err:
                        app.logger.warning(f"[IMPORT] Could not log failure: {str(log_err)}")
                        
            except Exception as e:
                app.logger.error(f"[IMPORT] EXCEPTION: {str(e)}", exc_info=True)

    # Schedule RH leave reminders (7-day notifications)
    if schedule_leave_reminders:
        try:
            schedule_leave_reminders()
            app.logger.info("RH leave reminders scheduled successfully")
        except Exception as e:
            app.logger.warning(f"Could not schedule leave reminders: {e}")

    # Schedule daily KPI calculation (at 2:00 AM UTC)
    @scheduler.task('cron', id='daily_kpi_calculation', hour=2, minute=0)
    def scheduled_kpi_calculation():
        """Daily job to calculate KPI scores for all technicians"""
        with app.app_context():
            try:
                from kpi_engine import calculate_daily_kpi
                calculate_daily_kpi()
                app.logger.info("Daily KPI calculation completed successfully")
            except Exception as e:
                app.logger.error(f"Error during daily KPI calculation: {str(e)}")

    if not scheduler.running:
        try:
            scheduler.start()
            app.logger.info("APScheduler démarré avec succès")
        except Exception as e:
            app.logger.error(f"Erreur lors du démarrage du scheduler: {str(e)}")

    def shutdown_scheduler():
        if scheduler.running:
            scheduler.shutdown()
    
    atexit.register(shutdown_scheduler)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)