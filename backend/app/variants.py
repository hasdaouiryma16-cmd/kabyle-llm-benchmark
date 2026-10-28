"""Construction des messages envoyés aux modèles, selon la variante.

- base / finetuned : la consigne du test, telle quelle (précédée du texte de compréhension).
- fewshot : k exemples de traduction tirés des données d'amélioration, en tours de dialogue.
- rag : les k entrées les plus proches d'un index (dictionnaire / corpus), en contexte.

Les exemples et l'index ne proviennent QUE de data/train/processed/ et sont vérifiés contre
le jeu de test avant tout usage : une variante contaminée refuse de démarrer.
"""

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
import numpy as np

from app.contamination import ContaminationIndex, normalize, shingles
from app.registry import ModelConfig, Variant

FEWSHOT_FILE = "fewshot_pool.jsonl"
RAG_DIR = "rag_index"

# Gabarits (en français) des exemples few-shot ; le contenu kabyle vient du corpus.
FEWSHOT_TEMPLATES = {
    "fr_kab": "Traduis en kabyle : « {fr} »",
    "kab_fr": "Traduis en français : « {kab} »",
}

RAG_HEADER = (
    "Voici des paires de phrases kabyle–français tirées d'un corpus de référence. "
    "Elles peuvent t'aider à répondre.\n"
)


class ContaminationError(RuntimeError):
    pass


def user_message(snapshot: dict[str, Any]) -> str:
    if snapshot.get("context"):
        return f"{snapshot['context']}\n\n{snapshot['prompt']}"
    return snapshot["prompt"]


def _query_text(snapshot: dict[str, Any]) -> str:
    return snapshot.get("source_text") or snapshot.get("context") or snapshot["prompt"]


def _load_pairs(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} introuvable : lancer d'abord le pipeline de préparation (pipelines/)"
        )
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _assert_clean(pairs: list[dict[str, Any]], guard: ContaminationIndex, origin: str) -> None:
    for pair in pairs:
        for text in (pair.get("fr"), pair.get("kab")):
            if text and (match := guard.check(text)):
                raise ContaminationError(
                    f"{origin} contient une phrase du jeu de test ({match.test_id}, "
                    f"{match.kind}, similarité {match.similarity}) : variante bloquée"
                )


@dataclass
class FewShotSelector:
    pairs: list[dict[str, Any]]
    k: int
    selection: str = "similar"  # "similar" (plus proches en n-grammes) ou "random" (graine fixe)
    seed: int = 0
    _grams: list[set[str]] = field(default_factory=list, init=False)

    def __post_init__(self):
        self._grams = [shingles(normalize(p["fr"] + " " + p["kab"])) for p in self.pairs]

    def select(self, query: str) -> list[dict[str, Any]]:
        if self.selection == "random":
            return random.Random(self.seed).sample(self.pairs, min(self.k, len(self.pairs)))
        q = shingles(normalize(query))
        scored = sorted(
            range(len(self.pairs)),
            key=lambda i: (-len(q & self._grams[i]), i),
        )
        return [self.pairs[i] for i in scored[: self.k]]


class RagIndex:
    def __init__(self, directory: Path, ollama_url: str):
        meta_path = directory / "meta.json"
        if not meta_path.exists():
            raise FileNotFoundError(f"{directory} introuvable : lancer pipelines.build_rag_index")
        self.meta = json.loads(meta_path.read_text(encoding="utf-8"))
        self.entries = _load_pairs(directory / "entries.jsonl")
        self.vectors = np.load(directory / "embeddings.npy")
        self._ollama = ollama_url.rstrip("/")

    def embed(self, text: str) -> np.ndarray:
        response = httpx.post(
            f"{self._ollama}/api/embed",
            json={"model": self.meta["embed_model"], "input": [text]},
            timeout=60,
        )
        response.raise_for_status()
        vector = np.asarray(response.json()["embeddings"][0], dtype=np.float32)
        return vector / (np.linalg.norm(vector) or 1.0)

    def search(self, query: str, k: int) -> list[dict[str, Any]]:
        scores = self.vectors @ self.embed(query)  # vecteurs normalisés : cosinus
        top = np.argsort(-scores)[:k]
        return [self.entries[i] for i in top]


class PromptBuilder:
    """Prépare (system, messages) pour un modèle et un test donnés."""

    def __init__(self, train_dir: Path, ollama_url: str, guard: ContaminationIndex):
        self._train_dir = train_dir
        self._ollama_url = ollama_url
        self._guard = guard
        self._fewshot: dict[str, FewShotSelector] = {}
        self._rag: RagIndex | None = None

    def prepare(self, model: ModelConfig) -> None:
        """Charge et vérifie les ressources d'une variante (appelé avant le run)."""
        if model.variant == Variant.fewshot and model.key not in self._fewshot:
            pairs = _load_pairs(self._train_dir / FEWSHOT_FILE)
            _assert_clean(pairs, self._guard, FEWSHOT_FILE)
            self._fewshot[model.key] = FewShotSelector(
                pairs,
                k=int(model.variant_params.get("k", 5)),
                selection=model.variant_params.get("selection", "similar"),
            )
        if model.variant == Variant.rag and self._rag is None:
            rag = RagIndex(self._train_dir / RAG_DIR, self._ollama_url)
            _assert_clean(rag.entries, self._guard, RAG_DIR)
            self._rag = rag

    def build(
        self, model: ModelConfig, snapshot: dict[str, Any]
    ) -> tuple[str | None, list[dict[str, str]]]:
        question = {"role": "user", "content": user_message(snapshot)}
        if model.variant == Variant.fewshot:
            direction = "kab_fr" if snapshot["category"] == "translation_kab_fr" else "fr_kab"
            messages: list[dict[str, str]] = []
            for pair in self._fewshot[model.key].select(_query_text(snapshot)):
                target = pair["fr"] if direction == "kab_fr" else pair["kab"]
                prompt = FEWSHOT_TEMPLATES[direction].format(fr=pair["fr"], kab=pair["kab"])
                messages += [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": target},
                ]
            return None, [*messages, question]
        if model.variant == Variant.rag:
            assert self._rag is not None
            k = int(model.variant_params.get("k", 8))
            hits = self._rag.search(_query_text(snapshot), k)
            lines = [f"- français : {h['fr']} | kabyle : {h['kab']}" for h in hits]
            return RAG_HEADER + "\n".join(lines), [question]
        return None, [question]
