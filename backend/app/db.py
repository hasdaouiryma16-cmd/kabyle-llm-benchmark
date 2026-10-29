"""Connexion à la base SQLite et session par requête."""

from collections.abc import Iterator
from pathlib import Path

from fastapi import Request
from sqlalchemy import event, inspect
from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

SQLITE_PREFIX = "sqlite:///"


def make_engine(url: str) -> Engine:
    if not url.startswith(SQLITE_PREFIX):
        return create_engine(url)
    Path(url.removeprefix(SQLITE_PREFIX)).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, connect_args={"check_same_thread": False})
    event.listen(engine, "connect", _enable_foreign_keys)
    return engine


def _enable_foreign_keys(dbapi_connection, _record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"
BASELINE_REVISION = "0001"


def init_db(engine: Engine) -> None:
    """Met le schéma à jour via les migrations Alembic.

    Une base créée avant les migrations (tables présentes, pas de version)
    est marquée à la révision initiale, puis mise à jour normalement.
    """
    from alembic import command
    from alembic.config import Config

    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(ALEMBIC_INI.parent / "migrations"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        tables = set(inspect(connection).get_table_names())
        if "test_items" in tables and "alembic_version" not in tables:
            command.stamp(config, BASELINE_REVISION)
        command.upgrade(config, "head")


def get_session(request: Request) -> Iterator[Session]:
    with Session(request.app.state.engine) as session:
        yield session
