"""Modèles disponibles, lancement et suivi des runs."""

import asyncio
import json

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from app.deps import SessionDep
from app.run_models import ModelResponse, Run
from app.runner import FINISHED, RunManager, RunRequest

router = APIRouter(prefix="/api", tags=["runs"])


def _manager(request: Request) -> RunManager:
    return request.app.state.runner


def _get_run(session: Session, run_id: int) -> Run:
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"run {run_id} introuvable")
    return run


@router.get("/models")
def list_models(request: Request):
    manager = _manager(request)
    available = manager.availability()
    return [
        {
            **model.model_dump(mode="json", exclude={"params"}),
            "params": model.params,
            "available": available[key],
        }
        for key, model in manager.registry.items()
    ]


@router.post("/runs/estimate")
def estimate(payload: RunRequest, request: Request, session: SessionDep):
    try:
        return _manager(request).estimate(session, payload)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.post("/runs", status_code=status.HTTP_201_CREATED)
async def create_run(
    payload: RunRequest, request: Request, session: SessionDep, start: bool = True
):
    manager = _manager(request)
    try:
        run = manager.create_run(session, payload)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    if start:
        manager.start(run.id)
    return manager.progress(session, run.id) | {"name": run.name}


@router.get("/runs")
def list_runs(request: Request, session: SessionDep):
    manager = _manager(request)
    runs = session.exec(select(Run).order_by(Run.created_at.desc())).all()  # type: ignore[union-attr]
    return [
        {
            **run.model_dump(mode="json", exclude={"model_snapshot"}),
            "progress": manager.progress(session, run.id),
        }
        for run in runs
    ]


@router.get("/runs/{run_id}")
def get_run(run_id: int, request: Request, session: SessionDep):
    run = _get_run(session, run_id)
    return {
        **run.model_dump(mode="json"),
        "progress": _manager(request).progress(session, run_id),
    }


@router.post("/runs/{run_id}/resume")
async def resume(run_id: int, request: Request, session: SessionDep, retry_errors: bool = True):
    _get_run(session, run_id)
    try:
        _manager(request).start(run_id, retry_errors=retry_errors)
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return _manager(request).progress(session, run_id)


@router.post("/runs/{run_id}/cancel")
def cancel(run_id: int, request: Request, session: SessionDep):
    _get_run(session, run_id)
    _manager(request).cancel(run_id)
    return {"cancelled": True}


@router.get("/runs/{run_id}/responses")
def run_responses(run_id: int, session: SessionDep):
    _get_run(session, run_id)
    rows = session.exec(
        select(ModelResponse)
        .where(ModelResponse.run_id == run_id)
        .order_by(ModelResponse.item_id, ModelResponse.model_key)
    ).all()
    return [r.model_dump(mode="json", exclude={"request"}) for r in rows]


@router.get("/runs/{run_id}/events")
async def events(run_id: int, request: Request):
    """Progression en direct (Server-Sent Events), une mise à jour par seconde."""
    manager = _manager(request)
    engine = request.app.state.engine

    async def stream():
        while True:
            with Session(engine) as session:
                try:
                    progress = manager.progress(session, run_id)
                except KeyError:
                    yield 'event: error\ndata: "run introuvable"\n\n'
                    return
            yield f"data: {json.dumps(progress)}\n\n"
            if not progress["active"] and (
                progress["status"] in FINISHED or progress["pending"] == 0
            ):
                return
            if await request.is_disconnected():
                return
            await asyncio.sleep(1)

    return StreamingResponse(stream(), media_type="text/event-stream")
