"""Modèle de données d'un test du benchmark.

Les classes sont nommées « BenchItem » (et non « Test… ») pour ne pas être confondues
avec des tests unitaires par pytest.
"""

import re
import unicodedata
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import field_validator, model_validator
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Category(StrEnum):
    translation_fr_kab = "translation_fr_kab"
    translation_kab_fr = "translation_kab_fr"
    comprehension = "comprehension"
    culture = "culture"
    writing = "writing"
    conversation = "conversation"


# Préfixe des identifiants générés automatiquement (ex. tr-fr-kab-0001)
CATEGORY_PREFIX: dict[Category, str] = {
    Category.translation_fr_kab: "tr-fr-kab",
    Category.translation_kab_fr: "tr-kab-fr",
    Category.comprehension: "comp",
    Category.culture: "cult",
    Category.writing: "writ",
    Category.conversation: "conv",
}

CATEGORY_LABEL_FR: dict[Category, str] = {
    Category.translation_fr_kab: "Traduction français → kabyle",
    Category.translation_kab_fr: "Traduction kabyle → français",
    Category.comprehension: "Compréhension",
    Category.culture: "Culture",
    Category.writing: "Écriture",
    Category.conversation: "Conversation",
}

TRANSLATION_CATEGORIES = {Category.translation_fr_kab, Category.translation_kab_fr}


class Script(StrEnum):
    latin = "latin"
    tifinagh = "tifinagh"


class Grading(StrEnum):
    auto = "auto"
    human = "human"
    auto_human = "auto+human"


class Split(StrEnum):
    public = "public"
    private = "private"


class Status(StrEnum):
    draft = "draft"  # en cours de saisie, exclu du benchmark
    ready = "ready"  # validé, utilisé par le benchmark


ID_PATTERN = r"^[a-z0-9][a-z0-9-]{1,63}$"
SEMVER_PATTERN = r"^\d+\.\d+\.\d+$"


def utcnow() -> datetime:
    # À la seconde près : c'est la précision des exports, un aller-retour ne change rien
    return datetime.now(UTC).replace(microsecond=0)


def nfc(value: Any) -> Any:
    """Normalise en Unicode NFC et retire les espaces en bord de chaîne.

    NFC ne change pas le texte visible : il unifie les deux encodages possibles
    d'un même caractère (ex. « ḥ » précomposé ou « h » + point souscrit).
    """
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value).strip()
    if isinstance(value, list):
        return [nfc(v) for v in value]
    return value


class BenchItemFields(SQLModel):
    category: Category
    subcategory: str | None = None
    script: Script = Script.latin
    prompt: str = Field(min_length=1)
    source_text: str | None = None
    context: str | None = None
    references: list[str] = Field(default_factory=list)
    grading: Grading = Grading.auto_human
    expected_lang: str = "kab"
    difficulty: int = Field(default=1, ge=1, le=3)
    split: Split = Split.public
    status: Status = Status.draft
    source: str = "author"
    author: str | None = None
    notes: str = ""

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = {key: nfc(value) for key, value in data.items()}
        if isinstance(data.get("references"), list):
            data["references"] = [ref for ref in data["references"] if ref]
        for key in ("subcategory", "source_text", "context", "author"):
            if data.get(key) == "":
                data[key] = None
        # Une traduction kabyle → français attend une réponse en français
        if data.get("category") == Category.translation_kab_fr and not data.get("expected_lang"):
            data["expected_lang"] = "fr"
        return data


def readiness_problems(item: BenchItemFields) -> list[str]:
    """Ce qui manque pour qu'un test puisse passer au statut « ready »."""
    problems = []
    if item.grading in (Grading.auto, Grading.auto_human) and not item.references:
        problems.append("au moins une référence est requise pour la notation automatique")
    if item.category in TRANSLATION_CATEGORIES and not item.source_text:
        problems.append("le texte source (source_text) est requis pour une traduction")
    if item.category == Category.comprehension and not item.context:
        problems.append("le texte de compréhension (context) est requis")
    return problems


class _ReadyCheck(BenchItemFields):
    @model_validator(mode="after")
    def _check_ready(self):
        if self.status == Status.ready and (problems := readiness_problems(self)):
            raise ValueError("test incomplet : " + " ; ".join(problems))
        return self


class BenchItemCreate(_ReadyCheck):
    id: str | None = None
    # Conservés lors d'un import, sinon fixés par le serveur
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("id")
    @classmethod
    def _check_id(cls, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(ID_PATTERN, value):
            raise ValueError("identifiant invalide : minuscules, chiffres et tirets uniquement")
        return value


class BenchItemUpdate(_ReadyCheck):
    pass


class BenchItemRead(BenchItemFields):
    id: str
    created_at: datetime
    updated_at: datetime


class BenchItem(BenchItemFields, table=True):
    __tablename__ = "test_items"

    id: str = Field(primary_key=True)
    references: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
