import sys, os
# Ensure project root is on sys.path when running from scripts/
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app import app
print('BLUEPRINTS:', sorted(list(app.blueprints.keys())))
import routes
print('HOOKS:', 'check_interventions_delayed' in dir(routes), 'check_interventions_deadline' in dir(routes))
