import os
import pandas as pd
from datetime import datetime
from flask import Flask
from extensions import db
from models import User, DemandeIntervention, FichierImport
from utils import process_excel_file

# Setup a minimal Flask app for testing
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def verify():
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create a test user
        user = User(username='testadmin', email='test@example.com', role='admin')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        
        print("Starting verification with MAQUETTE PROD VF xlsx.xlsx...")
        
        # Original file path
        file_path = 'MAQUETTE PROD VF xlsx.xlsx'
        
        if not os.path.exists(file_path):
            print(f"Error: {file_path} not found.")
            return

        # Process the file
        # Note: process_excel_file expects (filepath, service, importe_par)
        try:
            result = process_excel_file(file_path, 'Production', user.id)
            print(f"Import Result: {result}")
            
            if not result['success']:
                print(f"Import Failed: {result.get('error')}")
                return
            
            # Check imported data
            demandes = DemandeIntervention.query.all()
            print(f"Number of imported demandes: {len(demandes)}")
            
            if len(demandes) > 0:
                d = demandes[0]
                print(f"Sample Demande:")
                print(f"  ND: {d.nd}")
                print(f"  Zone (OLT): {d.zone}")
                print(f"  Type Techno: {d.type_techno}")
                print(f"  Offre: {d.offre}")
                print(f"  Nom Client: {d.nom_client}")
                print(f"  Prestataire: {d.prestataire}")
                print(f"  Service: {d.service}")
                
                # Check for specific expected mappings if we know the sample content
                # For now, just confirming it imported successfully.
            else:
                print("No demandes imported.")
                
        except Exception as e:
            print(f"Exception during import: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    verify()
