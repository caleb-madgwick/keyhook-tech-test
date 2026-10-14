"""A no-LLM baseline: keyword rules only. It answers "would plain code do this job?" with numbers.

    python -m triage.baseline [--dataset tenant_emails_test_suite.json] [--split dev]

It reuses the real pre-checks (injection regex, obfuscation) and the same metrics as the eval,
so the comparison with the LLM agent is like-for-like. The rules were written in a few minutes
from the label definitions; that's the point: this is what cheap plain code gets you.
"""

from __future__ import annotations

import argparse
import re

from .agent import load_messages
from .config import ROOT
from .eval import split_of
from .guardrails import precheck
from .metrics import category_metrics, escalation_metrics, message_pass, urgency_metrics


def _any(words: str, text: str) -> bool:
    return re.search(rf"\b({words})", text, re.IGNORECASE) is not None


EMERGENCY = r"gas smell|smell(s|ing)? (of )?gas|smoke|fire|flames|sparking|sparks|burst|flooding|sewage|carbon monoxide|collaps"
URGENT = r"no hot water|no power|no heat|heat pump|won'?t lock|can'?t lock|smoke alarm|mould|rats|mice|leak|broken window|locked out|toilet"
ARREARS = r"rent|arrears|payment|paid|pay\b|behind|overdue"
COMPLAINT = r"complain|noise|neighbour|rude|unacceptable|joke|disappointed|not happy|fed up"
MAINT = r"broken|leak|not working|isn'?t working|repair|fix|dripping|blocked|faulty|crack|damaged|stuck"
ENQUIRY = r"\?|can (i|we)|is it ok|allowed|permission|bond|inspection|lease|notice|application|viewing"
OTHER = r"thank|unsubscribe|out of office|on leave|auto-?reply|undeliverable"
ESCALATE = r"tribunal|lawyer|legal|lost my job|can'?t pay|hardship|winz|break (the|my) lease|end the tenancy|threat|unsafe|scared"


def classify(msg: dict) -> dict:
    pre = precheck(msg)
    text = f"{pre.msg.get('subject', '')}\n{pre.msg.get('body', '')}"
    if _any(EMERGENCY, text):
        urgency = "emergency"
    elif _any(URGENT, text):
        urgency = "urgent"
    else:
        urgency = "routine"
    if _any(OTHER, text) and not _any(MAINT, text):
        category = "other"
    elif _any(COMPLAINT, text):
        category = "complaint"
    elif _any(MAINT, text) or urgency != "routine":
        category = "maintenance"
    elif _any(ARREARS, text):
        category = "arrears"
    elif _any(ENQUIRY, text):
        category = "enquiry"
    else:
        category = "other"
    escalate = urgency == "emergency" or bool(pre.injection_hits) or pre.obfuscated or _any(ESCALATE, text)
    return {"category": category, "also_mentions": [], "urgency": urgency, "escalate_to_human": escalate}


def main() -> None:
    ap = argparse.ArgumentParser(description="Score a keyword-rules baseline (no LLM).")
    ap.add_argument("--dataset", default="tenant_emails_test_suite.json")
    ap.add_argument("--split", choices=["all", "dev", "holdout"], default="all")
    args = ap.parse_args()
    messages = [m for m in load_messages(ROOT / args.dataset) if "expected" in m]
    if args.split != "all":
        messages = [m for m in messages if split_of(m) == args.split]
    rows = [{"id": m["id"], "expected": m["expected"], "pred": classify(m)} for m in messages]
    c, u, e = category_metrics(rows), urgency_metrics(rows), escalation_metrics(rows)
    pct = lambda v: "n/a" if v is None else f"{v:.0%}"  # noqa: E731
    print(f"Keyword baseline on {args.dataset} ({args.split}, n={len(rows)})")
    print(f"  pass rate {pct(sum(message_pass(r) for r in rows) / len(rows))}  category {pct(c['strict_accuracy'])}  "
          f"urgency {pct(u['accuracy'])} (under-triage {u['under_triage']}, emergency recall {pct(u['emergency_recall'])})  "
          f"escalation recall {pct(e['recall'])} precision {pct(e['precision'])}")


if __name__ == "__main__":
    main()
