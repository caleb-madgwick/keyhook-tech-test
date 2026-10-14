# Eval report: `anthropic/claude-haiku-5.5` / prompt `v5`

- Dataset: `data/blind_set.json`, 80 labelled messages x 1 repeat(s) = 80 predictions
- Judge: `not run`
- Generated: 2026-10-14 23:12 UTC
- Cached results: `runs/blind_set__519f73/anthropic_claude-haiku-5.5__v5__13ca97a921`

Rates are pooled over all repeats (i.e. the mean across repeats). With ~30 messages, one message is ~3 percentage points, and per-class numbers are anecdotal.

## Safety gates

| Gate | Result | Detail |
|---|---|---|
| No fail-safe results | **FAIL** | 1 fail-safe |
| Emergency recall = 100% | PASS | 100% of 8 |
| Escalation recall >= 90% | PASS | 100% (0 missed) |

## Headline metrics

| Metric | Value |
|---|---|
| **Pass rate** (category + urgency + escalation all correct) | **80%** |
| Category accuracy (strict primary) | 95% |
| Category accuracy (lenient: primary within labelled categories) | 96% |
| also_mentions precision / recall | 45% / 83% |
| Urgency accuracy | 92% |
| Under-triage (predicted less urgent than label) | 1 |
| Over-triage (predicted more urgent than label) | 5 |
| Emergency recall | 100% (n=8) |
| Escalation recall (needed a human, got one) | 100% (39/39) |
| Escalation precision | 83% (39/47) |
| Escalation F1 | 0.91 |
| Fail-safe results | 1 |
| Retried (invalid first output) | 1 |
| Latency p50 / p95 | 4963 ms / 9630 ms |
| Mean tokens in / out | 5441 / 812 |
| Mean cost per message | $0.00049 (≈ $0.49 per 1,000) |
| Total agent cost for these predictions | $0.0394 |

## Breakdowns

**By split (holdout = never used for prompt tuning)**

| slice | n | pass | category | urgency | escalation | esc. recall | under-triage |
|---|---|---|---|---|---|---|---|
| dev | 53 | 81% | 96% | 94% | 89% | 100% | 1 |
| holdout | 27 | 78% | 93% | 89% | 93% | 100% | 0 |

**By test group**

| slice | n | pass | category | urgency | escalation | esc. recall | under-triage |
|---|---|---|---|---|---|---|---|
| adversarial | 8 | 75% | 75% | 88% | 100% | 100% | 0 |
| arrears | 7 | 71% | 100% | 86% | 86% | 100% | 0 |
| complaint | 7 | 71% | 86% | 71% | 100% | 100% | 0 |
| contra | 7 | 86% | 100% | 100% | 86% | 100% | 0 |
| emerg | 10 | 90% | 90% | 100% | 100% | 100% | 0 |
| enquiry | 8 | 75% | 100% | 100% | 75% | 100% | 0 |
| fpfn | 7 | 100% | 100% | 100% | 100% | 100% | 0 |
| lang | 10 | 60% | 100% | 100% | 60% | 100% | 0 |
| maint | 10 | 90% | 100% | 90% | 100% | n/a | 1 |
| other | 6 | 83% | 100% | 83% | 100% | 100% | 0 |

**By model-reported confidence (does 'low' actually predict errors?)**

| slice | n | pass | category | urgency | escalation | esc. recall | under-triage |
|---|---|---|---|---|---|---|---|
| high | 61 | 85% | 97% | 95% | 93% | 100% | 1 |
| low | 4 | 50% | 75% | 75% | 75% | 100% | 0 |
| medium | 15 | 67% | 93% | 87% | 80% | 100% | 0 |

**Tags with the most failures** (tag: failures / total)

`blind` 16/80, `bank-change` 2/2, `english` 2/2, `inspection` 2/3, `no-action` 2/2, `non-english` 2/8, `not-non-english` 2/2, `privacy` 2/2, `prompt-injection` 2/6, `te-reo-greeting` 2/3, `alteration` 1/1, `attachment` 1/1, `auto-reply` 1/2, `boundary-fence` 1/1, `consent` 1/3

## Confusion matrices

**Category** (rows = expected, columns = predicted)

| expected \ predicted | maintenance | arrears | complaint | enquiry | other |
|---|---|---|---|---|---|
| maintenance | **34** | · | · | · | · |
| arrears | · | **9** | · | · | · |
| complaint | 1 | · | **7** | · | · |
| enquiry | · | · | · | **16** | 2 |
| other | 1 | · | · | · | **10** |

**Urgency** (rows = expected, columns = predicted)

| expected \ predicted | emergency | urgent | routine |
|---|---|---|---|
| emergency | **8** | · | · |
| urgent | · | **15** | 1 |
| routine | · | 5 | **51** |

## Errors and partial credit

Every prediction where category, urgency or escalation differs from the label, or the judge scored the action below 2. Disputed labels (pre-registered in `data/label_notes.json` before any model run) are marked ⚑.

_16 error(s) withheld: `data/blind_set.json` is a blind set, so only aggregate metrics are reported. Inspect individual errors only with an explicit, logged decision._