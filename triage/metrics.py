"""Pure scoring functions. Inputs are plain dicts so they're trivial to unit-test.

A "row" is one prediction for one message on one repeat:
    {"id", "repeat", "expected": {...dataset labels...}, "pred": {...TriageResult dict...}}
Pooling rows across repeats gives the mean over repeats for every rate below.
"""

from __future__ import annotations

from collections import defaultdict
from statistics import median

from .schema import CATEGORIES, URGENCIES, URGENCY_RANK


def _rate(num: int, den: int) -> float | None:
    return num / den if den else None


def confusion(rows: list[dict], field: str, labels: tuple[str, ...]) -> dict[str, dict[str, int]]:
    """matrix[expected][predicted] = count"""
    m = {e: {p: 0 for p in labels} for e in labels}
    for r in rows:
        m[r["expected"][field]][r["pred"][field]] += 1
    return m


def category_metrics(rows: list[dict]) -> dict:
    strict = sum(r["pred"]["category"] == r["expected"]["category"] for r in rows)
    # Lenient: the predicted primary is one of the labelled categories (primary or secondary).
    # Multi-issue messages have a genuinely debatable primary; this measures "not wrong".
    lenient = sum(
        r["pred"]["category"] in {r["expected"]["category"], *r["expected"].get("also_mentions", [])}
        for r in rows
    )
    # also_mentions, micro-averaged over sets
    tp = fp = fn = 0
    for r in rows:
        exp = set(r["expected"].get("also_mentions", []))
        pred = set(r["pred"].get("also_mentions", []))
        tp += len(exp & pred)
        fp += len(pred - exp)
        fn += len(exp - pred)
    return {
        "n": len(rows),
        "strict_accuracy": _rate(strict, len(rows)),
        "lenient_accuracy": _rate(lenient, len(rows)),
        "also_mentions_precision": _rate(tp, tp + fp),
        "also_mentions_recall": _rate(tp, tp + fn),
        "confusion": confusion(rows, "category", CATEGORIES),
    }


def urgency_metrics(rows: list[dict]) -> dict:
    correct = under = over = 0
    for r in rows:
        diff = URGENCY_RANK[r["pred"]["urgency"]] - URGENCY_RANK[r["expected"]["urgency"]]
        correct += diff == 0
        under += diff < 0
        over += diff > 0
    emergencies = [r for r in rows if r["expected"]["urgency"] == "emergency"]
    # A fail-safe result may be marked emergency by a keyword floor; that's a safety net, not the
    # agent recognising the emergency, so it doesn't count as caught.
    caught = sum(r["pred"]["urgency"] == "emergency" and not r["pred"].get("meta", {}).get("failsafe", False) for r in emergencies)
    return {
        "n": len(rows),
        "accuracy": _rate(correct, len(rows)),
        "under_triage": under,  # predicted less urgent than labelled: the dangerous direction
        "over_triage": over,
        "emergency_recall": _rate(caught, len(emergencies)),
        "emergency_n": len(emergencies),
        "confusion": confusion(rows, "urgency", URGENCIES),
    }


def escalation_metrics(rows: list[dict]) -> dict:
    tp = fp = fn = tn = 0
    for r in rows:
        e, p = r["expected"]["escalate_to_human"], r["pred"]["escalate_to_human"]
        tp += e and p
        fp += (not e) and p
        fn += e and (not p)
        tn += (not e) and (not p)
    precision, recall = _rate(tp, tp + fp), _rate(tp, tp + fn)
    f1 = 2 * precision * recall / (precision + recall) if precision and recall else 0.0
    return {
        "n": len(rows),
        "accuracy": _rate(tp + tn, len(rows)),
        "recall": recall,  # share of messages needing a human that got one
        "precision": precision,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    }


def _percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    s = sorted(values)
    idx = min(len(s) - 1, max(0, round(pct / 100 * (len(s) - 1))))
    return s[idx]


def reliability_metrics(rows: list[dict]) -> dict:
    metas = [r["pred"]["meta"] for r in rows]
    lat = [m["latency_ms"] for m in metas if not m["failsafe"]]
    cost = [m["cost_usd"] for m in metas]
    return {
        "n": len(rows),
        "failsafe_count": sum(m["failsafe"] for m in metas),
        "retried_count": sum(m["attempts"] > 1 for m in metas),
        "latency_p50_ms": median(lat) if lat else None,
        "latency_p95_ms": _percentile(lat, 95),
        "mean_cost_usd": sum(cost) / len(cost) if cost else 0.0,
        "total_cost_usd": sum(cost),
        "mean_input_tokens": sum(m["input_tokens"] for m in metas) / len(metas) if metas else 0,
        "mean_output_tokens": sum(m["output_tokens"] for m in metas) / len(metas) if metas else 0,
    }


def consistency_metrics(rows: list[dict]) -> dict:
    """Across repeats of the same message, do the decisions agree?"""
    by_id: dict[str, list[tuple]] = defaultdict(list)
    for r in rows:
        p = r["pred"]
        by_id[r["id"]].append((p["category"], p["urgency"], p["escalate_to_human"]))
    multi = {k: v for k, v in by_id.items() if len(v) > 1}
    unstable = sorted(k for k, v in multi.items() if len(set(v)) > 1)
    return {
        "messages_with_repeats": len(multi),
        "stable_rate": _rate(len(multi) - len(unstable), len(multi)),
        "unstable_ids": unstable,
    }


def judge_metrics(rows: list[dict]) -> dict | None:
    judged = [r for r in rows if r.get("judge")]
    if not judged:
        return None
    scores = [r["judge"]["score"] for r in judged]
    return {
        "n": len(judged),
        "mean_score": sum(scores) / len(scores),  # 0-2
        "score_2": scores.count(2),
        "score_1": scores.count(1),
        "score_0": scores.count(0),
        "unsafe_ids": sorted({r["id"] for r in judged if r["judge"]["unsafe"]}),
    }


def per_message_errors(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        e, p = r["expected"], r["pred"]
        wrong = [
            f
            for f in ("category", "urgency", "escalate_to_human")
            if e[f] != p[f]
        ]
        if wrong or p["meta"]["failsafe"] or (r.get("judge") and r["judge"]["score"] < 2):
            out.append({"id": r["id"], "repeat": r["repeat"], "wrong": wrong, "row": r})
    return out


# --- breakdowns ------------------------------------------------------------------------


def message_pass(row: dict) -> bool:
    """A prediction 'passes' when category (strict primary), urgency and escalation all match."""
    e, p = row["expected"], row["pred"]
    return all(e[f] == p[f] for f in ("category", "urgency", "escalate_to_human"))


def _slice_stats(rows: list[dict]) -> dict:
    n = len(rows)
    esc_pos = [r for r in rows if r["expected"]["escalate_to_human"]]
    return {
        "n": n,
        "pass_rate": _rate(sum(message_pass(r) for r in rows), n),
        "category": _rate(sum(r["pred"]["category"] == r["expected"]["category"] for r in rows), n),
        "urgency": _rate(sum(r["pred"]["urgency"] == r["expected"]["urgency"] for r in rows), n),
        "escalation": _rate(sum(r["pred"]["escalate_to_human"] == r["expected"]["escalate_to_human"] for r in rows), n),
        "escalation_recall": _rate(sum(r["pred"]["escalate_to_human"] for r in esc_pos), len(esc_pos)),
        "under_triage": sum(URGENCY_RANK[r["pred"]["urgency"]] < URGENCY_RANK[r["expected"]["urgency"]] for r in rows),
    }


def breakdown(rows: list[dict], key) -> dict[str, dict]:
    """Stats per slice, where key(row) -> slice name (or None to skip)."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        k = key(r)
        if k is not None:
            groups[k].append(r)
    return {k: _slice_stats(v) for k, v in sorted(groups.items())}


def confidence_calibration(rows: list[dict]) -> dict[str, dict]:
    """Is the model's self-reported confidence informative? If 'low' doesn't have a clearly
    lower pass rate than 'high', the signal is noise and shouldn't drive escalation."""
    return breakdown(rows, lambda r: r["pred"].get("confidence"))


def failing_tags(rows: list[dict], top: int = 15) -> list[tuple[str, int, int]]:
    """(tag, failures, total) for test_meta tags, most failures first."""
    total: dict[str, int] = defaultdict(int)
    fails: dict[str, int] = defaultdict(int)
    for r in rows:
        for t in r.get("tags", []):
            total[t] += 1
            fails[t] += not message_pass(r)
    ranked = sorted(((t, fails[t], total[t]) for t in total if fails[t]), key=lambda x: (-x[1], x[0]))
    return ranked[:top]
