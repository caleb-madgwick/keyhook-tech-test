"""Eval harness caching and gate behaviour, with the model call stubbed (no network)."""

import json

import pytest

import triage.eval as ev
import triage.report as rep
from triage.agent import ModelOutcome
from triage.config import load_config
from triage.schema import Issue, LLMTriage, Meta

MSGS = [
    {"id": "a", "subject": "tap", "body": "tap drips",
     "expected": {"category": "maintenance", "also_mentions": [], "urgency": "routine",
                  "escalate_to_human": False, "expected_action": "book plumber"}},
    {"id": "b", "subject": "gas", "body": "gas smell",
     "expected": {"category": "maintenance", "also_mentions": [], "urgency": "emergency",
                  "escalate_to_human": True, "expected_action": "call now"}},
]


def outcome(urgency="routine"):
    llm = LLMTriage(reasoning="r", languages=["en"], language_mix="english",
                    issues=[Issue(summary="s", category="maintenance", urgency=urgency, suggested_action="x",
                                  is_primary=True)],
                    escalation_reasons=[], confidence="high", review_notes=[],
                    required_action="do it")
    return ModelOutcome(llm, Meta(model_requested="stub", prompt_version="v2", cost_usd=0.001))


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(ev, "ROOT", tmp_path)
    monkeypatch.setattr(rep, "ROOT", tmp_path)
    monkeypatch.setattr(ev, "api_key", lambda: "k")
    ds = tmp_path / "ds.json"
    ds.write_text(json.dumps({"messages": MSGS}))
    calls = []

    def install(behaviour):
        async def fake_call_model(pre, cfg, client):
            calls.append(pre.msg["id"])
            return behaviour(pre.msg["id"])
        monkeypatch.setattr(ev, "call_model", fake_call_model)

    return load_config(model="stub/model"), str(ds), install, calls


def test_failures_not_cached_and_retried_next_run(env):
    cfg, ds, install, calls = env
    install(lambda mid: outcome("emergency") if mid == "b" else ModelOutcome(None, Meta(
        model_requested="stub", prompt_version="v2", error="HTTP 503")))
    s1 = ev.run_eval(cfg, ds, repeats=1, use_judge=False)
    assert s1["metrics"]["reliability"]["failsafe_count"] == 1
    assert not s1["gates_passed"]
    cached = (ev.run_dir_for(cfg, ds) / "results.jsonl").read_text().splitlines()
    assert [json.loads(line)["id"] for line in cached] == ["b"]

    calls.clear()
    install(lambda mid: outcome("routine"))
    s2 = ev.run_eval(cfg, ds, repeats=1, use_judge=False)
    assert calls == ["a"]  # only the failed one is re-run
    assert s2["metrics"]["reliability"]["failsafe_count"] == 0 and s2["gates_passed"]


def test_policy_change_applies_without_new_calls(env, monkeypatch):
    cfg, ds, install, calls = env
    install(lambda mid: outcome("emergency" if mid == "b" else "routine"))
    ev.run_eval(cfg, ds, repeats=1, use_judge=False)
    calls.clear()
    # Simulate a policy-code change: escalate everything.
    real = ev.finalize

    def stricter(mid, oc, pre, cfg):
        r = real(mid, oc, pre, cfg)
        r.escalate_to_human = True
        return r
    monkeypatch.setattr(ev, "finalize", stricter)
    s = ev.run_eval(cfg, ds, repeats=1, use_judge=False)
    assert calls == []  # fully cached
    assert s["metrics"]["escalation"]["fp"] == 1  # but the new policy was applied


def test_cache_key_changes_with_prompt_text(env, monkeypatch):
    cfg, ds, *_ = env
    before = ev.run_dir_for(cfg, ds)
    monkeypatch.setitem(ev.SYSTEM_PROMPTS, cfg.agent.prompt_version, "edited prompt, same version label")
    assert ev.run_dir_for(cfg, ds) != before


def test_no_rows_fails_gates():
    cfg = load_config()
    assert ev.evaluate_gates([], {}, cfg, {})[0]["passed"] is False


def test_named_gate_skipped_when_label_disagrees():
    cfg = load_config()
    other_msg_002 = {"msg_002": {"id": "msg_002", "expected": {"urgency": "routine", "escalate_to_human": False}}}
    row = {"id": "msg_002", "repeat": 0, "pred": {"urgency": "routine", "escalate_to_human": False}}
    metrics = {"reliability": {"failsafe_count": 0}, "urgency": {"emergency_n": 0},
               "escalation": {"recall": None}, "judge": None}
    names = [g["name"] for g in ev.evaluate_gates([row], other_msg_002, cfg, metrics)]
    assert not any(n.startswith("msg_002") for n in names)


def test_editing_message_body_invalidates_only_that_record(env):
    cfg, ds, install, calls = env
    install(lambda mid: outcome("emergency" if mid == "b" else "routine"))
    ev.run_eval(cfg, ds, repeats=1, use_judge=False)
    edited = [dict(MSGS[0], body="tap drips AND the ceiling is wet"), MSGS[1]]
    open(ds, "w").write(json.dumps({"messages": edited}))
    calls.clear()
    ev.run_eval(cfg, ds, repeats=1, use_judge=False)
    assert calls == ["a"]


def test_total_spend_ledger_caps_across_runs(env):
    cfg, ds, install, calls = env
    cfg.eval.max_total_spend_usd = 0.0015  # first call costs 0.001, second pushes past the cap
    cfg.eval.concurrency = 1
    install(lambda mid: outcome("emergency" if mid == "b" else "routine"))
    s = ev.run_eval(cfg, ds, repeats=1, use_judge=False)
    assert s["spent_this_run"]["skipped_for_budget"] == 0  # 0.001 < cap when 2nd call starts
    assert ev.ledger_total(ev.ROOT) > 0
    calls.clear()
    (ev.run_dir_for(cfg, ds) / "results.jsonl").unlink()
    s = ev.run_eval(cfg, ds, repeats=1, use_judge=False)
    assert calls == [] and s["spent_this_run"]["skipped_for_budget"] == 2
    assert not s["gates_passed"]


def test_failsafe_keyword_floor_not_counted_as_caught(env):
    cfg, ds, install, calls = env
    install(lambda mid: ModelOutcome(None, Meta(model_requested="s", prompt_version="v2", error="down")))
    s = ev.run_eval(cfg, ds, repeats=1, use_judge=False)
    assert s["metrics"]["urgency"]["emergency_recall"] == 0.0
