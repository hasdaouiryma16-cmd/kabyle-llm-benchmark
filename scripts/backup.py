"""Sauvegarde locale de tout ce qui n'est pas dans Git.

Copie la base du labo (via l'API de sauvegarde SQLite, sûre même si l'API tourne)
et le jeu de test privé dans backend/var/backups/<horodatage>/ (ignoré par Git).
Conserve les KEEP dernières sauvegardes.

    docker compose run --rm api python -m scripts.backup
"""

import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from app.config import Settings
from app.db import SQLITE_PREFIX

KEEP = 10


def backup(settings: Settings, dest_root: Path, keep: int = KEEP) -> Path:
    if not settings.database_url.startswith(SQLITE_PREFIX):
        raise SystemExit("Seules les bases SQLite sont prises en charge.")
    db_path = Path(settings.database_url.removeprefix(SQLITE_PREFIX))
    dest = dest_root / datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    dest.mkdir(parents=True)

    if db_path.exists():
        src = sqlite3.connect(db_path)
        out = sqlite3.connect(dest / "lab.db")
        with out:
            src.backup(out)
        src.close()
        out.close()

    private = settings.testset_dir / "private"
    if private.is_dir():
        shutil.copytree(private, dest / "test-private")

    for old in sorted(p for p in dest_root.iterdir() if p.is_dir())[:-keep]:
        shutil.rmtree(old)
    return dest


def main() -> None:
    settings = Settings()
    db_path = Path(settings.database_url.removeprefix(SQLITE_PREFIX))
    dest = backup(settings, db_path.parent / "backups")
    print(f"Sauvegarde : {dest}")
    for f in sorted(dest.rglob("*")):
        if f.is_file():
            print(f"  {f.relative_to(dest)} ({f.stat().st_size} octets)")


if __name__ == "__main__":
    main()
