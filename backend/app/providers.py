"""Fournisseurs de modèles derrière une interface unique.

Ajouter un fournisseur = écrire une classe avec `available()` et `chat()`, puis l'enregistrer
dans `build_provider`. Les nouvelles tentatives sont gérées par le runner (pas par les SDK),
pour appliquer la même politique à tous les fournisseurs.
"""

import time
from dataclasses import dataclass
from typing import Any, Protocol

import anthropic
import httpx

from app.config import Settings
from app.registry import ModelConfig, ProviderName


@dataclass
class ChatResult:
    text: str
    stop_reason: str | None
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: int


class ProviderError(Exception):
    def __init__(self, message: str, retryable: bool, retry_after: float | None = None):
        super().__init__(message)
        self.retryable = retryable
        self.retry_after = retry_after


class Provider(Protocol):
    def available(self) -> bool: ...

    async def chat(
        self, model: ModelConfig, system: str | None, messages: list[dict[str, str]]
    ) -> ChatResult: ...


def _retry_after(headers: Any) -> float | None:
    try:
        return float(headers.get("retry-after"))
    except (TypeError, ValueError):
        return None


class AnthropicProvider:
    def __init__(self, settings: Settings):
        key = settings.anthropic_api_key
        self._client = (
            anthropic.AsyncAnthropic(
                api_key=key.get_secret_value(),
                max_retries=0,
                timeout=settings.request_timeout_s,
            )
            if key
            else None
        )

    def available(self) -> bool:
        return self._client is not None

    async def chat(self, model, system, messages):
        assert self._client is not None
        params = dict(model.params)
        kwargs: dict[str, Any] = {
            "model": model.model,
            "max_tokens": params.pop("max_tokens", 4096),
            "messages": messages,
        }
        if system:
            kwargs["system"] = system
        if effort := params.pop("effort", None):
            kwargs["output_config"] = {"effort": effort}
        kwargs.update(params)
        # Pas de repli automatique vers un autre modèle en cas de refus : dans un benchmark,
        # la réponse doit toujours provenir du modèle évalué. Un refus est enregistré tel quel.
        started = time.perf_counter()
        try:
            response = await self._client.messages.create(**kwargs)
        except anthropic.RateLimitError as exc:
            raise ProviderError(str(exc), True, _retry_after(exc.response.headers)) from exc
        except anthropic.APIStatusError as exc:
            raise ProviderError(f"{exc.status_code} {exc.message}", exc.status_code >= 500) from exc
        except anthropic.APIConnectionError as exc:
            raise ProviderError(f"connexion : {exc}", True) from exc
        text = "".join(block.text for block in response.content if block.type == "text")
        return ChatResult(
            text=text,
            stop_reason=response.stop_reason,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )


class _HttpProvider:
    def __init__(self, timeout: float):
        self._timeout = timeout

    async def _post(self, url: str, headers: dict[str, str], body: dict[str, Any]):
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, headers=headers, json=body)
        except httpx.HTTPError as exc:
            raise ProviderError(f"connexion : {exc}", True) from exc
        if response.status_code == 429 or response.status_code >= 500:
            raise ProviderError(
                f"{response.status_code} {response.text[:300]}",
                True,
                _retry_after(response.headers),
            )
        if response.status_code >= 400:
            raise ProviderError(f"{response.status_code} {response.text[:300]}", False)
        return response.json(), int((time.perf_counter() - started) * 1000)


class OpenAICompatibleProvider(_HttpProvider):
    """OpenAI, Mistral et OpenRouter exposent la même API « chat/completions »."""

    BASE_URLS = {
        ProviderName.openai: "https://api.openai.com/v1",
        ProviderName.mistral: "https://api.mistral.ai/v1",
        ProviderName.openrouter: "https://openrouter.ai/api/v1",
    }

    def __init__(self, name: ProviderName, api_key: str | None, timeout: float):
        super().__init__(timeout)
        self._url = self.BASE_URLS[name] + "/chat/completions"
        self._key = api_key

    def available(self) -> bool:
        return bool(self._key)

    async def chat(self, model, system, messages):
        all_messages = ([{"role": "system", "content": system}] if system else []) + messages
        body = {"model": model.model, "messages": all_messages, **model.params}
        headers = {"Authorization": f"Bearer {self._key}"}
        data, latency = await self._post(self._url, headers, body)
        choice = data["choices"][0]
        usage = data.get("usage") or {}
        return ChatResult(
            text=choice["message"].get("content") or "",
            stop_reason=choice.get("finish_reason"),
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            latency_ms=latency,
        )


class OllamaProvider(_HttpProvider):
    def __init__(self, base_url: str, timeout: float):
        super().__init__(timeout)
        self._base = base_url.rstrip("/")

    def available(self) -> bool:
        try:
            return httpx.get(f"{self._base}/api/version", timeout=2).status_code == 200
        except httpx.HTTPError:
            return False

    async def chat(self, model, system, messages):
        all_messages = ([{"role": "system", "content": system}] if system else []) + messages
        options = dict(model.params)
        body: dict[str, Any] = {"model": model.model, "messages": all_messages, "stream": False}
        # « think » est un paramètre de premier niveau d'Ollama (modèles à raisonnement)
        if "think" in options:
            body["think"] = options.pop("think")
        body["options"] = options
        data, latency = await self._post(f"{self._base}/api/chat", {}, body)
        return ChatResult(
            text=data["message"]["content"],
            stop_reason=data.get("done_reason"),
            input_tokens=data.get("prompt_eval_count"),
            output_tokens=data.get("eval_count"),
            latency_ms=latency,
        )


class MockProvider:
    """Fournisseur factice pour les tests : renvoie une sortie déterministe sans réseau."""

    def __init__(self):
        self.calls: list[list[dict[str, str]]] = []
        self.failures_before_success = 0

    def available(self) -> bool:
        return True

    async def chat(self, model, system, messages):
        self.calls.append(messages)
        if self.failures_before_success > 0:
            self.failures_before_success -= 1
            raise ProviderError("429 limite atteinte (simulée)", True, 0)
        return ChatResult(
            text=model.params.get("reply", "réponse factice"),
            stop_reason="end_turn",
            input_tokens=10,
            output_tokens=5,
            latency_ms=1,
        )


def _secret(value) -> str | None:
    return value.get_secret_value() if value else None


def build_providers(settings: Settings) -> dict[ProviderName, Provider]:
    timeout = settings.request_timeout_s
    return {
        ProviderName.anthropic: AnthropicProvider(settings),
        ProviderName.openai: OpenAICompatibleProvider(
            ProviderName.openai, _secret(settings.openai_api_key), timeout
        ),
        ProviderName.mistral: OpenAICompatibleProvider(
            ProviderName.mistral, _secret(settings.mistral_api_key), timeout
        ),
        ProviderName.openrouter: OpenAICompatibleProvider(
            ProviderName.openrouter, _secret(settings.openrouter_api_key), timeout
        ),
        ProviderName.ollama: OllamaProvider(settings.ollama_base_url, timeout),
        ProviderName.mock: MockProvider(),
    }
