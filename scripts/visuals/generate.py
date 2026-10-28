"""Génère les visuels de partage à partir des résultats exportés par le labo.

Entrée  : data/results/public/results.json (bouton « Exporter vers le site public » du labo)
Sorties : data/results/public/visuals/
  - og.png                          image d'aperçu du site (1200×630, balises Open Graph)
  - linkedin-square-{fr,en}.png     classement, format carré 1080×1080
  - linkedin-landscape-{fr,en}.png  classement, format paysage 1200×627
  - linkedin-gains-{fr,en}.png      avant/après de la phase 2 (si des gains existent)

Sans résultats, seule une image d'aperçu générique est produite : aucun chiffre n'est inventé.

    docker compose run --rm api python -m scripts.visuals.generate
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

from app.config import Settings  # noqa: E402

# Palette validée (daltonisme) et encres, mode sombre (meilleur rendu dans un fil LinkedIn)
BG, SURFACE, INK, INK2, MUTED, LINE = (
    "#0d0d0d",
    "#1a1a19",
    "#f0efec",
    "#c3c2b7",
    "#898781",
    "#2c2c2a",
)
SERIES = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"]
ACCENT = "#2dd4bf"
SITE = "hasdaouiryma16-cmd.github.io/kabyle-llm-benchmark"
DPI = 100

TEXT = {
    "fr": {
        "title": "Les LLM parlent-ils kabyle ?",
        "subtitle": (
            "Benchmark ouvert · références écrites par une locutrice native · notation à l'aveugle"
        ),
        "ranking": "Note humaine moyenne (%)",
        "pending": "Résultats à venir",
        "gains": "Phase 2 : améliorer un petit modèle open source",
        "before": "Avant",
        "after": "Après",
        "pts": "pts",
        "footnote": (
            "Barres d'erreur : intervalle de confiance à 95 % (bootstrap) · n = réponses notées"
        ),
    },
    "en": {
        "title": "Do LLMs speak Kabyle?",
        "subtitle": "Open benchmark · references written by a native speaker · blind grading",
        "ranking": "Mean human grade (%)",
        "pending": "Results coming soon",
        "gains": "Phase 2: improving a small open-source model",
        "before": "Before",
        "after": "After",
        "pts": "pts",
        "footnote": "Error bars: 95% bootstrap confidence interval · n = graded answers",
    },
}


def _canvas(width: int, height: int):
    fig = plt.figure(figsize=(width / DPI, height / DPI), dpi=DPI, facecolor=BG)
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK})
    return fig


def _header(fig, lang: str, top: float = 0.93, size: int = 40):
    fig.text(0.06, top, "KABYLE LLM BENCHMARK", color=ACCENT, fontsize=13, weight="bold")
    fig.text(0.06, top - 0.075, TEXT[lang]["title"], fontsize=size, weight="bold", va="top")


def _footer(fig, note: str | None = None):
    if note:
        fig.text(0.06, 0.06, note, color=MUTED, fontsize=11)
    fig.text(0.94, 0.03, SITE, color=MUTED, fontsize=11, ha="right")


def og_image(results: dict | None, out: Path) -> None:
    fig = _canvas(1200, 630)
    fig.patches.append(
        FancyBboxPatch(
            (0.07, 0.86),
            0.06,
            0.012,
            boxstyle="square,pad=0",
            transform=fig.transFigure,
            facecolor=ACCENT,
        )
    )
    fig.text(0.07, 0.80, "KABYLE LLM BENCHMARK", color=ACCENT, fontsize=18, weight="bold")
    fig.text(0.07, 0.70, TEXT["fr"]["title"], fontsize=46, weight="bold", va="top")
    fig.text(0.07, 0.50, TEXT["en"]["title"], fontsize=30, color=INK2, va="top")
    ranked = _ranked(results)[:3]
    if ranked:
        for i, model in enumerate(ranked):
            y = 0.30 - i * 0.075
            fig.text(0.07, y, f"{i + 1}. {model['label']}", fontsize=18, color=INK)
            fig.text(
                0.55,
                y,
                f"{model['overall']['human_pct']} %",
                fontsize=18,
                color=ACCENT,
                weight="bold",
            )
    else:
        fig.text(0.07, 0.26, TEXT["fr"]["subtitle"], fontsize=17, color=INK2)
    fig.text(0.07, 0.07, SITE, fontsize=15, color=MUTED)
    fig.savefig(out, facecolor=BG)
    plt.close(fig)


def _ranked(results: dict | None) -> list[dict]:
    if not results:
        return []
    return [
        m
        for m in results["models"]
        if m["overall"]["n_graded"] and m["overall"]["human_pct"] is not None
    ]


def leaderboard(results: dict, lang: str, width: int, height: int, out: Path, limit: int) -> None:
    models = _ranked(results)[:limit]
    fig = _canvas(width, height)
    square = width == height
    _header(fig, lang, size=40 if square else 32)
    fig.text(
        0.06, 0.93 - (0.15 if square else 0.20), TEXT[lang]["ranking"], color=INK2, fontsize=16
    )
    top = 0.72 if square else 0.66
    ax = fig.add_axes([0.06, 0.13, 0.88, top - 0.13], facecolor=BG)
    labels = [m["label"] for m in models][::-1]
    values = [m["overall"]["human_pct"] for m in models][::-1]
    cis = [m["overall"]["human_pct_ci95"] for m in models][::-1]
    ns = [m["overall"]["n_graded"] for m in models][::-1]
    ypos = range(len(models))
    # Barres fines ; le nom du modèle est écrit au-dessus de sa barre (jamais tronqué)
    ax.barh(ypos, [100] * len(models), color=SURFACE, height=0.34)
    ax.barh(ypos, values, color=SERIES[0], height=0.34)
    for y, label, value, ci, n in zip(ypos, labels, values, cis, ns, strict=True):
        ax.text(0, y + 0.3, label, va="bottom", fontsize=15, color=INK)
        ax.text(100, y + 0.3, f"n = {n}", va="bottom", ha="right", fontsize=11, color=MUTED)
        if ci:
            ax.plot([ci[0], ci[1]], [y, y], color=INK, lw=2, alpha=0.55)
        ax.text(102, y, f"{value:.0f} %", va="center", fontsize=17, weight="bold", color=INK)
    ax.set_ylim(-0.5, len(models) - 0.1)
    ax.set_xlim(0, 113)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    _footer(fig, TEXT[lang]["footnote"])
    fig.savefig(out, facecolor=BG)
    plt.close(fig)


def gains(results: dict, lang: str, out: Path) -> bool:
    entries = [g for g in results.get("gains", []) if g["overall"].get("gain_points") is not None]
    if not entries:
        return False
    fig = _canvas(1200, 627)
    _header(fig, lang, size=30)
    fig.text(0.06, 0.76, TEXT[lang]["gains"], color=INK2, fontsize=16)
    n = len(entries)
    for i, g in enumerate(entries):
        left = 0.06 + i * (0.88 / n)
        box = FancyBboxPatch(
            (left, 0.14),
            0.88 / n - 0.02,
            0.55,
            boxstyle="round,pad=0,rounding_size=0.02",
            transform=fig.transFigure,
            facecolor=SURFACE,
            edgecolor=LINE,
        )
        fig.patches.append(box)
        o = g["overall"]
        sign = "+" if o["gain_points"] >= 0 else ""
        fig.text(left + 0.02, 0.62, g["variant_label"], fontsize=15, weight="bold")
        fig.text(
            left + 0.02,
            0.45,
            f"{sign}{o['gain_points']} {TEXT[lang]['pts']}",
            fontsize=40,
            weight="bold",
            color=ACCENT if o["gain_points"] >= 0 else SERIES[7],
        )
        fig.text(
            left + 0.02,
            0.33,
            f"{TEXT[lang]['before']} {o['before_pct']} %  →  "
            f"{TEXT[lang]['after']} {o['after_pct']} %",
            fontsize=13,
            color=INK2,
        )
        fig.text(left + 0.02, 0.24, f"n = {o['n_paired']}", fontsize=12, color=MUTED)
    _footer(fig)
    fig.savefig(out, facecolor=BG)
    plt.close(fig)
    return True


def main() -> None:
    settings = Settings()
    source = settings.results_dir / "results.json"
    results = json.loads(source.read_text(encoding="utf-8")) if source.exists() else None
    out = settings.results_dir / "visuals"
    out.mkdir(parents=True, exist_ok=True)
    og_image(results, out / "og.png")
    produced = ["og.png"]
    if _ranked(results):
        for lang in ("fr", "en"):
            leaderboard(results, lang, 1080, 1080, out / f"linkedin-square-{lang}.png", limit=10)
            leaderboard(results, lang, 1200, 627, out / f"linkedin-landscape-{lang}.png", limit=6)
            produced += [f"linkedin-square-{lang}.png", f"linkedin-landscape-{lang}.png"]
            if gains(results, lang, out / f"linkedin-gains-{lang}.png"):
                produced.append(f"linkedin-gains-{lang}.png")
    else:
        print("Pas encore de résultats notés : seule l'image d'aperçu générique est produite.")
    print("Visuels :", ", ".join(produced), "→", out)


if __name__ == "__main__":
    main()
