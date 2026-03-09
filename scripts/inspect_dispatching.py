#!/usr/bin/env python
from app import app, db
from models import User
import traceback

# Prepare test environment
app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True

with app.app_context():
    print('--- Routes containing "dispatch" ---')
    found = False
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        if 'dispatch' in rule.rule or 'dispatch' in rule.endpoint:
            print(rule.rule, '->', rule.endpoint, 'methods', sorted(rule.methods))
            found = True
    if not found:
        print('(none found containing "dispatch")')

    client = app.test_client()

    print('\nGET /dispatching (anonymous):')
    try:
        r = client.get('/dispatching')
        print('status', r.status_code)
        print('headers:', {k: v for k, v in r.headers.items() if k in ('Location', 'Content-Type')})
        print('body snippet:', r.get_data(as_text=True)[:2000])
    except Exception:
        print('Exception during GET /dispatching:')
        traceback.print_exc()

    # If admin exists, try a logged-in request
    u = User.query.filter_by(username='admin').first()
    print('\nUser admin exists:', bool(u))
    if u:
        # login via test client
        rv = client.post('/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
        print('\nPOST /login (follow) -> status', rv.status_code)
        try:
            print('final path', rv.request.path)
        except Exception:
            print('no request.path')

        print('\nGET /dispatching (logged-in):')
        try:
            r2 = client.get('/dispatching')
            print('status', r2.status_code)
            print('body snippet:', r2.get_data(as_text=True)[:2000])
        except Exception:
            print('Exception during GET /dispatching (logged-in):')
            traceback.print_exc()
    else:
        print('\nAdmin not found; skip logged-in test. Consider creating an admin for debugging.')
