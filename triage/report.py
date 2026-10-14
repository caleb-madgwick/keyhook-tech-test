"""Markdown report for one eval run (plus a JSON summary used by the model comparison)."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .config import ROOT
from .metrics import DECISION_FIELDS, per_message_errors
from .schema import CATEGORIES, URGENCIES


def pct(v) -> str:
    return "n/a" if v is None else f"{v:.0%}"


def slug(text: str) -> str:
    """Make text safe for a file name."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", text)


def _matrix(title: str, m: dict, labels: tuple[str, ...]) -> list[str]:
    out = [f"**{title}** (rows = expected, columns = predicted)", "",
           "| expected \\ predicted | " + " | ".join(labels) + " |",
           "|---|" + "---|" * len(labels)]
    for e in labels:
        cells = [str(m[e][p]) if m[e][p] else "·" for p in labels]
        cells = [f"**{c}**" if e == p and c != "·" else c for c, p in zip(cells, labels)]
        out.append(f"| {e} | " + " | ".join(cells) + " |")
    return out + [""]


def _slices(title: str, data: dict) -> list[str]:
    out = [f"**{title}**", "", "| slice | n | pass | category | urgency | escalation | esc. recall | under-triage |",
           "|---|---|---|---|---|---|---|---|"]
    for k, v in data.items():
        out.append(f"| {k} | {v['n']} | {pct(v['pass_rate'])} | {pct(v['category'])} | {pct(v['urgency'])} | "
                   f"{pct(v['escalation'])} | {pct(v['escalation_recall'])} | {v['under_triage']} |")
    return out + [""]


def report_paths(summary: dict) -> tuple[Path, Path]:
    stem = f"{Path(summary['dataset']).stem}__{slug(summary['model'])}__{summary['prompt_version']}-{summary.get('prompt_digest', '')}"
    if summary.get("split", "all") != "all":
        stem += f"__{summary['split']}"
    if summary.get("group"):
        stem += f"__{summary['group']}"
    # A subset or multi-repeat run gets its own file, so it never overwrites the full single-repeat report
    # (an --ids smoke run once replaced the 349-message Haiku report with a 1-message one).
    if summary.get("ids"):
        ids = sorted(summary["ids"])
        stem += f"__ids-{len(ids)}-{hashlib.sha256(','.join(ids).encode()).hexdigest()[:6]}"
    if summary.get("repeats", 1) > 1:
        stem += f"__x{summary['repeats']}"
    return ROOT / "reports" / f"{stem}.md", ROOT / "reports" / f"{stem}.json"


def is_blind_dataset(dataset: str) -> bool:
    return "blind" in Path(dataset).stem.lower()


def write_report(summary: dict, rows: list[dict], messages: dict[str, dict], disputed: dict[str, str]) -> Path:
    md_path, json_path = report_paths(summary)
    md_path.parent.mkdir(exist_ok=True)
    m = summary["metrics"]
    c, u, e, r, cons, j = (m["category"], m["urgency"], m["escalation"], m["reliability"],
                           m["consistency"], m["judge"])

    L = [
        f"# Eval report: `{summary['model']}` / prompt `{summary['prompt_version']}`",
        "",
        f"- Dataset: `{summary['dataset']}`, {summary['n_messages']} labelled messages x {summary['repeats']} repeat(s) "
        f"= {c['n']} predictions",
        f"- Judge: `{summary['judge_model'] or 'not run'}`",
        *([f"- **Backend: replay.** Model outputs were recorded offline (see `triage/offline.py`), not produced "
           "by an API call in this run. Token counts and costs are ESTIMATES (bytes/3.5, priced with "
           "`agent.replay_pricing`); latency is not measured."] if summary.get("backend") == "replay" else []),
        f"- Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"- Cached results: `{summary['run_dir']}`",
        "",
        "Rates are pooled over all repeats (i.e. the mean across repeats). With ~30 messages, one message "
        "is ~3 percentage points, and per-class numbers are anecdotal.",
        "",
        "## Safety gates",
        "",
        "| Gate | Result | Detail |",
        "|---|---|---|",
    ]
    for g in summary["gates"]:
        L.append(f"| {g['name']} | {'PASS' if g['passed'] else '**FAIL**'} | {g['detail']} |")

    L += [
        "",
        "## Headline metrics",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| **Pass rate** (category + urgency + escalation all correct) | **{pct(m['pass_rate'])}** |",
        f"| Category accuracy (strict primary) | {pct(c['strict_accuracy'])} |",
        f"| Category accuracy (lenient: primary within labelled categories) | {pct(c['lenient_accuracy'])} |",
        f"| also_mentions precision / recall | {pct(c['also_mentions_precision'])} / {pct(c['also_mentions_recall'])} |",
        f"| Urgency accuracy | {pct(u['accuracy'])} |",
        f"| Under-triage (predicted less urgent than label) | {u['under_triage']} |",
        f"| Over-triage (predicted more urgent than label) | {u['over_triage']} |",
        f"| Emergency recall | {pct(u['emergency_recall'])} (n={u['emergency_n']}) |",
        f"| Escalation recall (needed a human, got one) | {pct(e['recall'])} ({e['tp']}/{e['tp'] + e['fn']}) |",
        f"| Escalation precision | {pct(e['precision'])} ({e['tp']}/{e['tp'] + e['fp']}) |",
        f"| Escalation F1 | {e['f1']:.2f} |",
    ]
    if j:
        L.append(f"| Action quality (judge, 0-2) | {j['mean_score']:.2f} (2: {j['score_2']}, 1: {j['score_1']}, 0: {j['score_0']}) |")
        L.append(f"| Actions flagged unsafe by judge | {', '.join(j['unsafe_ids']) or 'none'} |")
    if cons["messages_with_repeats"]:
        L.append(f"| Decision consistency across repeats | {pct(cons['stable_rate'])} stable; unstable: {', '.join(cons['unstable_ids']) or 'none'} |")
    L += [
        f"| Fail-safe results | {r['failsafe_count']} |",
        f"| Retried (invalid first output) | {r['retried_count']} |",
        f"| Latency p50 / p95 | {r['latency_p50_ms']} ms / {r['latency_p95_ms']} ms |",
        f"| Mean tokens in / out | {r['mean_input_tokens']:.0f} / {r['mean_output_tokens']:.0f} |",
        f"| Mean cost per message | ${r['mean_cost_usd']:.5f} (≈ ${r['mean_cost_usd'] * 1000:.2f} per 1,000) |",
        f"| Total agent cost for these predictions | ${r['total_cost_usd']:.4f} |",
        "",
        "## Breakdowns",
        "",
        *(_slices("By split (holdout = never used for prompt tuning)", m["by_split"]) if len(m["by_split"]) > 1 else []),
        *(_slices("By test group", m["by_group"]) if len(m["by_group"]) > 1 else []),
        *_slices("By model-reported confidence (does 'low' actually predict errors?)", m["by_confidence"]),
        "**Tags with the most failures** (tag: failures / total)",
        "",
        ", ".join(f"`{t}` {f}/{n}" for t, f, n in m["failing_tags"]) or "_none_",
        "",
        "## Confusion matrices",
        "",
        *_matrix("Category", c["confusion"], CATEGORIES),
        *_matrix("Urgency", u["confusion"], URGENCIES),
        "## Errors and partial credit",
        "",
        "Every prediction where category, urgency or escalation differs from the label, or the judge scored "
        "the action below 2. Disputed labels (pre-registered in `data/label_notes.json` before any model run) "
        "are marked ⚑.",
        "",
    ]

    errors = per_message_errors(rows)
    if not errors:
        L.append("_None._")
    if is_blind_dataset(summary["dataset"]):
        # Blind sets must stay blind: never write their messages, labels or rationales to disk in a
        # report, so "only aggregates were looked at" is something the repo itself can guarantee.
        L.append(f"_{len(errors)} error(s) withheld: `{summary['dataset']}` is a blind set, so only aggregate "
                 "metrics are reported. Inspect individual errors only with an explicit, logged decision._")
        errors = []
    dev_errors = [x for x in errors if x["row"].get("split", "dev") == "dev"]
    holdout_errors = [x for x in errors if x["row"].get("split") == "holdout"]
    ordered = [("Dev-set errors", dev_errors), ("Holdout errors (do not read while tuning the prompt)", holdout_errors)]
    for heading, errs in ordered:
        if not errs:
            continue
        L += [f"### {heading} ({len(errs)})", ""]
        L += _render_errors(errs, messages, disputed)

    md_path.write_text("\n".join(L))
    json_path.write_text(json.dumps(summary, indent=2, default=str))
    return md_path


def _render_errors(errors: list[dict], messages: dict[str, dict], disputed: dict[str, str]) -> list[str]:
    L: list[str] = []
    for err in errors:
        row = err["row"]
        exp, pred, mid = row["expected"], row["pred"], err["id"]
        msg = messages[mid]
        flag = " ⚑ disputed label" if mid in disputed else ""
        L += [
            f"#### {mid} (repeat {err['repeat']}){flag}: {msg.get('subject', '')}",
            "",
            f"> {msg.get('body', '').strip()[:400].replace(chr(10), ' ')}",
            "",
            "| field | expected | predicted |",
            "|---|---|---|",
        ]
        for f in DECISION_FIELDS:
            mark = " ❌" if f in err["wrong"] else ""
            L.append(f"| {f} | {exp[f]} | {pred[f]}{mark} |")
        L.append(f"| also_mentions | {', '.join(exp.get('also_mentions', [])) or '-'} | "
                 f"{', '.join(pred.get('also_mentions', [])) or '-'} |")
        L.append(f"| escalation_reasons | | {', '.join(pred['escalation_reasons']) or '-'} |")
        L.append(f"| confidence | | {pred.get('confidence', '-')} |")
        L += [
            "",
            f"- **Expected action:** {exp.get('expected_action', '')}",
            f"- **Agent action:** {pred['required_action']}",
            f"- **Agent reasoning:** {pred['reasoning']}",
        ]
        if pred.get("review_notes"):
            L.append("- **Agent review notes:** " + " / ".join(pred["review_notes"]))
        tm = msg.get("test_meta")
        if tm:
            L.append(f"- **Test group / tags:** {tm.get('group')} / {', '.join(tm.get('tags', []))}")
            L.append(f"- **Label rationale:** {tm.get('rationale', '')}")
        if pred.get("issues"):
            L.append("- **Issues:** " + "; ".join(f"[{i['category']}/{i['urgency']}] {i['summary']}" for i in pred["issues"]))
        if row.get("judge"):
            jd = row["judge"]
            L.append(f"- **Judge:** {jd['score']}/2{' UNSAFE' if jd['unsafe'] else ''}: {jd['rationale']}")
        if mid in disputed:
            L.append(f"- **Label note:** {disputed[mid]}")
        if pred["meta"].get("error"):
            L.append(f"- **Error:** `{pred['meta']['error'][:300]}`")
        L.append("")
    return L
