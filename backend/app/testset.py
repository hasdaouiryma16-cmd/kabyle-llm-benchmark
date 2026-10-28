"""Services du jeu de tests : sérialisation, import, empreinte, synchronisation avec le dépôt.

Le fichier JSONL versionné dans Git est la source de vérité ; la base SQLite est la copie
de travail du labo et peut toujours être reconstruite depuis le dépôt.
"""

import csv
import hashlib
import io
import json
import re
import uuid
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from sqlmodel import Session, select

from app.config import Settings
from app.models import CATEGORY_PREFIX, BenchItem, BenchItemCreate, Category, Split, utcnow

FIELD_ORDER = [
    "id", "category", "subcategory", "script", "prompt", "source_text", "context",
    "references", "grading", "expected_lang", "difficulty", "split", "status",
    "source", "author", "notes", "created_at", "updated_at",
]  # fmt: skip

# Champs qui définissent ce qui est réellement évalué : l'empreinte du benchmark ne change
# que si l'un d'eux change (une note ou une date modifiée ne change pas le benchmark).
HASHED_FIELDS = [
    "id", "category", "script", "prompt", "source_text", "context",
    "references", "grading", "expected_lang",
]  # fmt: skip

CANARY_TEMPLATE = (
    "KAB-BENCH CANARY GUID {guid}. "
    "Ce jeu de test ne doit pas apparaître dans des données d'entraînement. "
    "This test set must not appear in training data."
)


# ── Sérialisation ────────────────────────────────────────────


def item_to_record(item: BenchItem) -> dict[str, Any]:
    record: dict[str, Any] = {}
    for name in FIELD_ORDER:
        value = getattr(item, name)
        if isinstance(value, Enum):
            value = value.value
        elif isinstance(value, datetime):
            if value.tzinfo is None:  # SQLite ne conserve pas le fuseau : on stocke en UTC
                value = value.replace(tzinfo=UTC)
            value = value.replace(microsecond=0).isoformat()
        record[name] = value
    return record


def to_jsonl(records: Iterable[dict[str, Any]]) -> str:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)


def to_csv(records: Iterable[dict[str, Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=FIELD_ORDER)
    writer.writeheader()
    for record in records:
        writer.writerow(
            {**record, "references": json.dumps(record["references"], ensure_ascii=False)}
        )
    return buffer.getvalue()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def benchmark_hash(records: Iterable[dict[str, Any]]) -> str:
    """Empreinte des tests « ready », indépendante de l'ordre et des métadonnées."""
    ready = sorted((r for r in records if r["status"] == "ready"), key=lambda r: r["id"])
    lines = [
        json.dumps({k: r[k] for k in HASHED_FIELDS}, ensure_ascii=False, sort_keys=True)
        for r in ready
    ]
    return sha256_text("\n".join(lines))


# ── Lecture de fichiers importés ─────────────────────────────


class ParseError(ValueError):
    pass


def parse_upload(filename: str, content: bytes) -> list[Any]:
    try:
        text = content.decode("utf-8-sig")  # accepte le BOM ajouté par Excel
    except UnicodeDecodeError as exc:
        raise ParseError("le fichier doit être encodé en UTF-8") from exc

    suffix = Path(filename).suffix.lower()
    if suffix == ".jsonl":
        return _parse_jsonl(text)
    if suffix == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ParseError(f"JSON invalide : {exc}") from exc
        if isinstance(data, dict) and "items" in data:
            data = data["items"]
        if not isinstance(data, list):
            raise ParseError('le JSON doit être une liste de tests ou un objet {"items": [...]}')
        return data
    if suffix == ".csv":
        return [_csv_row(row) for row in csv.DictReader(io.StringIO(text))]
    raise ParseError("format non pris en charge (attendu : .json, .jsonl ou .csv)")


def _parse_jsonl(text: str) -> list[Any]:
    records = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ParseError(f"ligne {number} : JSON invalide ({exc.msg})") from exc
    return records


def _csv_row(row: dict[str | None, str]) -> dict[str, Any]:
    record: dict[str, Any] = {k: v for k, v in row.items() if k is not None and v != ""}
    refs = record.get("references")
    if refs is not None:
        try:
            record["references"] = json.loads(refs) if refs.lstrip().startswith("[") else [refs]
        except json.JSONDecodeError:
            record["references"] = [refs]
    return record


# ── Import en base ───────────────────────────────────────────


@dataclass
class ImportReport:
    created: int = 0
    updated: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)


def make_id_allocator(session: Session, reserved: set[str]) -> Callable[[Category], str]:
    used = set(session.exec(select(BenchItem.id)).all()) | reserved

    def allocate(category: Category) -> str:
        prefix = CATEGORY_PREFIX[category]
        pattern = re.compile(rf"{re.escape(prefix)}-(\d+)")
        numbers = (int(m.group(1)) for i in used if (m := pattern.fullmatch(i)))
        new_id = f"{prefix}-{max(numbers, default=0) + 1:04d}"
        used.add(new_id)
        return new_id

    return allocate


def _format_errors(exc: ValidationError) -> list[str]:
    messages = []
    for err in exc.errors():
        location = ".".join(str(part) for part in err["loc"])
        messages.append(f"{location} : {err['msg']}" if location else err["msg"])
    return messages


def import_records(
    session: Session, raw_records: list[Any], force_split: list[Split | None] | None = None
) -> ImportReport:
    """Importe (crée ou met à jour) des tests. Tout ou rien : si une ligne est invalide,
    rien n'est écrit et le rapport liste les erreurs."""
    report = ImportReport()
    valid: list[BenchItemCreate] = []
    seen: set[str] = set()

    for index, raw in enumerate(raw_records):
        row = index + 1
        if not isinstance(raw, dict):
            report.errors.append({"row": row, "id": None, "errors": ["un test doit être un objet"]})
            continue
        if force_split and force_split[index]:
            raw = {**raw, "split": force_split[index]}
        try:
            item = BenchItemCreate.model_validate(raw)
        except ValidationError as exc:
            report.errors.append({"row": row, "id": raw.get("id"), "errors": _format_errors(exc)})
            continue
        if item.id:
            if item.id in seen:
                report.errors.append(
                    {"row": row, "id": item.id, "errors": ["identifiant en double"]}
                )
                continue
            seen.add(item.id)
        valid.append(item)

    if report.errors:
        return report

    allocate = make_id_allocator(session, reserved=seen)
    now = utcnow()
    for item in valid:
        data = item.model_dump(exclude={"id", "created_at", "updated_at"})
        existing = session.get(BenchItem, item.id) if item.id else None
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            existing.updated_at = item.updated_at or now
            report.updated += 1
        else:
            session.add(
                BenchItem(
                    **data,
                    id=item.id or allocate(item.category),
                    created_at=item.created_at or now,
                    updated_at=item.updated_at or now,
                )
            )
            report.created += 1
    session.commit()
    return report


# ── Synchronisation avec le dépôt Git ────────────────────────


def all_records(session: Session) -> list[dict[str, Any]]:
    items = session.exec(select(BenchItem).order_by(BenchItem.id)).all()
    return [item_to_record(item) for item in items]


def repo_paths(settings: Settings) -> tuple[Path, Path, Path]:
    base = f"{settings.testset_name}.v{settings.testset_major}"
    directory = settings.testset_dir
    return (
        directory / f"{base}.jsonl",
        directory / "private" / f"{base}.private.jsonl",
        directory / "MANIFEST.json",
    )


def read_manifest(settings: Settings) -> dict[str, Any] | None:
    path = repo_paths(settings)[2]
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_category = {
        c.value: {
            "total": sum(r["category"] == c.value for r in records),
            "ready": sum(r["category"] == c.value and r["status"] == "ready" for r in records),
        }
        for c in Category
    }
    return {
        "items": len(records),
        "ready": sum(r["status"] == "ready" for r in records),
        "by_category": by_category,
        "by_split": dict(Counter(r["split"] for r in records)),
        "by_status": dict(Counter(r["status"] for r in records)),
    }


def save_to_repo(session: Session, settings: Settings, version: str | None) -> dict[str, Any]:
    records = all_records(session)
    public = [r for r in records if r["split"] == Split.public.value]
    private = [r for r in records if r["split"] == Split.private.value]
    public_path, private_path, manifest_path = repo_paths(settings)

    public_text, private_text = to_jsonl(public), to_jsonl(private)
    _write(public_path, public_text)
    if private or private_path.exists():
        _write(private_path, private_text)

    previous = read_manifest(settings) or {}
    manifest = {
        "name": settings.testset_name,
        "version": version or previous.get("version", f"{settings.testset_major}.0.0"),
        # La chaîne canari est générée une seule fois puis conservée
        "canary": previous.get("canary") or CANARY_TEMPLATE.format(guid=uuid.uuid4()),
        "license": "CC-BY-4.0",
        "generated_at": utcnow().replace(microsecond=0).isoformat(),
        "benchmark": {
            "items": sum(r["status"] == "ready" for r in records),
            "content_hash": benchmark_hash(records),
            "by_category": summarize(records)["by_category"],
        },
        "public": {
            "file": public_path.name,
            "items": len(public),
            "ready": sum(r["status"] == "ready" for r in public),
            "sha256": sha256_text(public_text),
            "content_hash": benchmark_hash(public),
        },
        # Seules des empreintes sont publiées : elles prouvent l'existence et la stabilité
        # de la partie privée sans en révéler le contenu.
        "private": {
            "items": len(private),
            "ready": sum(r["status"] == "ready" for r in private),
            "sha256": sha256_text(private_text),
            "content_hash": benchmark_hash(private),
        },
    }
    _write(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest


def repo_status(session: Session, settings: Settings) -> dict[str, Any]:
    records = all_records(session)
    manifest = read_manifest(settings)
    public = [r for r in records if r["split"] == Split.public.value]
    private = [r for r in records if r["split"] == Split.private.value]
    in_sync = bool(
        manifest
        and manifest["public"]["sha256"] == sha256_text(to_jsonl(public))
        and manifest["private"]["sha256"] == sha256_text(to_jsonl(private))
    )
    return {
        **summarize(records),
        "content_hash": benchmark_hash(records),
        "manifest": manifest,
        "repo_in_sync": in_sync,
    }


def load_from_repo(session: Session, settings: Settings) -> ImportReport:
    public_path, private_path, _ = repo_paths(settings)
    if not public_path.exists():
        raise FileNotFoundError(f"fichier introuvable : {public_path.name}")
    raw = _parse_jsonl(public_path.read_text(encoding="utf-8"))
    splits: list[Split | None] = [Split.public] * len(raw)
    if private_path.exists():
        private_raw = _parse_jsonl(private_path.read_text(encoding="utf-8"))
        raw += private_raw
        splits += [Split.private] * len(private_raw)
    return import_records(session, raw, force_split=splits)
