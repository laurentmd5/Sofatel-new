# Notes de sécurité — APScheduler

## Contexte
L'application utilise `APScheduler` pour exécuter des tâches planifiées :
- `check_delays` : vérification toutes les heures des interventions en retard
- `check_deadlines` : vérification quotidienne à 9h des échéances

Définies dans `app.py`, ces tâches appellent les fonctions `check_interventions_delayed()` et `check_interventions_deadline()` depuis `routes.py` (hooks globaux qui DOIVENT rester intacts lors du refactor).

## Risques principaux
1. **Exécution dupliquée** : en production avec plusieurs workers/processus, le scheduler peut s'exécuter dans chaque processus, causant plusieurs exécutions.
2. **Pas de verrouillage** : aucun mécanisme pour garantir une exécution unique.
3. **Dépendance sur `app.app_context()`** : les fonctions sont appelées avec l'app context, ce qui est correct.

## Recommandations (court terme)
- **Développement** : laisser APScheduler en place (acceptable, un seul processus).
- **Production** : implémenter l'une des solutions :
  
  A) **Processus dédié** (recommandé) :
     - Exécuter le scheduler dans un processus/container séparé.
     - Ex: `gunicorn -w 4 "app:app"` (workers sans scheduler) + `python run_scheduler.py` (processus dédié).
  
  B) **Verrou Redis** :
     - Installer `redis` et `redis-py`.
     - Wrapper les tâches avec un verrou distribué pour garantir unicité.
     - Code exemple :
       ```python
       import redis
       from contextlib import contextmanager
       
       redis_client = redis.Redis(host='localhost', port=6379)
       LOCK_TIMEOUT = 3600
       
       def with_lock(lock_key):
           def decorator(func):
               def wrapper(*args, **kwargs):
                   if redis_client.set(lock_key, '1', nx=True, ex=LOCK_TIMEOUT):
                       try:
                           return func(*args, **kwargs)
                       finally:
                           redis_client.delete(lock_key)
               return wrapper
           return decorator
       
       @scheduler.task('interval', id='check_delays', hours=1)
       @with_lock('check_delays_lock')
       def check_delays():
           # ...
       ```
  
  C) **Celery + Beat** :
     - Alternative complète à APScheduler.
     - Plus complexe mais scalable et robuste.

## Action immédiate
- Documenter la limitation actuellement (ce fichier).
- Reporter la migration vers processus dédié ou verrou Redis à la phase 2 du refactor (après validation des extractions de routes).

## Étapes de refactor liées à APScheduler
- Les fonctions `check_interventions_delayed()` et `check_interventions_deadline()` doivent :
  1. **Rester dans `routes.py`** ou être extraites vers un module séparé `routes/scheduler_tasks.py`.
  2. **Être importées et appelées depuis `app.py`** (inchangé).
  3. **JAMAIS** être déplacées de manière à briser les imports depuis `app.py`.

Voir `app.py` lignes 125-146 pour le contexte actuel.
