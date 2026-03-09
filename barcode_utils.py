import os
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from flask import current_app
from PIL import Image

def generate_barcode(produit_id, produit_reference):
    """
    Génère un code-barres pour un produit et le sauvegarde dans le dossier static/barcodes/
    Retourne le nom du fichier du code-barres généré
    """
    try:
        # Créer le dossier static/barcodes s'il n'existe pas
        barcode_dir = os.path.join(current_app.static_folder, 'barcodes')
        os.makedirs(barcode_dir, exist_ok=True)
        
        # Utiliser l'ID et la référence pour créer un identifiant unique
        code_value = f"{produit_id:06d}-{produit_reference}"
        
        # Créer un code-barres Code128
        code128 = barcode.get_barcode_class('code128')
        
        # Options du code-barres
        options = {
            'write_text': True,  # Afficher le texte sous le code-barres
            'text_distance': 2,  # Distance entre le code et le texte
            'font_size': 10,     # Taille de la police
            'module_height': 10,  # Hauteur des barres
            'quiet_zone': 5,     # Zone vide autour du code
            'dpi': 300           # Résolution
        }
        
        # Générer le code-barres
        barcode_instance = code128(code_value, writer=ImageWriter())
        
        # Nom du fichier (sans extension)
        filename = f"barcode_{produit_id}"
        filepath = os.path.join(barcode_dir, filename)
        
        # Sauvegarder le code-barres en PNG
        barcode_instance.save(filepath, options)
        
        # Retourner le nom du fichier avec l'extension
        return f"{filename}.png"
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la génération du code-barres : {str(e)}")
        return None

def get_barcode_path(produit_id):
    """
    Retourne le chemin relatif vers l'image du code-barres d'un produit
    """
    return f"barcodes/barcode_{produit_id}.png"

def barcode_exists(produit_id):
    """
    Vérifie si un code-barres existe pour un produit donné
    """
    barcode_path = os.path.join(
        current_app.static_folder, 
        get_barcode_path(produit_id)
    )
    return os.path.exists(barcode_path)
