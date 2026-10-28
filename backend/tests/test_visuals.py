"""Le générateur de visuels fonctionne sur des données factices (jamais publiées)."""

import json

from scripts.visuals import generate


def fake_results():
    def summary(pct):
        return {"n": 10, "n_graded": 10, "human_pct": pct, "human_pct_ci95": [pct - 8, pct + 8]}

    models = [
        {"key": f"m{i}", "label": f"Modèle factice {i}", "overall": summary(80 - 15 * i)}
        for i in range(4)
    ]
    gains = [
        {
            "variant": "m3",
            "variant_label": "Variante factice",
            "base": "m2",
            "overall": {"gain_points": 12.5, "before_pct": 35.0, "after_pct": 47.5, "n_paired": 10},
        }
    ]
    return {"models": models, "gains": gains}


def test_generates_all_visuals(tmp_path, monkeypatch):
    (tmp_path / "results.json").write_text(json.dumps(fake_results()), encoding="utf-8")
    monkeypatch.setattr(generate, "Settings", lambda: type("S", (), {"results_dir": tmp_path})())
    generate.main()
    names = sorted(p.name for p in (tmp_path / "visuals").glob("*.png"))
    assert names == sorted(
        ["og.png"]
        + [
            f"linkedin-{kind}-{lang}.png"
            for kind in ("square", "landscape", "gains")
            for lang in ("fr", "en")
        ]
    )


def test_without_results_only_generic_preview(tmp_path, monkeypatch):
    monkeypatch.setattr(generate, "Settings", lambda: type("S", (), {"results_dir": tmp_path})())
    generate.main()
    assert [p.name for p in (tmp_path / "visuals").glob("*.png")] == ["og.png"]
