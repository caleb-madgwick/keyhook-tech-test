# Eval report: `replay:suite_v3_haiku_subagent` / prompt `v3`

- Dataset: `tenant_emails_test_suite.json`, 256 labelled messages x 1 repeat(s) = 256 predictions
- Judge: `not run`
- **Backend: replay.** Model outputs were recorded offline (see `triage/offline.py`), not produced by an API call in this run. Token counts and costs are ESTIMATES (bytes/3.5, priced with `agent.replay_pricing`); latency is not measured.
- Generated: 2026-10-14 12:08 UTC
- Cached results: `runs/tenant_emails_test_suite__50db17/replay_suite_v3_haiku_subagent__v3__a75aedbcb1`

Rates are pooled over all repeats (i.e. the mean across repeats). With ~30 messages, one message is ~3 percentage points, and per-class numbers are anecdotal.

## Safety gates

| Gate | Result | Detail |
|---|---|---|
| No fail-safe results | PASS | 0 fail-safe |
| Emergency recall = 100% | **FAIL** | 97% of 30 |
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
| **Pass rate** (category + urgency + escalation all correct) | **87%** |
| Category accuracy (strict primary) | 95% |
| Category accuracy (lenient: primary within labelled categories) | 98% |
| also_mentions precision / recall | 49% / 60% |
| Urgency accuracy | 95% |
| Under-triage (predicted less urgent than label) | 3 |
| Over-triage (predicted more urgent than label) | 10 |
| Emergency recall | 97% (n=30) |
| Escalation recall (needed a human, got one) | 100% (146/146) |
| Escalation precision | 94% (146/155) |
| Escalation F1 | 0.97 |
| Fail-safe results | 0 |
| Retried (invalid first output) | 0 |
| Latency p50 / p95 | 0.0 ms / 0 ms |
| Mean tokens in / out | 3276 / 357 |
| Mean cost per message | $0.00051 (≈ $0.51 per 1,000) |
| Total agent cost for these predictions | $0.1295 |

## Breakdowns

**By test group**

| slice | n | pass | category | urgency | escalation | esc. recall | under-triage |
|---|---|---|---|---|---|---|---|
| adversarial | 21 | 90% | 95% | 95% | 100% | 100% | 0 |
| arrears | 18 | 94% | 100% | 100% | 94% | 100% | 0 |
| baseline | 30 | 93% | 93% | 100% | 100% | 100% | 0 |
| complaint | 25 | 68% | 80% | 84% | 96% | 100% | 1 |
| contra | 27 | 89% | 96% | 96% | 96% | 100% | 0 |
| emerg | 21 | 81% | 86% | 95% | 100% | 100% | 0 |
| enquiry | 24 | 79% | 96% | 88% | 92% | 100% | 0 |
| fpfn | 26 | 92% | 96% | 96% | 100% | 100% | 1 |
| lang | 24 | 92% | 100% | 92% | 100% | 100% | 1 |
| maint | 22 | 91% | 100% | 100% | 91% | n/a | 0 |
| other | 18 | 89% | 100% | 100% | 89% | 100% | 0 |

**By model-reported confidence (does 'low' actually predict errors?)**

| slice | n | pass | category | urgency | escalation | esc. recall | under-triage |
|---|---|---|---|---|---|---|---|
| high | 159 | 92% | 96% | 97% | 97% | 100% | 1 |
| low | 10 | 60% | 80% | 100% | 70% | 100% | 0 |
| medium | 87 | 82% | 94% | 90% | 98% | 100% | 2 |

**Tags with the most failures** (tag: failures / total)

`privacy` 6/14, `child` 2/4, `children` 2/5, `night` 2/4, `non-english` 2/18, `seed` 2/30, `90-days-notice` 1/1, `acknowledgement` 1/2, `allergy` 1/1, `alone` 1/1, `alone-with-children` 1/1, `alteration-request` 1/1, `arrears-in-quote` 1/1, `arrears-secondary` 1/2, `asbestos` 1/2

## Confusion matrices

**Category** (rows = expected, columns = predicted)

| expected \ predicted | maintenance | arrears | complaint | enquiry | other |
|---|---|---|---|---|---|
| maintenance | **108** | · | · | · | · |
| arrears | · | **21** | · | · | · |
| complaint | 4 | 1 | **27** | 2 | · |
| enquiry | 2 | 1 | · | **51** | 1 |
| other | 3 | · | · | · | **35** |

**Urgency** (rows = expected, columns = predicted)

| expected \ predicted | emergency | urgent | routine |
|---|---|---|---|
| emergency | **29** | 1 | · |
| urgent | 3 | **59** | 2 |
| routine | · | 7 | **155** |

## Errors and partial credit

Every prediction where category, urgency or escalation differs from the label, or the judge scored the action below 2. Disputed labels (pre-registered in `data/label_notes.json` before any model run) are marked ⚑.

### Dev-set errors (33)

#### msg_019 (repeat 0) ⚑ disputed label: Your service is a joke

> I have emailed THREE times about the broken window latch in the bedroom and nobody has replied. Three weeks. I pay $700 a week for this. If I don't hear back by Monday I'm going to the Tenancy Tribunal.

| field | expected | predicted |
|---|---|---|
| category | complaint | maintenance ❌ |
| urgency | urgent | urgent |
| escalate_to_human | True | True |
| also_mentions | maintenance | complaint |
| escalation_reasons | | dispute |
| confidence | | medium |

- **Expected action:** Escalate to the property manager to apologise, respond today, and book the window latch repair urgently (security issue).
- **Agent action:** Check for the three earlier emails and book the window latch repair within 24-48 hours. Reply to the tenant acknowledging the delay with a repair date. Do not commit to compensation; the PM handles the Tribunal threat.
- **Agent reasoning:** The bedroom window latch has been broken for three weeks, so the window cannot be locked, which is urgent. The sender is angry about unanswered emails and threatens the Tribunal, which makes the complaint a dispute. The urgent repair is primary because it is more urgent than the complaint.
- **Agent review notes:** Check the inbox for the three earlier emails and when they were received.
- **Test group / tags:** baseline / seed
- **Label rationale:** Original labelled example from the exercise brief.
- **Issues:** [maintenance/urgent] Broken bedroom window latch; window cannot be locked; [complaint/routine] Says three emails about the latch went unanswered; threatens the Tenancy Tribunal if no reply by Monday
- **Label note:** Primary 'complaint' vs 'maintenance': the underlying unresolved issue is a security repair (window latch). Either primary is defensible.

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
- **Agent action:** Book a routine gutter repair. Ask the PM to confirm the garden consent for the raised vegetable bed under policy and send the standard garden alteration form.
- **Agent reasoning:** The tenant reports a front gutter loose at one end and hanging down, which is a fault reported without blame and not an immediate hazard. The tenant also asks to plant a small raised vegetable bed, a routine garden consent. The gutter repair drives the action most.
- **Agent review notes:** Check the hanging gutter is not a fall or strike risk to people at the entrance.
- **Test group / tags:** baseline / seed
- **Label rationale:** Original labelled example from the exercise brief.
- **Issues:** [maintenance/routine] Front gutter loose at one end and hanging down; [enquiry/routine] Asks if a small raised vegetable bed can be planted in the backyard
- **Label note:** Primary 'enquiry' (garden bed) over 'maintenance' (loose gutter). The only actionable repair is the gutter; the label seems to follow 'first raised' ordering.

#### msg_039 (repeat 0): Power out to bedrooms - no rush

> Hi,  No rush on this but since about lunchtime there's been no power to any of the bedrooms. The lights and wall sockets in all three are dead. Kitchen and lounge are fine. The switch on the switchboard labelled 'BEDS' keeps flicking off a second or two after I push it back up. I've unplugged everything in the bedrooms and it still trips.  We've got extension leads running from the lounge for now 

| field | expected | predicted |
|---|---|---|
| category | maintenance | maintenance |
| urgency | urgent | urgent |
| escalate_to_human | False | True ❌ |
| also_mentions | - | - |
| escalation_reasons | | safety_concern |
| confidence | | high |

- **Expected action:** Book an electrician within 24 hours to trace the fault on the bedroom circuit that keeps tripping, and advise the tenant not to keep resetting it.
- **Agent action:** Call the tenant today and advise them to stop using the extension leads and keep the BEDS circuit switched off. Book an urgent electrician to find the fault on the bedroom circuit.
- **Agent reasoning:** There is no power to the bedrooms, and the BEDS circuit keeps tripping even with everything unplugged, which points to an electrical fault. Loss of power to part of the home is urgent despite the 'no rush' wording. The tenant is running extension leads from the lounge as temporary wiring, which is a fire risk needing safety advice.
- **Agent review notes:** The tenant says no rush, but the fault is persistent; ask about any heat or burning at the switchboard.
- **Test group / tags:** maint / electrical, no-power, circuit-tripping, tenant-downplays
- **Label rationale:** Tenant says 'no rush' but no power to part of the house with a breaker that trips under no load is urgent; tests urgency from risk, not tone.
- **Issues:** [maintenance/urgent] No power to the bedrooms; BEDS circuit keeps tripping; extension leads run from the lounge

#### msg_061 (repeat 0): Wasp nest - son allergic

> Hi,  There's a wasp nest forming under the eaves right next to my son's bedroom window. We're seeing dozens of wasps going in and out today. My son is 9 and is allergic to wasp stings (he carries an EpiPen), so we're keeping his window shut and he's sleeping in our room for now.  Can you please get pest control out as soon as possible?  Thanks, Nicola 021 555 0753

| field | expected | predicted |
|---|---|---|
| category | maintenance | maintenance |
| urgency | urgent | urgent |
| escalate_to_human | False | True ❌ |
| also_mentions | - | - |
| escalation_reasons | | safety_concern |
| confidence | | high |

- **Expected action:** Book pest control within 24 to 48 hours to remove the wasp nest under the eaves by the child's bedroom window.
- **Agent action:** Call the tenant today on the number in their message, check the family's safety and tell them to follow their child's allergy plan and call 111 if there is a reaction, then book urgent pest control for the nest.
- **Agent reasoning:** A wasp nest with dozens of wasps is under the eaves next to a 9-year-old's bedroom window, and he has a known allergy with an EpiPen. Pests that threaten health make this urgent, and a child with a serious allergy needs safety advice and a personal check-in, so it is escalated as a safety concern.
- **Agent review notes:** A child with a known allergy is at risk, so the PM should check in with the family today and follow the organisation's safety advice process.
- **Test group / tags:** maint / pests, wasps, allergy, child, spring
- **Label rationale:** An allergic child next to an active nest raises a normally routine job to urgent; the family has a plan in place so it's a standard job, not an escalation.
- **Issues:** [maintenance/urgent] Wasp nest forming under the eaves beside the 9-year-old son's bedroom window; dozens of wasps; son has a wasp allergy and carries an EpiPen; family keeping the window shut

#### msg_080 (repeat 0): window broke

> hi sorry its late. the wind blew the big lounge window in, glass all over the floor. nobody hurt. theres just a big hole now and its freezing and obviously I can't lock it. Im here with my two little ones. can someone come board it up tonight?

| field | expected | predicted |
|---|---|---|
| category | maintenance | maintenance |
| urgency | urgent | emergency ❌ |
| escalate_to_human | True | True |
| also_mentions | - | - |
| escalation_reasons | | emergency, safety_concern |
| confidence | | medium |

- **Expected action:** Arrange an after-hours glazier or board-up tonight so the property is secure and weatherproof, and check the tenant and children are safe and warm.
- **Agent action:** Phone the tenant immediately on the number in their message, keep the children away from the glass, and arrange an emergency glazier or board-up tonight.
- **Agent reasoning:** Wind has blown the lounge window in, leaving a large open hole with glass on the floor, in freezing weather, with two small children present. The home is open to the weather and cannot be secured tonight, so this is an emergency that needs same-night board-up and a safety check-in.
- **Agent review notes:** Urgency is judged from the open hole, the glass on the floor and the freezing night with children present. The PM may classify it as urgent if the glass has been cleared and the room is not in use.
- **Test group / tags:** emerg / broken-window, cannot-secure, night, alone-with-children
- **Label rationale:** A broken window that can't be secured is urgent rather than an emergency (no ongoing injury or structural risk), but a parent alone with young children at night means a person should handle it. Tests the urgent-but-escalate pattern from the seed broken lock.
- **Issues:** [maintenance/emergency] Lounge window blown in by wind, leaving a large open hole and glass on the floor; cannot be locked; freezing; tenant with two young children asks for it to be boarded up tonight

#### msg_082 (repeat 0): someone outside

> theres someone in the backyard trying the back door handle. i can see a torch. im upstairs with the lights off. is the back door deadlocked?? i cant remember if the landlord fixed it

| field | expected | predicted |
|---|---|---|
| category | other | maintenance ❌ |
| urgency | emergency | emergency |
| escalate_to_human | True | True |
| also_mentions | - | - |
| escalation_reasons | | emergency, safety_concern |
| confidence | | high |

- **Expected action:** Contact the tenant immediately and tell them to call 111 now; do not answer only the lock question. Follow up on the back door deadlock once they are safe.
- **Agent action:** Phone the tenant immediately on the number in their message, tell them to call 111 now and stay away from the door, and then arrange a lock check on the back door.
- **Agent reasoning:** Someone is in the backyard trying the back door handle with a torch, and the tenant is alone upstairs in the dark, so an intruder is present now. This is an emergency that needs immediate contact, a call to 111, and a personal safety check-in.
- **Agent review notes:** The tenant is unsure whether the back door is deadlocked. The PM should not answer that question by email as a reason to delay calling 111.
- **Test group / tags:** emerg / intruder, in-progress, night, alone, disguised-as-question
- **Label rationale:** An intruder in progress phrased as a question about a lock. Catches classifiers that file it as a maintenance enquiry and miss that the right action is 111 right now.
- **Issues:** [maintenance/emergency] Person in the backyard trying the back door handle with a torch; tenant is upstairs with lights off; tenant asks whether the back door is deadlocked

#### msg_083 (repeat 0) ⚑ disputed label: Need locks changed today please

> Hi,  I need the locks changed today if possible. My ex-partner was served with a protection order yesterday and he isn't allowed to come near me, but he still has a key to the house. He's not on the lease. I'm scared he'll come back while the kids are home. I'm happy to pay for it if that's what it takes.  Please don't give him any information about me or the house if he contacts you.  Kayla 021 5

| field | expected | predicted |
|---|---|---|
| category | other | maintenance ❌ |
| urgency | urgent | urgent |
| escalate_to_human | True | True |
| also_mentions | maintenance | - |
| escalation_reasons | | safety_concern |
| confidence | | high |

- **Expected action:** Have the property manager call the tenant today, approve and arrange an urgent lock change, flag the file so no information is shared with the ex-partner, and advise calling 111 if he turns up; offer details of family violence support services.
- **Agent action:** Phone the tenant today on the number in their message to check their safety and refer them to family-violence support. Arrange a locksmith to change the locks today or within 24h, PM to approve the cost, and do not share any information about the tenant or the property with anyone who calls about her.
- **Agent reasoning:** The tenant's ex-partner has been served with a protection order but still has a key to the house, and the children are at home, so there is a family-violence risk. The risk is not happening this minute but is serious, so this is urgent, with a safety escalation. The lock change is a cost decision for the PM.
- **Agent review notes:** The tenant asks that the ex-partner not be given any information if he calls. Staff should not confirm the tenant's details to anyone who calls about her. / Confirm the protection order details with the tenant before the locks are changed.
- **Test group / tags:** emerg / family-violence, protection-order, lock-change, privacy, children
- **Label rationale:** A family violence disclosure where the request looks like a simple lock change. Tests that it is escalated with care and privacy handling rather than booked as a routine locksmith job.
- **Issues:** [maintenance/urgent] Ex-partner under a protection order still has a key to the house and is not on the lease; tenant is scared he will return while the children are home; wants the locks changed today and will pay
- **Label note:** Same family-violence lock-change situation as msg_309, but labelled other+[maintenance] vs maintenance+[].

#### msg_091 (repeat 0): Neighbour's dog bit my son

> Hi,  The neighbour's dog got through the gap in the side fence again (I've reported this gap twice) and bit my 7yo son on the leg in our backyard this afternoon. We've been to the after-hours clinic and he needed stitches. I've reported it to the council's animal services.  The gap is still there and the dog is still next door. I'm not letting the kids outside until it's fixed. This is not ok.  Fi

| field | expected | predicted |
|---|---|---|
| category | complaint | maintenance ❌ |
| urgency | urgent | urgent |
| escalate_to_human | True | True |
| also_mentions | maintenance | complaint |
| escalation_reasons | | safety_concern |
| confidence | | medium |

- **Expected action:** Escalate to the property manager to check on the family, block the fence gap within 24 hours and arrange a permanent fence repair, and liaise with the neighbouring owner and the council.
- **Agent action:** Phone the tenant today to check on the son and the family's safety. Book the side-fence repair as a priority within 24-48 hours and check who owns the fence. Confirm whether the neighbour is our tenant before any action about the dog, and do not make liability decisions.
- **Agent reasoning:** A neighbour's dog bit the tenant's 7-year-old, who needed stitches, and the side-fence gap she reported twice is still open, so the dog can get through again. The open gap is an urgent boundary security issue for children, and the bite is a possible injury and liability concern needing a personal check-in. The anger is aimed at the unfixed gap and the neighbour, so the repair drives the action, with the complaint as a secondary matter.
- **Agent review notes:** It is unclear whether the neighbour is our tenant and who is responsible for the fence. / The son's injury is reported second-hand in the message; confirm his condition.
- **Test group / tags:** emerg / dog-attack, injury, child, previously-reported, neighbour
- **Label rationale:** An injury to a child caused by a repeatedly reported fence gap, with an angry tone. The hazard persists so it is urgent, and the complaint about inaction makes it primary with maintenance as a secondary.
- **Issues:** [maintenance/urgent] Side-fence gap that the neighbour's dog keeps getting through; reported twice and still open.; [complaint/routine] Unhappy that a neighbour's dog bit her son and is still next door; she has reported the dog to council animal services.

#### msg_127 (repeat 0) ⚑ disputed label: Payment Received: $2,450.00 NZD - Action Required

> Dear Customer,  A payment of $2,450.00 NZD has been sent to your account by HARBOURSIDE TENANT TRUST. To release the funds you must verify your account details within 24 hours.  View Remittance: http://secure-pay-verify.example.com/remit?id=88412  Failure to verify will result in the payment being returned to the sender.  KiwiSecure Bank Payments Team This is an automated message, please do not re

| field | expected | predicted |
|---|---|---|
| category | other | other |
| urgency | routine | routine |
| escalate_to_human | False | True ❌ |
| also_mentions | - | - |
| escalation_reasons | | fraud_or_impersonation |
| confidence | | high |

- **Expected action:** No action; mark as phishing, don't click the link, and delete.
- **Agent action:** Do not click the link or reply to the email. Check the trust account directly through the bank's own online banking to confirm whether any payment arrived. Report the email to the IT or security contact as phishing and warn staff.
- **Agent reasoning:** The message is an automated bank-style notice claiming a $2,450 payment from the agency's tenant trust account, and it asks the recipient to verify account details through a link within 24 hours or the funds will be returned. This is a phishing attempt to collect credentials, so it is categorised as other and escalated for fraud.
- **Agent review notes:** The claimed payment and the link are unverified and look like phishing.
- **Test group / tags:** arrears / phishing, bank-impersonation, spam, payment-word-not-arrears
- **Label rationale:** Generic bank-style phishing with no tenant behind it: other, routine, not escalated (spam). Unlike the owner bank-change fraud, it asks nothing of the PM's records. Tests that 'payment received' and 'action required' don't produce arrears or urgent labels.
- **Issues:** [other/routine] Automated notice of a $2,450 payment that requires account verification through a link within 24 hours.
- **Label note:** Credential-phishing link not escalated, while msg_198 and msg_262 (also credential phishing) are.

#### msg_131 (repeat 0): Cigarette smoke coming into our flat

> Hi,  The tenant in the unit below us (Unit 2) smokes on their balcony constantly and it comes straight up into our bedroom and our son's room through the windows. Our son is 4 and has asthma, and he has needed his reliever inhaler more since this started about a month ago. We can't open the windows to air the place, which is making the condensation worse.  I left a polite note under their door two

| field | expected | predicted |
|---|---|---|
| category | complaint | complaint |
| urgency | routine | urgent ❌ |
| escalate_to_human | True | True |
| also_mentions | - | maintenance |
| escalation_reasons | | safety_concern, dispute |
| confidence | | medium |

- **Expected action:** Escalate to the property manager to check the building's smoking rules and contact the Unit 2 tenant about smoke drifting into other units. Acknowledge the impact on the child's asthma.
- **Agent action:** Phone the tenant within 24 hours for a welfare check. Advise her to follow the child's asthma plan and to call 111 if he has severe breathing difficulty. Check the no-smoking terms and handle the Unit 2 complaint through the nuisance process without sharing details. Book a condensation and ventilation inspection.
- **Agent reasoning:** The tenant says smoke from the unit below comes into her flat and her 4-year-old's room, that he has asthma and has needed his reliever more since the smoking began a month ago, and that condensation is worsening. A child's asthma getting worse from smoke is a health effect needing a welfare check, so the complaint is urgent, and the condensation is routine maintenance.
- **Agent review notes:** The smoke source and its effect on the child's asthma are reported by the tenant and not yet verified. / Check the tenancy's no-smoking terms and whether the Unit 2 tenancy allows smoking on the balcony.
- **Test group / tags:** complaint / neighbour-smoking, health-impact, child-asthma, inter-tenant-dispute
- **Label rationale:** A dispute between tenants with a health angle, so it should be escalated. Urgency stays routine because nothing is in immediate danger and no essential service is lost. Catches over-rating urgency because a child's health is mentioned. The condensation remark is incidental, not a separate maintenance item.
- **Issues:** [complaint/urgent] Unit 2 neighbour smokes constantly on the balcony; smoke enters the flat and the 4-year-old's room; son has asthma and needs his reliever more since about a month ago; a polite note has not helped.; [maintenance/routine] Windows cannot be opened to air the flat, and condensation is getting worse.

#### msg_135 (repeat 0): Flatmate not paying - rent short

> Hi there,  I'm one of the four tenants at 88 Owen Street. Our flatmate Callum hasn't paid his share of the power or internet for three months (about $410 owing to me personally), and this week he told us he can't pay his share of the rent either. So the rent that went out on Monday was $195 short. The rest of us will try to cover it by Friday but we can't keep doing that.  We've had enough. Can yo

| field | expected | predicted |
|---|---|---|
| category | complaint | arrears ❌ |
| urgency | routine | routine |
| escalate_to_human | True | True |
| also_mentions | arrears | complaint, enquiry |
| escalation_reasons | | dispute, legal_or_tenancy_law |
| confidence | | medium |

- **Expected action:** Escalate to the property manager to confirm the $195 shortfall and explain that all tenants are jointly liable for the full rent. Outline the options for removing a tenant (agreement or a Tribunal application), noting that the bills debt is between the flatmates.
- **Agent action:** Check the rent ledger for the $195 shortfall, then refer the lease removal and penalty questions to the PM and owner. Reply to Ravi that the request is being reviewed and that flatmate debts are for the tenants to settle; do not confirm any penalty position or lease change.
- **Agent reasoning:** A flatmate has not paid his share of rent, so the rent that went out on Monday was $195 short, and the other tenants have had to cover it. The sender also wants the flatmate removed from the lease and assurance that the others will not be penalised. The arrears need checking now, but nothing is a hardship for the sender, so routine; removing a tenant from the lease and any penalty decisions need a person to review.
- **Agent review notes:** The sender's account of Callum's inability to pay is second-hand; it is unclear whether this is genuine financial hardship for Callum. / Confirm the $195 shortfall against the ledger before acting. / Lease removal and any rent or penalty decisions need PM and legal review; do not promise either.
- **Test group / tags:** complaint / flatmate, unpaid-bills, rent-shortfall, joint-liability, remove-tenant-request
- **Label rationale:** The main thrust is a dispute with a flatmate, but a real rent shortfall means arrears must appear in also_mentions. Tests multi-label detection and escalation for a tenancy-law question about removing a co-tenant.
- **Issues:** [arrears/routine] Rent received on Monday was $195 short because a flatmate (Callum) has not paid his share.; [complaint/routine] Flatmate owes the sender about $410 for power and internet and this is a private debt between tenants.; [enquiry/routine] Asks the agency to remove Callum from the lease and confirm the other tenants will not be penalised for his share of rent.

#### msg_140 (repeat 0): Damage from gutter guys

> Hi,  The gutter cleaners you sent on Tuesday leaned their ladder against my car in the driveway and there's now a long scratch and a dent on the driver's door. I've got photos. They also cracked one of the terracotta pots on the porch (that's mine) and snapped the side gate latch, which now won't close, so our dog can get out.  Who pays for the car? I've had a quote from a panel beater for $640.  

| field | expected | predicted |
|---|---|---|
| category | complaint | maintenance ❌ |
| urgency | routine | urgent ❌ |
| escalate_to_human | True | True |
| also_mentions | maintenance | complaint |
| escalation_reasons | | dispute |
| confidence | | high |

- **Expected action:** Escalate to the property manager to raise the tenant's damage claim (car and pot) with the gutter contractor and their insurer, and book a repair of the side gate latch.
- **Agent action:** Book an urgent gate latch repair so the dog cannot get out. Notify the gutter contractor of the car, pot and gate damage and ask for their insurance details. Refer the $640 claim to the PM for a liability decision; reply to Patrick that the claim is being reviewed and do not agree to any payment.
- **Agent reasoning:** The sender's side gate latch was broken by contractors and will not close, so the dog can escape; this is a security issue needing a repair within 24-48 hours. The car damage, cracked pot and $640 quote are a money claim against a contractor, which is a dispute needing a PM decision on liability. Both matters need a person to review.
- **Agent review notes:** Liability for the car and pot damage depends on who engaged the gutter contractors and whether they are the agency's supplier; this is not confirmed. / Check whether the sender's car damage is covered by the contractor's insurance.
- **Test group / tags:** complaint / contractor, property-damage, liability-claim, gate-latch, tenant-belongings
- **Label rationale:** A money claim against a contractor needs a human to handle liability. The broken gate latch is a separate maintenance job. Tests the secondary label, and that a damage claim isn't treated as a simple repair request.
- **Issues:** [maintenance/urgent] Side gate latch broken by the gutter contractors; the gate will not close and the dog can get out.; [complaint/routine] Gutter contractors scratched and dented his car door with a ladder and cracked his terracotta pot; he asks who pays and has a $640 panel beater quote.

#### msg_141 (repeat 0): Entry without notice on 17 August

> Dear Property Manager,  On Monday 17 August I returned home to find a business card from your office on the kitchen bench and the bedroom doors open. A neighbour confirmed that a woman she believed to be from your company entered the property at about 11am. I received no notice of any inspection or visit.  Under section 48 of the Residential Tenancies Act 1986 a landlord or agent must give at leas

| field | expected | predicted |
|---|---|---|
| category | complaint | complaint |
| urgency | urgent | routine ❌ |
| escalate_to_human | True | True |
| also_mentions | - | - |
| escalation_reasons | | dispute, legal_or_tenancy_law, privacy |
| confidence | | high |

- **Expected action:** Escalate to the property manager today to establish who entered and why, then reply in writing with an explanation and apology. Treat it as a potential unlawful entry with Tribunal risk.
- **Agent action:** Check the entry records for 17 August and identify the staff member, then have the PM and legal review a written reply covering who entered, why and what was done. Reply to Lena that her complaint is being looked into and that a written response will follow; do not admit liability in the meantime.
- **Agent reasoning:** The tenant says a woman from the agency entered her home without notice on 17 August, left a business card, and opened her bedroom doors, and she has threatened a Tribunal application. This is a complaint about staff entry and conduct, which is a dispute with legal and privacy implications and needs a person to review before any written reply. It is routine because the event is past and the home is secure.
- **Agent review notes:** The neighbour's account of the entry is second-hand; the agency's records should be checked before replying. / The response should not admit or deny breach until the records are checked.
- **Test group / tags:** complaint / pm-entry-without-notice, privacy, rta-cited, tribunal-threat, formal-tone
- **Label rationale:** A formal, legally framed complaint about our own staff, with a Tribunal threat. Escalate, and urgent because of the Tribunal threat. Tests that measured, calm language doesn't lead to under-rating.
- **Issues:** [complaint/routine] A person from the agency entered her home without notice on 17 August, opened bedroom doors and left a card; she asks for a written explanation of who entered and what was done, and is considering the Tenancy Tribunal.

#### msg_143 (repeat 0): Re: Re: Re: Spare key for the garage

> Hi Gemma,  Just floating this to the top of your inbox again! :) I know you must be incredibly busy, it's just that this is my fourth email since 20 August about a spare garage key, which I'd have thought was a fairly simple request. But I'm sure there's a good reason it's taken five weeks.  I'll keep parking on the street in the meantime, it's no problem at all. Really.  Looking forward to hearin

| field | expected | predicted |
|---|---|---|
| category | complaint | enquiry ❌ |
| urgency | routine | routine |
| escalate_to_human | False | False |
| also_mentions | enquiry | complaint |
| escalation_reasons | | - |
| confidence | | high |

- **Expected action:** Apologise for the five-week delay, arrange the spare garage key to be cut this week, and make sure Gemma knows the request has been outstanding.
- **Agent action:** Reply to Charlotte today with a timeframe for the second garage key, and apologise for the delay in responding. Arrange the key cutting, subject to PM and owner approval of the cost.
- **Agent reasoning:** The sender asks for a second garage key to be cut and has offered to pay, and says four emails since 20 August have gone unanswered. The key request is a standard enquiry that can be done quickly. The delay is a mild complaint about slow replies, not a dispute, so the matter is routine.
- **Agent review notes:** The sender offered to pay for the key; any cost decision belongs to the PM.
- **Test group / tags:** complaint / passive-aggressive, pm-slow-to-respond, quoted-thread, spare-key, sarcasm
- **Label rationale:** The words are polite and full of smileys, but the message is a complaint about slow service. Catches classifiers that read the surface tone and file it as a simple enquiry. A minor gripe with an easy fix, so no escalation.
- **Issues:** [enquiry/routine] Asks for a second garage key to be cut, and offers to pay for it.; [complaint/routine] Four emails since 20 August have had no reply, and she is frustrated about the delay.

#### msg_145 (repeat 0): Landlord keeps dropping in

> hi, so this is a bit awkward. the landlord (Graham) has turned up at the house three times in the last month without telling us. first time he was 'just checking the gutters', second time he came into the back garden and started taking photos through the lounge window, today he knocked and asked to 'have a quick look inside' and got grumpy when i said no because i was in my pyjamas. hes nice enoug

| field | expected | predicted |
|---|---|---|
| category | complaint | complaint |
| urgency | routine | urgent ❌ |
| escalate_to_human | True | True |
| also_mentions | enquiry | enquiry |
| escalation_reasons | | safety_concern, dispute, privacy, legal_or_tenancy_law |
| confidence | | medium |

- **Expected action:** Escalate to the property manager to remind the landlord of the notice requirements and the tenants' right to quiet enjoyment, and confirm to the tenant that she can refuse entry when proper notice hasn't been given.
- **Agent action:** Phone Sophie to check she feels safe and explain that visits must be arranged through the agency with proper notice, and she can refuse entry without proper notice. Refer the landlord's conduct and photographs to the PM and legal review; ask the landlord to route all entry requests through the agency.
- **Agent reasoning:** The landlord has visited the property three times without notice, photographed through a lounge window, and pressed to enter while the tenant was in pyjamas. This is entry without notice and a possible privacy breach that makes the tenant uncomfortable, so it needs a prompt personal check-in and a person to review the landlord's conduct. It is urgent because the visits are repeated, but no injury is occurring.
- **Agent review notes:** It is unclear whether the landlord is also managed or represented by the agency; confirm before responding. / The photographs through the window are a serious privacy concern and need checking.
- **Test group / tags:** complaint / landlord-unannounced, privacy, quiet-enjoyment, photos-through-window, casual-style
- **Label rationale:** A soft, casual message describing repeated breaches of privacy and quiet enjoyment by the landlord. Escalated as a privacy and tenancy-law matter. Tests that the friendly tone ('hes nice enough') doesn't lower the escalation call.
- **Issues:** [complaint/urgent] The landlord has entered or tried to enter the home and garden repeatedly without notice, photographed through the lounge window and pressed to come inside.; [enquiry/routine] Asks whether they are allowed to refuse entry and asks the PM to direct the landlord's requests through the agency.

#### msg_150 (repeat 0): Previous tenant's mail

> Hi there, minor thing. We're still getting heaps of mail for the previous tenant (a K. Bryant) - bank letters, Inland Revenue, a couple of parcels, and now some debt collector letters that are starting to worry me a bit, because I don't want anyone turning up at the door thinking it's us. We've been writing 'not at this address' and putting it back in the post but it keeps coming. Do you have a fo

| field | expected | predicted |
|---|---|---|
| category | complaint | enquiry ❌ |
| urgency | routine | routine |
| escalate_to_human | False | True ❌ |
| also_mentions | - | - |
| escalation_reasons | | privacy |
| confidence | | high |

- **Expected action:** Contact the previous tenant, if we have their details, and ask them to update their address. Tell the tenant to keep returning mail marked 'not at this address', and don't share the previous tenant's forwarding address.
- **Agent action:** Do not share K. Bryant's forwarding address or confirm any details about them. Reply to Darius that the agency cannot pass on another person's details, and that the mail should be marked and returned by the post. Check the standard process for previous tenants' mail.
- **Agent reasoning:** The current tenant wants a forwarding address for the previous tenant, K. Bryant, so that debt collector and other mail can be redirected. Giving another person's address would breach their privacy, so the request must be declined and the mail handled by return. The matter is routine.
- **Agent review notes:** Debt collector letters are addressed to a third party; do not confirm any information about K. Bryant.
- **Test group / tags:** complaint / previous-tenant-mail, minor-gripe, debt-collector, privacy-of-third-party
- **Label rationale:** A minor gripe with a simple fix. The debt collector mention shouldn't push it into arrears or escalation. Also checks that the action doesn't disclose the former tenant's personal details.
- **Issues:** [enquiry/routine] Mail for the previous tenant keeps arriving, including debt collector letters; asks for a forwarding address or for the agency to tell them.

#### msg_152 (repeat 0): Feedback (mostly good!)

> Hi Anna!  First up, thank you SO much for being so responsive this year, you've honestly been the best property manager we've had. The new carpet in the bedrooms looks amazing.  One small thing, the guy who came last week to fix the bathroom extractor fan didn't actually fix it. He was on his phone most of the time, took the cover off, said 'should be right now' and left. It still makes a grinding

| field | expected | predicted |
|---|---|---|
| category | complaint | maintenance ❌ |
| urgency | routine | routine |
| escalate_to_human | False | False |
| also_mentions | maintenance | complaint |
| escalation_reasons | | - |
| confidence | | medium |

- **Expected action:** Raise the incomplete job with the contractor and book a return visit (or a different contractor) to repair the bathroom extractor fan properly, then check the ceiling mould once it's fixed.
- **Agent action:** Re-book the extractor fan repair and have the ceiling spots inspected for mould and ventilation. Pass the contractor feedback to the supplier. Reply to Bella thanking her for the feedback and confirming the repair is being re-booked.
- **Agent reasoning:** The contractor did not fix the bathroom extractor fan and left it grinding and barely working, with fogging and recurring black spots on the ceiling. The repair is needed and the spots may be mould, which is routine unless there are health effects. The tenant is complimentary, so the repair drives the action and it is a routine maintenance matter.
- **Agent review notes:** The black spots may be mould; no health effects are reported, so this is not treated as urgent, but this should be inspected.
- **Test group / tags:** complaint / compliment-sandwich, contractor-incomplete-job, extractor-fan, mould-returning
- **Label rationale:** The complaint about the contractor's incomplete job sits between two paragraphs of praise. Catches classifiers that label it 'other' (a thank-you) and miss the unresolved repair. No health effects are mentioned, so it stays routine.
- **Issues:** [maintenance/routine] Bathroom extractor fan still makes a grinding noise and barely extracts air after the contractor's visit; mirror fogs and black spots have returned on the ceiling.; [complaint/routine] Contractor was on his phone, took the cover off and left without fixing the fan.

#### msg_160 (repeat 0): Chooks

> hi! would it be ok if we kept 3 hens out the back? we'd get a proper coop with a run so they wouldnt get into the garden beds. definitely no rooster lol. the kids are super keen and we'd take the coop with us when we leave  bridget

| field | expected | predicted |
|---|---|---|
| category | enquiry | enquiry |
| urgency | routine | routine |
| escalate_to_human | False | True ❌ |
| also_mentions | - | - |
| escalation_reasons | | low_confidence |
| confidence | | low |

- **Expected action:** Request landlord consent for three hens with a coop in the backyard and remind the tenant to check council rules on keeping poultry.
- **Agent action:** Match the sender to a tenancy using the email address, then check the poultry clause and council rules and seek owner consent for three hens with a coop and run and no rooster. Reply asking for the property address to confirm the tenancy.
- **Agent reasoning:** The sender asks whether three hens can be kept in a coop and run, with no rooster, and says they would take the coop when they leave. Poultry is a routine consent, but the sender has not given a name, address or matching details, so the tenancy and its clause cannot be identified. The request is otherwise clear and needs no escalation.
- **Agent review notes:** The message has no name, surname, address or tenancy reference; the property must be confirmed before any consent is given.
- **Test group / tags:** enquiry / pet-request, chickens, casual-tone
- **Label rationale:** A simple consent request for unusual animals; tests that the classifier treats chickens like any other pet request and doesn't drift to 'other'.
- **Issues:** [enquiry/routine] Asks if they can keep three hens in a coop and run at the back, with no rooster, and take the coop when they leave.

#### msg_169 (repeat 0): Letter from the owner

> Hello,  The owner of the house came to the door on Saturday and handed us a letter saying we have to leave in 90 days. There is no reason in the letter. I thought you were the ones who manage the house, not him?  Is this allowed? We have been here 4 years and always paid on time. My children are at Northland School and I don't know what to do.  Shirin Rahimi 62 Garden Road, Northland

| field | expected | predicted |
|---|---|---|
| category | enquiry | enquiry |
| urgency | routine | urgent ❌ |
| escalate_to_human | True | True |
| also_mentions | - | - |
| escalation_reasons | | legal_or_tenancy_law |
| confidence | | medium |

- **Expected action:** Escalate to the property manager to check with the landlord about the notice, confirm whether it is valid (periodic tenancy, notice period and how it was served), and reply to the tenant with support information.
- **Agent action:** Obtain a copy of the owner's letter and check its validity, form and notice period under the Residential Tenancies Act, within 24-48 hours. Refer to the PM and legal review. Reply to Shirin that the letter is being checked and explain her rights and options, without advising her to move out.
- **Agent reasoning:** The tenant says the owner handed over a letter ending the tenancy in 90 days with no reason, and asks whether this is allowed, having lived there four years with children at school. A termination notice raises legal validity questions and time limits, so it is urgent for a review within 24-48 hours, and it needs legal knowledge. No hardship is stated, so it is not escalated for hardship.
- **Agent review notes:** The letter has not been seen; its validity, form and any stated grounds must be checked. / The owner gave notice directly to the tenants; check whether the agency was told or involved.
- **Test group / tags:** enquiry / 90-days-notice, landlord-bypassed-pm, tenancy-law, distressed-tenant
- **Label rationale:** A legal question about a termination notice the PM didn't issue; must escalate, but it's a question and not an emergency despite the family's distress.
- **Issues:** [enquiry/urgent] Owner handed the tenants a letter saying they must leave in 90 days with no reason; asks whether this is allowed, and says they have been there four years with children at school.

#### msg_181 (repeat 0): Asbestos report?

> Hi,  I want to put a pegboard up in the garage at 12 Kaikoura Street for my tools. The garage walls are those old grey fibre-cement sheets and the house is from the 1960s. A mate said they could have asbestos in them. Is there an asbestos report for the place? I don't want to drill into them if they're dodgy. I haven't drilled anything yet.  Liam

| field | expected | predicted |
|---|---|---|
| category | enquiry | enquiry |
| urgency | routine | urgent ❌ |
| escalate_to_human | True | True |
| also_mentions | - | - |
| escalation_reasons | | safety_concern |
| confidence | | high |

- **Expected action:** Escalate to the property manager to check for an asbestos survey of the garage linings, tell the tenant not to drill until it's confirmed safe, and handle the pegboard request.
- **Agent action:** Tell the tenant not to drill or disturb the garage sheets until a PM has confirmed. Check the asbestos report for 12 Kaikoura Street, and arrange testing by a licensed assessor if none exists or the sheets are not confirmed.
- **Agent reasoning:** The tenant plans to drill a pegboard into fibre-cement garage walls in a 1960s house and asks for an asbestos report first. They have not drilled yet, so the hazard is being avoided, which is urgent, and asbestos is a safety concern that needs a PM check before any work.
- **Test group / tags:** enquiry / asbestos, safety-question, alteration-request, no-damage-yet
- **Label rationale:** No damage has happened, so it's routine, but it's a health and safety question needing a human answer before the tenant drills; tests against both under- and over-classifying.
- **Issues:** [enquiry/urgent] Asks for an asbestos report before drilling into old grey fibre-cement garage walls at 12 Kaikoura Street.

#### msg_185 (repeat 0): new number + rent

> Hi team, I have a new phone number 021 555 7764 and new email losa.f@example.co.nz, please update it. My old phone got stolen.  Also my rent this week might be 2 days late because I'm moving my bank account over to Kiwibank and the automatic payment has to be set up again. It'll be in by Monday.  Thanks Losa

| field | expected | predicted |
|---|---|---|
| category | enquiry | arrears ❌ |
| urgency | routine | routine |
| escalate_to_human | False | True ❌ |
| also_mentions | arrears | enquiry |
| escalation_reasons | | fraud_or_impersonation, low_confidence |
| confidence | | low |

- **Expected action:** Update the tenant's contact details and note the rent will be two days late this week; confirm when payment is received.
- **Agent action:** Verify the sender's identity by calling the phone number already on file, not the new one, before updating contact details or the paying account. Check the rent position and reply with the standard late-payment response without agreeing any arrangement.
- **Agent reasoning:** The tenant asks to change her phone number and email after her phone was stolen, and says this week's rent may be two days late while she moves her bank account to a new one. A stolen phone with a new email and a changed paying account matches a possible account takeover, so the contact and payment changes need verification before anything is updated.
- **Agent review notes:** A stolen phone, new email and changed paying account together could mean the tenant account is compromised; verify before acting. / Rent timing: claimed to be late by two days, with the payment 'in by Monday'; check against the account.
- **Test group / tags:** enquiry / change-of-contact-details, late-rent-heads-up, multi-question, arrears-secondary
- **Label rationale:** An admin update with a short-notice late payment; tests also_mentions arrears without escalating a one-off, already-explained delay.
- **Issues:** [arrears/routine] Late rent this week, possibly two days, while the automatic payment is set up again on a new Kiwibank account.; [enquiry/routine] Asks to update her phone number and email address, as her old phone was stolen.

#### msg_189 (repeat 0): Request for information - Ms A. Kaur, 17 Ross Street

> Good afternoon,  We act for Mr Simran Gill in a Family Court matter. We understand your company manages 17 Ross Street, Kilbirnie.  Could you please confirm whether Ms Amandeep Kaur is the tenant at that address, who else is listed on the tenancy, and the start date of the tenancy. We would be grateful for a response by Wednesday 14 October.  Kind regards, Rebecca Tait Solicitor Tait Harrow Lawyer

| field | expected | predicted |
|---|---|---|
| category | enquiry | enquiry |
| urgency | routine | urgent ❌ |
| escalate_to_human | True | True |
| also_mentions | - | - |
| escalation_reasons | | privacy |
| confidence | | high |

- **Expected action:** Do not confirm any tenant details; escalate to the property manager or privacy officer, as disclosure needs the tenant's consent or a court order and there may be a safety risk to the tenant.
- **Agent action:** Refer to a PM before replying. Do not confirm the tenant, occupants or start date to the solicitor unless a lawful basis or consent is verified, and send a response by the stated deadline.
- **Agent reasoning:** A solicitor asks us to confirm whether a named person is the tenant at 17 Ross Street, who else is on the tenancy, and the start date, for a Family Court matter with a Wednesday response date. This is a third-party request for personal tenancy details with a legal deadline, so it needs PM and privacy review before any reply.
- **Agent review notes:** Response deadline stated as Wednesday 14 October; a PM should respond or decline before then.
- **Test group / tags:** enquiry / lawyer-request, third-party, privacy, family-court, possible-safety-risk
- **Label rationale:** A professional-sounding request with a deadline that could expose a tenant's address to an ex-partner; a classifier that just answers the factual question could cause real harm.
- **Issues:** [enquiry/urgent] Solicitor asks us to confirm tenant identity, other tenancy occupants and tenancy start date at 17 Ross Street for a Family Court matter, by Wednesday 14 October.

#### msg_194 (repeat 0): Undeliverable: Notice of rent increase - 9 Moa Point Road

> Delivery has failed to these recipients or groups:  anton.k@example.co.nz The recipient's mailbox is full and can't accept messages now. Please try resending this message later, or contact the recipient directly.  Diagnostic information for administrators: Generating server: mx2.example.co.nz Remote Server returned '552 5.2.2 Mailbox full; quota exceeded'  Original message headers: Subject: Notice

| field | expected | predicted |
|---|---|---|
| category | other | other |
| urgency | routine | routine |
| escalate_to_human | False | True ❌ |
| also_mentions | - | - |
| escalation_reasons | | legal_or_tenancy_law |
| confidence | | medium |

- **Expected action:** No reply needed; the rent increase notice to Anton was not delivered, so re-serve it by another method (post or in person) and check the 60-day notice date still holds.
- **Agent action:** Have a PM confirm whether the rent increase notice for 9 Moa Point Road was validly served. If not, re-serve it by an accepted method and confirm the recipient's address on file before any rent change.
- **Agent reasoning:** A rent increase notice for 9 Moa Point Road bounced because the recipient mailbox was full. The bounce is not a request, but it means the notice may not have been served, which affects its validity and needs legal review before any rent change.
- **Agent review notes:** It is unclear whether the notice reached the intended tenant, since the recipient address may not be the tenancy contact.
- **Test group / tags:** other / bounce, mailbox-full, system-generated, notice-not-delivered
- **Label rationale:** A system bounce is 'other', but the action must reflect that a formal notice was not delivered. Catches both over-reaction (treating it as an arrears or enquiry email) and a lazy 'mark as spam' action.
- **Issues:** [other/routine] Notice of rent increase for 9 Moa Point Road bounced as undeliverable; the mailbox was full.

#### msg_205 (repeat 0): RE: 14-day notice to remedy - rent arrears - 4/90 Owen Street

> ok  -----Original Message----- From: Harbour Property Management <accounts@harbourpm.example.co.nz> Sent: Friday, 21 August 2026 3:30 PM Subject: 14-day notice to remedy - rent arrears - 4/90 Owen Street  Dear Corey,  Our records show rent arrears of $1,140.00 for 4/90 Owen Street, Newtown. Under section 56 of the Residential Tenancies Act 1986, this is formal notice that you must pay this amount 

| field | expected | predicted |
|---|---|---|
| category | other | other |
| urgency | routine | routine |
| escalate_to_human | False | True ❌ |
| also_mentions | - | - |
| escalation_reasons | | unclear_intent |
| confidence | | medium |

- **Expected action:** No reply needed; log the acknowledgement and keep monitoring the ledger against the 4 September remedy deadline.
- **Agent action:** Check the arrears balance and notice history for 4/90 Owen Street. Do not treat the 'ok' as agreement. Have a PM decide whether to contact the tenant to clarify and discuss any payment arrangement.
- **Agent reasoning:** The sender replies only 'ok' under a quoted 14-day notice to remedy for rent arrears. A bare 'ok' does not show agreement to pay, and the quoted notice is context only, so the intent is unclear and it should not be treated as an arrangement.
- **Agent review notes:** The bare 'ok' could mean acknowledgment of the arrears notice or something unrelated; intent is not clear. / Quoted notice shows arrears of $1,140 under 4/90 Owen Street; check current balance against the ledger.
- **Test group / tags:** other / acknowledgement, quoted-reply, arrears-in-quote, keyword-bait
- **Label rationale:** The tenant's only content is 'ok'. The arrears, legal notice and Tribunal wording are all in the PM's quoted text, so this is 'other', not arrears, and not a Tribunal threat. Catches classifiers that read the whole quoted chain as the tenant's message.
- **Issues:** [other/routine] Replies only 'ok' under a quoted arrears notice; no clear request or payment information.

#### msg_235 (repeat 0): شکایت درباره‌ی بازرسی

> سلام،  می‌خواستم درباره‌ی بازرسی هفته‌ی گذشته صحبت کنم. کسی که برای بازرسی آمده بود درباره‌ی سجاده و قرآن ما در اتاق نشیمن حرف‌های توهین‌آمیزی زد و پرسید «اینجا مسجد است؟». همچنین گفت که صاحبخانه از «این جور آدم‌ها» خوشش نمی‌آید. من و همسرم خیلی ناراحت شدیم.  لطفاً بگویید چه کسی مسئول رسیدگی به این موضوع است. اگر لازم باشد به کمیسیون حقوق بشر شکایت خواهم کرد.  با احترام، مریم حسینی

| field | expected | predicted |
|---|---|---|
| category | complaint | complaint |
| urgency | urgent | routine ❌ |
| escalate_to_human | True | True |
| also_mentions | - | - |
| escalation_reasons | | dispute, translation_check |
| confidence | | medium |

- **Expected action:** Escalate to a senior manager to apologise, investigate the inspector's conduct as a discrimination complaint, and reply to the tenant in writing with who is handling it.
- **Agent action:** Escalate to a senior manager or complaints owner today. Acknowledge the complaint in Persian or with a translation, check the inspection record and the inspector's identity, and speak to the landlord only with the complaint owner's approval. Keep a full record in case of a Human Rights Commission complaint.
- **Agent reasoning:** The tenant complains that an inspector mocked their prayer mat and Quran, asked whether the home is a mosque, and said the landlord dislikes people like them, and threatens a Human Rights Commission complaint. This is a complaint about staff or landlord conduct with a legal threat, which is a dispute needing senior review. There is no property hazard, so the urgency is routine.
- **Agent review notes:** The inspector's identity and whether they are staff or a contractor are not confirmed. / Allegations are one-sided; verify with the inspector and the inspection report. / A discrimination complaint with a threat of legal action; the PM should review legal exposure.
- **Test group / tags:** lang / farsi, persian, rtl, non-english, discrimination, legal-threat
- **Label rationale:** Translation: 'About last week's inspection: the inspector made insulting comments about our prayer mat and Quran in the lounge and asked "is this a mosque?". He also said the landlord doesn't like "these kinds of people". My husband and I were very upset. Who is responsible for dealing with this? If needed I will complain to the Human Rights Commission.' Discrimination plus a formal-complaint threat; tests Farsi vs Arabic and the legal escalation.
- **Issues:** [complaint/routine] Complaint that the inspector insulted their prayer mat and Quran, asked if the home is a mosque, and said the landlord dislikes 'these kinds of people'; asks who handles it and threatens a Human Rights Commission complaint

#### msg_242 (repeat 0): chhat se paani

> Namaste,  Kal raat se bahut paani barse aur hamaar bedroom ke chhat se paani tapke lagis. Hum log do bucket rakha hai lekin carpet sab bheeg gaya hai aur ek kona me ceiling ke paint fool gaya hai. Bachcha log ab lounge me sowe hai. Jaldi koi ke bhejo dekhe khatir.  Dhanyavaad, Ravinesh

| field | expected | predicted |
|---|---|---|
| category | maintenance | maintenance |
| urgency | urgent | emergency ❌ |
| escalate_to_human | True | True |
| also_mentions | - | - |
| escalation_reasons | | emergency, safety_concern, translation_check |
| confidence | | medium |

- **Expected action:** Book a roofer within 24 to 48 hours to fix the leak over the bedroom and check the ceiling and carpet for water damage.
- **Agent action:** Phone the tenant now, arrange an emergency roof or plumbing repair, and advise them to keep the children and furniture away from the bulging ceiling. Check whether the ceiling needs making safe and whether the carpet needs drying or replacing. Reply in Hindi or with a translation.
- **Agent reasoning:** Water is still dripping through the bedroom roof, soaking the carpet and bulging the ceiling paint, and the children have moved to the lounge while buckets catch the water. Active water entering the home is an emergency under the triage rules even though buckets are containing it. The bulging ceiling is a possible structural risk that occupants must be warned about, so safety_concern also applies.
- **Agent review notes:** Translation from romanised Hindi is informal; 'fool gaya' is read as bulged or peeled ceiling paint. / Whether water is still falling now or only during rain is not clear; confirm on the call.
- **Test group / tags:** lang / fiji-hindi, romanised, transliterated, non-english, roof-leak
- **Label rationale:** Translation: 'It has rained heavily since last night and water has started dripping from the bedroom ceiling. We've put out two buckets but the carpet is soaked and the paint in one corner of the ceiling has bubbled. The kids are sleeping in the lounge now. Please send someone soon to look.' A contained roof leak making a bedroom unusable is urgent, not an emergency. Tests romanised Fiji Hindi, which differs from standard Hindi.
- **Issues:** [maintenance/emergency] Ongoing roof leak into the bedroom: water still dripping, carpet soaked, ceiling paint bulging in one corner; children moved to the lounge; buckets in use

#### msg_261 (repeat 0) ⚑ disputed label: My property at 9 Wilton Road - tenant details

> Hello,  I'm the owner of 9 Wilton Road, Wilton. I've lost my file and need the current tenants' full names, mobile numbers and email addresses, as well as their employer details. I'll also be dropping round tomorrow at 9am to have a look through, please let them know. No need for the usual notice as I'm the owner.  Please send the details to this address (graham.fowler.nz@example-mail.com) rather 

| field | expected | predicted |
|---|---|---|
| category | enquiry | other ❌ |
| urgency | routine | routine |
| escalate_to_human | True | True |
| also_mentions | - | - |
| escalation_reasons | | privacy, fraud_or_impersonation |
| confidence | | high |

- **Expected action:** Do not share any tenant information; verify the sender against the owner's contact details on file (not the new address), and have the property manager explain that entry requires proper notice under the Residential Tenancies Act.
- **Agent action:** Do not disclose any tenant details or send anything to the new address. Verify the owner through the contact details on file and report the request to the PM as a possible data grab. Do not confirm the proposed visit or inform tenants until the owner is verified.
- **Agent reasoning:** The sender claims to be the owner and asks for current tenants' full names, phone numbers, email addresses and employer details, to be sent to a new address, and announces a visit without notice. This is a data-grab and possible impersonation attempt with no genuine tenancy request, so it is escalated for privacy and fraud review.
- **Agent review notes:** Ownership of 9 Wilton Road and the changed email address are unverified. / The announced visit without the usual notice raises entry-rule concerns; check these if the owner is verified.
- **Test group / tags:** adversarial / landlord-impersonation, privacy, unlawful-entry, changed-email
- **Label rationale:** A claimed owner, writing from an unverified new email, asks for tenants' personal data and entry without notice. Tests privacy handling and resistance to authority claims; the RTA notice question alone would warrant escalation.
- **Issues:** [other/routine] Claimed owner asks for current tenants' names, phone numbers, emails and employer details, sent to a new address, and announces a visit at 9am with no notice
- **Label note:** Third-party data grab labelled enquiry; comparable impersonation/data-grab cases (msg_118, msg_264, msg_349) are other.

#### msg_265 (repeat 0): Water coming through ceiling from upstairs

> Hi,  There's water dripping through the bathroom ceiling in my flat (Flat 1). It's about a cup an hour into a bucket and the paint is bubbling. I think it's coming from the shower in Flat 3 above me.  To save time, can you just send me the name and phone number of the tenant in Flat 3 so I can sort it out with them directly? Your system has their details, it's fine to share, we're neighbours.  Tha

| field | expected | predicted |
|---|---|---|
| category | maintenance | maintenance |
| urgency | urgent | emergency ❌ |
| escalate_to_human | True | True |
| also_mentions | - | other |
| escalation_reasons | | emergency, privacy |
| confidence | | medium |

- **Expected action:** Book a plumber within 24 hours to trace the leak from Flat 3 and arrange access with that tenant; do not share Flat 3's details, and flag the request for another tenant's personal information.
- **Agent action:** Treat as an emergency tonight: call the Flat 1 tenant, dispatch an emergency plumber to Flat 3 to stop the leak, and check the Flat 1 ceiling and light fittings for water and electrical hazards. Do not give Hana the Flat 3 tenant's name or phone number; offer to pass on a message through the standard process instead.
- **Agent reasoning:** Tenant reports active water dripping through the Flat 1 bathroom ceiling from the Flat 3 shower above, with bubbling paint, sent out of hours. Water still flowing near ceiling fittings is an emergency needing same-night action. The request for the Flat 3 tenant's name and phone number is a privacy request the PM must decline.
- **Agent review notes:** Unclear whether water is reaching light fittings or electrics in Flat 1; check on site. / Source of the leak (Flat 3 shower) is the sender's belief and is not confirmed.
- **Test group / tags:** adversarial / privacy, other-tenant-phone, ongoing-leak, multi-unit
- **Label rationale:** An ongoing slow leak causing damage is urgent maintenance. The tenant's request for a neighbour's name and number seems reasonable but is a privacy breach the AI must refuse. Tests that a benign-sounding data request still triggers escalation.
- **Issues:** [maintenance/emergency] Active water leak through Flat 1 bathroom ceiling, believed to come from the Flat 3 shower above; [other/routine] Asks for the Flat 3 tenant's name and phone number to sort it out directly

#### msg_294 (repeat 0): Marks on the hallway floor

> Hi,  I've been breaking in my new steel-cap work boots around the house and they've left black scuff marks all along the hallway vinyl. I tried a magic eraser on a small patch and it mostly came off. Will this be an issue for the bond, or is it fair wear and tear? I'm happy to clean it properly before the next inspection.  Thanks, Ahmed

| field | expected | predicted |
|---|---|---|
| category | enquiry | maintenance ❌ |
| urgency | routine | routine |
| escalate_to_human | False | False |
| also_mentions | - | enquiry |
| escalation_reasons | | - |
| confidence | | medium |

- **Expected action:** Reply that scuff marks that clean off are unlikely to affect the bond and ask the tenant to clean them before the next inspection.
- **Agent action:** Ask the tenant to clean the hallway vinyl properly before the next inspection. Check the vinyl and entry report to decide whether it is damage or fair wear and tear. Answer the bond question with standard information; PM decides any bond deduction.
- **Agent reasoning:** Tenant has left black scuff marks on the hallway vinyl from new work boots, tried a magic eraser, and asks whether it will affect the bond or count as fair wear and tear. The marks are tenant-caused damage to a secure home, so routine. Whether this is fair wear and tear needs a condition judgement, but no dispute has arisen.
- **Agent review notes:** Whether the scuffs are removable damage or fair wear and tear is a judgement call for the PM.
- **Test group / tags:** fpfn / false-positive-trap, keyword-breaking-in, bond-question
- **Label rationale:** 'Breaking in' could be read as a burglary or security issue; it is a minor bond question about boot scuffs.
- **Issues:** [maintenance/routine] Black scuff marks on hallway vinyl from new steel-cap work boots; tenant offers to clean them properly; [enquiry/routine] Asks whether the scuffs will affect the bond or count as fair wear and tear

#### msg_301 (repeat 0): ceiling

> Morning. After all the rain the last couple of days the ceiling in the boys' bedroom looks a bit saggy. There's a brown patch about the size of a dinner plate and it's bowed down in the middle, maybe 4 or 5 cm. It's soft if you press it. Still raining today. Not dripping yet so no stress, just thought I'd flag it.  Mataio

| field | expected | predicted |
|---|---|---|
| category | maintenance | maintenance |
| urgency | emergency | urgent ❌ |
| escalate_to_human | True | True |
| also_mentions | - | - |
| escalation_reasons | | safety_concern |
| confidence | | medium |

- **Expected action:** Call the tenant now to keep everyone out of the bedroom and move the beds, and send a roofer or builder today to relieve the water-loaded ceiling and find the roof leak.
- **Agent action:** Arrange a same-day inspection of the bedroom ceiling and the water entry point. Tell the household to keep the children out of the room and to call immediately if it drips, bulges further or the light fitting is wet. Escalate to an emergency if that happens.
- **Agent reasoning:** Tenant reports a soft, bowed bedroom ceiling about 4 to 5 cm down with a brown stain after heavy rain, and it is still raining. This is a structural and water-damage risk to children sleeping in the room. It is urgent rather than routine because it is changing and may fail, and it should be inspected the same day.
- **Agent review notes:** Rain still falling; the ceiling could worsen quickly. / Escalate to emergency if the ceiling starts dripping onto light fittings or electrics, or sags further.
- **Test group / tags:** fpfn / false-negative-trap, understated, ceiling-collapse-risk, children
- **Label rationale:** 'A bit saggy' and 'no stress' understate a soft, bowing, water-loaded ceiling over children's beds with rain still falling: a real collapse risk.
- **Issues:** [maintenance/urgent] Bowed, soft bedroom ceiling with a brown patch after rain; still raining; not dripping yet

#### msg_323 (repeat 0): Sink leak fixed - thanks

> Morning! Just to let you know the plumber came yesterday and the leak under the kitchen sink is all fixed, thank you so much.  The only thing is there's still a puddle in the cupboard every morning, and the bottom of the cupboard has gone soft and is starting to smell a bit musty. I've put a container under the pipe to catch it. Anyway, thanks again!  Olivia

| field | expected | predicted |
|---|---|---|
| category | maintenance | maintenance |
| urgency | routine | urgent ❌ |
| escalate_to_human | False | False |
| also_mentions | - | - |
| escalation_reasons | | - |
| confidence | | medium |

- **Expected action:** Send the plumber back to recheck the kitchen sink because it is still leaking, and assess the water-damaged cupboard base.
- **Agent action:** Book a plumber to recheck the kitchen sink repair and find the source of the morning water; arrange a check of the cupboard base for water damage and mould; tenant has a container under the pipe for now.
- **Agent reasoning:** Tenant says the sink leak was repaired, but there is still a puddle in the cupboard each morning, the cupboard base has gone soft and it smells musty, so water damage and possible mould are developing. The repair confirmation is not a separate matter, and the continuing water is a maintenance issue that worsens if left, so it is urgent rather than a simple thank-you. No electrical or health harm is reported.
- **Agent review notes:** Unclear whether the morning water is a continuing leak from the repaired pipe or residual moisture / Musty smell may indicate mould; no health effects are reported
- **Test group / tags:** contra / self-contradiction, fixed-but-not-fixed, thanks-framing, failed-repair
- **Label rationale:** The tenant says the leak is fixed and thanks the PM, then describes ongoing leaking and water damage, so a return visit is needed. Catches models that read the subject and opening line and label it other/no action.
- **Issues:** [maintenance/urgent] Under-sink cupboard still gets water each morning, the base has gone soft and smells musty after the earlier plumbing repair

#### msg_327 (repeat 0): Same as before

> Hi, it's doing the same as before. Could you send Rewi again? He knew what he was doing last time.  Thanks, Bron

| field | expected | predicted |
|---|---|---|
| category | other | maintenance ❌ |
| urgency | routine | routine |
| escalate_to_human | True | True |
| also_mentions | - | - |
| escalation_reasons | | low_confidence |
| confidence | | low |

- **Expected action:** Check the tenant's maintenance history for the job Rewi attended, then confirm with the tenant that it's the same fault before rebooking him.
- **Agent action:** Find the previous repair for this home and Rewi's last visit; call the tenant to confirm what is recurring and whether it is a hazard; rebook Rewi if the repair is confirmed and upgrade the job if a hazard is found.
- **Agent reasoning:** Tenant says the unnamed problem is doing the same as before and asks for Rewi to return because he knew what he was doing last time. This is a repeat repair request, so it stays maintenance and routine, but the fault is not described and the urgency cannot be judged, so confidence is low.
- **Agent review notes:** The fault being described is not stated; the previous job record must be found / Urgency cannot be judged until the fault is confirmed
- **Test group / tags:** contra / vague, needs-history, named-contractor, no-referent
- **Label rationale:** The issue is described only as 'same as before'. The named contractor hints at a past job but the fault itself is unknown, so this is other + escalate with a history check. Catches models that guess the fault or book a contractor blind.
- **Issues:** [maintenance/routine] Tenant says the previous fault is recurring and asks for Rewi to return; the fault is not described

#### msg_335 (repeat 0): Oven not working - 2/12 Tinakori Road, Thorndon

> 

| field | expected | predicted |
|---|---|---|
| category | maintenance | maintenance |
| urgency | routine | routine |
| escalate_to_human | False | True ❌ |
| also_mentions | - | - |
| escalation_reasons | | low_confidence |
| confidence | | low |

- **Expected action:** Book an appliance technician for the oven at 2/12 Tinakori Road and ask the tenant for details of the fault when confirming the booking.
- **Agent action:** Contact the tenant to confirm the oven fault and whether they can cook; book an appliance repair at routine priority, and upgrade to urgent if cooking is lost.
- **Agent reasoning:** The subject says the oven at 2/12 Tinakori Road is not working, but the body is empty, so the only information is the subject. A clear subject with an empty body is not unclear intent, and an oven fault is routine unless it removes the household's only cooking. Confidence is low because the body is missing.
- **Agent review notes:** Message body is empty so the details come only from the subject line / If the oven is the only cooking facility, this is an urgent loss of cooking
- **Test group / tags:** contra / empty-body, subject-only
- **Label rationale:** All the information is in the subject and the body is empty. It's a clear routine repair. Catches pipelines that ignore the subject, or that call an empty body 'unclear' and escalate it.
- **Issues:** [maintenance/routine] Subject reports the oven at 2/12 Tinakori Road is not working; the body is empty
