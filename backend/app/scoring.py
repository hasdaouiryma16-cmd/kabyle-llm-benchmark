"""Notation automatique : chrF++, BLEU, écriture et langue de la réponse.

chrF++ est la métrique principale (n-grammes de caractères + mots) : robuste pour une langue
morphologiquement riche dont l'orthographe varie. BLEU est fourni pour comparaison avec la
littérature. Ces scores sont des indicateurs ; la note humaine fait foi.
"""

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from sacrebleu.metrics import BLEU, CHRF

_CHRF = CHRF(word_order=2)  # chrF++
_BLEU = BLEU(effective_order=True)  # BLEU de phrase

_WRAPPING_QUOTES = "\"'«»“”„‘’`"

# Petits mots très fréquents du français, quasi absents du kabyle écrit
_FRENCH_STOPWORDS = {
    "le", "la", "les", "un", "une", "des", "du", "de", "et", "est", "je", "tu", "il", "elle",
    "nous", "vous", "ils", "elles", "que", "qui", "dans", "pour", "pas", "ne", "ce", "cette",
    "sur", "avec", "au", "aux", "mon", "ma", "mes", "son", "sa", "ses", "voici", "c'est",
}  # fmt: skip


def clean_output(text: str | None) -> str:
    """Retire espaces et guillemets englobants (« … »), sans toucher au contenu."""
    text = unicodedata.normalize("NFC", text or "").strip()
    while (
        len(text) >= 2
        and text[0] in _WRAPPING_QUOTES
        and text[-1] in _WRAPPING_QUOTES
        and not any(q in text[1:-1] for q in _WRAPPING_QUOTES)  # « a » et « b » : intact
    ):
        text = text[1:-1].strip()
    return text


def chrf(hypothesis: str, references: list[str]) -> float | None:
    if not references or not hypothesis:
        return 0.0 if references else None
    return round(_CHRF.sentence_score(hypothesis, references).score, 2)


def bleu(hypothesis: str, references: list[str]) -> float | None:
    if not references or not hypothesis:
        return 0.0 if references else None
    return round(_BLEU.sentence_score(hypothesis, references).score, 2)


def detect_script(text: str) -> str | None:
    """Écriture dominante parmi latin, tifinagh, arabe (plages Unicode, déterministe)."""
    counts = {"latin": 0, "tifinagh": 0, "arabic": 0, "other": 0}
    for char in text:
        if not char.isalpha():
            continue
        code = ord(char)
        if 0x2D30 <= code <= 0x2D7F:
            counts["tifinagh"] += 1
        elif 0x0600 <= code <= 0x06FF or 0x0750 <= code <= 0x077F or 0xFB50 <= code <= 0xFEFF:
            counts["arabic"] += 1
        elif unicodedata.name(char, "").startswith("LATIN"):
            counts["latin"] += 1
        else:
            counts["other"] += 1
    total = sum(counts.values())
    if total == 0:
        return None
    script, count = max(counts.items(), key=lambda kv: kv[1])
    return script if count / total >= 0.6 else "mixed"


@dataclass
class LangGuess:
    lang: str | None  # code ISO 639-3 (kab, fra, ara…) ou None si indéterminé
    confidence: float | None
    method: str


class LanguageDetector:
    """GlotLID (fastText) si le modèle est installé, sinon heuristique prudente.

    L'heuristique ne sait distinguer que : arabe (écriture), français (mots outils),
    tifinagh (écriture). Elle ne prétend jamais reconnaître le kabyle : « kab » n'est
    renvoyé que par GlotLID.
    """

    def __init__(self, model_path: Path | None = None):
        self._model = None
        if model_path and model_path.exists():
            try:
                import fasttext  # dépendance optionnelle

                self._model = fasttext.load_model(str(model_path))
            except ImportError:
                self._model = None

    @property
    def method(self) -> str:
        return "glotlid" if self._model else "heuristic"

    def detect(self, text: str) -> LangGuess:
        text = text.strip()
        if not text:
            return LangGuess(None, None, self.method)
        if self._model:
            labels, probs = self._model.predict(text.replace("\n", " "), k=1)
            code = labels[0].removeprefix("__label__").split("_")[0]
            return LangGuess(code, round(float(probs[0]), 3), "glotlid")
        script = detect_script(text)
        if script == "arabic":
            return LangGuess("ara", None, "heuristic")
        if script == "tifinagh":
            return LangGuess(None, None, "heuristic")  # langue berbère, laquelle : inconnu
        words = re.findall(r"\w+(?:'\w+)?", text.casefold())
        if words:
            ratio = sum(w in _FRENCH_STOPWORDS for w in words) / len(words)
            if ratio >= 0.2 and len(words) >= 3:
                return LangGuess("fra", round(ratio, 3), "heuristic")
        return LangGuess(None, None, "heuristic")


EXPECTED_LANG_CODES = {"kab": "kab", "fr": "fra", "fra": "fra"}


def language_ok(
    expected: str, guess: LangGuess, script: str | None, expected_script: str
) -> bool | None:
    """La réponse est-elle dans la langue attendue ? None si on ne peut pas trancher."""
    expected_code = EXPECTED_LANG_CODES.get(expected, expected)
    if guess.lang is not None and guess.method == "glotlid":
        return guess.lang == expected_code
    # Heuristique : on ne peut affirmer que des échecs évidents
    if expected_code == "kab":
        if guess.lang in ("ara", "fra"):
            return False
        if script and script not in ("mixed", expected_script):
            return False
        return None
    if expected_code == "fra":
        if guess.lang == "fra":
            return True
        if script in ("arabic", "tifinagh"):
            return False
    return None
