"""Configuration du labo, lue depuis les variables d'environnement (et .env en local)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    database_url: str = "sqlite:///./var/lab.db"
    # Dossier du jeu de test versionné dans Git (source de vérité)
    testset_dir: Path = REPO_ROOT / "data" / "test"
    testset_name: str = "kab-bench"
    # Version majeure, utilisée dans le nom de fichier (kab-bench.v1.jsonl)
    testset_major: int = 1
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
