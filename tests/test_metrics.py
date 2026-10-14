"""Metric maths checked against small hand-computed fixtures."""

import pytest

from triage.metrics import (
    category_metrics,
    consistency_metrics,
    escalation_metrics,
    reliability_metrics,
    urgency_metrics,
)


def row(id, exp, pred, repeat=0, failsafe=False, latency=100, cost=0.001):
    exp = {"also_mentions": [], **exp}
    pred = {
        "also_mentions": [],
        "meta": {
            "failsafe": failsafe,
            "latency_ms": latency,
            "cost_usd": cost,
            "attempts": 1,
            "input_tokens": 1000,
            "output_tokens": 200,
        },
        **pred,
    }
    return {"id": id, "repeat": repeat, "expected": exp, "pred": pred}


def test_category_strict_lenient_and_also_mentions():
    rows = [
        row("a", {"category": "maintenance"}, {"category": "maintenance"}),
        # primary wrong but it's one of the labelled secondaries -> lenient hit
        row("b", {"category": "enquiry", "also_mentions": ["maintenance"]},
            {"category": "maintenance", "also_mentions": ["enquiry"]}),
        row("c", {"category": "other"}, {"category": "complaint", "also_mentions": ["arrears"]}),
        row("d", {"category": "maintenance", "also_mentions": ["arrears", "complaint"]},
            {"category": "maintenance", "also_mentions": ["arrears"]}),
    ]
    m = category_metrics(rows)
    assert m["strict_accuracy"] == pytest.approx(2 / 4)
    assert m["lenient_accuracy"] == pytest.approx(3 / 4)
    # also_mentions: b: exp{maint} pred{enq} -> fp1 fn1; c: pred{arrears} fp1; d: tp1 fn1
    assert m["also_mentions_precision"] == pytest.approx(1 / 3)
    assert m["also_mentions_recall"] == pytest.approx(1 / 3)
    assert m["confusion"]["other"]["complaint"] == 1
    assert m["confusion"]["enquiry"]["maintenance"] == 1


def test_urgency_under_over_and_emergency_recall():
    rows = [
        row("a", {"urgency": "emergency"}, {"urgency": "emergency"}),
        row("b", {"urgency": "emergency"}, {"urgency": "urgent"}),  # under
        row("c", {"urgency": "routine"}, {"urgency": "urgent"}),  # over
        row("d", {"urgency": "urgent"}, {"urgency": "urgent"}),
        row("e", {"urgency": "urgent"}, {"urgency": "routine"}),  # under
    ]
    m = urgency_metrics(rows)
    assert m["accuracy"] == pytest.approx(2 / 5)
    assert (m["under_triage"], m["over_triage"]) == (2, 1)
    assert m["emergency_recall"] == pytest.approx(1 / 2) and m["emergency_n"] == 2


def test_escalation_confusion_and_f1():
    rows = [
        row("a", {"escalate_to_human": True}, {"escalate_to_human": True}),  # tp
        row("b", {"escalate_to_human": True}, {"escalate_to_human": True}),  # tp
        row("c", {"escalate_to_human": True}, {"escalate_to_human": False}),  # fn
        row("d", {"escalate_to_human": False}, {"escalate_to_human": True}),  # fp
        row("e", {"escalate_to_human": False}, {"escalate_to_human": False}),  # tn
    ]
    m = escalation_metrics(rows)
    assert (m["tp"], m["fp"], m["fn"], m["tn"]) == (2, 1, 1, 1)
    assert m["recall"] == pytest.approx(2 / 3)
    assert m["precision"] == pytest.approx(2 / 3)
    assert m["f1"] == pytest.approx(2 / 3)


def test_escalation_no_positives_predicted():
    m = escalation_metrics([row("a", {"escalate_to_human": True}, {"escalate_to_human": False})])
    assert m["recall"] == 0 and m["precision"] is None and m["f1"] == 0.0


def test_reliability_excludes_failsafe_latency():
    rows = [
        row("a", {}, {}, latency=100, cost=0.002),
        row("b", {}, {}, latency=300, cost=0.004),
        row("c", {}, {}, failsafe=True, latency=99999, cost=0.0),
    ]
    m = reliability_metrics(rows)
    assert m["failsafe_count"] == 1
    assert m["latency_p50_ms"] == 200
    assert m["total_cost_usd"] == pytest.approx(0.006)
    assert m["mean_cost_usd"] == pytest.approx(0.002)


def test_consistency_detects_flip():
    d = {"category": "maintenance", "urgency": "urgent", "escalate_to_human": False}
    rows = [
        row("a", {}, d, repeat=0),
        row("a", {}, d, repeat=1),
        row("b", {}, d, repeat=0),
        row("b", {}, {**d, "urgency": "routine"}, repeat=1),
    ]
    m = consistency_metrics(rows)
    assert m["unstable_ids"] == ["b"] and m["stable_rate"] == pytest.approx(0.5)


def test_message_pass_and_breakdown():
    from triage.metrics import breakdown, failing_tags, message_pass

    ok = {"category": "maintenance", "urgency": "urgent", "escalate_to_human": True}
    rows = [
        {**row("a", ok, ok), "group": "g1", "tags": ["x"]},
        {**row("b", ok, {**ok, "urgency": "routine"}), "group": "g1", "tags": ["x", "y"]},
        {**row("c", ok, ok), "group": "g2", "tags": ["y"]},
    ]
    assert [message_pass(r) for r in rows] == [True, False, True]
    b = breakdown(rows, lambda r: r["group"])
    assert b["g1"]["pass_rate"] == pytest.approx(0.5) and b["g1"]["under_triage"] == 1
    assert b["g2"]["pass_rate"] == 1.0
    assert failing_tags(rows) == [("x", 1, 2), ("y", 1, 2)]
