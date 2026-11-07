import asyncio
import json

import httpx
import pytest

from app import providers
from app.providers import OllamaProvider, ProviderError
from app.registry import ModelConfig, ProviderName


def _model() -> ModelConfig:
    return ModelConfig(
        key="q",
        label="Q",
        provider=ProviderName.ollama,
        model="qwen3.5:4b",
        params={"temperature": 0, "think": False},
    )


def _patch_transport(monkeypatch, handler):
    real = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real(*args, **kwargs)

    monkeypatch.setattr(providers.httpx, "AsyncClient", factory)


def test_ollama_streams_and_joins_chunks(monkeypatch):
    seen = {}

    def handler(request):
        seen["body"] = json.loads(request.content)
        lines = [
            {"message": {"content": "abc "}, "done": False},
            {"message": {"content": "def"}, "done": False},
            {
                "message": {"content": ""},
                "done": True,
                "done_reason": "stop",
                "prompt_eval_count": 12,
                "eval_count": 3,
            },
        ]
        return httpx.Response(200, text="\n".join(json.dumps(x) for x in lines))

    _patch_transport(monkeypatch, handler)
    result = asyncio.run(
        OllamaProvider("http://x", 5).chat(_model(), None, [{"role": "user", "content": "salut"}])
    )
    assert seen["body"]["stream"] is True
    assert seen["body"]["think"] is False
    assert "think" not in seen["body"]["options"]
    assert result.text == "abc def"
    assert (result.stop_reason, result.input_tokens, result.output_tokens) == ("stop", 12, 3)


def test_ollama_stream_cut_before_done_is_retryable(monkeypatch):
    def handler(request):
        return httpx.Response(200, text=json.dumps({"message": {"content": "ab"}, "done": False}))

    _patch_transport(monkeypatch, handler)
    with pytest.raises(ProviderError) as err:
        asyncio.run(OllamaProvider("http://x", 5).chat(_model(), None, []))
    assert err.value.retryable


def test_ollama_server_error_is_retryable(monkeypatch):
    _patch_transport(monkeypatch, lambda request: httpx.Response(524, text="timeout"))
    with pytest.raises(ProviderError) as err:
        asyncio.run(OllamaProvider("http://x", 5).chat(_model(), None, []))
    assert err.value.retryable
