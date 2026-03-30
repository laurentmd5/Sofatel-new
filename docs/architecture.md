# Architecture de l'application

## Vue d'ensemble
L'application est organisée selon une architecture typique Flask monolithique :
- `app.py` initialise l'application, les extensions (SQLAlchemy, Flask-Login, Mail, Migrate, APScheduler), et enregistre les blueprints.
- Les routes sont organisées entre `routes.py` (fonctions principales) et plusieurs fichiers `routes_*` (ex: `routes_stock.py`, `routes_interventions.py`) implémentant des blueprints.
- `models.py` contient les modèles principaux (User, DemandeIntervention, FichierImport, Equipe, Survey, FicheTechnique, etc.).
- `utils.py` contient des fonctions transverses (statistiques, import Excel, envoi SMS via l'API Orange, logging d'activité).

## Composants clés
- Authentification & gestion des sessions : `Flask-Login` + `flask_session` (session filesystem par défaut)
- CSRF : `Flask-WTF` (via `CSRFProtect` dans `extensions.py`)
- Tâches planifiées : `APScheduler` (tâches définies dans `app.py` exécutées dans l'app context)
- Migrations : `Flask-Migrate` + Alembic

## Blueprints et endpoints importants
- `stock_bp` — préfixe `/gestion-stock`
- `categories_bp` — préfixe `/api`
- `interventions` — préfixe `/interventions`
- `reservations` — préfixe `/reservations`

Endpoints clés (exemples)
- `GET /` → redirige vers `dashboard` (auth requis)
- `POST /login` → authentification
- `POST /api/publish-selected-teams` → publication d'équipes (AJAX)
- `POST /api/unpublish-selected-teams` → dé-publication d'équipes (AJAX)
- `POST /survey/create` → création de survey (upload photo possible)

## Notes d'exécution (scheduler)
Le scheduler `APScheduler` est initialisé dans `app.py` et démarré si `not scheduler.running`. Attention en production à ne pas exécuter plusieurs workers qui démarrent chacun le scheduler (double exécution). Solutions : exécuter le scheduler dans un processus dédié ou utiliser un verrou Redis / base pour garantir l'unicité.
