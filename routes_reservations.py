from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from models import db, ReservationPiece, Produit, Intervention, User, ReservationJustificatif
from forms import ReservationPieceForm
from datetime import datetime, timedelta

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
        if reservation.intervention_id:
            return redirect(url_for('reservations.liste_reservations', 
                                 intervention_id=reservation.intervention_id))
        return redirect(url_for('reservations.suivi_reservations_technicien'))
    
    # Valider la réservation
    success, message = reservation.valider(current_user.id)
    
    if success:
        flash(message, 'success')
    else:
        flash(f'Erreur lors de la validation: {message}', 'danger')
    
    if reservation.intervention_id:
        return redirect(url_for('reservations.liste_reservations', 
                             intervention_id=reservation.intervention_id))
    if current_user.role == 'magasinier':
        return redirect(url_for('reservations.magasinier_liste_reservations'))
    return redirect(url_for('reservations.suivi_reservations_technicien'))

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
        
        if reservation.intervention_id:
            return redirect(url_for('reservations.liste_reservations', 
                                 intervention_id=reservation.intervention_id))
        if current_user.role == 'magasinier':
            return redirect(url_for('reservations.magasinier_liste_reservations'))
        return redirect(url_for('reservations.suivi_reservations_technicien'))
    
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
        
        if reservation.intervention_id:
            return redirect(url_for('reservations.liste_reservations', 
                                 intervention_id=reservation.intervention_id))
        if current_user.role == 'magasinier':
            return redirect(url_for('reservations.magasinier_liste_reservations'))
        return redirect(url_for('reservations.suivi_reservations_technicien'))
    
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
    
    if reservation.intervention_id:
        return redirect(url_for('reservations.liste_reservations', 
                             intervention_id=reservation.intervention_id))
    return redirect(url_for('reservations.suivi_reservations_technicien'))

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

# --- NOUVELLES ROUTES POUR RÉSERVATIONS HORS INTERVENTION ---

@reservations_bp.route('/technicien/reservations/nouvelle', methods=['GET', 'POST'])
@login_required
def nouvelle_reservation_technicien():
    """Page permettant au technicien de réserver des pièces sans intervention"""
    if current_user.role != 'technicien':
        flash('Accès réservé aux techniciens', 'danger')
        return redirect(url_for('dashboard'))
    
    # Filtrer les produits disponibles par zone du technicien
    from zone_rbac import filter_produit_by_emplacement_zone
    produits_query = Produit.query.filter(Produit.actif == True)
    produits = filter_produit_by_emplacement_zone(produits_query).order_by(Produit.nom).all()
    
    if request.method == 'POST':
        produit_id = request.form.get('produit_id', type=int)
        quantite = request.form.get('quantite', type=float)
        commentaire = request.form.get('commentaire', '')
        
        if not produit_id or not quantite or quantite <= 0:
            flash('Veuillez remplir tous les champs obligatoires', 'danger')
        else:
            produit = db.session.get(Produit, produit_id)
            if not produit or produit.quantite < quantite:
                flash('Stock insuffisant pour ce produit', 'danger')
            else:
                reservation = ReservationPiece(
                    produit_id=produit_id,
                    quantite=quantite,
                    commentaire=commentaire,
                    utilisateur_id=current_user.id,
                    statut=ReservationPiece.STATUT_EN_ATTENTE,
                    intervention_id=None
                )
                try:
                    db.session.add(reservation)
                    db.session.commit()
                    
                    # ✅ Notifications pour les magasiniers de la zone
                    from models import NotificationSMS, User
                    magasiniers = User.query.filter_by(
                        role='magasinier',
                        zone_id=current_user.zone_id,
                        actif=True
                    ).all()
                    
                    for m in magasiniers:
                        notif = NotificationSMS(
                            technicien_id=m.id,
                            message=f"Demande de pièce: {current_user.prenom} {current_user.nom} réserve {quantite}x {produit.nom}",
                            type_notification='reservation_nouvelle',
                            envoye=False
                        )
                        db.session.add(notif)
                    db.session.commit()
                    
                    flash('Demande de réservation envoyée au magasinier', 'success')
                    return redirect(url_for('reservations.suivi_reservations_technicien'))
                except Exception as e:
                    db.session.rollback()
                    flash(f'Erreur lors de la réservation: {str(e)}', 'danger')

    return render_template('reservations/technicien_nouvelle.html', produits=produits)

@reservations_bp.route('/technicien/reservations/suivi')
@login_required
def suivi_reservations_technicien():
    """Liste des réservations du technicien connecté"""
    if current_user.role != 'technicien':
        flash('Accès réservé aux techniciens', 'danger')
        return redirect(url_for('dashboard'))
        
    reservations = ReservationPiece.query.filter_by(utilisateur_id=current_user.id)\
        .order_by(ReservationPiece.date_creation.desc()).all()
    
    return render_template('reservations/technicien_suivi.html', reservations=reservations)

import os
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import current_app

@reservations_bp.route('/reservations/<int:reservation_id>/maj_quantite', methods=['POST'])
@login_required
def maj_quantite_utilisee(reservation_id):
    """Met à jour la quantité utilisée par le technicien avec justificatif (photo)"""
    reservation = db.session.get(ReservationPiece, reservation_id)
    if not reservation:
        abort(404)
        
    if reservation.utilisateur_id != current_user.id and current_user.role != 'admin':
        flash('Vous n\'êtes pas autorisé à modifier cette réservation', 'danger')
        return redirect(url_for('reservations.suivi_reservations_technicien'))
    
    quantite_utilisee = request.form.get('quantite_utilisee', type=int)
    if quantite_utilisee is not None:
        # Interdire la diminution de la quantité
        if quantite_utilisee < (reservation.quantite_utilisee or 0):
            flash('Vous ne pouvez pas diminuer la quantité déjà déclarée.', 'danger')
            return redirect(url_for('reservations.suivi_reservations_technicien'))
            
        if quantite_utilisee > reservation.quantite:
            flash(f'La quantité utilisée ne peut pas dépasser la quantité réservée ({int(reservation.quantite)})', 'warning')
            return redirect(url_for('reservations.suivi_reservations_technicien'))
            
        reservation.quantite_utilisee = quantite_utilisee
        
        # Gestion du justificatif (photo) - OBLIGATOIRE
        if 'photo_justification' not in request.files:
            flash('La photo justificative est obligatoire.', 'danger')
            return redirect(url_for('reservations.suivi_reservations_technicien'))
            
        file = request.files['photo_justification']
        if not file or file.filename == '':
            flash('Veuillez sélectionner une photo pour justifier l\'utilisation.', 'danger')
            return redirect(url_for('reservations.suivi_reservations_technicien'))
            
        # S'assurer que le dossier existe
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'reservations')
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        
        filename = secure_filename(f"res_{reservation.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        file.save(os.path.join(upload_path, filename))
        
        # Création du justificatif séparé
        justificatif = ReservationJustificatif(
            reservation_id=reservation.id,
            quantite_declaree=quantite_utilisee,
            photo_path=f"reservations/{filename}"
        )
        db.session.add(justificatif)
        
        # Mise à jour de la photo "principale" (optionnel, pour compatibilité)
        reservation.photo_justification = f"reservations/{filename}"
        
        # Si toute la quantité est utilisée, on peut marquer la réservation comme terminée/utilisée
        if quantite_utilisee == reservation.quantite:
            reservation.statut = ReservationPiece.STATUT_UTILISEE
            
        try:
            db.session.commit()
            flash('Quantité utilisée mise à jour avec succès', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
            
    return redirect(request.referrer or url_for('reservations.suivi_reservations_technicien'))

@reservations_bp.route('/magasinier/reservations')
@login_required
def magasinier_liste_reservations():
    """Interface Magasinier pour voir et valider/rejeter les réservations"""
    if current_user.role not in ['magasinier', 'gestionnaire_stock', 'chef_pur']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
        
    query = ReservationPiece.query
    if current_user.role == 'magasinier':
        # Filtrer par la zone du technicien qui a fait la demande, correspondant à la zone du magasinier
        query = query.join(User, ReservationPiece.utilisateur_id == User.id)\
                     .filter(User.zone_id == current_user.zone_id)
                     
    reservations = query.order_by(ReservationPiece.date_creation.desc()).all()
    
    return render_template('reservations/magasinier_liste.html', reservations=reservations)

from flask import send_from_directory

@reservations_bp.route('/reservations/uploads/<filename>')
@login_required
def uploaded_reservation_file(filename):
    """Sert les fichiers justificatifs des réservations"""
    base_dir = current_app.config['UPLOAD_FOLDER']
    res_dir = os.path.join(base_dir, 'reservations')
    return send_from_directory(res_dir, filename)
