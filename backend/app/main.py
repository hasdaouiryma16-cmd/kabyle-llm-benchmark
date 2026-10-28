"""Point d'entrée de l'API du labo.

Lancement : uvicorn app.main:create_app --factory
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import grading, items, results, runs, testset
from app.config import Settings
from app.db import init_db, make_engine
from app.providers import build_providers
from app.registry import load_registry
from app.runner import RunManager
from app.scoring import LanguageDetector


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    engine = make_engine(settings.database_url)
    init_db(engine)
    runner = RunManager(
        engine,
        settings,
        load_registry(settings.models_config),
        build_providers(settings),
        LanguageDetector(settings.glotlid_model_path),
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        runner.mark_interrupted()
        yield

    app = FastAPI(title="Kabyle LLM Benchmark — Labo", version="0.2.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.runner = runner

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for module in (items, testset, runs, grading, results):
        app.include_router(module.router)

    @app.get("/api/health", tags=["system"])
    def health():
        return {"status": "ok", "language_detection": runner.detector.method}

    return app
