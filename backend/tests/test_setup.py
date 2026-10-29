"""Liste de préparation du labo (/api/setup)."""

import json

from conftest import make_item
from pydantic import SecretStr


def _checks(client) -> dict[str, dict]:
    data = client.get("/api/setup").json()
    return {c["id"]: c for g in data["groups"] for c in g["checks"]}


def test_empty_lab(client):
    checks = _checks(client)
    assert checks["tests"]["state"] == "todo"
    assert checks["categories"]["state"] == "warn"
    assert "private" not in checks
    assert checks["prepared"]["state"] == "todo"
    # Fournisseurs factices uniquement : aucune clé à demander
    assert not any(k.startswith("key-") for k in checks)
    assert client.get("/api/setup").json()["can_run_api_benchmark"] is False


def test_tests_and_repo_sync(client):
    for i in range(4):
        client.post("/api/tests", json=make_item(prompt=f"Consigne {i}", split="public"))
    client.post("/api/tests", json=make_item(prompt="Consigne privée", split="private"))
    checks = _checks(client)
    assert checks["tests"]["state"] == "warn"
    assert checks["private"]["state"] == "ok"  # 1 sur 5 = 20 %
    assert checks["repo"]["state"] == "todo"
    client.post("/api/testset/save-to-repo", json={})
    assert _checks(client)["repo"]["state"] == "ok"


def test_prepared_data_must_follow_test_set(client, settings):
    from app.contamination import protected_fingerprint

    settings.train_dir.mkdir(parents=True)
    (settings.train_dir / "fewshot_pool.jsonl").write_text("", encoding="utf-8")
    stats = {"pairs": {"kept": 10}, "protected_test_fingerprint": protected_fingerprint([])}
    (settings.train_dir / "STATS.json").write_text(json.dumps(stats), encoding="utf-8")
    assert _checks(client)["prepared"]["state"] == "ok"

    client.post("/api/tests", json=make_item())
    client.post("/api/testset/save-to-repo", json={})
    assert _checks(client)["prepared"]["state"] == "todo"


def test_api_key_presence_never_leaks_value(tmp_path, settings):
    from fastapi.testclient import TestClient

    from app.main import create_app

    config = tmp_path / "real-models.yaml"
    config.write_text(
        "models:\n  - key: c\n    label: C\n    provider: anthropic\n    model: c\n",
        encoding="utf-8",
    )
    secret = "valeur-secrete-de-test"
    s = settings.model_copy(
        update={"models_config": config, "anthropic_api_key": SecretStr(secret)}
    )
    with TestClient(create_app(s)) as client:
        response = client.get("/api/setup")
    assert secret not in response.text
    assert response.json()["can_run_api_benchmark"] is True
