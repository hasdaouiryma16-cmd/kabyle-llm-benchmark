"""Détection de contamination entre le jeu de test et les données d'amélioration.

Deux contrôles :
- doublon exact après normalisation (NFC, minuscules, sans ponctuation ni espaces multiples) ;
- quasi-doublon : similarité de Jaccard sur des 5-grammes de caractères ≥ seuil.

Utilisé par les pipelines (filtrage), par le backend (refus de lancer une variante few-shot/RAG
contaminée) et par la CI (échec du build).
"""

import hashlib
import re
import unicodedata
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

SHINGLE = 5
NEAR_DUP_THRESHOLD = 0.8
MIN_LEN_NEAR_DUP = 15  # en dessous, seul le doublon exact est pertinent

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)
_SPACES = re.compile(r"\s+")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text).casefold()
    text = _PUNCT.sub(" ", text)
    return _SPACES.sub(" ", text).strip()


def shingles(text: str) -> set[str]:
    if len(text) < SHINGLE:
        return {text} if text else set()
    return {text[i : i + SHINGLE] for i in range(len(text) - SHINGLE + 1)}


def protected_strings(records: Iterable[dict]) -> list[tuple[str, str]]:
    """Toutes les chaînes d'un jeu de test qui ne doivent jamais apparaître ailleurs,
    sous forme (identifiant du test, texte)."""
    out = []
    for r in records:
        for key in ("prompt", "source_text", "context"):
            if r.get(key):
                out.append((r["id"], r[key]))
        for ref in r.get("references") or []:
            out.append((r["id"], ref))
    return out


def protected_fingerprint(records: Iterable[dict]) -> str:
    """Empreinte de l'ensemble des chaînes protégées : si elle change, les données
    d'amélioration doivent être régénérées (pipelines.prepare) avant tout usage."""
    texts = sorted(normalize(text) for _, text in protected_strings(records))
    return hashlib.sha256("\n".join(texts).encode("utf-8")).hexdigest()


@dataclass
class Match:
    candidate: str
    test_id: str
    test_text: str
    kind: str  # "exact" | "near"
    similarity: float


class ContaminationIndex:
    def __init__(self, protected: list[tuple[str, str]], threshold: float = NEAR_DUP_THRESHOLD):
        self.threshold = threshold
        self._exact: dict[str, tuple[str, str]] = {}
        self._entries: list[tuple[str, str, set[str]]] = []
        self._inverted: dict[str, list[int]] = defaultdict(list)
        for test_id, text in protected:
            norm = normalize(text)
            if not norm:
                continue
            self._exact[norm] = (test_id, text)
            if len(norm) >= MIN_LEN_NEAR_DUP:
                grams = shingles(norm)
                index = len(self._entries)
                self._entries.append((test_id, text, grams))
                for gram in grams:
                    self._inverted[gram].append(index)

    def check(self, candidate: str) -> Match | None:
        norm = normalize(candidate)
        if not norm:
            return None
        if norm in self._exact:
            test_id, text = self._exact[norm]
            return Match(candidate, test_id, text, "exact", 1.0)
        if len(norm) < MIN_LEN_NEAR_DUP:
            return None
        grams = shingles(norm)
        overlap: dict[int, int] = defaultdict(int)
        for gram in grams:
            for index in self._inverted.get(gram, ()):
                overlap[index] += 1
        best: Match | None = None
        for index, common in overlap.items():
            test_id, text, test_grams = self._entries[index]
            similarity = common / (len(grams) + len(test_grams) - common)
            if similarity >= self.threshold and (best is None or similarity > best.similarity):
                best = Match(candidate, test_id, text, "near", round(similarity, 3))
        return best

    def check_all(self, candidates: Iterable[str]) -> list[Match]:
        return [m for c in candidates if (m := self.check(c))]
