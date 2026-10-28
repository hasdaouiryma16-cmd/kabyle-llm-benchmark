"""Vérifie qu'aucune donnée d'amélioration ne recoupe le jeu de test. Code de sortie 1 sinon.

Contrôle : few-shot, index RAG, données de fine-tuning et monolingues de data/train/processed/.
En CI, seule la partie publique du jeu de test est disponible ; en local, la partie privée
est contrôlée aussi. Le rapport n'affiche que les identifiants des tests, jamais leur texte.

    python -m pipelines.check_contamination
"""

import sys
from collections.abc import Iterator
from pathlib import Path

from pipelines.common import PROCESSED_DIR, build_guard, lines, read_jsonl


def candidates(processed: Path) -> Iterator[tuple[str, str]]:
    for name in ("fewshot_pool.jsonl", "pairs.jsonl", "rag_index/entries.jsonl"):
        path = processed / name
        if path.exists():
            for record in read_jsonl(path):
                for key in ("fr", "kab"):
                    if record.get(key):
                        yield name, record[key]
    for name in ("sft_train.jsonl", "sft_valid.jsonl"):
        path = processed / name
        if path.exists():
            for record in read_jsonl(path):
                for message in record["messages"]:
                    yield name, message["content"]
    mono = processed / "mono_kab.txt"
    if mono.exists():
        for line in lines(mono):
            if line:
                yield "mono_kab.txt", line


def main() -> int:
    guard, n_test = build_guard()
    checked, problems = 0, []
    for origin, text in candidates(PROCESSED_DIR):
        checked += 1
        if match := guard.check(text):
            problems.append((origin, match.test_id, match.kind, match.similarity))
    print(f"{n_test} test(s) protégé(s), {checked} chaîne(s) d'amélioration contrôlée(s)")
    if problems:
        for origin, test_id, kind, similarity in problems[:50]:
            print(f"  CONTAMINATION {origin} ↔ {test_id} ({kind}, {similarity})")
        print(f"ÉCHEC : {len(problems)} recoupement(s) avec le jeu de test")
        return 1
    print("OK : aucune contamination détectée")
    return 0


if __name__ == "__main__":
    sys.exit(main())
