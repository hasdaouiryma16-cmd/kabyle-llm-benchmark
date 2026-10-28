# Fiche du jeu de données : Kabyle LLM Benchmark (jeu de test)

> Mise à jour à chaque nouvelle version du jeu (voir `MANIFEST.json`).

## Résumé

Jeu de test destiné à évaluer la maîtrise du kabyle (taqbaylit, ISO 639-3 `kab`) par les modèles de langage. Il couvre six catégories : traduction français → kabyle, traduction kabyle → français, compréhension, culture, écriture (latin et tifinagh) et conversation.

## Auteurs et provenance

- Toutes les références en kabyle, les textes de compréhension et les consignes rédigées en kabyle sont écrits par [@hasdaouiryma16-cmd](https://github.com/hasdaouiryma16-cmd), locutrice native.
- **Aucun texte kabyle n'est généré par IA.** Les consignes en français du mode guidé sont listées dans `data/prompts/guided_fr.yaml`.
- Le champ `source` de chaque test indique son origine (`author`, `guided:<id>`…).

## Contenu et format

- `kab-bench.v1.jsonl` : partie publique, une ligne JSON par test, UTF-8, Unicode NFC.
- Partie privée (≈ 20 %) : non publiée, pour une évaluation à l'abri de la contamination.
- Le schéma complet est dans [`docs/testset-format.md`](../../docs/testset-format.md).
- `MANIFEST.json` contient la version, les empreintes SHA-256 (partie publique, partie privée, tests évalués), le nombre de tests par catégorie et la chaîne canari.

## Usage prévu

- **Évaluation uniquement** de modèles de langage sur le kabyle.
- **Interdit :** utiliser ce jeu pour l'entraînement, le réglage fin, le few-shot ou la constitution d'index RAG d'un modèle évalué ensuite sur ce même jeu.
- La chaîne canari du manifeste permet de détecter une contamination.

## Licence

[CC BY 4.0](../../LICENSE-DATA.md) : réutilisation libre avec attribution.

## Limites connues

- **Une seule annotatrice** : la variation dialectale et orthographique du kabyle n'est que partiellement couverte. Plusieurs références par test atténuent ce biais.
- **Taille modeste** : adaptée à une évaluation comparative, pas à des conclusions statistiques fines.
- **Thèmes du quotidien surreprésentés** par construction du mode guidé.

## Citation

Voir [`CITATION.cff`](../../CITATION.cff).
