"""Run lightweight validation checks against the local Flask app using its test client.

Usage:
  python tools/validation/run_validation.py --db tests/test_data.sqlite --output rapport.json

Produces a JSON report indicating pass/fail for each axis.
"""
import argparse
import json
from app import app
from extensions import db
from werkzeug.security import generate_password_hash
from datetime import datetime

REPORT = {'date': datetime.utcnow().isoformat(), 'results': {}}


def do_checks(db_path):
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    with app.app_context():
        # Ensure DB exists
        # Note: this script assumes setup_test_data.py has been run
        client = app.test_client()

        # Auth checks
        r = client.post('/login', data={'username': 'admin', 'password': 'pass'})
        REPORT['results']['auth_admin_login'] = {'status': r.status_code == 302, 'code': r.status_code}

        # Mobile JWT login
        r2 = client.post('/api/mobile/login', json={'username': 'tech', 'password': 'pass'})
        REPORT['results']['mobile_login'] = {'status': r2.status_code in (200, 201), 'code': r2.status_code}

        # Create intervention via web
        # login as admin first via client
        client.post('/login', data={'username': 'admin', 'password': 'pass'})
        # pick a demande (create one if none exist)
        from models import DemandeIntervention
        d = DemandeIntervention.query.first()
        if not d:
            d = DemandeIntervention(nd='ND-VAL', zone='ZoneTest', type_techno='Fibre', nom_client='ClientVal', date_demande_intervention=datetime.utcnow(), service='SAV')
            db.session.add(d)
            db.session.commit()
        resp = client.post('/interventions/creer', data={'demande_id': str(d.id)}, follow_redirects=True)
        REPORT['results']['web_create_intervention'] = {'status': resp.status_code == 200, 'code': resp.status_code}

        # SSE check (once)
        r3 = client.get('/api/stream/interventions?once=1&interval=0')
        REPORT['results']['sse_once'] = {'status': r3.status_code == 200, 'code': r3.status_code}

        # Completeness check
        # get an intervention id
        from models import Intervention
        it = Intervention.query.filter(Intervention.photos != None).first()
        if it:
            rc = client.get(f'/api/intervention/{it.id}/completude')
            REPORT['results']['completeness'] = {'status': rc.status_code == 200, 'code': rc.status_code, 'body': rc.get_json()}
        else:
            REPORT['results']['completeness'] = {'status': False, 'reason': 'no intervention with photos'}

        # Stock stats
        rs = client.get('/gestion-stock/api/stats/stock')
        REPORT['results']['stock_stats'] = {'status': rs.status_code == 200, 'code': rs.status_code}

        # RH leave create
        rlr = client.post('/conges', json={'technicien_id': 1, 'date_debut': datetime.utcnow().date().isoformat(), 'date_fin': (datetime.utcnow().date()).isoformat(), 'type': 'conges'})
        REPORT['results']['rh_create_leave'] = {'status': rlr.status_code in (200,201), 'code': rlr.status_code}

    return REPORT


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default='tests/test_data.sqlite')
    parser.add_argument('--output', default='reports/rapport.json')
    args = parser.parse_args()

    report = do_checks(args.db)
    import os
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    print(f'Wrote report to {args.output}')
