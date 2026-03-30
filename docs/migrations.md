# Database migration instructions

If you see runtime errors mentioning missing columns (OperationalError), it means the database schema is out of sync with the application models.

Quick steps to fix (MySQL):

1. Backup your database (always):
   - mysqldump -u <user> -p <db_name> > backup_before_migration.sql

2. Check current schema with the helper script (optional):
   - FLASK_APP=app.py python tools/check_schema.py

3. Apply the SQL helper (provided):
   - mysql -u <user> -p <db_name> < tools/migrations/0002_add_sla_and_history.sql

   Or, if you use Flask-Migrate/Alembic in your environment:
   - flask db migrate -m "Add SLA fields and intervention_history"
   - flask db upgrade

4. Restart the Flask application / WSGI server so SQLAlchemy picks up the changes.

5. Verify by running the schema check script again or perform a quick smoke test (login and visit /dashboard, /dispatching).

Notes:
- The SQL file adds columns that are nullable or have safe defaults (avoid blocking writes).
- If you're in a multi-instance production environment, perform the migration on a single instance's DB and drain traffic if necessary.
- If you prefer, create an Alembic migration to keep schema changes under version control.
