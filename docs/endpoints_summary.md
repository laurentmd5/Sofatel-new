# Résumé des endpoints importants

> Ce fichier liste les endpoints les plus utilisés et leurs objectifs. Pour chaque endpoint, vérifiez les autorisations (rôles) dans les vues.

- `GET /` → redirection vers `dashboard` (authentifié)
- `GET/POST /login` → connexion
- `GET /logout` → déconnexion
- `GET /dashboard` → tableau de bord, pages par rôle

- `POST /survey/create` → création d'un survey (upload de photos possible)
- `GET /surveys` → liste des surveys (pagination)
- `GET /survey/<id>` → détail d'un survey

- `POST /import-demandes` → upload et traitement d'un fichier Excel pour créer des demandes d'intervention

- `POST /api/publish-selected-teams` → publication d'équipes (AJAX, rôles : chef_zone/chef_pur)
- `POST /api/unpublish-selected-teams` → dé-publication d'équipes

- `GET /uploads/<filename>` → téléchargement d'assets (auth requis)

- `Routes /gestion-stock` → gestion du stock (blueprint `stock_bp`)
- `Routes /interventions` → gestion des interventions (blueprint `interventions`)
- `Routes /reservations` → gestion des réservations (blueprint `reservations`)

- Intervention SLA and history APIs (mounted under `/interventions` blueprint):
  - `POST /interventions/api/intervention/<id>/ack_sla` → Acknowledge SLA for an intervention (login required)
  - `POST /interventions/api/intervention/<id>/manager_approve` → Approve intervention as manager (role: chef_* or admin)
  - `GET  /interventions/api/intervention/<id>/history` → Get intervention action/history entries

  Examples (with session cookie after login):

  - Acknowledge SLA:

    curl -X POST -b cookiejar.txt -c cookiejar.txt http://localhost:5000/interventions/api/intervention/123/ack_sla

  - Manager approve:

    curl -X POST -b cookiejar.txt -c cookiejar.txt http://localhost:5000/interventions/api/intervention/123/manager_approve

  - Get history:

    curl -X GET -b cookiejar.txt -c cookiejar.txt http://localhost:5000/interventions/api/intervention/123/history

> Pour plus de détails, voir `routes.py` et les fichiers `routes_*.py`.
