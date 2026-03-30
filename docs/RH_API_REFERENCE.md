📡 RH API ENDPOINTS - RÉFÉRENCE COMPLÈTE
═══════════════════════════════════════════════════════════════════════════════

BASE URL: http://localhost:5000/api/rh/

AUTHENTICATIION:
- Tous les endpoints requièrent login_required
- RBAC: contrôle permissions par role


1️⃣ LEAVE REQUESTS - Gestion demandes
═══════════════════════════════════════════════════════════════════════════════

GET /conges
───────────
Description: Lister les demandes de congé
Auth:        Required (filtered by role)
Query Params:
  - statut: pending|approved|rejected|cancelled
  - technicien_id: Filtrer par employé
  - page: Numéro page (défaut: 1)
  - per_page: Résultats par page (défaut: 20, max: 100)

Response (200):
{
  "success": true,
  "page": 1,
  "total": 10,
  "total_pages": 1,
  "leaves": [
    {
      "id": 1,
      "technicien_id": 5,
      "technicien": {"id": 5, "username": "john", "nom": "Doe", "prenom": "John"},
      "date_debut": "2026-02-01",
      "date_fin": "2026-02-05",
      "type": "conge_paye",
      "reason": "Vacation",
      "statut": "pending",
      "business_days": 5,
      "created_at": "2026-01-15T10:30:00",
      "approved_at": null,
      "manager": null,
      "manager_comment": null
    }
  ]
}

Example:
  curl http://localhost:5000/api/rh/conges?statut=pending


POST /conges
────────────
Description: Créer une nouvelle demande
Auth:        Required (techniciens can create own)
Content-Type: application/json

Body:
{
  "technicien_id": 5,           // Required
  "date_debut": "2026-02-01",   // Required, ISO format
  "date_fin": "2026-02-05",     // Required, ISO format
  "type": "conge_paye",         // Required: conge_paye|maladie|absence|conge_sans_solde|rtt
  "reason": "Vacation in family" // Required: min 10 chars
}

Response (201):
{
  "success": true,
  "id": 123,
  "statut": "pending",
  "business_days": 5,
  "message": "Leave request submitted successfully"
}

Errors:
  400 - Missing/Invalid fields
  403 - Unauthorized (can't create for others)
  404 - Technicien not found
  409 - Overlapping leaves

Example:
  curl -X POST http://localhost:5000/api/rh/conges \
    -H "Content-Type: application/json" \
    -d '{
      "technicien_id": 5,
      "date_debut": "2026-02-01",
      "date_fin": "2026-02-05",
      "type": "conge_paye",
      "reason": "Vacances en famille"
    }'


GET /conges/{id}
────────────────
Description: Obtenir détails d'une demande
Auth:        Required (owner or manager can view)
Path Params:
  - id: Leave request ID

Response (200):
{
  "success": true,
  "leave": {
    "id": 1,
    "technicien": {...},
    "date_debut": "2026-02-01",
    "date_fin": "2026-02-05",
    "type": "conge_paye",
    "business_days": 5,
    "reason": "Vacation",
    "statut": "approved",
    "created_at": "2026-01-15T10:30:00",
    "approved_at": "2026-01-16T14:00:00",
    "manager": {"id": 1, "username": "boss"},
    "manager_comment": "Accordé"
  }
}

Errors:
  404 - Leave not found
  403 - Unauthorized

Example:
  curl http://localhost:5000/api/rh/conges/123


2️⃣ VALIDATION - Approuver/Rejeter demandes
═══════════════════════════════════════════════════════════════════════════════

PATCH /conges/{id}/validate
─────────────────────────────
Description: Approuver ou rejeter une demande
Auth:        Required (rh, chef_pur, chef_pilote, admin)
Content-Type: application/json
Path Params:
  - id: Leave request ID

Body:
{
  "statut": "approved",          // Required: approved|rejected
  "manager_comment": "Accordé"   // Required: raison approbation/rejet
}

Response (200):
{
  "success": true,
  "message": "Leave request approved"
}

Errors:
  403 - Unauthorized
  404 - Leave not found
  409 - Leave not in pending status

Example:
  curl -X PATCH http://localhost:5000/api/rh/conges/123/validate \
    -H "Content-Type: application/json" \
    -d '{
      "statut": "approved",
      "manager_comment": "Accordé sans problème"
    }'


POST /leave/bulk-approve
─────────────────────────
Description: Approuver plusieurs demandes à la fois
Auth:        Required (rh, chef_pur, admin)
Content-Type: application/json

Body:
{
  "leave_ids": [1, 2, 3],           // Required: array of IDs
  "comment": "Batch approval"       // Optional
}

Response (200):
{
  "success": true,
  "approved": 3,
  "message": "3 leave(s) approved"
}

Errors:
  403 - Unauthorized
  400 - Invalid leave_ids

Example:
  curl -X POST http://localhost:5000/api/rh/leave/bulk-approve \
    -H "Content-Type: application/json" \
    -d '{"leave_ids": [1, 2, 3], "comment": "Approuvé"}'


POST /leave/bulk-reject
────────────────────────
Description: Rejeter plusieurs demandes à la fois
Auth:        Required (rh, chef_pur, admin)
Content-Type: application/json

Body:
{
  "leave_ids": [1, 2, 3],
  "comment": "Raison du rejet"
}

Response (200):
{
  "success": true,
  "rejected": 3,
  "message": "3 leave(s) rejected"
}


3️⃣ STATISTIQUES ET REPORTING
═══════════════════════════════════════════════════════════════════════════════

GET /leave/stats
────────────────
Description: Obtenir statistiques des congés
Auth:        Required (rh, admin)
Query Params:
  - year: Filtre année (défaut: année courante)
  - month: Filtre mois (optionnel)

Response (200):
{
  "success": true,
  "year": 2026,
  "month": 2,
  "total": 15,
  "pending": 3,
  "approved": 10,
  "rejected": 2,
  "by_technician": {
    "John Doe": {
      "total_days": 12,
      "approved_days": 10,
      "pending": 1
    },
    "Jane Smith": {
      "total_days": 8,
      "approved_days": 5,
      "pending": 2
    }
  }
}

Example:
  curl http://localhost:5000/api/rh/leave/stats?year=2026&month=2


GET /calendar/team
──────────────────
Description: Obtenir calendrier d'équipe avec absences
Auth:        Required (rh, admin)
Query Params:
  - year: Année (défaut: courante)
  - month: Mois (défaut: courant)

Response (200):
{
  "success": true,
  "calendar": {
    "2026-02-01": {
      "count": 2,
      "names": ["John Doe", "Jane Smith"]
    },
    "2026-02-02": {
      "count": 1,
      "names": ["John Doe"]
    }
  },
  "year": 2026,
  "month": 2
}

Example:
  curl http://localhost:5000/api/rh/calendar/team?year=2026&month=2


GET /calendar/export.ics
────────────────────────
Description: Exporter calendrier en format .ICS
Auth:        Required (rh, admin)
Query Params:
  - year: Année (défaut: courante)

Response (200):
File download (.ICS format for Outlook/Google Calendar)

Content-Type: text/calendar
Content-Disposition: attachment; filename="sofatelcom-calendar-2026.ics"

Example:
  curl http://localhost:5000/api/rh/calendar/export.ics?year=2026 -o calendar.ics


4️⃣ GESTION CONFLITS
═══════════════════════════════════════════════════════════════════════════════

POST /leave/check-conflicts
────────────────────────────
Description: Vérifier conflits et interventions impactées
Auth:        Required
Content-Type: application/json

Body:
{
  "date_debut": "2026-02-01",        // Required: ISO format
  "date_fin": "2026-02-05",          // Required: ISO format
  "technicien_id": 5                 // Optional: défaut = current user
}

Response (200):
{
  "success": true,
  "conflicts": [
    {
      "type": "leave",
      "date_debut": "2026-02-01",
      "date_fin": "2026-02-03",
      "reason": "Existing conge_paye approved"
    }
  ],
  "interventions": [
    {
      "id": 123,
      "date_debut": "2026-02-04T09:00:00",
      "date_fin": "2026-02-04T17:00:00",
      "type": "installation",
      "client": "Client ABC"
    }
  ],
  "has_conflicts": true,
  "has_interventions": true
}

Example:
  curl -X POST http://localhost:5000/api/rh/leave/check-conflicts \
    -H "Content-Type: application/json" \
    -d '{
      "date_debut": "2026-02-01",
      "date_fin": "2026-02-05",
      "technicien_id": 5
    }'


PATCH /leave/{id}/cancel
──────────────────────────
Description: Annuler urgence un congé approuvé
Auth:        Required (rh, chef_pur, admin)
Path Params:
  - id: Leave request ID

Body:
{
  "reason": "Emergency situation - need technician"
}

Response (200):
{
  "success": true,
  "message": "Leave cancelled"
}

Errors:
  403 - Unauthorized
  404 - Leave not found
  409 - Leave not in approved status


5️⃣ EXPORT
═══════════════════════════════════════════════════════════════════════════════

GET /export
────────────
Description: Exporter toutes les demandes
Auth:        Required (admin, manager, chef_pur)

Response (200):
{
  "success": true,
  "export": [
    {
      "id": 1,
      "technicien": "john_doe",
      "date_debut": "2026-02-01",
      "date_fin": "2026-02-05",
      "type": "conge_paye",
      "business_days": 5,
      "statut": "approved",
      "created_at": "2026-01-15T10:30:00",
      "approved_by": "boss_user"
    }
  ]
}


═══════════════════════════════════════════════════════════════════════════════

HTTP STATUS CODES
─────────────────

200 - OK (succès)
201 - Created (ressource créée)
400 - Bad Request (données invalides)
403 - Forbidden (permissions insuffisantes)
404 - Not Found (ressource inexistante)
409 - Conflict (conflit détecté)
500 - Internal Server Error


AUTHENTICATION HEADERS
──────────────────────

Tous les endpoints requièrent login_required.
Les cookies de session sont automatiquement envoyés.

Optional headers:
  Accept: application/json
  Content-Type: application/json (pour POST/PATCH)


EXEMPLES COMPLETS (JavaScript)
═══════════════════════════════════════════════════════════════════════════════

// Créer demande
async function submitLeaveRequest() {
  const response = await fetch('/api/rh/conges', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    },
    body: JSON.stringify({
      technicien_id: 5,
      date_debut: '2026-02-01',
      date_fin: '2026-02-05',
      type: 'conge_paye',
      reason: 'Vacances en famille'
    })
  });
  
  const data = await response.json();
  console.log('Leave created:', data.id);
  return data;
}

// Charger demandes en attente
async function loadPendingLeaves() {
  const response = await fetch('/api/rh/conges?statut=pending');
  const data = await response.json();
  console.log('Pending leaves:', data.leaves);
  return data.leaves;
}

// Approuver demande
async function approveLeave(leaveId) {
  const response = await fetch(`/api/rh/conges/${leaveId}/validate`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      statut: 'approved',
      manager_comment: 'Accordé'
    })
  });
  
  const data = await response.json();
  console.log('Leave approved');
  return data;
}

// Charger statistiques
async function loadStatistics() {
  const response = await fetch('/api/rh/leave/stats?year=2026');
  const data = await response.json();
  console.log('Stats:', data);
  return data;
}


EXEMPLES COMPLETS (cURL)
═════════════════════════════════════════════════════════════════════════════

# Créer demande
curl -X POST http://localhost:5000/api/rh/conges \
  -H "Content-Type: application/json" \
  -d '{
    "technicien_id": 5,
    "date_debut": "2026-02-01",
    "date_fin": "2026-02-05",
    "type": "conge_paye",
    "reason": "Vacation"
  }' \
  -b cookies.txt

# Lister demandes en attente
curl http://localhost:5000/api/rh/conges?statut=pending \
  -b cookies.txt

# Approuver demande
curl -X PATCH http://localhost:5000/api/rh/conges/123/validate \
  -H "Content-Type: application/json" \
  -d '{"statut": "approved", "manager_comment": "Accordé"}' \
  -b cookies.txt

# Obtenir statistiques
curl http://localhost:5000/api/rh/leave/stats?year=2026 \
  -b cookies.txt

# Télécharger calendrier .ICS
curl http://localhost:5000/api/rh/calendar/export.ics?year=2026 \
  -o calendar.ics \
  -b cookies.txt


═══════════════════════════════════════════════════════════════════════════════
