"""Point d'entrée de l'API du labo.

Lancement : uvicorn app.main:create_app --factory
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import items, testset
from app.config import Settings
from app.db import init_db, make_engine


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    engine = make_engine(settings.database_url)
    init_db(engine)

    app = FastAPI(title="Kabyle LLM Benchmark — Labo", version="0.1.0")
    app.state.settings = settings
    app.state.engine = engine

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(items.router)
    app.include_router(testset.router)

    @app.get("/api/health", tags=["system"])
    def health():
        return {"status": "ok"}

    return app
