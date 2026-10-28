# Notebooks : fine-tuning QLoRA

| Notebook | Rôle |
|---|---|
| [`01_qlora_finetune.ipynb`](01_qlora_finetune.ipynb) | Fine-tuning QLoRA (Unsloth) sur les paires décontaminées, puis export GGUF |

Ouvrir dans Colab : <https://colab.research.google.com/github/hasdaouiryma16-cmd/kabyle-llm-benchmark/blob/main/notebooks/01_qlora_finetune.ipynb>

## 1. Préparer les données (sur le PC, après avoir saisi le jeu de test)

```bash
docker compose run --rm api python -m pipelines.download
docker compose run --rm api python -m pipelines.prepare
docker compose run --rm api python -m pipelines.check_contamination   # doit afficher « OK »
```

Les fichiers à téléverser se trouvent dans `data/train/processed/` : `sft_train.jsonl` et `sft_valid.jsonl`.

## 2. Coûts et durées estimés (à lire avant de lancer)

Ce sont des estimations grossières, non mesurées. Hypothèses : modèle d'environ 4 milliards de paramètres en 4 bits, LoRA r=16, environ 60 tokens par exemple.

| Option | Coût | 60 000 exemples | Tout le corpus (≈ 185 000) |
|---|---|---|---|
| Colab gratuit (T4, non garanti, sessions ≤ 12 h) | 0 € | ≈ 1 à 1,5 h | ≈ 3 à 4 h |
| Kaggle gratuit (≈ 30 h de GPU par semaine) | 0 € | ≈ 1 à 1,5 h | ≈ 3 à 4 h |
| RTX 4090 louée (RunPod / Vast.ai, ≈ 0,34 à 0,90 $/h) | < 0,30 $ | ≈ 10 à 20 min | ≈ 30 à 60 min (< 1 $) |

Les prix ont été relevés le 28/10/2026 et fluctuent.

## 3. Servir le modèle fine-tuné avec Ollama

1. Installer Ollama sur le PC (<https://ollama.com>), puis `ollama pull qwen3.5:4b`.
2. Placer le fichier `.gguf` téléchargé dans un dossier, par exemple `models/` (ignoré par Git).
3. Créer un `Modelfile` à côté du `.gguf` :
   - si Unsloth en a généré un, l'utiliser tel quel ;
   - sinon, partir de celui du modèle de base, pour reprendre exactement le même gabarit de conversation :
     ```bash
     ollama show qwen3.5:4b --modelfile > Modelfile
     ```
     puis remplacer la ligne `FROM …` par `FROM ./kab-qwen3.5-4b.Q4_K_M.gguf` (nom exact du fichier).
4. Créer le modèle :
   ```bash
   ollama create kab-qwen3.5-4b -f Modelfile
   ```
5. Dans le labo, le modèle « Qwen3.5 4B fine-tuné (QLoRA) » (`qwen3.5-4b-lora` dans `backend/config/models.yaml`) devient disponible. Relancer **exactement** le même benchmark que pour le modèle de base.

## Changer de modèle de base

Dans le notebook, modifier `BASE_MODEL`, par exemple `unsloth/gemma-4-E4B-it`. Pour un modèle qui n'utilise pas le gabarit ChatML (`<|im_start|>`), adapter `instruction_part` et `response_part` dans `train_on_responses_only`. Dupliquer ensuite les entrées correspondantes dans `models.yaml`.
