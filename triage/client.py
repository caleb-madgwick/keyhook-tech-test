"""Minimal OpenRouter chat-completions client with retries and cost capture."""

from __future__ import annotations

import asyncio
import json
import random
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from .config import ModelSettings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
RETRYABLE_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}
MAX_BACKOFF_S = 20


class LLMError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


@dataclass
class LLMResponse:
    content: str
    model_used: str | None
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    finish_reason: str | None = None
    cached_input_tokens: int = 0  # input tokens read from the prompt cache (included in input_tokens)


def _int(v: Any) -> int:
    try:
        return int(v or 0)
    except (TypeError, ValueError):
        return 0


def _float(v: Any) -> float:
    try:
        return float(v or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _retry_after(resp: httpx.Response) -> float | None:
    try:
        return min(float(resp.headers.get("retry-after", "")), MAX_BACKOFF_S)
    except ValueError:
        return None


def _caches(settings: ModelSettings) -> bool:
    # Anthropic models need an explicit cache_control breakpoint; OpenAI and DeepSeek cache
    # automatically, so they get the plain request.
    return settings.prompt_cache and any(
        m.startswith("anthropic/") for m in [settings.model, *settings.fallback_models])


def _with_cache_breakpoint(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Send the system prompt as a text block marked for caching. The system prompt is the stable
    prefix; the user turn after it changes every message."""
    return [
        {**m, "content": [{"type": "text", "text": m["content"], "cache_control": {"type": "ephemeral"}}]}
        if m["role"] == "system" and isinstance(m["content"], str) else m
        for m in messages
    ]


@dataclass
class OpenRouterClient:
    api_key: str
    http: httpx.AsyncClient = field(default_factory=lambda: httpx.AsyncClient())

    async def aclose(self) -> None:
        await self.http.aclose()

    async def chat(
        self,
        settings: ModelSettings,
        messages: list[dict[str, str]],
        json_schema: dict | None = None,
        schema_name: str = "output",
    ) -> LLMResponse:
        """One logical call. Retries transport errors, retryable HTTP statuses and malformed
        bodies with backoff (honouring Retry-After); raises LLMError when attempts run out.
        Never raises anything else for network/response problems."""
        body: dict[str, Any] = {
            "model": settings.model,
            "messages": _with_cache_breakpoint(messages) if _caches(settings) else messages,
            "max_tokens": settings.max_tokens,
            "usage": {"include": True},
        }
        if settings.temperature is not None:
            body["temperature"] = settings.temperature
        if settings.fallback_models:
            body["models"] = [settings.model, *settings.fallback_models]
        provider = dict(settings.provider or {})
        if json_schema is not None:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": schema_name, "strict": True, "schema": json_schema},
            }
        else:
            # Without a schema we validate ourselves, so don't restrict providers on it.
            provider.pop("require_parameters", None)
        if provider:
            body["provider"] = provider
        if settings.reasoning is not None:
            body["reasoning"] = settings.reasoning

        headers = {"Authorization": f"Bearer {self.api_key}", "X-Title": "keyhook-triage"}
        last_err, last_status, wait = "unknown error", None, None
        for attempt in range(settings.max_retries + 1):
            if attempt:
                await asyncio.sleep(wait if wait is not None else min(2**attempt + random.random(), MAX_BACKOFF_S))
            wait = None
            start = time.monotonic()
            try:
                resp = await self.http.post(OPENROUTER_URL, json=body, headers=headers, timeout=settings.timeout_s)
            except httpx.HTTPError as e:
                last_err, last_status = f"transport error: {type(e).__name__}: {e}", None
                continue
            latency_ms = int((time.monotonic() - start) * 1000)

            if resp.status_code != 200:
                last_err, last_status = f"HTTP {resp.status_code}: {resp.text[:300]}", resp.status_code
                if resp.status_code in RETRYABLE_STATUS:
                    wait = _retry_after(resp)
                    continue
                raise LLMError(last_err, resp.status_code)  # 400/401/402/403/404: retrying won't help

            try:
                data = resp.json()
            except ValueError:
                last_err = f"non-JSON response body: {resp.text[:200]!r}"
                continue
            if not isinstance(data, dict):
                last_err = f"unexpected response body: {str(data)[:200]}"
                continue
            if data.get("error"):  # OpenRouter can return 200 with an upstream error body
                last_err = f"upstream error: {json.dumps(data['error'])[:300]}"
                continue
            try:
                choice = data["choices"][0]
                content = choice["message"].get("content") or ""
            except (KeyError, IndexError, TypeError, AttributeError):
                last_err = f"malformed response: {json.dumps(data)[:300]}"
                continue
            usage = data.get("usage") or {}
            return LLMResponse(
                content=content,
                model_used=data.get("model"),
                input_tokens=_int(usage.get("prompt_tokens")),
                output_tokens=_int(usage.get("completion_tokens")),
                cost_usd=_float(usage.get("cost")),
                latency_ms=latency_ms,
                finish_reason=choice.get("finish_reason"),
                cached_input_tokens=_int((usage.get("prompt_tokens_details") or {}).get("cached_tokens")),
            )
        raise LLMError(last_err, last_status)
