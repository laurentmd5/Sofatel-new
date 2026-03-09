from flask import Blueprint, send_from_directory, render_template, jsonify
import yaml
import os
from app import app

api_docs_bp = Blueprint('api_docs', __name__)

@api_docs_bp.route('/api/openapi.json')
def openapi_json():
    # Charge le YAML et renvoie du JSON
    spec_path = os.path.join(os.path.dirname(__file__), 'docs', 'openapi.yaml')
    with open(spec_path, 'r', encoding='utf-8') as f:
        spec = yaml.safe_load(f)
    return jsonify(spec)

@api_docs_bp.route('/api/docs')
def swagger_ui():
    return render_template('swagger_ui.html')

# Enregistrer le blueprint si l'app est déjà importée
try:
    app.register_blueprint(api_docs_bp)
except Exception:
    pass
