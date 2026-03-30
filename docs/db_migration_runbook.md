# RUNBOOK DE MIGRATION — BASE DE DONNÉES (Alembic + vérifs) ✅

> Objectif : Permettre à tout ingénieur compétent d’exécuter la migration de schéma en staging / production sans intervention supplémentaire. Ce runbook est prescriptif : suivez chaque étape et arrêtez-vous si un critère NO-GO se produit.

---

## 0) Métadonnées (OBLIGATOIRE) 🧾
- **Commit / Version du code** : `bf187a88acf9940c4730b4b121600ab7d5028fbe`
- **Auteur du runbook** : GitHub Copilot
- **Date** : 2026-01-13
- **Environnement cible** : (spécifier) staging / production
- **Fenêtre de maintenance proposée** : (ex : 02:00–03:00 UTC, durée estimée 15–30 min)
- **Responsable de validation** : (Nom du Lead Tech / approbateur)
- **Contact d’urgence DBA** : (nom + téléphone/email)

---

## 1) Checklist préalable (TOUT doit être vrai avant de commencer) ✅
- [ ] **Backup DB** : dump complet effectué et RESTORE testé sur instance isolée (procédure de test de restore documentée).
- [ ] **Scheduler / cron / APScheduler** : tous les jobs programmés arrêtés (ou planifiés pause) pendant la migration.
- [ ] **Accès admin DB** : credentials et accès OK (user avec droits ALTER / CREATE / DROP / INDEX).
- [ ] **Version Alembic connue** : exécuter `alembic current` et coller le résultat dans le rapport.
- [ ] **Notification utilisateurs** : annoncer la fenêtre de maintenance.
- [ ] **Plan de rollback prêt** (voir section Rollback).
- [ ] **Personne disponible pour validation post-migration** (Responsable de validation).

> Ne démarrez pas la migration sans cocher toutes les cases.

---

## 2) Audit DATA AVANT migration (CRITIQUE) — exécuter toutes les requêtes ci-dessous → critères GO/NO-GO

**a) Vérifier doublons `produits.code_barres`**

```sql
SELECT code_barres, COUNT(*) 
FROM produits 
WHERE code_barres IS NOT NULL
GROUP BY code_barres
HAVING COUNT(*) > 1;
```
- **Critère GO : 0 ligne retournée**
- Si >=1 ligne : **STOP migration** — corriger les doublons (merge, suppression, renommer) puis recommencer l’audit.

**b) Vérifier `intervention.statut` NULL**

```sql
SELECT COUNT(*) 
FROM intervention 
WHERE statut IS NULL;
```
- **Critère GO : = 0**
- Si >0 : **NOTES**
  - Si la migration inclut une correction (migration SQL populant les NULLs), documenter la logique ici.
  - Sinon, **STOP** et corriger les NULLs avant upgrade.

**c) (Recommandé) Vérifier autres points importants**

```sql
-- doublons clef unique prévue
SELECT code_barres, COUNT(*) FROM produits GROUP BY code_barres HAVING COUNT(*)>1;
-- FK orphan check (exemple intervention.demande_id)
SELECT i.id FROM intervention i LEFT JOIN demande_intervention d ON i.demande_id=d.id WHERE d.id IS NULL;
```
- Tout résultat significatif : **ajouter au plan de correction** avant migration.

---

## 3) Exécution des migrations (ordre strict) 🔁

**⚠️ RÈGLE ABSOLUE — VERROU DE SÉCURITÉ ANTI-ERREUR HUMAINE**

Avant d’exécuter la migration, vérifiez que la base ciblée correspond à l’environnement attendu :

```sql
SELECT DATABASE(), @@hostname;
```
- **Critère GO :** le nom de la base **ET** le hostname correspondent à l’environnement annoncé (staging / prod).
- Si incorrect : **STOP** et ne poursuivez pas.

---

**1) Activer l’environnement Python / virtuel (copier-coller)**

- Windows PowerShell

```powershell
.\venv\Scripts\Activate.ps1
```

- Linux / macOS

```bash
source venv/bin/activate
```

**2) Vérification Alembic (avant)**

```bash
alembic current
```

**3) Vérification supplémentaire (optionnel mais recommandée)**

```bash
# Vérifier l'état du dépôt et s'assurer d'être sur le bon commit
git fetch --all --prune
git checkout bf187a88acf9940c4730b4b121600ab7d5028fbe
```

**4) Appliquer migrations (ordre mécanique)**

```bash
alembic upgrade head
```

**5) Vérification Alembic (après)**

```bash
alembic current
```

> Sur erreur SQL/DDL : stopper et ne pas tenter de nettoyage manuel sans accord du Lead Tech/DBA.

---

## 4) Vérification post-migration (OBLIGATOIRE) ✅

Exécuter le script de vérification fourni :

```bash
mysql -u <admin_user> -p <your_database_name> < tools/migrations/verify_post_migration.sql
```

Critères GO (tous requis) :
- Toutes les **colonnes attendues** sont présentes (ex. SLA fields, intervention_history table, produits.code_barres, emplacement_stock).
- **Aucune colonne critique** (ex. intervention.statut, demande_intervention.service) n’est NULL si la contrainte l’exige.
- **Toutes les FK sont valides** (pas d’orphan rows).
- **Les index attendus existent** (ex. ix_intervention_statut, ix_mouvement_produit).
- **Tout test SQL du script renvoie OK**.

Règle : **Un seul check KO => rollback immédiat** (voir section Rollback).

---

## 5) Smoke tests fonctionnels (APPLI / API) — effectuer « mot pour mot » les actions ci-dessous (exigence) 🔬

- Login admin
- Création intervention
- Transition CREATED → ASSIGNED → IN_PROGRESS
- Tentative transition invalide (doit échouer)
- Validation → clôture
- GET /api/stats/performance (non vide)
- SSE /api/stream/interventions?once=1&interval=0

**Ajout : Test SLA minimal post-migration (SQL)**

```sql
SELECT
  id,
  sla_escalation_level,
  sla_last_alerted_at
FROM intervention
ORDER BY updated_at DESC
LIMIT 5;
```
- **Critère GO** :
  - Les colonnes existent
  - Les valeurs sont cohérentes (NULL autorisé si pas encore escaladé)

**Procédure concrète** :
1. Se connecter en tant qu’admin via UI ou curl (s’assurer que l’auth fonctionne).
2. Créer une demande et une intervention via formulaire ou endpoint.
3. Via UI/API, effectuer les transitions (vérifier codes HTTP 200 success, ou erreurs attendues si invalide).
4. GET /api/stats/performance — vérifier que la réponse contient des métriques (json non vide).
5. Connecter au SSE :

```bash
curl -N -H "Accept: text/event-stream" "http://<host>/api/stream/interventions?once=1&interval=0"
```
— vérifier que des données d’interventions sont streamées.

Documenter chaque étape avec screenshots / logs et coller les réponses HTTP / payloads.

---

## 6) Plan de rollback (NON NÉGOCIABLE) ⛑️

- **Trigger rollback** : tout échec de vérification post-migration ou smoke test KO.

**Rollback procédure** :
1. Stopper l'application (mettre en maintenance).
2. Restaurer la DB depuis le backup pris avant la migration :

```bash
mysql -u <admin> -p <your_database_name> < /path/to/pre_migration_dump.sql
```

3. Revenir au commit code précédent (pré-migration) :

```bash
git checkout <previous_commit_sha>
```

4. Redémarrer l'application (avec la DB restaurée).
5. **Validation rollback (smoke test minimal)** :
   - Login admin
   - GET /api/stats/performance (doit répondre)

> Note : Conserver les dumps de la migration ratée pour analyse (ne pas écraser).

---

## 7) Consignes Lead Tech (RÈGLE) — À respecter sans exception 🧠
- ❌ **Pas de migration en prod sans runbook validé** par le Lead Tech.
- ❌ **Pas de runbook sans critères GO / NO-GO** clairs (définis ci-dessus).
- ✅ Le runbook est document et livrable aussi important que le code.

---

## 8) Artefacts à joindre au ticket/PR (obligatoire)
- Commit SHA utilisé (`bf187a88acf9940c4730b4b121600ab7d5028fbe`).
- Résultats `alembic current` avant et après.
- Dump SQL pré-migration (lien / path).
- Sorties des queries d’audit PRE (copies).
- Sortie de `alembic upgrade head` (logs).
- Sortie / résultats de `tools/migrations/verify_post_migration.sql`.
- Résultats smoke tests (screenshots, logs).
- Personne(s) ayant validé (nom + timestamp).

---

## 9) Post-run notes & follow-up
- Si tous les checks sont GO, planifier une fenêtre de surveillance (ex : 2h post-migration) et monitorer métriques clés (SLA alerts, queue lengths, API errors).
- En cas d’anomalie après GO, suivre plan de rollback si issue critique (déterminée par Lead Tech/DBA).

---

> Si tu veux, je peux :
> - Générer une PR contenant ce fichier dans `docs/` (je peux créer la branche et ouvrir la PR), ou
> - Exécuter l’audit PRE si tu veux que j’exécute les queries (tu peux fournir accès ou coller les sorties), ou
> - Préparer un Playbook d’exécution (checklist imprimable) pour l’ops team.

---

*Fichier généré automatiquement — placer dans le dossier `docs/` et joindre au ticket / runbook officiel avant toute exécution.*
