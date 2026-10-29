"""Construit l'index RAG (data/train/processed/rag_index/) à partir des paires décontaminées.

Les vecteurs sont calculés par un modèle d'embedding multilingue servi par Ollama
(par défaut bge-m3, licence MIT, 1024 dimensions) puis normalisés : la recherche est un
simple produit scalaire (cosinus) avec numpy, suffisant pour quelques centaines de milliers
d'entrées et sans serveur de base vectorielle.

    ollama pull bge-m3
    python -m pipelines.build_rag_index --embed-model bge-m3 [--limit 20000]
"""

import argparse
import json

import httpx
import numpy as np

from app.models import utcnow
from pipelines.common import (
    PROCESSED_DIR,
    SETTINGS,
    build_guard,
    protected_test_fingerprint,
    read_jsonl,
    write_jsonl,
)

BATCH = 64


def embed(texts: list[str], model: str, url: str) -> np.ndarray:
    response = httpx.post(f"{url}/api/embed", json={"model": model, "input": texts}, timeout=300)
    response.raise_for_status()
    return np.asarray(response.json()["embeddings"], dtype=np.float32)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embed-model", default="bge-m3")
    parser.add_argument("--limit", type=int, default=0, help="nombre max d'entrées (0 = toutes)")
    args = parser.parse_args()

    pairs = read_jsonl(PROCESSED_DIR / "pairs.jsonl")
    if args.limit:
        pairs = pairs[: args.limit]
    guard, _ = build_guard()
    pairs = [p for p in pairs if not guard.check(p["fr"]) and not guard.check(p["kab"])]

    url = SETTINGS.ollama_base_url.rstrip("/")
    vectors = []
    for start in range(0, len(pairs), BATCH):
        batch = pairs[start : start + BATCH]
        # On indexe la paire complète : une requête en français ou en kabyle la retrouve
        vectors.append(embed([f"{p['fr']} | {p['kab']}" for p in batch], args.embed_model, url))
        print(f"\r{min(start + BATCH, len(pairs))}/{len(pairs)}", end="", flush=True)
    print()
    matrix = np.vstack(vectors)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True).clip(min=1e-9)

    out = PROCESSED_DIR / "rag_index"
    out.mkdir(parents=True, exist_ok=True)
    write_jsonl(out / "entries.jsonl", pairs)
    np.save(out / "embeddings.npy", matrix)
    meta = {
        "embed_model": args.embed_model,
        "entries": len(pairs),
        "dim": int(matrix.shape[1]),
        "built_at": utcnow().isoformat(),
        "protected_test_fingerprint": protected_test_fingerprint(),
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"Index RAG : {len(pairs)} entrées, dimension {matrix.shape[1]}")


if __name__ == "__main__":
    main()
