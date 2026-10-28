from conftest import make_item

from app.api.guided import load_guided
from app.config import Settings


def test_repository_guided_prompts_are_valid_and_unique():
    entries = load_guided(Settings(_env_file=None).prompts_file)
    assert len(entries) >= 50
    assert len({e["id"] for e in entries}) == len(entries)
    for entry in entries:
        assert entry["guide"]
        assert entry["prompt"] or entry["prompt_template"] or "prompt" in entry["fill"]


def test_guided_marks_prompts_already_used(client, settings):
    settings.prompts_file.parent.mkdir(parents=True, exist_ok=True)
    settings.prompts_file.write_text(
        'defaults: { fr_kab: "Traduis : {text}" }\n'
        "prompts:\n"
        "  - { id: g1, theme: t, category: translation_fr_kab, text: Bonjour }\n"
        "  - { id: g2, theme: t, category: translation_fr_kab, text: Merci }\n",
        encoding="utf-8",
    )
    item = client.post("/api/tests", json=make_item(source="guided:g1")).json()
    entries = {e["id"]: e for e in client.get("/api/guided").json()}
    assert entries["g1"]["used_by"] == item["id"]
    assert entries["g2"]["used_by"] is None
    assert entries["g2"]["prompt"] == "Traduis : Merci"
