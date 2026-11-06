"""Vérifie que l'index RAG est compatible avec le modèle d'embedding servi localement.

Utile quand les vecteurs ont été calculés ailleurs (Colab) : on recalcule ici quelques
vecteurs avec l'Ollama du labo et on les compare à ceux de l'index (cosinus).

    python -m pipelines.verify_rag_index [--samples 8] [--min-cosine 0.98]
"""

import argparse
import json
import sys

import numpy as np

from pipelines.build_rag_index import embed, index_text
from pipelines.common import PROCESSED_DIR, SETTINGS, read_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--min-cosine", type=float, default=0.98)
    args = parser.parse_args()

    out = PROCESSED_DIR / "rag_index"
    meta = json.loads((out / "meta.json").read_text("utf-8"))
    entries = read_jsonl(out / "entries.jsonl")
    matrix = np.load(out / "embeddings.npy")
    step = max(1, len(entries) // args.samples)
    rows = list(range(0, len(entries), step))[: args.samples]
    local = embed(
        [index_text(entries[i]) for i in rows],
        meta["embed_model"],
        SETTINGS.ollama_base_url.rstrip("/"),
    )
    local /= np.linalg.norm(local, axis=1, keepdims=True).clip(min=1e-9)
    cosines = [float(local[k] @ matrix[i]) for k, i in enumerate(rows)]
    print(f"cosinus index / local : min {min(cosines):.4f}, moyenne {np.mean(cosines):.4f}")
    if min(cosines) < args.min_cosine:
        print("INCOMPATIBLE : vecteurs différents de ceux du labo, ne pas lancer le RAG")
        sys.exit(1)
    print("OK : index compatible avec le modèle d'embedding local")


if __name__ == "__main__":
    main()
