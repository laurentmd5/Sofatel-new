from flask import Blueprint, jsonify, request, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from models import Categorie, db
from utils import log_activity

# Création du Blueprint
categories_bp = Blueprint('categories', __name__)

# ==================== ROUTES POUR LA GESTION DES CATÉGORIES ====================

@categories_bp.route('/categories', methods=['GET'])
@login_required
def get_categories():
    """
    Récupère toutes les catégories
    """
    if current_user.role not in ['chef_pur', 'gestionnaire_stock']:
        return jsonify({'error': 'Accès non autorisé'}), 403
        
    try:
        categories = Categorie.query.order_by(Categorie.nom).all()
        categories_data = [{
            'id': cat.id,
            'nom': cat.nom,
            'description': cat.description or '',
            'date_creation': cat.date_creation.isoformat() if cat.date_creation else None,
            'date_maj': cat.date_maj.isoformat() if cat.date_maj else None,
            'nombre_produits': len(cat.produits) if hasattr(cat, 'produits') else 0
        } for cat in categories]
        
        return jsonify({
            'data': categories_data,
            'recordsTotal': len(categories_data),
            'recordsFiltered': len(categories_data),
            'draw': request.args.get('draw', 1, type=int)
        })
    except Exception as e:
        return jsonify({'error': str(e), 'data': []}), 500

@categories_bp.route('/categories/<int:category_id>', methods=['GET'])
@login_required
def get_category(category_id):
    """
    Récupère une catégorie par son ID
    """
    if current_user.role not in ['chef_pur', 'gestionnaire_stock']:
        return jsonify({'error': 'Accès non autorisé'}), 403
        
    try:
        category = db.session.get(Categorie, category_id)
        if not category:
            abort(404)
        return jsonify({
            'id': category.id,
            'nom': category.nom,
            'description': category.description,
            'date_creation': category.date_creation.isoformat() if category.date_creation else None,
            'date_maj': category.date_maj.isoformat() if category.date_maj else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@categories_bp.route('/categories', methods=['POST'])
@login_required
def create_category():
    """
    Crée une nouvelle catégorie
    """
    if current_user.role not in ['chef_pur', 'gestionnaire_stock']:
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    try:
        data = request.get_json()
        
        if not data or not data.get('nom'):
            return jsonify({'error': 'Le nom de la catégorie est requis'}), 400
            
        # Vérifier si une catégorie avec le même nom existe déjà
        existing = Categorie.query.filter_by(nom=data['nom']).first()
        if existing:
            return jsonify({'error': 'Une catégorie avec ce nom existe déjà'}), 409
            
        category = Categorie(
            nom=data['nom'],
            description=data.get('description', '')
        )
        
        db.session.add(category)
        db.session.commit()
        
        log_activity(
            user_id=current_user.id,
            action='create',
            module='categories',
            entity_id=category.id,
            entity_name=f"Catégorie {category.nom}",
            details={'nom': category.nom, 'description': category.description}
        )
        
        return jsonify({
            'id': category.id,
            'nom': category.nom,
            'description': category.description,
            'date_creation': category.date_creation.isoformat() if category.date_creation else None,
            'message': 'Catégorie créée avec succès'
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Erreur d\'intégrité des données. Vérifiez que les données sont valides.'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@categories_bp.route('/categories/<int:category_id>', methods=['PUT'])
@login_required
def update_category(category_id):
    """
    Met à jour une catégorie existante
    """
    if current_user.role not in ['chef_pur', 'gestionnaire_stock']:
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    try:
        category = db.session.get(Categorie, category_id)
        if not category:
            abort(404)
        data = request.get_json()
        
        if 'nom' in data and data['nom']:
            # Vérifier si une autre catégorie avec le même nom existe
            existing = Categorie.query.filter(
                Categorie.nom == data['nom'],
                Categorie.id != category_id
            ).first()
            if existing:
                return jsonify({'error': 'Une autre catégorie avec ce nom existe déjà'}), 409
            category.nom = data['nom']
            
        if 'description' in data:
            category.description = data['description']
        
        db.session.commit()
        
        log_activity(
            user_id=current_user.id,
            action='update',
            module='categories',
            entity_id=category.id,
            entity_name=f"Catégorie {category.nom}",
            details={'nom': category.nom, 'description': category.description}
        )
        
        return jsonify({
            'id': category.id,
            'nom': category.nom,
            'description': category.description,
            'date_maj': category.date_maj.isoformat() if category.date_maj else None,
            'message': 'Catégorie mise à jour avec succès'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@categories_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@login_required
def delete_category(category_id):
    """
    Supprime une catégorie
    """
    if current_user.role not in ['chef_pur', 'gestionnaire_stock']:
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    try:
        category = db.session.get(Categorie, category_id)
        if not category:
            abort(404)

        # Vérifier si la catégorie est utilisée par des produits
        if hasattr(category, 'produits') and category.produits:
            return jsonify({
                'error': 'Impossible de supprimer cette catégorie car elle est utilisée par un ou plusieurs produits',
                'produits_count': len(category.produits)
            }), 400

        db.session.delete(category)
        db.session.commit()

        log_activity(
            user_id=current_user.id,
            action='delete',
            module='categories',
            entity_id=category_id,
            entity_name=f"Catégorie {category.nom}",
            details={'nom': category.nom}
        )

        return jsonify({'message': 'Catégorie supprimée avec succès'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
