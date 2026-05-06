from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, case, and_
from app import db
from models import Equipe, MembreEquipe, User, Intervention, PiloteEquipe
from utils import log_activity

pilote_equipes_bp = Blueprint('pilote_equipes', __name__)

@pilote_equipes_bp.route('/pilote/equipes', methods=['GET'])
@login_required
def get_equipes():
    if current_user.role != 'chef_pilote':
        return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403

    # Récupérer les ID des équipes assignées au pilote actuel
    assigned_equipe_ids = [pe.equipe_id for pe in PiloteEquipe.query.filter_by(user_id=current_user.id).all()]
    
    # Query optimisée pour obtenir toutes les équipes avec leurs statistiques
    # Basée sur les techniciens membres de chaque équipe
    stats_query = db.session.query(
        Equipe.id,
        Equipe.nom_equipe,
        func.count(func.distinct(MembreEquipe.technicien_id)).label('nb_techniciens'),
        func.sum(case((Intervention.statut == 'en_cours', 1), else_=0)).label('interventions_en_cours'),
        func.sum(case((Intervention.statut == 'valide', 1), else_=0)).label('interventions_validees'),
        func.count(Intervention.id).label('total_interventions')
    ).outerjoin(MembreEquipe, and_(Equipe.id == MembreEquipe.equipe_id, MembreEquipe.type_membre == 'technicien'))\
     .outerjoin(Intervention, Intervention.technicien_id == MembreEquipe.technicien_id)\
     .group_by(Equipe.id, Equipe.nom_equipe).all()
     
    equipes_data = []
    for row in stats_query:
        total = row.total_interventions or 0
        valide = row.interventions_validees or 0
        perf = (valide / total * 100) if total > 0 else 0
        
        equipes_data.append({
            'id': row.id,
            'nom_equipe': row.nom_equipe,
            'nb_techniciens': row.nb_techniciens or 0,
            'interventions_en_cours': int(row.interventions_en_cours or 0),
            'interventions_validees': int(row.interventions_validees or 0),
            'performance': round(perf, 1),
            'assignee': row.id in assigned_equipe_ids
        })
        
    return jsonify({
        'success': True,
        'equipes': equipes_data
    })

@pilote_equipes_bp.route('/pilote/equipes/assigner', methods=['POST'])
@login_required
def assigner_equipe():
    if current_user.role != 'chef_pilote':
        return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403
    
    try:
        data = request.get_json()
        equipe_id = data.get('equipe_id')
        
        if not equipe_id:
            return jsonify({'success': False, 'error': 'ID équipe manquant'}), 400
            
        # Vérifier si l'équipe existe
        equipe = db.session.get(Equipe, equipe_id)
        if not equipe:
            return jsonify({'success': False, 'error': 'Équipe non trouvée'}), 404
            
        # Vérifier si déjà assignée
        exists = PiloteEquipe.query.filter_by(user_id=current_user.id, equipe_id=equipe_id).first()
        if exists:
            return jsonify({'success': True, 'message': 'Équipe déjà assignée'})
            
        pe = PiloteEquipe(user_id=current_user.id, equipe_id=equipe_id)
        db.session.add(pe)
        db.session.commit()
        
        log_activity(
            user_id=current_user.id,
            action='assign_team',
            module='chef_pilote',
            entity_id=equipe_id,
            entity_name=f"Équipe {equipe.nom_equipe}",
            details={'pilote_id': current_user.id}
        )
        
        return jsonify({'success': True, 'message': 'Équipe assignée avec succès'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur assignation équipe: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@pilote_equipes_bp.route('/pilote/equipes/retirer', methods=['POST'])
@login_required
def retirer_equipe():
    if current_user.role != 'chef_pilote':
        return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403
    
    try:
        data = request.get_json()
        equipe_id = data.get('equipe_id')
        
        if not equipe_id:
            return jsonify({'success': False, 'error': 'ID équipe manquant'}), 400
            
        pe = PiloteEquipe.query.filter_by(user_id=current_user.id, equipe_id=equipe_id).first()
        if pe:
            db.session.delete(pe)
            db.session.commit()
            
            log_activity(
                user_id=current_user.id,
                action='remove_team',
                module='chef_pilote',
                entity_id=equipe_id,
                entity_name=f"Équipe {equipe_id}",
                details={'pilote_id': current_user.id}
            )
            
            return jsonify({'success': True, 'message': 'Équipe retirée avec succès'})
        return jsonify({'success': True, 'message': 'Équipe non assignée'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur retrait équipe: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
