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


def test_judge_verdict_invalidated_when_reference_label_changes(env, monkeypatch):
    cfg, ds, install, calls = env
    install(lambda mid: outcome("emergency" if mid == "b" else "routine"))
    judged = []

    async def fake_judge(client, settings, msg, expected_action, proposed):
        judged.append((msg["id"], expected_action))
        return {"rationale": "ok", "score": 2, "unsafe": False, "cost_usd": 0.0}

    monkeypatch.setattr(ev, "judge_action", fake_judge)
    ev.run_eval(cfg, ds, repeats=1, use_judge=True)
    assert sorted(judged) == [("a", "book plumber"), ("b", "call now")]

    judged.clear()
    ev.run_eval(cfg, ds, repeats=1, use_judge=True)
    assert judged == []  # nothing changed: verdicts reused

    relabelled = [dict(MSGS[0], expected=dict(MSGS[0]["expected"], expected_action="book plumber today")), MSGS[1]]
    open(ds, "w").write(json.dumps({"messages": relabelled}))
    ev.run_eval(cfg, ds, repeats=1, use_judge=True)
    assert judged == [("a", "book plumber today")]  # only the relabelled message is re-judged


@pytest.mark.parametrize("backend,rejudged", [("openrouter", []), ("replay", ["a", "b"])])
def test_legacy_action_hash_verdicts(env, monkeypatch, backend, rejudged):
    # Verdicts written before judge_input_hash existed: a live judge reuses them rather than paying again.
    cfg, ds, install, calls = env
    cfg.judge.backend = backend
    install(lambda mid: outcome("emergency" if mid == "b" else "routine"))
    ev.run_eval(cfg, ds, repeats=1, use_judge=False)
    run_dir = ev.run_dir_for(cfg, ds)
    msgs = {m["id"]: m for m in MSGS}
    cached = ev._load_jsonl(run_dir / "results.jsonl")
    with ev.judge_file_for(cfg, run_dir).open("w") as f:
        for (mid, k), rec in cached.items():
            action = ev._prediction(rec, msgs[mid], cfg)["required_action"]
            f.write(json.dumps({"id": mid, "repeat": k, "action_hash": ev._digest(action),
                                "judge": {"rationale": "old", "score": 2, "unsafe": False}}) + "\n")
    judged = []

    async def fake_judge(client, settings, msg, expected_action, proposed):
        judged.append(msg["id"])
        return {"rationale": "new", "score": 2, "unsafe": False, "cost_usd": 0.0}

    monkeypatch.setattr(ev, "judge_action", fake_judge)
    monkeypatch.setattr(ev, "make_client", lambda *a, **k: _NullClient())
    ev.run_eval(cfg, ds, repeats=1, use_judge=True)
    assert sorted(judged) == rejudged


class _NullClient:
    async def aclose(self):
        pass


def test_run_dir_independent_of_cwd(env, tmp_path, monkeypatch):
    cfg, ds, install, calls = env
    expected = ev.run_dir_for(cfg, ds)  # absolute path
    monkeypatch.chdir(tmp_path.parent)
    assert ev.run_dir_for(cfg, "ds.json") == expected  # relative to the repo root, not the cwd


def test_validate_labels_normalises_case_and_reports_bad_values():
    msgs = [{"id": "a", "expected": {"category": " Maintenance", "urgency": "URGENT", "also_mentions": ["Enquiry"],
                                     "escalate_to_human": False}}]
    ev.validate_labels(msgs)
    assert msgs[0]["expected"]["category"] == "maintenance" and msgs[0]["expected"]["urgency"] == "urgent"
    assert msgs[0]["expected"]["also_mentions"] == ["enquiry"]
    bad = [{"id": "b", "expected": {"category": "repairs", "urgency": "high", "escalate_to_human": "yes"}},
           {"id": "c"}]  # unlabelled messages are fine
    with pytest.raises(SystemExit) as e:
        ev.validate_labels(bad)
    assert "3 label problem(s)" in str(e.value) and "category='repairs'" in str(e.value)


def test_label_notes_only_apply_to_the_original_message(tmp_path, monkeypatch):
    monkeypatch.setattr(ev, "ROOT", tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "data/label_notes.json").write_text(json.dumps({"disputed": {"msg_006": "debatable"}}))
    (tmp_path / "tenant_emails_test_suite.json").write_text(
        json.dumps({"messages": [{"id": "msg_006", "body": "heat pump broken"}]}))
    assert ev.label_notes_for({"msg_006": {"id": "msg_006", "body": "heat pump broken"}}) == {"msg_006": "debatable"}
    assert ev.label_notes_for({"msg_006": {"id": "msg_006", "body": "a different message"}}) == {}


def test_baseline_runs(capsys, monkeypatch):
    from triage import baseline
    monkeypatch.setattr("sys.argv", ["baseline", "--dataset", "tenant_emails.json"])
    baseline.main()
    assert "pass rate" in capsys.readouterr().out
