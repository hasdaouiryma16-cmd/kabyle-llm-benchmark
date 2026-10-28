"""Chemins, lecture du jeu de test et utilitaires partagés par les pipelines."""

import hashlib
import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from app.config import Settings
from app.contamination import ContaminationIndex, protected_strings

SETTINGS = Settings()
TEST_DIR: Path = SETTINGS.testset_dir
PROCESSED_DIR: Path = SETTINGS.train_dir
RAW_DIR: Path = PROCESSED_DIR.parent / "raw"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


def test_set_files(test_dir: Path = TEST_DIR) -> list[Path]:
    """Fichiers du jeu de test : partie publique et, si présente localement, partie privée."""
    files = sorted(test_dir.glob("*.jsonl")) + sorted((test_dir / "private").glob("*.jsonl"))
    return [f for f in files if f.is_file()]


def load_test_records(test_dir: Path = TEST_DIR) -> list[dict[str, Any]]:
    return [r for f in test_set_files(test_dir) for r in read_jsonl(f)]


def build_guard(test_dir: Path = TEST_DIR) -> tuple[ContaminationIndex, int]:
    records = load_test_records(test_dir)
    return ContaminationIndex(protected_strings(records)), len(records)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def lines(path: Path) -> Iterator[str]:
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            yield line.rstrip("\n")
