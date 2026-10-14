# Eval report: `anthropic/claude-haiku-5.5` / prompt `v5`

- Dataset: `data/blind_test_set.json`, 120 labelled messages x 1 repeat(s) = 120 predictions
- Judge: `not run`
- Generated: 2026-10-14 23:14 UTC
- Cached results: `runs/blind_test_set__57050f/anthropic_claude-haiku-5.5__v5__13ca97a921`

Rates are pooled over all repeats (i.e. the mean across repeats). With ~30 messages, one message is ~3 percentage points, and per-class numbers are anecdotal.

## Safety gates

| Gate | Result | Detail |
|---|---|---|
| No fail-safe results | PASS | 0 fail-safe |
| Emergency recall = 100% | PASS | 100% of 17 |
| Escalation recall >= 90% | PASS | 98% (1 missed) |

## Headline metrics

| Metric | Value |
|---|---|
| **Pass rate** (category + urgency + escalation all correct) | **77%** |
| Category accuracy (strict primary) | 92% |
| Category accuracy (lenient: primary within labelled categories) | 95% |
| also_mentions precision / recall | 85% / 33% |
| Urgency accuracy | 95% |
| Under-triage (predicted less urgent than label) | 1 |
| Over-triage (predicted more urgent than label) | 5 |
| Emergency recall | 100% (n=17) |
| Escalation recall (needed a human, got one) | 98% (62/63) |
| Escalation precision | 83% (62/75) |
| Escalation F1 | 0.90 |
| Fail-safe results | 0 |
| Retried (invalid first output) | 0 |
| Latency p50 / p95 | 4520.0 ms / 9052 ms |
| Mean tokens in / out | 5467 / 797 |
| Mean cost per message | $0.00047 (≈ $0.47 per 1,000) |
| Total agent cost for these predictions | $0.0568 |

## Breakdowns

**By split (holdout = never used for prompt tuning)**

| slice | n | pass | category | urgency | escalation | esc. recall | under-triage |
|---|---|---|---|---|---|---|---|
| dev | 78 | 73% | 90% | 95% | 88% | 100% | 1 |
| holdout | 42 | 83% | 98% | 95% | 88% | 95% | 0 |

**By model-reported confidence (does 'low' actually predict errors?)**

| slice | n | pass | category | urgency | escalation | esc. recall | under-triage |
|---|---|---|---|---|---|---|---|
| high | 83 | 86% | 93% | 98% | 95% | 97% | 0 |
| low | 4 | 75% | 75% | 100% | 100% | 100% | 0 |
| medium | 33 | 55% | 94% | 88% | 70% | 100% | 1 |

**Tags with the most failures** (tag: failures / total)

`multi-intent` 7/30, `urgent` 7/19, `debatable-primary` 6/14, `bilingual` 5/9, `partial-payment` 3/3, `administrative` 2/5, `bond-dispute` 2/2, `children` 2/3, `essential-service` 2/7, `hardship` 2/6, `hindi` 2/3, `impersonation` 2/2, `inspection` 2/5, `occupancy` 2/2, `prompt-injection` 2/7

## Confusion matrices

**Category** (rows = expected, columns = predicted)

| expected \ predicted | maintenance | arrears | complaint | enquiry | other |
|---|---|---|---|---|---|
| maintenance | **60** | · | · | · | · |
| arrears | · | **14** | · | 2 | · |
| complaint | · | · | **7** | 2 | · |
| enquiry | · | 1 | · | **17** | 1 |
| other | · | 1 | · | 2 | **13** |

**Urgency** (rows = expected, columns = predicted)

| expected \ predicted | emergency | urgent | routine |
|---|---|---|---|
| emergency | **17** | · | · |
| urgent | · | **30** | 1 |
| routine | · | 5 | **67** |

## Errors and partial credit

Every prediction where category, urgency or escalation differs from the label, or the judge scored the action below 2. Disputed labels (pre-registered in `data/label_notes.json` before any model run) are marked ⚑.

_28 error(s) withheld: `data/blind_test_set.json` is a blind set, so only aggregate metrics are reported. Inspect individual errors only with an explicit, logged decision._