from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from models import db, ReservationPiece, Produit, Intervention, User
from forms import ReservationPieceForm
from datetime import datetime

reservations_bp = Blueprint('reservations', __name__)

@reservations_bp.route('/intervention/<int:intervention_id>/reservations')
@login_required
def liste_reservations(intervention_id):
    """Affiche la liste des réservations pour une intervention"""
    intervention = db.session.get(Intervention, intervention_id)
    if not intervention:
        abort(404)
    reservations = ReservationPiece.query.filter_by(intervention_id=intervention_id)\
        .order_by(ReservationPiece.date_creation.desc()).all()
    
    return render_template('reservations/liste.html',
                         intervention=intervention,
                         reservations=reservations)

@reservations_bp.route('/intervention/<int:intervention_id>/reservations/nouvelle', methods=['GET', 'POST'])
@login_required
def nouvelle_reservation(intervention_id):
    """Crée une nouvelle réservation de pièce pour une intervention"""
    intervention = db.session.get(Intervention, intervention_id)
    if not intervention:
        abort(404)
    form = ReservationPieceForm()
    
    if form.validate_on_submit():
        # Vérifier la disponibilité du stock
        produit = db.session.get(Produit, form.produit_id.data)
        if not produit or produit.quantite < form.quantite.data:
            flash('Stock insuffisant pour ce produit', 'danger')
            return render_template('reservations/nouvelle.html', 
                                form=form, 
                                intervention=intervention)
        
        # Créer la réservation
        reservation = ReservationPiece(
            intervention_id=intervention_id,
            produit_id=form.produit_id.data,
            quantite=form.quantite.data,
            commentaire=form.commentaire.data,
            utilisateur_id=current_user.id,
            statut=ReservationPiece.STATUT_EN_ATTENTE
        )
        
        try:
            db.session.add(reservation)
            db.session.commit()
            flash('Réservation créée avec succès', 'success')
            return redirect(url_for('reservations.liste_reservations', 
                                 intervention_id=intervention_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création de la réservation: {str(e)}', 'danger')
    
    return render_template('reservations/nouvelle.html', 
                         form=form, 
                         intervention=intervention)

@reservations_bp.route('/reservations/<int:reservation_id>/valider', methods=['POST'])
@login_required
def valider_reservation(reservation_id):
    """Valide une réservation de pièce"""
    reservation = db.session.get(ReservationPiece, reservation_id)
    if not reservation:
        abort(404)
    
    # Vérifier que la réservation est en attente
    if reservation.statut != ReservationPiece.STATUT_EN_ATTENTE:
        flash('Seules les réservations en attente peuvent être validées', 'warning')
        return redirect(url_for('reservations.liste_reservations', 
                             intervention_id=reservation.intervention_id))
    
    # Valider la réservation
    success, message = reservation.valider(current_user.id)
    
    if success:
        flash(message, 'success')
    else:
        flash(f'Erreur lors de la validation: {message}', 'danger')
    
    return redirect(url_for('reservations.liste_reservations', 
                         intervention_id=reservation.intervention_id))

@reservations_bp.route('/reservations/<int:reservation_id>/annuler', methods=['GET', 'POST'])
@login_required
def annuler_reservation(reservation_id):
    """Annule une réservation de pièce (vue pour l'interface utilisateur)"""
    reservation = db.session.get(ReservationPiece, reservation_id)
    if not reservation:
        abort(404)
    
    # Vérifier les autorisations
    if current_user.role not in ['chef_pur', 'gestionnaire_stock']:
        flash('Vous n\'êtes pas autorisé à effectuer cette action', 'danger')
        return redirect(url_for('reservations.liste_reservations', 
                             intervention_id=reservation.intervention_id))
    
    if request.method == 'POST':
        motif = request.form.get('motif', '')
        # Passer rejeter=False pour une annulation normale
        success, message = reservation.annuler(motif=motif, rejeter=False)
        
        if success:
            flash(message, 'success')
        else:
            flash(f'Erreur lors de l\'annulation: {message}', 'danger')
        
        return redirect(url_for('reservations.liste_reservations', 
                             intervention_id=reservation.intervention_id))
    
    return render_template('reservations/annuler.html', 
                         reservation=reservation, 
                         action='annuler',
                         titre_modal='Confirmer l\'annulation')

@reservations_bp.route('/reservations/<int:reservation_id>/rejeter', methods=['GET', 'POST'])
@login_required
def rejeter_reservation(reservation_id):
    """Rejette une réservation de pièce (vue pour l'interface utilisateur)"""
    reservation = db.session.get(ReservationPiece, reservation_id)
    if not reservation:
        abort(404)
    
    # Vérifier les autorisations
    if current_user.role not in ['chef_pur', 'gestionnaire_stock']:
        flash('Vous n\'êtes pas autorisé à effectuer cette action', 'danger')
        return redirect(url_for('reservations.liste_reservations', 
                             intervention_id=reservation.intervention_id))
    
    if request.method == 'POST':
        motif = request.form.get('motif', '')
        # Passer rejeter=True pour marquer comme rejeté
        success, message = reservation.annuler(motif=motif, rejeter=True)
        
        if success:
            flash(message, 'success')
        else:
            flash(f'Erreur lors du rejet: {message}', 'danger')
        
        return redirect(url_for('reservations.liste_reservations', 
                             intervention_id=reservation.intervention_id))
    
    return render_template('reservations/annuler.html', 
                         reservation=reservation, 
                         action='rejeter',
                         titre_modal='Confirmer le rejet')

@reservations_bp.route('/reservations/<int:reservation_id>/utiliser', methods=['POST'])
@login_required
def utiliser_reservation(reservation_id):
    """Marque une réservation comme utilisée (après sortie de stock)"""
    reservation = db.session.get(ReservationPiece, reservation_id)
    if not reservation:
        abort(404)
    
    # Vérifier que la réservation est validée
    if reservation.statut != ReservationPiece.STATUT_VALIDEE:
        flash('Seules les réservations validées peuvent être marquées comme utilisées', 'warning')
        return redirect(url_for('reservations.liste_reservations', 
                             intervention_id=reservation.intervention_id))
    
    # Marquer comme utilisée
    success, message = reservation.marquer_comme_utilisee()
    
    if success:
        flash(message, 'success')
    else:
        flash(f'Erreur: {message}', 'danger')
    
    return redirect(url_for('reservations.liste_reservations', 
                         intervention_id=reservation.intervention_id))

# API pour les réservations (utilisé en AJAX)
@reservations_bp.route('/api/reservation/<int:reservation_id>/statut', methods=['GET'])
@login_required
def get_reservation_statut(reservation_id):
    """Retourne le statut d'une réservation au format JSON"""
    reservation = db.session.get(ReservationPiece, reservation_id)
    if not reservation:
        abort(404)
    
    return jsonify({
        'id': reservation.id,
        'statut': reservation.statut,
        'statut_libelle': reservation.statut_libelle,
        'statut_technicien': reservation.statut_technicien,
        'statut_technicien_libelle': reservation.statut_technicien_libelle()
    })

# API pour récupérer les informations d'un produit (utilisé en AJAX)
@reservations_bp.route('/api/produit/<int:produit_id>')
@login_required
def get_produit_info(produit_id):
    """Retourne les informations d'un produit au format JSON"""
    produit = db.session.get(Produit, produit_id)
    if not produit:
        abort(404)
    
    return jsonify({
        'id': produit.id,
        'nom': produit.nom,
        'reference': produit.reference,
        'quantite_disponible': produit.quantite,
        'unite_mesure': produit.unite_mesure or 'unité'
    })

# Fonction utilitaire pour vérifier la disponibilité d'un produit
def verifier_disponibilite_produit(produit_id, quantite_demandee, reservation_id=None):
    """
    Vérifie si la quantité demandée est disponible pour un produit
    Retourne un tuple (disponible, message, quantite_disponible)
    """
    produit = db.session.get(Produit, produit_id)
    if not produit:
        return False, 'Produit non trouvé', 0
    
    # Calculer la quantité déjà réservée (hors la réservation courante si elle existe)
    from sqlalchemy import func
    query = db.session.query(
        func.sum(ReservationPiece.quantite)
    ).filter(
        ReservationPiece.produit_id == produit_id,
        ReservationPiece.statut.in_([
            ReservationPiece.STATUT_EN_ATTENTE, 
            ReservationPiece.STATUT_VALIDEE
        ])
    )
    
    if reservation_id:
        query = query.filter(ReservationPiece.id != reservation_id)
    
    quantite_reservee = query.scalar() or 0
    quantite_disponible = produit.quantite - quantite_reservee
    
    if quantite_disponible >= quantite_demandee:
        return True, 'Quantité disponible', quantite_disponible
    else:
        return False, f'Stock insuffisant. Quantité disponible: {quantite_disponible}', quantite_disponible
