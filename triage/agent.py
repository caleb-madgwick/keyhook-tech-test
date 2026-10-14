"""Triage agent: one structured LLM call per message, wrapped in deterministic guardrails.

CLI:
    python -m triage.agent --input tenant_emails.json [--out results.jsonl] [--model X] [--ids msg_001,msg_014]

Input is either {"messages": [...]} or a bare list of messages with subject / body (id,
from_name and received_at optional). Any `expected` field is ignored here.

Pipeline per message:  precheck (code) -> call_model (LLM) -> finalize (code policy)
The eval harness caches call_model's raw output and re-runs finalize at scoring time, so
changes to the policy code take effect without paying for new model calls.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from .client import LLMError, OpenRouterClient
from .config import Config, api_key, load_config
from .guardrails import PreCheck, apply_policy, failsafe_result, format_message_for_llm, precheck
from .prompts import SYSTEM_PROMPTS
from .replay import make_client
from .schema import LLM_JSON_SCHEMA, LLMTriage, Meta, TriageResult

# 404 ("no endpoints support the requested parameters") or a 400 that complains about the
# schema, when strict json_schema is requested: retry once without it and validate ourselves.
SCHEMA_ERROR_HINT = re.compile(r"response_format|json_schema|structured|schema", re.IGNORECASE)


def _schema_rejected(e: LLMError) -> bool:
    return e.status == 404 or (e.status == 400 and bool(SCHEMA_ERROR_HINT.search(str(e))))


def build_user_message(pre: PreCheck) -> str:
    """The exact user turn sent to the model (the eval cache keys on a hash of this)."""
    return format_message_for_llm(pre.msg, pre.notes(), pre.decoded_blobs)


@dataclass
class ModelOutcome:
    llm: LLMTriage | None  # None when the model never produced valid output
    meta: Meta


def _strip_fences(text: str) -> str:
    text = text.strip()
    m = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    return m.group(1) if m else text


def _short_errors(e: ValidationError) -> str:
    return "; ".join(f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors()[:5])


async def call_model(pre: PreCheck, cfg: Config, client: OpenRouterClient) -> ModelOutcome:
    """At most 3 model calls: the first, one fallback if the provider rejects strict schemas,
    and one corrective retry if the output is invalid. (Transport retries happen in client.)"""
    settings = cfg.agent
    meta = Meta(model_requested=settings.model, prompt_version=settings.prompt_version)
    system = SYSTEM_PROMPTS[settings.prompt_version]
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": build_user_message(pre)},
    ]
    use_schema, corrected = True, False
    error = "no attempt made"

    for _ in range(3):
        meta.attempts += 1
        try:
            resp = await client.chat(
                settings, messages, json_schema=LLM_JSON_SCHEMA if use_schema else None, schema_name="triage"
            )
        except LLMError as e:
            error = str(e)
            if use_schema and _schema_rejected(e):
                use_schema = False
                meta.structured_fallback = True
                messages[0] = {
                    "role": "system",
                    "content": f"{system}\n\nReturn ONLY a JSON object (no prose, no code fences) matching "
                    f"this JSON schema:\n{json.dumps(LLM_JSON_SCHEMA)}",
                }
                continue
            break

        meta.model_used = resp.model_used
        meta.finish_reason = resp.finish_reason
        meta.input_tokens += resp.input_tokens
        meta.output_tokens += resp.output_tokens
        meta.cost_usd += resp.cost_usd
        meta.latency_ms += resp.latency_ms

        if resp.finish_reason == "length":
            error = f"output truncated at max_tokens={settings.max_tokens}"
            break  # a corrective retry would hit the same limit
        try:
            return ModelOutcome(LLMTriage.model_validate_json(_strip_fences(resp.content)), meta)
        except ValidationError as e:
            error = f"invalid model output: {_short_errors(e)} | raw: {resp.content[:200]!r}"
            if corrected:
                break
            corrected = True
            messages += [
                {"role": "assistant", "content": resp.content[:4000]},
                {"role": "user", "content": f"That output was invalid ({_short_errors(e)}). "
                 "Reply with only the corrected JSON object."},
            ]

    meta.error = error
    return ModelOutcome(None, meta)


def finalize(message_id: str, outcome: ModelOutcome, pre: PreCheck, cfg: Config) -> TriageResult:
    if outcome.llm is None:
        return failsafe_result(message_id, outcome.meta, outcome.meta.error or "unknown error", pre)
    return apply_policy(message_id, outcome.llm, pre, outcome.meta, cfg.policy.escalate_on_confidence)


async def triage_message(msg: dict, cfg: Config, client: OpenRouterClient) -> TriageResult:
    """Never raises: any unexpected error becomes a fail-safe (escalated) result."""
    message_id = str(msg.get("id", "unknown"))
    try:
        pre = precheck(msg)
        return finalize(message_id, await call_model(pre, cfg, client), pre, cfg)
    except Exception as e:  # noqa: BLE001 - last line of defence; a crash must not drop a message
        meta = Meta(model_requested=cfg.agent.model, prompt_version=cfg.agent.prompt_version)
        return failsafe_result(message_id, meta, f"internal error: {type(e).__name__}: {e}", PreCheck(msg=msg))


async def triage_batch(messages: list[dict], cfg: Config, concurrency: int | None = None) -> list[TriageResult]:
    client = make_client(cfg.agent, api_key)
    sem = asyncio.Semaphore(concurrency or cfg.eval.concurrency)

    async def one(m: dict) -> TriageResult:
        async with sem:
            return await triage_message(m, cfg, client)

    try:
        return await asyncio.gather(*(one(m) for m in messages))
    finally:
        await client.aclose()


def load_messages(path: str | Path) -> list[dict]:
    data = json.loads(Path(path).read_text())
    messages = data["messages"] if isinstance(data, dict) else data
    for n, m in enumerate(messages):
        m.setdefault("id", f"row_{n:04d}")  # ids are needed for caching and reporting
    return messages


def main() -> None:
    ap = argparse.ArgumentParser(description="Triage tenant messages.")
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", help="JSONL output path (default: stdout)")
    ap.add_argument("--config", default=None)
    ap.add_argument("--model", default=None, help="Override agent model")
    ap.add_argument("--ids", default=None, help="Comma-separated message ids to run")
    ap.add_argument("--replay", default=None, help="Use recorded outputs (JSONL) instead of the API")
    args = ap.parse_args()

    kw = {"model": args.model, "replay": args.replay}
    cfg = load_config(args.config, **kw) if args.config else load_config(**kw)
    messages = load_messages(args.input)
    if args.ids:
        wanted = set(args.ids.split(","))
        messages = [m for m in messages if m.get("id") in wanted]

    results = asyncio.run(triage_batch(messages, cfg))

    lines = [r.model_dump_json() for r in results]
    if args.out:
        Path(args.out).write_text("\n".join(lines) + "\n")
    else:
        print("\n".join(lines))

    cost = sum(r.meta.cost_usd for r in results)
    print(f"\n{'id':<10} {'category':<12} {'urgency':<10} {'esc':<5} {'conf':<7} reasons", file=sys.stderr)
    for r in results:
        flag = " FAILSAFE" if r.meta.failsafe else ""
        print(
            f"{r.message_id:<10} {r.category:<12} {r.urgency:<10} {str(r.escalate_to_human):<5} {r.confidence:<7} "
            f"{','.join(r.escalation_reasons)}{flag}",
            file=sys.stderr,
        )
    print(f"\n{len(results)} messages, model={cfg.agent.model}, cost=${cost:.4f}", file=sys.stderr)


if __name__ == "__main__":
    main()
