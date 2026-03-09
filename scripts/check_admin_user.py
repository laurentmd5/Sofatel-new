from app import app, db
from models import User
from werkzeug.security import check_password_hash

with app.app_context():
    u = User.query.filter_by(username='admin').first()
    if not u:
        print('admin user: NOT FOUND')
    else:
        print('admin user found:')
        print(' id:', u.id)
        print(' username:', u.username)
        print(' email:', u.email)
        print(' role:', u.role)
        print(' actif:', u.actif)
        print(' password_hash:', bool(u.password_hash))
        print(' password matches "admin":', check_password_hash(u.password_hash, 'admin'))

    cps = User.query.filter_by(role='chef_pur').all()
    print('\nchef_pur accounts:')
    for c in cps:
        print(' -', c.username, 'actif=', c.actif)
