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
