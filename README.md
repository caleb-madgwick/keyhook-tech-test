# Tenant Message Triage Agent

This is an LLM agent that triages tenant messages for a property manager (PM). An evaluation harness scores it against labelled data.

For each message the agent returns a category, an urgency, a next action, whether a person must review it first and why, and its reasoning.

## Running it

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env              # add OPENROUTER_API_KEY
.venv/bin/python -m pytest -q     # 154 offline tests, no API calls

# Triage any JSON file shaped like tenant_emails.json (labels optional)
.venv/bin/python -m triage.agent --input tenant_emails.json --out results.jsonl

# Evaluate. Writes reports/<dataset>__<model>__<prompt>.md and exits 1 if a safety gate fails
.venv/bin/python -m triage.eval --dataset tenant_emails.json          # the 30 seed messages
.venv/bin/python -m triage.eval --split dev                           # extended suite, dev split
.venv/bin/python -m triage.compare --split dev                        # several models side by side
```

**Configuration.** The model, fallbacks, temperature, token limits, retries, prompt version, judge model and spend caps are all in [config.yaml](config.yaml). You can switch the model with `--model <openrouter-id>` or with `TRIAGE_MODEL=<id>`.

Eval results are cached per model, prompt hash and message, so running a model again costs nothing. Add `--no-judge` to skip the LLM judge.

## Approach and key decisions

**1. The LLM extracts facts and code makes the decisions.** The model returns a list of issues, each with its own category and urgency, plus the reasons it thinks a person should review the message and how confident it is. Code ([triage/guardrails.py](triage/guardrails.py)) then derives the final fields:
- **Urgency** is the highest urgency across all issues. An emergency buried in small talk can't be averaged away.
- **Category** is the primary issue. That is always one of the most urgent issues; the model's choice only breaks ties.
- **escalate_to_human** is true if any reason applies.

Every rule in code can only push a message towards a person, never away. Making these decisions in code means they are testable and can't be argued away by the message text.

**2. Changes to the schema I was given, and why:**

| Field | Why it's there |
|---|---|
| `issues[]` with `also_mentions` | This is how I handle messages with more than one request. Each matter gets its own category, urgency and action, and nothing is dropped. `also_mentions` matches how the dataset is labelled. |
| `escalation_reasons[]` instead of a bare boolean | A PM needs to know *why* a message is in their queue, e.g. `hardship`, `legal_or_tenancy_law`, `manipulation_attempt`. Reasons can also be audited and measured. |
| `confidence` and `review_notes` | Low confidence escalates automatically. The report checks whether "low" really predicts errors. If it doesn't, the signal should be dropped. |
| `languages` and `language_mix` | A non-English message is escalated so someone checks the translation before anyone acts or replies. This includes messages the model thinks need no action, because that judgement depends on the model reading the language correctly. |

**3. Plain code where it does the job better than an LLM:**
- **Injection detection.** A regex backstop catches the obvious attacks, and a hit forces human review whatever the model says. The model is the main defence. The regex makes sure the blatant attacks never depend on the model.
- **Obfuscation.** Code strips invisible characters (zero-width, bidi controls and Unicode tag characters) and decodes base64. Bidi marks and flag-emoji tags are not counted as obfuscation, because RTL email and subdivision flags use them legitimately. The decoded text is shown to the model inside the untrusted block, never as an instruction.
- **Time of day.** Code works out whether a message arrived inside NZ business hours.
- **Spend caps, retries and output validation** are all code.

Tenant text always sits inside a `<tenant_message>` delimiter and is treated as data, never instructions.

**4. Fail closed.** If the model errors, times out, truncates its answer or returns invalid JSON twice, the message is escalated as `triage_failed`. It's marked `urgent`, or `emergency` if it mentions things like gas, fire or flooding. A message is never dropped and never auto-handled without a model answer.

**5. Assumptions.** Messages are from New Zealand tenancies: the data mentions the toby, WINZ and +12:00 timestamps, so the prompt refers to the Residential Tenancies Act and the Healthy Homes Standards. The agent recommends actions; it never takes them or makes promises on the PM's behalf.

## Model choice and cost

**Agent model: `anthropic/claude-haiku-5.5`**, with strict JSON-schema output and the model's default sampling. Haiku 5.5, Sonnet 5.5 and GPT-6 don't accept `temperature` on OpenRouter, so the config doesn't send it. Triage is a short classification-and-extraction task over a fairly long rulebook, so a small, cheap model with reliable structured output fits. The comparison runs it against `openai/gpt-6-luna`, `google/gemini-3.5-flash-lite`, `deepseek/deepseek-v4-flash` and `anthropic/claude-sonnet-5.5` as a quality ceiling.

**Status: chosen on design grounds, not yet benchmarked against the API.** I deliberately spent none of the OpenRouter budget until the pipeline was complete and validated. All results below come from **replay mode** (see *How the numbers were produced*), with Claude Haiku subagents standing in for Haiku 5.5. The rule for the real comparison is: **pick the cheapest model that passes every safety gate.** It is one command, `python -m triage.compare --split dev`, about US$2–4 for 5 models × 256 messages, most of it Sonnet 5.5. That's the next step before production.

Provider routing requires structured-output support and sets `data_collection: deny`, because tenant messages contain personal information.

**Estimated cost per 1,000 messages: about US$0.61 without caching, before thinking tokens.** Budget about $1 per 1,000 to cover thinking, token-count error and retries.

| Item | Tokens per message (mean, 349-message suite, prompt v5) | Haiku 5.5 price (per million tokens) | Cost per message |
|---|---|---|---|
| Input: system prompt 3,381 + JSON schema 746 + message ~208 | 4,335 | $0.10 | $0.00043 |
| Output (structured JSON) | 353 | $0.50 | $0.00018 |
| Thinking | not measured | $0.50 | +$0.00005 per 100 tokens |

What these numbers can't show yet:
- **Token counts are estimates.** They come from the exact requests the agent builds, at bytes/3.5, because no API call was made. Haiku 5.5's tokenizer counts about 30% more tokens than Haiku 4.5's for the same text, so the real counts may be higher.
- **Thinking is extra.** Haiku 5.5 thinks adaptively by default, and the config keeps that default (`reasoning: null`). Thinking is billed as output and isn't in the replay answers.
- **Prices** are OpenRouter list prices on 2026-10-14, the same as Anthropic's. The first real run replaces all of this with the provider-reported `usage.cost`, which the harness records per message, along with cached input tokens.

**Prompt caching** (`prompt_cache: true` in [config.yaml](config.yaml)) marks the system prompt as a cache breakpoint. A cache hit reads it at 0.1× the input price; a miss writes it at 1.25×, and the cache lasts 5 minutes from its last use.

| Traffic | Cost per 1,000 messages |
|---|---|
| Every message within 5 minutes of the last (eval runs, a busy inbox) | about $0.31 |
| No caching | about $0.61 |
| Every message more than 5 minutes apart (a quiet inbox) | about $0.69 |

Caching pays off once more than about 1 in 5 messages arrives within 5 minutes of the previous one. For a very quiet inbox, turn it off.

For comparison, the same workload on Sonnet 5.5 would be about $12 per 1,000 without caching. The LLM judge runs only in evaluation (`openai/gpt-6-sol`, a different model family from the agent to reduce self-preference bias). It isn't a production cost.

## Evaluation

**Data.** There are two datasets, with very different standing:

| File | Source | Messages | Labels |
|---|---|---|---|
| `tenant_emails.json` | **Provided by Keyhook** | 30 | Written by Keyhook: the only real ground truth here |
| `tenant_emails_test_suite.json` | **Generated by me with AI** for this exercise | 349 = Keyhook's 30, copied in unchanged, + 319 generated | The 319 generated labels were written by AI along with the messages, each with a rationale. No property manager has checked them. |
| `data/blind_set.json` | **Generated by a Claude subagent** as a second blind set, never read by me or the prompt | 80 | Labelled by that subagent, which followed the suite's conventions. Only aggregate scores were ever looked at. |
| `data/blind_test_set.json` | **Generated by ChatGPT** as a blind test, after the prompt was frozen | 120 (17 emergency, 31 urgent, 72 routine; 29 multi-issue; 8 injection or phishing; 13 with Samoan, Tongan, Mandarin or Hindi content, plus 8 with te reo greetings) | Labelled by ChatGPT. Cross-checked against Keyhook's seed labels, and 6 labels were corrected. Each correction is logged in `data/blind_label_review.json` with the original label. |

- **The blind set.** I added it because the holdout above isn't fully blind (see the caveats below). ChatGPT saw only Keyhook's label definitions and two of their example messages. It never saw this agent's prompt or the generated suite. Using a different model family from the agent also reduces the chance that the agent scores well just by agreeing with labels written in its own style. The set is built and validated by `scripts/build_blind_set.py`.
- **Label review. These corrections were made *after* the v4 and v5 runs on this set, not before** (git timestamps: frozen v4 result 23:29, v5 runs 23:35, label corrections 23:39; the committed file has the original labels). In 5 of the 6, the corrected label matches v5's prediction. The results are therefore reported under both the original and corrected labels, and the original labels are the honest basis (see *Results*).
  - **Corrections.** I cross-checked ChatGPT's labels against how Keyhook labelled similar seed messages and changed 6 labels in 6 messages. Five of them follow Keyhook's own conventions:
    - a lockout is `maintenance`
    - a vague "it's happening again" message is `other`
    - routine consent requests aren't escalated
    - two secondary categories had no basis in the message
  - **Consistency fix.** The sixth makes two family-violence messages consistent with each other. Its `emergency` urgency was deliberately left unchanged.
  - **Hand-check.** TODO: hand-check the 17 emergencies and the 18 low-confidence labels, and record them in `checked_ids`.

- **Why I generated a suite.** 30 messages contain only 2 emergencies, a single injection attempt and no non-English text. That's too few to test the failure modes that matter. The generated messages cover 10 groups of about 30 messages each, targeting specific risks:
  - emergencies and near-misses
  - non-English and mixed-language messages
  - prompt injection and impersonation
  - keyword and tone traps
  - contradictory and multi-intent messages
  - inbox noise
- **Splits.** There is no training in the machine-learning sense; only the prompt is tuned. The generated messages are split by a fixed hash into **dev** (used while iterating on the prompt) and **holdout** (scored only, failures not read). Keyhook's 30 are always in dev. That gives 256 dev and 93 holdout messages.
- **Headline numbers.** The Keyhook set is reported separately and treated as the headline. The generated suite is evidence about specific failure modes, not a measure of real-world accuracy.

**What the harness measures** ([triage/eval.py](triage/eval.py), [triage/metrics.py](triage/metrics.py)):
- **Exact metrics for the structured fields:**
  - category accuracy, both strict and lenient (lenient means the prediction is any labelled category)
  - urgency accuracy, split into **under-triage** (dangerous) and **over-triage**
  - emergency recall
  - escalation recall, precision and F1
- **An LLM judge for `required_action`.** It scores the action from 0 to 2 against the labelled action and flags unsafe actions, such as promising money or following instructions in the message.
- **Breakdowns** by split, test group, tag and model-reported confidence.
- **Reliability and cost:** fail-safes, retries, latency, tokens, cost per message, and consistency across repeated runs.
- **Safety gates** that make the run exit non-zero:
  - every emergency is caught
  - escalation recall is at least 90%
  - there are no fail-safes and no unsafe actions
  - per-message checks, such as "the gas leak in msg_014 is an emergency" and "the injection in msg_016 is escalated and not an emergency"

Labels I think are debatable were recorded in [data/label_notes.json](data/label_notes.json) *before any model run*. They are flagged ⚑ in reports rather than quietly changed.

### Results

**How the numbers were produced: replay, no API spend.** Every number below comes from the real pipeline: pre-checks, schema validation, policy code, metrics and gates. Only the model call is replaced by recorded answers. The stand-in is weaker evidence than a real run:
- **Stand-in model.** Claude Haiku subagents answered the exact system prompt and message the agent would send, without seeing labels.
  - Each subagent answered about 20–45 messages in one context, not one isolated call each.
  - The JSON schema was given as text, not enforced through strict structured output.
  - The model version and sampling settings aren't controlled.
  - Their instructions forbade reading other files, but nothing logs that they didn't.
- **Judge.** Claude Sonnet subagents graded the actions. That's a different model from the stand-in, but **the same family**: Claude wrote the suite labels, wrote the second blind set, stands in for the agent and judges. The configured production judge (`openai/gpt-6-sol`) is a different family for exactly this reason, but it wasn't used here.
- **Validity checks.** Replay answers are keyed to a hash of the exact system prompt and message, so a stale answer can't be scored against a changed prompt.
- **Costs** are token *estimates* priced at Haiku 5.5 rates.
- **What's still needed:** one real API run (`triage.compare --split dev`, a few dollars) to confirm all of this for `anthropic/claude-haiku-5.5`. It would also be the first test of the live path: provider routing, strict schemas and the retry logic.

**Final configuration: prompt v5, policy `escalate_on_confidence: [low, medium]`.** All safety gates pass on every dataset.

| Dataset | Pass rate (all 3 fields) | Category | Urgency | Under / over-triage | Emergency recall | Escalation recall / precision | Action (judge 0–2) | Unsafe actions |
|---|---|---|---|---|---|---|---|---|
| **Keyhook-provided (30)** | 90% | 97% | 100% | 0 / 0 | 100% (2) | 100% / 88% | 1.90 | 0 |
| Generated suite: dev (256) | 76% | 94% | 94% | 0 / 15 | 100% (30) | 100% / 79% | 1.83 | 0 |
| Generated suite: holdout (93) | 71% | 90% | 91% | 2 / 6 | 100% (11) | 98% / 78% | 1.85 | 0 |
| Blind set, Claude-written (80) ¹ | 78% | 96% | 92% | 1 / 5 | 100% (8) | 100% / 76% | 1.90 | 0 |
| **ChatGPT set, first 90, original labels** ² | 73% | 87% | 94% | 2 / 3 | 100% (16) | 98% (51/52) / 88% | 1.92 | 0 |
| ChatGPT set, first 90, corrected labels ² | 76% | 89% | 94% | 2 / 3 | 100% (16) | 100% (51/51) / 88% | 1.92 | 0 |
| **ChatGPT set, last 30, blind for v5** ³ | 70% | 97% | 93% | 2 / 0 | 100% (1) | 92% (11/12) / 69% | 2.00 | 0 |
| *Keyword rules, no LLM* (`triage.baseline`), first 90, original labels | 22% | 52% | 64% | 23 / 9 | 19% | 23% / 80% | n/a | n/a |

1. **Claude-written blind set.** It was never read and only its aggregates were used. But aggregates from it informed the medium-confidence policy decision, so it is *not* blind for that policy. It is blind for the v5 prompt rules.
2. **First 90 ChatGPT-labelled messages: post-hoc for v5.** v5 was written after I read their safety failures. **Six labels in this set** (blind_014, 026, 043, 049, 059 and 088) **were corrected after the v4 and v5 runs on it**, not before; the committed file has the original labels. In 5 of the 6, the corrected label now matches v5's prediction. The original labels are the honest basis, which is why both rows are shown. The judge scored actions against the label file as it was when the judge ran.
3. **Last 30 ChatGPT-labelled messages: blind for v5.** They were added after the v4 inspection and never read. The label corrections don't touch them. With 12 escalations and 1 emergency, the 95% interval on 92% escalation recall is roughly 62–100%. **That makes it thin evidence.**

Estimated cost: **about US$0.61 per 1,000 messages** without caching (4,335 input and 353 output tokens per message on the suite; see *Model choice and cost*).

**The official blind result is the pre-registered one, recorded before any inspection.** That is v4, under the policy in force at the time (low-confidence escalation only), on the **original** labels of the first 90 ChatGPT-labelled messages:
- pass rate 71%
- category 84%
- **emergency recall 88% (2 of 16 missed)**
- escalation recall 90% (47/52)
- 2 unsafe actions

[reports/FROZEN_blind_test_set_v4.json](reports/FROZEN_blind_test_set_v4.json) records this together with the medium-confidence variant (94%). That variant was chosen *after* seeing this set, so it isn't the official number. Everything after it, including v5, the medium-confidence policy and the emergency-preamble fixes, was influenced by this set's failures.

**Blind sets stay blind in the repo.** Reports for any dataset whose name contains "blind" contain only aggregates. Per-message errors are withheld by `triage/report.py`, and the earlier reports that included them were deleted.

**The pass rate is deliberately traded for safety.** Escalating medium-confidence answers and the stricter v5 emergency rules raise recall and lower precision. Under v4, with low-confidence-only escalation, the suite pass rate was 89% against 75–76% now. The difference is almost all extra escalations (false positives about 9 → 52) and over-triage (8 → 21). In practice about 57–69% of messages reach a person. That's a business decision about PM workload; one config line restores the leaner policy, and the trade-off table is in the changelog. **Under-triage is close to zero everywhere** (at most 2 per set), and no action is unsafe.

### What these results do and don't tell you

- **The real ground truth is small.** On the Keyhook set, one message is about 3 percentage points, and 2 emergencies make "100% emergency recall" a weak claim on its own. The generated suite adds 39 emergencies, but with AI-written labels.
- **Generated labels measure consistency, not correctness.** The same kind of model wrote the messages, wrote their labels and does the triage. A high score on the generated suite shows the agent applies a consistent policy. It doesn't show that the policy matches how a real PM would act, and it may flatter a model from the same family. Generating more messages the same way would add volume, not validity.
- **The holdout is optimistic.** The labelling conventions in the prompt were worked out from all 349 labels, and a few holdout messages were read while tuning the injection regex. It is blind to prompt iteration, but not to conventions. The ChatGPT blind set is the cleaner out-of-sample number, and Keyhook's unseen messages are the real test. See [PROMPT_CHANGELOG.md](PROMPT_CHANGELOG.md).
- **The judge's score is a proxy.** I haven't calibrated it against human ratings.

## Where it fails or is weakest

**What the eval runs actually showed**, in order of importance:
- **The biggest failure is a labelling convention the model can't infer: when a hazard counts as active.** The Claude-labelled suite treats a door that can't be locked after a burglary as *urgent*. The ChatGPT set treats the same situation as an *emergency*. Under v4 the agent missed 2 of 16 ChatGPT-labelled emergencies this way. v5 now chooses emergency. That costs over-triage on the suite (21 messages), and it shows that **the urgency boundary needs a decision from Keyhook, not a better model.**
- **Free-text emergency advice can't be left to the model.** It twice made a 111 call conditional ("if smoke returns") while smoke was present. Fixed safety wording now comes from code.
  - My own first version of that fixed wording said "phone the tenant now" to a family-violence victim who had asked not to be phoned. The judge caught it and the wording was fixed. Fixed wording needs reviewing as carefully as model output.
- **Granting things it shouldn't.** Under v4 the model granted an alteration consent and a change of payment frequency in its proposed action. v5 forbids granting anything; the judge found no further cases.
- **Complaints vs requests** remain the weakest category, at about 70–80% in the complaint group. The model files a gripe that contains a request as the request.
- **Large variation between runs.** Between two prompt versions, 14 dev messages were fixed and 12 broke. Much of that is variation between model instances, so 1–3 point differences in pass rate aren't meaningful; the gates check every run.
- **"Low" confidence carries little signal; "medium" does.** Medium-confidence answers pass far less often (73% vs 98% for high on the Claude blind set), which is why medium now escalates.

Weak spots expected from the design:
- **Escalation is the softest label.** The labels themselves are inconsistent about where a judgement call ends and a standard workflow begins. [data/label_notes.json](data/label_notes.json) lists 16 such cases. Expect most errors here, mostly over-escalation, which is the safe direction.
- **The primary category in multi-issue messages is often debatable**, e.g. an angry complaint about an unresolved repair. The lenient category score exists for this reason.
- **The injection regex** catches roughly a third of the suite's attacks. The rest rely on the model. Novel phrasing in Keyhook's unseen messages is the biggest unknown.
- **The prompt is long** (about 3k tokens) and encodes conventions from this dataset. It may overfit to these labelling habits and generalise less well.
- **Rules can over-escalate.** The non-English rule escalates every non-English message, even ones the model reads as needing no action, and low or medium confidence escalates too. Both are deliberate choices that cost PM time.
- **Each message is triaged on its own.** The agent has no tenancy history, open jobs or previous messages, so it can't tell a follow-up from a new issue.

## Before I'd trust it with real tenants

1. **Shadow mode first.** Run it on real inbound mail alongside PMs for several weeks, with real PMs labelling a sample. Measure under-triage and missed escalations against their decisions, not against synthetic labels.
2. **No autonomous actions.** At first it only sorts and prioritises the queue; a person reads everything. Emergencies trigger a page or phone call, not just a queue position. Auto-handling non-escalated routine messages would come later, and only once shadow-mode data supports it.
3. **Agreed thresholds.** Zero missed emergencies over a meaningful real sample, and a missed-escalation rate the business accepts in writing.
4. **Operational basics:**
   - provider fallback and alerting when the fail-safe rate spikes
   - logging of every decision with its prompt version
   - a privacy review of sending tenant personal information to a third-party model
5. **Ongoing evaluation.** Messages PMs re-triage feed back into the eval set, and any prompt or model change must pass the gates before release.

## Repository map

| Path | What's in it |
|---|---|
| `triage/agent.py` | Pipeline: precheck → model call (with retries and schema fallback) → policy |
| `triage/guardrails.py` | Injection and obfuscation detection, policy derivation, fail-safe |
| `triage/prompts.py` | Versioned system prompts, with history in `PROMPT_CHANGELOG.md` |
| `triage/eval.py`, `metrics.py`, `report.py`, `judge.py`, `compare.py` | Evaluation harness |
| `triage/replay.py`, `offline.py` | Score recorded model outputs without API spend |
| `scripts/build_blind_set.py`, `data/blind_raw/` | Build and validate the ChatGPT blind test set |
| `reports/` | Eval reports, plus an independent AI code review I commissioned (`senior_engineer_review.md`) and the fixes made in response |
| `ai-sessions/` | AI session history: my prompts and a readable transcript of each Claude Code session, including subagent briefs and reports (see its README for what's included) |
