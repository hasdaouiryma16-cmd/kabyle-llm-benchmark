import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

# Les tests n'utilisent que des valeurs factices : aucun texte kabyle n'est écrit ici.


@pytest.fixture
def settings(tmp_path):
    return Settings(
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'lab.db'}",
        testset_dir=tmp_path / "test",
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
