"""Liste de préparation du labo : ce qui est prêt, ce qui reste à faire avant un benchmark.

Ne fait que lire l'état existant (base, fichiers, variables d'environnement, Ollama) ;
n'expose jamais la valeur d'une clé d'API, seulement sa présence.
"""

import json
from enum import StrEnum
from pathlib import Path
from typing import Any

import httpx
from sqlmodel import Session

from app.config import Settings
from app.contamination import protected_fingerprint
from app.models import CATEGORY_LABEL_FR, Category
from app.registry import ModelConfig, ProviderName
from app.testset import all_records, repo_paths, repo_status

RECOMMENDED_TESTS = 30
PRIVATE_SHARE = (0.10, 0.30)
DEFAULT_EMBED_MODEL = "bge-m3"
RUN = "docker compose run --rm api python -m"

API_KEYS = {
    ProviderName.anthropic: ("Anthropic (Claude)", "ANTHROPIC_API_KEY"),
    ProviderName.openai: ("OpenAI (GPT)", "OPENAI_API_KEY"),
    ProviderName.mistral: ("Mistral", "MISTRAL_API_KEY"),
    ProviderName.openrouter: ("OpenRouter", "OPENROUTER_API_KEY"),
}


class State(StrEnum):
    ok = "ok"
    todo = "todo"  # bloquant pour l'étape concernée
    warn = "warn"  # possible, mais à corriger avant de publier
    optional = "optional"


def _check(
    id: str, label: str, state: State, detail: str, hint: str = "", command: str = ""
) -> dict[str, str]:
    """`hint` : consigne en français ; `command` : commande(s) à copier, une par ligne."""
    return {
        "id": id,
        "label": label,
        "state": state,
        "detail": detail,
        "hint": hint,
        "command": command,
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def _read_json(path: Path) -> dict[str, Any] | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def ollama_models(base_url: str) -> set[str] | None:
    """Noms des modèles téléchargés dans Ollama, ou None si Ollama est injoignable."""
    try:
        response = httpx.get(f"{base_url.rstrip('/')}/api/tags", timeout=2)
        response.raise_for_status()
    except httpx.HTTPError:
        return None
    names = set()
    for model in response.json().get("models", []):
        name = model.get("name") or model.get("model") or ""
        names.add(name)
        names.add(name.removesuffix(":latest"))
    return names


def _test_set_checks(session: Session, settings: Settings) -> list[dict[str, str]]:
    status = repo_status(session, settings)
    ready = status["ready"]
    checks = []
    if ready >= RECOMMENDED_TESTS:
        checks.append(_check("tests", "Tests prêts", State.ok, f"{ready} tests prêts."))
    else:
        checks.append(
            _check(
                "tests",
                "Tests prêts",
                State.warn if ready else State.todo,
                f"{ready} test(s) prêt(s) ; au moins {RECOMMENDED_TESTS} sont conseillés "
                "pour des intervalles de confiance utiles.",
                "Onglet « Mode guidé ».",
            )
        )
    missing = [
        CATEGORY_LABEL_FR[c] for c in Category if status["by_category"][c.value]["ready"] == 0
    ]
    checks.append(
        _check(
            "categories",
            "Les six catégories sont couvertes",
            State.warn if missing else State.ok,
            f"Sans test prêt : {', '.join(missing)}."
            if missing
            else "Chaque catégorie a des tests.",
            "Onglet « Mode guidé », en choisissant la catégorie." if missing else "",
        )
    )
    if ready:
        private = sum(
            r["status"] == "ready" and r["split"] == "private" for r in all_records(session)
        )
        share = private / ready
        low, high = PRIVATE_SHARE
        checks.append(
            _check(
                "private",
                "Part de tests privés",
                State.ok if low <= share <= high else State.warn,
                f"{private} sur {ready} ({share:.0%}) ; environ 20 % visés.",
                "" if low <= share <= high else "Changer la visibilité de quelques tests.",
            )
        )
    checks.append(
        _check(
            "repo",
            "Jeu de test enregistré dans le dépôt",
            State.ok if status["repo_in_sync"] else State.todo,
            "Les fichiers du dépôt correspondent à la base."
            if status["repo_in_sync"]
            else "Des tests ne sont pas encore enregistrés dans les fichiers du dépôt.",
            "" if status["repo_in_sync"] else "Onglet Tests → « Enregistrer dans le dépôt ».",
        )
    )
    return checks


def _model_checks(
    settings: Settings, registry: dict[str, ModelConfig], pulled: set[str] | None
) -> list[dict[str, str]]:
    checks = []
    for provider, (name, env) in API_KEYS.items():
        models = [m for m in registry.values() if m.provider == provider]
        if not models:
            continue
        has_key = getattr(settings, f"{provider.value}_api_key") is not None
        checks.append(
            _check(
                f"key-{provider.value}",
                f"Clé {name}",
                State.ok if has_key else State.optional,
                f"{len(models)} modèle(s) configuré(s)."
                if has_key
                else f"Absente : ses {len(models)} modèle(s) seront ignorés.",
                "" if has_key else f"Ajouter {env}=… dans le fichier .env, puis redémarrer l'API.",
            )
        )
    local = sorted({m.model for m in registry.values() if m.provider == ProviderName.ollama})
    if not local:
        return checks
    if pulled is None:
        checks.append(
            _check(
                "ollama",
                "Ollama",
                State.optional,
                "Injoignable : les modèles locaux (phase 2) seront indisponibles.",
                "Installer et lancer Ollama (https://ollama.com), ou le lancer dans Docker :",
                "docker compose --profile ollama up -d ollama",
            )
        )
        return checks
    checks.append(_check("ollama", "Ollama", State.ok, "Joignable."))
    for model in local:
        ok = model in pulled
        checks.append(
            _check(
                f"ollama-{model}",
                f"Modèle local {model}",
                State.ok if ok else State.optional,
                "Téléchargé." if ok else "Pas encore téléchargé.",
                command="" if ok else f"ollama pull {model}",
            )
        )
    return checks


def _phase2_checks(
    settings: Settings, registry: dict[str, ModelConfig], pulled: set[str] | None
) -> list[dict[str, str]]:
    public_path, private_path, _ = repo_paths(settings)
    current = protected_fingerprint(_read_jsonl(public_path) + _read_jsonl(private_path))
    checks = []

    stats = _read_json(settings.train_dir / "STATS.json")
    prepared = stats is not None and (settings.train_dir / "fewshot_pool.jsonl").exists()
    if not prepared:
        checks.append(
            _check(
                "prepared",
                "Données d'amélioration préparées",
                State.todo,
                "Corpus non téléchargés ou non préparés.",
                command=f"{RUN} pipelines.download\n{RUN} pipelines.prepare",
            )
        )
    elif stats.get("protected_test_fingerprint") != current:
        checks.append(
            _check(
                "prepared",
                "Données d'amélioration à jour",
                State.todo,
                "Préparées avant l'ajout de ce contrôle : impossible de vérifier qu'elles "
                "excluent le jeu de test actuel."
                if "protected_test_fingerprint" not in stats
                else "Le jeu de test a changé depuis la dernière préparation : les nouveaux "
                "tests ne sont pas encore retirés des données d'amélioration.",
                command=f"{RUN} pipelines.prepare",
            )
        )
    else:
        pairs = stats.get("pairs", {}).get("kept")
        checks.append(
            _check(
                "prepared",
                "Données d'amélioration à jour",
                State.ok,
                f"{pairs} paires décontaminées, préparées après la dernière modification "
                "du jeu de test.",
            )
        )

    uses_rag = any(m.variant == "rag" for m in registry.values())
    if uses_rag:
        meta = _read_json(settings.train_dir / "rag_index" / "meta.json")
        embed = (meta or {}).get("embed_model", DEFAULT_EMBED_MODEL)
        if meta is None:
            state, detail, hint = (
                State.todo,
                "Index absent.",
                f"ollama pull {embed}\n{RUN} pipelines.build_rag_index --limit 20000",
            )
        elif meta.get("protected_test_fingerprint") != current:
            state, detail, hint = (
                State.todo,
                "Index construit avant la dernière modification du jeu de test.",
                f"{RUN} pipelines.build_rag_index",
            )
        else:
            state, detail, hint = State.ok, f"{meta['entries']} entrées ({embed}).", ""
        checks.append(_check("rag", "Index RAG", state, detail, command=hint))
        if pulled is not None:
            ok = embed in pulled
            checks.append(
                _check(
                    "embed",
                    f"Modèle d'embedding {embed}",
                    State.ok if ok else State.todo,
                    "Téléchargé." if ok else "Nécessaire pour la variante RAG.",
                    command="" if ok else f"ollama pull {embed}",
                )
            )
    return checks


def setup_status(
    session: Session, settings: Settings, registry: dict[str, ModelConfig]
) -> dict[str, Any]:
    pulled = ollama_models(settings.ollama_base_url)
    groups = [
        {"id": "testset", "title": "Jeu de test", "checks": _test_set_checks(session, settings)},
        {"id": "models", "title": "Modèles", "checks": _model_checks(settings, registry, pulled)},
        {
            "id": "phase2",
            "title": "Phase 2 : amélioration du petit modèle",
            "checks": _phase2_checks(settings, registry, pulled),
        },
    ]
    api_ready = any(
        c["state"] == State.ok for c in groups[1]["checks"] if c["id"].startswith("key-")
    )
    return {"groups": groups, "can_run_api_benchmark": api_ready}
