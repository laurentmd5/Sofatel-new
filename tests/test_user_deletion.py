from app import app, db
from models import User, DemandeIntervention, Intervention
from werkzeug.security import generate_password_hash
from datetime import datetime


def test_cannot_delete_user_with_dependencies():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        # create chef_pur (admin)
        admin = User(username='admin2', email='admin2@example.com', password_hash=generate_password_hash('admin'), role='chef_pur', nom='Admin', prenom='Admin', telephone='000')
        db.session.add(admin)
        db.session.commit()

        # create technicien user
        tech = User(username='tech1', email='tech1@example.com', password_hash=generate_password_hash('pass'), role='technicien', nom='Tech', prenom='One', telephone='111')
        db.session.add(tech)
        db.session.commit()

        # create a demande and an intervention assigned to tech
        demande = DemandeIntervention(nd='ND001', zone='Dakar', type_techno='Fibre', nom_client='Client', date_demande_intervention=datetime.now(), service='SAV')
        db.session.add(demande)
        db.session.commit()

        intervention = Intervention(demande_id=demande.id, technicien_id=tech.id, statut='en_cours', date_debut=datetime.now())
        db.session.add(intervention)
        db.session.commit()

        # authenticate as admin in test client
        client = app.test_client()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin.id)
            sess['_fresh'] = True

        # attempt deletion
        resp = client.post(f'/delete-user/{tech.id}')
        assert resp.status_code == 400
        data = resp.get_json()
        assert data and data.get('success') == False
        assert 'dépendances' in data.get('error') or 'Impossible' in data.get('error')

        # Add an activity log and verify deletion is blocked and message mentions activity history
        from models import ActivityLog
        activity = ActivityLog(user_id=tech.id, action='login', module='auth')
        db.session.add(activity)
        db.session.commit()

        resp_act = client.post(f'/delete-user/{tech.id}')
        assert resp_act.status_code == 400
        data_act = resp_act.get_json()
        assert data_act and data_act.get('success') == False
        assert 'activit' in data_act.get('error') or 'historique' in data_act.get('error')

        # attempt successful deletion of a user without dependencies
        tech2 = User(username='tech2', email='tech2@example.com', password_hash=generate_password_hash('pass'), role='technicien', nom='Tech', prenom='Two', telephone='222')
        db.session.add(tech2)
        db.session.commit()

        resp2 = client.post(f'/delete-user/{tech2.id}')
        assert resp2.status_code == 200
        data2 = resp2.get_json()
        assert data2 and data2.get('success') == True

        db.session.remove()
        db.drop_all()
