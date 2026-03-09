import pytest
from app import app, db
from models import User, Intervention, DemandeIntervention
import sla_utils
from datetime import timedelta
from sla_utils import _now_utc


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_sla_override_respected(client):
    with app.app_context():
        from werkzeug.security import generate_password_hash
        tech = User(username='t1', email='t1@example.com', password_hash=generate_password_hash('pwd'), role='technicien', nom='Tech', prenom='User', telephone='000')
        db.session.add(tech)
        db.session.commit()

        from datetime import datetime
        demande = DemandeIntervention(
            nd='ND-001',
            zone='Z1',
            type_techno='Fibre',
            nom_client='Client A',
            date_demande_intervention=datetime.utcnow(),
            service='SAV',
            priorite_traitement='normal',
            sla_hours_override=1
        )
        db.session.add(demande)
        db.session.commit()

        # Create intervention older than 2 hours -> override=1 should mark it as violating
        inter = Intervention(demande_id=demande.id, technicien_id=tech.id, statut='en_cours')
        # force creation time 2 hours in the past
        inter.date_creation = _now_utc() - timedelta(hours=2)
        db.session.add(inter)
        db.session.commit()

        i = db.session.get(Intervention, inter.id)
        assert sla_utils.check_intervention_sla(i) is True


def test_run_sla_check_and_backoff(client):
    with app.app_context():
        from werkzeug.security import generate_password_hash
        tech = User(username='t2', email='t2@example.com', password_hash=generate_password_hash('pwd'), role='technicien', nom='Tech', prenom='User', telephone='000')
        db.session.add(tech)
        db.session.commit()

        from datetime import datetime
        demande = DemandeIntervention(
            nd='ND-002',
            zone='Z1',
            type_techno='Fibre',
            nom_client='Client B',
            date_demande_intervention=datetime.utcnow(),
            service='SAV',
            priorite_traitement='urgent'
        )
        db.session.add(demande)
        db.session.commit()

        inter = Intervention(demande_id=demande.id, technicien_id=tech.id, statut='en_cours')
        inter.date_creation = _now_utc() - timedelta(hours=48)  # clearly overdue
        db.session.add(inter)
        db.session.commit()

        # First run should alert
        alerted, total = sla_utils.run_sla_check(send_alerts=True, send_email=False)
        assert total >= 1
        assert alerted >= 1

        db.session.refresh(inter)
        assert inter.sla_last_alerted_at is not None
        assert inter.sla_escalation_level >= 1

        # Immediate second run should not alert due to backoff
        alerted2, total2 = sla_utils.run_sla_check(send_alerts=True, send_email=False)
        # alerted2 should be 0 because of backoff
        assert alerted2 == 0
