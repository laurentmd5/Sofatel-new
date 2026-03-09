import os
import sys

# Chemin du virtualenv généré par cPanel
VIRTUALENV = "/home/qirm8908/virtualenv/sofatel-sn.com/3.10"
python_version = "3.10"
site_packages = os.path.join(VIRTUALENV, "lib", f"python{python_version}", "site-packages")
sys.path.insert(0, site_packages)

# Chemin de ton projet Flask
project_folder = '/home/qirm8908/sofatel-sn.com'
if project_folder not in sys.path:
    sys.path.insert(0, project_folder)

# Charger les variables d'environnement
import dotenv
dotenv.load_dotenv(os.path.join(project_folder, '.env'))

from app import app as application