"""Registre des modèles, chargé depuis config/models.yaml."""

from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, model_validator


class ProviderName(StrEnum):
    anthropic = "anthropic"
    openai = "openai"
    mistral = "mistral"
    openrouter = "openrouter"
    ollama = "ollama"
    mock = "mock"  # utilisé par les tests automatisés uniquement


class Variant(StrEnum):
    base = "base"
    fewshot = "fewshot"
    rag = "rag"
    finetuned = "finetuned"


class Pricing(BaseModel):
    input: float  # USD par million de tokens
    output: float


class ModelConfig(BaseModel):
    key: str
    label: str
    provider: ProviderName
    model: str
    params: dict[str, Any] = Field(default_factory=dict)
    pricing: Pricing | None = None
    base: str | None = None
    variant: Variant = Variant.base
    variant_params: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _variant_needs_base(self):
        if self.variant != Variant.base and not self.base:
            raise ValueError(f"{self.key} : une variante doit indiquer son modèle de base (base)")
        return self

    def cost(self, input_tokens: int | None, output_tokens: int | None) -> float | None:
        if self.pricing is None or input_tokens is None or output_tokens is None:
            return None
        return (input_tokens * self.pricing.input + output_tokens * self.pricing.output) / 1e6


def load_registry(path: Path) -> dict[str, ModelConfig]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    models = [ModelConfig.model_validate(entry) for entry in data.get("models", [])]
    registry = {m.key: m for m in models}
    if len(registry) != len(models):
        raise ValueError("clé de modèle en double dans models.yaml")
    for m in models:
        if m.base and m.base not in registry:
            raise ValueError(f"{m.key} : modèle de base inconnu « {m.base} »")
    return registry
