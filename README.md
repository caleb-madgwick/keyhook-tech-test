# Tenant Message Triage Agent

This is an LLM agent that triages tenant messages for a property manager (PM). An evaluation harness scores it against labelled data.

For each message the agent returns a category, an urgency, a next action, whether a person must review it first and why, and its reasoning.

## Running it

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env              # add OPENROUTER_API_KEY
.venv/bin/python -m pytest -q     # 94 offline tests, no API calls

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
| `languages` and `language_mix` | A non-English message that needs action is escalated so someone checks the translation before anyone replies. |

**3. Plain code where it does the job better than an LLM:**
- **Injection detection.** A regex backstop catches the obvious attacks, and a hit forces human review whatever the model says. The model is the main defence. The regex makes sure the blatant attacks never depend on the model.
- **Obfuscation.** Code strips zero-width characters and decodes base64. The decoded text is shown to the model inside the untrusted block, never as an instruction.
- **Time of day.** Code works out whether a message arrived inside NZ business hours.
- **Spend caps, retries and output validation** are all code.

Tenant text always sits inside a `<tenant_message>` delimiter and is treated as data, never instructions.

**4. Fail closed.** If the model errors, times out, truncates its answer or returns invalid JSON twice, the message is escalated as `triage_failed`. It's marked `urgent`, or `emergency` if it mentions things like gas, fire or flooding. A message is never dropped and never auto-handled without a model answer.

**5. Assumptions.** Messages are from New Zealand tenancies: the data mentions the toby, WINZ and +12:00 timestamps, so the prompt refers to the Residential Tenancies Act and the Healthy Homes Standards. The agent recommends actions; it never takes them or makes promises on the PM's behalf.

## Model choice and cost

**Agent model: `anthropic/claude-haiku-5.5`**, temperature 0, with strict JSON-schema output. Triage is a short classification-and-extraction task over a fairly long rulebook, so a small, cheap model with reliable structured output fits. The comparison runs it against `openai/gpt-6-luna`, `google/gemini-3.5-flash-lite`, `deepseek/deepseek-v4-flash` and `anthropic/claude-sonnet-5.5` as a quality ceiling.

**Status: chosen on design grounds, not yet benchmarked against the API.** I deliberately spent none of the OpenRouter budget until the pipeline was complete and validated. All results below come from **replay mode** (see *How the numbers were produced*), with Claude Haiku subagents standing in for Haiku 5.5. The rule for the real comparison is: **pick the cheapest model that passes every safety gate.** It is one command, `python -m triage.compare --split dev`, about US$1.50 for 5 models × 256 messages. That's the next step before production.

Provider routing requires structured-output support and sets `data_collection: deny`, because tenant messages contain personal information.

**Estimated cost per 1,000 messages: about US$0.51** (allow about $0.60 for retries and the occasional long email).

| Item | Tokens per message (mean, 349-message suite) | Haiku 5.5 price (per million tokens) | Cost per message |
|---|---|---|---|
| Input (system prompt, schema and message) | 3,376 | $0.10 | $0.00034 |
| Output (structured JSON) | 348 | $0.50 | $0.00017 |

The token counts are measured from the exact requests the agent builds, but estimated as bytes/3.5 because no API call was made. The prices are OpenRouter list prices on 2026-10-14. The first real run will replace these with the provider-reported `usage.cost`; the harness records it per message.

For comparison, the same workload on Sonnet 5.5 would be about $11 per 1,000. Caching the static system prompt, which is about 95% of input tokens, would cut the Haiku cost further. The LLM judge runs only in evaluation (`openai/gpt-6-sol`, a different model family from the agent to reduce self-preference bias). It isn't a production cost.

## Evaluation

**Data.** There are two datasets, with very different standing:

| File | Source | Messages | Labels |
|---|---|---|---|
| `tenant_emails.json` | **Provided by Keyhook** | 30 | Written by Keyhook: the only real ground truth here |
| `tenant_emails_test_suite.json` | **Generated by me with AI** for this exercise | 349 = Keyhook's 30, copied in unchanged, + 319 generated | The 319 generated labels were written by AI along with the messages, each with a rationale. No property manager has checked them. |
| `data/blind_test_set.json` | **Generated by ChatGPT** as a blind test, after the prompt was frozen | 120 (17 emergency, 31 urgent, 72 routine; 31 multi-issue; 8 injection or phishing; 13 with Samoan, Tongan, Mandarin or Hindi content, plus 8 with te reo greetings) | Labelled by ChatGPT, with every emergency, escalated and low-confidence label hand-checked by me. Changes are logged in `data/blind_label_review.json`. |

- **The blind set.** I added it because the holdout above isn't fully blind (see the caveats below). ChatGPT saw only Keyhook's label definitions and two of their example messages. It never saw this agent's prompt or the generated suite. Using a different model family from the agent also reduces the chance that the agent scores well just by agreeing with labels written in its own style. The set is built and validated by `scripts/build_blind_set.py`. TODO: the number of labels I changed during review.

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

> TODO: fill in from `reports/*.md` after running against the real API. No numbers here yet.

| Dataset | Pass rate (all 3 fields) | Category | Urgency | Under-triage | Emergency recall | Escalation recall / precision | Action (judge 0–2) | $/1k |
|---|---|---|---|---|---|---|---|---|
| **Keyhook-provided (30)** | | | | | | | | |
| Generated: dev (226 generated + Keyhook's 30) | | | | | | | | |
| Generated: holdout (93) | | | | | | | | |
| **Blind, ChatGPT (120)** | | | | | | | | |

### What these results do and don't tell you

- **The real ground truth is small.** On the Keyhook set, one message is about 3 percentage points, and 2 emergencies make "100% emergency recall" a weak claim on its own. The generated suite adds 39 emergencies, but with AI-written labels.
- **Generated labels measure consistency, not correctness.** The same kind of model wrote the messages, wrote their labels and does the triage. A high score on the generated suite shows the agent applies a consistent policy. It doesn't show that the policy matches how a real PM would act, and it may flatter a model from the same family. Generating more messages the same way would add volume, not validity.
- **The holdout is optimistic.** The labelling conventions in the prompt were worked out from all 349 labels, and a few holdout messages were read while tuning the injection regex. It is blind to prompt iteration, but not to conventions. The ChatGPT blind set is the cleaner out-of-sample number, and Keyhook's unseen messages are the real test. See [PROMPT_CHANGELOG.md](PROMPT_CHANGELOG.md).
- **The judge's score is a proxy.** I haven't calibrated it against human ratings.

## Where it fails or is weakest

> TODO: replace or extend with the actual top error clusters from the report.

The weak spots I expect:
- **Escalation is the softest label.** The labels themselves are inconsistent about where a judgement call ends and a standard workflow begins. [data/label_notes.json](data/label_notes.json) lists 16 such cases. Expect most errors here, mostly over-escalation, which is the safe direction.
- **The primary category in multi-issue messages is often debatable**, e.g. an angry complaint about an unresolved repair. The lenient category score exists for this reason.
- **The injection regex** catches roughly a third of the suite's attacks. The rest rely on the model. Novel phrasing in Keyhook's unseen messages is the biggest unknown.
- **The prompt is long** (about 3k tokens) and encodes conventions from this dataset. It may overfit to these labelling habits and generalise less well.
- **Rules can over-escalate.** The non-English rule escalates every actionable non-English message, and low confidence escalates too. Both are deliberate choices that cost PM time.
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
| `sessions/` | Raw AI session history (TODO: export) |
