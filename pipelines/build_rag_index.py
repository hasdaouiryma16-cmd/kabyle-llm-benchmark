"""Construit l'index RAG (data/train/processed/rag_index/) à partir des paires décontaminées.

Les vecteurs sont calculés par un modèle d'embedding multilingue servi par Ollama
(par défaut bge-m3, licence MIT, 1024 dimensions) puis normalisés : la recherche est un
simple produit scalaire (cosinus) avec numpy, suffisant pour quelques centaines de milliers
d'entrées et sans serveur de base vectorielle.

Sur le PC (si la mémoire le permet) :

    ollama pull bge-m3
    python -m pipelines.build_rag_index --embed-model bge-m3 [--limit 20000]

Sur Colab (PC trop juste en mémoire), en trois temps :

    python -m pipelines.build_rag_index --limit 20000 --export-colab
        → data/train/processed/rag_colab/rag_texts.jsonl (paires déjà décontaminées
          contre tout le jeu de test, privé compris : aucun test ne part sur Colab)
    notebooks/02_rag_index.ipynb  → embeddings.npy (même modèle bge-m3 via Ollama)
    python -m pipelines.build_rag_index --import-colab data/train/processed/rag_colab/embeddings.npy
"""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

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
COLAB_DIR = PROCESSED_DIR / "rag_colab"
COLAB_TEXTS = "rag_texts.jsonl"


def index_text(pair: dict[str, Any]) -> str:
    # On indexe la paire complète : une requête en français ou en kabyle la retrouve
    return f"{pair['fr']} | {pair['kab']}"


def texts_digest(pairs: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for pair in pairs:
        digest.update(index_text(pair).encode("utf-8") + b"\n")
    return digest.hexdigest()


def embed(texts: list[str], model: str, url: str) -> np.ndarray:
    response = httpx.post(f"{url}/api/embed", json={"model": model, "input": texts}, timeout=300)
    response.raise_for_status()
    return np.asarray(response.json()["embeddings"], dtype=np.float32)


def selected_pairs(limit: int) -> list[dict[str, Any]]:
    pairs = read_jsonl(PROCESSED_DIR / "pairs.jsonl")
    if limit:
        pairs = pairs[:limit]
    guard, _ = build_guard()
    return [p for p in pairs if not guard.check(p["fr"]) and not guard.check(p["kab"])]


def write_index(pairs: list[dict[str, Any]], matrix: np.ndarray, embed_model: str) -> None:
    matrix = matrix.astype(np.float32)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True).clip(min=1e-9)
    out = PROCESSED_DIR / "rag_index"
    out.mkdir(parents=True, exist_ok=True)
    write_jsonl(out / "entries.jsonl", pairs)
    np.save(out / "embeddings.npy", matrix)
    meta = {
        "embed_model": embed_model,
        "entries": len(pairs),
        "dim": int(matrix.shape[1]),
        "built_at": utcnow().isoformat(),
        "protected_test_fingerprint": protected_test_fingerprint(),
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"Index RAG : {len(pairs)} entrées, dimension {matrix.shape[1]}")


def export_colab(pairs: list[dict[str, Any]], embed_model: str) -> None:
    COLAB_DIR.mkdir(parents=True, exist_ok=True)
    # Seul le texte à vectoriser part sur Colab ; les paires complètes restent ici
    write_jsonl(COLAB_DIR / COLAB_TEXTS, ({"text": index_text(p)} for p in pairs))
    manifest = {
        "embed_model": embed_model,
        "entries": len(pairs),
        "texts_sha256": texts_digest(pairs),
        "pairs": pairs,
        "protected_test_fingerprint": protected_test_fingerprint(),
    }
    (COLAB_DIR / "pending.json").write_text(json.dumps(manifest, ensure_ascii=False), "utf-8")
    print(f"{len(pairs)} textes exportés : {COLAB_DIR / COLAB_TEXTS}")
    print("Téléverser ce fichier dans notebooks/02_rag_index.ipynb, puis rapporter embeddings.npy")


def import_colab(path: Path) -> None:
    pending_path = COLAB_DIR / "pending.json"
    if not pending_path.exists():
        raise SystemExit("Aucun export en attente : lancer d'abord --export-colab")
    pending = json.loads(pending_path.read_text("utf-8"))
    if pending["protected_test_fingerprint"] != protected_test_fingerprint():
        raise SystemExit("Le jeu de test a changé depuis l'export : refaire --export-colab")
    pairs = pending["pairs"]
    if texts_digest(pairs) != pending["texts_sha256"]:
        raise SystemExit("Export en attente corrompu : refaire --export-colab")
    matrix = np.load(path)
    if matrix.ndim != 2 or matrix.shape[0] != len(pairs):
        raise SystemExit(f"{path} : {matrix.shape} vecteurs, {len(pairs)} attendus (même export ?)")
    write_index(pairs, matrix, pending["embed_model"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embed-model", default="bge-m3")
    parser.add_argument("--limit", type=int, default=0, help="nombre max d'entrées (0 = toutes)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--export-colab", action="store_true", help="préparer le fichier pour Colab")
    mode.add_argument(
        "--import-colab", type=Path, metavar="NPY", help="embeddings calculés sur Colab"
    )
    args = parser.parse_args()

    if args.import_colab:
        import_colab(args.import_colab)
        return
    pairs = selected_pairs(args.limit)
    if args.export_colab:
        export_colab(pairs, args.embed_model)
        return

    url = SETTINGS.ollama_base_url.rstrip("/")
    vectors = []
    for start in range(0, len(pairs), BATCH):
        batch = pairs[start : start + BATCH]
        vectors.append(embed([index_text(p) for p in batch], args.embed_model, url))
        print(f"\r{min(start + BATCH, len(pairs))}/{len(pairs)}", end="", flush=True)
    print()
    write_index(pairs, np.vstack(vectors), args.embed_model)


if __name__ == "__main__":
    main()
