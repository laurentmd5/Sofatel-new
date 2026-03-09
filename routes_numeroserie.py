"""
routes_numeroserie.py - Routes pour gestion NumeroSerie

Endpoints pour:
- Import Sonatel
- Affectation zone/technicien
- Installation client
- Suivi et traçabilité
- Rapports
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timezone
from models import (
    NumeroSerie, NumeroSerieStatut, MouvementNumeroSerie, NumeroSerieTypeTransition,
    HistoriqueEtatNumeroSerie, Produit, User, Zone, EmplacementStock, Client, db
)
from rbac_stock import require_stock_permission
from numeroserie_import import importer_numeros_sonatel
import json

numeroserie_bp = Blueprint('numeroserie', __name__, url_prefix='/api/numero-serie')


def utcnow():
    """Return timezone-aware UTC datetime"""
    return datetime.now(timezone.utc)


# ============================================================================
# IMPORT SONATEL
# ============================================================================

@numeroserie_bp.route('/import', methods=['POST'])
@login_required
@require_stock_permission('importer_articles')
def import_sonatel():
    """
    POST /api/numero-serie/import
    
    Upload fichier Sonatel et validation dry-run
    
    Payload:
        - file: fichier CSV/Excel
        - produit_id: ID produit
        - bon_livraison_ref: Référence bon Sonatel
        - dry_run: true/false (defaut: true)
    
    Returns:
        {
            'succes': bool,
            'mode': 'dry_run' ou 'commit',
            'nb_lignes': int,
            'nb_importe': int,
            'nb_erreurs': int,
            'erreurs': [...],
            'message': str
        }
    """
    try:
        # Récupérer fichier
        if 'file' not in request.files:
            return jsonify({'erreur': 'Fichier manquant'}), 400
        
        fichier = request.files['file']
        if not fichier or fichier.filename == '':
            return jsonify({'erreur': 'Fichier invalide'}), 400
        
        # Récupérer paramètres
        produit_id = request.form.get('produit_id', type=int)
        bon_livraison_ref = request.form.get('bon_livraison_ref')
        dry_run = request.form.get('dry_run', 'true').lower() == 'true'
        
        if not produit_id or not bon_livraison_ref:
            return jsonify({'erreur': 'Paramètres manquants'}), 400
        
        # Valider produit
        produit = Produit.query.get(produit_id)
        if not produit:
            return jsonify({'erreur': 'Produit non trouvé'}), 404
        
        # Détecter format
        if fichier.filename.endswith('.csv'):
            format_type = 'csv'
        elif fichier.filename.endswith(('.xlsx', '.xls')):
            format_type = 'excel'
        else:
            return jsonify({'erreur': 'Format fichier non supporté (CSV ou Excel attendu)'}), 400
        
        # Lire contenu
        contenu = fichier.read()
        
        # Importer
        resultat = importer_numeros_sonatel(
            contenu=contenu,
            nom_fichier=fichier.filename,
            format_type=format_type,
            produit_id=produit_id,
            bon_livraison_ref=bon_livraison_ref,
            utilisateur_id=current_user.id,
            dry_run=dry_run
        )
        
        if resultat['succes']:
            return jsonify(resultat), 200 if dry_run else 201
        else:
            return jsonify(resultat), 400
    
    except Exception as e:
        return jsonify({'erreur': str(e)}), 500


@numeroserie_bp.route('/import/history', methods=['GET'])
@login_required
@require_stock_permission('lire_articles')
def import_history():
    """
    GET /api/numero-serie/import/history
    
    Récupère historique des imports
    
    Query params:
        - page: numéro page (defaut: 1)
        - per_page: articles par page (defaut: 20)
    
    Returns:
        {
            'total': int,
            'page': int,
            'imports': [
                {
                    'id': int,
                    'bon_livraison_ref': str,
                    'nb_importe': int,
                    'nb_erreurs': int,
                    'date_import': datetime,
                    'utilisateur': str,
                    'statut': str
                }
            ]
        }
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    from models import ImportHistoriqueNumeroSerie
    
    query = ImportHistoriqueNumeroSerie.query.order_by(
        ImportHistoriqueNumeroSerie.date_import.desc()
    )
    
    pagination = query.paginate(page=page, per_page=per_page)
    
    imports = []
    for import_hist in pagination.items:
        imports.append({
            'id': import_hist.id,
            'bon_livraison_ref': import_hist.bon_livraison_ref,
            'nom_fichier': import_hist.nom_fichier,
            'produit': import_hist.produit.nom if import_hist.produit else 'N/A',
            'nb_lignes': import_hist.nb_lignes_fichier,
            'nb_importe': import_hist.nb_importe,
            'nb_erreurs': import_hist.nb_erreurs,
            'nb_doublons': import_hist.nb_doublons,
            'date_import': import_hist.date_import.isoformat(),
            'utilisateur': import_hist.utilisateur.nom if import_hist.utilisateur else 'N/A',
            'statut': import_hist.statut
        })
    
    return jsonify({
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages,
        'imports': imports
    }), 200


# ============================================================================
# AFFECTATION ZONE/TECHNICIEN
# ============================================================================

@numeroserie_bp.route('/<numero>/affecter-zone/<int:zone_id>', methods=['POST'])
@login_required
@require_stock_permission('affecter_materiel')
def affecter_zone(numero, zone_id):
    """
    POST /api/numero-serie/SN-2024-0001234/affecter-zone/1
    
    Affecte NumeroSerie à une zone
    Transition: EN_MAGASIN → ALLOUE_ZONE
    
    Permissions: Chef PUR, Gestionnaire stock
    
    Returns:
        {
            'succes': bool,
            'numero': str,
            'ancien_statut': str,
            'nouveau_statut': str,
            'zone': str,
            'message': str
        }
    """
    try:
        # Récupérer NumeroSerie
        ns = NumeroSerie.query.filter_by(numero=numero).first()
        if not ns:
            return jsonify({'erreur': f'NumeroSerie {numero} non trouvé'}), 404
        
        # Vérifier statut actuel
        if ns.statut != NumeroSerieStatut.EN_MAGASIN:
            return jsonify({
                'erreur': f'NumeroSerie doit être EN_MAGASIN pour affectation zone (actuellement: {ns.get_statut_display()})'
            }), 409
        
        # Récupérer zone
        zone = Zone.query.get(zone_id)
        if not zone:
            return jsonify({'erreur': f'Zone {zone_id} non trouvée'}), 404
        
        # Transition
        ancien_statut = ns.statut
        ns.transition_vers(
            NumeroSerieStatut.ALLOUE_ZONE,
            current_user.id,
            raison=f'Affectation zone {zone.nom}'
        )
        ns.zone_id = zone_id
        
        # Emplacement zone
        emplacement_zone = EmplacementStock.query.filter_by(
            type_emplacement='zone',
            zone_id=zone_id
        ).first()
        if emplacement_zone:
            ns.emplacement_id = emplacement_zone.id
        
        db.session.commit()
        
        return jsonify({
            'succes': True,
            'numero': ns.numero,
            'ancien_statut': ancien_statut.value,
            'nouveau_statut': ns.statut.value,
            'zone': zone.nom,
            'message': f'NumeroSerie {numero} affecté zone {zone.nom}'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erreur': str(e)}), 500


@numeroserie_bp.route('/<numero>/affecter-tech/<int:tech_id>', methods=['POST'])
@login_required
@require_stock_permission('affecter_materiel')
def affecter_technicien(numero, tech_id):
    """
    POST /api/numero-serie/SN-2024-0001234/affecter-tech/5
    
    Affecte NumeroSerie à technicien
    Transition: ALLOUE_ZONE → ALLOUE_TECHNICIEN
    
    Permissions: Chef zone, Magasinier zone
    
    Returns:
        {
            'succes': bool,
            'numero': str,
            'technicien': str,
            'zone': str,
            'message': str
        }
    """
    try:
        # Récupérer NumeroSerie
        ns = NumeroSerie.query.filter_by(numero=numero).first()
        if not ns:
            return jsonify({'erreur': f'NumeroSerie {numero} non trouvé'}), 404
        
        # Vérifier statut
        if ns.statut != NumeroSerieStatut.ALLOUE_ZONE:
            return jsonify({
                'erreur': f'NumeroSerie doit être ALLOUE_ZONE (actuellement: {ns.get_statut_display()})'
            }), 409
        
        # Récupérer technicien
        tech = User.query.get(tech_id)
        if not tech or tech.role != 'technicien':
            return jsonify({'erreur': f'Technicien {tech_id} non trouvé'}), 404
        
        # Vérifier zone
        if tech.zone_id and ns.zone_id != tech.zone_id:
            return jsonify({
                'erreur': f'Technicien affecté zone {tech.zone.nom}, NumeroSerie affecté zone {ns.zone.nom}'
            }), 409
        
        # Transition
        ancien_statut = ns.statut
        ns.transition_vers(
            NumeroSerieStatut.ALLOUE_TECHNICIEN,
            current_user.id,
            raison=f'Affectation technicien {tech.nom}'
        )
        ns.technicien_id = tech_id
        ns.date_affectation_tech = utcnow()
        
        db.session.commit()
        
        return jsonify({
            'succes': True,
            'numero': ns.numero,
            'technicien': f'{tech.prenom} {tech.nom}',
            'zone': ns.zone.nom if ns.zone else 'N/A',
            'message': f'NumeroSerie affecté technicien {tech.prenom} {tech.nom}'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erreur': str(e)}), 500


# ============================================================================
# INSTALLATION CLIENT
# ============================================================================

@numeroserie_bp.route('/<numero>/installer', methods=['POST'])
@login_required
@require_stock_permission('installer_materiel')
def installer(numero):
    """
    POST /api/numero-serie/SN-2024-0001234/installer
    
    Marque NumeroSerie comme installé chez client
    Transition: ALLOUE_TECHNICIEN → INSTALLEE
    
    Payload:
        {
            'adresse_client': str (required),
            'numero_ligne_sonatel': str (required),
            'client_id': int (optional)
        }
    
    Permissions: Technicien affecté
    """
    try:
        # Récupérer NumeroSerie
        ns = NumeroSerie.query.filter_by(numero=numero).first()
        if not ns:
            return jsonify({'erreur': f'NumeroSerie {numero} non trouvé'}), 404
        
        # Vérifier technicien
        if ns.technicien_id != current_user.id:
            return jsonify({
                'erreur': f'Vous n\'êtes pas technicien affecté pour ce NumeroSerie'
            }), 403
        
        # Vérifier statut
        if ns.statut != NumeroSerieStatut.ALLOUE_TECHNICIEN:
            return jsonify({
                'erreur': f'NumeroSerie doit être ALLOUE_TECHNICIEN (actuellement: {ns.get_statut_display()})'
            }), 409
        
        # Récupérer données
        data = request.get_json()
        adresse_client = data.get('adresse_client', '').strip()
        numero_ligne_sonatel = data.get('numero_ligne_sonatel', '').strip()
        client_id = data.get('client_id')
        
        if not adresse_client or not numero_ligne_sonatel:
            return jsonify({
                'erreur': 'adresse_client et numero_ligne_sonatel requis'
            }), 400
        
        # Transition
        ns.transition_vers(
            NumeroSerieStatut.INSTALLEE,
            current_user.id,
            raison='Installation client'
        )
        ns.date_installation = utcnow()
        ns.adresse_client = adresse_client
        ns.numero_ligne_sonatel = numero_ligne_sonatel
        if client_id:
            ns.client_id = client_id
        
        db.session.commit()
        
        return jsonify({
            'succes': True,
            'numero': ns.numero,
            'statut': ns.get_statut_display(),
            'adresse': adresse_client,
            'date_installation': ns.date_installation.isoformat(),
            'message': f'NumeroSerie installé chez client: {adresse_client}'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erreur': str(e)}), 500


@numeroserie_bp.route('/<numero>/retourner', methods=['POST'])
@login_required
@require_stock_permission('gerer_retours')
def retourner(numero):
    """
    POST /api/numero-serie/SN-2024-0001234/retourner
    
    Enregistre retour NumeroSerie du client
    Transition: INSTALLEE → RETOURNEE
    
    Payload:
        {
            'motif_retour': str (required) - défectueux|fin_contrat|changement|autre,
            'description_probleme': str (optional)
        }
    
    Permissions: Tech support, Chef PUR
    """
    try:
        # Récupérer NumeroSerie
        ns = NumeroSerie.query.filter_by(numero=numero).first()
        if not ns:
            return jsonify({'erreur': f'NumeroSerie {numero} non trouvé'}), 404
        
        # Vérifier statut
        if ns.statut != NumeroSerieStatut.INSTALLEE:
            return jsonify({
                'erreur': f'NumeroSerie doit être INSTALLEE (actuellement: {ns.get_statut_display()})'
            }), 409
        
        # Récupérer données
        data = request.get_json()
        motif_retour = data.get('motif_retour', '').strip()
        description_probleme = data.get('description_probleme', '').strip()
        
        if not motif_retour:
            return jsonify({'erreur': 'motif_retour requis'}), 400
        
        # Transition
        ns.transition_vers(
            NumeroSerieStatut.RETOURNEE,
            current_user.id,
            raison=motif_retour
        )
        ns.date_retour = utcnow()
        ns.motif_retour = motif_retour
        
        # Créer dossier SAV si défectueux
        if motif_retour.lower() == 'défectueux':
            from models import DossierSAV
            dossier = DossierSAV(
                numero_dossier=f'SAV-{utcnow().strftime("%Y%m%d%H%M%S")}-{numero.replace("-", "")}',
                numero_serie_id=ns.id,
                client_id=ns.client_id,
                motif_retour='défectueux',
                description_probleme=description_probleme,
                date_ouverture=utcnow(),
                statut='ouvert',
                cree_par_id=current_user.id
            )
            db.session.add(dossier)
            ns.dossier_sav_id = dossier.id
        
        db.session.commit()
        
        return jsonify({
            'succes': True,
            'numero': ns.numero,
            'statut': ns.get_statut_display(),
            'motif_retour': motif_retour,
            'date_retour': ns.date_retour.isoformat(),
            'message': f'NumeroSerie retourné: {motif_retour}'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erreur': str(e)}), 500


# ============================================================================
# SUIVI & TRAÇABILITÉ
# ============================================================================

@numeroserie_bp.route('/<numero>', methods=['GET'])
@login_required
@require_stock_permission('lire_articles')
def get_numero_serie(numero):
    """
    GET /api/numero-serie/SN-2024-0001234
    
    Récupère informations complètes NumeroSerie
    """
    try:
        ns = NumeroSerie.query.filter_by(numero=numero).first()
        if not ns:
            return jsonify({'erreur': f'NumeroSerie {numero} non trouvé'}), 404
        
        return jsonify({
            'id': ns.id,
            'numero': ns.numero,
            'produit': {
                'id': ns.produit.id,
                'reference': ns.produit.reference,
                'nom': ns.produit.nom
            } if ns.produit else None,
            'statut': ns.statut.value,
            'statut_display': ns.get_statut_display(),
            'statut_color': ns.get_statut_color(),
            'date_entree': ns.date_entree.isoformat() if ns.date_entree else None,
            'emplacement': ns.emplacement.nom if ns.emplacement else None,
            'zone': ns.zone.nom if ns.zone else None,
            'technicien': f'{ns.technicien.prenom} {ns.technicien.nom}' if ns.technicien else None,
            'date_affectation_tech': ns.date_affectation_tech.isoformat() if ns.date_affectation_tech else None,
            'date_installation': ns.date_installation.isoformat() if ns.date_installation else None,
            'adresse_client': ns.adresse_client,
            'numero_ligne_sonatel': ns.numero_ligne_sonatel,
            'date_retour': ns.date_retour.isoformat() if ns.date_retour else None,
            'motif_retour': ns.motif_retour,
            'cree_par': f'{ns.cree_par.prenom} {ns.cree_par.nom}' if ns.cree_par else None,
            'date_creation': ns.date_creation.isoformat() if ns.date_creation else None
        }), 200
    
    except Exception as e:
        return jsonify({'erreur': str(e)}), 500


@numeroserie_bp.route('/<numero>/timeline', methods=['GET'])
@login_required
@require_stock_permission('lire_articles')
def get_timeline(numero):
    """
    GET /api/numero-serie/SN-2024-0001234/timeline
    
    Récupère timeline complète (historique d'état)
    """
    try:
        ns = NumeroSerie.query.filter_by(numero=numero).first()
        if not ns:
            return jsonify({'erreur': f'NumeroSerie {numero} non trouvé'}), 404
        
        timeline = ns.get_historique_timeline()
        
        return jsonify({
            'numero': ns.numero,
            'timeline': timeline
        }), 200
    
    except Exception as e:
        return jsonify({'erreur': str(e)}), 500


@numeroserie_bp.route('/search', methods=['GET'])
@login_required
@require_stock_permission('lire_articles')
def search_numero():
    """
    GET /api/numero-serie/search?q=SN-2024&statut=INSTALLEE
    
    Recherche numéros de série
    
    Query params:
        - q: Query texte (numero)
        - statut: Filtrer par statut
        - page: numéro page
        - per_page: articles par page
    """
    q = request.args.get('q', '').strip()
    statut = request.args.get('statut')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = NumeroSerie.query
    
    if q:
        query = query.filter(NumeroSerie.numero.ilike(f'%{q}%'))
    
    if statut:
        try:
            statut_enum = NumeroSerieStatut[statut]
            query = query.filter_by(statut=statut_enum)
        except KeyError:
            pass
    
    pagination = query.paginate(page=page, per_page=per_page)
    
    numeros = []
    for ns in pagination.items:
        numeros.append({
            'numero': ns.numero,
            'produit': ns.produit.nom if ns.produit else 'N/A',
            'statut': ns.statut.value,
            'statut_display': ns.get_statut_display(),
            'zone': ns.zone.nom if ns.zone else 'N/A',
            'technicien': f'{ns.technicien.prenom} {ns.technicien.nom}' if ns.technicien else 'N/A',
            'adresse_client': ns.adresse_client or 'N/A'
        })
    
    return jsonify({
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages,
        'numeros': numeros
    }), 200


# ============================================================================
# RAPPORTS
# ============================================================================

@numeroserie_bp.route('/rapports/stocks', methods=['GET'])
@login_required
@require_stock_permission('generer_rapports')
def rapport_stocks():
    """
    GET /api/numero-serie/rapports/stocks
    
    Rapport stocks par état
    """
    try:
        rapport = {}
        
        for statut in NumeroSerieStatut:
            count = NumeroSerie.query.filter_by(statut=statut).count()
            rapport[statut.value] = {
                'count': count,
                'display': NumeroSerie(statut=statut).get_statut_display(),
                'color': NumeroSerie(statut=statut).get_statut_color()
            }
        
        return jsonify({
            'rapport': rapport,
            'total': NumeroSerie.query.count()
        }), 200
    
    except Exception as e:
        return jsonify({'erreur': str(e)}), 500
