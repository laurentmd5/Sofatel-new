"""
GUIDE D'INTÉGRATION - DASHBOARD RH COMPLET
Toutes les étapes pour intégrer le dashboard RH dans SOFATELCOM-V2
"""

# ============================================================
# ÉTAPE 1: MISE À JOUR DE app.py
# ============================================================

"""
Dans app.py, ajouter les imports et enregistrer le blueprint enrichi:

1. AJOUTER LES IMPORTS (line ~80):
"""

from routes.rh import rh_bp
from utils.rh_notifications import schedule_leave_reminders

"""
2. ENREGISTRER LE BLUEPRINT (line ~200, après les autres blueprints):
"""

app.register_blueprint(rh_bp, url_prefix='/api/rh')

"""
3. INTÉGRER LES ENDPOINTS SUPPLÉMENTAIRES DANS routes/rh.py:
   Copier le contenu de rh_extended_endpoints.py dans rh.py (avant la fin du fichier)
   OU importer:
"""

from routes.rh_extended_endpoints import *  # Import all extended endpoints

"""
4. PLANIFIER LES RAPPELS EMAIL (line ~230, dans with app.app_context()):
"""

with app.app_context():
    db.create_all()
    schedule_leave_reminders()  # Ajouter cette ligne


# ============================================================
# ÉTAPE 2: MODIFIER LES ROUTES PRINCIPALES (routes.py ou similar)
# ============================================================

"""
Ajouter une route pour afficher le dashboard RH:
"""

@app.route('/dashboard/rh')
@login_required
def dashboard_rh():
    # Vérifier les permissions
    if current_user.role != 'rh':
        flash('Accès refusé: seuls les utilisateurs RH peuvent accéder', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('dashboard_rh.html')


# ============================================================
# ÉTAPE 3: METTRE À JOUR LE MENU/NAVIGATION
# ============================================================

"""
Dans base.html ou le menu de navigation, ajouter un lien vers le dashboard RH:
"""

{% if current_user.role == 'rh' %}
<a href="{{ url_for('dashboard_rh') }}" class="nav-link">
    <i data-feather="users"></i> RH
</a>
{% endif %}


# ============================================================
# ÉTAPE 4: UTILISER LES FONCTIONS DE NOTIFICATION
# ============================================================

"""
Dans routes/rh.py, après la création d'une demande, appeler:
"""

from utils.rh_notifications import (
    send_leave_request_confirmation,
    send_leave_manager_notification,
    send_leave_decision_email
)

# Après db.session.commit() dans create_leave():
send_leave_request_confirmation(leave_request)

# Trouver le manager et envoyer notification
manager = User.query.filter_by(role='manager', zone=technicien.zone).first()
if manager:
    send_leave_manager_notification(leave_request, manager)


# ============================================================
# ÉTAPE 5: VARIABLES D'ENVIRONNEMENT REQUISES
# ============================================================

"""
Vérifier que le fichier .env contient:

# Email Configuration
MAIL_SERVER=smtp.gmail.com  (ou votre serveur)
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-password
MAIL_DEFAULT_SENDER=rh@sofatelcom.com

# Pour les tests sans email:
MAIL_SUPPRESS_SEND=True  (en développement)
"""


# ============================================================
# ÉTAPE 6: MISE À JOUR DE models.py (si nécessaire)
# ============================================================

"""
Le modèle LeaveRequest existe déjà. Vérifier qu'il contient:
- id (PK)
- technicien_id (FK)
- date_debut, date_fin
- type (conge_paye, maladie, absence, etc.)
- reason
- statut (pending, approved, rejected, cancelled)
- manager_id (FK - qui a approuvé)
- manager_comment
- created_at, updated_at, approved_at
- business_days_count
"""


# ============================================================
# ÉTAPE 7: PERMISSIONS RBAC
# ============================================================

"""
Le système utilise ces rôles:
- 'rh': Accès complet au dashboard RH
- 'chef_pur', 'chef_pilote': Peut valider les demandes
- 'technicien': Peut soumettre ses propres demandes
- 'admin': Accès complet

Les endpoints API ont des contrôles de permission:
- GET /api/rh/conges: Tous les connectés (filters par role)
- POST /api/rh/conges: Techniciens
- PATCH /api/rh/conges/{id}/validate: RH/Manager/Admin
- POST /api/rh/leave/bulk-approve: RH/Admin
- GET /api/rh/leave/stats: RH/Admin
- GET /api/rh/calendar/team: RH/Admin
- GET /api/rh/calendar/export.ics: RH/Admin
"""


# ============================================================
# ÉTAPE 8: TESTER L'INTÉGRATION
# ============================================================

"""
Checklist de test:

1. [ ] Technician peut soumettre une demande
   GET http://localhost:5000/dashboard/rh
   POST /api/rh/conges (data: date_debut, date_fin, type, reason)

2. [ ] Demande apparaît en attente pour RH
   GET /api/rh/conges?statut=pending

3. [ ] RH peut approuver/rejeter
   PATCH /api/rh/conges/{id}/validate (data: statut, manager_comment)

4. [ ] Email de confirmation envoyé (vérifier logs)
   Logger.info() dans send_leave_request_confirmation()

5. [ ] Calendrier affiche les absences
   GET /api/rh/calendar/team?year=2026&month=2

6. [ ] Statistiques calculées correctement
   GET /api/rh/leave/stats?year=2026

7. [ ] Export .ICS fonctionne
   GET /api/rh/calendar/export.ics?year=2026

8. [ ] Détection conflits
   POST /api/rh/leave/check-conflicts (data: date_debut, date_fin)

9. [ ] Actions groupées
   POST /api/rh/leave/bulk-approve (data: leave_ids, comment)
"""


# ============================================================
# ÉTAPE 9: CONFIGURATION PRODUCTION
# ============================================================

"""
Avant le déploiement:

1. Configurer le serveur email (Gmail, SendGrid, etc.)
2. Définir MAIL_USE_TLS approprié
3. Utiliser HTTPS en production
4. Tester les emails avec de vrais destinataires
5. Configurer l'APScheduler pour le serveur (Redis, etc.)
6. Mettre à jour les URLs des emails (approval_link)
7. Ajouter logging et monitoring des emails
"""


# ============================================================
# ÉTAPE 10: FICHIERS CRÉÉS/MODIFIÉS
# ============================================================

"""
Fichiers créés:
✓ templates/dashboard_rh.html (2500+ lignes)
✓ static/js/rh-dashboard.js (600+ lignes)
✓ routes/rh_extended_endpoints.py (400+ lignes)
✓ utils/rh_notifications.py (500+ lignes)

Fichiers modifiés:
- app.py: Ajouter imports et enregistrement blueprint
- routes.py: Ajouter route /dashboard/rh
- base.html: Ajouter lien menu
- models.py: Aucune modification (LeaveRequest existe)

Fichiers à vérifier:
- routes/rh.py: Blueprint existant
- extensions.py: Mail et scheduler doivent être configurés
- .env: Credentials email
"""


# ============================================================
# ENDPOINTS DISPONIBLES
# ============================================================

"""
GET /api/rh/conges
  - Lister les demandes (avec filtrage par status, technicien)
  - Query params: statut, technicien_id, page, per_page
  - Retour: list of leaves avec statut

POST /api/rh/conges
  - Soumettre une nouvelle demande
  - Body: technicien_id, date_debut, date_fin, type, reason
  - Validation: dates en futur, pas de chevauchement
  - Envoie email confirmation

GET /api/rh/conges/{id}
  - Détails d'une demande

PATCH /api/rh/conges/{id}/validate
  - Approuver ou rejeter
  - Body: statut (approved/rejected), manager_comment
  - Envoie email au technicien

POST /api/rh/leave/bulk-approve
  - Approuver plusieurs demandes
  - Body: leave_ids[], comment
  - RH only

POST /api/rh/leave/bulk-reject
  - Rejeter plusieurs demandes
  - Body: leave_ids[], comment
  - RH only

GET /api/rh/leave/stats
  - Statistiques par statut et technicien
  - Query params: year, month
  - Retour: total, pending, approved, rejected, by_technician

GET /api/rh/calendar/team
  - Calendrier avec absences par jour
  - Query params: year, month
  - Retour: calendar object (date -> count)

POST /api/rh/leave/check-conflicts
  - Détecter conflits et interventions impactées
  - Body: date_debut, date_fin, technicien_id
  - Retour: conflicting_leaves, interventions

PATCH /api/rh/leave/{id}/cancel
  - Annuler urgence un congé approuvé
  - Body: reason
  - RH only
  - Envoie alerte au technicien

GET /api/rh/calendar/export.ics
  - Exporter calendrier en format .ICS
  - Query params: year
  - Retour: .ICS file (calendar format)

GET /api/rh/export
  - Exporter tous les congés (CSV/JSON)
  - Admin only
"""


# ============================================================
# EXEMPLE D'UTILISATION FRONTEND
# ============================================================

"""
JavaScript dans le navigateur:

// Soumettre une demande
fetch('/api/rh/conges', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        technicien_id: 1,
        date_debut: '2026-02-01',
        date_fin: '2026-02-05',
        type: 'conge_paye',
        reason: 'Vacances en famille'
    })
})
.then(r => r.json())
.then(data => console.log('Leave ID:', data.id))

// Charger les demandes en attente
fetch('/api/rh/conges?statut=pending')
.then(r => r.json())
.then(data => console.log('Pending leaves:', data.leaves))

// Approuver une demande
fetch('/api/rh/conges/123/validate', {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        statut: 'approved',
        manager_comment: 'Accordé'
    })
})

// Charger le calendrier
fetch('/api/rh/calendar/team?year=2026&month=2')
.then(r => r.json())
.then(data => console.log('Calendar:', data.calendar))

// Exporter en .ICS
window.location.href = '/api/rh/calendar/export.ics?year=2026'
"""


# ============================================================
# TROUBLESHOOTING
# ============================================================

"""
Problème: Emails non envoyés
- Vérifier MAIL_SERVER, MAIL_PORT, credentials
- Logger dans console: MAIL_SUPPRESS_SEND=False
- Tester directement: app.extensions['mail'].send(msg)

Problème: 403 Unauthorized sur endpoints
- Vérifier role de l'utilisateur connecté
- Utiliser user avec role 'rh' pour test
- Logger dans la requête qui vérify les permissions

Problème: Dates invalides
- S'assurer format ISO (YYYY-MM-DD)
- Dates doivent être en futur pour création
- Fin >= Début

Problème: Calendrier vide
- S'assurer que des demandes sont approuvées
- Vérifier la plage dates/mois
- GET /api/rh/conges?statut=approved pour vérifier

Problème: APScheduler non tâches planifiées
- Vérifier que scheduler.start() est appelé dans app
- Logs: "Scheduled leave reminders task registered"
- Tester avec: scheduler.get_jobs()
"""


# ============================================================
# ROADMAP FUTURE
# ============================================================

"""
Possibilités d'extension:

1. Soldes de congés
   - Modèle LeaveBalance (technicien_id, days_available, days_used)
   - API: GET /api/rh/balance/{id}
   - Check au moment de la création

2. Approbation multi-niveaux
   - Approbation par manager local + RH
   - Workflow configurable
   - Statut intermédiaire "manager_approved"

3. Rapport d'absences
   - PDF export avec détails
   - Groupé par équipe, par mois
   - KPIs absence

4. Intégration planning
   - Auto-marquer technicien comme indisponible
   - Suggestions pour remplacement
   - Alertes conflits automatiques

5. Mobile app
   - Soumettre demande depuis app mobile
   - Push notifications
   - Calendrier dans app

6. Analyse/BI
   - Dashboard avec graphiques
   - Tendances absence (congés vs maladie)
   - Prédiction d'absences
   - Charge par équipe
"""
