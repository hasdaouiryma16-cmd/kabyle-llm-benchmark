"""Export des résultats vers le site public (data/results/public/results.json).

Liste blanche explicite : seuls les champs ci-dessous sont publiés. Aucune clé, aucun
paramètre de configuration locale, aucun texte de la partie privée du jeu de test
(les tests privés ne contribuent qu'aux scores agrégés).
"""

import json
from typing import Any

from sqlmodel import Session

from app.config import Settings
from app.models import CATEGORY_LABEL_FR, Category, utcnow
from app.results import ERROR_TAGS, compute_results, response_rows
from app.testset import read_manifest

CATEGORY_LABEL_EN = {
    Category.translation_fr_kab: "Translation French → Kabyle",
    Category.translation_kab_fr: "Translation Kabyle → French",
    Category.comprehension: "Comprehension",
    Category.culture: "Culture",
    Category.writing: "Writing",
    Category.conversation: "Conversation",
}

ERROR_TAGS_EN = {
    "wrong_language": "Wrong language (French, English…)",
    "arabic": "Confusion with Arabic",
    "other_berber": "Confusion with another Berber language",
    "invented_words": "Invented words",
    "spelling": "Spelling / transcription",
    "grammar": "Grammar / conjugation",
    "meaning": "Wrong meaning",
    "literal": "Overly literal translation",
    "incomplete": "Incomplete answer",
    "script": "Wrong script (Latin / Tifinagh)",
    "refusal": "Refusal or no answer",
}

PUBLIC_ITEM_FIELDS = ("id", "category", "script", "prompt", "source_text", "context", "references")


def build_public_results(session: Session, settings: Settings) -> dict[str, Any]:
    results = compute_results(session)
    manifest = read_manifest(settings) or {}
    examples = []
    for row in response_rows(session, results["test_set_hash"], favorites_only=True):
        item = row["item"]
        if item.get("split") != "public":
            continue
        examples.append(
            {
                "kind": row["favorite"]["kind"],
                "note": row["favorite"]["note"],
                "model": row["model_label"],
                "model_key": row["model_key"],
                "item": {k: item.get(k) for k in PUBLIC_ITEM_FIELDS},
                "output": row["output"],
                "score": row["score"],
                "error_tags": row["error_tags"],
                "chrf": row["chrf"],
            }
        )
    return {
        "schema_version": 1,
        "generated_at": utcnow().isoformat(),
        "test_set": {
            "name": manifest.get("name"),
            "version": manifest.get("version"),
            "content_hash": results["test_set_hash"],
            "manifest_benchmark_hash": manifest.get("benchmark", {}).get("content_hash"),
            "items": manifest.get("benchmark", {}).get("items"),
            "public_items": manifest.get("public", {}).get("ready"),
            "private_items": manifest.get("private", {}).get("ready"),
            "canary": manifest.get("canary"),
        },
        "categories": [
            {"id": c.value, "label_fr": CATEGORY_LABEL_FR[c], "label_en": CATEGORY_LABEL_EN[c]}
            for c in Category
        ],
        "error_tags": [
            {"id": k, "label_fr": v, "label_en": ERROR_TAGS_EN[k]} for k, v in ERROR_TAGS.items()
        ],
        "models": [
            {
                k: m[k]
                for k in (
                    "key",
                    "label",
                    "provider",
                    "model",
                    "variant",
                    "base",
                    "overall",
                    "by_category",
                    "error_tags",
                )
            }  # fmt: skip
            for m in results["models"]
        ],
        "gains": results["gains"],
        "examples": examples,
    }


def write_public_results(session: Session, settings: Settings) -> dict[str, Any]:
    data = build_public_results(session, settings)
    settings.results_dir.mkdir(parents=True, exist_ok=True)
    path = settings.results_dir / "results.json"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return {
        "path": str(path),
        "models": len(data["models"]),
        "examples": len(data["examples"]),
        "test_set_hash": data["test_set"]["content_hash"],
    }
