"""Téléchargement des sources ouvertes dans data/train/raw/ (ignoré par Git).

Sources et licences : voir data/train/SOURCES.md. Chaque fichier téléchargé est consigné
avec son URL, sa taille et son empreinte SHA-256 dans data/train/raw/downloads.json.

    python -m pipelines.download                 # Tatoeba + Common Voice
    python -m pipelines.download --with-nllb     # + NLLB (43 Mo, aligné automatiquement, bruité)
"""

import argparse
import json
import urllib.request
import zipfile
from pathlib import Path

from app.models import utcnow
from pipelines.common import RAW_DIR, sha256_file

SOURCES = {
    "tatoeba": {
        "url": "https://object.pouta.csc.fi/OPUS-Tatoeba/v2026-07-08/moses/fr-kab.txt.zip",
        "license": "CC BY 2.0 FR (certaines phrases CC0)",
    },
    "nllb": {
        "url": "https://object.pouta.csc.fi/OPUS-NLLB/v1/moses/fr-kab.txt.zip",
        "license": "ODC-By 1.0",
    },
}
COMMON_VOICE_API = "https://api.github.com/repos/common-voice/common-voice/contents/server/data/kab"
USER_AGENT = "kabyle-llm-benchmark (https://github.com/hasdaouiryma16-cmd/kabyle-llm-benchmark)"


def fetch(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response, dest.open("wb") as out:
        while chunk := response.read(1 << 20):
            out.write(chunk)
    return dest


def download_zip(name: str, raw_dir: Path) -> list[dict]:
    source = SOURCES[name]
    archive = fetch(source["url"], raw_dir / name / Path(source["url"]).name)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(raw_dir / name)
    return [
        {
            "source": name,
            "url": source["url"],
            "license": source["license"],
            "file": str(archive.name),
            "bytes": archive.stat().st_size,
            "sha256": sha256_file(archive),
        }
    ]


def download_common_voice(raw_dir: Path) -> list[dict]:
    request = urllib.request.Request(COMMON_VOICE_API, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        listing = json.load(response)
    entries = []
    for item in listing:
        if item["type"] != "file" or not item["name"].endswith(".txt"):
            continue
        path = fetch(item["download_url"], raw_dir / "commonvoice" / item["name"])
        entries.append(
            {
                "source": "commonvoice",
                "url": item["download_url"],
                "license": "CC0 1.0",
                "file": item["name"],
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-nllb", action="store_true")
    parser.add_argument("--skip-commonvoice", action="store_true")
    args = parser.parse_args()

    log: list[dict] = []
    print("Tatoeba (OPUS)…")
    log += download_zip("tatoeba", RAW_DIR)
    if not args.skip_commonvoice:
        print("Common Voice (phrases kabyles, CC0)…")
        log += download_common_voice(RAW_DIR)
    if args.with_nllb:
        print("NLLB (OPUS)…")
        log += download_zip("nllb", RAW_DIR)

    manifest = {"downloaded_at": utcnow().isoformat(), "files": log}
    (RAW_DIR / "downloads.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"{len(log)} fichier(s) dans {RAW_DIR}")


if __name__ == "__main__":
    main()
