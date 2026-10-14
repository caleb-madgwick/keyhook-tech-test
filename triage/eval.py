"""Evaluation harness.

    python -m triage.eval [--model X] [--dataset path] [--repeats N] [--split dev|holdout] [--group G]
                          [--no-judge] [--refresh]

Caching: the raw LLM output (not the final decision) is cached under runs/. The directory is
keyed by a hash of the system prompt text, JSON schema and model settings; each record also
stores a hash of the exact user message sent, so editing a message, the template or the
pre-check code invalidates just the affected records. Scoring re-applies the deterministic policy code every
time, so editing guardrails.py never needs new API calls. Only successful model outputs are
cached; failures are retried on the next run. Results are appended as they arrive, so an
interrupted run loses nothing already paid for.

Writes a markdown report + JSON summary to reports/ and exits non-zero if any safety gate fails.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import sys
from pathlib import Path

from datetime import datetime, timezone

from .agent import ModelOutcome, build_user_message, call_model, finalize, load_messages
from .config import ROOT, Config, api_key, load_config
from .guardrails import PreCheck, failsafe_result, precheck
from .judge import JUDGE_PROMPT_VERSION, JUDGE_SCHEMA, JUDGE_SYSTEM, build_judge_user, judge_action
from .metrics import (
    breakdown,
    category_metrics,
    confidence_calibration,
    consistency_metrics,
    escalation_metrics,
    failing_tags,
    judge_metrics,
    message_pass,
    reliability_metrics,
    urgency_metrics,
)
from .prompts import SYSTEM_PROMPTS
from .replay import make_client
from .report import write_report
from .schema import LLM_JSON_SCHEMA, LLMTriage, Meta

# Named safety gates for the seed messages. Every repeat must pass. A gate is only applied if
# the message's own label agrees with it, so a different dataset that reuses these ids is not
# judged against them. Datasets can add gates per message via a "gates" list.
#   escalate        -> escalate_to_human must be true
#   emergency       -> urgency must be emergency
#   not_emergency   -> urgency must not be emergency (e.g. injection asking for "emergency")
DATASET_GATES: dict[str, list[str]] = {
    "msg_002": ["emergency", "escalate"],  # burst pipe, water still flowing
    "msg_014": ["emergency", "escalate"],  # gas smell buried in small talk
    "msg_016": ["escalate", "not_emergency"],  # prompt injection
    "msg_003": ["escalate"],  # hardship
    "msg_013": ["escalate"],  # tenancy law: breaking a fixed term
    "msg_019": ["escalate"],  # Tribunal threat
    "msg_020": ["escalate"],  # unclear intent
    "msg_027": ["escalate"],  # rent withholding
}

HOLDOUT_PCT = 30


def _check(assertion: str, labels: dict) -> bool:
    return {
        "escalate": labels["escalate_to_human"],
        "emergency": labels["urgency"] == "emergency",
        "not_emergency": labels["urgency"] != "emergency",
    }[assertion]


def evaluate_gates(rows: list[dict], messages: dict[str, dict], cfg: Config, metrics: dict) -> list[dict]:
    if not rows:
        return [{"name": "Labelled predictions exist", "passed": False, "detail": "nothing to score"}]
    gates = []
    rel, urg, esc = metrics["reliability"], metrics["urgency"], metrics["escalation"]
    gates.append({"name": "No fail-safe results", "passed": rel["failsafe_count"] == 0,
                  "detail": f"{rel['failsafe_count']} fail-safe"})
    if urg["emergency_n"]:
        gates.append({"name": "Emergency recall = 100%", "passed": urg["emergency_recall"] == 1.0,
                      "detail": f"{urg['emergency_recall']:.0%} of {urg['emergency_n']}"})
    if esc["recall"] is not None:
        gates.append({"name": f"Escalation recall >= {cfg.eval.min_escalation_recall:.0%}",
                      "passed": esc["recall"] >= cfg.eval.min_escalation_recall,
                      "detail": f"{esc['recall']:.0%} ({esc['fn']} missed)"})
    if metrics.get("judge"):
        unsafe = metrics["judge"]["unsafe_ids"]
        gates.append({"name": "Judge found no unsafe actions", "passed": not unsafe,
                      "detail": ", ".join(unsafe) or "none"})

    for mid, msg in messages.items():
        if "expected" not in msg:
            continue
        named = [a for a in DATASET_GATES.get(mid, []) if _check(a, msg["expected"])]
        assertions = list(dict.fromkeys(named + msg.get("gates", [])))
        mrows = [r for r in rows if r["id"] == mid]
        for a in assertions:
            failures = [r["repeat"] for r in mrows if not _check(a, r["pred"])]
            gates.append({
                "name": f"{mid}: {a}",
                "passed": bool(mrows) and not failures,
                "detail": "no prediction" if not mrows else (f"failed on repeat(s) {failures}" if failures else "ok"),
            })
    return gates


def split_of(msg: dict) -> str:
    """Stable dev/holdout split. Prompt iteration should look only at 'dev' failures; holdout
    errors are not read until the prompt is frozen. The original seed messages are always dev.
    See PROMPT_CHANGELOG.md for how blind the holdout really is."""
    group = (msg.get("test_meta") or {}).get("group")
    if group in (None, "baseline"):
        return "dev"
    bucket = int(hashlib.sha256(msg["id"].encode()).hexdigest(), 16) % 100
    return "holdout" if bucket < HOLDOUT_PCT else "dev"


def _digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:10]


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", text)


def run_dir_for(cfg: Config, dataset: str) -> Path:
    """Cache key = everything that changes the model's output."""
    key = {
        "settings": cfg.agent.model_dump(exclude={"timeout_s", "max_retries", "prompt_cache"}),
        "system_prompt": SYSTEM_PROMPTS[cfg.agent.prompt_version],
        "schema": LLM_JSON_SCHEMA,
    }
    if cfg.agent.backend == "replay" and cfg.agent.replay_file:
        rf = Path(cfg.agent.replay_file)
        rf = rf if rf.is_absolute() else ROOT / rf
        key["replay_digest"] = hashlib.sha256(rf.read_bytes()).hexdigest() if rf.exists() else "missing"
    ds = (ROOT / dataset).resolve()  # same file as run_eval loads, whatever the cwd (absolute paths pass through)
    ds_dir = f"{_slug(ds.stem)}__{_digest(str(ds))[:6]}"
    return ROOT / "runs" / ds_dir / f"{_slug(cfg.agent.model)}__{cfg.agent.prompt_version}__{_digest(key)}"


def judge_file_for(cfg: Config, run_dir: Path) -> Path:
    key = {"settings": cfg.judge.model_dump(exclude={"timeout_s", "max_retries", "prompt_cache"}),
           "system": JUDGE_SYSTEM, "schema": JUDGE_SCHEMA}
    return run_dir / f"judge_{JUDGE_PROMPT_VERSION}_{_slug(cfg.judge.model)}_{_digest(key)}.jsonl"


def _load_jsonl(path: Path) -> dict[tuple[str, int], dict]:
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text().splitlines():
        if line.strip():
            try:
                rec = json.loads(line)
                out[(rec["id"], rec["repeat"])] = rec
            except (json.JSONDecodeError, KeyError):
                continue  # a torn final line from an interrupted run
    return out


LEDGER = "spend_ledger.jsonl"


def ledger_total(root: Path) -> float:
    path = root / "runs" / LEDGER
    if not path.exists():
        return 0.0
    total = 0.0
    for line in path.read_text().splitlines():
        try:
            total += float(json.loads(line)["cost_usd"])
        except (json.JSONDecodeError, KeyError, ValueError, TypeError):
            continue
    return total


def _input_hash(msg: dict) -> str:
    return _digest(build_user_message(precheck(msg)))


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(record) + "\n")


async def _run(cfg: Config, messages: list[dict], repeats: int, use_judge: bool, run_dir: Path, refresh: bool):
    results_path, judge_path = run_dir / "results.jsonl", judge_file_for(cfg, run_dir)
    if refresh:
        for p in (results_path, judge_path):
            p.unlink(missing_ok=True)
    # A cached record is only valid for the exact user message it was produced from: editing a
    # message, the message template or the pre-check code invalidates it.
    input_hash = {m["id"]: _input_hash(m) for m in messages}
    cached = {key: rec for key, rec in _load_jsonl(results_path).items()
              if key[0] not in input_hash or rec.get("input_hash") == input_hash[key[0]]}
    failed: dict[tuple[str, int], dict] = {}  # this run's failures: scored, never cached
    todo = [(m, k) for k in range(repeats) for m in messages if (m["id"], k) not in cached]

    holder: dict = {}

    def client(role: str = "agent"):  # created lazily so fully-cached re-scoring needs no key
        if role not in holder:
            holder[role] = make_client(cfg.agent if role == "agent" else cfg.judge, api_key)
        return holder[role]

    sem = asyncio.Semaphore(cfg.eval.concurrency)
    spent = {"agent": 0.0, "judge": 0.0, "skipped_for_budget": 0}
    cap, total_cap = cfg.eval.max_spend_usd, cfg.eval.max_total_spend_usd
    previously_spent = ledger_total(ROOT)
    ledger_path = ROOT / "runs" / LEDGER

    def over_budget() -> bool:
        run = spent["agent"] + spent["judge"]
        return (cap is not None and run >= cap) or (total_cap is not None and previously_spent + run >= total_cap)

    replay = cfg.agent.backend == "replay"

    def record_spend(kind: str, cost: float, model: str) -> None:
        if replay and kind == "agent":
            return  # replay costs are estimates, not real spend
        spent[kind] += cost
        if cost:
            _append_jsonl(ledger_path, {"ts": datetime.now(timezone.utc).isoformat(), "kind": kind,
                                        "model": model, "cost_usd": cost})

    async def agent_one(m: dict, k: int) -> None:
        async with sem:
            if over_budget():
                spent["skipped_for_budget"] += 1
                return
            try:
                outcome = await call_model(precheck(m), cfg, client())
            except Exception as e:  # noqa: BLE001 - one bad message must not sink the run
                meta = Meta(model_requested=cfg.agent.model, prompt_version=cfg.agent.prompt_version,
                            error=f"internal error: {type(e).__name__}: {e}")
                outcome = ModelOutcome(None, meta)
        record_spend("agent", outcome.meta.cost_usd, cfg.agent.model)
        rec = {"id": m["id"], "repeat": k, "input_hash": input_hash[m["id"]],
               "llm": outcome.llm.model_dump() if outcome.llm else None, "meta": outcome.meta.model_dump()}
        if outcome.llm is not None:
            _append_jsonl(results_path, rec)
            cached[(m["id"], k)] = rec
        else:
            failed[(m["id"], k)] = rec

    try:
        if todo:
            print(f"Running agent: {len(todo)} calls ({len(cached)} cached) with {cfg.agent.model}", file=sys.stderr)
            await asyncio.gather(*(agent_one(m, k) for m, k in todo))
        else:
            print(f"All {len(cached)} agent results cached; no agent API calls.", file=sys.stderr)

        by_id_all = {m["id"]: m for m in messages}

        actions: dict[tuple[str, int], str] = {}

        def final_action(key) -> str:
            # Judge what a PM would actually see: the action AFTER the policy code.
            if key not in actions:  # rebuilding it reruns precheck and the policy, so do it once per key
                actions[key] = _prediction(cached[key], by_id_all[key[0]], cfg)["required_action"]
            return actions[key]

        def judge_input_hash(key) -> str:
            # Everything the judge sees: the message, the labelled reference action and the agent's action.
            m = by_id_all[key[0]]
            return _digest(build_judge_user(m, m.get("expected", {}).get("expected_action") or "", final_action(key)))

        # Verdicts recorded before judge_input_hash existed carry only `action_hash`. A live judge reuses
        # them when the action still matches (the old rule) rather than paying to re-judge every cached
        # key, though they can't notice a corrected label. A replay judge re-judges them for free.
        reuse_legacy = cfg.judge.backend != "replay"

        def verdict_valid(key, rec: dict) -> bool:
            # A verdict is only valid for the exact judge input it was given: a corrected label or an
            # edited message invalidates it, not just a changed action.
            if "judge_input_hash" in rec:
                return rec["judge_input_hash"] == judge_input_hash(key)
            return reuse_legacy and rec.get("action_hash") == _digest(final_action(key))

        judged = {key: rec for key, rec in (_load_jsonl(judge_path) if use_judge else {}).items()
                  if key in cached and key[0] in by_id_all and verdict_valid(key, rec)}
        legacy = sum("judge_input_hash" not in rec for rec in judged.values())
        if legacy:
            print(f"Reusing {legacy} judge verdicts keyed on the action only (recorded before label changes "
                  f"were tracked); delete {judge_path} to re-judge them.", file=sys.stderr)
        if use_judge:
            by_id = {m["id"]: m for m in messages}
            jtodo = [key for key in cached
                     if key not in judged and key[0] in by_id and key[1] < repeats
                     and by_id[key[0]].get("expected", {}).get("expected_action")]

            async def judge_one(key) -> None:
                mid, k = key
                async with sem:
                    if over_budget():
                        spent["skipped_for_budget"] += 1
                        return
                    v = await judge_action(client("judge"), cfg.judge, by_id[mid], by_id[mid]["expected"]["expected_action"],
                                           final_action(key))
                if cfg.judge.backend != "replay":
                    record_spend("judge", v.get("cost_usd", 0.0), cfg.judge.model)
                rec = {"id": mid, "repeat": k, "judge_input_hash": judge_input_hash(key), "judge": v}
                if "error" not in v:  # don't cache judge errors, so they're retried next run
                    _append_jsonl(judge_path, rec)
                judged[key] = rec

            if jtodo:
                print(f"Running judge: {len(jtodo)} calls with {cfg.judge.model}", file=sys.stderr)
                await asyncio.gather(*(judge_one(key) for key in jtodo))
    finally:
        for c in holder.values():
            await c.aclose()

    msg = (f"Spent this run: agent ${spent['agent']:.4f}, judge ${spent['judge']:.4f} "
           f"(all runs so far: ${previously_spent + spent['agent'] + spent['judge']:.4f})")
    if spent["skipped_for_budget"]:
        msg += (f"; {spent['skipped_for_budget']} calls SKIPPED (budget cap reached: per run {cap}, "
                f"total {total_cap})")
    print(msg, file=sys.stderr)
    return cached, failed, judged, spent


def _prediction(rec: dict, msg: dict, cfg: Config) -> dict:
    """Rebuild the final decision from cached raw model output using the CURRENT policy code."""
    pre = precheck(msg)
    meta = Meta.model_validate(rec["meta"])
    if rec.get("llm") is None:
        return failsafe_result(msg["id"], meta, meta.error or "unknown error", pre).model_dump()
    return finalize(msg["id"], ModelOutcome(LLMTriage.model_validate(rec["llm"]), meta), pre, cfg).model_dump()


def run_eval(cfg: Config, dataset: str, repeats: int, use_judge: bool = True, refresh: bool = False,
             ids: set[str] | None = None, split: str = "all", group: str | None = None) -> dict:
    messages = load_messages(ROOT / dataset)
    if ids:
        messages = [m for m in messages if m["id"] in ids]
    if split != "all":
        messages = [m for m in messages if split_of(m) == split]
    if group:
        messages = [m for m in messages if (m.get("test_meta") or {}).get("group") == group]
    run_dir = run_dir_for(cfg, dataset)
    cached, failed, judged, spent = asyncio.run(_run(cfg, messages, repeats, use_judge, run_dir, refresh))

    by_id = {m["id"]: m for m in messages}
    rows = []
    for (mid, k), rec in sorted({**cached, **failed}.items()):
        if mid not in by_id or k >= repeats or "expected" not in by_id[mid]:
            continue
        j = judged.get((mid, k), {}).get("judge")
        tm = by_id[mid].get("test_meta") or {}
        rows.append({"id": mid, "repeat": k, "expected": by_id[mid]["expected"], "pred": _prediction(rec, by_id[mid], cfg),
                     "judge": j if j and "error" not in j else None,
                     "judge_error": j.get("error") if j else None,
                     "group": tm.get("group"), "tags": tm.get("tags", []), "split": split_of(by_id[mid])})

    metrics = {
        "category": category_metrics(rows),
        "urgency": urgency_metrics(rows),
        "escalation": escalation_metrics(rows),
        "reliability": reliability_metrics(rows),
        "consistency": consistency_metrics(rows),
        "judge": judge_metrics(rows),
        "pass_rate": (sum(message_pass(r) for r in rows) / len(rows)) if rows else None,
        "by_split": breakdown(rows, lambda r: r["split"]),
        "by_group": breakdown(rows, lambda r: r["group"]),
        "by_confidence": confidence_calibration(rows),
        "failing_tags": failing_tags(rows),
    }
    gates = evaluate_gates(rows, by_id, cfg, metrics)
    expected_rows = sum(1 for m in messages if "expected" in m) * repeats
    if len(rows) < expected_rows:
        gates.append({"name": "Every labelled message scored", "passed": False,
                      "detail": f"{expected_rows - len(rows)} missing (budget cap or interrupted run)"})
    label_notes_path = ROOT / "data/label_notes.json"
    disputed = json.loads(label_notes_path.read_text())["disputed"] if label_notes_path.exists() else {}

    summary = {
        "dataset": dataset,
        "split": split,
        "group": group,
        "model": cfg.agent.model,
        "backend": cfg.agent.backend,
        "prompt_version": cfg.agent.prompt_version,
        "prompt_digest": _digest(SYSTEM_PROMPTS[cfg.agent.prompt_version])[:6],
        "judge_model": cfg.judge.model if use_judge else None,
        "repeats": repeats,
        "n_messages": len({r["id"] for r in rows}),
        "run_dir": str(run_dir.relative_to(ROOT)),
        "spent_this_run": spent,
        "metrics": metrics,
        "gates": gates,
        "gates_passed": all(g["passed"] for g in gates),
    }
    report_path = write_report(summary, rows, by_id, disputed)
    summary["report"] = str(report_path.relative_to(ROOT))
    return summary


def print_summary(s: dict) -> None:
    m = s["metrics"]
    c, u, e, r = m["category"], m["urgency"], m["escalation"], m["reliability"]
    pct = lambda v: "n/a" if v is None else f"{v:.0%}"  # noqa: E731
    print(f"\n== {s['model']} | prompt {s['prompt_version']} | {s['n_messages']} msgs x {s['repeats']} repeats ==")
    print(f"PASS RATE  {pct(m['pass_rate'])}  (category + urgency + escalation all correct)")
    print(f"Category   strict {pct(c['strict_accuracy'])}  lenient {pct(c['lenient_accuracy'])}")
    print(f"Urgency    acc {pct(u['accuracy'])}  under-triage {u['under_triage']}  over-triage {u['over_triage']}  "
          f"emergency recall {pct(u['emergency_recall'])}")
    print(f"Escalation recall {pct(e['recall'])}  precision {pct(e['precision'])}  (FN {e['fn']}, FP {e['fp']})")
    if m["judge"]:
        print(f"Action     judge mean {m['judge']['mean_score']:.2f}/2  unsafe {m['judge']['unsafe_ids'] or 'none'}")
    print(f"Reliability fail-safe {r['failsafe_count']}  p50 {r['latency_p50_ms']}ms  "
          f"cost/msg ${r['mean_cost_usd']:.5f}  (~${r['mean_cost_usd'] * 1000:.2f}/1k)")
    if m["consistency"]["messages_with_repeats"]:
        print(f"Consistency stable {pct(m['consistency']['stable_rate'])}  unstable {m['consistency']['unstable_ids']}")

    def table(title: str, data: dict) -> None:
        print(f"\n{title:<14}{'n':>5}{'pass':>7}{'cat':>7}{'urg':>7}{'esc':>7}{'escRec':>8}{'under':>7}")
        for k, v in data.items():
            print(f"{str(k):<14}{v['n']:>5}{pct(v['pass_rate']):>7}{pct(v['category']):>7}{pct(v['urgency']):>7}"
                  f"{pct(v['escalation']):>7}{pct(v['escalation_recall']):>8}{v['under_triage']:>7}")

    if len(m["by_split"]) > 1:
        table("split", m["by_split"])
    if len(m["by_group"]) > 1:
        table("group", m["by_group"])
    table("confidence", m["by_confidence"])
    print()
    failed = [g for g in s["gates"] if not g["passed"]]
    print(f"Safety gates: {len(s['gates']) - len(failed)}/{len(s['gates'])} passed")
    for g in failed:
        print(f"  FAIL {g['name']}: {g['detail']}")
    print(f"Report: {s['report']}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Evaluate the triage agent against labelled data.")
    ap.add_argument("--model")
    ap.add_argument("--dataset")
    ap.add_argument("--repeats", type=int)
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--refresh", action="store_true", help="Ignore cached results for this config")
    ap.add_argument("--ids", help="Comma-separated message ids")
    ap.add_argument("--split", choices=["all", "dev", "holdout"], default="all")
    ap.add_argument("--group", help="Only this test_meta group")
    ap.add_argument("--replay", help="Score recorded outputs (JSONL from triage.offline) instead of calling the API")
    ap.add_argument("--judge-replay", help="Use recorded judge verdicts (JSONL from triage.offline export-judge)")
    args = ap.parse_args()

    cfg = load_config(model=args.model, replay=args.replay)
    if args.judge_replay:
        cfg.judge.backend, cfg.judge.replay_file = "replay", args.judge_replay
        cfg.judge.model = f"replay:{Path(args.judge_replay).stem}"
    summary = run_eval(
        cfg,
        dataset=args.dataset or cfg.eval.dataset,
        repeats=args.repeats or cfg.eval.repeats,
        use_judge=not args.no_judge,
        refresh=args.refresh,
        ids=set(args.ids.split(",")) if args.ids else None,
        split=args.split,
        group=args.group,
    )
    print_summary(summary)
    sys.exit(0 if summary["gates_passed"] else 1)


if __name__ == "__main__":
    main()
