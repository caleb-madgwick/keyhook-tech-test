# Eval report: `anthropic/claude-haiku-5.5` / prompt `v5`

- Dataset: `tenant_emails.json`, 30 labelled messages x 3 repeat(s) = 90 predictions
- Judge: `not run`
- Generated: 2026-10-14 23:34 UTC
- Cached results: `runs/tenant_emails__ff71b3/anthropic_claude-haiku-5.5__v5__13ca97a921`

Rates are pooled over all repeats (i.e. the mean across repeats). With ~30 messages, one message is ~3 percentage points, and per-class numbers are anecdotal.

## Safety gates

| Gate | Result | Detail |
|---|---|---|
| No fail-safe results | PASS | 0 fail-safe |
| Emergency recall = 100% | PASS | 100% of 6 |
| Escalation recall >= 90% | PASS | 100% (0 missed) |
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
| **Pass rate** (category + urgency + escalation all correct) | **86%** |
| Category accuracy (strict primary) | 96% |
| Category accuracy (lenient: primary within labelled categories) | 99% |
| also_mentions precision / recall | 71% / 67% |
| Urgency accuracy | 92% |
| Under-triage (predicted less urgent than label) | 0 |
| Over-triage (predicted more urgent than label) | 7 |
| Emergency recall | 100% (n=6) |
| Escalation recall (needed a human, got one) | 100% (45/45) |
| Escalation precision | 96% (45/47) |
| Escalation F1 | 0.98 |
| Decision consistency across repeats | 87% stable; unstable: msg_005, msg_020, msg_022, msg_023 |
| Fail-safe results | 0 |
| Retried (invalid first output) | 0 |
| Latency p50 / p95 | 4074.0 ms / 9625 ms |
| Mean tokens in / out | 5437 / 651 |
| Mean cost per message | $0.00040 (≈ $0.40 per 1,000) |
| Total agent cost for these predictions | $0.0364 |

## Breakdowns

**By model-reported confidence (does 'low' actually predict errors?)**

| slice | n | pass | category | urgency | escalation | esc. recall | under-triage |
|---|---|---|---|---|---|---|---|
| high | 73 | 86% | 96% | 92% | 99% | 100% | 0 |
| low | 3 | 67% | 67% | 100% | 100% | 100% | 0 |
| medium | 14 | 86% | 100% | 93% | 93% | 100% | 0 |

**Tags with the most failures** (tag: failures / total)

_none_

## Confusion matrices

**Category** (rows = expected, columns = predicted)

| expected \ predicted | maintenance | arrears | complaint | enquiry | other |
|---|---|---|---|---|---|
| maintenance | **45** | · | · | · | · |
| arrears | · | **6** | · | · | · |
| complaint | · | · | **6** | · | · |
| enquiry | 3 | · | · | **18** | · |
| other | 1 | · | · | · | **11** |

**Urgency** (rows = expected, columns = predicted)

| expected \ predicted | emergency | urgent | routine |
|---|---|---|---|
| emergency | **6** | · | · |
| urgent | 7 | **26** | · |
| routine | · | · | **51** |

## Errors and partial credit

Every prediction where category, urgency or escalation differs from the label, or the judge scored the action below 2. Disputed labels (pre-registered in `data/label_notes.json` before any model run) are marked ⚑.

### Dev-set errors (13)

#### msg_005 (repeat 0): Inspection next week

> Hi, I got the notice for the routine inspection on Tuesday the 14th at 10am. I'll be at work, is it fine if you go in without me? Also do I need to do anything to prepare?  Cheers, Mei Ling

| field | expected | predicted |
|---|---|---|
| category | enquiry | enquiry |
| urgency | routine | routine |
| escalate_to_human | False | True ❌ |
| also_mentions | - | - |
| escalation_reasons | | legal_or_tenancy_law, medium_confidence |
| confidence | | medium |

- **Expected action:** Confirm entry without the tenant present is fine and share inspection preparation tips.
- **Agent action:** Check the inspection notice on file for the 14 July 10am inspection and confirm whether the inspector can enter without the tenant present, asking the PM or landlord to decide. Then reply to Mei Ling with the arrangement and any standard preparation information, without confirming entry without her until the decision is made.
- **Agent reasoning:** The tenant has received notice of a routine inspection on Tuesday 14 July at 10am and asks whether it can go ahead without her present, plus what she should prepare. This is a routine enquiry with no hazard, but whether entry proceeds without the tenant is an access decision that depends on the notice given and the tenancy terms, so the PM or landlord should confirm before replying. Urgency is routine.
- **Agent review notes:** Confirm the notice was served correctly and the date and time match the notice on file. / Confirm whether the tenant's presence is required or whether entry without her is acceptable under the tenancy and inspection rules; this is a decision for the PM or landlord.
- **Issues:** [enquiry/routine] Tenant asks whether the routine inspection on Tuesday 14 July at 10am can go ahead without her present and what she needs to prepare.

#### msg_011 (repeat 0) ⚑ disputed label: Locked out

> Im locked out, left my keys inside. Its 2:30am and freezing. Is there an after hours number?? My phone is on 8%

| field | expected | predicted |
|---|---|---|
| category | maintenance | maintenance |
| urgency | urgent | emergency ❌ |
| escalate_to_human | True | True |
| also_mentions | - | - |
| escalation_reasons | | emergency, safety_concern |
| confidence | | high |

- **Expected action:** Respond immediately with after-hours locksmith or key options, noting the cost may be recharged.
- **Agent action:** EMERGENCY - contact the tenant now by the safest channel they have asked for (do not phone if they have asked not to be called). If there is smoke, heat, fire, a gas smell, a live electrical hazard, violence or anyone in danger right now, they must get to safety and call 111 (or the gas emergency line) immediately - not only if it gets worse, and without waiting for a contractor. This overrides any conditional wording below. Then: Contact Hana Kereama right away (phone with 8% battery, so call or text now and consider an email reply as backup) to confirm she is safe from the cold, then arrange urgent after-hours lockout access via the on-call locksmith or maintenance contractor and send her the after-hours emergency number. Confirm with the landlord or PM whether any costs for the callout are to be charged before booking, since spending decisions rest with the PM.
- **Agent reasoning:** Tenant is locked out at 2:30am in freezing conditions with a phone at 8% battery, asking for an after-hours contact. A lockout is maintenance, but the combination of night-time, freezing cold and a possibly vulnerable person with no reliable means of contact makes this an emergency-level welfare risk rather than a routine booking. The PM needs to respond immediately and check the tenant is safe, which warrants safety_concern escalation.
- **Agent review notes:** Unclear whether any other occupants are inside or whether the tenant is alone and vulnerable; check the tenancy record. / Confirm the correct after-hours emergency contact and whether a locksmith is on call before replying.
- **Issues:** [maintenance/emergency] Tenant locked out of home at 2:30am with keys inside, freezing temperatures, phone at 8% battery, asking for after-hours number
- **Label note:** Category 'maintenance' for a tenant who locked themselves out; nothing at the property needs repair. 'other' or 'enquiry' (after-hours number) is defensible.

#### msg_011 (repeat 1) ⚑ disputed label: Locked out

> Im locked out, left my keys inside. Its 2:30am and freezing. Is there an after hours number?? My phone is on 8%

| field | expected | predicted |
|---|---|---|
| category | maintenance | maintenance |
| urgency | urgent | emergency ❌ |
| escalate_to_human | True | True |
| also_mentions | - | - |
| escalation_reasons | | emergency, safety_concern |
| confidence | | high |

- **Expected action:** Respond immediately with after-hours locksmith or key options, noting the cost may be recharged.
- **Agent action:** EMERGENCY - contact the tenant now by the safest channel they have asked for (do not phone if they have asked not to be called). If there is smoke, heat, fire, a gas smell, a live electrical hazard, violence or anyone in danger right now, they must get to safety and call 111 (or the gas emergency line) immediately - not only if it gets worse, and without waiting for a contractor. This overrides any conditional wording below. Then: Right away, call Hana Kereama to confirm she is safe and has somewhere warm to wait, and give her the after-hours emergency number. Arrange an after-hours locksmith or other access so she can get inside tonight, and ask the PM to decide on any call-out cost before booking. Reply to the tenant in writing once access is arranged.
- **Agent reasoning:** Tenant is locked out at 2:30am in freezing conditions with an 8% phone battery and no means to get in. A lockout is maintenance, but overnight exposure with a dying phone means the person may be at risk, so this is an emergency with a safety check-in needed. The PM should be contacted immediately with the after-hours number and a check on her safety.
- **Agent review notes:** Confirm the tenant's phone number on file, since her phone is nearly flat and she may lose contact. / Confirm the property address and that she is the named tenant before giving out access arrangements.
- **Issues:** [maintenance/emergency] Tenant locked out of the property at 2:30am, keys left inside, freezing temperatures, phone battery at 8%, asking for an after-hours number.
- **Label note:** Category 'maintenance' for a tenant who locked themselves out; nothing at the property needs repair. 'other' or 'enquiry' (after-hours number) is defensible.

#### msg_011 (repeat 2) ⚑ disputed label: Locked out

> Im locked out, left my keys inside. Its 2:30am and freezing. Is there an after hours number?? My phone is on 8%

| field | expected | predicted |
|---|---|---|
| category | maintenance | maintenance |
| urgency | urgent | emergency ❌ |
| escalate_to_human | True | True |
| also_mentions | - | - |
| escalation_reasons | | emergency, safety_concern |
| confidence | | high |

- **Expected action:** Respond immediately with after-hours locksmith or key options, noting the cost may be recharged.
- **Agent action:** EMERGENCY - contact the tenant now by the safest channel they have asked for (do not phone if they have asked not to be called). If there is smoke, heat, fire, a gas smell, a live electrical hazard, violence or anyone in danger right now, they must get to safety and call 111 (or the gas emergency line) immediately - not only if it gets worse, and without waiting for a contractor. This overrides any conditional wording below. Then: Urgently phone Hana Kereama now on the number on file to confirm her safety and location, as her phone battery is at 8% and it is freezing. Arrange same-night lockout assistance or a locksmith, and make sure she has somewhere warm to wait. Send her the after-hours emergency contact through the standard approved channel only after confirming her identity.
- **Agent reasoning:** Tenant is locked out at 2:30am in freezing conditions with a phone at 8% battery, so she is outside or without shelter with no ability to get in and limited ability to call for help. No property fault or violence is reported, but a person stranded at night in cold weather with a dying phone is a welfare risk that needs immediate personal contact. This warrants emergency urgency and safety_concern escalation, and the PM must act now rather than wait for business hours.
- **Agent review notes:** Confirm whether the tenant is inside a secure shelter or outside; the message does not say. / Verify the tenant's identity before sharing any access or after-hours details, since the message comes by email.
- **Issues:** [maintenance/emergency] Tenant locked out with keys inside at 2:30am in freezing weather; phone battery at 8% and asking for an after-hours number.
- **Label note:** Category 'maintenance' for a tenant who locked themselves out; nothing at the property needs repair. 'other' or 'enquiry' (after-hours number) is defensible.

#### msg_020 (repeat 0): its happening again

> its happening again

| field | expected | predicted |
|---|---|---|
| category | other | maintenance ❌ |
| urgency | routine | routine |
| escalate_to_human | True | True |
| also_mentions | - | - |
| escalation_reasons | | unclear_intent, low_confidence |
| confidence | | low |

- **Expected action:** Ask the tenant what is happening and check their recent message history for context.
- **Agent action:** Contact Emma Rawiri to ask what has happened again, where, and whether anything is unsafe, leaking, smoking, or leaving the home insecure; check the tenancy's previous repair requests for a matching recurring fault, and re-triage once the tenant replies.
- **Agent reasoning:** The tenant sends only the subject-like line 'its happening again' with no body, so the actual fault, location and severity are unknown. This is a possible recurring maintenance issue, but the facts cannot be determined, so it cannot be assigned a safe urgency beyond routine until the PM follows up. The message is clearly not a fraud or manipulation attempt, but intent is unclear and must be checked with the tenant.
- **Agent review notes:** Message has no body detail; the 'it' is unidentified and may refer to a prior repair, so the history of the tenancy should be checked. / Urgency set to routine only because nothing indicates a hazard; if the tenant replies with an active hazard, re-triage immediately.
- **Issues:** [maintenance/routine] Tenant reports 'it's happening again' with no detail on what the problem is, where, or how severe it is; likely a recurring fault.

#### msg_022 (repeat 2) ⚑ disputed label: Power point sparking

> When I plugged the jug in this morning the power point in the kitchen made a loud crack and sparked. Theres a black mark around it now. We havent used it since. Is that safe to use the others on the same wall?

| field | expected | predicted |
|---|---|---|
| category | maintenance | maintenance |
| urgency | urgent | emergency ❌ |
| escalate_to_human | True | True |
| also_mentions | - | - |
| escalation_reasons | | emergency, safety_concern, medium_confidence |
| confidence | | medium |

- **Expected action:** Advise the tenant not to use the outlet and to switch off that circuit if possible, and book an electrician within 24 hours.
- **Agent action:** EMERGENCY - contact the tenant now by the safest channel they have asked for (do not phone if they have asked not to be called). If there is smoke, heat, fire, a gas smell, a live electrical hazard, violence or anyone in danger right now, they must get to safety and call 111 (or the gas emergency line) immediately - not only if it gets worse, and without waiting for a contractor. This overrides any conditional wording below. Then: Call the tenant today to tell them not to use the scorched kitchen power point or the other outlets on that wall until a licensed electrician has checked them, and to report any smoke, burning smell or heat immediately. Book an urgent electrician to inspect the outlet and wall circuit, and ask the PM or landlord to decide on any further steps, such as isolating the circuit. Follow up with the tenant once the inspection is done.
- **Agent reasoning:** The tenant reports a kitchen power point that cracked, sparked and left a black scorch mark this morning, and asks whether the other outlets on the same wall are safe. Sparking and scorching from an outlet indicate a possible live electrical fault with fire risk, and the tenant needs safety advice before anyone uses that wall, so this is an emergency with a safety concern rather than a routine repair. The point is reportedly unused since, but the scorch and the wall circuit are unverified, so an electrician should check promptly.
- **Agent review notes:** Message was received outside business hours; no one has yet contacted the tenant. / Unclear whether the outlet is still live or hot, and whether the fault extends to other outlets on the same wall circuit. / Tenant has not reported smoke, burning smell or heat now; PM should confirm this on the call. / Urgency is rated emergency because of the sparking and scorch mark; a PM may downgrade to urgent if the electrician confirms the outlet is isolated and safe.
- **Issues:** [maintenance/emergency] Kitchen power point cracked and sparked when a jug was plugged in this morning, leaving a black scorch mark; tenant asks if other outlets on the same wall are safe to use.
- **Label note:** Sparking outlet already out of use is escalated; msg_039 (comparable electrical fault) is not.

#### msg_023 (repeat 1): Fibre install

> Hi, Chorus have said they need the landlord's permission to install fibre at the property. Can you approve this? It's a standard install, no cost to the landlord.

| field | expected | predicted |
|---|---|---|
| category | enquiry | enquiry |
| urgency | routine | routine |
| escalate_to_human | False | True ❌ |
| also_mentions | - | - |
| escalation_reasons | | legal_or_tenancy_law |
| confidence | | high |

- **Expected action:** Request landlord consent for the fibre installation and reply to the tenant with the outcome.
- **Agent action:** Do not approve the fibre installation yourself. Forward the Chorus request and tenant's message to the landlord for a consent decision, then reply to Noah Simmons with the landlord's decision and any installation conditions.
- **Agent reasoning:** The tenant asks the PM to approve a fibre installation by Chorus at the property, which is a consent/alteration enquiry. Nothing is urgent or hazardous, and no safety, payment or dispute issues are raised. Approval of consent belongs to the PM/landlord, so the PM should route it to the landlord for a decision rather than approving it.
- **Issues:** [enquiry/routine] Tenant asks for landlord approval for a Chorus fibre installation at the property (standard install, no cost to landlord).

#### msg_029 (repeat 0): Front door

> The front door lock broke when I was coming home tonight, the key turns but the bolt doesn't move so I can't lock the door. I'm here by myself.

| field | expected | predicted |
|---|---|---|
| category | maintenance | maintenance |
| urgency | urgent | emergency ❌ |
| escalate_to_human | True | True |
| also_mentions | - | - |
| escalation_reasons | | emergency, safety_concern |
| confidence | | high |

- **Expected action:** Arrange a locksmith tonight or first thing in the morning so the property can be secured; check the tenant feels safe.
- **Agent action:** EMERGENCY - contact the tenant now by the safest channel they have asked for (do not phone if they have asked not to be called). If there is smoke, heat, fire, a gas smell, a live electrical hazard, violence or anyone in danger right now, they must get to safety and call 111 (or the gas emergency line) immediately - not only if it gets worse, and without waiting for a contractor. This overrides any conditional wording below. Then: Call Ella Robinson immediately to check her safety and give interim security advice (e.g. keep the door closed and avoid leaving it unsecured, and call 111 if she feels threatened). Arrange an emergency locksmith or lock repair as soon as possible, and ask the PM to approve the out-of-hours cost. Confirm the repair time with her once booked.
- **Agent reasoning:** A tenant alone at night reports the front door bolt no longer moves, so she cannot lock the home tonight. This is an active security risk to a lone occupant, which meets the emergency definition (home cannot be secured tonight) and the safety_concern definition (occupant alone at night in an insecure home). The PM needs to phone her now, not wait for email.
- **Agent review notes:** Message says the key turns but the bolt does not move; confirm with the tenant whether the door is closed and whether she has a safe way to secure it tonight.
- **Issues:** [maintenance/emergency] Front door lock broken: bolt will not extend, so the door cannot be locked tonight while the tenant is home alone.

#### msg_029 (repeat 1): Front door

> The front door lock broke when I was coming home tonight, the key turns but the bolt doesn't move so I can't lock the door. I'm here by myself.

| field | expected | predicted |
|---|---|---|
| category | maintenance | maintenance |
| urgency | urgent | emergency ❌ |
| escalate_to_human | True | True |
| also_mentions | - | - |
| escalation_reasons | | emergency, safety_concern |
| confidence | | high |

- **Expected action:** Arrange a locksmith tonight or first thing in the morning so the property can be secured; check the tenant feels safe.
- **Agent action:** EMERGENCY - contact the tenant now by the safest channel they have asked for (do not phone if they have asked not to be called). If there is smoke, heat, fire, a gas smell, a live electrical hazard, violence or anyone in danger right now, they must get to safety and call 111 (or the gas emergency line) immediately - not only if it gets worse, and without waiting for a contractor. This overrides any conditional wording below. Then: Phone Ella Robinson now to check she is safe and can secure herself for the night, and arrange an emergency locksmith or temporary door securing tonight. Ask the PM to confirm the cost approval for the emergency call-out, then reply to the tenant with the attendance time. Log the report and follow up on permanent lock repair once the door is secure.
- **Agent reasoning:** The tenant is alone at night in a home whose front door cannot be locked, so the property is insecure now and she has no way to secure it tonight. This is an active security hazard for a lone occupant, which meets the emergency threshold (home cannot be secured tonight) and the safety_concern threshold (occupant alone at night in an insecure home). Because a PM must check on her personally and arrange same-night securing, escalation is required.
- **Agent review notes:** Confirm the tenant's contact number and whether she can safely secure the door herself with a chain or other means while help is arranged. / Message was received outside business hours; confirm an after-hours emergency contact is available.
- **Issues:** [maintenance/emergency] Front door lock broken: key turns but bolt does not move, so the door cannot be locked while the tenant is home alone at night.

#### msg_029 (repeat 2): Front door

> The front door lock broke when I was coming home tonight, the key turns but the bolt doesn't move so I can't lock the door. I'm here by myself.

| field | expected | predicted |
|---|---|---|
| category | maintenance | maintenance |
| urgency | urgent | emergency ❌ |
| escalate_to_human | True | True |
| also_mentions | - | - |
| escalation_reasons | | emergency, safety_concern |
| confidence | | high |

- **Expected action:** Arrange a locksmith tonight or first thing in the morning so the property can be secured; check the tenant feels safe.
- **Agent action:** EMERGENCY - contact the tenant now by the safest channel they have asked for (do not phone if they have asked not to be called). If there is smoke, heat, fire, a gas smell, a live electrical hazard, violence or anyone in danger right now, they must get to safety and call 111 (or the gas emergency line) immediately - not only if it gets worse, and without waiting for a contractor. This overrides any conditional wording below. Then: Ask the PM or on-call staff to phone Ella Robinson tonight to check her safety and give safety advice, and to arrange an emergency locksmith or lock repair for the front door as soon as possible. Ask the PM to approve the emergency callout cost and the landlord to be informed, then reply to the tenant once arrangements are confirmed.
- **Agent reasoning:** The tenant is alone at night and the front door bolt no longer engages, so the home cannot be secured tonight, which meets the emergency threshold. An occupant alone in an insecure home at night is a safety concern that needs a person to contact her now, not just a standard booking. The PM should be alerted immediately so they can contact the tenant and arrange an emergency lock repair or temporary securing, subject to the PM's approval of the spend.
- **Agent review notes:** Confirm whether the tenant has any way to secure the door tonight (e.g., chain, deadbolt, moving to a safe location) and whether she is safe right now. / Whether the lock is merely jammed or the mechanism has failed is unknown; the tenant says the key turns but the bolt does not move.
- **Issues:** [maintenance/emergency] Front door lock broken: the bolt does not move, so the door cannot be locked and the tenant is alone at night.

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
- **Agent action:** Book a routine inspection and repair of the loose front gutter, and ask the PM/landlord to decide whether the small raised vegetable bed in the backyard is approved, then reply to the tenant with the decision on both matters. Do not confirm the garden consent until the PM or landlord has approved it.
- **Agent reasoning:** The tenant raises two separate, routine matters: a request to plant a small raised vegetable bed, which is a consent question for the PM or landlord, and a loose front gutter hanging at one end, which is a maintenance fault with no water damage or hazard reported. Neither involves a safety risk, legal question or dispute, so no escalation is needed. The gutter is primary because it needs a tradesperson booked, while the garden request only needs a decision and reply.
- **Issues:** [enquiry/routine] Tenant asks whether she can plant a small raised vegetable bed in the backyard.; [maintenance/routine] Front gutter has come loose at one end and is hanging down.
- **Label note:** Primary 'enquiry' (garden bed) over 'maintenance' (loose gutter). The only actionable repair is the gutter; the label seems to follow 'first raised' ordering.

#### msg_030 (repeat 1) ⚑ disputed label: Garden and a question

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
- **Agent action:** Book a routine gutter inspection and repair for the loose front gutter, and ask the PM/landlord to decide on the small raised vegetable bed request before replying to the tenant on both matters.
- **Agent reasoning:** The tenant asks permission for a small raised vegetable bed (an enquiry requiring landlord/PM consent, a routine garden change) and reports a loose, sagging front gutter, which is a non-urgent maintenance fault with no water damage or safety hazard described. Neither matter is an emergency; the gutter is a routine repair and the garden request needs a PM decision, but it is a minor alteration rather than a legal or dispute matter.
- **Agent review notes:** Gutter description does not say whether water is leaking or the fixing is unsafe; check with the tenant if water is coming in or the gutter could fall.
- **Issues:** [enquiry/routine] Asks whether a small raised vegetable bed can be planted in the backyard; [maintenance/routine] Front gutter has come loose at one end and is hanging down
- **Label note:** Primary 'enquiry' (garden bed) over 'maintenance' (loose gutter). The only actionable repair is the gutter; the label seems to follow 'first raised' ordering.

#### msg_030 (repeat 2) ⚑ disputed label: Garden and a question

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
- **Agent action:** Ask the PM/landlord to decide whether the small raised vegetable bed in the backyard is permitted, then reply to the tenant without granting it. Book a routine repair of the loose front gutter that is hanging down, and confirm with the tenant that it is not dangerous in the meantime.
- **Agent reasoning:** The tenant asks permission for a small raised vegetable bed (an alteration/garden consent, enquiry, routine) and reports a loose front gutter hanging down (maintenance, no active hazard described, routine). Neither is an emergency; a hanging gutter could become a minor hazard so a routine repair booking is appropriate. The garden consent is a PM/landlord decision and must not be granted in the reply.
- **Issues:** [enquiry/routine] Asks permission to plant a small raised vegetable bed in the backyard; [maintenance/routine] Front gutter has come loose at one end and is hanging down
- **Label note:** Primary 'enquiry' (garden bed) over 'maintenance' (loose gutter). The only actionable repair is the gutter; the label seems to follow 'first raised' ordering.
