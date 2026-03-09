"""Create a temporary SQLite test database and minimal fixtures.

Run as: python tools/validation/setup_test_data.py --db tests/test_data.sqlite

This script does not run tests; it only creates a DB file with minimal data:
- Users: admin (chef_pur), manager, technicien, gestionnaire_stock, rh
- Demandes / Interventions: 10 interventions with mixed status
- Stock: 20 products with thresholds
- Leave requests: sample
"""
import argparse
import os
from app import app
from extensions import db
from models import User, DemandeIntervention, Intervention, Produit, LeaveRequest
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta


def create_fixture(db_path):
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['TESTING'] = True
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Users
        admin = User(username='admin', email='admin@example.com', password_hash=generate_password_hash('pass'), role='chef_pur', nom='Admin', prenom='Admin', telephone='000')
        manager = User(username='manager', email='manager@example.com', password_hash=generate_password_hash('pass'), role='manager', nom='Manager', prenom='Manager', telephone='000')
        tech = User(username='tech', email='tech@example.com', password_hash=generate_password_hash('pass'), role='technicien', nom='Tech', prenom='Tech', telephone='000')
        stock_user = User(username='stock', email='stock@example.com', password_hash=generate_password_hash('pass'), role='gestionnaire_stock', nom='Stock', prenom='Stock', telephone='000')
        rh_user = User(username='rh', email='rh@example.com', password_hash=generate_password_hash('pass'), role='rh', nom='RH', prenom='RH', telephone='000')
        db.session.add_all([admin, manager, tech, stock_user, rh_user])
        db.session.commit()

        # Demandes and Interventions
        demandes = []
        for i in range(1, 6):
            d = DemandeIntervention(nd=f'ND{i}', zone='Zone1' if i % 2 == 0 else 'Zone2', type_techno='Fibre', nom_client=f'Client{i}', date_demande_intervention=datetime.utcnow() - timedelta(days=i), service='SAV' if i % 2 == 0 else 'Production')
            db.session.add(d)
            demandes.append(d)
        db.session.commit()

        for i, d in enumerate(demandes, start=1):
            it = Intervention(demande_id=d.id, technicien_id=tech.id, statut='en_cours' if i % 3 else 'termine', date_creation=datetime.utcnow() - timedelta(days=i), date_debut=(datetime.utcnow() - timedelta(days=i) if i % 2 == 0 else None), date_fin=(datetime.utcnow() - timedelta(days=i) + timedelta(hours=2) if i % 2 == 0 else None), photos='["/a.jpg"]' if i % 2 == 0 else None, signature_client='s' if i % 2 == 0 else None, diagnostic_technicien='ok' if i % 2 == 0 else None)
            db.session.add(it)
        db.session.commit()

        # Stock products
        for i in range(1, 21):
            p = Produit(reference=f'P{i}', nom=f'Produit {i}', code_barres=f'CB{i}', stock_min=5, stock_max=100)
            db.session.add(p)
        db.session.commit()

        # Seed an initial stock movement for each product
        from models import MouvementStock
        for idx, p in enumerate(Produit.query.all(), start=1):
            m = MouvementStock(type_mouvement='entree', reference=f'INIT{idx}', produit_id=p.id, quantite=20 + idx, utilisateur_id=admin.id, date_reference=datetime.utcnow().date())
            db.session.add(m)
        db.session.commit()

        # Leaves
        lr = LeaveRequest(technicien_id=tech.id, date_debut=datetime.utcnow().date(), date_fin=(datetime.utcnow().date() + timedelta(days=3)), type='conges', statut='pending', commentaire='Test leave')
        db.session.add(lr)
        db.session.commit()

        print(f'Created test DB at {db_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default='tests/test_data.sqlite', help='Path to sqlite DB file')
    args = parser.parse_args()
    path = args.db
    os.makedirs(os.path.dirname(path), exist_ok=True)
    create_fixture(path)
