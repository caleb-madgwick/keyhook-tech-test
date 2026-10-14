# Eval report: `openai/gpt-6-luna` / prompt `v5`

- Dataset: `data/blind_set.json`, 80 labelled messages x 1 repeat(s) = 80 predictions
- Judge: `not run`
- Generated: 2026-10-14 23:15 UTC
- Cached results: `runs/blind_set__519f73/openai_gpt-6-luna__v5__4a1aaa8a48`

Rates are pooled over all repeats (i.e. the mean across repeats). With ~30 messages, one message is ~3 percentage points, and per-class numbers are anecdotal.

## Safety gates

| Gate | Result | Detail |
|---|---|---|
| No fail-safe results | PASS | 0 fail-safe |
| Emergency recall = 100% | PASS | 100% of 8 |
| Escalation recall >= 90% | PASS | 100% (0 missed) |

## Headline metrics

| Metric | Value |
|---|---|
| **Pass rate** (category + urgency + escalation all correct) | **90%** |
| Category accuracy (strict primary) | 99% |
| Category accuracy (lenient: primary within labelled categories) | 99% |
| also_mentions precision / recall | 56% / 83% |
| Urgency accuracy | 95% |
| Under-triage (predicted less urgent than label) | 2 |
| Over-triage (predicted more urgent than label) | 2 |
| Emergency recall | 100% (n=8) |
| Escalation recall (needed a human, got one) | 100% (39/39) |
| Escalation precision | 91% (39/43) |
| Escalation F1 | 0.95 |
| Fail-safe results | 0 |
| Retried (invalid first output) | 0 |
| Latency p50 / p95 | 4160.5 ms / 8019 ms |
| Mean tokens in / out | 3154 / 443 |
| Mean cost per message | $0.00027 (≈ $0.27 per 1,000) |
| Total agent cost for these predictions | $0.0218 |

## Breakdowns

**By split (holdout = never used for prompt tuning)**

| slice | n | pass | category | urgency | escalation | esc. recall | under-triage |
|---|---|---|---|---|---|---|---|
| dev | 53 | 91% | 100% | 94% | 94% | 100% | 1 |
| holdout | 27 | 89% | 96% | 96% | 96% | 100% | 1 |

**By test group**

| slice | n | pass | category | urgency | escalation | esc. recall | under-triage |
|---|---|---|---|---|---|---|---|
| adversarial | 8 | 100% | 100% | 100% | 100% | 100% | 0 |
| arrears | 7 | 100% | 100% | 100% | 100% | 100% | 0 |
| complaint | 7 | 100% | 100% | 100% | 100% | 100% | 0 |
| contra | 7 | 100% | 100% | 100% | 100% | 100% | 0 |
| emerg | 10 | 80% | 90% | 90% | 90% | 100% | 0 |
| enquiry | 8 | 100% | 100% | 100% | 100% | 100% | 0 |
| fpfn | 7 | 100% | 100% | 100% | 100% | 100% | 0 |
| lang | 10 | 60% | 100% | 80% | 80% | 100% | 1 |
| maint | 10 | 80% | 100% | 90% | 90% | n/a | 1 |
| other | 6 | 100% | 100% | 100% | 100% | 100% | 0 |

**By model-reported confidence (does 'low' actually predict errors?)**

| slice | n | pass | category | urgency | escalation | esc. recall | under-triage |
|---|---|---|---|---|---|---|---|
| high | 74 | 91% | 99% | 95% | 96% | 100% | 2 |
| low | 3 | 100% | 100% | 100% | 100% | 100% | 0 |
| medium | 3 | 67% | 100% | 100% | 67% | 100% | 0 |

**Tags with the most failures** (tag: failures / total)

`blind` 8/80, `non-english` 4/8, `security` 3/4, `contained` 2/2, `no-action` 2/2, `auto-reply` 1/2, `child` 1/3, `framed-as-access-request` 1/1, `glass` 1/1, `heating` 1/1, `japanese` 1/1, `lock` 1/1, `night` 1/3, `no-injury` 1/1, `no-vulnerable-occupant` 1/1

## Confusion matrices

**Category** (rows = expected, columns = predicted)

| expected \ predicted | maintenance | arrears | complaint | enquiry | other |
|---|---|---|---|---|---|
| maintenance | **34** | · | · | · | · |
| arrears | · | **9** | · | · | · |
| complaint | · | · | **8** | · | · |
| enquiry | · | · | · | **18** | · |
| other | · | · | · | 1 | **10** |

**Urgency** (rows = expected, columns = predicted)

| expected \ predicted | emergency | urgent | routine |
|---|---|---|---|
| emergency | **8** | · | · |
| urgent | 2 | **12** | 2 |
| routine | · | · | **56** |

## Errors and partial credit

Every prediction where category, urgency or escalation differs from the label, or the judge scored the action below 2. Disputed labels (pre-registered in `data/label_notes.json` before any model run) are marked ⚑.

_8 error(s) withheld: `data/blind_set.json` is a blind set, so only aggregate metrics are reported. Inspect individual errors only with an explicit, logged decision._