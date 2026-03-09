#!/usr/bin/env python
from app import app, db
from models import User
from werkzeug.security import check_password_hash
import json

# Disable CSRF for programmatic test client
app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    print('--- Routes containing "notifications" ---')
    found = False
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        if 'notifications' in rule.rule or 'notifications' in rule.endpoint:
            print(rule.rule, '->', rule.endpoint, 'methods', sorted(rule.methods))
            found = True
    if not found:
        print('(none found containing "notifications")')

    print('\n--- Total routes:', len(list(app.url_map.iter_rules())), ')')

    client = app.test_client()

    print('\nGET /api/notifications (anonymous):')
    r = client.get('/api/notifications')
    print('status', r.status_code)
    print('headers:', {k: v for k, v in r.headers.items() if k in ('Location', 'Content-Type')})
    try:
        print('body snippet:', r.get_data(as_text=True)[:800])
    except Exception as e:
        print('body snippet error:', e)

    u = User.query.filter_by(username='admin').first()
    print('\nUser admin exists:', bool(u))
    if u:
        print('id', u.id, 'actif', u.actif)
        # Try to login with test client
        rv = client.post('/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
        print('\nPOST /login (follow) -> status', rv.status_code)
        try:
            print('final path', rv.request.path)
        except Exception:
            print('no request.path')
        # Now try to access notifications as logged-in user
        r2 = client.get('/api/notifications')
        print('\nGET /api/notifications (logged-in) ->', r2.status_code)
        try:
            print('response json:', json.dumps(r2.get_json(), ensure_ascii=False, indent=2))
        except Exception:
            print('response text:', r2.get_data(as_text=True)[:800])
    else:
        print('\nAdmin user not found; skipping logged-in test. If you want, I can create a temp admin for local debugging.')
