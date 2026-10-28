"""Tables des exécutions de benchmark, des réponses des modèles et des notations.

Contrairement aux tests (reconstructibles depuis le dépôt), ces données sont uniques :
la base doit être sauvegardée (voir docs/lab.md).
"""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models import utcnow


class RunStatus(StrEnum):
    pending = "pending"
    running = "running"
    completed = "completed"  # toutes les réponses sont arrivées (certaines peuvent être en erreur)
    cancelled = "cancelled"
    interrupted = "interrupted"  # serveur arrêté pendant l'exécution : reprise possible
    stopped_cost = "stopped_cost"  # plafond de coût atteint


class ResponseStatus(StrEnum):
    pending = "pending"
    ok = "ok"
    error = "error"


class FavoriteKind(StrEnum):
    success = "success"  # réponse réussie, à montrer
    error = "error"  # erreur révélatrice


def new_response_id() -> str:
    # Identifiant opaque : ne révèle pas le modèle pendant la notation à l'aveugle
    return uuid.uuid4().hex


class Run(SQLModel, table=True):
    __tablename__ = "runs"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    status: RunStatus = RunStatus.pending
    created_at: datetime = Field(default_factory=utcnow)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    test_set_hash: str = Field(index=True)
    test_set_version: str | None = None
    model_keys: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    # Configuration exacte de chaque modèle au moment du run (paramètres, variante, prix)
    model_snapshot: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False)
    )
    categories: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    sample_per_category: int | None = None
    seed: int = 0
    cost_usd: float = 0.0
    notes: str = ""


class RunItem(SQLModel, table=True):
    """Copie figée d'un test au moment du run : un test modifié plus tard ne change pas
    l'interprétation des réponses déjà obtenues."""

    __tablename__ = "run_items"

    run_id: int = Field(foreign_key="runs.id", primary_key=True)
    item_id: str = Field(primary_key=True)
    category: str = Field(index=True)
    snapshot: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))


class ModelResponse(SQLModel, table=True):
    __tablename__ = "responses"
    __table_args__ = (UniqueConstraint("run_id", "item_id", "model_key"),)

    id: str = Field(default_factory=new_response_id, primary_key=True)
    run_id: int = Field(foreign_key="runs.id", index=True)
    item_id: str = Field(index=True)
    category: str = Field(index=True)
    model_key: str = Field(index=True)
    status: ResponseStatus = Field(default=ResponseStatus.pending, index=True)
    attempts: int = 0
    request: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    output: str | None = None
    stop_reason: str | None = None
    error: str | None = None
    latency_ms: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    created_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None
    # Notation automatique
    chrf: float | None = None
    bleu: float | None = None
    script: str | None = None
    detected_lang: str | None = None
    lang_confidence: float | None = None
    lang_ok: bool | None = None


class Grade(SQLModel, table=True):
    __tablename__ = "grades"

    response_id: str = Field(foreign_key="responses.id", primary_key=True)
    score: int = Field(ge=0, le=3)
    error_tags: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    comment: str = ""
    graded_at: datetime = Field(default_factory=utcnow)


class Favorite(SQLModel, table=True):
    __tablename__ = "favorites"

    response_id: str = Field(foreign_key="responses.id", primary_key=True)
    kind: FavoriteKind
    note: str = ""
    created_at: datetime = Field(default_factory=utcnow)
