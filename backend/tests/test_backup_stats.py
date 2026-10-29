"""Sauvegarde locale et corrélation de Spearman."""

import sqlite3

import pytest

from app.config import Settings
from app.results import spearman
from scripts.backup import backup


def test_spearman_known_values():
    assert spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert spearman([1, 2, 3, 4], [40, 30, 20, 10]) == pytest.approx(-1.0)
    # Ex aequo : rangs x = [1.5, 1.5, 3, 4, 5], y = [1, 3, 2, 5, 4] → cov 7, var 9,5 et 10
    assert spearman([0, 0, 1, 2, 3], [5.0, 7.0, 6.0, 9.0, 8.0]) == pytest.approx(7 / 95**0.5)


def test_spearman_undefined():
    assert spearman([1, 2], [3, 4]) is None
    assert spearman([2, 2, 2], [1, 2, 3]) is None


def test_backup_copies_db_and_private_tests(tmp_path):
    db = tmp_path / "var" / "lab.db"
    db.parent.mkdir()
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE t (x)")
        conn.execute("INSERT INTO t VALUES (42)")
    private = tmp_path / "test" / "private"
    private.mkdir(parents=True)
    (private / "items.jsonl").write_text("{}\n", encoding="utf-8")

    settings = Settings(database_url=f"sqlite:///{db}", testset_dir=tmp_path / "test")
    dest = backup(settings, tmp_path / "backups")

    with sqlite3.connect(dest / "lab.db") as conn:
        assert conn.execute("SELECT x FROM t").fetchone() == (42,)
    assert (dest / "test-private" / "items.jsonl").read_text(encoding="utf-8") == "{}\n"


def test_backup_rotation(tmp_path):
    root = tmp_path / "backups"
    for name in ["20260101-000000", "20260102-000000", "20260103-000000"]:
        (root / name).mkdir(parents=True)
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'absent.db'}", testset_dir=tmp_path)
    backup(settings, root, keep=2)
    kept = sorted(p.name for p in root.iterdir())
    assert len(kept) == 2 and "20260101-000000" not in kept
