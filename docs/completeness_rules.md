# Règle de complétude des rapports d'intervention

But : définir des champs obligatoires par type d'intervention, calculer un score de complétude, empêcher la validation si score < 100% et stocker le score en base.

## Champs obligatoires par type (implémentés)
- Fibre : `numero`, `diagnostic_technicien`, `pieces`, `debit_cable_montant`
- Cuivre : `numero`, `diagnostic_technicien`, `pieces`
- 5G : `numero`, `diagnostic_technicien`

Les champs sont stockés sur le modèle `Intervention`.

## Calcul du score
- Le score est un entier 0-100 : (nombre de champs requis renseignés / total requis) * 100
- Méthode : `Intervention.compute_completeness()`
- Persistance : `Intervention.completeness_score` (colonne Integer, non nullable)

## Blocage de la validation
- Avant la transition `COMPLETED -> VALIDATED`, le système vérifie que `completeness_score == 100`.
- Si le score < 100, la tentative de validation échoue avec une erreur claire (`InvalidStateTransition` contenant le motif de l'échec).

## Tests
- Tests unitaires : `tests/test_completeness_rules.py` couvrant calcul, blocage et succès de validation.

## Bonnes pratiques
- Appeler `update_completeness()` après modification manuelle importante des champs (les formulaires/handlers peuvent appeler cela automatiquement juste avant la validation finale).
- Ajouter/modifier la liste `_REQUIRED_FIELDS_BY_TYPE` si de nouveaux types apparaissent.

## Migration
- Ajout d'une migration Alembic `migrations/versions/b1c2d3e4f5_add_completeness_score.py` qui ajoute la colonne `completeness_score` avec valeur par défaut 0.

---

Si tu veux, je peux: 
- ajouter un hook automatique (listener SQLAlchemy) pour recalculer la complétude au moment du `before_update`, ou
- ajouter la mise à jour automatique dans le endpoint de sauvegarde d'intervention.

Dis-moi si tu veux que j'ajoute l9une de ces améliorations.