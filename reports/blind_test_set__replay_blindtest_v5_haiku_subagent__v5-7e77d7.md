# Eval report: `replay:blindtest_v5_haiku_subagent` / prompt `v5`

- Dataset: `data/blind_test_set.json`, 120 labelled messages x 1 repeat(s) = 120 predictions
- Judge: `replay:judge_blindtest_v5_sonnet_subagent`
- **Backend: replay.** Model outputs were recorded offline (see `triage/offline.py`), not produced by an API call in this run. Token counts and costs are ESTIMATES (bytes/3.5, priced with `agent.replay_pricing`); latency is not measured.
- Generated: 2026-10-14 12:53 UTC
- Cached results: `runs/blind_test_set__57050f/replay_blindtest_v5_haiku_subagent__v5__421fd0f146`

Rates are pooled over all repeats (i.e. the mean across repeats). With ~30 messages, one message is ~3 percentage points, and per-class numbers are anecdotal.

## Safety gates

| Gate | Result | Detail |
|---|---|---|
| No fail-safe results | PASS | 0 fail-safe |
| Emergency recall = 100% | PASS | 100% of 17 |
| Escalation recall >= 90% | PASS | 98% (1 missed) |
| Judge found no unsafe actions | PASS | none |

## Headline metrics

| Metric | Value |
|---|---|
| **Pass rate** (category + urgency + escalation all correct) | **74%** |
| Category accuracy (strict primary) | 91% |
| Category accuracy (lenient: primary within labelled categories) | 95% |
| also_mentions precision / recall | 79% / 33% |
| Urgency accuracy | 94% |
| Under-triage (predicted less urgent than label) | 4 |
| Over-triage (predicted more urgent than label) | 3 |
| Emergency recall | 100% (n=17) |
| Escalation recall (needed a human, got one) | 98% (62/63) |
| Escalation precision | 84% (62/74) |
| Escalation F1 | 0.91 |
| Action quality (judge, 0-2) | 1.94 (2: 113, 1: 7, 0: 0) |
| Actions flagged unsafe by judge | none |
| Fail-safe results | 0 |
| Retried (invalid first output) | 0 |
| Latency p50 / p95 | 0.0 ms / 0 ms |
| Mean tokens in / out | 4304 / 326 |
| Mean cost per message | $0.00059 (≈ $0.59 per 1,000) |
| Total agent cost for these predictions | $0.0712 |

## Breakdowns

**By split (holdout = never used for prompt tuning)**

| slice | n | pass | category | urgency | escalation | esc. recall | under-triage |
|---|---|---|---|---|---|---|---|
| dev | 78 | 72% | 88% | 92% | 91% | 100% | 4 |
| holdout | 42 | 79% | 95% | 98% | 86% | 95% | 0 |

**By model-reported confidence (does 'low' actually predict errors?)**

| slice | n | pass | category | urgency | escalation | esc. recall | under-triage |
|---|---|---|---|---|---|---|---|
| high | 88 | 80% | 92% | 93% | 94% | 97% | 3 |
| low | 4 | 50% | 50% | 100% | 100% | 100% | 0 |
| medium | 28 | 61% | 93% | 96% | 71% | 100% | 1 |

**Tags with the most failures** (tag: failures / total)

`multi-intent` 9/30, `debatable-primary` 7/14, `urgent` 7/19, `bilingual` 5/9, `children` 3/3, `essential-service` 3/7, `false-alarm` 3/9, `tenancy-law` 3/8, `administrative` 2/5, `appointment` 2/2, `complaint` 2/3, `hardship` 2/6, `healthy-homes` 2/5, `heating-failure` 2/2, `hindi` 2/3

## Confusion matrices

**Category** (rows = expected, columns = predicted)

| expected \ predicted | maintenance | arrears | complaint | enquiry | other |
|---|---|---|---|---|---|
| maintenance | **55** | · | 3 | 1 | 1 |
| arrears | · | **15** | · | 1 | · |
| complaint | · | · | **9** | · | · |
| enquiry | 1 | · | 1 | **16** | 1 |
| other | 1 | · | · | 1 | **14** |

**Urgency** (rows = expected, columns = predicted)

| expected \ predicted | emergency | urgent | routine |
|---|---|---|---|
| emergency | **17** | · | · |
| urgent | · | **27** | 4 |
| routine | · | 3 | **69** |

## Errors and partial credit

Every prediction where category, urgency or escalation differs from the label, or the judge scored the action below 2. Disputed labels (pre-registered in `data/label_notes.json` before any model run) are marked ⚑.

_36 error(s) withheld: `data/blind_test_set.json` is a blind set, so only aggregate metrics are reported. Inspect individual errors only with an explicit, logged decision._