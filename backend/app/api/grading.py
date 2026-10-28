"""Notation humaine à l'aveugle.

L'interface reçoit une réponse tirée au hasard parmi celles non notées, identifiée par un
identifiant opaque : ni le modèle, ni le fournisseur, ni la variante, ni les scores
automatiques ne sont transmis (pour ne pas influencer la note). Le modèle n'est révélé
qu'après notation, sur demande.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlmodel import Session, select

from app.deps import SessionDep
from app.models import utcnow
from app.results import ERROR_TAGS
from app.run_models import (
    Favorite,
    FavoriteKind,
    Grade,
    ModelResponse,
    ResponseStatus,
    Run,
    RunItem,
)

router = APIRouter(prefix="/api", tags=["grading"])

BLIND_ITEM_FIELDS = (
    "id", "category", "script", "prompt", "source_text", "context", "references",
    "expected_lang", "grading",
)  # fmt: skip


class GradeIn(BaseModel):
    score: int = Field(ge=0, le=3)
    error_tags: list[str] = Field(default_factory=list)
    comment: str = ""


class FavoriteIn(BaseModel):
    kind: FavoriteKind
    note: str = ""


def _ungraded(run_id: int | None, category: str | None):
    stmt = (
        select(ModelResponse)
        .outerjoin(Grade, Grade.response_id == ModelResponse.id)
        .where(ModelResponse.status == ResponseStatus.ok, Grade.response_id.is_(None))  # type: ignore[union-attr]
    )
    if run_id:
        stmt = stmt.where(ModelResponse.run_id == run_id)
    if category:
        stmt = stmt.where(ModelResponse.category == category)
    return stmt


def _blind_view(session: Session, response: ModelResponse) -> dict:
    run_item = session.get(RunItem, (response.run_id, response.item_id))
    assert run_item is not None
    grade = session.get(Grade, response.id)
    return {
        "response_id": response.id,
        "item": {k: run_item.snapshot.get(k) for k in BLIND_ITEM_FIELDS},
        "output": response.output,
        "grade": grade.model_dump(mode="json") if grade else None,
    }


@router.get("/grading/tags")
def tags():
    return [{"id": k, "label": v} for k, v in ERROR_TAGS.items()]


@router.get("/grading/stats")
def stats(session: SessionDep, run_id: int | None = None):
    ok = (
        select(func.count())
        .select_from(ModelResponse)
        .where(ModelResponse.status == ResponseStatus.ok)
    )
    if run_id:
        ok = ok.where(ModelResponse.run_id == run_id)
    total = session.exec(ok).one()
    remaining = session.exec(
        select(func.count()).select_from(_ungraded(run_id, None).subquery())
    ).one()
    return {"total": total, "graded": total - remaining, "remaining": remaining}


@router.get("/grading/next")
def next_response(session: SessionDep, run_id: int | None = None, category: str | None = None):
    response = session.exec(_ungraded(run_id, category).order_by(func.random()).limit(1)).first()
    if response is None:
        return None
    return _blind_view(session, response)


@router.get("/grading/{response_id}")
def get_blind(response_id: str, session: SessionDep):
    response = session.get(ModelResponse, response_id)
    if response is None or response.status != ResponseStatus.ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "réponse introuvable")
    return _blind_view(session, response)


@router.put("/grading/{response_id}")
def grade(response_id: str, payload: GradeIn, session: SessionDep):
    if session.get(ModelResponse, response_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "réponse introuvable")
    unknown = set(payload.error_tags) - ERROR_TAGS.keys()
    if unknown:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, f"étiquettes inconnues : {unknown}"
        )
    existing = session.get(Grade, response_id)
    record = existing or Grade(response_id=response_id, score=payload.score)
    record.score = payload.score
    record.error_tags = payload.error_tags
    record.comment = payload.comment
    record.graded_at = utcnow()
    session.add(record)
    session.commit()
    return record.model_dump(mode="json")


@router.get("/grading/{response_id}/reveal")
def reveal(response_id: str, session: SessionDep):
    """Révèle le modèle, uniquement pour une réponse déjà notée."""
    response = session.get(ModelResponse, response_id)
    if response is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "réponse introuvable")
    if session.get(Grade, response_id) is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "notez d'abord la réponse")
    run = session.get(Run, response.run_id)
    info = run.model_snapshot.get(response.model_key, {}) if run else {}
    return {
        "model_key": response.model_key,
        "label": info.get("label", response.model_key),
        "chrf": response.chrf,
        "lang_ok": response.lang_ok,
        "detected_lang": response.detected_lang,
    }


@router.put("/favorites/{response_id}")
def set_favorite(response_id: str, payload: FavoriteIn, session: SessionDep):
    if session.get(ModelResponse, response_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "réponse introuvable")
    favorite = session.get(Favorite, response_id) or Favorite(
        response_id=response_id, kind=payload.kind
    )
    favorite.kind = payload.kind
    favorite.note = payload.note
    session.add(favorite)
    session.commit()
    return favorite.model_dump(mode="json")


@router.delete("/favorites/{response_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_favorite(response_id: str, session: SessionDep):
    if favorite := session.get(Favorite, response_id):
        session.delete(favorite)
        session.commit()
