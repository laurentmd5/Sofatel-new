"""Quick schema checker — run from project root with the application env configured.

Example: FLASK_APP=app.py FLASK_ENV=production python tools/check_schema.py
"""
import sys
from app import create_app, db
from models import DemandeIntervention, Intervention
from sqlalchemy.exc import OperationalError

app = create_app()
app.app_context().push()

errors = []
try:
    # Try simple queries that reference the new columns
    db.session.query(DemandeIntervention.sla_hours_override).limit(1).all()
except OperationalError as e:
    errors.append(str(e))

try:
    db.session.query(Intervention.sla_escalation_level).limit(1).all()
except OperationalError as e:
    errors.append(str(e))

if errors:
    print('Schema problems detected:')
    for err in errors:
        print('-', err)
    print('\nSuggested fix: run the SQL in tools/migrations/0002_add_sla_and_history.sql or run Alembic/Flask-Migrate migration.')
    sys.exit(1)
else:
    print('Schema OK: new SLA fields are present.')
    sys.exit(0)
