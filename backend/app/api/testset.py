"""Jeu de tests dans son ensemble : état, import/export, synchronisation avec le dépôt."""

import json
from datetime import UTC, datetime
from enum import StrEnum

from fastapi import APIRouter, HTTPException, Response, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.deps import SessionDep, SettingsDep
from app.models import CATEGORY_LABEL_FR, SEMVER_PATTERN
from app.testset import (
    ImportReport,
    ParseError,
    all_records,
    benchmark_hash,
    import_records,
    load_from_repo,
    parse_upload,
    repo_status,
    save_to_repo,
    to_csv,
    to_jsonl,
)

router = APIRouter(prefix="/api/testset", tags=["testset"])


class ExportFormat(StrEnum):
    jsonl = "jsonl"
    json = "json"
    csv = "csv"


class SplitFilter(StrEnum):
    all = "all"
    public = "public"
    private = "private"


class SaveRequest(BaseModel):
    version: str | None = Field(default=None, pattern=SEMVER_PATTERN)


def _report_response(report: ImportReport) -> JSONResponse:
    # 422 si au moins une ligne est invalide : dans ce cas rien n'a été écrit
    code = 422 if report.errors else status.HTTP_200_OK
    return JSONResponse(status_code=code, content=report.__dict__)


@router.get("/categories")
def categories():
    return [{"id": c.value, "label": label} for c, label in CATEGORY_LABEL_FR.items()]


@router.get("/status")
def get_status(session: SessionDep, settings: SettingsDep):
    return repo_status(session, settings)


@router.get("/export")
def export(
    session: SessionDep,
    format: ExportFormat = ExportFormat.jsonl,
    split: SplitFilter = SplitFilter.all,
):
    records = [r for r in all_records(session) if split == SplitFilter.all or r["split"] == split]
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    filename = f"kab-bench-{split.value}-{stamp}.{format.value}"
    if format == ExportFormat.jsonl:
        body, media = to_jsonl(records).encode("utf-8"), "application/x-ndjson"
    elif format == ExportFormat.json:
        payload = {
            "exported_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
            "content_hash": benchmark_hash(records),
            "items": records,
        }
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        media = "application/json"
    else:
        # BOM UTF-8 pour qu'Excel affiche correctement ɛ, ɣ, ḥ, tifinagh…
        body, media = to_csv(records).encode("utf-8-sig"), "text/csv"
    return Response(
        content=body,
        media_type=f"{media}; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import")
async def import_file(file: UploadFile, session: SessionDep):
    try:
        raw = parse_upload(file.filename or "", await file.read())
    except ParseError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return _report_response(import_records(session, raw))


@router.post("/save-to-repo")
def save(session: SessionDep, settings: SettingsDep, body: SaveRequest | None = None):
    return save_to_repo(session, settings, body.version if body else None)


@router.post("/load-from-repo")
def load(session: SessionDep, settings: SettingsDep):
    try:
        report = load_from_repo(session, settings)
    except FileNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except ParseError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return _report_response(report)
