import json

from conftest import make_item, wait_run

from app.registry import ProviderName


def _seed(client, n=3, **overrides):
    for _ in range(n):
        client.post("/api/tests", json=make_item(**overrides))


def _run(client, models, **extra):
    payload = {"name": "essai", "model_keys": models, **extra}
    response = client.post("/api/runs", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["run_id"]


def _mock(client):
    return client.app.state.runner.providers[ProviderName.mock]


def test_models_are_listed_with_availability(client):
    models = {m["key"]: m for m in client.get("/api/models").json()}
    assert models["mock-a"]["available"] is True
    assert models["mock-b-fewshot"]["base"] == "mock-b"


def test_estimate_counts_calls_and_known_costs(client):
    _seed(client)
    estimate = client.post(
        "/api/runs/estimate", json={"name": "x", "model_keys": ["mock-a", "mock-b"]}
    ).json()
    assert estimate["calls"] == 6
    costs = {m["key"]: m["cost_usd"] for m in estimate["models"]}
    assert costs["mock-a"] > 0 and costs["mock-b"] is None  # prix inconnu : jamais inventé


def test_free_tier_model_never_receives_private_tests(client):
    _seed(client, n=2)
    _seed(client, n=1, split="private", prompt="Consigne privée")
    for split in (None, "private"):
        payload = {"name": "x", "model_keys": ["mock-a", "mock-free"], "split": split}
        assert client.post("/api/runs/estimate", json=payload).status_code == 400
        response = client.post("/api/runs", json=payload)
        assert response.status_code == 400 and "mock-free" in response.text
    assert client.get("/api/runs").json() == []  # rien n'a été créé
    run_id = _run(client, ["mock-free"], split="public")
    assert wait_run(client, run_id)["total"] == 2
    sent = json.dumps(_mock(client).calls, ensure_ascii=False)
    assert "Consigne privée" not in sent


def test_run_completes_and_scores_automatically(client):
    _seed(client, n=2)
    run_id = _run(client, ["mock-a", "mock-b"])
    progress = wait_run(client, run_id)
    assert progress["status"] == "completed" and progress["ok"] == 4
    responses = client.get(f"/api/runs/{run_id}/responses").json()
    chrf = {r["model_key"]: r["chrf"] for r in responses}
    assert chrf["mock-a"] == 100.0  # identique à la référence
    assert chrf["mock-b"] < 50
    run = client.get(f"/api/runs/{run_id}").json()
    assert run["test_set_hash"] and run["model_snapshot"]["mock-a"]["params"] == {"reply": "ref-a"}


def test_only_ready_items_are_used(client):
    _seed(client, n=2)
    client.post("/api/tests", json=make_item(status="draft"))
    run_id = _run(client, ["mock-a"])
    assert wait_run(client, run_id)["total"] == 2


def test_sample_per_category_limits_cost(client):
    _seed(client, n=5)
    _seed(client, n=5, category="culture", source_text=None)
    run_id = _run(client, ["mock-a"], sample_per_category=2)
    assert wait_run(client, run_id)["total"] == 4


def test_errors_are_retried_then_resumable_without_redoing_successes(client):
    _seed(client, n=2)
    runner = client.app.state.runner
    runner.settings.max_attempts = 2
    mock = _mock(client)
    mock.failures_before_success = 1  # une erreur 429 simulée, rattrapée par la 2e tentative
    run_id = _run(client, ["mock-a"])
    assert wait_run(client, run_id)["ok"] == 2

    runner.settings.max_attempts = 1
    mock.failures_before_success = 1
    client.post("/api/tests", json=make_item())
    run_id = _run(client, ["mock-a"])
    progress = wait_run(client, run_id)
    assert progress["error"] == 1 and progress["ok"] == 2

    calls_before = len(mock.calls)
    client.post(f"/api/runs/{run_id}/resume")
    progress = wait_run(client, run_id)
    assert progress["ok"] == 3 and progress["error"] == 0
    assert len(mock.calls) == calls_before + 1  # seule la réponse en erreur est rejouée


def test_cost_cap_stops_run(client):
    _seed(client, n=3)
    client.app.state.runner.settings.max_run_cost_usd = 0.000001
    client.app.state.runner.settings.max_concurrency_per_provider = 1
    run_id = _run(client, ["mock-a"])
    progress = wait_run(client, run_id)
    assert progress["status"] == "stopped_cost"
    assert progress["pending"] > 0


def test_run_keeps_a_frozen_copy_of_items(client):
    item = client.post("/api/tests", json=make_item()).json()
    run_id = _run(client, ["mock-a"])
    wait_run(client, run_id)
    update = {k: v for k, v in item.items() if k not in ("id", "created_at", "updated_at")}
    client.put(f"/api/tests/{item['id']}", json={**update, "references": ["changée"]})
    blind = client.get("/api/grading/next").json()
    assert blind["item"]["references"] == ["ref-a"]


def test_fewshot_variant_requires_training_pool(client):
    _seed(client, n=1)
    run_id = _run(client, ["mock-b-fewshot"])
    wait_run(client, run_id)
    responses = client.get(f"/api/runs/{run_id}/responses").json()
    assert responses[0]["status"] == "error" and "introuvable" in responses[0]["error"]


def _write_pool(settings, pairs):
    settings.train_dir.mkdir(parents=True, exist_ok=True)
    with (settings.train_dir / "fewshot_pool.jsonl").open("w", encoding="utf-8") as handle:
        for fr, kab in pairs:
            handle.write(json.dumps({"fr": fr, "kab": kab}, ensure_ascii=False) + "\n")


def test_fewshot_variant_blocked_when_pool_is_contaminated(client, settings):
    _seed(client, n=1)
    _write_pool(settings, [("Bonjour.", "ref-a")])  # phrase du jeu de test
    run_id = _run(client, ["mock-b-fewshot"])
    wait_run(client, run_id)
    response = client.get(f"/api/runs/{run_id}/responses").json()[0]
    assert response["status"] == "error" and "jeu de test" in response["error"]


def test_fewshot_variant_adds_examples_as_dialogue_turns(client, settings):
    _seed(client, n=1)
    _write_pool(
        settings, [("Il pleut beaucoup.", "ex-kab-1"), ("La maison est grande.", "ex-kab-2")]
    )
    mock = _mock(client)
    run_id = _run(client, ["mock-b-fewshot"])
    assert wait_run(client, run_id)["ok"] == 1
    messages = mock.calls[-1]
    assert [m["role"] for m in messages] == ["user", "assistant", "user", "assistant", "user"]
    assert {messages[1]["content"], messages[3]["content"]} == {"ex-kab-1", "ex-kab-2"}
