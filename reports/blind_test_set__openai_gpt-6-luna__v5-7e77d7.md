# Eval report: `openai/gpt-6-luna` / prompt `v5`

- Dataset: `data/blind_test_set.json`, 120 labelled messages x 1 repeat(s) = 120 predictions
- Judge: `not run`
- Generated: 2026-10-14 23:17 UTC
- Cached results: `runs/blind_test_set__57050f/openai_gpt-6-luna__v5__4a1aaa8a48`

Rates are pooled over all repeats (i.e. the mean across repeats). With ~30 messages, one message is ~3 percentage points, and per-class numbers are anecdotal.

## Safety gates

| Gate | Result | Detail |
|---|---|---|
| No fail-safe results | PASS | 0 fail-safe |
| Emergency recall = 100% | PASS | 100% of 17 |
| Escalation recall >= 90% | PASS | 97% (2 missed) |

## Headline metrics

| Metric | Value |
|---|---|
| **Pass rate** (category + urgency + escalation all correct) | **72%** |
| Category accuracy (strict primary) | 88% |
| Category accuracy (lenient: primary within labelled categories) | 95% |
| also_mentions precision / recall | 69% / 33% |
| Urgency accuracy | 89% |
| Under-triage (predicted less urgent than label) | 9 |
| Over-triage (predicted more urgent than label) | 4 |
| Emergency recall | 100% (n=17) |
| Escalation recall (needed a human, got one) | 97% (61/63) |
| Escalation precision | 91% (61/67) |
| Escalation F1 | 0.94 |
| Fail-safe results | 0 |
| Retried (invalid first output) | 0 |
| Latency p50 / p95 | 4310.5 ms / 11007 ms |
| Mean tokens in / out | 3124 / 508 |
| Mean cost per message | $0.00030 (≈ $0.30 per 1,000) |
| Total agent cost for these predictions | $0.0362 |

## Breakdowns

**By split (holdout = never used for prompt tuning)**

| slice | n | pass | category | urgency | escalation | esc. recall | under-triage |
|---|---|---|---|---|---|---|---|
| dev | 78 | 68% | 86% | 87% | 94% | 98% | 7 |
| holdout | 42 | 79% | 93% | 93% | 93% | 95% | 2 |

**By model-reported confidence (does 'low' actually predict errors?)**

| slice | n | pass | category | urgency | escalation | esc. recall | under-triage |
|---|---|---|---|---|---|---|---|
| high | 98 | 77% | 93% | 90% | 94% | 95% | 6 |
| low | 4 | 75% | 75% | 100% | 100% | 100% | 0 |
| medium | 18 | 44% | 67% | 83% | 89% | 100% | 3 |

**Tags with the most failures** (tag: failures / total)

`multi-intent` 11/30, `debatable-primary` 10/14, `urgent` 7/19, `bilingual` 6/9, `inspection` 4/5, `tenancy-law` 4/8, `healthy-homes` 3/5, `access-dispute` 2/2, `administrative` 2/5, `children` 2/3, `complaint` 2/3, `essential-facility` 2/2, `essential-service` 2/7, `false-alarm` 2/9, `hardship` 2/6

## Confusion matrices

**Category** (rows = expected, columns = predicted)

| expected \ predicted | maintenance | arrears | complaint | enquiry | other |
|---|---|---|---|---|---|
| maintenance | **55** | 1 | 3 | 1 | · |
| arrears | 1 | **13** | · | 2 | · |
| complaint | · | · | **9** | · | · |
| enquiry | · | · | 2 | **16** | 1 |
| other | 1 | · | · | 2 | **13** |

**Urgency** (rows = expected, columns = predicted)

| expected \ predicted | emergency | urgent | routine |
|---|---|---|---|
| emergency | **17** | · | · |
| urgent | · | **22** | 9 |
| routine | · | 4 | **68** |

## Errors and partial credit

Every prediction where category, urgency or escalation differs from the label, or the judge scored the action below 2. Disputed labels (pre-registered in `data/label_notes.json` before any model run) are marked ⚑.

_34 error(s) withheld: `data/blind_test_set.json` is a blind set, so only aggregate metrics are reported. Inspect individual errors only with an explicit, logged decision._