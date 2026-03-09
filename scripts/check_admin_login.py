#!/usr/bin/env python
from app import app, db
from models import User
from werkzeug.security import check_password_hash
import traceback

# Disable CSRF for the test client
app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    u = User.query.filter_by(username='admin').first()
    print('user found:', bool(u))
    if u:
        print('id:', u.id, 'actif:', u.actif, 'has_password_hash:', bool(u.password_hash))
        try:
            print('password matches admin:', check_password_hash(u.password_hash, 'admin'))
        except Exception as e:
            print('password check error:', e)

    client = app.test_client()

    try:
        r = client.post('/login', data={'username':'admin', 'password':'admin'}, follow_redirects=False)
        print('\nPOST /login ->', r.status_code)
        print('Location header:', r.headers.get('Location'))
        if r.status_code in (302, 303) and r.headers.get('Location'):
            loc = r.headers.get('Location')
            rr = client.get(loc)
            print('GET', loc, '->', rr.status_code)
    except Exception:
        print('Exception during POST (no follow):')
        traceback.print_exc()

    try:
        r2 = client.post('/login', data={'username':'admin', 'password':'admin'}, follow_redirects=True)
        print('\nPOST /login (follow) ->', r2.status_code)
        try:
            print('final request path:', r2.request.path)
        except Exception:
            print('no request.path')
        print('response length:', len(r2.data))
        print('\nresponse snippet:\n')
        print(r2.data.decode('utf-8')[:2000])
    except Exception:
        print('Exception during POST (follow):')
        traceback.print_exc()