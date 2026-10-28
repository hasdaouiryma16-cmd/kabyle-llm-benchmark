# Fiche du jeu de données : Kabyle LLM Benchmark (jeu de test)

> Brouillon, complété au fur et à mesure de la saisie des tests.

## Résumé
Jeu de test destiné à évaluer la maîtrise du kabyle (taqbaylit) par les modèles de langage :
traduction (fr→kab, kab→fr), compréhension, culture, écriture (latin et tifinagh), conversation.

## Auteurs
Toutes les références en kabyle sont écrites par [@hasdaouiryma16-cmd](https://github.com/hasdaouiryma16-cmd), locutrice native.
Aucun texte kabyle n'est généré par IA.

## Format
JSONL (une ligne par test), UTF-8, normalisé NFC. Schéma documenté dans `docs/` (étape 1).

## Version
Voir `MANIFEST.json` (version, empreinte SHA-256, nombre d'items, chaîne canari).

## Licence
CC BY 4.0 (voir `LICENSE-DATA.md`).

## Usage prévu
Évaluation uniquement. **Ne pas utiliser pour l'entraînement.**

## Limites connues
- Une seule annotatrice : la variation dialectale et orthographique du kabyle n'est que partiellement couverte
  (atténuée par la possibilité de plusieurs références par test).
- Taille modeste, adaptée à une évaluation comparative plutôt qu'à des conclusions statistiques fines.
