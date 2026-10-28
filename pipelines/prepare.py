"""Nettoyage, dédoublonnage et décontamination des données d'amélioration.

Entrées : data/train/raw/ (voir pipelines.download).
Sorties (data/train/processed/, non versionnées sauf STATS.json) :
- pairs.jsonl          : paires français–kabyle propres et décontaminées
- fewshot_pool.jsonl   : réservoir d'exemples pour la variante few-shot
- sft_train.jsonl / sft_valid.jsonl : conversations pour le fine-tuning (deux sens)
- mono_kab.txt         : phrases kabyles monolingues (Common Voice)
- STATS.json           : comptes à chaque étape, empreintes, phrases retirées pour contamination

Chaque phrase est vérifiée contre TOUT le jeu de test disponible localement (public + privé) :
doublon exact après normalisation, ou quasi-doublon (Jaccard ≥ 0,8 sur 5-grammes de caractères).
"""

import argparse
import json
import random
import re
import unicodedata
from collections import Counter
from pathlib import Path

from app.contamination import ContaminationIndex, normalize
from app.models import utcnow
from app.scoring import detect_script
from pipelines.common import PROCESSED_DIR, RAW_DIR, build_guard, lines, sha256_file, write_jsonl

MIN_CHARS, MAX_CHARS = 2, 300
VALID_FRACTION = 0.01
SEED = 13

# Consignes (en français) des exemples de fine-tuning ; le contenu vient des corpus.
SFT_TEMPLATES = {
    "fr_kab": [
        "Traduis en kabyle (alphabet latin). Réponds uniquement par la traduction : « {src} »",
        "Traduis en kabyle : « {src} »",
        "Comment dit-on en kabyle : « {src} » ?",
    ],
    "kab_fr": [
        "Traduis en français. Réponds uniquement par la traduction : « {src} »",
        "Traduis en français : « {src} »",
        "Que signifie en français : « {src} » ?",
    ],
}

_SPACES = re.compile(r"\s+")


def clean(text: str) -> str:
    return _SPACES.sub(" ", unicodedata.normalize("NFC", text)).strip()


def valid_kab(text: str) -> bool:
    return MIN_CHARS <= len(text) <= MAX_CHARS and detect_script(text) in ("latin", None)


def valid_fr(text: str) -> bool:
    return MIN_CHARS <= len(text) <= MAX_CHARS and detect_script(text) in ("latin", None)


def read_moses(directory: Path, prefix: str) -> list[tuple[str, str]]:
    fr_path, kab_path = directory / f"{prefix}.fr-kab.fr", directory / f"{prefix}.fr-kab.kab"
    if not fr_path.exists():
        return []
    return list(zip(lines(fr_path), lines(kab_path), strict=True))


def read_nllb(directory: Path, keep_best: int) -> list[tuple[str, str]]:
    pairs = read_moses(directory, "NLLB")
    scores_path = directory / "NLLB.fr-kab.scores"
    if not pairs or not scores_path.exists():
        return pairs[:keep_best]
    scores = [float(s or 0) for s in lines(scores_path)]
    ranked = sorted(range(len(pairs)), key=lambda i: -scores[i])[:keep_best]
    return [pairs[i] for i in sorted(ranked)]


def filter_pairs(
    raw: list[tuple[str, str, str]], guard: ContaminationIndex, stats: Counter
) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    out = []
    for source, fr, kab in raw:
        fr, kab = clean(fr), clean(kab)
        stats["input"] += 1
        if not (valid_fr(fr) and valid_kab(kab)) or normalize(fr) == normalize(kab):
            stats["removed_invalid"] += 1
            continue
        key = (normalize(fr), normalize(kab))
        if key in seen:
            stats["removed_duplicate"] += 1
            continue
        seen.add(key)
        if guard.check(fr) or guard.check(kab):
            stats["removed_contamination"] += 1
            continue
        out.append({"fr": fr, "kab": kab, "source": source})
    stats["kept"] = len(out)
    return out


def sft_records(pairs: list[dict[str, str]], rng: random.Random) -> list[dict]:
    records = []
    for pair in pairs:
        for direction, src, tgt in (
            ("fr_kab", pair["fr"], pair["kab"]),
            ("kab_fr", pair["kab"], pair["fr"]),
        ):
            prompt = rng.choice(SFT_TEMPLATES[direction]).format(src=src)
            records.append(
                {
                    "messages": [
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": tgt},
                    ],
                    "source": pair["source"],
                }
            )
    return records


def monolingual(raw_dir: Path, guard: ContaminationIndex, stats: Counter) -> list[str]:
    seen: set[str] = set()
    out = []
    for path in sorted((raw_dir / "commonvoice").glob("*.txt")):
        for line in lines(path):
            text = clean(line)
            if not text:
                continue
            stats["input"] += 1
            if not valid_kab(text):
                stats["removed_invalid"] += 1
                continue
            key = normalize(text)
            if key in seen:
                stats["removed_duplicate"] += 1
                continue
            seen.add(key)
            if guard.check(text):
                stats["removed_contamination"] += 1
                continue
            out.append(text)
    stats["kept"] = len(out)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--nllb-keep-best",
        type=int,
        default=0,
        help="ajouter les N meilleures paires NLLB (0 = aucune)",
    )
    parser.add_argument(
        "--fewshot-pool-size",
        type=int,
        default=0,
        help="taille du réservoir few-shot (0 = toutes les paires Tatoeba)",
    )
    args = parser.parse_args()

    guard, n_test = build_guard()
    print(f"Jeu de test chargé : {n_test} test(s) protégés")

    raw = [("tatoeba", fr, kab) for fr, kab in read_moses(RAW_DIR / "tatoeba", "Tatoeba")]
    if args.nllb_keep_best:
        raw += [("nllb", fr, kab) for fr, kab in read_nllb(RAW_DIR / "nllb", args.nllb_keep_best)]
    if not raw:
        raise SystemExit("Aucune donnée brute : lancer d'abord python -m pipelines.download")

    pair_stats: Counter = Counter()
    pairs = filter_pairs(raw, guard, pair_stats)
    rng = random.Random(SEED)

    tatoeba = [p for p in pairs if p["source"] == "tatoeba"]
    pool = (
        tatoeba
        if not args.fewshot_pool_size
        else rng.sample(tatoeba, min(args.fewshot_pool_size, len(tatoeba)))
    )

    shuffled = pairs[:]
    rng.shuffle(shuffled)
    n_valid = max(1, int(len(shuffled) * VALID_FRACTION))
    sft_valid, sft_train = (
        sft_records(shuffled[:n_valid], rng),
        sft_records(shuffled[n_valid:], rng),
    )

    mono_stats: Counter = Counter()
    mono = monolingual(RAW_DIR, guard, mono_stats)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "pairs.jsonl": write_jsonl(PROCESSED_DIR / "pairs.jsonl", pairs),
        "fewshot_pool.jsonl": write_jsonl(PROCESSED_DIR / "fewshot_pool.jsonl", pool),
        "sft_train.jsonl": write_jsonl(PROCESSED_DIR / "sft_train.jsonl", sft_train),
        "sft_valid.jsonl": write_jsonl(PROCESSED_DIR / "sft_valid.jsonl", sft_valid),
    }
    (PROCESSED_DIR / "mono_kab.txt").write_text("\n".join(mono) + "\n", encoding="utf-8")
    outputs["mono_kab.txt"] = len(mono)

    stats = {
        "generated_at": utcnow().isoformat(),
        "protected_test_items": n_test,
        "pairs": dict(pair_stats),
        "pairs_by_source": dict(Counter(p["source"] for p in pairs)),
        "monolingual": dict(mono_stats),
        "outputs": {
            name: {"records": count, "sha256": sha256_file(PROCESSED_DIR / name)}
            for name, count in outputs.items()
        },
    }
    (PROCESSED_DIR / "STATS.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
