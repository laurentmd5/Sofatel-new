# Sécurité — recommandations et bonnes pratiques

## Remarques identifiées lors de l'audit
- `debug=True` ne doit pas être activé en production.
- `WTF_CSRF_CHECK_DEFAULT` était désactivé (risque) — il faut activer la vérification CSRF par défaut et envoyer le token dans les requêtes AJAX.
- `SESSION_COOKIE_SECURE` doit être `True` en production (HTTPS obligatoire).
- Les uploads ne sont pas suffisamment verrouillés : vérifier extension, type MIME et valider le contenu (PIL pour images).
- Utiliser `logging` plutôt que `print` et configurer la rotation des logs.

## Recommandations concrètes
1. Activer CSRF par défaut :
```python
app.config['WTF_CSRF_CHECK_DEFAULT'] = True
```
2. Envoyer le token CSRF via meta tag dans les templates et l'ajouter dans l'en-tête AJAX (`X-CSRFToken`).
3. Stocker secrets en variables d'environnement ou secret manager (Jamstack / Hashicorp Vault / Azure Key Vault...).
4. Exécuter les jobs planifiés dans un processus séparé ou utiliser un système de verrouillage pour éviter l'exécution multiple.
5. Scanner les dépendances (pip-audit / GitHub Dependabot) régulièrement.
