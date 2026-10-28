"""Configuration du labo, lue depuis les variables d'environnement (et .env en local)."""

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    database_url: str = "sqlite:///./var/lab.db"
    # Dossier du jeu de test versionné dans Git (source de vérité)
    testset_dir: Path = REPO_ROOT / "data" / "test"
    testset_name: str = "kab-bench"
    # Version majeure, utilisée dans le nom de fichier (kab-bench.v1.jsonl)
    testset_major: int = 1
    # Données d'amélioration (phase 2) : seule source autorisée pour le few-shot et le RAG
    train_dir: Path = REPO_ROOT / "data" / "train" / "processed"
    results_dir: Path = REPO_ROOT / "data" / "results" / "public"
    models_config: Path = BACKEND_ROOT / "config" / "models.yaml"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Fournisseurs (un fournisseur sans clé est simplement indisponible)
    anthropic_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    mistral_api_key: SecretStr | None = None
    openrouter_api_key: SecretStr | None = None
    ollama_base_url: str = "http://localhost:11434"

    # Détection de langue GlotLID (optionnelle, voir docs/lab.md)
    glotlid_model_path: Path = BACKEND_ROOT / "var" / "models" / "glotlid.bin"

    # Exécution
    max_concurrency_per_provider: int = 2
    max_run_cost_usd: float = 5.0
    max_attempts: int = 4
    request_timeout_s: float = 180.0
