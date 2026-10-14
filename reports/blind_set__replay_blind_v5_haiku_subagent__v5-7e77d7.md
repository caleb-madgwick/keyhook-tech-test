# Eval report: `replay:blind_v5_haiku_subagent` / prompt `v5`

- Dataset: `data/blind_set.json`, 80 labelled messages x 1 repeat(s) = 80 predictions
- Judge: `replay:judge_blind_v5_sonnet_subagent`
- **Backend: replay.** Model outputs were recorded offline (see `triage/offline.py`), not produced by an API call in this run. Token counts and costs are ESTIMATES (bytes/3.5, priced with `agent.replay_pricing`); latency is not measured.
- Generated: 2026-10-14 12:53 UTC
- Cached results: `runs/blind_set__519f73/replay_blind_v5_haiku_subagent__v5__ed4c4cf936`

Rates are pooled over all repeats (i.e. the mean across repeats). With ~30 messages, one message is ~3 percentage points, and per-class numbers are anecdotal.

## Safety gates

| Gate | Result | Detail |
|---|---|---|
| No fail-safe results | PASS | 0 fail-safe |
| Emergency recall = 100% | PASS | 100% of 8 |
| Escalation recall >= 90% | PASS | 100% (0 missed) |
| Judge found no unsafe actions | PASS | none |

## Headline metrics

| Metric | Value |
|---|---|
| **Pass rate** (category + urgency + escalation all correct) | **78%** |
| Category accuracy (strict primary) | 96% |
| Category accuracy (lenient: primary within labelled categories) | 98% |
| also_mentions precision / recall | 62% / 83% |
| Urgency accuracy | 92% |
| Under-triage (predicted less urgent than label) | 1 |
| Over-triage (predicted more urgent than label) | 5 |
| Emergency recall | 100% (n=8) |
| Escalation recall (needed a human, got one) | 100% (39/39) |
| Escalation precision | 76% (39/51) |
| Escalation F1 | 0.87 |
| Action quality (judge, 0-2) | 1.90 (2: 72, 1: 8, 0: 0) |
| Actions flagged unsafe by judge | none |
| Fail-safe results | 0 |
| Retried (invalid first output) | 0 |
| Latency p50 / p95 | 0.0 ms / 0 ms |
| Mean tokens in / out | 4331 / 322 |
| Mean cost per message | $0.00059 (≈ $0.59 per 1,000) |
| Total agent cost for these predictions | $0.0475 |

## Breakdowns

**By split (holdout = never used for prompt tuning)**

| slice | n | pass | category | urgency | escalation | esc. recall | under-triage |
|---|---|---|---|---|---|---|---|
| dev | 53 | 77% | 98% | 94% | 81% | 100% | 1 |
| holdout | 27 | 78% | 93% | 89% | 93% | 100% | 0 |

**By test group**

| slice | n | pass | category | urgency | escalation | esc. recall | under-triage |
|---|---|---|---|---|---|---|---|
| adversarial | 8 | 88% | 88% | 100% | 100% | 100% | 0 |
| arrears | 7 | 86% | 100% | 100% | 86% | 100% | 0 |
| complaint | 7 | 71% | 86% | 71% | 100% | 100% | 0 |
| contra | 7 | 57% | 100% | 71% | 71% | 100% | 0 |
| emerg | 10 | 80% | 90% | 100% | 90% | 100% | 0 |
| enquiry | 8 | 75% | 100% | 100% | 75% | 100% | 0 |
| fpfn | 7 | 86% | 100% | 100% | 86% | 100% | 0 |
| lang | 10 | 80% | 100% | 100% | 80% | 100% | 0 |
| maint | 10 | 80% | 100% | 90% | 80% | n/a | 1 |
| other | 6 | 67% | 100% | 83% | 83% | 100% | 0 |

**By model-reported confidence (does 'low' actually predict errors?)**

| slice | n | pass | category | urgency | escalation | esc. recall | under-triage |
|---|---|---|---|---|---|---|---|
| high | 54 | 93% | 96% | 98% | 98% | 100% | 0 |
| low | 2 | 50% | 100% | 50% | 100% | 100% | 0 |
| medium | 24 | 46% | 96% | 83% | 54% | 100% | 1 |

**Tags with the most failures** (tag: failures / total)

`blind` 18/80, `auto-reply` 2/2, `bank-change` 2/2, `no-action` 2/2, `non-english` 2/8, `alteration` 1/1, `boundary-fence` 1/1, `consent` 1/3, `data-exfiltration` 1/1, `died` 1/1, `exterior` 1/1, `fake-urgency` 1/1, `false-positive-trap` 1/6, `figurative-language` 1/2, `framed-as-access-request` 1/1

## Confusion matrices

**Category** (rows = expected, columns = predicted)

| expected \ predicted | maintenance | arrears | complaint | enquiry | other |
|---|---|---|---|---|---|
| maintenance | **34** | · | · | · | · |
| arrears | · | **9** | · | · | · |
| complaint | 1 | · | **7** | · | · |
| enquiry | · | · | · | **17** | 1 |
| other | 1 | · | · | · | **10** |

**Urgency** (rows = expected, columns = predicted)

| expected \ predicted | emergency | urgent | routine |
|---|---|---|---|
| emergency | **8** | · | · |
| urgent | 1 | **14** | 1 |
| routine | · | 4 | **52** |

## Errors and partial credit

Every prediction where category, urgency or escalation differs from the label, or the judge scored the action below 2. Disputed labels (pre-registered in `data/label_notes.json` before any model run) are marked ⚑.

_25 error(s) withheld: `data/blind_set.json` is a blind set, so only aggregate metrics are reported. Inspect individual errors only with an explicit, logged decision._