"""Mode guidé : consignes en français proposées une à une (data/prompts/guided_fr.yaml)."""

from typing import Any

import yaml
from fastapi import APIRouter, HTTPException, status
from sqlmodel import col, select

from app.deps import SessionDep, SettingsDep
from app.models import BenchItem

router = APIRouter(prefix="/api/guided", tags=["guided"])

SOURCE_PREFIX = "guided:"


def load_guided(path) -> list[dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    fr_kab = data.get("defaults", {}).get("fr_kab", "{text}")
    entries = []
    for raw in data.get("prompts", []):
        entry = {
            "id": raw["id"],
            "theme": raw.get("theme"),
            "category": raw["category"],
            "guide": raw.get("guide"),
            "fill": raw.get("fill", ["references"]),
            "prompt_template": raw.get("prompt_template"),
            "item": raw.get("item", {}),
            "source_text": None,
            "prompt": raw.get("prompt"),
        }
        if "text" in raw:  # traduction français → kabyle : consigne entièrement fournie
            entry["source_text"] = raw["text"]
            entry["prompt"] = fr_kab.format(text=raw["text"])
            entry["guide"] = entry["guide"] or "Écris la traduction kabyle de référence."
        entries.append(entry)
    return entries


@router.get("")
def guided(session: SessionDep, settings: SettingsDep):
    if not settings.prompts_file.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "fichier de consignes introuvable")
    used = {
        source.removeprefix(SOURCE_PREFIX): item_id
        for item_id, source in session.exec(
            select(BenchItem.id, BenchItem.source).where(
                col(BenchItem.source).startswith(SOURCE_PREFIX)
            )
        ).all()
    }
    return [
        {**entry, "used_by": used.get(entry["id"])} for entry in load_guided(settings.prompts_file)
    ]
