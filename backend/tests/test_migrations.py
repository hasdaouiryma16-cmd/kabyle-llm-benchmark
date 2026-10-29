"""Les migrations Alembic produisent exactement le schéma des modèles."""

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text
from sqlmodel import SQLModel

from app import models, run_models  # noqa: F401
from app.db import BASELINE_REVISION, init_db, make_engine


def _version(engine) -> str:
    with engine.connect() as conn:
        return conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()


def test_migrations_match_models(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'lab.db'}")
    init_db(engine)
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), SQLModel.metadata)
    assert diff == [], f"Migration manquante : {diff}"


def test_init_db_is_idempotent(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'lab.db'}")
    init_db(engine)
    init_db(engine)
    assert "test_items" in inspect(engine).get_table_names()


def test_legacy_database_is_stamped(tmp_path):
    # Base créée avant Alembic : tables présentes, pas de table de version
    engine = make_engine(f"sqlite:///{tmp_path / 'lab.db'}")
    SQLModel.metadata.create_all(engine)
    init_db(engine)
    assert _version(engine) >= BASELINE_REVISION
