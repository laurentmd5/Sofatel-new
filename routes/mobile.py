from flask import Blueprint, request, jsonify, current_app, g, url_for, abort, render_template
from models import db, User, Intervention, Produit, DemandeIntervention, ReservationPiece, TokenBlacklist
from werkzeug.security import check_password_hash
import jwt
from datetime import datetime, timedelta
import os
import uuid
import json
import base64
import time
import math
import logging
from functools import wraps

# ✅ NOUVEAU: Rate limiting pour les routes mobiles
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    limiter = Limiter(key_func=get_remote_address)
except ImportError:
    # Fallback si flask_limiter n'est pas installé
    limiter = None
    print("WARNING: flask_limiter not installed. Rate limiting disabled for mobile routes.")

mobile_bp = Blueprint('mobile', __name__)

# Token utilities
ACCESS_TOKEN_EXPIRES_MINUTES = 60
REFRESH_TOKEN_EXPIRES_DAYS = 7

# Simple in-memory TTL cache for light performance improvements (per-process)
# key -> (expires_at_ts, value)
_simple_cache = {}
DEFAULT_CACHE_TTL = int(os.environ.get('MOBILE_CACHE_TTL', 10))  # seconds


def _get_cached(key):
    now = int(time.time())
    entry = _simple_cache.get(key)
    if not entry:
        return None
    expires, value = entry
    if now >= expires:
        try:
            del _simple_cache[key]
        except KeyError:
            pass
        return None
    return value


def _set_cached(key, value, ttl=DEFAULT_CACHE_TTL):
    _simple_cache[key] = (int(time.time()) + int(ttl), value)


def _generate_tokens(user):
    secret = current_app.secret_key
    # ✅ NOUVEAU: Générer un JWT ID unique pour chaque token
    jti = str(uuid.uuid4())
    
    access_payload = {
        'user_id': user.id,
        'jti': jti,  # JWT ID pour revocation
        'exp': datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)
    }
    refresh_payload = {
        'user_id': user.id,
        'jti': jti,  # Même JTI pour lier access et refresh tokens
        'type': 'refresh',
        'exp': datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRES_DAYS)
    }
    access_token = jwt.encode(access_payload, secret, algorithm='HS256')
    refresh_token = jwt.encode(refresh_payload, secret, algorithm='HS256')
    return access_token, refresh_token


def jwt_required(f):
    """Decorator that accepts JWT tokens OR Flask-Login sessions.
    
    Tries JWT first (for native mobile clients), then falls back to session auth
    (for WebView clients using Flask-Login).
    
    ✅ NOUVEAU: Vérifie également que le token n'est pas blacklisté.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        from flask_login import current_user
        
        # Try JWT authentication first (for native mobile clients)
        auth = request.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            token = auth.split(' ', 1)[1]
            try:
                payload = jwt.decode(token, current_app.secret_key, algorithms=['HS256'])
                user = db.session.get(User, payload.get('user_id'))
                if not user:
                    return jsonify({'success': False, 'error': 'User not found'}), 401
                
                # ✅ NOUVEAU: Vérifier si le token est blacklisté
                jti = payload.get('jti')
                if jti and TokenBlacklist.query.filter_by(jti=jti).first():
                    return jsonify({'success': False, 'error': 'Token has been revoked'}), 401
                
                g.current_user = user
                return f(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                return jsonify({'success': False, 'error': 'Token expired'}), 401
            except Exception:
                return jsonify({'success': False, 'error': 'Invalid token'}), 401
        
        # Fall back to Flask-Login session auth (for WebView clients)
        if current_user.is_authenticated:
            g.current_user = current_user
            return f(*args, **kwargs)
        
        # No valid auth found
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    return wrapper


@mobile_bp.route('/api/mobile/login', methods=['POST'])
def mobile_login():
    # ✅ NOUVEAU: Rate limiting appliqué dynamiquement si disponible
    if limiter:
        # Limiter à 5 tentatives par minute par IP
        limiter.limit("5 per minute")(mobile_login)
    
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'success': False, 'error': 'Missing credentials'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.password_hash or not check_password_hash(user.password_hash, password):
        # ✅ NOUVEAU: Logger les tentatives échouées pour audit
        try:
            current_app.logger.warning(f"Failed login attempt for '{username}' from {request.remote_addr}")
        except:
            pass
        return jsonify({'success': False, 'error': 'Invalid username or password'}), 401

    access, refresh = _generate_tokens(user)
    return jsonify({
        'access_token': access,
        'refresh_token': refresh,
        'user': {
            'id': user.id,
            'username': user.username,
            'nom': user.nom,
            'prenom': user.prenom
            # ✅ SUPPRESSION : 'role' n'est plus inclus (risque sécurité)
        }
    })


@mobile_bp.route('/api/mobile/refresh', methods=['POST'])
def mobile_refresh():
    data = request.get_json() or {}
    refresh_token = data.get('refresh_token')
    if not refresh_token:
        return jsonify({'success': False, 'error': 'Missing refresh token'}), 400
    try:
        payload = jwt.decode(refresh_token, current_app.secret_key, algorithms=['HS256'])
        if payload.get('type') != 'refresh':
            return jsonify({'success': False, 'error': 'Invalid token type'}), 400
        user = db.session.get(User, payload.get('user_id'))
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 401
        access, refresh = _generate_tokens(user)
        return jsonify({'access_token': access, 'refresh_token': refresh})
    except jwt.ExpiredSignatureError:
        return jsonify({'success': False, 'error': 'Refresh token expired'}), 401
    except Exception:
        return jsonify({'success': False, 'error': 'Invalid token'}), 401


@mobile_bp.route('/api/mobile/logout', methods=['POST'])
@jwt_required
def mobile_logout():
    """Logout sécurisé : revoque le token JWT de l'utilisateur"""
    # ✅ NOUVEAU: Extraire le token et le blacklister
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        token = auth.split(' ', 1)[1]
        try:
            payload = jwt.decode(token, current_app.secret_key, algorithms=['HS256'])
            jti = payload.get('jti')
            
            # Ajouter le token à la blacklist
            if jti:
                blacklist_entry = TokenBlacklist(
                    jti=jti,
                    token_type='access',
                    user_id=g.current_user.id,
                    revoke_reason='User logged out'
                )
                db.session.add(blacklist_entry)
                db.session.commit()
        except Exception as e:
            current_app.logger.warning(f"Error blacklisting token on logout: {str(e)}")
    
    return jsonify({'success': True, 'message': 'Logged out successfully'})


@mobile_bp.route('/api/mobile/get-token', methods=['POST'])
def mobile_get_token():
    """
    Generate a JWT token for the currently authenticated WebView user (session-based).
    This endpoint allows WebView clients using Flask-Login to get a JWT token
    that can be passed to Flutter's native GeolocationService for authenticated tracking.
    
    Returns: {access_token, user_info}
    """
    from flask_login import current_user
    
    # Check if user is authenticated via session (WebView client)
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        # Generate JWT token for this user
        access_token, _ = _generate_tokens(current_user)
        
        return jsonify({
            'success': True,
            'access_token': access_token,
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'nom': current_user.nom,
                'prenom': current_user.prenom
                # ✅ SUPPRESSION : 'role' n'est plus inclus
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def _serialize_intervention(i: Intervention):
    return {
        'id': i.id,
        'demande_id': i.demande_id,
        'technicien_id': i.technicien_id,
        'statut': i.statut,
        'date_debut': i.date_debut.isoformat() if i.date_debut else None,
        'date_fin': i.date_fin.isoformat() if i.date_fin else None,
        'gps_lat': i.gps_lat,
        'gps_long': i.gps_long,
        'photos_list': json.loads(i.photos) if i.photos else []
    }


# Mobile GET endpoints for WebView Flutter (JWT protected)
@mobile_bp.route('/api/mobile/interventions', methods=['GET'])
@jwt_required
def api_mobile_interventions():
    """Return a JSON list of interventions. Supports optional query params: date_debut (YYYY-MM-DD), date_fin (YYYY-MM-DD), technicien_id, statut, page, per_page."""
    date_debut = request.args.get('date_debut')
    date_fin = request.args.get('date_fin')
    technicien_id = request.args.get('technicien_id', type=int)
    statut = request.args.get('statut')
    # Pagination
    page = max(1, request.args.get('page', 1, type=int))
    per_page = min(100, max(5, request.args.get('per_page', 20, type=int)))

    # Build cache key
    cache_key = f"interventions:{date_debut}:{date_fin}:{technicien_id}:{statut}:{page}:{per_page}:{g.current_user.id}"
    cached = _get_cached(cache_key)
    if cached:
        return jsonify(cached)

    query = Intervention.query

    if date_debut:
        try:
            date_deb = datetime.strptime(date_debut, '%Y-%m-%d')
            query = query.filter(Intervention.date_creation >= date_deb)
        except Exception:
            pass

    if date_fin:
        try:
            date_f = datetime.strptime(date_fin, '%Y-%m-%d')
            query = query.filter(Intervention.date_creation <= date_f)
        except Exception:
            pass

    if statut:
        query = query.filter(Intervention.statut == statut)

    # If the token belongs to a technician, only return their interventions
    if g.current_user.role == 'technicien':
        query = query.filter(Intervention.technicien_id == g.current_user.id)
    elif technicien_id:
        query = query.filter(Intervention.technicien_id == technicien_id)

    total = query.count()
    total_pages = math.ceil(total / per_page) if per_page else 1
    items = query.order_by(Intervention.date_creation.desc()).offset((page - 1) * per_page).limit(per_page).all()

    payload = {'success': True,
               'page': page,
               'per_page': per_page,
               'total': total,
               'total_pages': total_pages,
               'interventions': [_serialize_intervention(i) for i in items]}

    _set_cached(cache_key, payload, ttl=5)  # short cache for list
    return jsonify(payload)


@mobile_bp.route('/api/mobile/intervention/<int:intervention_id>', methods=['GET'])
@jwt_required
def api_mobile_get_intervention(intervention_id):
    intervention = db.session.get(Intervention, intervention_id)
    if not intervention:
        abort(404)
    if g.current_user.role == 'technicien' and intervention.technicien_id != g.current_user.id:
        return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403
    return jsonify({'success': True, 'intervention': _serialize_intervention(intervention)})


# ===== REMOVED =====
# Endpoint /api/intervention POST - SUPPRIMÉ
# Raison: Les techniciens ne créent pas d'interventions
# La création d'interventions est réservée aux administrateurs via l'interface web


@mobile_bp.route('/api/intervention/<int:intervention_id>/photos', methods=['POST'])
@jwt_required
def api_upload_intervention_photo(intervention_id):
    intervention = db.session.get(Intervention, intervention_id)
    if not intervention:
        abort(404)

    # Permission: technicien owner or manager roles
    if g.current_user.role == 'technicien' and intervention.technicien_id != g.current_user.id:
        return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403

    files = request.files.getlist('file') or []
    if not files:
        return jsonify({'success': False, 'error': 'No files uploaded'}), 400

    saved = []
    for f in files:
        ext = os.path.splitext(f.filename)[1] or '.jpg'
        filename = f"int_{intervention_id}_{uuid.uuid4().hex}{ext}"
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        f.save(save_path)
        saved.append(filename)

    # Append to intervention.photos (JSON list)
    try:
        photos = json.loads(intervention.photos) if intervention.photos else []
        photos.extend(saved)
        intervention.photos = json.dumps(photos)
        db.session.commit()
        # Return URLs (client can use /uploads/<filename>)
        urls = [f"/uploads/{fn}" for fn in saved]
        return jsonify({'success': True, 'files': urls})
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception('Error saving photos')
        return jsonify({'success': False, 'error': str(e)}), 500


@mobile_bp.route('/api/tracking', methods=['POST'])
@jwt_required
def api_tracking():
    """
    Store real-time tracking position with validation and rate limiting.
    
    Request JSON:
    {
        "latitude": 36.7372,
        "longitude": 3.0588,
        "accuracy": 5.2,
        "speed": 15.5,
        "altitude": 120,
        "timestamp": "2026-01-15T10:30:00Z",
        "status": "en_route|on_site|pause"  // optional
    }
    
    Returns: {success, tracking_id, retry_after, distance_traveled}
    """
    from models import ActivityLog, Intervention
    from utils_tracking import (
        validate_gps_coordinates, validate_gps_accuracy, 
        haversine_distance, can_track_update
    )
    
    data = request.get_json() or {}
    
    # Extract coordinates
    latitude = data.get('latitude') or data.get('lat')
    longitude = data.get('longitude') or data.get('lon') or data.get('lng')
    
    # Validate coordinates
    if latitude is None or longitude is None:
        return jsonify({
            'success': False,
            'error': 'Coordonnées GPS manquantes'
        }), 400
    
    is_valid, error_msg = validate_gps_coordinates(latitude, longitude, use_regional_bounds=False)
    if not is_valid:
        return jsonify({'success': False, 'error': error_msg}), 400
    
    # Validate accuracy if provided
    accuracy = data.get('accuracy')
    if accuracy:
        is_valid, error_msg = validate_gps_accuracy(accuracy, max_accuracy=200.0)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
    
    # Rate limiting: max 1 update every 30 seconds per technician
    can_update, retry_after = can_track_update(g.current_user.id)
    if not can_update:
        return jsonify({
            'success': False,
            'error': f'Trop de mises à jour. Attendez {retry_after}s',
            'retry_after': retry_after
        }), 429  # Too Many Requests
    
    try:
        # Get current intervention for this technician
        intervention = Intervention.query.filter_by(
            technicien_id=g.current_user.id,
            statut='en_cours'
        ).first()
        
        # Extract additional data
        speed = data.get('speed')
        altitude = data.get('altitude')
        status = data.get('status', 'en_route')
        timestamp = data.get('timestamp')
        
        if not timestamp:
            timestamp = datetime.utcnow().isoformat()
        
        # Parse timestamp if string
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                timestamp = datetime.utcnow()
        
        # Prepare details
        details = {
            'latitude': float(latitude),
            'longitude': float(longitude),
            'accuracy': float(accuracy) if accuracy else None,
            'speed': float(speed) if speed else None,
            'altitude': float(altitude) if altitude else None,
            'status': status,
            'timestamp': timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
            'intervention_id': intervention.id if intervention else None,
            'intervention_nd': intervention.demande.nd if intervention and intervention.demande else None
        }
        
        # Calculate distance from last position if intervention exists
        distance_traveled = 0.0
        if intervention and intervention.gps_lat and intervention.gps_long:
            distance_traveled = haversine_distance(
                float(intervention.gps_lat),
                float(intervention.gps_long),
                float(latitude),
                float(longitude)
            )
        
        # Update intervention GPS
        if intervention:
            intervention.gps_lat = latitude
            intervention.gps_long = longitude
            intervention.date_debut = intervention.date_debut or datetime.utcnow()
        
        # Create activity log entry
        log = ActivityLog(
            user_id=g.current_user.id,
            action='location_update',
            module='tracking',
            details=json.dumps(details, default=str),
            ip_address=request.remote_addr
        )
        
        db.session.add(log)
        db.session.commit()
        
        # Log successful tracking
        current_app.logger.info(
            f"[TRACKING] User {g.current_user.id} at ({latitude:.4f}, {longitude:.4f}), "
            f"accuracy: {accuracy}m, status: {status}"
        )
        
        return jsonify({
            'success': True,
            'tracking_id': log.id,
            'distance_traveled': round(distance_traveled, 2),
            'intervention_id': intervention.id if intervention else None,
            'timestamp': details['timestamp']
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f'[TRACKING] Error saving position: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }), 500


# ============================================================
# 🔍 BARCODE SCANNER API ENDPOINTS (SPRINT 2, TASK 2.2)
# ============================================================

@mobile_bp.route('/scanner', methods=['GET'])
@jwt_required
def barcode_scanner_page():
    """
    Mobile barcode scanner interface (HTML).
    Displays camera feed with barcode detection.
    """
    return render_template('barcode_scanner.html', user=g.current_user)


@mobile_bp.route('/api/barcode/scan', methods=['POST'])
@jwt_required
def api_barcode_scan():
    """
    Process a barcode scan and return matching products or interventions.
    
    Request JSON:
    {
        "barcode": "123456789",
        "type": "product|intervention|nd",  // default: "product"
        "action": "lookup|reserve"  // default: "lookup"
    }
    
    Returns: {success, data, type}
    """
    data = request.get_json() or {}
    barcode = str(data.get('barcode', '')).strip()
    scan_type = data.get('type', 'product').lower()  # product, intervention, nd
    action = data.get('action', 'lookup').lower()
    
    logger = current_app.logger
    logger.debug(f"[SCANNER] Scan received: barcode={barcode}, type={scan_type}, action={action}")
    
    if not barcode or len(barcode) < 3:
        return jsonify({
            'success': False,
            'error': 'Barcode invalide ou trop court'
        }), 400
    
    try:
        result = None
        
        # ========================================
        # PRODUCT SCAN (default)
        # ========================================
        if scan_type == 'product':
            # Search by code_produit (barcode) or produit.id
            produit = Produit.query.filter_by(code_produit=barcode).first() or \
                      Produit.query.filter_by(id=barcode).first()
            
            if not produit:
                return jsonify({
                    'success': False,
                    'error': f'Produit "{barcode}" introuvable',
                    'type': 'product'
                }), 404
            
            result = {
                'success': True,
                'type': 'product',
                'data': {
                    'id': produit.id,
                    'nom': produit.nom,
                    'code_produit': produit.code_produit,
                    'quantite_stock': produit.quantite_stock,
                    'prix_unitaire': float(produit.prix_unitaire) if produit.prix_unitaire else 0,
                    'stock_min': produit.stock_min or 0,
                    'sla_status': 'danger' if (produit.quantite_stock or 0) <= (produit.stock_min or 0) else 'ok'
                }
            }
            logger.info(f"[SCANNER] Product found: {produit.nom} (ID: {produit.id})")
            
            # If action is 'reserve', create or update reservation
            if action == 'reserve':
                try:
                    # Check for existing open reservation for this user & product
                    existing = Reservation.query.filter_by(
                        produit_id=produit.id,
                        user_id=g.current_user.id,
                        statut='en_attente'
                    ).first()
                    
                    if existing:
                        existing.quantite += 1
                        result['data']['reservation_status'] = 'updated'
                        result['data']['reservation_id'] = existing.id
                    else:
                        reservation = Reservation(
                            produit_id=produit.id,
                            user_id=g.current_user.id,
                            quantite=1,
                            statut='en_attente',
                            date_demande=datetime.utcnow()
                        )
                        db.session.add(reservation)
                        result['data']['reservation_status'] = 'created'
                        result['data']['reservation_id'] = reservation.id
                    
                    db.session.commit()
                    logger.info(f"[SCANNER] Reservation updated for user {g.current_user.id}, product {produit.id}")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"[SCANNER] Reservation error: {str(e)}")
                    result['reservation_error'] = str(e)
        
        # ========================================
        # INTERVENTION SCAN
        # ========================================
        elif scan_type == 'intervention':
            # Search by ID or by related demande.nd
            intervention = Intervention.query.filter_by(id=barcode).first()
            
            if not intervention:
                # Try to find by demande ND
                demande = DemandeIntervention.query.filter_by(nd=barcode).first()
                if demande:
                    intervention = Intervention.query.filter_by(demande_id=demande.id).first()
            
            if not intervention:
                return jsonify({
                    'success': False,
                    'error': f'Intervention "{barcode}" introuvable',
                    'type': 'intervention'
                }), 404
            
            # Permission check: technician can only see their own
            if g.current_user.role == 'technicien' and intervention.technicien_id != g.current_user.id:
                return jsonify({
                    'success': False,
                    'error': 'Accès non autorisé à cette intervention'
                }), 403
            
            demande = intervention.demande if intervention.demande else None
            result = {
                'success': True,
                'type': 'intervention',
                'data': {
                    'intervention_id': intervention.id,
                    'statut': intervention.statut,
                    'date_debut': intervention.date_debut.isoformat() if intervention.date_debut else None,
                    'date_fin': intervention.date_fin.isoformat() if intervention.date_fin else None,
                    'demande': {
                        'nd': demande.nd,
                        'nom_client': demande.nom_client,
                        'zone': demande.zone,
                        'type_techno': demande.type_techno
                    } if demande else {}
                }
            }
            logger.info(f"[SCANNER] Intervention found: ID={intervention.id}")
        
        # ========================================
        # DEMAND (ND) SCAN
        # ========================================
        elif scan_type == 'nd':
            # Search by ND number
            demande = DemandeIntervention.query.filter_by(nd=barcode).first()
            
            if not demande:
                return jsonify({
                    'success': False,
                    'error': f'Demande ND "{barcode}" introuvable',
                    'type': 'nd'
                }), 404
            
            intervention = Intervention.query.filter_by(demande_id=demande.id).first()
            
            # Permission check: technician can only see assigned interventions
            if g.current_user.role == 'technicien' and intervention:
                if intervention.technicien_id != g.current_user.id:
                    return jsonify({
                        'success': False,
                        'error': 'Accès non autorisé à cette demande'
                    }), 403
            
            result = {
                'success': True,
                'type': 'nd',
                'data': {
                    'nd': demande.nd,
                    'nom_client': demande.nom_client,
                    'zone': demande.zone,
                    'priorite_traitement': demande.priorite_traitement,
                    'statut': demande.statut,
                    'intervention_id': intervention.id if intervention else None,
                    'intervention_statut': intervention.statut if intervention else 'non_assignee'
                }
            }
            logger.info(f"[SCANNER] Demand found: ND={demande.nd}")
        
        # Unknown scan type
        else:
            return jsonify({
                'success': False,
                'error': f'Type de scan inconnu: {scan_type}'
            }), 400
        
        # ========================================
        # LOG SCAN (automatique)
        # ========================================
        try:
            from models import ActivityLog
            log = ActivityLog(
                user_id=g.current_user.id,
                action='barcode_scan',
                module='barcode_scanner',
                details=json.dumps({
                    'barcode': barcode,
                    'type': scan_type,
                    'action': action,
                    'result': 'success' if result.get('success') else 'error',
                    'data_keys': list(result.get('data', {}).keys()) if result.get('data') else []
                }, default=str),
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
        except Exception as log_error:
            db.session.rollback()
            logger.warning(f"[SCANNER] Failed to log scan: {str(log_error)}")
        
        return jsonify(result)
    
    except Exception as e:
        logger.exception(f"[SCANNER] Exception during scan: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }), 500


# ===== REMOVED =====
# Endpoint /api/barcode/manual POST - SUPPRIMÉ
# Raison: Consolidé dans /api/barcode/scan
# Les clients envoient simplement le barcode au endpoint /api/barcode/scan


@mobile_bp.route('/api/barcode/history', methods=['GET'])
@jwt_required
def api_barcode_history():
    """
    Get scan history for current user.
    
    Query params:
    - page: page number (default: 1)
    - per_page: results per page (default: 20, max: 100)
    - type: filter by scan type (product|intervention|nd)
    """
    page = max(1, request.args.get('page', 1, type=int))
    per_page = min(100, max(5, request.args.get('per_page', 20, type=int)))
    scan_type = request.args.get('type', '').lower()
    
    try:
        from models import ActivityLog
        
        query = ActivityLog.query.filter_by(
            user_id=g.current_user.id,
            action='barcode_scan'
        )
        
        if scan_type:
            # Filter by scan_type in details JSON
            query = query.filter(ActivityLog.details.like(f'%"type":"{scan_type}"%'))
        
        total = query.count()
        total_pages = (total + per_page - 1) // per_page if per_page else 1
        
        history = query.order_by(ActivityLog.timestamp.desc()) \
                      .offset((page - 1) * per_page) \
                      .limit(per_page) \
                      .all()
        
        items = []
        for log in history:
            try:
                details = json.loads(log.details) if log.details else {}
                items.append({
                    'id': log.id,
                    'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                    'barcode': details.get('barcode'),
                    'type': details.get('type'),
                    'action': details.get('action', 'lookup'),
                    'result': details.get('result', 'unknown')
                })
            except:
                pass
        
        return jsonify({
            'success': True,
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'history': items
        })
    
    except Exception as e:
        current_app.logger.exception('Error fetching scan history')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ===== REMOVED =====
# Endpoint /api/barcode/log-scan POST - SUPPRIMÉ
# Raison: Logging automatique dans /api/barcode/scan
# Chaque scan crée automatiquement une entrée ActivityLog avec tous les détails
