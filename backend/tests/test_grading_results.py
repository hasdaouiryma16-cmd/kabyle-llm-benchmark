import json

from conftest import make_item, wait_run


def _run(client, models, n=2, **item):
    for _ in range(n):
        client.post("/api/tests", json=make_item(**item))
    run_id = client.post("/api/runs", json={"name": "r", "model_keys": models}).json()["run_id"]
    wait_run(client, run_id)
    return run_id


def _grade_all(client, score_for):
    """Note toutes les réponses ; score_for(modèle révélé) → note."""
    graded = 0
    while (blind := client.get("/api/grading/next").json()) is not None:
        rid = blind["response_id"]
        client.put(f"/api/grading/{rid}", json={"score": 0})
        model = client.get(f"/api/grading/{rid}/reveal").json()["model_key"]
        client.put(f"/api/grading/{rid}", json={"score": score_for(model)})
        graded += 1
    return graded


def test_blind_view_hides_the_model(client):
    _run(client, ["mock-a"], n=1)
    blind = client.get("/api/grading/next").json()
    text = json.dumps(blind)
    assert "mock" not in text and "Modèle" not in text and "chrf" not in text
    assert blind["output"] == "ref-a"


def test_reveal_only_after_grading(client):
    _run(client, ["mock-a"], n=1)
    rid = client.get("/api/grading/next").json()["response_id"]
    assert client.get(f"/api/grading/{rid}/reveal").status_code == 403
    client.put(f"/api/grading/{rid}", json={"score": 3, "error_tags": []})
    assert client.get(f"/api/grading/{rid}/reveal").json()["model_key"] == "mock-a"


def test_grading_validates_score_and_tags(client):
    _run(client, ["mock-a"], n=1)
    rid = client.get("/api/grading/next").json()["response_id"]
    assert client.put(f"/api/grading/{rid}", json={"score": 4}).status_code == 422
    assert (
        client.put(f"/api/grading/{rid}", json={"score": 1, "error_tags": ["x"]}).status_code == 422
    )
    assert (
        client.put(f"/api/grading/{rid}", json={"score": 1, "error_tags": ["spelling"]}).status_code
        == 200
    )


def test_stats_and_queue_exhaustion(client):
    _run(client, ["mock-a", "mock-b"], n=2)
    assert client.get("/api/grading/stats").json() == {"total": 4, "graded": 0, "remaining": 4}
    assert _grade_all(client, lambda m: 3) == 4
    assert client.get("/api/grading/next").json() is None
    assert client.get("/api/grading/stats").json()["remaining"] == 0


def test_results_and_paired_gain(client, settings):
    settings.train_dir.mkdir(parents=True)
    (settings.train_dir / "fewshot_pool.jsonl").write_text(
        json.dumps({"fr": "Il pleut.", "kab": "ex-kab"}) + "\n", encoding="utf-8"
    )
    _run(client, ["mock-b", "mock-b-fewshot"], n=3)
    _grade_all(client, lambda m: 3 if m == "mock-b-fewshot" else 1)

    results = client.get("/api/results").json()
    models = {m["key"]: m for m in results["models"]}
    assert models["mock-b"]["overall"]["human_mean"] == 1.0
    assert models["mock-b-fewshot"]["overall"]["human_pct"] == 100.0
    assert results["models"][0]["key"] == "mock-b-fewshot"  # classement décroissant

    gain = results["gains"][0]
    assert gain["variant"] == "mock-b-fewshot" and gain["base"] == "mock-b"
    overall = gain["overall"]
    assert overall["n_paired"] == 3
    assert overall["before_pct"] == 33.3 and overall["after_pct"] == 100.0
    assert overall["gain_points"] == 66.7 and overall["gain_relative_pct"] == 200.0
    assert "translation_fr_kab" in gain["by_category"]


def test_export_public_publishes_only_public_favorites(client, settings):
    _run(client, ["mock-a"], n=1)
    _run(client, ["mock-a"], n=1, split="private", prompt="Consigne privée")
    _grade_all(client, lambda m: 2)
    for row in client.get("/api/results/responses").json():
        client.put(f"/api/favorites/{row['response_id']}", json={"kind": "success"})

    summary = client.post("/api/results/export-public").json()
    assert summary["examples"] == 1
    published = (settings.results_dir / "results.json").read_text(encoding="utf-8")
    assert "Consigne privée" not in published
    data = json.loads(published)
    assert data["models"][0]["overall"]["n_graded"] >= 1
    assert "params" not in json.dumps(data["models"])
