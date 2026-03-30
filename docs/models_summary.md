# Résumé des modèles (aperçu)

Ce document résume les principaux modèles définis dans `models.py`.

- `User` : id, username, email, password_hash, role, nom, prenom, telephone, zone, service, actif, date_creation
- `DemandeIntervention` : nd, zone, type_techno, nom_client, statut, service, date_demande_intervention, technicien_id, fichier_importe_id, etc.
- `FichierImport` : nom_fichier, date_import, importe_par, nb_lignes, nb_erreurs, statut
- `Equipe` : nom_equipe, date_creation, chef_zone_id, zone, technologies, service, publie, actif
- `MembreEquipe` : equipe_id, technicien_id, nom, prenom, telephone, type_membre
- `FicheTechnique` : fiche technique client / matériel / tests etc.
- `Survey` : formulaire de survey, photos, observations, lien vers intervention

> Pour les détails complets (colonnes et relations), voir `models.py`.
