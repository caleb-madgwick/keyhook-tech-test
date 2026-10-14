"""OpenRouter client against a mocked HTTP transport (no network)."""

import asyncio
import json

import httpx
import pytest

from triage import client as client_mod
from triage.client import LLMError, OpenRouterClient
from triage.config import ModelSettings

SETTINGS = ModelSettings(model="m", max_retries=2)
OK = {"model": "m-actual", "choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}],
      "usage": {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.001}}


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    async def fast(_):
        return None
    monkeypatch.setattr(client_mod.asyncio, "sleep", fast)


def run(responses, settings=SETTINGS, **kw):
    seen = []

    def handler(request):
        seen.append(json.loads(request.content))
        r = responses.pop(0)
        return r if isinstance(r, httpx.Response) else httpx.Response(200, json=r)

    c = OpenRouterClient(api_key="k", http=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    try:
        return asyncio.run(c.chat(settings, [{"role": "user", "content": "x"}], **kw)), seen
    finally:
        asyncio.run(c.aclose())


def test_success_reads_usage_and_cost():
    r, _ = run([OK])
    assert (r.input_tokens, r.output_tokens, r.cost_usd, r.model_used) == (10, 5, 0.001, "m-actual")


def test_null_usage_is_zero_not_crash():
    r, _ = run([{**OK, "usage": {"prompt_tokens": None, "completion_tokens": None, "cost": None}}])
    assert (r.input_tokens, r.output_tokens, r.cost_usd) == (0, 0, 0.0)


def test_html_body_with_200_is_retried():
    r, seen = run([httpx.Response(200, text="<html>gateway</html>"), OK])
    assert len(seen) == 2 and r.cost_usd == 0.001


def test_429_retried_then_success():
    r, seen = run([httpx.Response(429, headers={"retry-after": "1"}, text="slow down"), OK])
    assert len(seen) == 2


def test_404_not_retried_and_status_exposed():
    with pytest.raises(LLMError) as e:
        run([httpx.Response(404, text="No endpoints found that support response_format")])
    assert e.value.status == 404


def test_exhausted_retries_raise_llm_error():
    with pytest.raises(LLMError):
        run([httpx.Response(503, text="x")] * 3)


def test_no_schema_drops_require_parameters():
    s = ModelSettings(model="m", provider={"require_parameters": True, "data_collection": "deny"})
    _, seen = run([OK], settings=s, json_schema=None)
    assert "response_format" not in seen[0] and seen[0]["provider"] == {"data_collection": "deny"}


def test_temperature_omitted_when_unset_and_sent_when_set():
    _, seen = run([OK])
    assert "temperature" not in seen[0]  # Haiku 5.5 / Sonnet 5.5 / GPT-6 reject it on OpenRouter
    _, seen = run([OK], settings=ModelSettings(model="m", temperature=0))
    assert seen[0]["temperature"] == 0


def run_messages(settings, messages):
    seen = []

    def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(200, json=OK)

    c = OpenRouterClient(api_key="k", http=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    try:
        return asyncio.run(c.chat(settings, messages)), seen
    finally:
        asyncio.run(c.aclose())


MSGS = [{"role": "system", "content": "rules"}, {"role": "user", "content": "x"}]


def test_prompt_cache_marks_system_prompt_for_anthropic_models_only():
    _, seen = run_messages(ModelSettings(model="anthropic/claude-haiku-5.5", prompt_cache=True), MSGS)
    assert seen[0]["messages"][0]["content"] == [
        {"type": "text", "text": "rules", "cache_control": {"type": "ephemeral"}}]
    assert seen[0]["messages"][1] == MSGS[1]  # the per-message user turn is never cached
    _, seen = run_messages(ModelSettings(model="openai/gpt-6-luna", prompt_cache=True), MSGS)
    assert seen[0]["messages"] == MSGS  # caches automatically; plain request
    _, seen = run_messages(ModelSettings(model="anthropic/claude-haiku-5.5"), MSGS)
    assert seen[0]["messages"] == MSGS  # off by default


def test_cached_tokens_read_from_usage():
    usage = {**OK["usage"], "prompt_tokens_details": {"cached_tokens": 8}}
    r, _ = run([{**OK, "usage": usage}])
    assert (r.input_tokens, r.cached_input_tokens) == (10, 8)
