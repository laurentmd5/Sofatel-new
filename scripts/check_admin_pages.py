#!/usr/bin/env python
from app import app
from models import User

app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    client = app.test_client()
    u = User.query.filter_by(username='admin').first()
    print('admin exists:', bool(u))
    if u:
        rv = client.post('/login', data={'username':'admin','password':'admin'}, follow_redirects=True)
        print('login status', rv.status_code, 'final path', getattr(rv.request, 'path', None))

        for path in ['/create-user','/manage-users','/connection-history']:
            r = client.get(path, follow_redirects=False)
            print(path, '->', r.status_code, 'location' if r.status_code in (301,302) else '', r.headers.get('Location'))
            if r.status_code == 200:
                print('-- body starts with --')
                print(r.get_data(as_text=True)[:200])
    else:
        print('admin missing; cannot fully test admin pages')
