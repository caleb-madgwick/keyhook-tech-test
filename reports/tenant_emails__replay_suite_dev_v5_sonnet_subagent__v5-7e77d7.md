# Eval report: `replay:suite_dev_v5_sonnet_subagent` / prompt `v5`

- Dataset: `tenant_emails.json`, 30 labelled messages x 1 repeat(s) = 30 predictions
- Judge: `replay:judge_suite_dev_v5_sonnet_by_opus_subagent`
- **Backend: replay.** Model outputs were recorded offline (see `triage/offline.py`), not produced by an API call in this run. Token counts and costs are ESTIMATES (bytes/3.5, priced with `agent.replay_pricing`); latency is not measured.
- Generated: 2026-10-14 21:52 UTC
- Cached results: `runs/tenant_emails__ff71b3/replay_suite_dev_v5_sonnet_subagent__v5__b9059befad`

Rates are pooled over all repeats (i.e. the mean across repeats). With ~30 messages, one message is ~3 percentage points, and per-class numbers are anecdotal.

## Safety gates

| Gate | Result | Detail |
|---|---|---|
| No fail-safe results | PASS | 0 fail-safe |
| Emergency recall = 100% | PASS | 100% of 2 |
| Escalation recall >= 90% | PASS | 100% (0 missed) |
| Judge found no unsafe actions | PASS | none |
| msg_002: emergency | PASS | ok |
| msg_002: escalate | PASS | ok |
| msg_003: escalate | PASS | ok |
| msg_013: escalate | PASS | ok |
| msg_014: emergency | PASS | ok |
| msg_014: escalate | PASS | ok |
| msg_016: escalate | PASS | ok |
| msg_016: not_emergency | PASS | ok |
| msg_019: escalate | PASS | ok |
| msg_020: escalate | PASS | ok |
| msg_027: escalate | PASS | ok |

## Headline metrics

| Metric | Value |
|---|---|
| **Pass rate** (category + urgency + escalation all correct) | **100%** |
| Category accuracy (strict primary) | 100% |
| Category accuracy (lenient: primary within labelled categories) | 100% |
| also_mentions precision / recall | 100% / 83% |
| Urgency accuracy | 100% |
| Under-triage (predicted less urgent than label) | 0 |
| Over-triage (predicted more urgent than label) | 0 |
| Emergency recall | 100% (n=2) |
| Escalation recall (needed a human, got one) | 100% (15/15) |
| Escalation precision | 100% (15/15) |
| Escalation F1 | 1.00 |
| Action quality (judge, 0-2) | 1.87 (2: 26, 1: 4, 0: 0) |
| Actions flagged unsafe by judge | none |
| Fail-safe results | 0 |
| Retried (invalid first output) | 0 |
| Latency p50 / p95 | 0.0 ms / 0 ms |
| Mean tokens in / out | 4277 / 211 |
| Mean cost per message | $0.00053 (≈ $0.53 per 1,000) |
| Total agent cost for these predictions | $0.0160 |

## Breakdowns

**By model-reported confidence (does 'low' actually predict errors?)**

| slice | n | pass | category | urgency | escalation | esc. recall | under-triage |
|---|---|---|---|---|---|---|---|
| high | 24 | 100% | 100% | 100% | 100% | 100% | 0 |
| low | 1 | 100% | 100% | 100% | 100% | 100% | 0 |
| medium | 5 | 100% | 100% | 100% | 100% | 100% | 0 |

**Tags with the most failures** (tag: failures / total)

_none_

## Confusion matrices

**Category** (rows = expected, columns = predicted)

| expected \ predicted | maintenance | arrears | complaint | enquiry | other |
|---|---|---|---|---|---|
| maintenance | **15** | · | · | · | · |
| arrears | · | **2** | · | · | · |
| complaint | · | · | **2** | · | · |
| enquiry | · | · | · | **7** | · |
| other | · | · | · | · | **4** |

**Urgency** (rows = expected, columns = predicted)

| expected \ predicted | emergency | urgent | routine |
|---|---|---|---|
| emergency | **2** | · | · |
| urgent | · | **11** | · |
| routine | · | · | **17** |

## Errors and partial credit

Every prediction where category, urgency or escalation differs from the label, or the judge scored the action below 2. Disputed labels (pre-registered in `data/label_notes.json` before any model run) are marked ⚑.

### Dev-set errors (4)

#### msg_008 (repeat 0): Quick question about the bond

> Hi, we're moving out on the 31st. How long does it take to get the bond back and do we need to sign anything?

| field | expected | predicted |
|---|---|---|
| category | enquiry | enquiry |
| urgency | routine | routine |
| escalate_to_human | False | False |
| also_mentions | - | - |
| escalation_reasons | | - |
| confidence | | high |

- **Expected action:** Explain the bond refund process and the form required, and confirm the final inspection.
- **Agent action:** Send the standard move-out and bond refund information, including any forms to sign.
- **Agent reasoning:** Bond refund timing and paperwork enquiry ahead of move-out; bond is an enquiry, not rent.
- **Issues:** [enquiry/routine] Asks how long bond refund takes and whether anything must be signed on moving out on the 31st
- **Judge:** 1/2: Sends bond refund and form information but omits confirming the final inspection, which is a key step in the reference.

#### msg_012 (repeat 0): Mould in the bedroom

> Hi,  There's black mould growing on the ceiling and around the window frame in the back bedroom. We wipe it down every week but it keeps coming back. My daughter sleeps in there and has had a cough for a few weeks. We open the windows when we can. Is there a ventilation fan or something that could be installed?  Oliver

| field | expected | predicted |
|---|---|---|
| category | maintenance | maintenance |
| urgency | urgent | urgent |
| escalate_to_human | True | True |
| also_mentions | - | - |
| escalation_reasons | | safety_concern |
| confidence | | high |

- **Expected action:** Arrange an inspection of the moisture and ventilation issue and treatment of the mould; check Healthy Homes compliance.
- **Agent action:** Arrange a prompt inspection of the mould and moisture source, ask the PM/landlord to decide on ventilation options, and check in with the tenant about the child's health.
- **Agent reasoning:** Black mould keeps returning in the bedroom where a child has had a cough for weeks. Mould with health effects is urgent and needs safety escalation.
- **Issues:** [maintenance/urgent] Recurring black mould in back bedroom; daughter has had a cough for weeks; asks about a ventilation fan
- **Judge:** 1/2: Arranges an inspection of the mould and moisture but does not include mould treatment or a Healthy Homes compliance check, which are key reference steps.

#### msg_021 (repeat 0) ⚑ disputed label: New flatmate

> Hi there, one of our flatmates (Jess) is moving out at the end of the month and we've found someone to take her room, his name is Tama. What do we need to do to get him added to the lease and Jess removed? Does Tama need to apply?

| field | expected | predicted |
|---|---|---|
| category | enquiry | enquiry |
| urgency | routine | routine |
| escalate_to_human | True | True |
| also_mentions | - | - |
| escalation_reasons | | legal_or_tenancy_law |
| confidence | | high |

- **Expected action:** Explain the flatmate change process, send Tama an application, and arrange the change of tenant paperwork with landlord consent.
- **Agent action:** Ask the PM to explain the process for changing names on the tenancy, including whether Tama must apply and landlord approval.
- **Agent reasoning:** Flatmate swap needs tenancy changes and application for the new person, which involves changing who is on the tenancy.
- **Issues:** [enquiry/routine] Asks how to add new flatmate Tama to the lease and remove Jess
- **Judge:** 1/2: Only has the PM explain the process; it does not send Tama an application or arrange the change-of-tenant paperwork, both key reference steps.
- **Label note:** escalate=true for a flatmate change, but msg_023 (landlord consent for fibre) is escalate=false. Both are consent/paperwork processes; the line between them is unclear.

#### msg_022 (repeat 0) ⚑ disputed label: Power point sparking

> When I plugged the jug in this morning the power point in the kitchen made a loud crack and sparked. Theres a black mark around it now. We havent used it since. Is that safe to use the others on the same wall?

| field | expected | predicted |
|---|---|---|
| category | maintenance | maintenance |
| urgency | urgent | urgent |
| escalate_to_human | True | True |
| also_mentions | - | - |
| escalation_reasons | | medium_confidence |
| confidence | | medium |

- **Expected action:** Advise the tenant not to use the outlet and to switch off that circuit if possible, and book an electrician within 24 hours.
- **Agent action:** Book an electrician urgently, advise the tenant not to use that outlet, and consider cautioning against the others until checked.
- **Agent reasoning:** A power point cracked and sparked with a black mark but is no longer being used, so the hazard is contained. Needs an electrician soon and advice about nearby outlets.
- **Agent review notes:** Unclear if the other outlets on the wall are affected; the electrician should check.
- **Issues:** [maintenance/urgent] Kitchen power point cracked, sparked and scorched when jug was plugged in; not used since
- **Judge:** 1/2: Books an electrician and says not to use the outlet, but omits advising the tenant to switch off that circuit, a key safety step in the reference.
- **Label note:** Sparking outlet already out of use is escalated; msg_039 (comparable electrical fault) is not.
