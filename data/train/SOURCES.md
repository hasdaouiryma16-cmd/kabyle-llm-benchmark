# Sources des données d'amélioration (phase 2)

Chaque corpus utilisé pour le few-shot, le RAG ou le fine-tuning doit être listé ici **avant** utilisation.

| Source | URL | Licence | Date de collecte | Taille brute | Après nettoyage et dédoublonnage contre le test | Usage |
|---|---|---|---|---|---|---|
| *(à compléter en phase 2)* | | | | | | |

Règle : aucune phrase présente (exactement ou presque) dans `data/test/` ne peut figurer dans ces données.
Le contrôle est automatisé par `pipelines/check_contamination.py`.
