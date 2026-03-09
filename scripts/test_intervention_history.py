from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Ensure a chef_pur user exists
    u = User.query.filter_by(username='admin').first()
    if not u:
        u = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin'),
            role='chef_pur',
            nom='Admin',
            prenom='Admin',
            actif=True
        )
        db.session.add(u)
        db.session.commit()
        print('Created admin user')
    else:
        print('Admin user exists')

    client = app.test_client()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(u.id)
        sess['_fresh'] = True

    resp = client.get('/intervention_history')
    print('/intervention_history ->', resp.status_code)
    content = resp.get_data(as_text=True)
    if 'Historique des interventions' in content:
        print('intervention_history page rendered')
    else:
        print('intervention_history page NOT rendered; first 200 chars:\n', content[:200])
