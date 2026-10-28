"""Exécution des benchmarks.

Principes :
- Idempotence : chaque (run, test, modèle) est une ligne créée d'avance au statut « pending ».
  Relancer un run ne traite que les lignes en attente (et, sur demande, en erreur) :
  une interruption ne fait jamais repayer les réponses déjà obtenues.
- Même politique pour tous les fournisseurs : nouvelles tentatives avec attente exponentielle
  + aléa (ou délai « retry-after » indiqué par l'API), concurrence plafonnée par fournisseur.
- Plafond de coût par run : au-delà, les appels restants ne sont pas envoyés.
"""

import asyncio
import random
from collections import Counter, defaultdict
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.config import Settings
from app.contamination import ContaminationIndex, protected_strings
from app.models import BenchItem, Category, Split, Status, utcnow
from app.providers import Provider, ProviderError
from app.registry import ModelConfig, ProviderName
from app.run_models import ModelResponse, ResponseStatus, Run, RunItem, RunStatus
from app.scoring import (
    LanguageDetector,
    bleu,
    chrf,
    clean_output,
    detect_script,
    language_ok,
)
from app.testset import all_records, benchmark_hash, item_to_record, read_manifest
from app.variants import ContaminationError, PromptBuilder

FINISHED = {RunStatus.completed, RunStatus.cancelled, RunStatus.stopped_cost}
# Estimation grossière, volontairement prudente (le kabyle est mal découpé par les tokenizers)
CHARS_PER_TOKEN = 2.5
ESTIMATED_OUTPUT_TOKENS = 300


class RunRequest(BaseModel):
    name: str = Field(min_length=1)
    model_keys: list[str] = Field(min_length=1)
    categories: list[Category] = Field(default_factory=lambda: list(Category))
    split: Split | None = None  # None = public + privé
    sample_per_category: int | None = Field(default=None, ge=1)  # mode test : quelques questions
    seed: int = 0
    notes: str = ""


def score_response(snapshot: dict[str, Any], output: str, detector: LanguageDetector) -> dict:
    text = clean_output(output)
    refs = snapshot.get("references") or []
    auto = snapshot.get("grading") in ("auto", "auto+human") and refs
    script = detect_script(text)
    guess = detector.detect(text)
    return {
        "chrf": chrf(text, refs) if auto else None,
        "bleu": bleu(text, refs) if auto else None,
        "script": script,
        "detected_lang": guess.lang,
        "lang_confidence": guess.confidence,
        "lang_ok": language_ok(
            snapshot.get("expected_lang", "kab"), guess, script, snapshot.get("script", "latin")
        ),
    }


def select_items(session: Session, request: RunRequest) -> list[BenchItem]:
    stmt = select(BenchItem).where(BenchItem.status == Status.ready)
    if request.split:
        stmt = stmt.where(BenchItem.split == request.split)
    items = [i for i in session.exec(stmt.order_by(BenchItem.id)).all()]
    wanted = set(request.categories)
    by_category: dict[str, list[BenchItem]] = defaultdict(list)
    for item in items:
        if item.category in wanted:
            by_category[item.category].append(item)
    rng = random.Random(request.seed)
    selected: list[BenchItem] = []
    for category in sorted(by_category):
        group = by_category[category]
        n = request.sample_per_category
        selected += rng.sample(group, n) if n and n < len(group) else group
    return selected


class RunManager:
    def __init__(
        self,
        engine: Engine,
        settings: Settings,
        registry: dict[str, ModelConfig],
        providers: dict[ProviderName, Provider],
        detector: LanguageDetector,
    ):
        self.engine = engine
        self.settings = settings
        self.registry = registry
        self.providers = providers
        self.detector = detector
        self._tasks: dict[int, asyncio.Task] = {}
        self._cancelled: set[int] = set()
        self._semaphores: dict[ProviderName, asyncio.Semaphore] = {}

    # ── Préparation ──────────────────────────────────────────

    def mark_interrupted(self) -> None:
        """Au démarrage : un run resté « running » a été interrompu par un arrêt du serveur."""
        with Session(self.engine) as session:
            for run in session.exec(select(Run).where(Run.status == RunStatus.running)).all():
                run.status = RunStatus.interrupted
                session.add(run)
            session.commit()

    def availability(self) -> dict[str, bool]:
        cache: dict[ProviderName, bool] = {}
        out = {}
        for key, model in self.registry.items():
            if model.provider not in cache:
                cache[model.provider] = self.providers[model.provider].available()
            out[key] = cache[model.provider]
        return out

    def _check_models(self, keys: list[str]) -> list[ModelConfig]:
        unknown = [k for k in keys if k not in self.registry]
        if unknown:
            raise ValueError(f"modèles inconnus : {', '.join(unknown)}")
        return [self.registry[k] for k in keys]

    def estimate(self, session: Session, request: RunRequest) -> dict[str, Any]:
        models = self._check_models(request.model_keys)
        items = select_items(session, request)
        input_chars = sum(len(i.prompt) + len(i.context or "") for i in items)
        input_tokens = input_chars / CHARS_PER_TOKEN
        per_model = []
        for model in models:
            cost = model.cost(int(input_tokens), int(ESTIMATED_OUTPUT_TOKENS * len(items)))
            per_model.append({"key": model.key, "calls": len(items), "cost_usd": cost})
        known = [m["cost_usd"] for m in per_model if m["cost_usd"] is not None]
        return {
            "items": len(items),
            "by_category": dict(Counter(i.category.value for i in items)),
            "calls": len(items) * len(models),
            "models": per_model,
            "cost_usd_known_models": round(sum(known), 4) if known else None,
            "note": "estimation grossière (hors few-shot/RAG), prix inconnus non comptés",
        }

    def create_run(self, session: Session, request: RunRequest) -> Run:
        models = self._check_models(request.model_keys)
        items = select_items(session, request)
        if not items:
            raise ValueError("aucun test « ready » ne correspond à la sélection")
        manifest = read_manifest(self.settings)
        run = Run(
            name=request.name,
            test_set_hash=benchmark_hash(all_records(session)),
            test_set_version=manifest.get("version") if manifest else None,
            model_keys=[m.key for m in models],
            model_snapshot={m.key: m.model_dump(mode="json") for m in models},
            categories=[c.value for c in request.categories],
            sample_per_category=request.sample_per_category,
            seed=request.seed,
            notes=request.notes,
        )
        session.add(run)
        session.flush()
        for item in items:
            record = item_to_record(item)
            session.add(
                RunItem(run_id=run.id, item_id=item.id, category=item.category, snapshot=record)
            )
            for model in models:
                session.add(
                    ModelResponse(
                        run_id=run.id, item_id=item.id, category=item.category, model_key=model.key
                    )
                )
        session.commit()
        session.refresh(run)
        return run

    # ── Exécution ────────────────────────────────────────────

    def is_active(self, run_id: int) -> bool:
        task = self._tasks.get(run_id)
        return bool(task and not task.done())

    def start(self, run_id: int, retry_errors: bool = False) -> None:
        if self.is_active(run_id):
            raise RuntimeError("ce run est déjà en cours")
        self._cancelled.discard(run_id)
        self._tasks[run_id] = asyncio.create_task(self._execute(run_id, retry_errors))

    def cancel(self, run_id: int) -> None:
        self._cancelled.add(run_id)

    async def wait(self, run_id: int) -> None:
        if task := self._tasks.get(run_id):
            await task

    def _semaphore(self, provider: ProviderName) -> asyncio.Semaphore:
        if provider not in self._semaphores:
            self._semaphores[provider] = asyncio.Semaphore(
                self.settings.max_concurrency_per_provider
            )
        return self._semaphores[provider]

    async def _execute(self, run_id: int, retry_errors: bool) -> None:
        with Session(self.engine) as session:
            run = session.get(Run, run_id)
            assert run is not None
            run.status = RunStatus.running
            run.started_at = run.started_at or utcnow()
            run.finished_at = None
            session.add(run)
            if retry_errors:
                errors = session.exec(
                    select(ModelResponse).where(
                        ModelResponse.run_id == run_id,
                        ModelResponse.status == ResponseStatus.error,
                    )
                ).all()
                for response in errors:
                    response.status = ResponseStatus.pending
                    response.error = None
                    session.add(response)
            session.commit()
            models = {k: ModelConfig.model_validate(v) for k, v in run.model_snapshot.items()}
            snapshots = {
                ri.item_id: ri.snapshot
                for ri in session.exec(select(RunItem).where(RunItem.run_id == run_id)).all()
            }
            pending = session.exec(
                select(ModelResponse.id, ModelResponse.model_key).where(
                    ModelResponse.run_id == run_id,
                    ModelResponse.status == ResponseStatus.pending,
                )
            ).all()
            # Protège toutes les phrases du jeu de test (public et privé) et du run
            guard = ContaminationIndex(
                protected_strings(all_records(session) + list(snapshots.values()))
            )

        builder = PromptBuilder(self.settings.train_dir, self.settings.ollama_base_url, guard)
        blocked: dict[str, str] = {}
        for key, model in models.items():
            if not self.providers[model.provider].available():
                blocked[key] = f"fournisseur {model.provider} indisponible (clé API ou service)"
                continue
            try:
                await asyncio.to_thread(builder.prepare, model)
            except (FileNotFoundError, ContaminationError) as exc:
                blocked[key] = str(exc)

        state = {"stopped_cost": False}
        await asyncio.gather(
            *(
                self._one(run_id, rid, models[key], snapshots, builder, blocked, state)
                for rid, key in pending
            )
        )

        with Session(self.engine) as session:
            run = session.get(Run, run_id)
            assert run is not None
            if run_id in self._cancelled:
                run.status = RunStatus.cancelled
            elif state["stopped_cost"]:
                run.status = RunStatus.stopped_cost
            else:
                run.status = RunStatus.completed
            run.finished_at = utcnow()
            session.add(run)
            session.commit()

    def _save(self, response_id: str, **fields: Any) -> None:
        with Session(self.engine) as session:
            response = session.get(ModelResponse, response_id)
            assert response is not None
            for key, value in fields.items():
                setattr(response, key, value)
            session.add(response)
            cost = fields.get("cost_usd")
            if cost:
                run = session.get(Run, response.run_id)
                assert run is not None
                run.cost_usd = round(run.cost_usd + cost, 6)
                session.add(run)
            session.commit()

    def _run_cost(self, run_id: int) -> float:
        with Session(self.engine) as session:
            run = session.get(Run, run_id)
            return run.cost_usd if run else 0.0

    async def _one(
        self,
        run_id: int,
        response_id: str,
        model: ModelConfig,
        snapshots: dict[str, dict],
        builder: PromptBuilder,
        blocked: dict[str, str],
        state: dict[str, bool],
    ) -> None:
        if model.key in blocked:
            self._save(response_id, status=ResponseStatus.error, error=blocked[model.key])
            return
        async with self._semaphore(model.provider):
            if run_id in self._cancelled or state["stopped_cost"]:
                return
            if self._run_cost(run_id) >= self.settings.max_run_cost_usd:
                state["stopped_cost"] = True
                return
            with Session(self.engine) as session:
                response = session.get(ModelResponse, response_id)
                assert response is not None
                snapshot = snapshots[response.item_id]
                attempts = response.attempts
            system, messages = await asyncio.to_thread(builder.build, model, snapshot)
            request = {
                "provider": model.provider.value,
                "model": model.model,
                "variant": model.variant.value,
                "params": model.params,
                "system": system,
                "messages": messages,
            }
            provider = self.providers[model.provider]
            for attempt in range(1, self.settings.max_attempts + 1):
                attempts += 1
                try:
                    result = await provider.chat(model, system, messages)
                except ProviderError as exc:
                    last = attempt == self.settings.max_attempts
                    if not exc.retryable or last or run_id in self._cancelled:
                        self._save(
                            response_id,
                            status=ResponseStatus.error,
                            error=str(exc),
                            attempts=attempts,
                            request=request,
                        )
                        return
                    delay = exc.retry_after if exc.retry_after is not None else 2**attempt
                    await asyncio.sleep(delay + random.random())
                    continue
                scores = score_response(snapshot, result.text, self.detector)
                self._save(
                    response_id,
                    status=ResponseStatus.ok,
                    attempts=attempts,
                    request=request,
                    output=result.text,
                    stop_reason=result.stop_reason,
                    error=None,
                    latency_ms=result.latency_ms,
                    input_tokens=result.input_tokens,
                    output_tokens=result.output_tokens,
                    cost_usd=model.cost(result.input_tokens, result.output_tokens),
                    completed_at=utcnow(),
                    **scores,
                )
                return

    # ── Suivi ────────────────────────────────────────────────

    def progress(self, session: Session, run_id: int) -> dict[str, Any]:
        run = session.get(Run, run_id)
        if run is None:
            raise KeyError(run_id)
        rows = session.exec(
            select(ModelResponse.model_key, ModelResponse.status).where(
                ModelResponse.run_id == run_id
            )
        ).all()
        totals = Counter(status for _, status in rows)
        by_model: dict[str, Counter] = defaultdict(Counter)
        for key, status in rows:
            by_model[key][status] += 1
        return {
            "run_id": run_id,
            "status": run.status,
            "active": self.is_active(run_id),
            "total": len(rows),
            "pending": totals[ResponseStatus.pending],
            "ok": totals[ResponseStatus.ok],
            "error": totals[ResponseStatus.error],
            "cost_usd": run.cost_usd,
            "by_model": {k: dict(v) for k, v in by_model.items()},
        }
