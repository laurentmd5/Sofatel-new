#!/usr/bin/env python
"""Script pour ajouter les colonnes soft delete à FichierImport"""

from app import app, db
from sqlalchemy import text

app.app_context().push()

print("🔄 Ajout des colonnes soft delete...\n")

try:
    with db.engine.connect() as conn:
        try:
            conn.execute(text('ALTER TABLE fichier_import ADD COLUMN actif BOOLEAN DEFAULT TRUE'))
            conn.commit()
            print('✅ Colonne "actif" créée')
        except Exception as e:
            if 'Duplicate column' in str(e) or 'already exists' in str(e):
                print('ℹ️  Colonne "actif" déjà existante')
            else:
                print(f'⚠️  {str(e)[:100]}')
        
        try:
            conn.execute(text('ALTER TABLE fichier_import ADD COLUMN date_suppression DATETIME'))
            conn.commit()
            print('✅ Colonne "date_suppression" créée')
        except Exception as e:
            if 'Duplicate column' in str(e) or 'already exists' in str(e):
                print('ℹ️  Colonne "date_suppression" déjà existante')
            else:
                print(f'⚠️  {str(e)[:100]}')
        
        try:
            conn.execute(text('ALTER TABLE fichier_import ADD INDEX idx_fichier_import_actif (actif)'))
            conn.commit()
            print('✅ Index créé')
        except Exception as e:
            if 'Duplicate key' in str(e):
                print('ℹ️  Index déjà existant')
            else:
                print(f'⚠️  {str(e)[:100]}')
    
    print('\n✅ Migration BD terminée avec succès!')

except Exception as e:
    print(f'❌ Erreur fatale: {str(e)}')
    import traceback
    traceback.print_exc()
