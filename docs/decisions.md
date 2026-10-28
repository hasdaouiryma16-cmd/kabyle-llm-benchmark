# Journal des décisions techniques

Chaque décision importante est notée ici avec sa justification, pour pouvoir la défendre et la réviser.

| # | Date | Décision | Justification |
|---|---|---|---|
| 1 | 2026-10-28 | SQLite (SQLModel + Alembic) plutôt que PostgreSQL | Une seule utilisatrice, faible volume ; un seul fichier, aucun service à gérer. Migration possible plus tard. |
| 2 | 2026-10-28 | Jeu de test en JSONL dans Git, normalisé Unicode NFC | Versionné, lisible en diff, citable ; NFC évite que deux graphies identiques de « ḥ », « ɛ »… soient comparées comme différentes. |
| 3 | 2026-10-28 | Code sous Apache-2.0 | Permissive, avec clause explicite sur les brevets ; bien acceptée en entreprise. |
| 4 | 2026-10-28 | Données sous CC BY 4.0 | Réutilisation maximale (recherche et industrie) avec attribution obligatoire. |
| 5 | 2026-10-28 | ~20 % du jeu de test gardés privés (`data/test/private/`, ignoré par Git) | Le jeu public finira sur le web et potentiellement dans l'entraînement de futurs modèles ; la partie privée reste une mesure propre dans le temps. |
| 6 | 2026-10-28 | chrF++ comme métrique automatique principale, BLEU en secondaire, pas de COMET | chrF++ (n-grammes de caractères) est robuste à la morphologie riche et à l'orthographe variable ; COMET s'appuie sur XLM-R qui couvre mal le kabyle. |
| 7 | 2026-10-28 | Détection de langue avec GlotLID + détection d'écriture par plages Unicode | GlotLID couvre le kabyle ; l'écriture (latin / tifinagh / arabe) se détecte de façon déterministe. |
| 8 | 2026-10-28 | Labo uniquement local (écoute sur 127.0.0.1), site public statique séparé | Les clés API ne quittent jamais la machine ; le site ne contient que des résultats exportés via une liste blanche de champs. |
| 9 | 2026-10-28 | Protection des secrets : .gitignore + hook pre-commit (gitleaks, blocage des .env) + gitleaks en CI sur tout l'historique | Défense en profondeur : une erreur à un niveau est rattrapée au suivant. |
| 10 | 2026-10-28 | Tout le labo tourne dans Docker | Smart App Control (Windows) bloque des binaires non signés (bash, libcurl de Git) ; Docker isole l'environnement et rend le labo reproductible sur n'importe quelle machine. |
| 11 | 2026-10-28 | Le JSONL du dépôt est la source de vérité, la base SQLite en est une copie reconstructible | Les tests restent lisibles, versionnés et auditables ; la base peut être supprimée et rechargée à tout moment. Alembic (migrations) sera introduit quand la base contiendra des données non reconstructibles (réponses, notations). |
| 12 | 2026-10-28 | Empreinte SHA-256 du benchmark limitée aux champs évalués | Deux scores ne sont comparables que sur un jeu identique ; une note ou une date modifiée ne doit pas casser la comparabilité. |
| 13 | 2026-10-28 | Import « tout ou rien » avec rapport ligne par ligne | Évite un jeu de tests à moitié importé, difficile à diagnostiquer. |
| 14 | 2026-10-28 | Statuts `draft` / `ready` | Permet de saisir progressivement ; seul un test complet et validé entre dans le benchmark. |
