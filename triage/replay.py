"""Replay backend: serve recorded model outputs instead of calling an API.

Used to run and score the full pipeline (parsing, validation, retries, policy code, metrics)
without spending API budget. Outputs are keyed by a hash of the exact system prompt and user
message the agent would send, so if the prompt, a message, the template or the pre-check code
changes, the recorded output no longer matches and the message fails safe instead of silently reusing a stale answer.

A replay file is JSONL: {"input_key": ..., "id": ..., "content": "<raw model text>", "producer": ...}
See triage/offline.py for producing one (export prompts -> have a model answer -> import).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .client import LLMError, LLMResponse
from .config import ROOT, ModelSettings


def input_key(system_prompt: str, user_message: str) -> str:
    """Identifies one exact model request. Both turns are included: an answer produced under a
    different system prompt must never be replayed as if it came from the current one."""
    return hashlib.sha256(f"{system_prompt}\x00{user_message}".encode()).hexdigest()[:16]


def estimate_tokens(text: str) -> int:
    # ~4 bytes/token for English, ~1 token per CJK char (3 bytes); 3.5 bytes/token is a rough
    # middle. Only used for cost ESTIMATES in replay mode. Newer tokenizers (Claude Haiku 5.5's
    # counts ~30% more tokens than Haiku 4.5's) may run higher; real runs use provider counts.
    return max(1, round(len(text.encode("utf-8")) / 3.5))


def load_replay(path: str | Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for line in Path(path).read_text().splitlines():
        if line.strip():
            rec = json.loads(line)
            out[rec["input_key"]] = rec
    return out


class ReplayClient:
    def __init__(self, settings: ModelSettings):
        if not settings.replay_file:
            raise SystemExit("backend=replay needs agent.replay_file (or --replay path)")
        path = Path(settings.replay_file)
        self.outputs = load_replay(path if path.is_absolute() else ROOT / path)
        self.pricing = settings.replay_pricing

    async def aclose(self) -> None:
        return None

    async def chat(self, settings: ModelSettings, messages: list[dict], json_schema=None, schema_name="output"):
        system = next(m["content"] for m in messages if m["role"] == "system")
        user = next(m["content"] for m in messages if m["role"] == "user")  # the original message turn
        rec = self.outputs.get(input_key(system, user))
        if rec is None:
            raise LLMError("replay: no recorded output for this exact input", status=None)
        content = rec["content"]
        tin = sum(estimate_tokens(m["content"]) for m in messages)
        if json_schema is not None:  # a structured-output schema is billed as input too
            tin += estimate_tokens(json.dumps(json_schema))
        tout = estimate_tokens(content)
        cost = tin * self.pricing.get("input", 0) / 1e6 + tout * self.pricing.get("output", 0) / 1e6
        return LLMResponse(content, f"replay:{rec.get('producer', 'unknown')}", tin, tout, cost, 0, "stop")


def make_client(settings: ModelSettings, api_key_fn):
    if settings.backend == "replay":
        return ReplayClient(settings)
    from .client import OpenRouterClient

    return OpenRouterClient(api_key=api_key_fn())
