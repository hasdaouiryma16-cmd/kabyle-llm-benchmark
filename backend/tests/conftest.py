import time

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

# Les tests n'utilisent que des valeurs factices : aucun texte kabyle n'est écrit ici.

MOCK_MODELS = """
models:
  - key: mock-a
    label: Modèle A
    provider: mock
    model: a
    params: { reply: "ref-a" }
    pricing: { input: 1.0, output: 1.0 }
  - key: mock-b
    label: Modèle B
    provider: mock
    model: b
    params: { reply: "autre chose" }
  - key: mock-b-fewshot
    label: Modèle B + few-shot
    provider: mock
    model: b
    base: mock-b
    variant: fewshot
    variant_params: { k: 2 }
    params: { reply: "ref-a" }
  - key: mock-free
    label: Modèle gratuit
    provider: mock
    model: free
    public_only: true
"""


@pytest.fixture
def settings(tmp_path):
    config = tmp_path / "models.yaml"
    config.write_text(MOCK_MODELS, encoding="utf-8")
    return Settings(
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'lab.db'}",
        testset_dir=tmp_path / "test",
        train_dir=tmp_path / "train",
        results_dir=tmp_path / "results",
        prompts_file=tmp_path / "prompts" / "guided.yaml",
        models_config=config,
        glotlid_model_path=tmp_path / "absent.bin",
        anthropic_api_key=None,
        openai_api_key=None,
        mistral_api_key=None,
        openrouter_api_key=None,
        gemini_api_key=None,
        ollama_base_url="http://127.0.0.1:9",
    )


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def make_item(**overrides):
    item = {
        "category": "translation_fr_kab",
        "prompt": "Traduis en kabyle : « Bonjour. »",
        "source_text": "Bonjour.",
        "references": ["ref-a"],
        "status": "ready",
    }
    item.update(overrides)
    return item


def wait_run(client, run_id, timeout=10.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        progress = client.get(f"/api/runs/{run_id}").json()["progress"]
        if not progress["active"] and progress["status"] != "running":
            return progress
        time.sleep(0.05)
    raise TimeoutError("run non terminé")
