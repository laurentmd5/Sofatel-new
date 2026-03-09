#!/bin/bash
# Entrypoint script for SOFATELCOM Docker container
# Handles database migrations and server startup

set -e

echo "[SOFATELCOM] Starting initialization..."

# Attendre que MySQL soit prêt
echo "[SOFATELCOM] Waiting for MySQL to be ready..."
while ! nc -z db 3306; do
  sleep 1
done
echo "[SOFATELCOM] MySQL is ready!"

# Attendre que Redis soit prêt
echo "[SOFATELCOM] Waiting for Redis to be ready..."
while ! nc -z redis 6379; do
  sleep 1
done
echo "[SOFATELCOM] Redis is ready!"

# Exécuter les migrations Alembic
echo "[SOFATELCOM] Running database migrations..."
flask db upgrade || echo "[SOFATELCOM] Migrations skipped or already done"

# Créer les tables si nécessaire
echo "[SOFATELCOM] Initializing database tables..."
python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('[SOFATELCOM] Database tables initialized')
"

# Démarrer l'application avec Gunicorn en production
if [ "$FLASK_ENV" = "production" ]; then
    echo "[SOFATELCOM] Starting with Gunicorn (production)..."
    exec gunicorn \
        --workers 4 \
        --worker-class sync \
        --worker-connections 1000 \
        --max-requests 1000 \
        --max-requests-jitter 50 \
        --timeout 60 \
        --bind 0.0.0.0:5000 \
        --access-logfile - \
        --error-logfile - \
        --log-level info \
        app:app
else
    echo "[SOFATELCOM] Starting with Flask development server..."
    exec python app.py
fi
