"""
MODIFICATIONS PRÉCISES POUR app.py ET AUTRES FICHIERS
Code exact à ajouter/modifier
"""

# ============================================================
# app.py - MODIFICATIONS EXACTES
# ============================================================

"""
1. LIGNE ~80: Ajouter après les autres imports de Blueprint

   From:
   from routes.mobile import mobile_bp
   from routes.gps_stream import gps_stream_bp
   
   To:
   from routes.mobile import mobile_bp
   from routes.gps_stream import gps_stream_bp
   from routes.rh import rh_bp  # <-- AJOUTER CETTE LIGNE
"""

"""
2. LIGNE ~230: Dans with app.app_context(): after db.create_all()

   From:
   with app.app_context():
       db.create_all()
   
   To:
   with app.app_context():
       db.create_all()
       # Schedule leave reminders  # <-- AJOUTER CES LIGNES
       try:
           from utils.rh_notifications import schedule_leave_reminders
           schedule_leave_reminders()
       except Exception as e:
           app.logger.warning(f"Could not schedule leave reminders: {e}")
"""

"""
3. LIGNE ~250: Register blueprints (ajouter après les autres)

   From:
   app.register_blueprint(mobile_bp, url_prefix='/api/mobile')
   app.register_blueprint(gps_stream_bp, url_prefix='/api/gps')
   
   To:
   app.register_blueprint(mobile_bp, url_prefix='/api/mobile')
   app.register_blueprint(gps_stream_bp, url_prefix='/api/gps')
   app.register_blueprint(rh_bp, url_prefix='/api/rh')  # <-- AJOUTER
"""


# ============================================================
# routes.py OU routes/__init__.py - AJOUTER ROUTE
# ============================================================

"""
Ajouter cette nouvelle route pour afficher le dashboard RH:
"""

@app.route('/dashboard/rh')
@login_required
def dashboard_rh():
    """RH Dashboard - Manage leave requests"""
    if current_user.role != 'rh':
        flash('Accès refusé: seuls les utilisateurs RH peuvent accéder à ce dashboard', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('dashboard_rh.html')


# ============================================================
# base.html - AJOUTER LIEN MENU
# ============================================================

"""
Dans le menu de navigation (après les autres dashboards):

{% if current_user.role == 'rh' %}
<li class="nav-item">
    <a class="nav-link" href="{{ url_for('dashboard_rh') }}">
        <i data-feather="users" class="me-2"></i>
        RH & Congés
    </a>
</li>
{% endif %}
"""


# ============================================================
# routes/rh.py - INTÉGRER ENDPOINTS ÉTENDUS
# ============================================================

"""
À la FIN du fichier routes/rh.py, ajouter:

# ============================================================
# EXTENDED ENDPOINTS - Validation, Stats, Calendar, Conflicts
# ============================================================

[COPIER TOUT LE CONTENU DE rh_extended_endpoints.py]

OU plus simple: ajouter les imports à la fin:

from routes.rh_extended_endpoints import *
"""


# ============================================================
# utils/__init__.py - AJOUTER IMPORTS
# ============================================================

"""
Si utils/ est un package avec __init__.py, ajouter:

from utils.rh_notifications import (
    send_leave_request_confirmation,
    send_leave_manager_notification,
    send_leave_decision_email,
    send_leave_reminder,
    send_team_alert_email,
    send_emergency_cancellation_email,
    schedule_leave_reminders
)
"""


# ============================================================
# MODIFICATION: routes/rh.py - create_leave() endpoint
# ============================================================

"""
Dans la fonction create_leave() (line ~120), après db.session.commit():

AJOUTER CES LIGNES:

        try:
            # Log audit
            log_audit(
                action='leave_request_created',
                entity_type='leave_request',
                entity_id=leave_request.id,
                new_value={
                    'technicien_id': technicien_id,
                    'date_debut': start_date.isoformat(),
                    'date_fin': end_date.isoformat(),
                    'type': leave_type,
                    'business_days': business_days
                },
                details={'reason': reason}
            )
            
            # AJOUTER: Send confirmation email
            from utils.rh_notifications import send_leave_request_confirmation, send_leave_manager_notification
            
            send_leave_request_confirmation(leave_request)
            
            # Find manager and send notification
            manager = None
            if technicien.zone:
                manager = User.query.filter_by(
                    role='chef_zone',
                    zone=technicien.zone,
                    actif=True
                ).first()
            if not manager:
                manager = User.query.filter_by(role='chef_pur', actif=True).first()
            
            if manager:
                send_leave_manager_notification(leave_request, manager)
            
            return jsonify({
                'success': True,
                'id': leave_request.id,
                'statut': leave_request.statut,
                'business_days': business_days,
                'message': 'Leave request submitted successfully'
            }), 201
"""


# ============================================================
# MODIFICATION: models.py - Vérifier LeaveRequest (optionnel)
# ============================================================

"""
Vérifier que LeaveRequest contient ces colonnes:

class LeaveRequest(db.Model):
    __tablename__ = 'leave_request'
    id = db.Column(db.Integer, primary_key=True)
    technicien_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    statut = db.Column(db.String(20), default='pending')
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    manager_comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    business_days_count = db.Column(db.Float, default=0)

Si des colonnes manquent, créer une migration:
$ flask db migrate -m "Add missing columns to leave_request"
$ flask db upgrade
"""


# ============================================================
# .env - VÉRIFIER/AJOUTER CONFIGURATION EMAIL
# ============================================================

"""
Vérifier que .env contient:

MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@sofatelcom.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=rh@sofatelcom.com

Pour Gmail:
- Enable 2FA
- Create App Password: https://myaccount.google.com/apppasswords
- Utiliser l'App Password comme MAIL_PASSWORD

Pour envirionnement de développement:
MAIL_SUPPRESS_SEND=True  (pour éviter d'envoyer vraiment les mails)

Pour production:
MAIL_SUPPRESS_SEND=False
MAIL_USE_TLS=True
"""


# ============================================================
# STRUCTURE DES FICHIERS CRÉÉS
# ============================================================

"""
Fichiers créés:

templates/dashboard_rh.html (2500+ lignes)
  ├─ 5 onglets principaux
  ├─ Formulaire demande congé
  ├─ Calendrier mensuel
  ├─ Interface validation (RH)
  └─ Statistiques

static/js/rh-dashboard.js (600+ lignes)
  ├─ loadMyRequests()
  ├─ submitLeaveRequest()
  ├─ loadTeamCalendar()
  ├─ loadStatistics()
  ├─ loadPendingRequests()
  ├─ validateLeave()
  └─ Utility functions

routes/rh_extended_endpoints.py (450+ lignes)
  ├─ validate_leave()
  ├─ bulk_approve_leaves()
  ├─ bulk_reject_leaves()
  ├─ get_leave_statistics()
  ├─ get_team_calendar()
  ├─ check_leave_conflicts()
  ├─ cancel_leave()
  └─ export_calendar_ics()

utils/rh_notifications.py (500+ lignes)
  ├─ Email templates
  ├─ send_leave_request_confirmation()
  ├─ send_leave_manager_notification()
  ├─ send_leave_decision_email()
  ├─ send_leave_reminder()
  ├─ send_team_alert_email()
  ├─ schedule_leave_reminders()
  └─ Utility functions
"""


# ============================================================
# PERMISSIONS & RBAC MATRIX
# ============================================================

"""
Dashboard RH:
- Route: /dashboard/rh
- Accès: role == 'rh'

API Endpoints:
┌─────────────────────────────────────────────────┬──────────────────────────────────┐
│ Endpoint                                        │ Permissions                      │
├─────────────────────────────────────────────────┼──────────────────────────────────┤
│ GET /api/rh/conges                             │ authenticated (filtered by role)  │
│ POST /api/rh/conges                            │ authenticated (can create own)    │
│ GET /api/rh/conges/{id}                        │ owner or rh/manager              │
│ PATCH /api/rh/conges/{id}/validate            │ rh, chef_pur, chef_pilote, admin │
│ POST /api/rh/leave/bulk-approve               │ rh, chef_pur, admin              │
│ POST /api/rh/leave/bulk-reject                │ rh, chef_pur, admin              │
│ GET /api/rh/leave/stats                       │ rh, admin                        │
│ GET /api/rh/calendar/team                     │ rh, admin                        │
│ POST /api/rh/leave/check-conflicts            │ authenticated                    │
│ PATCH /api/rh/leave/{id}/cancel               │ rh, chef_pur, admin              │
│ GET /api/rh/calendar/export.ics               │ rh, admin                        │
│ GET /api/rh/export                            │ admin, manager, chef_pur         │
└─────────────────────────────────────────────────┴──────────────────────────────────┘
"""


# ============================================================
# TESTING CHECKLIST
# ============================================================

"""
Test unitaire:
□ Créer demande de congé
  POST /api/rh/conges
  
□ Vérifier dates valides
  Pas de dates passées, pas de chevauchement
  
□ Tester permissions
  Technicien ne peut créer que pour lui
  RH peut pour tout le monde
  
□ Test validation
  Approuver demande
  Rejeter demande avec commentaire
  
□ Test statistiques
  GET /api/rh/leave/stats?year=2026
  Vérifier count par status
  
□ Test calendrier
  GET /api/rh/calendar/team?year=2026&month=2
  Vérifier données
  
□ Test emails (si configuré)
  Vérifier logs: "email sent to ..."
  Ou vérifier dans console SMTP

□ Test bulk operations
  POST /api/rh/leave/bulk-approve
  POST /api/rh/leave/bulk-reject
  
□ Test export .ICS
  GET /api/rh/calendar/export.ics?year=2026
  File téléchargeable en format calendar
"""


# ============================================================
# DÉPLOIEMENT PRODUCTION
# ============================================================

"""
Avant mise en production:

1. Email
   - [ ] Configurer serveur email réel (Gmail, SendGrid, etc.)
   - [ ] Tester avec vrais destinataires
   - [ ] Vérifier templates visuellement dans email client
   - [ ] Ajouter signature/footer standardisé

2. Database
   - [ ] Migration: alembic upgrade head
   - [ ] Backup avant migration
   - [ ] Tester rollback

3. Security
   - [ ] HTTPS activé
   - [ ] CSRF tokens validés
   - [ ] Rate limiting sur endpoints
   - [ ] Input validation complete

4. Monitoring
   - [ ] Logs email errors
   - [ ] Alerte sur failed emails
   - [ ] Monitor APScheduler jobs
   - [ ] Dashboard erreurs RH

5. Performance
   - [ ] Paginer les listes
   - [ ] Cache calendrier (5 min TTL)
   - [ ] Indexes sur date_debut, statut, technicien_id
   - [ ] Query optimization pour stats

6. Backup
   - [ ] Backup leave_request table
   - [ ] Plan restore si incident
   - [ ] Test restore régulièrement
"""
