import json

from conftest import make_item
from fastapi.testclient import TestClient

from app.main import create_app
from app.testset import benchmark_hash

LETTERS = "ɛ ɣ ḥ ṭ ẓ č ǧ ṛ ṣ ḍ ⴰ ⵣ"  # caractères isolés pour tester l'Unicode


def _records(client):
    return sorted(client.get("/api/tests").json(), key=lambda r: r["id"])


def _seed(client):
    client.post("/api/tests", json=make_item(references=[LETTERS, "ref-b"]))
    client.post(
        "/api/tests",
        json=make_item(category="comprehension", source_text=None, context=LETTERS),
    )


def _fresh_client(tmp_path, settings, name):
    other = settings.model_copy(update={"database_url": f"sqlite:///{tmp_path / name}"})
    return TestClient(create_app(other))


def _roundtrip(client, tmp_path, settings, fmt):
    exported = client.get("/api/testset/export", params={"format": fmt})
    assert exported.status_code == 200
    with _fresh_client(tmp_path, settings, f"{fmt}.db") as other:
        files = {"file": (f"export.{fmt}", exported.content)}
        report = other.post("/api/testset/import", files=files).json()
        assert report["created"] == 2
        return _records(other)


def test_jsonl_roundtrip(client, tmp_path, settings):
    _seed(client)
    assert _roundtrip(client, tmp_path, settings, "jsonl") == _records(client)


def test_json_roundtrip(client, tmp_path, settings):
    _seed(client)
    assert _roundtrip(client, tmp_path, settings, "json") == _records(client)


def test_csv_roundtrip_with_excel_bom(client, tmp_path, settings):
    _seed(client)
    assert client.get("/api/testset/export", params={"format": "csv"}).content.startswith(
        b"\xef\xbb\xbf"
    )
    assert _roundtrip(client, tmp_path, settings, "csv") == _records(client)


def test_import_is_all_or_nothing(client):
    lines = [make_item(id="ok-1"), make_item(id="ko-1", references=[]), make_item(id="ok-1")]
    content = "\n".join(json.dumps(line) for line in lines).encode()
    response = client.post("/api/testset/import", files={"file": ("t.jsonl", content)})
    assert response.status_code == 422
    rows = {error["row"] for error in response.json()["errors"]}
    assert rows == {2, 3}
    assert client.get("/api/tests").json() == []


def test_import_rejects_unknown_format(client):
    response = client.post("/api/testset/import", files={"file": ("t.txt", b"x")})
    assert response.status_code == 400


def test_benchmark_hash_tracks_evaluated_content_only():
    base = {
        "id": "a", "category": "culture", "script": "latin", "prompt": "p",
        "source_text": None, "context": None, "references": ["r"], "grading": "auto",
        "expected_lang": "kab", "status": "ready", "notes": "",
    }  # fmt: skip
    reference = benchmark_hash([base])
    assert benchmark_hash([{**base, "notes": "autre"}]) == reference
    assert benchmark_hash([{**base, "references": ["r2"]}]) != reference
    assert benchmark_hash([{**base, "status": "draft"}]) != reference  # exclu du benchmark


def test_save_to_repo_separates_private_items(client, settings):
    client.post("/api/tests", json=make_item(id="pub-1"))
    client.post("/api/tests", json=make_item(id="priv-1", split="private"))

    manifest = client.post("/api/testset/save-to-repo", json={"version": "1.0.0"}).json()

    public_file = (settings.testset_dir / "kab-bench.v1.jsonl").read_text(encoding="utf-8")
    private_file = settings.testset_dir / "private" / "kab-bench.v1.private.jsonl"
    assert "pub-1" in public_file and "priv-1" not in public_file
    assert "priv-1" in private_file.read_text(encoding="utf-8")
    assert manifest["public"]["items"] == 1 and manifest["private"]["items"] == 1
    assert manifest["benchmark"]["items"] == 2
    assert "CANARY GUID" in manifest["canary"]


def test_canary_is_stable_and_sync_status_detects_changes(client):
    item = client.post("/api/tests", json=make_item()).json()
    first = client.post("/api/testset/save-to-repo").json()
    assert client.get("/api/testset/status").json()["repo_in_sync"] is True

    update = {k: v for k, v in item.items() if k not in ("id", "created_at", "updated_at")}
    client.put(f"/api/tests/{item['id']}", json={**update, "notes": "modifié"})
    assert client.get("/api/testset/status").json()["repo_in_sync"] is False

    second = client.post("/api/testset/save-to-repo", json={"version": "1.1.0"}).json()
    assert second["canary"] == first["canary"]
    assert second["version"] == "1.1.0"


def test_load_from_repo_rebuilds_database(client, tmp_path, settings):
    _seed(client)
    client.post("/api/tests", json=make_item(id="priv-1", split="private"))
    client.post("/api/testset/save-to-repo")

    with _fresh_client(tmp_path, settings, "rebuilt.db") as other:
        report = other.post("/api/testset/load-from-repo").json()
        assert report["created"] == 3
        assert _records(other) == _records(client)


def test_load_from_repo_without_file_returns_404(client):
    assert client.post("/api/testset/load-from-repo").status_code == 404
