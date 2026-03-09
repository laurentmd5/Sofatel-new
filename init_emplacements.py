from app import app, db
from models import EmplacementStock

def init_emplacements():
    with app.app_context():
        # Vérifier si la table existe
        if not db.engine.dialect.has_table(db.engine, 'emplacement_stock'):
            print("La table 'emplacement_stock' n'existe pas. Veuillez exécuter les migrations d'abord.")
            return
        
        # Liste des emplacements par défaut
        emplacements = [
            {'code': 'ENTREPOT', 'designation': 'Entrepôt central', 'description': 'Stock principal de l\'entrepôt central'},
            {'code': 'VEHICULE', 'designation': 'Stock véhicule', 'description': 'Stock dans les véhicules de service'},
            {'code': 'PERSO', 'designation': 'Stock personnel', 'description': 'Stock attribué au personnel'},
            {'code': 'ZONE1', 'designation': 'Zone 1 - Dakar', 'description': 'Stock pour la zone de Dakar'},
            {'code': 'ZONE2', 'designation': 'Zone 2 - Mbour', 'description': 'Stock pour la zone de Mbour'},
            {'code': 'ZONE3', 'designation': 'Zone 3 - Kaolack', 'description': 'Stock pour la zone de Kaolack'},
            {'code': 'ZONE4', 'designation': 'Zone 4 - Autres', 'description': 'Stock pour les autres zones'},
        ]
        
        # Ajouter les emplacements s'ils n'existent pas déjà
        for emp in emplacements:
            if not EmplacementStock.query.filter_by(code=emp['code']).first():
                nouvel_emplacement = EmplacementStock(**emp)
                db.session.add(nouvel_emplacement)
                print(f"Ajout de l'emplacement: {emp['designation']}")
        
        try:
            db.session.commit()
            print("Initialisation des emplacements terminée avec succès.")
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de l'initialisation des emplacements: {str(e)}")

if __name__ == '__main__':
    init_emplacements()
