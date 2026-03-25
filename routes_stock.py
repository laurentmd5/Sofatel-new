from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file, Response, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, and_, or_, desc, asc, case
from sqlalchemy.sql.expression import case as case_sql
from datetime import datetime, timedelta, timezone
import traceback
from models import db, Produit, MouvementStock, Categorie, EmplacementStock
from sqlalchemy import func, extract, and_
from extensions import db
from forms import EntreeStockForm, SortieStockForm, ProduitForm, FournisseurForm
from models import Produit, Categorie, MouvementStock, User, Fournisseur, EmplacementStock, Intervention, ReservationPiece, Zone
import pandas as pd
import traceback
from io import BytesIO
import os
from barcode_utils import generate_barcode
from utils_audit import log_stock_entry, log_stock_removal
from utils_export import generate_csv, PDFReport, format_datetime, apply_date_filter
from rbac_stock import require_stock_permission, require_stock_role, has_stock_permission, can_modify_produit, can_delete_produit
from supplier_import import process_supplier_import
from sonatel_stock_import import process_sonatel_import

# Création d'un Blueprint pour les routes de gestion de stock
stock_bp = Blueprint('stock', __name__, url_prefix='/gestion-stock')

# ============================================================================
# 🔴 PRODUCTION CRITICAL: Workflow & Stock Validation Helpers
# ============================================================================

def validate_and_initialize_mouvement_workflow(mouvement, user):
    """
    🔴 PRODUCTION CRITICAL: Initialize workflow state BEFORE any stock is applied.
    
    This ensures:
    1. All stock movements require approval before being applied
    2. Movements start in EN_ATTENTE state
    3. Only EN_ATTENTE_DOCS → APPROUVE → EXECUTE → VALIDE flow allowed
    
    Args:
        mouvement: MouvementStock object (not yet committed)
        user: User object creating the movement
    
    Returns:
        mouvement: Modified MouvementStock with proper workflow state
    """
    from workflow_stock import WORKFLOW_RULES, WorkflowState
    
    try:
        # Ensure workflow state is set BEFORE commit
        mouvement.workflow_state = WorkflowState.EN_ATTENTE.value
        mouvement.applique_au_stock = False  # CRITICAL: Never auto-apply
        
        # Log the initialization
        current_app.logger.info(
            f"✅ Mouvement workflow initialized: ID={mouvement.id}, "
            f"type={mouvement.type_mouvement}, state={mouvement.workflow_state}, "
            f"applique_au_stock=False"
        )
        
        return mouvement
    
    except Exception as e:
        current_app.logger.error(f"❌ Error initializing workflow: {str(e)}")
        raise

def prevent_negative_stock_on_creation(produit_id, quantite_to_remove):
    """
    🔴 PRODUCTION CRITICAL: Prevent negative stock before creating ANY stock movement.
    
    Args:
        produit_id: Product ID
        quantite_to_remove: Quantity being removed (for sortie movements)
    
    Returns:
        (is_valid: bool, available_stock: float, message: str)
    """
    try:
        current_stock = db.session.query(
            func.coalesce(
                func.sum(
                    case(
                        (MouvementStock.type_mouvement == 'entree', MouvementStock.quantite),
                        (MouvementStock.type_mouvement == 'sortie', -MouvementStock.quantite),
                        else_=0
                    )
                ), 
                0
            )
        ).filter(MouvementStock.produit_id == produit_id).scalar()
        
        if quantite_to_remove > current_stock:
            return (False, current_stock, f"Insufficient stock: {current_stock} available, {quantite_to_remove} requested")
        
        return (True, current_stock, "OK")
    
    except Exception as e:
        current_app.logger.error(f"❌ Error checking stock: {str(e)}")
        return (False, 0, f"Error checking stock: {str(e)}")

# Routes pour l'API du tableau de bord de gestion des stocks

@stock_bp.route('/api/stats/stock')
@login_required
def api_stats_stock():
    """
    API pour récupérer les statistiques globales du stock
    Filtre par zone pour magasinier
    """
    try:
        from rbac_stock import filter_produits_by_zone
        
        current_app.logger.info("Début de la récupération des statistiques du stock")
        
        # Nombre total de produits (filtré par zone pour magasinier)
        query = db.session.query(Produit)
        query = filter_produits_by_zone(query, current_user)
        total_produits = query.count()
        current_app.logger.info(f"Nombre total de produits: {total_produits}")
        
        # Nombre de produits en dessous du seuil d'alerte
        try:
            # Récupérer tous les produits avec leur seuil d'alerte (filtré par zone)
            produits_query = db.session.query(Produit)
            produits_query = filter_produits_by_zone(produits_query, current_user)
            produits = produits_query.all()
            # Compter ceux dont la quantité est inférieure ou égale au seuil d'alerte spécifique
            produits_faible_stock = sum(1 for p in produits if p.quantite <= p.seuil_alerte)
            current_app.logger.info(f"Produits en dessous du seuil d'alerte: {produits_faible_stock}")
        except Exception as e:
            current_app.logger.error(f"Erreur lors du calcul des produits en faible stock: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            produits_faible_stock = 0
        
        # Calcul des entrées/sorties du mois en cours
        maintenant = datetime.now()
        debut_mois = maintenant.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Entrées du mois (filtrées par zone)
        try:
            from rbac_stock import filter_mouvements_by_zone
            # Pour magasinier: filtrer les mouvements par zone
            mouvements_entree = db.session.query(MouvementStock).filter(
                MouvementStock.type_mouvement == 'entree',
                MouvementStock.date_mouvement >= debut_mois
            )
            mouvements_entree = filter_mouvements_by_zone(mouvements_entree, current_user)
            entrees_mois = sum(m.quantite for m in mouvements_entree)
        except Exception as e:
            current_app.logger.error(f"Erreur lors du calcul des entrées du mois: {str(e)}")
            entrees_mois = 0
        
        # Sorties du mois (filtrées par zone)
        try:
            mouvements_sortie = db.session.query(MouvementStock).filter(
                MouvementStock.type_mouvement == 'sortie',
                MouvementStock.date_mouvement >= debut_mois
            )
            mouvements_sortie = filter_mouvements_by_zone(mouvements_sortie, current_user)
            sorties_mois = sum(m.quantite for m in mouvements_sortie)
        except Exception as e:
            current_app.logger.error(f"Erreur lors du calcul des sorties du mois: {str(e)}")
            sorties_mois = 0
        
        current_app.logger.info(f"Entrées du mois: {entrees_mois}, Sorties du mois: {sorties_mois}")
        
        # Mouvements des 30 derniers jours pour le graphique
        date_30j = maintenant - timedelta(days=30)
        current_app.logger.info(f"Récupération des mouvements depuis le {date_30j}")
        mouvements_30j = []
        
        try:
            # Récupérer les données par jour (filtrées par zone pour magasinier)
            from zone_rbac import user_has_global_access
            
            # Build base query
            base_query = db.session.query(
                func.date(MouvementStock.date_mouvement).label('date'),
                func.sum(
                    case(
                        (MouvementStock.type_mouvement == 'entree', MouvementStock.quantite),
                        else_=0
                    )
                ).label('entrees'),
                func.sum(
                    case(
                        (MouvementStock.type_mouvement == 'sortie', MouvementStock.quantite),
                        else_=0
                    )
                ).label('sorties')
            ).filter(
                MouvementStock.date_mouvement >= date_30j
            )
            
            # Apply zone filter for magasinier
            if not user_has_global_access():
                from models import EmplacementStock
                base_query = base_query.join(EmplacementStock).filter(
                    EmplacementStock.zone_id == current_user.zone_id
                )
            
            mouvements_par_jour = base_query.group_by(
                func.date(MouvementStock.date_mouvement)
            ).order_by(
                func.date(MouvementStock.date_mouvement)
            ).all()
            
            current_app.logger.info(f"Mouvements par jour trouvés: {len(mouvements_par_jour)}")
            
            # Formater les données pour le graphique
            for date, entrees, sorties in mouvements_par_jour:
                entrees = int(entrees or 0)
                sorties = int(sorties or 0)
                date_str = date.strftime('%Y-%m-%d')
                mouvements_30j.append({
                    'date': date_str,
                    'entrees': entrees,
                    'sorties': sorties
                })
                current_app.logger.debug(f"Date: {date_str}, Entrées: {entrees}, Sorties: {sorties}")
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la récupération des mouvements: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            mouvements_30j = []
        
        # Répartition par catégorie
        repartition_categories = []
        try:
            categories = db.session.query(
                Categorie.nom,
                func.count(Produit.id).label('nombre')
            ).outerjoin(
                Produit, Produit.categorie_id == Categorie.id
            ).group_by(
                Categorie.nom
            ).all()
            
            current_app.logger.info(f"Catégories trouvées: {len(categories)}")
            
            for nom, nombre in categories:
                repartition_categories.append({
                    'nom': nom,
                    'nombre': int(nombre or 0)
                })
                current_app.logger.debug(f"Catégorie: {nom}, Nombre de produits: {nombre}")
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la récupération des catégories: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            repartition_categories = []
        
        # Créer la réponse
        response_data = {
            'success': True,
            'total_produits': total_produits,
            'produits_faible_stock': produits_faible_stock,
            'entrees_mois': int(entrees_mois or 0),
            'sorties_mois': int(sorties_mois or 0),
            'mouvements_30j': mouvements_30j,
            'categories': repartition_categories
        }
        
        current_app.logger.info("Réponse de l'API générée avec succès")
        return jsonify(response_data)
        
    except Exception as e:
        error_msg = f"Erreur dans api_stats_stock: {str(e)}"
        current_app.logger.error(error_msg)
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': error_msg,
            'error_details': str(e),
            'traceback': traceback.format_exc()
        }), 500

@stock_bp.route('/api/produits-faibles-stocks')
@login_required
def api_produits_faibles_stocks():
    """
    API pour récupérer la liste des produits en faible stock
    """
    try:
        current_app.logger.info("Récupération des produits en faible stock")
        
        # Récupérer tous les produits
        produits = db.session.query(Produit).all()
        
        # Filtrer les produits en faible stock
        faibles_stocks = []
        for produit in produits:
            if produit.quantite <= produit.seuil_alerte:
                faibles_stocks.append({
                    'id': produit.id,
                    'reference': produit.reference,
                    'nom': produit.nom,
                    'quantite': float(produit.quantite) if produit.quantite else 0,
                    'seuil_alerte': float(produit.seuil_alerte) if produit.seuil_alerte else 0,
                    'unite_mesure': produit.unite_mesure or '',
                    'categorie': produit.categorie.nom if produit.categorie else 'Non catégorisé',
                    'emplacement': produit.emplacement.designation if produit.emplacement else 'Non spécifié',
                    'code_barres': produit.code_barres,
                    'prix_achat': float(produit.prix_achat) if produit.prix_achat else 0
                })
        
        current_app.logger.info(f"Nombre de produits en faible stock: {len(faibles_stocks)}")
        
        return jsonify({
            'success': True,
            'produits': faibles_stocks,
            'total': len(faibles_stocks)
        })
    
    except Exception as e:
        error_msg = f"Erreur dans api_produits_faibles_stocks: {str(e)}"
        current_app.logger.error(error_msg)
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': error_msg,
            'error_details': str(e),
            'traceback': traceback.format_exc()
        }), 500

@stock_bp.route('/produits-faibles-stocks')
@login_required
def page_produits_faibles_stocks():
    """
    Page dédiée pour afficher les produits en faible stock
    Cette page remplace la section du dashboard
    """
    try:
        return render_template('produits_faibles_stocks.html')
    except Exception as e:
        current_app.logger.error(f"Erreur dans page_produits_faibles_stocks: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        flash('Erreur: ' + str(e), 'danger')
        return redirect(url_for('stock.liste_produits'))

@stock_bp.route('/produits-en-stock')
@login_required
def page_produits_en_stock():
    """
    Page dédiée pour afficher tous les produits en stock
    """
    try:
        return render_template('produits_stock.html')
    except Exception as e:
        current_app.logger.error(f"Erreur dans page_produits_en_stock: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        flash('Erreur: ' + str(e), 'danger')
        return redirect(url_for('stock.liste_produits'))

@stock_bp.route('/entrees-mois')
@login_required
def page_entrees_mois():
    """
    Page dédiée pour afficher les entrées du mois courant
    """
    try:
        return render_template('entrees_mois.html')
    except Exception as e:
        current_app.logger.error(f"Erreur dans page_entrees_mois: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        flash('Erreur: ' + str(e), 'danger')
        return redirect(url_for('stock.liste_produits'))

@stock_bp.route('/sorties-mois')
@login_required
def page_sorties_mois():
    """
    Page dédiée pour afficher les sorties du mois courant
    """
    try:
        return render_template('sorties_mois.html')
    except Exception as e:
        current_app.logger.error(f"Erreur dans page_sorties_mois: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        flash('Erreur: ' + str(e), 'danger')
        return redirect(url_for('stock.liste_produits'))

@stock_bp.route('/debug/mouvements')
@login_required
def debug_mouvements():
    """
    Route de débogage pour afficher le contenu de la table mouvement_stock
    """
    try:
        current_app.logger.info("Début du débogage des mouvements de stock")
        
        # Vérifier si la table existe
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if 'mouvement_stock' not in inspector.get_table_names():
            return jsonify({
                'success': False,
                'error': 'La table mouvement_stock n\'existe pas dans la base de données',
                'tables_disponibles': inspector.get_table_names()
            }), 500
        
        # Compter le nombre total d'entrées
        try:
            total_entrees = db.session.query(MouvementStock).filter(
                MouvementStock.type_mouvement == 'entree'
            ).count()
        except Exception as e:
            current_app.logger.error(f"Erreur lors du comptage des entrées: {str(e)}")
            total_entrees = 0
        
        # Compter le nombre total de sorties
        try:
            total_sorties = db.session.query(MouvementStock).filter(
                MouvementStock.type_mouvement == 'sortie'
            ).count()
        except Exception as e:
            current_app.logger.error(f"Erreur lors du comptage des sorties: {str(e)}")
            total_sorties = 0
        
        # Récupérer les 5 derniers mouvements avec les informations du produit
        try:
            derniers_mouvements = db.session.query(
                MouvementStock,
                Produit.nom.label('produit_nom')
            ).outerjoin(
                Produit, MouvementStock.produit_id == Produit.id
            ).order_by(
                MouvementStock.date_mouvement.desc()
            ).limit(5).all()
            
            # Formater les résultats
            mouvements_formates = []
            for m, produit_nom in derniers_mouvements:
                mouvements_formates.append({
                    'id': m.id,
                    'type': m.type_mouvement,
                    'produit_id': m.produit_id,
                    'produit_nom': produit_nom,
                    'quantite': float(m.quantite) if m.quantite is not None else 0.0,
                    'date': m.date_mouvement.isoformat() if m.date_mouvement else None,
                    'reference': m.reference,
                    'utilisateur_id': m.utilisateur_id,
                    'date_creation': m.date_creation.isoformat() if hasattr(m, 'date_creation') and m.date_creation else None
                })
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la récupération des derniers mouvements: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            mouvements_formates = []
        
        # Vérifier la structure de la table
        try:
            colonnes = [c['name'] for c in inspector.get_columns('mouvement_stock')]
            current_app.logger.info(f"Colonnes de la table mouvement_stock: {colonnes}")
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la récupération des colonnes: {str(e)}")
            colonnes = []
        
        result = {
            'total_entrees': total_entrees,
            'total_sorties': total_sorties,
            'derniers_mouvements': mouvements_formates,
            'structure_table': {
                'nom': 'mouvement_stock',
                'colonnes': colonnes,
                'nombre_total': db.session.query(MouvementStock).count()
            }
        }
        
        current_app.logger.info("Débogage des mouvements terminé avec succès")
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        error_msg = f"Erreur lors du débogage des mouvements: {str(e)}"
        current_app.logger.error(error_msg)
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': error_msg,
            'traceback': traceback.format_exc()
        }), 500

@stock_bp.route('/api/mouvements/stock', methods=['POST'])
@login_required
def api_mouvements_stock():
    """
    API pour la liste paginée des mouvements de stock (pour DataTables)
    """
    current_app.logger.info("Début de la fonction api_mouvements_stock")
    try:
        # Récupérer les données de la requête (form ou json)
        current_app.logger.info(f"Headers: {request.headers}")
        current_app.logger.info(f"Content-Type: {request.content_type}")
        current_app.logger.info(f"Données brutes: {request.get_data()}")
        
        if request.is_json or request.content_type == 'application/json':
            try:
                data = request.get_json()
                current_app.logger.info(f"Données JSON reçues: {data}")
                draw = int(data.get('draw', 1))
                start = int(data.get('start', 0))
                length = int(data.get('length', 10))
                date_debut = data.get('dateDebut')
                date_fin = data.get('dateFin')
                type_mouvement = data.get('typeMouvement')
                order = data.get('order', [{}])[0] if data.get('order') else {}
                order_column = int(order.get('column', 0))
                order_dir = order.get('dir', 'desc')
            except Exception as e:
                current_app.logger.error(f"Erreur lors du parsing JSON: {str(e)}")
                return jsonify({'error': 'Format de requête invalide'}), 400
        else:
            draw = int(request.form.get('draw', 1))
            start = int(request.form.get('start', 0))
            length = int(request.form.get('length', 10))
            date_debut = request.form.get('dateDebut')
            date_fin = request.form.get('dateFin')
            type_mouvement = request.form.get('typeMouvement')
            order_column = int(request.form.get('order[0][column]', 0))
            order_dir = request.form.get('order[0][dir]', 'desc')
        
        current_app.logger.info(f"Paramètres: draw={draw}, start={start}, length={length}, date_debut={date_debut}, date_fin={date_fin}, type_mouvement={type_mouvement}")
        
        # Construire la requête de base avec des labels explicites
        current_app.logger.info("Construction de la requête avec jointures...")
        
        query = db.session.query(
            MouvementStock,
            Produit.reference.label('produit_reference'),
            Produit.nom.label('produit_nom'),  # Utilisation de 'nom' au lieu de 'designation'
            User.nom.label('user_nom'),
            User.prenom.label('user_prenom')
        ).outerjoin(
            Produit, MouvementStock.produit_id == Produit.id
        ).outerjoin(
            User, MouvementStock.utilisateur_id == User.id
        )
        
        # Appliquer les filtres
        if date_debut:
            query = query.filter(MouvementStock.date_mouvement >= date_debut)
        if date_fin:
            # Ajouter 1 jour pour inclure toute la journée de fin
            date_fin_dt = datetime.strptime(date_fin, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(MouvementStock.date_mouvement < date_fin_dt)
        if type_mouvement:
            query = query.filter(MouvementStock.type_mouvement == type_mouvement)
        
        # Compter le nombre total de résultats (sans pagination)
        try:
            total_records = query.count()
            current_app.logger.info(f"Nombre total d'enregistrements: {total_records}")
        except Exception as e:
            current_app.logger.error(f"Erreur lors du comptage des enregistrements: {str(e)}")
            return jsonify({'error': 'Erreur lors du comptage des enregistrements'}), 500
        
        # Mapper les colonnes triables avec les bons noms de colonnes
        column_mapping = {
            0: 'MouvementStock.date_mouvement',
            1: 'produit_reference',
            2: 'produit_nom',  # Changé de produit_designation à produit_nom
            3: 'MouvementStock.type_mouvement',
            4: 'MouvementStock.quantite',
            5: 'MouvementStock.prix_unitaire',
            6: 'MouvementStock.montant_total',
            7: 'user_nom',  # Nom de l'utilisateur
        }
        
        current_app.logger.info(f"Mapping des colonnes: {column_mapping}")
        current_app.logger.info(f"Ordre demandé: colonne={order_column}, direction={order_dir}")
        
        # Vérifier si la colonne de tri est valide
        if order_column not in column_mapping:
            current_app.logger.warning(f"Colonne de tri invalide: {order_column}. Utilisation de la date par défaut.")
            order_column = 0  # Utiliser la date par défaut
        
        # Appliquer le tri
        try:
            if order_column in column_mapping:
                order_field = column_mapping[order_column]
                
                # Gérer le tri ascendant/descendant
                if order_dir == 'desc':
                    order_expr = getattr(MouvementStock if order_field.startswith('MouvementStock') else None, 
                                      order_field.split('.')[-1], None).desc()
                else:
                    order_expr = getattr(MouvementStock if order_field.startswith('MouvementStock') else None, 
                                      order_field.split('.')[-1], None).asc()
                
                if order_expr is not None:
                    query = query.order_by(order_expr)
                    current_app.logger.info(f"Tri appliqué: {order_field} ({order_dir})")
                else:
                    # Si le champ n'est pas trouvé dans MouvementStock, essayer avec un accès direct
                    if order_dir == 'desc':
                        query = query.order_by(db.desc(order_field))
                    else:
                        query = query.order_by(order_field)
                    current_app.logger.info(f"Tri direct appliqué: {order_field} ({order_dir})")
        except Exception as e:
            current_app.logger.error(f"Erreur lors de l'application du tri: {str(e)}\n{traceback.format_exc()}")
            # Continuer sans tri en cas d'erreur
            query = query.order_by(MouvementStock.date_mouvement.desc())
            current_app.logger.info("Tri par défaut appliqué: date_mouvement DESC")
        
        # Appliquer la pagination
        try:
            current_app.logger.info(f"Application de la pagination: offset={start}, limit={length}")
            mouvements = query.offset(start).limit(length).all()
            current_app.logger.info(f"Nombre de mouvements récupérés: {len(mouvements)}")
            
            # Formater les résultats pour DataTables
            data = []
            current_app.logger.info(f"Formatage de {len(mouvements)} mouvements...")
            
            for row in mouvements:
                try:
                    mvt = row[0]  # L'objet MouvementStock
                    ref = getattr(row, 'produit_reference', '')
                    nom_produit = getattr(row, 'produit_nom', 'Produit inconnu')  # Changé de designation à nom
                    nom_utilisateur = getattr(row, 'user_nom', '')
                    prenom_utilisateur = getattr(row, 'user_prenom', '')
                    
                    # Créer l'entrée avec des valeurs par défaut sécurisées
                    entry = {
                        'DT_RowId': f'mvt_{mvt.id}',
                        'date': mvt.date_mouvement.isoformat() if mvt.date_mouvement else '',
                        'reference': ref if ref is not None else 'N/A',
                        'designation': nom_produit,  # Utilisation de nom_produit au lieu de designation
                        'type_mouvement': mvt.type_mouvement or 'inconnu',
                        'quantite': float(mvt.quantite) if mvt.quantite is not None else 0,
                        'prix_unitaire': float(mvt.prix_unitaire) if mvt.prix_unitaire is not None else 0,
                        'montant_total': float(mvt.montant_total) if mvt.montant_total is not None else 0,
                        'utilisateur': f"{prenom_utilisateur or ''} {nom_utilisateur or ''}".strip() or 'Système',
                        'commentaire': str(mvt.commentaire) if mvt.commentaire else ''
                    }
                    
                    # Calculer le montant total si nécessaire
                    if entry['montant_total'] == 0 and entry['quantite'] and entry['prix_unitaire']:
                        entry['montant_total'] = entry['quantite'] * entry['prix_unitaire']
                    
                    data.append(entry)
                    
                except Exception as e:
                    current_app.logger.error(f"Erreur lors du formatage d'un mouvement (ID: {getattr(mvt, 'id', 'inconnu')}): {str(e)}")
                    continue
            
            current_app.logger.info(f"{len(data)} mouvements formatés avec succès")
            
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la récupération des données: {str(e)}")
            return jsonify({
                'draw': draw,
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
                'error': str(e)
            }), 500
        
        # Préparer la réponse
        response_data = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': total_records,
            'data': data
        }
        
        current_app.logger.info(f"Réponse envoyée: {len(data)} mouvements sur {total_records}")
        return jsonify(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Erreur inattendue dans api_mouvements_stock: {str(e)}", exc_info=True)
        return jsonify({
            'draw': request.form.get('draw', 1),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': str(e)
        }), 500

@stock_bp.route('/api/produits', methods=['GET'])
@stock_bp.route('/gestion-stock/api/produits', methods=['GET'])
@login_required
def api_get_produits():
    """
    API pour récupérer la liste des produits, avec filtrage par catégorie et zone
    """
    try:
        # Récupérer les paramètres de filtrage
        categorie_id = request.args.get('categorie_id')
        
        # Construire la requête de base
        query = Produit.query
        
        # JOUR 3: Filtrer par zone de l'utilisateur
        from rbac_stock import filter_produits_by_zone
        query = filter_produits_by_zone(query, current_user)
        
        # Appliquer le filtre de catégorie si spécifié
        if categorie_id:
            query = query.filter_by(categorie_id=categorie_id)
        
        # Exécuter la requête
        produits = query.all()
        
        # Formater les résultats
        produits_data = []
        for produit in produits:
            produits_data.append({
                'id': produit.id,
                'reference': produit.reference,
                'nom': produit.nom,
                'description': produit.description,
                'quantite': float(produit.quantite) if hasattr(produit, 'quantite') else 0,
                'seuil_alerte': float(produit.seuil_alerte) if hasattr(produit, 'seuil_alerte') else 0,
                'prix_achat': float(produit.prix_achat) if produit.prix_achat else 0,
                'code_barres': produit.code_barres or '',
                'emplacement': produit.emplacement.designation if produit.emplacement else 'Non spécifié',
                'categorie_id': produit.categorie_id,
                'categorie_nom': produit.categorie.nom if produit.categorie else ''
            })
        
        return jsonify({
            'success': True,
            'produits': produits_data,
            'total': len(produits_data)
        })
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des produits: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': 'Erreur lors de la récupération des produits',
            'error': str(e)
        }), 500

@stock_bp.route('/api/produits/<int:produit_id>')
@stock_bp.route('/gestion-stock/api/produits/<int:produit_id>')
@login_required
def api_get_produit(produit_id):
    """
    API pour récupérer les détails d'un produit
    Filtre par zone pour magasinier
    """
    try:
        produit = db.session.get(Produit, produit_id)
        if not produit:
            abort(404)
        
        # NOUVEAU: Vérifier accès zone magasinier
        if current_user.role.lower() == 'magasinier':
            # Produit doit avoir un emplacement dans la zone magasinier
            if not produit.emplacement or produit.emplacement.zone_id != current_user.zone_id:
                abort(403, "Accès refusé. Produit en dehors de votre zone")
        
        return jsonify({
            'success': True,
            'produit': {
                'id': produit.id,
                'reference': produit.reference,
                'designation': produit.nom,  # Using 'nom' instead of 'designation'
                'description': produit.description,
                'categorie': produit.categorie.nom if produit.categorie else None,
                'quantite': float(produit.quantite) if hasattr(produit, 'quantite') else 0.0,
                'seuil_alerte': float(produit.stock_min) if hasattr(produit, 'stock_min') and produit.stock_min is not None else 0.0,
                'unite_mesure': produit.unite_mesure if hasattr(produit, 'unite_mesure') else None,
                'prix_achat': float(produit.prix_achat) if hasattr(produit, 'prix_achat') and produit.prix_achat is not None else None,
                'prix_vente': float(produit.prix_vente) if hasattr(produit, 'prix_vente') and produit.prix_vente is not None else None,
                'emplacement': produit.emplacement if hasattr(produit, 'emplacement') else None,
                'date_creation': produit.date_creation.isoformat() if hasattr(produit, 'date_creation') and produit.date_creation else None,
                'date_maj': produit.date_maj.isoformat() if hasattr(produit, 'date_maj') and produit.date_maj else None
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error in api_get_produit: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@stock_bp.route('/api/produits/<int:produit_id>/ajuster-stock', methods=['POST'])
@login_required
def api_ajuster_stock(produit_id):
    """
    API pour ajuster manuellement le stock d'un produit
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Aucune donnée fournie.'
            }), 400
            
        # Récupérer les données de la requête
        type_ajustement = data.get('type')
        quantite = float(data.get('quantite', 0))
        raison = data.get('raison', '').strip()
        
        # Validation des données
        if not type_ajustement or type_ajustement not in ['ajout', 'retrait', 'correction']:
            return jsonify({
                'success': False,
                'message': 'Type d\'ajustement invalide. Doit être \'ajout\', \'retrait\' ou \'correction\''
            }), 400
            
        if quantite <= 0:
            return jsonify({
                'success': False,
                'message': 'La quantité doit être supérieure à zéro.'
            }), 400
            
        if not raison:
            return jsonify({
                'success': False,
                'message': 'Veuillez indiquer une raison pour cet ajustement.'
            }), 400
            
        # Récupérer le produit
        produit = db.session.get(Produit, produit_id)
        if not produit:
            abort(404)
        
        # Calculer la nouvelle quantité en fonction du type d'ajustement
        ancienne_quantite = produit.quantite
        
        if type_ajustement == 'ajout':
            nouvelle_quantite = ancienne_quantite + quantite
        elif type_ajustement == 'retrait':
            nouvelle_quantite = max(0, ancienne_quantite - quantite)  # Ne pas aller en dessous de zéro
        else:  # correction
            nouvelle_quantite = quantite
            
        # Calculer la différence
        difference = nouvelle_quantite - ancienne_quantite
        # Déterminer type mouvement pour affecter stock
        if difference > 0:
            mouvement_type = 'entree'
            quantite_mouvement = float(difference)
        else:
            mouvement_type = 'sortie'
            quantite_mouvement = float(abs(difference))

        mouvement = MouvementStock(
            produit_id=produit.id,
            type_mouvement=mouvement_type,
            quantite=quantite_mouvement,
            prix_unitaire=produit.prix_achat if hasattr(produit, 'prix_achat') else 0,
            montant_total=quantite_mouvement * (produit.prix_achat if hasattr(produit, 'prix_achat') else 0),
            utilisateur_id=current_user.id,
            commentaire=f"Ajustement manuel: {raison} (Ancien stock: {ancienne_quantite}, Nouveau stock: {nouvelle_quantite})",
            date_mouvement=datetime.now(timezone.utc),
            reference=f"AJUST-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            date_reference=datetime.now(timezone.utc).date()
        )
        
        # Enregistrer le mouvement et mettre à jour la date de mise à jour
        produit.date_maj = datetime.now(timezone.utc)
        produit.modifie_par = current_user.id
        db.session.add(mouvement)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Stock ajusté avec succès.',
            'nouvelle_quantite': nouvelle_quantite,
            'ancienne_quantite': ancienne_quantite,
            'difference': difference
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur lors de l'ajustement du stock: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f"Une erreur est survenue lors de l'ajustement du stock: {str(e)}"
        }), 500

@stock_bp.route('/api/produits/<int:produit_id>/mouvements')
@stock_bp.route('/gestion-stock/api/produits/<int:produit_id>/mouvements')
@login_required
def api_get_mouvements_produit(produit_id):
    """
    API pour récupérer l'historique des mouvements d'un produit
    Filtre par zone pour magasinier
    """
    try:
        # Vérifier que le produit existe
        produit = db.session.get(Produit, produit_id)
        if not produit:
            abort(404)
        
        # Zone-based access control for magasinier
        if current_user.role.lower() == 'magasinier':
            if not produit.emplacement or produit.emplacement.zone_id != current_user.zone_id:
                abort(403, 'Accès refusé: produit d\'une autre zone')
        
        # Récupérer les 50 derniers mouvements
        mouvements = MouvementStock.query.filter_by(
            produit_id=produit_id
        ).order_by(
            MouvementStock.date_mouvement.desc()
        ).limit(50).all()
        
        return jsonify({
            'success': True,
            'mouvements': [{
                'id': m.id,
                'date': m.date_mouvement.isoformat(),
                'type': m.type_mouvement,
                'quantite': float(m.quantite),
                'prix_unitaire': float(m.prix_unitaire) if m.prix_unitaire else None,
                'montant_total': float(m.montant_total) if m.montant_total else None,
                'utilisateur': f"{m.utilisateur.prenom} {m.utilisateur.nom}",
                'commentaire': m.commentaire,
                'reference': m.reference
            } for m in mouvements]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@stock_bp.route('/api/produits/<int:produit_id>/historique-stock')
@stock_bp.route('/gestion-stock/api/produits/<int:produit_id>/historique-stock')
@login_required
def api_historique_stock(produit_id):
    """
    API pour récupérer l'historique du stock d'un produit sur les 30 derniers jours
    Filtre par zone pour magasinier
    """
    try:
        # Vérifier que le produit existe
        produit = db.session.get(Produit, produit_id)
        if not produit:
            abort(404)
        
        # Zone-based access control for magasinier
        if current_user.role.lower() == 'magasinier':
            if not produit.emplacement or produit.emplacement.zone_id != current_user.zone_id:
                abort(403, 'Accès refusé: produit d\'une autre zone')
        
        # Date d'il y a 30 jours
        date_debut = datetime.now() - timedelta(days=30)
        
        # Récupérer les mouvements du produit
        mouvements = db.session.query(
            func.date(MouvementStock.date_mouvement).label('date'),
            func.sum(
                case_sql([
                    (MouvementStock.type_mouvement == 'entree', MouvementStock.quantite),
                ], else_=0)
            ).label('entrees'),
            func.sum(
                case_sql([
                    (MouvementStock.type_mouvement == 'sortie', MouvementStock.quantite),
                ], else_=0)
            ).label('sorties')
        ).filter(
            MouvementStock.produit_id == produit_id,
            MouvementStock.date_mouvement >= date_debut
        ).group_by(
            func.date(MouvementStock.date_mouvement)
        ).order_by(
            func.date(MouvementStock.date_mouvement)
        ).all()
        
        # Créer un dictionnaire des mouvements par date
        mouvements_par_date = {}
        for date_mvt, entrees, sorties in mouvements:
            date_str = date_mvt.strftime('%Y-%m-%d')
            mouvements_par_date[date_str] = {
                'entrees': float(entrees or 0),
                'sorties': float(sorties or 0)
            }
        
        # Générer la série de dates complète
        dates = [(date_debut + timedelta(days=i)).strftime('%Y-%m-%d') 
                for i in range(31)]  # 30 jours + aujourd'hui
        
        # Calculer le stock pour chaque jour
        stock_initial = db.session.query(
            func.sum(
                case_sql([
                    (MouvementStock.type_mouvement == 'entree', MouvementStock.quantite),
                    (MouvementStock.type_mouvement == 'sortie', -MouvementStock.quantite)
                ], else_=0)
            )
        ).filter(
            MouvementStock.produit_id == produit_id,
            MouvementStock.date_mouvement < date_debut
        ).scalar() or 0
        
        stock_courant = float(stock_initial)
        donnees_stock = []
        
        for date_str in dates:
            # Ajouter les mouvements de la journée
            mouvements_jour = mouvements_par_date.get(date_str, {'entrees': 0, 'sorties': 0})
            stock_courant += mouvements_jour['entrees'] - mouvements_jour['sorties']
            
            donnees_stock.append({
                'date': date_str,
                'stock': stock_courant
            })
        
        return jsonify({
            'success': True,
            'labels': [d['date'] for d in donnees_stock],
            'data': [d['stock'] for d in donnees_stock]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500



# ---------------------- New inventory helper endpoints ----------------------
@stock_bp.route('/api/produits/by-barcode/<string:code_barre>')
@login_required
def api_get_produit_by_barcode(code_barre):
    """Return product JSON for a given barcode (used by barcode scanner UI)."""
    try:
        produit = Produit.query.filter_by(code_barres=code_barre).first()
        if not produit:
            return jsonify({'success': False, 'message': 'Produit non trouvé'}), 404
        return jsonify({'success': True, 'produit': {
            'id': produit.id,
            'reference': produit.reference,
            'nom': produit.nom,
            'code_barres': produit.code_barres,
            'quantite': produit.quantite,
            'emplacement_id': produit.emplacement_id
        }})
    except Exception as e:
        current_app.logger.error(f"Erreur recherche produit par code-barres: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@stock_bp.route('/api/inventaire', methods=['POST'])
@login_required
@require_stock_permission('can_adjust_stock')
def api_inventaire_bulk():
    """
    Handle bulk inventory adjustments (JSON payload with list of items).
    
    ✅ PHASE 3 TÂCHE 3.2: Vérification de Zone (ÉLEVÉ)
    Zone filtering:
    - magasinier: Peut SEULEMENT créer ajustements pour sa zone
    - chef_zone: Peut SEULEMENT créer ajustements pour sa zone
    - chef_pur, admin: Peuvent créer pour TOUTES les zones

    Expected payload:
    {
        'items': [ {'produit_id': int, 'stock_reel': float, 'emplacement_id': int (optional), 'motif': str (optional)}, ... ],
        'commentaire': str (optional)
    }
    """
    data = request.get_json() or {}
    items = data.get('items', [])
    commentaire = data.get('commentaire', 'Inventaire')

    if not items:
        return jsonify({'success': False, 'message': 'Aucun item fourni'}), 400

    results = []
    try:
        from datetime import datetime
        from models import EmplacementStock
        
        for it in items:
            pid = it.get('produit_id')
            if not pid:
                results.append({'produit_id': None, 'success': False, 'message': 'produit_id manquant'})
                continue
            
            produit = db.session.get(Produit, pid)
            if not produit:
                results.append({'produit_id': pid, 'success': False, 'message': 'Produit introuvable'})
                continue
            
            try:
                stock_reel = float(it.get('stock_reel'))
            except Exception:
                results.append({'produit_id': pid, 'success': False, 'message': 'stock_reel invalide'})
                continue

            emplacement_id = it.get('emplacement_id')
            
            # ✅ NOUVEAU: Vérifier zone si magasinier/chef_zone
            if current_user.role in ['magasinier', 'chef_zone']:
                if emplacement_id:
                    # Vérifier que l'emplacement appartient à la zone de l'utilisateur
                    emplacement = db.session.get(EmplacementStock, emplacement_id)
                    if not emplacement:
                        results.append({
                            'produit_id': pid,
                            'success': False,
                            'message': f'Emplacement {emplacement_id} introuvable'
                        })
                        continue
                    
                    if emplacement.zone_id != current_user.zone_id:
                        current_app.logger.warning(
                            f"🔴 Zone access denied: user {current_user.id} (zone={current_user.zone_id}) "
                            f"tried to adjust inventory for emplacement in zone {emplacement.zone_id}"
                        )
                        results.append({
                            'produit_id': pid,
                            'success': False,
                            'message': f'Permission refusée: emplacement dans une autre zone'
                        })
                        continue
                else:
                    # Si emplacement_id pas fourni, utiliser un emplacement de sa zone
                    default_emplacement = EmplacementStock.query.filter_by(
                        zone_id=current_user.zone_id
                    ).first()
                    if default_emplacement:
                        emplacement_id = default_emplacement.id
                    else:
                        results.append({
                            'produit_id': pid,
                            'success': False,
                            'message': f'Aucun emplacement disponible dans votre zone'
                        })
                        continue
            
            motif = it.get('motif') or commentaire
            stock_calcule = produit.quantite
            difference = stock_reel - stock_calcule

            if abs(difference) < 1e-9:
                # Log inventory with zero difference
                mouvement = MouvementStock(
                    produit_id=produit.id,
                    type_mouvement='inventaire',
                    quantite=0,
                    quantite_reelle=stock_reel,
                    ecart=0,
                    utilisateur_id=current_user.id,
                    commentaire=f"Inventaire: {motif} (aucun écart)",
                    date_mouvement=datetime.now(timezone.utc),
                    emplacement_id=emplacement_id
                )
                db.session.add(mouvement)
                db.session.flush()
                results.append({'produit_id': pid, 'success': True, 'difference': 0, 'mouvement_id': mouvement.id})
                continue

            if difference > 0:
                mouvement_type = 'entree'
                quantite_mouvement = float(difference)
            else:
                mouvement_type = 'sortie'
                quantite_mouvement = float(abs(difference))

            mouvement = MouvementStock(
                produit_id=produit.id,
                type_mouvement=mouvement_type,
                quantite=quantite_mouvement,
                quantite_reelle=stock_reel,
                ecart=difference,
                utilisateur_id=current_user.id,
                commentaire=f"Inventaire: {motif} (écart: {difference})",
                date_mouvement=datetime.now(timezone.utc),
                emplacement_id=emplacement_id
            )
            db.session.add(mouvement)
            db.session.flush()
            results.append({'produit_id': pid, 'success': True, 'difference': difference, 'mouvement_id': mouvement.id})

        db.session.commit()
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur lors de l'enregistrement de l'inventaire: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Route pour afficher le tableau de bord de gestion des stocks
@stock_bp.route('/fournisseurs')
@login_required
def liste_fournisseurs():
    fournisseurs = Fournisseur.query.order_by(Fournisseur.raison_sociale).all()
    return render_template('fournisseurs/liste.html', fournisseurs=fournisseurs)

@stock_bp.route('/fournisseur/ajouter', methods=['GET', 'POST'])
@login_required
@require_stock_role('chef_pur', 'admin', 'gestionnaire_stock')
def ajouter_fournisseur():
    """
    Ajouter un fournisseur
    Autorisé: chef_pur, admin, gestionnaire_stock
    """
    form = FournisseurForm()
    if form.validate_on_submit():
        try:
            fournisseur = Fournisseur(
                code=form.code.data,
                raison_sociale=form.raison_sociale.data,
                contact=form.contact.data,
                telephone=form.telephone.data,
                email=form.email.data,
                adresse=form.adresse.data,
                actif=form.actif.data,
                date_creation=datetime.now(timezone.utc),
                date_maj=datetime.now(timezone.utc)
            )
            db.session.add(fournisseur)
            db.session.commit()
            flash('Fournisseur ajouté avec succès!', 'success')
            return redirect(url_for('stock.liste_fournisseurs'))
        except Exception as e:
            db.session.rollback()
            flash('Une erreur est survenue lors de l\'ajout du fournisseur.', 'danger')
            print(f"Erreur ajout fournisseur: {str(e)}")
    return render_template('fournisseurs/ajouter.html', form=form, title='Ajouter un fournisseur')

@stock_bp.route('/fournisseur/modifier/<int:id>', methods=['GET', 'POST'])
@login_required
@require_stock_role('chef_pur', 'admin', 'gestionnaire_stock')
def modifier_fournisseur(id):
    """
    Modifier un fournisseur
    Autorisé: chef_pur, admin, gestionnaire_stock
    """
    fournisseur = db.session.get(Fournisseur, id)
    if not fournisseur:
        abort(404)
    form = FournisseurForm(obj=fournisseur)
    
    if form.validate_on_submit():
        try:
            fournisseur.code = form.code.data
            fournisseur.raison_sociale = form.raison_sociale.data
            fournisseur.contact = form.contact.data
            fournisseur.telephone = form.telephone.data
            fournisseur.email = form.email.data
            fournisseur.adresse = form.adresse.data
            fournisseur.actif = form.actif.data
            fournisseur.date_maj = datetime.now(timezone.utc)
            
            db.session.commit()
            flash('Fournisseur mis à jour avec succès!', 'success')
            return redirect(url_for('stock.liste_fournisseurs'))
        except Exception as e:
            db.session.rollback()
            flash('Une erreur est survenue lors de la mise à jour du fournisseur.', 'danger')
            print(f"Erreur modification fournisseur: {str(e)}")
    
    return render_template('fournisseurs/modifier.html', form=form, fournisseur=fournisseur, title='Modifier un fournisseur')

@stock_bp.route('/fournisseur/supprimer/<int:id>', methods=['POST'])
@login_required
@require_stock_role('chef_pur', 'admin', 'gestionnaire_stock')
def supprimer_fournisseur(id):
    """
    Supprimer un fournisseur
    Autorisé: chef_pur, admin, gestionnaire_stock
    """
    fournisseur = db.session.get(Fournisseur, id)
    if not fournisseur:
        abort(404)
    try:
        # Vérifier si le fournisseur est utilisé dans des produits
        produits_count = Produit.query.filter_by(fournisseur_id=id).count()
        if produits_count > 0:
            flash('Impossible de supprimer ce fournisseur car il est associé à des produits.', 'warning')
        else:
            db.session.delete(fournisseur)
            db.session.commit()
            flash('Fournisseur supprimé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Une erreur est survenue lors de la suppression du fournisseur.', 'danger')
        print(f"Erreur suppression fournisseur: {str(e)}")
    
    return redirect(url_for('stock.liste_fournisseurs'))

@stock_bp.route('/')
@login_required
def gestion_stock():
    """
    Affiche le tableau de bord de gestion des stocks
    Route agnostique aux rôles - redirige vers l'interface appropriée
    
    - Pour magainiers: redirige vers 'liste_produits_zone' (vue zone uniquement)
    - Pour autres: redirige vers 'liste_produits' (vue globale, nécessite permission)
    """
    # PHASE 2 FIX: Route magainier vers sa vue zone, pas vers globale
    if current_user.role == 'magasinier':
        return redirect(url_for('stock.liste_produits_zone'))
    
    # Pour les autres rôles: rediriger vers liste globale (avec permission check)
    # Cette route applique la permission check nécessaire
    return redirect(url_for('stock.liste_produits'))

@stock_bp.route('/produit/ajouter', methods=['GET', 'POST'])
@login_required
@require_stock_permission('can_create_produit')
def ajouter_produit():
    """
    Affiche le formulaire d'ajout d'un nouveau produit
    Autorisé: chef_pur, gestionnaire_stock, admin
    """
    from models import EmplacementStock
    
    form = ProduitForm()
    
    # Remplir les choix de catégories, fournisseurs et emplacements
    form.categorie_id.choices = [(c.id, c.nom) for c in Categorie.query.order_by('nom').all()]
    form.fournisseur_id.choices = [(0, 'Aucun')] + [(f.id, f.raison_sociale) for f in Fournisseur.query.filter_by(actif=True).order_by('raison_sociale').all()]
    
    # Remplir les choix d'emplacement
    emplacements = EmplacementStock.query.filter_by(actif=True).order_by('designation').all()
    if not emplacements:
        # Créer des emplacements par défaut si aucun n'existe
        emplacements = [
            EmplacementStock(designation='Entrepôt Principal', code='ENTREPOT', actif=True),
            EmplacementStock(designation='Magasin', code='MAGASIN', actif=True),
            EmplacementStock(designation='Atelier', code='ATELIER', actif=True)
        ]
        db.session.bulk_save_objects(emplacements)
        db.session.commit()
    
    form.emplacement_id.choices = [(0, 'Non spécifié')] + [(e.id, e.designation) for e in emplacements]
    
    if form.validate_on_submit():
        try:
            # Création du produit avec les données du formulaire
            produit = Produit(
                reference=form.reference.data,
                code_barres=form.code_barres.data if form.code_barres.data else None,
                nom=form.nom.data,
                description=form.description.data,
                categorie_id=form.categorie_id.data,
                fournisseur_id=form.fournisseur_id.data if form.fournisseur_id.data != 0 else None,
                emplacement_id=form.emplacement_id.data if form.emplacement_id.data != 0 else None,
                prix_achat=float(form.prix_achat.data) if form.prix_achat.data else None,
                prix_vente=float(form.prix_vente.data) if form.prix_vente.data else None,
                tva=float(form.tva.data) if form.tva.data else 0.0,
                unite_mesure=form.unite_mesure.data if form.unite_mesure.data else None,
                stock_min=int(form.stock_min.data) if form.stock_min.data else None,
                stock_max=int(form.stock_max.data) if form.stock_max.data else None,
                actif=form.actif.data
            )
            
            db.session.add(produit)
            db.session.flush()  # Pour obtenir l'ID du produit
            
            # Générer un code-barres pour le produit
            try:
                barcode_filename = generate_barcode(produit.id, produit.reference)
                if barcode_filename:
                    # Mettre à jour le produit avec le nom du fichier du code-barres
                    produit.code_barres = barcode_filename
                    db.session.commit()
            except Exception as e:
                current_app.logger.error(f"Erreur lors de la génération du code-barres : {str(e)}")
                db.session.rollback()
                # Continuer même en cas d'échec de génération du code-barres
            
            # Créer un mouvement d'entrée de stock initial si une quantité est spécifiée
            if form.quantite.data and float(form.quantite.data) > 0:
                mouvement = MouvementStock(
                    type_mouvement='entree',
                    produit_id=produit.id,
                    quantite=float(form.quantite.data),
                    prix_unitaire=float(form.prix_achat.data) if form.prix_achat.data else 0.0,
                    utilisateur_id=current_user.id,
                    emplacement_id=form.emplacement_id.data if form.emplacement_id.data != 0 else None,
                    commentaire="Stock initial",
                    date_mouvement=datetime.now(timezone.utc)
                )
                db.session.add(mouvement)
            
            db.session.commit()
            flash('Produit ajouté avec succès!', 'success')
            return redirect(url_for('stock.liste_produits'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de l\'ajout du produit : {str(e)}', 'danger')
            current_app.logger.error(f'Erreur ajout produit: {str(e)}')
            current_app.logger.error(traceback.format_exc())
    
    # Initialisation des valeurs par défaut pour le formulaire
    if not form.is_submitted():
        form.prix_achat.data = None
        form.prix_vente.data = None
        form.tva.data = 0.0
        form.unite_mesure.data = ''
        form.stock_min.data = None
        form.stock_max.data = None
        form.actif.data = True
        
    return render_template('ajouter_produit.html', form=form, title='Ajouter un produit')

@stock_bp.route('/produit/modifier/<int:id>', methods=['GET', 'POST'])
@login_required
@require_stock_permission('can_modify_produit')
def modifier_produit(id):
    """
    Modifie un produit existant
    Autorisé: chef_pur, admin
    """
    from models import EmplacementStock
    
    produit = db.session.get(Produit, id)
    if not produit:
        abort(404)
    form = ProduitForm(obj=produit)
    
    # Remplir les choix de catégories, fournisseurs et emplacements
    form.categorie_id.choices = [(c.id, c.nom) for c in Categorie.query.order_by('nom').all()]
    form.fournisseur_id.choices = [(0, 'Aucun')] + [(f.id, f.raison_sociale) for f in Fournisseur.query.filter_by(actif=True).order_by('raison_sociale').all()]
    
    # Remplir les choix d'emplacement
    emplacements = EmplacementStock.query.filter_by(actif=True).order_by('designation').all()
    form.emplacement_id.choices = [(0, 'Non spécifié')] + [(e.id, e.designation) for e in emplacements]
    
    if form.validate_on_submit():
        try:
            # Mise à jour du produit avec les données du formulaire
            produit.reference = form.reference.data
            produit.code_barres = form.code_barres.data if form.code_barres.data else None
            produit.nom = form.nom.data
            produit.description = form.description.data
            produit.categorie_id = form.categorie_id.data
            produit.fournisseur_id = form.fournisseur_id.data if form.fournisseur_id.data != 0 else None
            produit.emplacement_id = form.emplacement_id.data if form.emplacement_id.data != 0 else None
            produit.prix_achat = float(form.prix_achat.data) if form.prix_achat.data else None
            produit.prix_vente = float(form.prix_vente.data) if form.prix_vente.data else None
            produit.tva = float(form.tva.data) if form.tva.data else 0.0
            produit.unite_mesure = form.unite_mesure.data if form.unite_mesure.data else None
            produit.stock_min = int(form.stock_min.data) if form.stock_min.data else None
            produit.stock_max = int(form.stock_max.data) if form.stock_max.data else None
            produit.actif = form.actif.data
            produit.date_mise_a_jour = datetime.now(timezone.utc)
            produit.modifie_par = current_user.id
            
            db.session.commit()
            flash('Produit modifié avec succès!', 'success')
            return redirect(url_for('stock.liste_produits'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification du produit : {str(e)}', 'danger')
            current_app.logger.error(f'Erreur modification produit: {str(e)}')
            current_app.logger.error(traceback.format_exc())
    
    # Pré-remplir le formulaire avec les données actuelles du produit
    form.reference.data = produit.reference
    form.code_barres.data = produit.code_barres
    form.nom.data = produit.nom
    form.description.data = produit.description
    form.categorie_id.data = produit.categorie_id
    form.fournisseur_id.data = produit.fournisseur_id if produit.fournisseur_id else 0
    form.emplacement_id.data = produit.emplacement_id if produit.emplacement_id else 0
    form.prix_achat.data = float(produit.prix_achat) if produit.prix_achat is not None else None
    form.prix_vente.data = float(produit.prix_vente) if produit.prix_vente is not None else None
    form.tva.data = float(produit.tva) if produit.tva is not None else 0.0
    form.unite_mesure.data = produit.unite_mesure
    form.stock_min.data = int(produit.stock_min) if produit.stock_min is not None else None
    form.stock_max.data = int(produit.stock_max) if produit.stock_max is not None else None
    form.actif.data = produit.actif
    
    return render_template('ajouter_produit.html', form=form, title='Modifier un produit', produit=produit)

@stock_bp.route('/produits-zone')
@login_required
def liste_produits_zone():
    """
    Affiche la liste des produits pour la zone du magasinier
    Route pour magasiniers - Vue zone uniquement
    """
    from zone_rbac import filter_produit_by_emplacement_zone
    
    # Vérifier que l'utilisateur est magasinier avec une zone assignée
    if current_user.role != 'magasinier':
        flash('❌ Accès réservé aux magasiniers', 'danger')
        return redirect(url_for('dashboard'))
    
    if not current_user.zone_id:
        flash('❌ Vous n\'êtes pas assigné à une zone', 'danger')
        return redirect(url_for('dashboard'))
    
    # Récupérer les paramètres de tri
    sort = request.args.get('sort', 'id')
    direction = request.args.get('direction', 'asc')
    
    # Construire la requête de base filtrée par zone
    query = Produit.query.options(
        db.joinedload(Produit.categorie),
        db.joinedload(Produit.emplacement),
        db.joinedload(Produit.mouvements)
    )
    
    # Appliquer le filtre zone
    query = filter_produit_by_emplacement_zone(query)
    
    # Appliquer le tri
    if hasattr(Produit, sort):
        column = getattr(Produit, sort)
        if direction == 'desc':
            column = column.desc()
        query = query.order_by(column)
    
    # Récupérer tous les produits de la zone
    produits = query.all()
    
    # Forcer le chargement de la propriété quantite pour chaque produit
    for produit in produits:
        _ = produit.quantite  # Force le chargement de la propriété quantite
    
    # Calculer le nombre de produits par emplacement (zone filtrée)
    from collections import defaultdict
    emplacements = defaultdict(int)
    total_produits = len(produits)
    
    # Compter les produits par emplacement
    for produit in produits:
        if produit.emplacement:
            emplacement_nom = produit.emplacement.designation if hasattr(produit.emplacement, 'designation') else 'Non spécifié'
            emplacements[emplacement_nom] += 1
    
    # Convertir le dictionnaire en liste de dictionnaires pour le template
    emplacements_liste = [{'nom': nom, 'nombre': nombre} for nom, nombre in emplacements.items()]
    
    # Debug logging
    current_app.logger.info(f"🏪 Magasinier {current_user.username} (Zone {current_user.zone_id})")
    current_app.logger.info(f"   Produits trouvés: {total_produits}")
    current_app.logger.info(f"   Emplacements: {len(emplacements_liste)}")
    
    # Fetch pending transfers for this zone
    from models import EmplacementStock
    mouvements_en_attente = MouvementStock.query.filter(
        MouvementStock.type_mouvement == 'entree',
        MouvementStock.workflow_state == 'EN_ATTENTE',
        MouvementStock.applique_au_stock == False
    ).join(EmplacementStock).filter(EmplacementStock.zone_id == current_user.zone_id).all()

    # Fetch pending technician reservations for this zone
    reservations_en_attente = db.session.query(ReservationPiece).join(
        Intervention, ReservationPiece.intervention_id == Intervention.id
    ).join(
        User, Intervention.technicien_id == User.id
    ).filter(
        User.zone_id == current_user.zone_id,
        ReservationPiece.statut == ReservationPiece.STATUT_EN_ATTENTE
    ).all()
    
    return render_template('produits_zone_magasinier.html', 
                         produits=produits,
                         mouvements_en_attente=mouvements_en_attente,
                         reservations_en_attente=reservations_en_attente,
                         sort=sort,
                         direction=direction,
                         emplacements=emplacements_liste,
                         total_produits=total_produits,
                         title='Produits de ma Zone')

@stock_bp.route('/historique-mouvements-zone')
@login_required
def historique_mouvements_zone():
    """
    Affiche l'historique des mouvements de stock pour la zone du magasinier
    PHASE 3 FIX: Page dédiée pour magainiers voyant leur historique stock
    """
    # Vérifier que l'utilisateur est magasinier avec une zone assignée
    if current_user.role != 'magasinier':
        flash('❌ Accès réservé aux magainiers', 'danger')
        return redirect(url_for('dashboard'))
    
    if not current_user.zone_id:
        flash('❌ Vous n\'êtes pas assigné à une zone', 'danger')
        return redirect(url_for('dashboard'))
    
    from zone_rbac import filter_mouvement_by_zone

    # Récupérer les mouvements de la zone du magasinier (derniers 30 jours)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    mouvements_query = db.session.query(MouvementStock).filter(
        MouvementStock.date_mouvement >= thirty_days_ago
    )
    
    # Appliquer le filtre zone
    mouvements = filter_mouvement_by_zone(mouvements_query).all()
    
    # Trier par date décroissante
    mouvements = sorted(mouvements, key=lambda m: m.date_mouvement, reverse=True)
    
    # Récupérer les statistiques
    entrees = sum(m.quantite for m in mouvements if m.type_mouvement == 'entree')
    sorties = sum(m.quantite for m in mouvements if m.type_mouvement == 'sortie')
    
    current_app.logger.info(f"🏪 Historique zone - Magasinier {current_user.username} (Zone {current_user.zone_id})")
    current_app.logger.info(f"   Mouvements trouvés: {len(mouvements)}")
    current_app.logger.info(f"   Entrées: {entrees}, Sorties: {sorties}")
    
    return render_template('historique_mouvements_zone.html',
                         mouvements=mouvements,
                         entrees=entrees,
                         sorties=sorties,
                         total_mouvements=len(mouvements),
                         title='Historique des Mouvements - Zone')

@stock_bp.route('/produits')
@login_required
@require_stock_permission('can_view_global_stock')
def liste_produits():
    """
    Affiche la liste des produits
    REQUIRES: can_view_global_stock permission (chef_pur, gestionnaire_stock, direction, admin)
    """
    # Récupérer les paramètres de tri
    sort = request.args.get('sort', 'id')
    direction = request.args.get('direction', 'asc')
    
    # Construire la requête de base avec chargement des relations nécessaires
    query = Produit.query.options(
        db.joinedload(Produit.categorie),
        db.joinedload(Produit.emplacement),
        db.joinedload(Produit.mouvements)
    )
    
    # Appliquer le tri
    if hasattr(Produit, sort):
        column = getattr(Produit, sort)
        if direction == 'desc':
            column = column.desc()
        query = query.order_by(column)
    
    # Désactiver la pagination et récupérer tous les produits
    produits = query.all()
    
    # Forcer le chargement de la propriété quantite pour chaque produit
    for produit in produits:
        _ = produit.quantite  # Force le chargement de la propriété quantite
    
    # Calculer le nombre de produits par emplacement
    from collections import defaultdict
    emplacements = defaultdict(int)
    total_produits = 0
    
    # Compter les produits par emplacement
    for produit in Produit.query.all():
        if produit.emplacement:
            emplacement_nom = produit.emplacement.designation if hasattr(produit.emplacement, 'designation') else 'Non spécifié'
            emplacements[emplacement_nom] += 1
            total_produits += 1
    
    # Convertir le dictionnaire en liste de dictionnaires pour le template
    emplacements_liste = [{'nom': nom, 'nombre': nombre} for nom, nombre in emplacements.items()]
    
    # Debug: Afficher les données des emplacements dans la console
    current_app.logger.info("=== DEBUG EMPLACEMENTS ===")
    current_app.logger.info(f"Nombre d'emplacements: {len(emplacements_liste)}")
    for emp in emplacements_liste:
        current_app.logger.info(f"- {emp['nom']}: {emp['nombre']} produits")
    current_app.logger.info(f"Total produits: {total_produits}")
    current_app.logger.info("=========================")
    
    # Récupérer les zones pour le dispatching (filtrage robuste pour MySQL/MariaDB)
    toutes_zones = Zone.query.all()
    zones = [z for z in toutes_zones if getattr(z, 'actif', True)]
    
    return render_template('dashboard_gestion_stock.html', 
                         produits=produits,
                         sort=sort,
                         direction=direction,
                         emplacements=emplacements_liste,
                         total_produits=total_produits,
                         zones=zones,
                         title='Liste des produits')

@stock_bp.route('/produit/supprimer/<int:id>', methods=['POST'])
@login_required
@require_stock_role('chef_pur', 'admin')
def supprimer_produit(id):
    """
    Supprime définitivement un produit et ses mouvements de stock associés
    CRITIQUE: Autorisé SEUL à chef_pur et admin (accès très restreint)
    """
    produit = db.session.get(Produit, id)
    if not produit:
        abort(404)
    
    try:
        # Supprimer d'abord tous les mouvements de stock liés à ce produit
        MouvementStock.query.filter_by(produit_id=id).delete()
        
        # Ensuite supprimer le produit
        db.session.delete(produit)
        db.session.commit()
        
        flash('Produit et ses mouvements de stock supprimés avec succès!', 'success')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression du produit : {str(e)}', 'danger')
        current_app.logger.error(f'Erreur suppression produit: {str(e)}')
    
    return redirect(url_for('stock.liste_produits'))

@stock_bp.route('/produit/entree/<int:produit_id>', methods=['GET', 'POST'])
@login_required
@require_stock_permission('can_receive_stock')
def entree_stock(produit_id):
    """
    Gère les entrées en stock pour un produit
    Autorisé: chef_pur, gestionnaire_stock, magasinier, admin
    """
    from models import EmplacementStock
    
    produit = db.session.get(Produit, produit_id)
    if not produit:
        abort(404)
    form = EntreeStockForm()
    
    # Remplir les choix d'emplacement avant la validation
    # Filter by zone for magasiniers
    if current_user.role == 'magasinier':
        emplacements = EmplacementStock.query.filter_by(
            zone_id=current_user.zone_id,
            actif=True
        ).order_by('designation').all()
    else:
        emplacements = EmplacementStock.query.filter_by(actif=True).order_by('designation').all()
    
    if not emplacements:
        # Créer des emplacements par défaut si aucun n'existe
        emplacements = [
            EmplacementStock(designation='Entrepôt Principal', code='ENTREPOT', actif=True),
            EmplacementStock(designation='Magasin', code='MAGASIN', actif=True),
            EmplacementStock(designation='Atelier', code='ATELIER', actif=True)
        ]
        db.session.bulk_save_objects(emplacements)
        db.session.commit()
    
    form.emplacement_id.choices = [(e.id, e.designation) for e in emplacements]
    
    if form.validate_on_submit():
        try:
            # 🔴 NOUVEAU: SÉCURITÉ MAGASINIER - Vérifier que l'emplacement est dans sa zone
            emplacement_id = form.emplacement_id.data
            if current_user.role.lower() == 'magasinier':
                from zone_rbac import validate_emplacement_zone
                validate_emplacement_zone(emplacement_id)  # Lève abort(403) si zone différente
            
            quantite = form.quantite.data
            prix_unitaire = form.prix_unitaire.data if form.prix_unitaire.data else None
            commentaire = form.commentaire.data
            
            # Mise à jour du prix d'achat si fourni
            if prix_unitaire is not None and prix_unitaire > 0:
                produit.prix_achat = prix_unitaire
                # Mise à jour du prix de vente avec une marge par défaut de 30%
                if not produit.prix_vente or prix_unitaire * 1.3 > produit.prix_vente:
                    produit.prix_vente = round(prix_unitaire * 1.3, 2)
            
            # 🔴 PRODUCTION CRITICAL: Initialize workflow BEFORE creating mouvement
            mouvement = MouvementStock(
                produit_id=produit.id,
                type_mouvement='entree',
                quantite=quantite,
                prix_unitaire=prix_unitaire if prix_unitaire else produit.prix_achat,
                utilisateur_id=current_user.id,
                emplacement_id=form.emplacement_id.data,
                commentaire=commentaire,
                date_mouvement=datetime.now(timezone.utc),
                applique_au_stock=False  # ← CRITICAL: Never auto-apply until approved
            )
            
            # ✅ Enforce workflow state initialization
            mouvement = validate_and_initialize_mouvement_workflow(mouvement, current_user)
            
            db.session.add(mouvement)
            
            # Mise à jour de la date de mise à jour
            produit.date_mise_a_jour = datetime.now(timezone.utc)
            produit.modifie_par = current_user.id
            
            # Log audit entry
            log_stock_entry(
                produit_id=produit.id,
                quantity=quantite,
                actor_id=current_user.id,
                supplier=form.fournisseur.data if hasattr(form, 'fournisseur') and form.fournisseur.data else None,
                invoice_num=form.num_facture.data if hasattr(form, 'num_facture') and form.num_facture.data else None
            )
            
            db.session.commit()
            
            flash('Entrée en stock enregistrée avec succès!', 'success')
            # Redirect to zone view for magasiniers, global view for others
            if current_user.role == 'magasinier':
                return redirect(url_for('stock.liste_produits_zone'))
            else:
                return redirect(url_for('stock.liste_produits'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de l\'enregistrement de l\'entrée en stock : {str(e)}', 'danger')
            current_app.logger.error(f'Erreur entrée stock: {str(e)}')
    
    # Pré-remplir le formulaire avec le prix d'achat actuel si disponible
    if produit.prix_achat:
        form.prix_unitaire.data = float(produit.prix_achat)
    
    # Remplir la liste déroulante des emplacements
    from models import EmplacementStock
    form.emplacement_id.choices = [(e.id, e.designation) for e in EmplacementStock.query.filter_by(actif=True).order_by('designation').all()]
    
    return render_template('entree_stock.html', 
                         produit=produit,
                         form=form,
                         title=f'Entrée en stock - {produit.nom}')

@stock_bp.route('/produit/sortie/<int:produit_id>', methods=['GET', 'POST'])
@login_required
@require_stock_permission('can_dispatch_stock')
def sortie_stock(produit_id):
    """
    Gère les sorties de stock pour un produit
    Autorisé: chef_pur, gestionnaire_stock, magasinier, admin
    """
    from models import EmplacementStock  # Import ici pour éviter les imports circulaires
    
    produit = db.session.get(Produit, produit_id)
    if not produit:
        abort(404)
    form = SortieStockForm()
    
    # Remplir les choix d'emplacement avant la validation
    # Filter by zone for magasiniers
    if current_user.role == 'magasinier':
        emplacements = EmplacementStock.query.filter_by(
            zone_id=current_user.zone_id,
            actif=True
        ).order_by('designation').all()
    else:
        emplacements = EmplacementStock.query.filter_by(actif=True).order_by('designation').all()
    
    if not emplacements:
        # Créer des emplacements par défaut si aucun n'existe
        emplacements = [
            EmplacementStock(designation='Entrepôt Principal', code='ENTREPOT', actif=True),
            EmplacementStock(designation='Magasin', code='MAGASIN', actif=True),
            EmplacementStock(designation='Atelier', code='ATELIER', actif=True)
        ]
        db.session.bulk_save_objects(emplacements)
        db.session.commit()
    
    form.emplacement_id.choices = [(e.id, e.designation) for e in emplacements]
    
    if form.validate_on_submit():
        # Zone-based access control for magasinier
        if current_user.role.lower() == 'magasinier':
            from zone_rbac import validate_emplacement_zone
            validate_emplacement_zone(form.emplacement_id.data)
        
        quantite = form.quantite.data
        prix_vente = form.prix_vente.data
        motif = form.motif.data
        commentaire = form.commentaire.data
        
        try:
            # 🔴 PRODUCTION CRITICAL: Validate stock negative prevention
            # Calculate available stock for this product (entree - sortie)
            stock_disponible = db.session.query(
                func.coalesce(
                    func.sum(
                        case(
                            (MouvementStock.type_mouvement == 'entree', MouvementStock.quantite),
                            (MouvementStock.type_mouvement == 'sortie', -MouvementStock.quantite),
                            else_=0
                        )
                    ), 
                    0
                )
            ).filter(MouvementStock.produit_id == produit_id).scalar()
            
            # ✅ BLOCKER CHECK: Prevent negative stock creation
            if quantite <= 0:
                flash('❌ ERREUR: Quantité invalide. Doit être > 0', 'danger')
                return render_template('sortie_stock.html', produit=produit, form=form, 
                                     title=f'Sortie de stock - {produit.nom}')
            
            # ✅ BLOCKER CHECK: Prevent stock from going negative
            if quantite > stock_disponible:
                flash(f'❌ ERREUR STOCK: Insufficient stock. Available: {stock_disponible} {produit.unite_mesure}. Requested: {quantite}', 'danger')
                # Log this attempted violation for audit
                current_app.logger.warning(
                    f'SECURITY: User {current_user.id} attempted to create sortie exceeding available stock '
                    f'(produit_id={produit_id}, available={stock_disponible}, requested={quantite})'
                )
                return render_template('sortie_stock.html', produit=produit, form=form, 
                                     title=f'Sortie de stock - {produit.nom}')
            else:
                # Mise à jour du prix de vente si fourni et différent du prix actuel
                if prix_vente is not None and prix_vente > 0 and prix_vente != produit.prix_vente:
                    produit.prix_vente = prix_vente
                
                # 🔴 PRODUCTION CRITICAL: Enforce workflow on sortie
                # Construire le commentaire avec le motif
                commentaire_complet = f"[{motif.upper()}]"
                if commentaire:
                    commentaire_complet += f" - {commentaire}"
                
                mouvement = MouvementStock(
                    produit_id=produit.id,
                    type_mouvement='sortie',
                    quantite=quantite,
                    prix_unitaire=prix_vente if prix_vente else produit.prix_vente,
                    utilisateur_id=current_user.id,
                    emplacement_id=form.emplacement_id.data,
                    commentaire=commentaire_complet,
                    date_mouvement=datetime.now(timezone.utc),
                    applique_au_stock=False  # ← CRITICAL: Never auto-apply
                )
                
                # ✅ Enforce workflow state initialization
                mouvement = validate_and_initialize_mouvement_workflow(mouvement, current_user)
                
                db.session.add(mouvement)
                
                # Mise à jour de la date de mise à jour du produit
                produit.date_mise_a_jour = datetime.now(timezone.utc)
                if hasattr(produit, 'modifie_par'):
                    produit.modifie_par = current_user.id
                
                # Log audit removal
                log_stock_removal(
                    produit_id=produit.id,
                    quantity=quantite,
                    actor_id=current_user.id,
                    reason=commentaire_complet
                )
                
                db.session.commit()
                
                flash(f'✅ Sortie créée - En attente approbation manager', 'warning')
                # Redirect to zone view for magasiniers, global view for others
                if current_user.role == 'magasinier':
                    return redirect(url_for('stock.liste_produits_zone'))
                else:
                    return redirect(url_for('stock.liste_produits'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de l\'enregistrement de la sortie de stock : {str(e)}', 'danger')
            current_app.logger.error(f'Erreur sortie stock: {str(e)}')
    
    # Pré-remplir le formulaire avec le prix de vente actuel si disponible
    if produit.prix_vente:
        form.prix_vente.data = float(produit.prix_vente)
    
    # Remplir la liste déroulante des emplacements
    from models import EmplacementStock
    form.emplacement_id.choices = [(e.id, e.designation) for e in EmplacementStock.query.filter_by(actif=True).order_by('designation').all()]
    
    return render_template('sortie_stock.html', 
                         produit=produit,
                         form=form,
                         title=f'Sortie de stock - {produit.nom}')


@stock_bp.route('/produit/ajuster/<int:produit_id>', methods=['POST'])
@login_required
def ajuster_stock(produit_id):
    """
    Gère l'ajustement manuel du stock pour un produit (inventaire ponctuel)
    """
    from flask import jsonify
    from datetime import datetime
    
    produit = db.session.get(Produit, produit_id)
    if not produit:
        abort(404)
    data = request.get_json()
    
    if not data or 'stock_reel' not in data or 'motif' not in data:
        return jsonify({'success': False, 'message': 'Données manquantes'}), 400
    
    try:
        stock_reel = float(data['stock_reel'])
        motif = data['motif']
        emplacement_id = data.get('emplacement_id')
        
        # JOUR 3: Vérifier zone autorisée pour magasinier
        if current_user.role in ['magasinier', 'chef_zone']:
            if emplacement_id:
                emplacement = db.session.get(EmplacementStock, emplacement_id)
                if not emplacement or emplacement.zone_id != current_user.zone_id:
                    return jsonify({'error': 'Permission refusée: emplacement d\'une autre zone'}), 403
            else:
                # Utiliser l'emplacement par défaut de la zone
                emplacement_id = db.session.query(EmplacementStock.id).filter_by(
                    zone_id=current_user.zone_id
                ).first()
                if not emplacement_id:
                    return jsonify({'error': 'Aucun emplacement disponible dans votre zone'}), 400
                emplacement_id = emplacement_id[0]
        
        # Calculer la différence entre le stock réel et le stock calculé
        stock_calcule = produit.quantite
        difference = stock_reel - stock_calcule
        
        # Si pas de différence, enregistrer un mouvement d'inventaire avec ecart 0
        if abs(difference) < 1e-9:
            mouvement = MouvementStock(
                produit_id=produit.id,
                type_mouvement='inventaire',
                quantite=0,
                quantite_reelle=stock_reel,
                ecart=0,
                utilisateur_id=current_user.id,
                commentaire=f"Inventaire - {motif} (Aucun écart)",
                date_mouvement=datetime.now(timezone.utc),
                emplacement_id=emplacement_id
            )
            db.session.add(mouvement)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Inventaire enregistré (aucun écart)', 'nouvelle_quantite': stock_reel})
        
        # Déterminer le type de mouvement pour appliquer la différence
        if difference > 0:
            mouvement_type = 'entree'
            quantite_mouvement = float(difference)
        else:
            mouvement_type = 'sortie'
            quantite_mouvement = float(abs(difference))
        
        # Créer le mouvement d'inventaire (enregistré comme entrée/sortie pour affecter le stock)
        mouvement = MouvementStock(
            produit_id=produit.id,
            type_mouvement=mouvement_type,
            quantite=quantite_mouvement,
            quantite_reelle=stock_reel,
            ecart=difference,
            utilisateur_id=current_user.id,
            commentaire=f"Inventaire - {motif} (écart: {difference})",
            date_mouvement=datetime.now(timezone.utc),
            emplacement_id=emplacement_id
        )

        db.session.add(mouvement)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Stock ajusté avec succès',
            'nouvelle_quantite': stock_reel,
            'difference': difference
        })
        
    except ValueError:
        return jsonify({'success': False, 'message': 'Valeur de stock invalide'}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erreur ajustement stock: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# EXPORT ENDPOINTS
# ============================================================

@stock_bp.route('/api/export/mouvements', methods=['GET'])
@login_required
def api_export_mouvements():
    """
    Export stock movements as CSV or PDF
    
    ✅ PHASE 3 TÂCHE 3.2 : Filtrage Zone appliqué (CRITIQUE)
    Zone filtering:
    - magasinier: Exporte SEULEMENT mouvements de sa zone
    - chef_zone: Exporte SEULEMENT mouvements de sa zone  
    - chef_pur, admin: Exporte TOUS les mouvements
    
    Query Parameters:
    - format: 'csv' or 'pdf' (default: csv)
    - date_debut: YYYY-MM-DD
    - date_fin: YYYY-MM-DD
    - type_mouvement: entree, sortie, adjustment
    - produit_id: Filter by product
    """
    try:
        # Get query parameters
        export_format = request.args.get('format', 'csv').lower()
        date_debut = request.args.get('date_debut')
        date_fin = request.args.get('date_fin')
        type_mouvement = request.args.get('type_mouvement')
        produit_id = request.args.get('produit_id', type=int)
        
        # Validate format
        if export_format not in ['csv', 'pdf']:
            return jsonify({'error': 'Invalid format. Use csv or pdf'}), 400
        
        # Build base query
        query = MouvementStock.query
        
        # ✅ NOUVEAU: Filtrer par zone pour magasinier/chef_zone
        from middleware import apply_zone_filter
        from models import EmplacementStock
        
        # Joindre avec EmplacementStock pour accéder à la zone
        if current_user.role in ['magasinier', 'chef_zone']:
            query = query.join(
                EmplacementStock,
                MouvementStock.emplacement_id == EmplacementStock.id
            ).filter(EmplacementStock.zone_id == current_user.zone_id)
            current_app.logger.info(
                f"✅ Export mouvements filtré par zone_id={current_user.zone_id} "
                f"pour {current_user.role} {current_user.id}"
            )
        
        # Apply type filter
        if type_mouvement:
            query = query.filter(MouvementStock.type_mouvement == type_mouvement)
        
        # Apply product filter
        if produit_id:
            query = query.filter(MouvementStock.produit_id == produit_id)
        
        mouvements = query.order_by(MouvementStock.date_mouvement.desc()).all()
        
        # Apply date filters
        if date_debut or date_fin:
            mouvements = apply_date_filter(
                mouvements,
                'date_mouvement',
                date_debut,
                date_fin
            )
        
        # Log export
        current_app.logger.info(
            f"Export mouvements: {len(mouvements)} records, "
            f"user={current_user.id}, format={export_format}, "
            f"role={current_user.role}"
        )
        
        # Prepare data for export
        export_data = []
        for m in mouvements:
            utilisateur = db.session.get(User, m.utilisateur_id)
            
            export_data.append({
                'ID': m.id,
                'Date': format_datetime(m.date_mouvement),
                'Produit': m.produit.designation if m.produit else '-',
                'Catégorie': m.produit.categorie.nom if m.produit and m.produit.categorie else '-',
                'Type': m.type_mouvement.upper(),
                'Quantité': str(m.quantite),
                'Prix Unitaire': f"{m.prix_unitaire:,.2f}" if m.prix_unitaire else '-',
                'Total': f"{(m.quantite * m.prix_unitaire):,.2f}" if m.prix_unitaire else '-',
                'Utilisateur': f"{utilisateur.nom} {utilisateur.prenom}" if utilisateur else '-',
                'Commentaire': m.commentaire or '-'
            })
        
        # Generate CSV or PDF
        if export_format == 'csv':
            headers = [
                'ID', 'Date', 'Produit', 'Catégorie', 'Type', 'Quantité',
                'Prix Unitaire', 'Total', 'Utilisateur', 'Commentaire'
            ]
            csv_data, filename = generate_csv(export_data, headers)
            
            return send_file(
                BytesIO(csv_data),
                mimetype='text/csv',
                as_attachment=True,
                download_name=filename
            )
        
        else:  # PDF format
            from reportlab.lib.units import inch
            
            # Create PDF report
            report = PDFReport(
                'RAPPORT DE MOUVEMENTS DE STOCK',
                filename=f"mouvements_stock_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                landscape_mode=True
            )
            
            # Add title and metadata
            report.add_title('RAPPORT DE MOUVEMENTS DE STOCK')
            
            metadata = {
                'Date de rapport': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'Total mouvements': str(len(export_data))
            }
            if date_debut or date_fin:
                date_range = f"{date_debut or '...'} à {date_fin or '...'}"
                metadata['Période'] = date_range
            if type_mouvement:
                metadata['Type'] = type_mouvement.upper()
            if produit_id:
                produit = db.session.get(Produit, produit_id)
                if produit:
                    metadata['Produit'] = produit.designation
            
            report.add_metadata(metadata)
            
            # Add summary statistics
            report.add_heading('Résumé Statistiques')
            entrees = sum(1 for d in export_data if d['Type'] == 'ENTREE')
            sorties = sum(1 for d in export_data if d['Type'] == 'SORTIE')
            
            total_entrees = sum(float(d['Total'].replace(',', '').split()[0]) for d in export_data if d['Type'] == 'ENTREE' and d['Total'] != '-') if export_data else 0
            total_sorties = sum(float(d['Total'].replace(',', '').split()[0]) for d in export_data if d['Type'] == 'SORTIE' and d['Total'] != '-') if export_data else 0
            
            stats_text = f"<b>Total Mouvements:</b> {len(export_data)} | <b>Entrées:</b> {entrees} | <b>Sorties:</b> {sorties} | <b>Montant Entrées:</b> {total_entrees:,.2f} DZD | <b>Montant Sorties:</b> {total_sorties:,.2f} DZD"
            report.add_paragraph(stats_text, 'SmallText')
            report.add_spacer(0.1)
            
            # Add table
            if export_data:
                table_data = []
                for d in export_data:
                    table_data.append([
                        str(d['ID']),
                        d['Date'][:10],
                        d['Produit'][:20],
                        d['Type'],
                        d['Quantité'],
                        d['Prix Unitaire'],
                        d['Total'],
                        d['Utilisateur'][:20]
                    ])
                
                report.add_table(
                    table_data,
                    headers=['ID', 'Date', 'Produit', 'Type', 'Qty', 'Prix Unit.', 'Total', 'Utilisateur'],
                    col_widths=[0.5*inch, 0.9*inch, 1.2*inch, 0.7*inch, 0.6*inch, 0.9*inch, 1*inch, 1.2*inch]
                )
            else:
                report.add_paragraph("Aucune donnée à afficher.", 'Normal')
            
            # Build PDF and return
            pdf_bytes = report.build()
            
            return send_file(
                BytesIO(pdf_bytes),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=report.filename
            )
    
    except Exception as e:
        current_app.logger.error(f"Error exporting stock movements: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# PAGE D'APPROBATION DES MOUVEMENTS
# ============================================================================

@stock_bp.route('/approver-mouvements')
@login_required
@require_stock_role('chef_pur', 'gestionnaire_stock', 'admin')
def page_approver_mouvements():
    """
    Page HTML pour approuver/rejeter les mouvements en attente
    Accessible uniquement aux managers/admin
    """
    return render_template('approver_mouvements.html', title='Approbation des Mouvements')


@stock_bp.route('/inventaire', methods=['GET', 'POST'])
@login_required
@require_stock_permission('can_receive_stock')
def inventaire_physique():
    """
    Page HTML pour gérer l'inventaire physique
    - Upload fichier Excel/CSV
    - Scanner code-barres
    - Comparer vs stock système
    """
    return render_template('inventaire.html', title='Inventaire Physique')


@stock_bp.route('/api/inventaire/compare', methods=['POST'])
@login_required
@require_stock_permission('can_receive_stock')
def api_compare_inventaire():
    """
    Compare l'inventaire physique avec le stock système
    
    Endpoint: POST /gestion-stock/api/inventaire/compare
    
    Payload:
        {
            "articles": {
                "REF-001": {"nom": "Routeur", "quantite_physique": 10},
                "REF-002": {"nom": "Switch", "quantite_physique": 5},
                ...
            }
        }
    
    Réponse:
        {
            "comparaison": [
                {
                    "reference": "REF-001",
                    "nom": "Routeur",
                    "quantite_bd": 10,
                    "quantite_physique": 10,
                    "ecart": 0,
                    "statut": "✅"
                },
                ...
            ],
            "resume": {
                "total_articles": 2,
                "articles_corrects": 1,
                "articles_differents": 1,
                "ecart_total": 3
            }
        }
    """
    try:
        data = request.get_json() or {}
        articles_physiques = data.get('articles', {})
        
        if not articles_physiques:
            return jsonify({'error': 'Aucun article à comparer'}), 400
        
        comparaison = []
        stats = {
            'total_articles': len(articles_physiques),
            'articles_corrects': 0,
            'articles_differents': 0,
            'ecart_total': 0,
            'montant_ecart': 0
        }
        
        # Comparer chaque article
        for ref, info_physique in articles_physiques.items():
            # Chercher le produit par référence
            produit = Produit.query.filter_by(reference=ref).first()
            
            if not produit:
                # Produit non trouvé
                comparaison.append({
                    'reference': ref,
                    'nom': info_physique.get('nom', 'Produit inconnu'),
                    'quantite_bd': 0,
                    'quantite_physique': info_physique.get('quantite_physique', 0),
                    'ecart': info_physique.get('quantite_physique', 0),
                    'statut': '❌',  # DANGER: Produit inexistant en BD
                    'type': 'produit_inexistant'
                })
                stats['articles_differents'] += 1
                ecart = info_physique.get('quantite_physique', 0)
                stats['ecart_total'] += abs(ecart)
                continue
            
            # Récupérer la quantité en stock
            quantite_bd = produit.quantite
            quantite_physique = info_physique.get('quantite_physique', 0)
            ecart = quantite_physique - quantite_bd
            
            # Déterminer le statut
            if ecart == 0:
                statut = '✅'
                stats['articles_corrects'] += 1
            elif abs(ecart) <= 2:  # Tolérance 2 units
                statut = '⚠️'
                stats['articles_differents'] += 1
            else:
                statut = '❌'
                stats['articles_differents'] += 1
            
            stats['ecart_total'] += abs(ecart)
            
            montant_ecart = (abs(ecart) * produit.prix_achat) if produit.prix_achat else 0
            stats['montant_ecart'] += montant_ecart
            
            comparaison.append({
                'reference': ref,
                'nom': produit.nom,
                'quantite_bd': int(quantite_bd),
                'quantite_physique': int(quantite_physique),
                'ecart': int(ecart),
                'statut': statut,
                'prix_unitaire': float(produit.prix_achat or 0),
                'montant_ecart': montant_ecart,
                'produit_id': produit.id
            })
        
        # Ordonner par écart décroissant
        comparaison.sort(key=lambda x: abs(x['ecart']), reverse=True)
        
        current_app.logger.info(
            f"Inventaire comparé par {current_user.username}: "
            f"{len(comparaison)} articles, {stats['articles_differents']} différences"
        )
        
        return jsonify({
            'comparaison': comparaison,
            'resume': stats
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la comparaison d'inventaire: {str(e)}")
        return jsonify({'error': f'Erreur: {str(e)}'}), 500

# ============================================================================
# WORKFLOW VALIDATION ENDPOINTS
# ============================================================================

@stock_bp.route('/api/mouvements/approuver/<int:mouvement_id>', methods=['POST'])
@login_required
@require_stock_role('chef_pur', 'gestionnaire_stock')
def approuver_mouvement(mouvement_id):
    """
    Approuve un mouvement de stock et le rend prêt pour exécution
    
    Endpoint: POST /gestion-stock/api/mouvements/approuver/123
    Payload:
        {
            "motif_approbation": "Approuvé après vérification" (optionnel)
        }
    
    Réponse:
        {
            "success": true,
            "message": "Mouvement approuvé avec succès",
            "mouvement": {...}
        }
    """
    from workflow_stock import WorkflowState
    from rbac_stock import filter_mouvements_by_zone
    
    try:
        mouvement = db.session.get(MouvementStock, mouvement_id)
        if not mouvement:
            return jsonify({'error': 'Mouvement non trouvé'}), 404
        
        # JOUR 3: Vérifier zone autorisée pour magasinier
        if current_user.role.lower() == 'magasinier':
            # Magasinier ne peut approuver que mouvements de sa zone
            if not mouvement.emplacement_id:
                return jsonify({'error': 'Mouvement sans emplacement: impossible à approuver'}), 400
            
            emplacement = db.session.get(EmplacementStock, mouvement.emplacement_id)
            if not emplacement or emplacement.zone_id != current_user.zone_id:
                return jsonify({'error': 'Permission refusée: mouvement d\'une autre zone'}), 403
        
        # Vérifier que l'utilisateur a les droits d'approbation
        if mouvement.type_mouvement == 'entree' and not has_stock_permission(current_user, 'can_receive_stock'):
            return jsonify({'error': 'Permission refusée pour approuver une entrée'}), 403
        
        if mouvement.type_mouvement == 'sortie' and not has_stock_permission(current_user, 'can_dispatch_stock'):
            return jsonify({'error': 'Permission refusée pour approuver une sortie'}), 403
        
        if mouvement.type_mouvement == 'ajustement' and not has_stock_permission(current_user, 'can_adjust_stock'):
            return jsonify({'error': 'Permission refusée pour approuver un ajustement'}), 403
        
        # Vérifier l'état actuel
        current_state = mouvement.workflow_state
        if current_state not in ['EN_ATTENTE', 'EN_ATTENTE_DOCS']:
            return jsonify({'error': f'Mouvement en état {current_state}, impossible à approuver'}), 400
        
        # Mettre à jour le mouvement
        mouvement.workflow_state = WorkflowState.APPROUVE.value
        mouvement.date_approbation = datetime.utcnow()
        mouvement.approuve_par_id = current_user.id
        
        # Log de l'approbation
        current_app.logger.info(
            f"Mouvement {mouvement_id} approuvé par {current_user.username} "
            f"({mouvement.type_mouvement} - {mouvement.produit_relation.nom} x{mouvement.quantite})"
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Mouvement approuvé avec succès',
            'mouvement_id': mouvement.id,
            'workflow_state': mouvement.workflow_state,
            'approuve_par': current_user.username,
            'date_approbation': mouvement.date_approbation.isoformat() if mouvement.date_approbation else None
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur lors de l'approbation du mouvement: {str(e)}")
        return jsonify({'error': f'Erreur: {str(e)}'}), 500


@stock_bp.route('/api/mouvements/rejeter/<int:mouvement_id>', methods=['POST'])
@login_required
@require_stock_role('chef_pur', 'gestionnaire_stock')
def rejeter_mouvement(mouvement_id):
    """
    Rejette un mouvement de stock (pas d'application au stock)
    
    Endpoint: POST /gestion-stock/api/mouvements/rejeter/123
    Payload:
        {
            "motif_rejet": "Stock inexistant" (obligatoire)
        }
    
    Réponse:
        {
            "success": true,
            "message": "Mouvement rejeté",
            "mouvement": {...}
        }
    """
    from workflow_stock import WorkflowState
    
    try:
        data = request.get_json()
        motif_rejet = data.get('motif_rejet', '').strip()
        
        if not motif_rejet:
            return jsonify({'error': 'Motif du rejet obligatoire'}), 400
        
        mouvement = db.session.get(MouvementStock, mouvement_id)
        if not mouvement:
            return jsonify({'error': 'Mouvement non trouvé'}), 404
        
        # Zone-based access control for magasinier
        if current_user.role.lower() == 'magasinier':
            if not mouvement.emplacement_id:
                return jsonify({'error': 'Mouvement sans emplacement: impossible à rejeter'}), 400
            emplacement = db.session.get(EmplacementStock, mouvement.emplacement_id)
            if not emplacement or emplacement.zone_id != current_user.zone_id:
                return jsonify({'error': 'Permission refusée: mouvement d\'une autre zone'}), 403
        
        # Vérifier l'état actuel
        current_state = mouvement.workflow_state
        if current_state not in ['EN_ATTENTE', 'EN_ATTENTE_DOCS', 'APPROUVE']:
            return jsonify({'error': f'Mouvement en état {current_state}, impossible à rejeter'}), 400
        
        # Mettre à jour le mouvement
        mouvement.workflow_state = WorkflowState.REJETE.value
        mouvement.motif_rejet = motif_rejet
        mouvement.approuve_par_id = current_user.id
        
        # Log du rejet
        current_app.logger.info(
            f"Mouvement {mouvement_id} rejeté par {current_user.username}: {motif_rejet}"
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Mouvement rejeté',
            'mouvement_id': mouvement.id,
            'workflow_state': mouvement.workflow_state,
            'motif_rejet': motif_rejet
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur lors du rejet du mouvement: {str(e)}")
        return jsonify({'error': f'Erreur: {str(e)}'}), 500


@stock_bp.route('/api/mouvements/appliquer-stock/<int:mouvement_id>', methods=['POST'])
@login_required
@require_stock_role('chef_pur', 'admin')
def appliquer_stock_mouvement(mouvement_id):
    """
    Applique un mouvement APPROUVÉ au stock
    
    ⚠️ CRITIQUE: Ne peut être appelé que si workflow_state = 'APPROUVE'
    
    Endpoint: POST /gestion-stock/api/mouvements/appliquer-stock/123
    
    Réponse:
        {
            "success": true,
            "message": "Stock appliqué avec succès",
            "mouvement": {...}
        }
    """
    from workflow_stock import WorkflowState
    
    try:
        mouvement = db.session.get(MouvementStock, mouvement_id)
        if not mouvement:
            return jsonify({'error': 'Mouvement non trouvé'}), 404
        
        # JOUR 3: Vérifier zone autorisée pour magasinier
        if current_user.role.lower() == 'magasinier':
            if not mouvement.emplacement_id:
                return jsonify({'error': 'Mouvement sans emplacement: impossible à appliquer'}), 400
            
            emplacement = db.session.get(EmplacementStock, mouvement.emplacement_id)
            if not emplacement or emplacement.zone_id != current_user.zone_id:
                return jsonify({'error': 'Permission refusée: mouvement d\'une autre zone'}), 403
        
        # ⚠️ SÉCURITÉ CRITIQUE: Vérifier que le mouvement est APPROUVÉ
        if mouvement.workflow_state != WorkflowState.APPROUVE.value:
            return jsonify({
                'error': f'Mouvement doit être approuvé. État actuel: {mouvement.workflow_state}',
                'workflow_state': mouvement.workflow_state
            }), 400
        
        # Vérifier que le stock n'a pas déjà été appliqué
        if mouvement.applique_au_stock:
            return jsonify({'error': 'Le stock a déjà été appliqué pour ce mouvement'}), 400
        
        # Vérifier la disponibilité pour les sorties
        if mouvement.type_mouvement == 'sortie':
            stock_disponible = db.session.query(
                func.coalesce(
                    func.sum(
                        case(
                            (MouvementStock.type_mouvement.in_(['entree', 'inventaire', 'retour']), 
                             MouvementStock.quantite),
                            (MouvementStock.type_mouvement.in_(['sortie', 'ajustement']), 
                             -MouvementStock.quantite),
                            else_=0
                        )
                    ), 
                    0
                )
            ).filter(
                MouvementStock.produit_id == mouvement.produit_id,
                MouvementStock.applique_au_stock == True
            ).scalar()
            
            if mouvement.quantite > stock_disponible:
                return jsonify({
                    'error': f'Stock insuffisant. Disponible: {stock_disponible}, Demandé: {mouvement.quantite}',
                    'stock_disponible': stock_disponible,
                    'quantite_demandee': mouvement.quantite
                }), 400
        
        # Appliquer le stock
        mouvement.applique_au_stock = True
        mouvement.workflow_state = WorkflowState.EXECUTE.value
        mouvement.date_execution = datetime.utcnow()
        
        # Log de l'application
        current_app.logger.info(
            f"Stock appliqué pour mouvement {mouvement_id}: "
            f"{mouvement.type_mouvement} {mouvement.produit_relation.nom} x{mouvement.quantite} "
            f"par {current_user.username}"
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Stock appliqué avec succès',
            'mouvement_id': mouvement.id,
            'workflow_state': mouvement.workflow_state,
            'applique_au_stock': mouvement.applique_au_stock,
            'date_execution': mouvement.date_execution.isoformat() if mouvement.date_execution else None
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur lors de l'application du stock: {str(e)}")
        return jsonify({'error': f'Erreur: {str(e)}'}), 500


@stock_bp.route('/api/mouvements/en-attente', methods=['GET'])
@login_required
def lister_mouvements_en_attente():
    """
    Liste tous les mouvements en attente d'approbation
    
    Endpoint: GET /gestion-stock/api/mouvements/en-attente
    
    Query params:
        - type: 'entree', 'sortie', 'ajustement', etc. (optionnel)
        - limit: 50 (optionnel)
    
    Réponse:
        {
            "mouvements": [
                {
                    "id": 123,
                    "type_mouvement": "entree",
                    "produit": "Routeur TP-Link",
                    "quantite": 50,
                    "workflow_state": "EN_ATTENTE",
                    "date_mouvement": "2026-01-26T10:30:00",
                    "cree_par": "john.doe",
                    "montant": 2500.00
                },
                ...
            ],
            "total": 3,
            "stats": {
                "entree": 1,
                "sortie": 2,
                "en_attente": 3,
                "montant_total": 5500.00
            }
        }
    """
    from workflow_stock import WorkflowState
    from rbac_stock import filter_mouvements_by_zone
    
    try:
        # Récupérer les paramètres de filtre
        type_filtre = request.args.get('type', '').strip()
        limit = int(request.args.get('limit', 50))
        
        # Query de base: mouvements non approuvés
        query = MouvementStock.query.filter(
            MouvementStock.workflow_state.in_([
                WorkflowState.EN_ATTENTE.value,
                WorkflowState.EN_ATTENTE_DOCS.value
            ]),
            MouvementStock.applique_au_stock == False
        )
        
        # JOUR 3: Filtrer par zone de l'utilisateur
        query = filter_mouvements_by_zone(query, current_user)
        
        # Filtrer par type si spécifié
        if type_filtre and type_filtre in ['entree', 'sortie', 'ajustement', 'inventaire', 'retour']:
            query = query.filter_by(type_mouvement=type_filtre)
        
        # Ordonner par date (plus récents d'abord)
        mouvements = query.order_by(desc(MouvementStock.date_mouvement)).limit(limit).all()
        
        # Construire la réponse
        mouvements_data = []
        stats = {'entree': 0, 'sortie': 0, 'ajustement': 0, 'inventaire': 0, 'retour': 0, 
                 'en_attente': len(mouvements), 'montant_total': 0}
        
        for m in mouvements:
            stats[m.type_mouvement] += 1
            montant = (m.quantite * m.prix_unitaire) if m.prix_unitaire else 0
            stats['montant_total'] += montant
            
            mouvements_data.append({
                'id': m.id,
                'type_mouvement': m.type_mouvement,
                'produit': m.produit_relation.nom,
                'quantite': m.quantite,
                'prix_unitaire': m.prix_unitaire,
                'montant': montant,
                'workflow_state': m.workflow_state,
                'date_mouvement': m.date_mouvement.isoformat(),
                'cree_par': m.utilisateur.username,
                'reference': m.reference,
                'commentaire': m.commentaire
            })
        
        return jsonify({
            'mouvements': mouvements_data,
            'total': len(mouvements),
            'stats': stats
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des mouvements: {str(e)}")
        return jsonify({'error': f'Erreur: {str(e)}'}), 500


@stock_bp.route('/api/mouvements/entrees-mois')
@login_required
def api_entrees_mois():
    """
    API pour récupérer les entrées du mois courant
    """
    try:
        from datetime import datetime, date
        
        # Récupérer le mois courant
        today = date.today()
        debut_mois = date(today.year, today.month, 1)
        
        # Déterminer le dernier jour du mois
        if today.month == 12:
            fin_mois = date(today.year + 1, 1, 1)
        else:
            fin_mois = date(today.year, today.month + 1, 1)
        
        # Query les mouvements d'entrée du mois courant
        query = db.select(MouvementStock).filter(
            MouvementStock.type_mouvement == 'entree',
            MouvementStock.date_mouvement >= datetime.combine(debut_mois, datetime.min.time()),
            MouvementStock.date_mouvement < datetime.combine(fin_mois, datetime.min.time())
        )
        
        # JOUR 3: Filtrer par zone pour magasinier/chef_zone
        if current_user.role in ['magasinier', 'chef_zone']:
            query = query.join(
                EmplacementStock,
                MouvementStock.emplacement_id == EmplacementStock.id
            ).filter(
                EmplacementStock.zone_id == current_user.zone_id
            )
        
        entrees = db.session.execute(
            query.order_by(MouvementStock.date_mouvement.desc())
        ).scalars().all()
        
        entrees_data = []
        for e in entrees:
            entrees_data.append({
                'id': e.id,
                'date': e.date_mouvement.strftime('%Y-%m-%d'),
                'date_mouvement': e.date_mouvement.strftime('%Y-%m-%d %H:%M'),
                'nom_produit': e.produit_relation.nom if e.produit_relation else 'N/A',
                'reference_produit': e.produit_relation.reference if e.produit_relation else 'N/A',
                'quantite': float(e.quantite) if e.quantite is not None else 0,
                'prix_unitaire': float(e.prix_unitaire) if e.prix_unitaire is not None else 0,
                'fournisseur': e.fournisseur.raison_sociale if e.fournisseur else 'N/A',
                'utilisateur': e.utilisateur.username if e.utilisateur else 'N/A',
                'reference': e.reference,
                'commentaire': e.commentaire
            })
        
        return jsonify({
            'success': True,
            'data': entrees_data,
            'total': len(entrees_data)
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des entrées du mois: {str(e)}")
        return jsonify({'error': f'Erreur: {str(e)}'}), 500


@stock_bp.route('/api/mouvements/sorties-mois')
@login_required
def api_sorties_mois():
    """
    API pour récupérer les sorties du mois courant
    """
    try:
        from datetime import datetime, date
        
        # Récupérer le mois courant
        today = date.today()
        debut_mois = date(today.year, today.month, 1)
        
        # Déterminer le dernier jour du mois
        if today.month == 12:
            fin_mois = date(today.year + 1, 1, 1)
        else:
            fin_mois = date(today.year, today.month + 1, 1)
        
        # Query les mouvements de sortie du mois courant
        query = db.select(MouvementStock).filter(
            MouvementStock.type_mouvement == 'sortie',
            MouvementStock.date_mouvement >= datetime.combine(debut_mois, datetime.min.time()),
            MouvementStock.date_mouvement < datetime.combine(fin_mois, datetime.min.time())
        )
        
        # JOUR 3: Filtrer par zone pour magasinier/chef_zone
        if current_user.role in ['magasinier', 'chef_zone']:
            query = query.join(
                EmplacementStock,
                MouvementStock.emplacement_id == EmplacementStock.id
            ).filter(
                EmplacementStock.zone_id == current_user.zone_id
            )
        
        sorties = db.session.execute(
            query.order_by(MouvementStock.date_mouvement.desc())
        ).scalars().all()
        
        sorties_data = []
        for s in sorties:
            sorties_data.append({
                'id': s.id,
                'date': s.date_mouvement.strftime('%Y-%m-%d'),
                'date_mouvement': s.date_mouvement.strftime('%Y-%m-%d %H:%M'),
                'nom_produit': s.produit_relation.nom if s.produit_relation else 'N/A',
                'reference_produit': s.produit_relation.reference if s.produit_relation else 'N/A',
                'quantite': float(s.quantite) if s.quantite is not None else 0,
                'prix_unitaire': float(s.prix_unitaire) if s.prix_unitaire is not None else 0,
                'motif': s.commentaire if s.commentaire else 'N/A',
                'utilisateur': s.utilisateur.username if s.utilisateur else 'N/A',
                'reference': s.reference,
                'commentaire': s.commentaire
            })
        
        return jsonify({
            'success': True,
            'data': sorties_data,
            'total': len(sorties_data)
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des sorties du mois: {str(e)}")
        return jsonify({'error': f'Erreur: {str(e)}'}), 500


# ============================================================================
# 📦 SUPPLIER BULK IMPORT ENDPOINTS
# ============================================================================

@stock_bp.route('/import-supplier', methods=['POST'])
@login_required
@require_stock_permission('can_dispatch_stock')
def api_import_supplier():
    """
    Bulk import stock from external suppliers via CSV
    
    Supports:
    - Generic CSV format (supplier-agnostic)
    - 5000+ rows efficiently
    - Partial success handling
    - Audit logging on all imports
    - Workflow enforcement (imports require approval)
    
    CSV Format:
    - product_reference: Product reference (required, must exist)
    - quantity: Number of units (required, > 0)
    - serial_number: Serial or batch number (optional)
    - emplacement_code: Storage location (optional, default=ENTREPOT)
    - unit_price: Unit cost (optional)
    - note: Import comment (optional)
    
    Request:
    - POST with multipart/form-data
    - Field 'file': CSV file upload
    
    Response:
    {
        'success': bool,
        'phase': 'parsing|validation|import|complete|unexpected_error',
        'summary': {
            'total_requested': int,
            'successfully_inserted': int,
            'failed_rows': int,
            'total_quantity_imported': int
        },
        'validation': {
            'total_rows': int,
            'valid_rows': int,
            'error_rows': int,
            'warning_rows': int,
            'errors_by_type': {error_type: count}
        },
        'errors': [error_messages],
        'processing_time_seconds': float
    }
    """
    try:
        # Validate request
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided',
                'phase': 'validation'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Empty filename',
                'phase': 'validation'
            }), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({
                'success': False,
                'error': 'File must be CSV format (.csv)',
                'phase': 'validation'
            }), 400
        
        # Read file content
        try:
            file_content = file.read()
            if isinstance(file_content, bytes):
                file_content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            return jsonify({
                'success': False,
                'error': 'CSV file must be UTF-8 encoded',
                'phase': 'parsing'
            }), 400
        
        current_app.logger.info(
            f'📦 Starting supplier import: user={current_user.id}, '
            f'file={file.filename}, size={len(file_content)} bytes'
        )
        
        # Process import
        result = process_supplier_import(file_content, current_user)
        
        # Determine HTTP status
        status_code = 200 if result['success'] else 400 if result['phase'] in ['parsing', 'validation'] else 500
        
        # Log result
        if result['success']:
            current_app.logger.info(
                f'✅ Import successful: {result["summary"]["successfully_inserted"]} '
                f'rows inserted, {result["summary"]["total_quantity_imported"]} units, '
                f'{result["processing_time_seconds"]:.2f}s'
            )
        else:
            current_app.logger.warning(
                f'⚠️ Import failed at phase "{result["phase"]}: {result["errors"]}'
            )
        
        return jsonify(result), status_code
    
    except Exception as e:
        error_msg = f'Unexpected error in import endpoint: {str(e)}'
        current_app.logger.error(error_msg)
        return jsonify({
            'success': False,
            'error': error_msg,
            'phase': 'unexpected_error'
        }), 500


@stock_bp.route('/import-sonatel', methods=['POST'])
@login_required
@require_stock_permission('can_dispatch_stock')
def api_import_sonatel():
    """
    Import stock from Sonatel Excel via Excel parsing logic.
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Aucun fichier fourni'}), 400
        
        file = request.files['file']
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'success': False, 'error': 'Format invalide (Excel attendu)'}), 400
            
        file_content = file.read()
        result = process_sonatel_import(file_content, current_user)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error in Sonatel import: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@stock_bp.route('/stock/transfert/initier', methods=['POST'])
@login_required
@require_stock_permission('can_dispatch_stock')
def initier_transfert():
    """
    Initiate a transfer from Dakar to another zone.
    """
    try:
        data = request.get_json()
        produit_id = data.get('produit_id')
        quantite = float(data.get('quantite', 0))
        target_zone_id = data.get('target_zone_id')
        
        if quantite <= 0:
            return jsonify({'success': False, 'error': 'Quantité invalide'}), 400
            
        # 1. Source: Dakar Central
        source_warehouse = db.session.query(EmplacementStock).filter_by(code='ENTREPOT').first()
        if not source_warehouse:
            return jsonify({'success': False, 'error': 'Entrepôt central non trouvé'}), 500
            
        # 2. Check stock in Dakar
        valid, current_stock, msg = prevent_negative_stock_on_creation(produit_id, quantite)
        if not valid:
            return jsonify({'success': False, 'error': msg}), 400
            
        # 3. Create Sortie from Dakar (EN_TRANSIT)
        mouvement_sortie = MouvementStock(
            type_mouvement='sortie',
            reference=f'TRANS-{datetime.now().strftime("%y%m%d%H%M")}',
            produit_id=produit_id,
            quantite=quantite,
            utilisateur_id=current_user.id,
            emplacement_id=source_warehouse.id,
            commentaire=f"Transfert vers zone ID {target_zone_id}",
            workflow_state='APPROUVE', # GS can approve their own transfers if they have roles
            applique_au_stock=True # Deduct immediately from Dakar
        )
        db.session.add(mouvement_sortie)
        db.session.flush()
        
        # 4. Find target warehouse for the zone
        # a. Try by direct zone_id link
        target_warehouse = db.session.query(EmplacementStock).filter_by(zone_id=target_zone_id, actif=True).first()
        
        if not target_warehouse:
            # Get zone name for fallback lookup
            target_zone = db.session.query(Zone).get(target_zone_id)
            if target_zone:
                # b. Try by designation matching zone name (e.g. "Zone 2 - Mbour" contains "Mbour")
                target_warehouse = db.session.query(EmplacementStock).filter(
                    EmplacementStock.designation.ilike(f"%{target_zone.nom}%"),
                    EmplacementStock.actif == True
                ).first()
                
                if not target_warehouse:
                    # c. Last resort: Try by code (ZONE1, ZONE2...)
                    zone_code = f"ZONE{target_zone_id}"
                    target_warehouse = db.session.query(EmplacementStock).filter_by(code=zone_code, actif=True).first()
            
            # AUTO-LINK: Si on trouve l'emplacement par nom/code mais qu'il n'est pas lié à la zone, on le lie
            if target_warehouse and target_warehouse.zone_id is None:
                current_app.logger.info(f"🔗 Auto-linking warehouse {target_warehouse.code} to zone ID {target_zone_id}")
                target_warehouse.zone_id = target_zone_id
                db.session.flush()
            
        # 5. Create Pending Entree for Target
        mouvement_entree = MouvementStock(
            type_mouvement='entree',
            reference=mouvement_sortie.reference,
            produit_id=produit_id,
            quantite=quantite,
            utilisateur_id=current_user.id,
            emplacement_id=target_warehouse.id if target_warehouse else None,
            commentaire=f"Réception transfert de Dakar (Ref: {mouvement_sortie.reference})",
            workflow_state='EN_ATTENTE', # Requires magasinier action
            applique_au_stock=False
        )
        db.session.add(mouvement_entree)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Transfert initié'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error initiating transfer: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@stock_bp.route('/stock/transfert/recevoir/<int:mouvement_id>', methods=['POST'])
@login_required
@require_stock_permission('can_receive_stock')
def recevoir_transfert(mouvement_id):
    """
    Magasinier confirms reception of a transfer.
    """
    from workflow_stock import WorkflowState
    try:
        mouvement = db.session.get(MouvementStock, mouvement_id)
        if not mouvement or mouvement.type_mouvement != 'entree':
            return jsonify({'success': False, 'error': 'Mouvement introuvable'}), 404
            
        # Security: must be in same zone
        emplacement = db.session.get(EmplacementStock, mouvement.emplacement_id)
        if current_user.role == 'magasinier' and (not emplacement or emplacement.zone_id != current_user.zone_id):
            return jsonify({'success': False, 'error': 'Accès refusé: zone incorrecte'}), 403
            
        if mouvement.workflow_state != 'EN_ATTENTE':
            return jsonify({'success': False, 'error': 'Déjà traité'}), 400
            
        # Confirm reception
        mouvement.workflow_state = WorkflowState.EXECUTE.value # or VALIDE
        mouvement.applique_au_stock = True
        mouvement.date_execution = datetime.now(timezone.utc)
        mouvement.approuve_par_id = current_user.id
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Réception confirmée'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error receiving transfer: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@stock_bp.route('/import-template', methods=['GET'])
@login_required
def get_import_template():
    """
    Download supplier import CSV template
    
    Returns CSV file with example headers and sample data
    """
    try:
        template_content = """product_reference,quantity,serial_number,emplacement_code,unit_price,note
ONT-GPON-V5,10,SN-2024-001-010,ENTREPOT,45000,Initial stock
OLT-FIBER-X2,5,,MAGASIN,250000,
SPLITTER-1X8,20,BATCH-2024-001,ENTREPOT,5000,Batch import
MODEM-DOCSIS,100,,ENTREPOT,35000,Bulk order
"""
        
        csv_bytes = template_content.encode('utf-8-sig')
        filename = f'supplier_import_template_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return send_file(
            BytesIO(csv_bytes),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        current_app.logger.error(f'Error generating template: {str(e)}')
        return jsonify({'error': str(e)}), 500


@stock_bp.route('/import/doc', methods=['GET'])
@login_required
def get_import_documentation():
    """
    Get supplier import documentation
    
    Returns HTML documentation with format details and examples
    """
    try:
        documentation = """
        <div class="card">
            <div class="card-header bg-primary text-white">
                <h5>📦 Supplier Bulk Import Documentation</h5>
            </div>
            <div class="card-body">
                <h6>CSV Format</h6>
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Column</th>
                            <th>Required</th>
                            <th>Type</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><code>product_reference</code></td>
                            <td>✓ Yes</td>
                            <td>String</td>
                            <td>Product reference code (must exist in system)</td>
                        </tr>
                        <tr>
                            <td><code>quantity</code></td>
                            <td>✓ Yes</td>
                            <td>Integer</td>
                            <td>Number of units to import (must be > 0)</td>
                        </tr>
                        <tr>
                            <td><code>serial_number</code></td>
                            <td>Optional</td>
                            <td>String</td>
                            <td>Serial or batch identifier (unique or base for range)</td>
                        </tr>
                        <tr>
                            <td><code>emplacement_code</code></td>
                            <td>Optional</td>
                            <td>String</td>
                            <td>Storage location code (default: ENTREPOT)</td>
                        </tr>
                        <tr>
                            <td><code>unit_price</code></td>
                            <td>Optional</td>
                            <td>Decimal</td>
                            <td>Unit cost for inventory tracking</td>
                        </tr>
                        <tr>
                            <td><code>note</code></td>
                            <td>Optional</td>
                            <td>String</td>
                            <td>Import comment or note</td>
                        </tr>
                    </tbody>
                </table>
                
                <h6 class="mt-3">Features</h6>
                <ul>
                    <li>✅ Generic CSV format (supplier-agnostic)</li>
                    <li>✅ Supports 5000+ rows efficiently</li>
                    <li>✅ Row-level validation with detailed error reporting</li>
                    <li>✅ Partial success handling (failed rows don't block valid rows)</li>
                    <li>✅ Duplicate serial number prevention</li>
                    <li>✅ Automatic serial number generation (if pattern provided)</li>
                    <li>✅ Transaction-safe bulk insert</li>
                    <li>✅ Complete audit logging</li>
                    <li>✅ Workflow enforcement (all imports require manager approval)</li>
                </ul>
                
                <h6 class="mt-3">Processing Flow</h6>
                <ol>
                    <li><strong>Parsing:</strong> CSV format validation</li>
                    <li><strong>Validation:</strong> Row-level data validation (product exists, serials unique, etc.)</li>
                    <li><strong>Import:</strong> Batch insert with transaction safety</li>
                    <li><strong>Workflow:</strong> Imports automatically enter EN_ATTENTE state (require approval)</li>
                </ol>
                
                <h6 class="mt-3">Example</h6>
                <pre>product_reference,quantity,serial_number,emplacement_code,unit_price,note
ONT-GPON-V5,10,SN-2024-001-010,ENTREPOT,45000,Initial stock
OLT-FIBER-X2,5,,MAGASIN,250000,
SPLITTER-1X8,20,BATCH-2024-001,ENTREPOT,5000,Batch import</pre>
            </div>
        </div>
        """
        
        return jsonify({
            'success': True,
            'documentation': documentation
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# 🔴 PHASE 2 FIX: Stock Movement Approval Routes for Magasinier
# ============================================================================

@stock_bp.route('/approve-movement/<int:mouvement_id>', methods=['GET', 'POST'])
@login_required
@require_stock_permission('can_approve_stock_movement')
def approve_stock_movement(mouvement_id):
    """
    Approve a stock movement (for chief_pur or magasinier of same zone).
    
    Magasinier can only approve their own movements (EN_ATTENTE -> APPROUVE).
    Chief_pur can approve any movement.
    
    Transition workflow: EN_ATTENTE -> APPROUVE -> EXECUTE -> VALIDE
    """
    try:
        mouvement = MouvementStock.query.get_or_404(mouvement_id)
        
        # RBAC: Magasinier can only approve own zone movements
        if current_user.role == 'magasinier':
            # Verify magasinier zone matches movement zone
            if not mouvement.emplacement or mouvement.emplacement.zone_id != current_user.zone_id:
                flash('❌ Vous ne pouvez approuver que les mouvements de votre zone.', 'danger')
                return redirect(url_for('stock.liste_mouvements'))
        
        if request.method == 'POST':
            # Transition EN_ATTENTE -> APPROUVE
            if mouvement.workflow_state != 'EN_ATTENTE':
                flash(f'⚠️ Ce mouvement ne peut pas être approuvé (état: {mouvement.workflow_state})', 'warning')
            else:
                mouvement.workflow_state = 'APPROUVE'
                mouvement.approuve_par_id = current_user.id
                mouvement.date_approbation = datetime.now(timezone.utc)
                
                db.session.commit()
                
                log_activity(
                    user_id=current_user.id,
                    action='approve_stock_movement',
                    module='stock',
                    entity_name=f"Mouvement #{mouvement.id}",
                    details={
                        'mouvement_id': mouvement.id,
                        'mouvement_type': mouvement.type_mouvement,
                        'produit': mouvement.produit.designation if mouvement.produit else 'Unknown',
                        'quantite': mouvement.quantite,
                        'emplacement_zone': mouvement.emplacement.zone.nom if mouvement.emplacement and mouvement.emplacement.zone else 'Unknown'
                    }
                )
                
                flash(f'✅ Mouvement #{mouvement.id} approuvé avec succès!', 'success')
                return redirect(url_for('stock.liste_mouvements'))
        
        return render_template(
            'approve_movement.html',
            mouvement=mouvement,
            zone_name=mouvement.emplacement.zone.nom if mouvement.emplacement and mouvement.emplacement.zone else 'Unknown'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error approving movement: {e}")
        flash(f'❌ Erreur lors de l\'approbation: {str(e)}', 'danger')
        return redirect(url_for('stock.liste_mouvements'))


@stock_bp.route('/list-pending-approvals')
@login_required
@require_stock_permission('can_approve_stock_movement')
def liste_approbations_en_attente():
    """
    List pending stock movement approvals.
    
    Magasinier sees: Pending movements in their zone
    Chief_pur sees: All pending movements
    """
    try:
        # Filter by workflow state EN_ATTENTE
        query = MouvementStock.query.filter_by(workflow_state='EN_ATTENTE')
        
        # Magasinier: only their zone
        if current_user.role == 'magasinier':
            from models import EmplacementStock
            zone_emplacements = db.session.query(EmplacementStock.id).filter_by(
                zone_id=current_user.zone_id
            ).subquery()
            query = query.filter(MouvementStock.emplacement_id.in_(
                db.session.query(EmplacementStock.id).filter_by(zone_id=current_user.zone_id)
            ))
        
        mouvements = query.order_by(MouvementStock.date_creation.desc()).all()
        
        return render_template(
            'list_pending_approvals.html',
            mouvements=mouvements,
            user_role=current_user.role
        )
        
    except Exception as e:
        current_app.logger.error(f"Error listing approvals: {e}")
        flash(f'❌ Erreur: {str(e)}', 'danger')
        return redirect(url_for('stock.dashboard'))

# ============================================================================
# 🔴 MAGASINIER: Gestion des Réservations Techniciens
# ============================================================================

@stock_bp.route('/reservations/attente')
@login_required
def liste_reservations_attente():
    """
    Affiche la liste des réservations en attente pour la zone du magasinier
    """
    if current_user.role.lower() != 'magasinier':
        flash('Accès réservé aux magasiniers.', 'error')
        return redirect(url_for('dashboard'))
    
    if not current_user.zone_id:
        flash('Vous n\'êtes pas assigné à une zone.', 'error')
        return redirect(url_for('dashboard'))

    # Récupérer les réservations en attente dont le technicien est dans la même zone
    reservations = db.session.query(ReservationPiece).join(
        Intervention, ReservationPiece.intervention_id == Intervention.id
    ).join(
        User, Intervention.technicien_id == User.id
    ).filter(
        User.zone_id == current_user.zone_id,
        ReservationPiece.statut == ReservationPiece.STATUT_EN_ATTENTE
    ).all()
    
    return render_template('reservations_zone_magasinier.html', reservations=reservations)

@stock_bp.route('/reservation/valider/<int:reservation_id>', methods=['POST'])
@login_required
def valider_reservation(reservation_id):
    """
    Valide une réservation de pièce par un magasinier
    """
    if current_user.role.lower() != 'magasinier':
        return jsonify({'success': False, 'message': 'Accès non autorisé'}), 403
    
    reservation = db.session.get(ReservationPiece, reservation_id)
    if not reservation:
        return jsonify({'success': False, 'message': 'Réservation introuvable'}), 404
    
    # Vérifier que le technicien est dans la zone du magasinier
    if reservation.intervention.technicien.zone_id != current_user.zone_id:
        return jsonify({'success': False, 'message': 'Cette réservation ne concerne pas votre zone'}), 403
    
    success, message = reservation.valider(current_user.id)
    
    if success:
        # Automatiquement marquer comme utilisée pour sortir du stock ? 
        # Ou attendre que le tech vienne chercher ? 
        # Dans le workflow Sonatel, le magasinier valide la SORTIE.
        # Donc on marque comme utilisée immédiatement pour décrémenter le stock.
        success_use, message_use = reservation.marquer_comme_utilisee()
        if not success_use:
            # Si on ne peut pas marquer comme utilisé (stock insuffisant au moment T), on rollback la validation
            reservation.statut = ReservationPiece.STATUT_EN_ATTENTE
            db.session.commit()
            return jsonify({'success': False, 'message': f"Validation impossible: {message_use}"})
            
        return jsonify({'success': True, 'message': 'Réservation validée et stock mis à jour'})
    else:
        return jsonify({'success': False, 'message': message})

@stock_bp.route('/reservation/rejeter/<int:reservation_id>', methods=['POST'])
@login_required
def rejeter_reservation(reservation_id):
    """
    Rejette une réservation de pièce par un magasinier
    """
    if current_user.role.lower() != 'magasinier':
        return jsonify({'success': False, 'message': 'Accès non autorisé'}), 403
    
    reservation = db.session.get(ReservationPiece, reservation_id)
    if not reservation:
        return jsonify({'success': False, 'message': 'Réservation introuvable'}), 404
    
    # Vérifier que le technicien est dans la zone du magasinier
    if reservation.intervention.technicien.zone_id != current_user.zone_id:
        return jsonify({'success': False, 'message': 'Cette réservation ne concerne pas votre zone'}), 403
    
    data = request.get_json()
    motif = data.get('motif', 'Rejeté par le magasinier')
    
    success, message = reservation.annuler(motif=motif, rejeter=True)
    
    if success:
        return jsonify({'success': True, 'message': 'Réservation rejetée'})
    else:
        return jsonify({'success': False, 'message': message})
