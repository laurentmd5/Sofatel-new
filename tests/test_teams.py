from app import app, db
from models import User
from werkzeug.security import generate_password_hash


def test_create_team_page_for_chef_pur():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        user = User(username='chef_test', email='chef_test@example.com', password_hash=generate_password_hash('p'), role='chef_pur', nom='Chef', prenom='ChefPrenom', telephone='0000000000')
        db.session.add(user)
        db.session.commit()

        client = app.test_client()

        # Directly set session to the created user (avoid flaky login redirects)
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)

        r = client.get('/create-team', follow_redirects=True)
        assert r.status_code == 200
        assert b'name="nom_equipe"' in r.data or b'id="nom_equipe"' in r.data
