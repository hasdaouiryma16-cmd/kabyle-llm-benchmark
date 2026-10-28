"""Résultats agrégés, exploration des réponses et export vers le site public."""

from fastapi import APIRouter
from sqlalchemy import func
from sqlmodel import select

from app.deps import SessionDep, SettingsDep
from app.export_public import write_public_results
from app.results import compute_results, response_rows
from app.run_models import Run

router = APIRouter(prefix="/api/results", tags=["results"])


@router.get("")
def results(session: SessionDep, test_set_hash: str | None = None, split: str | None = None):
    return compute_results(session, test_set_hash, split)


@router.get("/test-sets")
def test_sets(session: SessionDep):
    """Empreintes de jeu de test pour lesquelles des runs existent (les plus récentes d'abord)."""
    rows = session.exec(
        select(Run.test_set_hash, Run.test_set_version, func.count(), func.max(Run.created_at))
        .group_by(Run.test_set_hash, Run.test_set_version)
        .order_by(func.max(Run.created_at).desc())
    ).all()
    return [
        {"test_set_hash": h, "version": v, "runs": n, "last_run": str(last)}
        for h, v, n, last in rows
    ]


@router.get("/responses")
def responses(
    session: SessionDep,
    test_set_hash: str | None = None,
    model_key: str | None = None,
    category: str | None = None,
    favorites_only: bool = False,
    graded_only: bool = False,
):
    return response_rows(session, test_set_hash, model_key, category, favorites_only, graded_only)


@router.post("/export-public")
def export_public(session: SessionDep, settings: SettingsDep):
    return write_public_results(session, settings)
