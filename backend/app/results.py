"""Agrégation des résultats.

Règles :
- On ne compare que des réponses obtenues sur le même jeu de test (même empreinte).
- Pour chaque (modèle, test), seule la réponse la plus récente est retenue.
- Score humain : moyenne des notes 0–3, exprimée aussi en % (note / 3 × 100), avec un
  intervalle de confiance à 95 % par bootstrap (rééchantillonnage des tests).
- Gain d'une variante : calculé uniquement sur les tests notés pour la variante ET pour son
  modèle de base (comparaison appariée), en points de % et en % relatif.
"""

import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from statistics import mean
from typing import Any

from sqlmodel import Session, select

from app.models import CATEGORY_LABEL_FR, Category
from app.run_models import Favorite, Grade, ModelResponse, ResponseStatus, Run, RunItem

BOOTSTRAP_SAMPLES = 1000

ERROR_TAGS: dict[str, str] = {
    "wrong_language": "Mauvaise langue (français, anglais…)",
    "arabic": "Confusion avec l'arabe",
    "other_berber": "Confusion avec une autre langue berbère",
    "invented_words": "Mots inventés",
    "spelling": "Orthographe / transcription",
    "grammar": "Grammaire / conjugaison",
    "meaning": "Contresens / sens erroné",
    "literal": "Traduction trop littérale",
    "incomplete": "Réponse incomplète",
    "script": "Mauvaise écriture (latin / tifinagh)",
    "refusal": "Refus ou non-réponse",
}


@dataclass
class Row:
    response: ModelResponse
    snapshot: dict[str, Any]
    grade: Grade | None


def latest_hash(session: Session) -> str | None:
    run = session.exec(select(Run).order_by(Run.created_at.desc())).first()  # type: ignore[union-attr]
    return run.test_set_hash if run else None


def load_rows(
    session: Session, test_set_hash: str, split: str | None = None
) -> tuple[list[Row], dict[str, dict[str, Any]]]:
    runs = session.exec(select(Run).where(Run.test_set_hash == test_set_hash)).all()
    run_ids = [r.id for r in runs]
    models: dict[str, dict[str, Any]] = {}
    for run in sorted(runs, key=lambda r: r.created_at):
        models.update(run.model_snapshot)  # la configuration la plus récente l'emporte
    if not run_ids:
        return [], models
    snapshots = {
        (ri.run_id, ri.item_id): ri.snapshot
        for ri in session.exec(select(RunItem).where(RunItem.run_id.in_(run_ids))).all()  # type: ignore[attr-defined]
    }
    responses = session.exec(
        select(ModelResponse).where(
            ModelResponse.run_id.in_(run_ids),  # type: ignore[attr-defined]
            ModelResponse.status == ResponseStatus.ok,
        )
    ).all()
    latest: dict[tuple[str, str], ModelResponse] = {}
    for response in responses:
        key = (response.model_key, response.item_id)
        current = latest.get(key)
        if current is None or (response.completed_at or response.created_at) > (
            current.completed_at or current.created_at
        ):
            latest[key] = response
    grades = {
        g.response_id: g
        for g in session.exec(
            select(Grade).where(Grade.response_id.in_([r.id for r in latest.values()]))  # type: ignore[attr-defined]
        ).all()
    }
    rows = []
    for response in latest.values():
        snapshot = snapshots[(response.run_id, response.item_id)]
        if split and snapshot.get("split") != split:
            continue
        rows.append(Row(response, snapshot, grades.get(response.id)))
    return rows, models


def bootstrap_ci(values: list[float], seed: int = 0) -> tuple[float, float] | None:
    if len(values) < 2:
        return None
    rng = random.Random(seed)
    n = len(values)
    means = sorted(mean(rng.choices(values, k=n)) for _ in range(BOOTSTRAP_SAMPLES))
    return means[int(0.025 * BOOTSTRAP_SAMPLES)], means[int(0.975 * BOOTSTRAP_SAMPLES) - 1]


def _r(value: float | None, digits: int = 1) -> float | None:
    return None if value is None else round(value, digits)


def summarize_rows(rows: list[Row]) -> dict[str, Any]:
    scores = [r.grade.score for r in rows if r.grade]
    pct = [s / 3 * 100 for s in scores]
    chrfs = [r.response.chrf for r in rows if r.response.chrf is not None]
    lang = [r.response.lang_ok for r in rows if r.response.lang_ok is not None]
    ci = bootstrap_ci(pct)
    return {
        "n": len(rows),
        "n_graded": len(scores),
        "human_mean": _r(mean(scores), 2) if scores else None,
        "human_pct": _r(mean(pct)) if pct else None,
        "human_pct_ci95": [_r(ci[0]), _r(ci[1])] if ci else None,
        "score_distribution": {str(s): scores.count(s) for s in range(4)},
        "chrf": _r(mean(chrfs)) if chrfs else None,
        "n_chrf": len(chrfs),
        "lang_ok_rate": _r(100 * sum(lang) / len(lang)) if lang else None,
        "n_lang_checked": len(lang),
    }


def _paired_gain(variant: list[Row], base: list[Row]) -> dict[str, Any]:
    base_scores = {r.response.item_id: r.grade.score for r in base if r.grade}
    pairs = [
        (base_scores[r.response.item_id], r.grade.score)
        for r in variant
        if r.grade and r.response.item_id in base_scores
    ]
    base_chrf = {r.response.item_id: r.response.chrf for r in base if r.response.chrf is not None}
    chrf_pairs = [
        (base_chrf[r.response.item_id], r.response.chrf)
        for r in variant
        if r.response.chrf is not None and r.response.item_id in base_chrf
    ]
    out: dict[str, Any] = {"n_paired": len(pairs), "n_paired_chrf": len(chrf_pairs)}
    if pairs:
        before = mean(b for b, _ in pairs) / 3 * 100
        after = mean(a for _, a in pairs) / 3 * 100
        deltas = [(a - b) / 3 * 100 for b, a in pairs]
        ci = bootstrap_ci(deltas)
        out.update(
            before_pct=_r(before),
            after_pct=_r(after),
            gain_points=_r(after - before),
            gain_relative_pct=_r((after - before) / before * 100) if before else None,
            gain_points_ci95=[_r(ci[0]), _r(ci[1])] if ci else None,
        )
    if chrf_pairs:
        before_c = mean(b for b, _ in chrf_pairs)
        after_c = mean(a for _, a in chrf_pairs)
        out.update(
            chrf_before=_r(before_c), chrf_after=_r(after_c), chrf_gain=_r(after_c - before_c)
        )
    return out


def compute_results(
    session: Session, test_set_hash: str | None = None, split: str | None = None
) -> dict[str, Any]:
    test_set_hash = test_set_hash or latest_hash(session)
    if not test_set_hash:
        return {"test_set_hash": None, "models": [], "gains": [], "categories": []}
    rows, model_info = load_rows(session, test_set_hash, split)
    by_model: dict[str, list[Row]] = defaultdict(list)
    for row in rows:
        by_model[row.response.model_key].append(row)

    models = []
    for key, model_rows in by_model.items():
        info = model_info.get(key, {})
        by_cat: dict[str, list[Row]] = defaultdict(list)
        for row in model_rows:
            by_cat[row.snapshot["category"]].append(row)
        tags = Counter(tag for r in model_rows if r.grade for tag in r.grade.error_tags)
        models.append(
            {
                "key": key,
                "label": info.get("label", key),
                "provider": info.get("provider"),
                "model": info.get("model"),
                "variant": info.get("variant", "base"),
                "base": info.get("base"),
                "overall": summarize_rows(model_rows),
                "by_category": {c: summarize_rows(rs) for c, rs in sorted(by_cat.items())},
                "error_tags": dict(tags.most_common()),
            }
        )
    models.sort(
        key=lambda m: (m["overall"]["human_pct"] is None, -(m["overall"]["human_pct"] or 0))
    )

    gains = []
    for model in models:
        base_key = model["base"]
        if not base_key or base_key not in by_model:
            continue
        variant_rows, base_rows = by_model[model["key"]], by_model[base_key]
        per_category = {}
        for category in Category:
            v = [r for r in variant_rows if r.snapshot["category"] == category.value]
            b = [r for r in base_rows if r.snapshot["category"] == category.value]
            if v and b:
                per_category[category.value] = _paired_gain(v, b)
        gains.append(
            {
                "variant": model["key"],
                "variant_label": model["label"],
                "variant_type": model["variant"],
                "base": base_key,
                "overall": _paired_gain(variant_rows, base_rows),
                "by_category": per_category,
            }
        )

    return {
        "test_set_hash": test_set_hash,
        "split": split or "all",
        "categories": [{"id": c.value, "label": CATEGORY_LABEL_FR[c]} for c in Category],
        "error_tags": ERROR_TAGS,
        "models": models,
        "gains": gains,
    }


def response_rows(
    session: Session,
    test_set_hash: str | None = None,
    model_key: str | None = None,
    category: str | None = None,
    favorites_only: bool = False,
    graded_only: bool = False,
) -> list[dict[str, Any]]:
    test_set_hash = test_set_hash or latest_hash(session)
    if not test_set_hash:
        return []
    rows, model_info = load_rows(session, test_set_hash)
    favorites = {f.response_id: f for f in session.exec(select(Favorite)).all()}
    out = []
    for row in rows:
        r = row.response
        if model_key and r.model_key != model_key:
            continue
        if category and row.snapshot["category"] != category:
            continue
        if favorites_only and r.id not in favorites:
            continue
        if graded_only and not row.grade:
            continue
        fav = favorites.get(r.id)
        out.append(
            {
                "response_id": r.id,
                "model_key": r.model_key,
                "model_label": model_info.get(r.model_key, {}).get("label", r.model_key),
                "item": row.snapshot,
                "output": r.output,
                "chrf": r.chrf,
                "lang_ok": r.lang_ok,
                "detected_lang": r.detected_lang,
                "script": r.script,
                "score": row.grade.score if row.grade else None,
                "error_tags": row.grade.error_tags if row.grade else [],
                "comment": row.grade.comment if row.grade else "",
                "favorite": {"kind": fav.kind, "note": fav.note} if fav else None,
            }
        )
    out.sort(key=lambda x: (x["item"]["id"], x["model_key"]))
    return out
