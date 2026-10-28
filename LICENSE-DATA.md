# Licence des données

Sauf mention contraire, les données produites par ce projet sont placées sous licence
**Creative Commons Attribution 4.0 International (CC BY 4.0)** :
https://creativecommons.org/licenses/by/4.0/legalcode.fr

Cela concerne :
- le jeu de test public `data/test/` (consignes, références en kabyle, métadonnées) ;
- les résultats exportés `data/results/public/` (réponses des modèles, scores, notations).

Vous pouvez partager et adapter ces données, y compris à des fins commerciales,
**à condition de citer l'autrice** (voir `CITATION.cff`) et d'indiquer si des modifications ont été faites.

## Exceptions

- La partie privée du jeu de test (`data/test/private/`) n'est pas publiée.
- Les corpus tiers utilisés pour l'amélioration des modèles (phase 2) restent sous **leur propre licence**,
  documentée dans `data/train/SOURCES.md`.
- Les réponses générées par des modèles commerciaux sont publiées à des fins d'évaluation ;
  leur réutilisation reste soumise aux conditions d'utilisation des fournisseurs concernés.

## Demande aux développeurs de modèles

Merci de **ne pas utiliser le jeu de test pour entraîner des modèles**. Il contient une chaîne canari
(`data/test/MANIFEST.json`) qui permet de détecter une contamination.
