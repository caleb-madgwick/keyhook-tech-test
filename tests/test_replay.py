"""Replay backend + offline export/import round trip (no network)."""

import asyncio
import json

import pytest

import triage.eval as ev
import triage.offline as off
import triage.report as rep
from triage.agent import triage_message
from triage.config import load_config
from triage.replay import ReplayClient

MSGS = [
    {"id": "a", "subject": "tap", "body": "tap drips",
     "expected": {"category": "maintenance", "also_mentions": [], "urgency": "routine",
                  "escalate_to_human": False, "expected_action": "book plumber"}},
    {"id": "b", "subject": "gas", "body": "gas smell in the kitchen",
     "expected": {"category": "maintenance", "also_mentions": [], "urgency": "emergency",
                  "escalate_to_human": True, "expected_action": "call now"}},
]


def answer(urgency, reasons=()):
    return {"reasoning": "r", "languages": ["en"], "language_mix": "english",
            "issues": [{"summary": "s", "category": "maintenance", "urgency": urgency,
                        "suggested_action": "x", "is_primary": True}],
            "escalation_reasons": list(reasons), "confidence": "high", "review_notes": [],
            "required_action": "do it"}


@pytest.fixture
def setup(tmp_path, monkeypatch):
    for mod in (ev, rep, off):
        monkeypatch.setattr(mod, "ROOT", tmp_path)
    ds = tmp_path / "ds.json"
    ds.write_text(json.dumps({"messages": MSGS}))
    off.export(str(ds), tmp_path / "exp", chunk=1, split="all")
    exported = [json.loads(p.read_text()) for p in sorted((tmp_path / "exp").glob("batch_*.jsonl"))]
    assert all("expected" not in e and set(e) == {"id", "user_message"} for e in exported)  # no label leak
    (tmp_path / "exp" / "answers_0.jsonl").write_text(
        json.dumps({"id": "a", "output": answer("routine")}) + "\n"
        + json.dumps({"id": "b", "output": json.dumps(answer("emergency", ["emergency"]))}) + "\n"
        + "garbage line\n"
    )
    replay = tmp_path / "replay.jsonl"
    off.import_answers(tmp_path / "exp", replay, "test")
    return ds, replay


def test_round_trip_scores_through_full_pipeline(setup):
    ds, replay = setup
    cfg = load_config(replay=str(replay))
    s = ev.run_eval(cfg, str(ds), repeats=1, use_judge=False)
    assert s["backend"] == "replay" and s["metrics"]["pass_rate"] == 1.0 and s["gates_passed"]
    assert s["spent_this_run"]["agent"] == 0  # estimates are not real spend
    assert s["metrics"]["reliability"]["mean_cost_usd"] > 0  # but cost is estimated for the report


def test_changed_message_fails_safe_instead_of_reusing_answer(setup):
    ds, replay = setup
    cfg = load_config(replay=str(replay))
    r = asyncio.run(triage_message(dict(MSGS[0], body="tap drips and ceiling sagging"), cfg, ReplayClient(cfg.agent)))
    assert r.meta.failsafe and "no recorded output" in r.meta.error


def test_replay_file_change_invalidates_cache(setup):
    ds, replay = setup
    cfg = load_config(replay=str(replay))
    before = ev.run_dir_for(cfg, str(ds))
    new = replay.read_text().replace("routine", "urgent")
    assert new != replay.read_text()
    replay.write_text(new)
    assert ev.run_dir_for(cfg, str(ds)) != before


def test_prompt_change_invalidates_replay(setup, monkeypatch):
    ds, replay = setup
    cfg = load_config(replay=str(replay))
    import triage.agent as agent_mod
    monkeypatch.setitem(agent_mod.SYSTEM_PROMPTS, cfg.agent.prompt_version, "a different system prompt")
    r = asyncio.run(triage_message(MSGS[0], cfg, ReplayClient(cfg.agent)))
    assert r.meta.failsafe and "no recorded output" in r.meta.error


def test_judge_replay_round_trip(setup, tmp_path):
    ds, replay = setup
    cfg = load_config(replay=str(replay))
    ev.run_eval(cfg, str(ds), repeats=1, use_judge=False)  # cache agent results
    off.export_judge(str(ds), str(replay), tmp_path / "jexp", chunk=10)
    (tmp_path / "jexp" / "answers_0.jsonl").write_text(
        json.dumps({"id": "a", "output": {"rationale": "fine", "score": 2, "unsafe": False}}) + "\n"
        + json.dumps({"id": "b", "output": {"rationale": "misses call", "score": 1, "unsafe": False}}) + "\n")
    jreplay = tmp_path / "judge.jsonl"
    off.import_answers(tmp_path / "jexp", jreplay, "test-judge")
    cfg.judge.backend, cfg.judge.replay_file = "replay", str(jreplay)
    s = ev.run_eval(cfg, str(ds), repeats=1, use_judge=True)
    assert s["metrics"]["judge"]["mean_score"] == 1.5 and s["spent_this_run"]["judge"] == 0
