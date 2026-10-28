"""Pipelines de données de la phase 2 (téléchargement, nettoyage, contamination, index RAG).

Exécution dans le conteneur du labo, depuis la racine du dépôt :
    docker compose run --rm api python -m pipelines.download
    docker compose run --rm api python -m pipelines.prepare
    docker compose run --rm api python -m pipelines.check_contamination
    docker compose run --rm api python -m pipelines.build_rag_index
"""
