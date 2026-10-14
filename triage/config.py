"""Load config.yaml into typed settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent


class ModelSettings(BaseModel):
    model: str
    fallback_models: list[str] = Field(default_factory=list)
    # None = don't send it. Claude Haiku 5.5 / Sonnet 5.5 and GPT-6 don't accept temperature on
    # OpenRouter, and with provider.require_parameters a request that sets it finds no provider.
    temperature: float | None = None
    max_tokens: int = 1500
    timeout_s: float = 60
    max_retries: int = 2
    prompt_version: str = "v1"
    reasoning: dict[str, Any] | None = None
    provider: dict[str, Any] | None = None
    # Mark the system prompt as a prompt-cache breakpoint (Anthropic models only; the other
    # compared providers cache automatically). Doesn't change model output.
    prompt_cache: bool = False
    # "openrouter" calls the API. "replay" reads recorded model outputs from replay_file (see
    # triage/replay.py) so the whole pipeline can be run and scored without spending anything.
    backend: Literal["openrouter", "replay"] = "openrouter"
    replay_file: str | None = None
    # USD per 1M tokens, used only to ESTIMATE cost in replay mode (tokens are estimated too).
    replay_pricing: dict[str, float] = Field(default_factory=lambda: {"input": 0.10, "output": 0.50})

    def use_replay(self, replay_file: str) -> None:
        """Serve recorded outputs from replay_file instead of calling the API."""
        self.backend = "replay"
        self.replay_file = replay_file
        self.model = f"replay:{Path(replay_file).stem}"


class EvalSettings(BaseModel):
    dataset: str = "tenant_emails_test_suite.json"
    repeats: int = 1
    concurrency: int = 5
    min_escalation_recall: float = 0.9
    # Stop launching new API calls once this much has been spent in one eval run (None = no cap).
    max_spend_usd: float | None = 3.0
    # Cap across ALL runs ever recorded in runs/spend_ledger.jsonl (protects the whole key,
    # e.g. when compare.py runs several models). None = no cap.
    max_total_spend_usd: float | None = 10.0
    compare_models: list[str] = Field(default_factory=list)


class PolicySettings(BaseModel):
    # Model self-reported confidence levels that force human review. Applied in code at scoring
    # time, so changing it never needs new model calls.
    escalate_on_confidence: list[Literal["low", "medium"]] = Field(default_factory=lambda: ["low", "medium"])


class Config(BaseModel):
    agent: ModelSettings
    judge: ModelSettings
    eval: EvalSettings = Field(default_factory=EvalSettings)
    policy: PolicySettings = Field(default_factory=PolicySettings)


def load_config(path: str | Path = ROOT / "config.yaml", model: str | None = None,
                replay: str | None = None) -> Config:
    raw = yaml.safe_load(Path(path).read_text())
    cfg = Config.model_validate(raw)
    override = model or os.environ.get("TRIAGE_MODEL")
    if override:
        cfg.agent.model = override
    if replay:
        cfg.agent.use_replay(replay)
    return cfg


def api_key() -> str:
    load_dotenv(ROOT / ".env")
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise SystemExit("OPENROUTER_API_KEY is not set. Copy .env.example to .env and add your key.")
    return key
