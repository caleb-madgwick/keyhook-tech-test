# Eval report: `replay:suite_v4_haiku_subagent` / prompt `v4`

- Dataset: `tenant_emails.json`, 30 labelled messages x 1 repeat(s) = 30 predictions
- Judge: `replay:judge_suite_v4_sonnet_subagent`
- **Backend: replay.** Model outputs were recorded offline (see `triage/offline.py`), not produced by an API call in this run. Token counts and costs are ESTIMATES (bytes/3.5, priced with `agent.replay_pricing`); latency is not measured.
- Generated: 2026-10-14 12:23 UTC
- Cached results: `runs/tenant_emails__ff71b3/replay_suite_v4_haiku_subagent__v4__21587c293b`

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
| **Pass rate** (category + urgency + escalation all correct) | **93%** |
| Category accuracy (strict primary) | 97% |
| Category accuracy (lenient: primary within labelled categories) | 100% |
| also_mentions precision / recall | 83% / 83% |
| Urgency accuracy | 100% |
| Under-triage (predicted less urgent than label) | 0 |
| Over-triage (predicted more urgent than label) | 0 |
| Emergency recall | 100% (n=2) |
| Escalation recall (needed a human, got one) | 100% (15/15) |
| Escalation precision | 94% (15/16) |
| Escalation F1 | 0.97 |
| Action quality (judge, 0-2) | 1.93 (2: 28, 1: 2, 0: 0) |
| Actions flagged unsafe by judge | none |
| Fail-safe results | 0 |
| Retried (invalid first output) | 0 |
| Latency p50 / p95 | 0.0 ms / 0 ms |
| Mean tokens in / out | 3318 / 300 |
| Mean cost per message | $0.00048 (≈ $0.48 per 1,000) |
| Total agent cost for these predictions | $0.0145 |

## Breakdowns

**By model-reported confidence (does 'low' actually predict errors?)**

| slice | n | pass | category | urgency | escalation | esc. recall | under-triage |
|---|---|---|---|---|---|---|---|
| high | 27 | 96% | 96% | 100% | 100% | 100% | 0 |
| low | 1 | 100% | 100% | 100% | 100% | 100% | 0 |
| medium | 2 | 50% | 100% | 100% | 50% | 100% | 0 |

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

### Dev-set errors (4)

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
- **Agent action:** Send the standard bond refund timeframe and move-out paperwork information. Confirm the move-out date and written notice are on file, and arrange the exit inspection.
- **Agent reasoning:** The tenant is moving out on the 31st and asks how long the bond takes to be returned and whether anything needs signing. This is a standard bond and move-out enquiry, with no dispute or hazard.
- **Agent review notes:** Confirm that written notice of the 31st move-out date is on file, as the message does not say whether it was formally given.
- **Issues:** [enquiry/routine] Moving out on the 31st; asks how long bond refund takes and whether they need to sign anything
- **Judge:** 2/2: Covers bond refund process and paperwork, and arranges the exit inspection.

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
- **Agent action:** Call the tenant immediately to confirm they are safe and have shelter. Give them the after-hours emergency line and arrange an after-hours locksmith to regain entry. If they are in danger, advise them to call 111.
- **Agent reasoning:** The tenant is locked out at 2:30am in freezing weather with a phone at 8%, so they are stranded outside at night. A lockout is a standard maintenance booking, but a stranded person at night needs an immediate check-in and safety advice, so the matter is urgent with a safety_concern escalation.
- **Agent review notes:** Tenant is stranded outside at night in freezing conditions with a low phone battery; confirm their safety on the call.
- **Issues:** [maintenance/urgent] Locked out at 2:30am, keys inside, freezing outside, phone battery at 8%; asks for after-hours number
- **Judge:** 1/2: Arranges after-hours locksmith and emergency contact, but does not note that the cost may be recharged to the tenant.
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
- **Agent action:** Book an inspection within 24-48 hours to assess the mould, moisture source and ventilation. Refer the extraction fan request to the PM for approval, without promising it. Advise the tenant to see a doctor if the cough continues.
- **Agent reasoning:** Black mould is recurring on the bedroom ceiling and window frame, and the tenant's daughter has had a cough for weeks in that room. Mould with possible health effects is urgent and a safety concern, and the ventilation fan question needs landlord approval.
- **Agent review notes:** The child's cough may be linked to the mould; the link is not confirmed.
- **Issues:** [maintenance/urgent] Recurring black mould on ceiling and window frame in back bedroom; daughter has had a cough for weeks; asks about a ventilation fan
- **Judge:** 1/2: Books an inspection of mould and ventilation but omits mould treatment and a Healthy Homes compliance check.

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
- **Agent action:** Book a handyman to re-fix the loose front gutter and check it is secure. Refer the raised vegetable bed request to the PM under the standard garden-change consent process.
- **Agent reasoning:** The tenant asks about planting a raised vegetable bed and reports the front gutter has come loose and is hanging down. The gutter is a routine repair and the garden bed is a routine consent that the PM must decide on.
- **Issues:** [maintenance/routine] Front gutter loose at one end and hanging down; [enquiry/routine] Asks to plant a small raised vegetable bed in the backyard
- **Judge:** 2/2: Books the gutter repair and refers the garden bed to the PM for consent.
- **Label note:** Primary 'enquiry' (garden bed) over 'maintenance' (loose gutter). The only actionable repair is the gutter; the label seems to follow 'first raised' ordering.
