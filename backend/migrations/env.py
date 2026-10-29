"""Environnement Alembic : utilise les métadonnées SQLModel du labo."""

import os

from alembic import context
from sqlalchemy import create_engine
from sqlmodel import SQLModel

from app import models, run_models  # noqa: F401  (enregistre les tables)

config = context.config
target_metadata = SQLModel.metadata


def _run(connection) -> None:
    # render_as_batch : SQLite ne sait pas modifier une colonne en place
    context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


connection = config.attributes.get("connection")
if connection is not None:
    _run(connection)
else:
    url = os.environ.get("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    with create_engine(url).connect() as conn:
        _run(conn)
