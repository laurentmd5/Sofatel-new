# Installation & exécution locale

## 1. Préparer l'environnement
- Créer un venv et activer
- Installer les dépendances : `pip install -r requirements.txt`
- Copier `.env.example` → `.env` et renseigner les valeurs

## 2. Variables d'environnement importantes
Voir `.env.example`. Assurez-vous d'avoir :
- `SQLALCHEMY_DATABASE_URI`
- `SESSION_SECRET`
- `CSRF_SECRET_KEY`
- `MAIL_*` si vous utilisez l'envoi d'email
- `ORANGE_CLIENT_ID`, `ORANGE_CLIENT_SECRET` si vous utilisez le module SMS

## 3. Initialiser la base de données
```bash
# Définir la variable d'app Flask
export FLASK_APP=main.py
# (Windows PowerShell) $env:FLASK_APP = 'main.py'
flask db upgrade
```

## 4. Lancer l'application
- Développement rapide :
```bash
python main.py
# ou
flask run --host 127.0.0.1 --port 4300
```
- En production (exemple with gunicorn) :
```bash
pip install gunicorn
gunicorn -w 4 "main:app" -b 0.0.0.0:8000
```

## 5. Vérifications après démarrage
- Accéder à la page d'accueil `/` et se connecter
- Consulter `/gestion-stock`, `/interventions`, `/reservations` selon vos droits
- Vérifier les logs pour erreurs

## 6. Tips développement
- Utiliser `pip-audit` pour checker vulnérabilités
- Exécuter `flask db migrate` puis `flask db upgrade` quand vous modifiez les modèles
