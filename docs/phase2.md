# Phase 2 : améliorer un petit modèle open source

## 1. Choix du modèle

Candidats vérifiés le 28/10/2026 (fiches Hugging Face et bibliothèque Ollama) :

| Modèle | Paramètres | Licence | Langues annoncées | Ollama | Unsloth (QLoRA) |
|---|---|---|---|---|---|
| **Qwen3.5 4B** (`Qwen/Qwen3.5-4B`) | 4,7 Md | Apache 2.0 | « 201 langues et dialectes » | `qwen3.5:4b` | `unsloth/Qwen3.5-4B` |
| **Gemma 4 E4B** (`google/gemma-4-E4B-it`) | ≈ 4 Md effectifs (8 Md en mémoire) | Apache 2.0 | pré-entraîné sur plus de 140 langues | `gemma4:e4b` | `unsloth/gemma-4-E4B-it` |
| **Apertus 8B** (`swiss-ai/Apertus-8B-Instruct-2509`) | 8 Md | Apache 2.0 | « 1 811 langues », pré-entraîné sur FineWeb-2, qui contient une partie kabyle | via `hf.co/unsloth/Apertus-8B-Instruct-2509-GGUF` | `unsloth/Apertus-8B-Instruct-2509-unsloth-bnb-4bit` |

Aucune des trois fiches ne cite explicitement le kabyle.

**Démarche.** On mesure d'abord les trois modèles de base sur le benchmark, puis on améliore celui qui offre le meilleur compromis. **Qwen3.5 4B est préconfiguré par défaut** : licence permissive, rapide sur un T4 gratuit, bien pris en charge par Unsloth. Apertus 8B est le plus intéressant scientifiquement, car il a probablement vu du kabyle à l'entraînement, mais il est deux fois plus lourd.

## 2. Données d'amélioration

Les sources et licences sont détaillées dans [`data/train/SOURCES.md`](../data/train/SOURCES.md). Le pipeline :

```bash
docker compose run --rm api python -m pipelines.download            # Tatoeba + Common Voice
docker compose run --rm api python -m pipelines.prepare             # nettoyage + décontamination
docker compose run --rm api python -m pipelines.check_contamination # doit afficher « OK »
```

Le premier passage, avec un jeu de test encore vide, a donné :
- 93 908 paires Tatoeba en entrée, 93 645 conservées (196 doublons, 67 invalides retirés) ;
- 178 095 phrases monolingues Common Voice.

Les comptes à jour sont dans [`data/train/processed/STATS.json`](../data/train/processed/STATS.json).

> ⚠️ **Relancer `prepare` après chaque ajout au jeu de test**, pour retirer d'éventuelles phrases qui le recoupent. Le labo refuse de toute façon de lancer une variante few-shot ou RAG dont les données sont contaminées.

## 3. Les trois approches

| # | Approche | Principe | Configuration |
|---|---|---|---|
| 1 | **Few-shot** | Les k paires de Tatoeba les plus proches de la phrase à traduire (similarité de 5-grammes de caractères) sont ajoutées comme tours de dialogue avant la question | `qwen3.5-4b-fewshot`, k = 5 |
| 2 | **RAG** | Les k paires les plus proches selon des embeddings multilingues (`bge-m3` via Ollama, cosinus) sont fournies en contexte système | `qwen3.5-4b-rag`, k = 8 ; index : `python -m pipelines.build_rag_index` |
| 3 | **Fine-tuning QLoRA** | Adaptateur LoRA (r = 16) sur le modèle quantifié en 4 bits, entraîné sur les paires décontaminées dans les deux sens | [`notebooks/01_qlora_finetune.ipynb`](../notebooks/01_qlora_finetune.ipynb), puis `qwen3.5-4b-lora` |

**Pourquoi la recherche vectorielle se fait avec numpy plutôt qu'avec une base vectorielle.** Pour moins de 100 000 entrées, un produit matriciel sur des vecteurs normalisés prend quelques millisecondes. Il n'y a pas de serveur à gérer, et le comportement reste entièrement transparent.

## 4. Coûts et durées estimés (fine-tuning)

Ce sont des estimations grossières, non mesurées. Hypothèses : modèle d'environ 4 milliards de paramètres en 4 bits, LoRA r = 16, environ 60 tokens par exemple.

| Option | Coût | 60 000 exemples, 1 époque | ≈ 185 000 exemples (tout) |
|---|---|---|---|
| Colab gratuit (T4, non garanti, sessions ≤ 12 h) | 0 € | ≈ 1 à 1,5 h | ≈ 3 à 4 h |
| Kaggle gratuit (≈ 30 h de GPU par semaine) | 0 € | ≈ 1 à 1,5 h | ≈ 3 à 4 h |
| RTX 4090 louée (RunPod communautaire ≈ 0,34 $/h ; Vast.ai ≈ 0,34 à 0,61 $/h) | < 0,30 $ | ≈ 10 à 20 min | ≈ 30 à 60 min (< 1 $) |

Recommandation : commencer gratuitement sur Kaggle ou Colab avec 60 000 exemples. Rien n'est lancé automatiquement.

## 5. Mesurer le gain (phase 3)

1. Servir le modèle fine-tuné avec Ollama (voir [`notebooks/README.md`](../notebooks/README.md)).
2. Lancer **une seule exécution** contenant le modèle de base et ses trois variantes, sur toutes les catégories, sans le mode test.
3. Noter à l'aveugle : les réponses des quatre modèles sont mélangées.
4. L'onglet Résultats calcule les gains appariés par catégorie, et le site les publie après export.
