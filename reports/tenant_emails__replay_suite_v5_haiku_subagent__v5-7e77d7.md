# Eval report: `replay:suite_v5_haiku_subagent` / prompt `v5`

- Dataset: `tenant_emails.json`, 30 labelled messages x 1 repeat(s) = 30 predictions
- Judge: `replay:judge_suite_v5_sonnet_subagent`
- **Backend: replay.** Model outputs were recorded offline (see `triage/offline.py`), not produced by an API call in this run. Token counts and costs are ESTIMATES (bytes/3.5, priced with `agent.replay_pricing`); latency is not measured.
- Generated: 2026-10-14 12:49 UTC
- Cached results: `runs/tenant_emails__ff71b3/replay_suite_v5_haiku_subagent__v5__24018335c4`

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
| **Pass rate** (category + urgency + escalation all correct) | **90%** |
| Category accuracy (strict primary) | 97% |
| Category accuracy (lenient: primary within labelled categories) | 100% |
| also_mentions precision / recall | 80% / 67% |
| Urgency accuracy | 100% |
| Under-triage (predicted less urgent than label) | 0 |
| Over-triage (predicted more urgent than label) | 0 |
| Emergency recall | 100% (n=2) |
| Escalation recall (needed a human, got one) | 100% (15/15) |
| Escalation precision | 88% (15/17) |
| Escalation F1 | 0.94 |
| Action quality (judge, 0-2) | 1.90 (2: 27, 1: 3, 0: 0) |
| Actions flagged unsafe by judge | none |
| Fail-safe results | 0 |
| Retried (invalid first output) | 0 |
| Latency p50 / p95 | 0.0 ms / 0 ms |
| Mean tokens in / out | 4277 / 298 |
| Mean cost per message | $0.00058 (≈ $0.58 per 1,000) |
| Total agent cost for these predictions | $0.0173 |

## Breakdowns

**By model-reported confidence (does 'low' actually predict errors?)**

| slice | n | pass | category | urgency | escalation | esc. recall | under-triage |
|---|---|---|---|---|---|---|---|
| high | 22 | 95% | 95% | 100% | 100% | 100% | 0 |
| low | 1 | 100% | 100% | 100% | 100% | 100% | 0 |
| medium | 7 | 71% | 100% | 100% | 71% | 100% | 0 |

**Tags with the most failures** (tag: failures / total)

_none_

## Confusion matrices

**Category** (rows = expected, columns = predicted)

| expected \ predicted | maintenance | arrears | complaint | enquiry | other |
|---|---|---|---|---|---|
| maintenance | **15** | · | · | · | · |
| arrears | · | **2** | · | · | · |
| complaint | · | · | **2** | · | · |
| enquiry | 1 | · | · | **6** | · |
| other | · | · | · | · | **4** |

**Urgency** (rows = expected, columns = predicted)

| expected \ predicted | emergency | urgent | routine |
|---|---|---|---|
| emergency | **2** | · | · |
| urgent | · | **11** | · |
| routine | · | · | **17** |

## Errors and partial credit

Every prediction where category, urgency or escalation differs from the label, or the judge scored the action below 2. Disputed labels (pre-registered in `data/label_notes.json` before any model run) are marked ⚑.

### Dev-set errors (5)

#### msg_008 (repeat 0): Quick question about the bond

> Hi, we're moving out on the 31st. How long does it take to get the bond back and do we need to sign anything?

| field | expected | predicted |
|---|---|---|
| category | enquiry | enquiry |
| urgency | routine | routine |
| escalate_to_human | False | True ❌ |
| also_mentions | - | - |
| escalation_reasons | | medium_confidence |
| confidence | | medium |

- **Expected action:** Explain the bond refund process and the form required, and confirm the final inspection.
- **Agent action:** Confirm the vacate date and notice on file, then send the standard bond refund timeline and move-out documentation to the tenant.
- **Agent reasoning:** The tenant is moving out on the 31st and asks how long the bond refund takes and whether anything needs signing. Bond questions are enquiries answered with standard move-out information, so this is routine with no escalation, but the vacate date needs confirming.
- **Agent review notes:** The message gives the 31st without a month; confirm the vacate date and that written notice is on file.
- **Issues:** [enquiry/routine] Moving out on the 31st; asks about bond refund timing and documents to sign
- **Judge:** 1/2: Misses confirming the final inspection.

#### msg_011 (repeat 0) ⚑ disputed label: Locked out

> Im locked out, left my keys inside. Its 2:30am and freezing. Is there an after hours number?? My phone is on 8%

| field | expected | predicted |
|---|---|---|
| category | maintenance | maintenance |
| urgency | urgent | urgent |
| escalate_to_human | True | True |
| also_mentions | - | - |
| escalation_reasons | | safety_concern |
| confidence | | high |

- **Expected action:** Respond immediately with after-hours locksmith or key options, noting the cost may be recharged.
- **Agent action:** Contact the tenant immediately, as her phone is nearly flat, to confirm she is safe. The PM needs to approve the out-of-hours locksmith call-out, then arrange access and a follow-up check.
- **Agent reasoning:** The tenant is locked out at 2:30am in freezing weather with keys inside and a phone at 8% battery. She is stranded outside at night, which needs a personal check-in and fast access, though the home itself is secure. A lockout is urgent maintenance and the stranded occupant is a safety concern.
- **Agent review notes:** Confirm she is safe now and whether anyone is with her; the message gives no callback number.
- **Issues:** [maintenance/urgent] Locked out at 2:30am in freezing weather with keys inside; phone battery at 8%
- **Judge:** 1/2: Immediate contact and PM approval, but no mention of locksmith/key options to the tenant or that cost may be recharged.
- **Label note:** Category 'maintenance' for a tenant who locked themselves out; nothing at the property needs repair. 'other' or 'enquiry' (after-hours number) is defensible.

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
- **Agent action:** Arrange an urgent inspection within 24-48 hours to find the moisture source and assess ventilation and extraction options. Ask the PM to decide on any fan installation and reply to the tenant. Arrange a personal check-in on the family's health concern.
- **Agent reasoning:** Black mould is growing on the bedroom ceiling and window frame and returns after weekly cleaning, and the tenant's daughter has had a cough for weeks in that room. Mould with possible health effects is urgent and a safety concern. The ventilation question needs an inspection and a PM decision.
- **Agent review notes:** The link between the mould and the daughter's cough is not established; do not assume a cause.
- **Issues:** [maintenance/urgent] Recurring black mould on bedroom ceiling and window frame; daughter has had a cough for weeks; asks about ventilation fan
- **Judge:** 1/2: Inspection and ventilation covered but no mould treatment or Healthy Homes compliance check.

#### msg_015 (repeat 0): Rent paid

> Hi, just letting you know I've paid the $540 I was behind from last week, along with this week's rent. Sorry about the delay. Can you confirm my account is now up to date?

| field | expected | predicted |
|---|---|---|
| category | arrears | arrears |
| urgency | routine | routine |
| escalate_to_human | False | True ❌ |
| also_mentions | - | - |
| escalation_reasons | | medium_confidence |
| confidence | | medium |

- **Expected action:** Check the rent ledger and confirm the account balance to the tenant.
- **Agent action:** Check the bank and rent ledger for the $540 arrears payment and this week's rent. If both are received and the balance is zero, send the standard payment confirmation. If not received, the PM should review before replying.
- **Agent reasoning:** The tenant reports paying $540 of arrears plus this week's rent and asks for confirmation that the account is up to date. This is a payment confirmation in the arrears category. It is routine, but the payment must be checked in the ledger before confirming.
- **Agent review notes:** The payment is not yet verified in the ledger; do not confirm until the receipt is seen.
- **Issues:** [arrears/routine] Says $540 arrears and this week's rent have been paid; asks to confirm the account is up to date
- **Judge:** 2/2: Checks ledger and confirms balance.

#### msg_030 (repeat 0) ⚑ disputed label: Garden and a question

> Hi! Spring's coming and I'd love to plant some vegetables in the backyard, would that be alright? Just a small raised bed. Also, the gutter at the front has come loose at one end and is hanging down a bit.

| field | expected | predicted |
|---|---|---|
| category | enquiry | maintenance ❌ |
| urgency | routine | routine |
| escalate_to_human | False | False |
| also_mentions | maintenance | enquiry |
| escalation_reasons | | - |
| confidence | | high |

- **Expected action:** Get landlord approval for the raised garden bed and book a gutter repair.
- **Agent action:** Book a gutter repair for the loose front gutter. Ask the PM to decide on the raised vegetable bed consent, then reply to the tenant with the outcome.
- **Agent reasoning:** The tenant reports the front gutter is loose at one end and hanging down, and asks whether a small raised vegetable bed is allowed. The gutter is a routine maintenance fault that drives the action and is primary. The garden request is a routine consent for the PM to decide.
- **Agent review notes:** A hanging gutter may need faster attention in windy weather; check at the next visit.
- **Issues:** [maintenance/routine] Front gutter loose at one end and hanging down; [enquiry/routine] Asks permission to plant a small raised vegetable bed in the backyard
- **Judge:** 2/2: Gutter booked, consent to PM.
- **Label note:** Primary 'enquiry' (garden bed) over 'maintenance' (loose gutter). The only actionable repair is the gutter; the label seems to follow 'first raised' ordering.
