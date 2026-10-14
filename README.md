# Tenant Message Triage Agent

An LLM agent that triages tenant messages for a property manager (PM), with an evaluation harness that scores it against labelled data. For each message it returns a category, an urgency, a recommended next action, whether a person must review it first and why, and its reasoning.

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env                               # add OPENROUTER_API_KEY
.venv/bin/python -m pytest -q                      # offline tests, no API calls
.venv/bin/python -m triage.agent --input tenant_emails.json --out results.jsonl
.venv/bin/python -m triage.eval --dataset tenant_emails.json    # exits 1 if a safety gate fails
```

Settings (model, prompt version, escalation policy, spend caps) are in [config.yaml](config.yaml). The full evaluation write-up is in [docs/EVALUATION.md](docs/EVALUATION.md), and every prompt and policy change is in [PROMPT_CHANGELOG.md](PROMPT_CHANGELOG.md).

## 1. Approach, key decisions and trade-offs

- **The model extracts and code decides.** The model returns each issue in the message with its own category and urgency, plus any reasons for review and its confidence. Code in [triage/guardrails.py](triage/guardrails.py) derives the final fields:
  - **urgency** is the highest urgency of any issue, so an emergency buried in small talk can't be averaged away
  - **escalate_to_human** is true if any review reason applies
  - every code rule can only push a message *towards* a person
- **Schema changes.**
  - `issues[]` handles messages with several requests.
  - `escalation_reasons[]` tells the PM *why* a message is in their queue (`hardship`, `legal_or_tenancy_law`, `manipulation_attempt`…).
  - `confidence` lets uncertain answers escalate.
  - `languages` sends every non-English message to a person to check the translation.
- **Code where code is more reliable than a model:**
  - a regex backstop for blatant prompt injection
  - stripping invisible characters and decoding base64
  - NZ business-hours detection
  - fixed emergency wording ("call 111 now"), because the model twice made the 111 call conditional while smoke was present
  - output validation, retries and spend caps
- **Fail closed.** A model error, timeout or invalid output escalates the message as `triage_failed`, so nothing is dropped or auto-handled without a model answer.
- **Main trade-off: recall over PM workload.** Medium- and low-confidence answers escalate, and so does every non-English message. Missed escalations are near zero, but 57–69% of messages reach a person, and the suite pass rate is 76% (it was 89% under v4's leaner policy). Escalating only low confidence again is one config line.
- **No API spend so far.** Everything was evaluated in *replay mode*: Claude subagents answered the exact prompts the agent sends, and the real pipeline scored their answers.
- **Assumptions.** The tenancies are in New Zealand (toby, WINZ, +12:00 timestamps). The agent recommends actions; it never takes them or makes promises.

## 2. Model choice and cost

**Choice: `anthropic/claude-haiku-5.5`.** The rule, set before any comparison, was *the cheapest model that passes every safety gate*. Triage is short classification and extraction over a long rulebook, so a small model with reliable structured output fits.

I compared Haiku with Sonnet 5.5 on the same 256 dev messages, through the same pipeline. Both stand-ins were Claude subagents given the identical system prompt. Sonnet's actions were judged by Claude Opus, so the judge wasn't grading its own model's work.

| Same 256 dev messages | Haiku 5.5 | Sonnet 5.5 |
|---|---|---|
| Safety gates | **all pass** | **1 fails** (an unsafe action) |
| Pass rate (category, urgency and escalation all correct) | 76% | 86% |
| Emergency recall (30 emergencies) | 100% | 100% |
| Under-triage / over-triage | 0 / 15 | 0 / 7 |
| Escalation recall | **100%** | 99% (2 missed) |
| Unnecessary escalations | 38 | **18** |
| Keyhook's 30 messages, pass rate | 90% | 100% |
| Action quality (judge, 0–2) / unsafe actions | 1.83 / **0** | 1.79 / 1 |
| Est. cost per 1,000 messages | **$0.61** | $11.34 |

Sonnet classifies better and sends about half as many messages to a person unnecessarily (roughly 80 fewer per 1,000). But it **fails the safety gate** and is the less safe model where it matters:
- **It writes its own emergency advice.** Haiku defers to the fixed safety text that code adds, but Sonnet improvises. It told a tenant to unplug a wet, sparking multibox, which the judge flagged as unsafe. In a gas-smell emergency it said to call the gas line "if the smell returns".
- **It missed 2 escalations that Haiku caught.** One was a tenant who had disabled a smoke alarm, the other a six-issue email with a contractor complaint. Neither was an emergency.
- **It costs 19 times more.**

Haiku is the cheapest model that passes every gate, so it's the choice. Sonnet's accuracy shows there is headroom, especially for cutting PM workload. If Sonnet's emergency advice were restricted to the fixed wording, it would be worth re-testing.

Costs at OpenRouter list prices (15 Oct 2026), using Haiku's measured token counts (Sonnet uses its own, shorter output). DeepSeek, GPT-6 Luna and Gemini are compared on cost only; their quality hasn't been tested yet.

| Model | $ per 1M tokens (in / out) | Est. $ per 1,000 messages |
|---|---|---|
| `deepseek/deepseek-v4-flash` | 0.091 / 0.18 | $0.46 |
| `anthropic/claude-haiku-5.5` (chosen) | 0.10 / 0.50 | $0.61 |
| `openai/gpt-6-luna` | 0.10 / 0.50 | $0.61 |
| `google/gemini-3.5-flash-lite` | 0.30 / 2.50 | $2.18 |
| `anthropic/claude-sonnet-5.5` | 2.00 / 10.00 | $11.34 |

**Production estimate: about US$0.61 per 1,000 messages** (4,335 input and 353 output tokens per message), or about $0.31 when prompt caching hits. I'd budget **about $1 per 1,000** to cover thinking tokens, retries and tokenizer error. Token counts are estimates until the first API call ([detail](docs/EVALUATION.md#cost-detail)). The judge runs only in evaluation, so it isn't a production cost.

**Next step:** `python -m triage.compare --split dev` (about $2–4) runs all five real models through OpenRouter. If DeepSeek or GPT-6 Luna also passes every gate, the rule would pick DeepSeek on price, subject to a data-handling check.

## 3. Eval results, and what they do and don't tell you

**Data:**
- **Keyhook's 30 labelled messages**: the only real ground truth.
- **A 349-message suite I generated with AI**: Keyhook's 30 plus 319 edge cases (emergencies, non-English, injection, contradictions, tone traps), split into 256 *dev* (used while tuning the prompt) and 93 *holdout* (scored only).
- **Two blind sets** written by models that never saw the prompt: 80 messages from a separate Claude subagent and 120 from ChatGPT. ChatGPT saw only Keyhook's label definitions and two example messages.

ChatGPT's labels were cross-checked against Keyhook's. Six were corrected *after* the v4 and v5 runs, so the table uses the original labels, and all 17 emergency and 18 low-confidence labels were hand-checked ([detail](docs/EVALUATION.md)).

**Results** (prompt v5, Haiku stand-in; every safety gate passes on every set):

| Dataset | Pass rate | Emergency recall | Escalation recall / precision | Under / over-triage | Unsafe actions |
|---|---|---|---|---|---|
| **Keyhook's 30** | 90% | 100% (2) | 100% / 88% | 0 / 0 | 0 |
| Suite, dev (256) | 76% | 100% (30) | 100% / 79% | 0 / 15 | 0 |
| Suite, holdout (93) | 71% | 100% (11) | 98% / 78% | 2 / 6 | 0 |
| Claude blind set (80) | 78% | 100% (8) | 100% / 76% | 1 / 5 | 0 |
| ChatGPT set, first 90 (post-hoc for v5, original labels) | 73% | 100% (16) | 98% / 88% | 2 / 3 | 0 |
| **ChatGPT set, last 30 (blind for v5)** | 70% | 100% (1) | 92% / 69% | 2 / 0 | 0 |
| Keyword rules, no LLM (baseline) | 22% | 19% | 23% / 80% | 23 / 9 | n/a |

**The pre-registered blind result is the honest one.** Before inspecting anything, v4 scored on the first 90 ChatGPT messages:
- emergency recall 88% (2 of 16 missed)
- escalation recall 90%
- 2 unsafe actions

v5 was written after reading those failures, so its 100% on that set is post-hoc. The frozen result is in [reports/FROZEN_blind_test_set_v4.json](reports/FROZEN_blind_test_set_v4.json).

**What they tell you:** the pipeline catches every labelled emergency and almost every escalation, under-triage is at most 2 per set, and this holds across six datasets, including one written by a different model family. It also beats a keyword baseline by a wide margin.

**What they don't tell you:**
- **Real-world accuracy is unproven.** Only 30 labels come from Keyhook, and 2 emergencies make "100% emergency recall" thin on its own.
- **Generated labels measure consistency, not correctness.** The suite's labels were written by the same model family that does the triage.
- **The holdout is only partly blind.** The prompt's conventions came from all 349 labels.
- **The truly blind ChatGPT slice is small.** It has 12 escalations, so the 95% interval on 92% recall is roughly 62–100%.
- **Replay isn't a real run.** No real API call has been made. The subagents answered in batches, without enforced JSON schemas, and the judge was also Claude.
- **The judge's scores are a proxy.** They haven't been calibrated against human ratings.

## 4. Where the agent fails or is weakest

- **The emergency/urgent boundary is a labelling convention, not something the model can work out.** A door that can't be locked is *urgent* in Keyhook's example and in the generated suite, but ChatGPT labels it *emergency* after a burglary. v4 missed 2 ChatGPT emergencies this way. v5 errs towards emergency, which costs over-triage. Keyhook needs to decide where the line is.
- **Over-escalation.** Roughly 1 in 5 escalations is unnecessary. That's deliberate, but it costs PM time.
- **Complaint vs request.** Category accuracy is about 70–80% in the complaint group: a gripe that contains a request gets filed as the request.
- **Free-text safety advice.** The model made a 111 call conditional, so fixed wording now comes from code. My own first version of that wording told staff to phone a family-violence victim who had asked not to be called. The judge caught it, and it has been fixed. Fixed text needs the same review as model output.
- **Novel prompt injection.** The regex catches about a third of the suite's attacks, and the model handles the rest; new phrasing is the biggest unknown.
- **Run-to-run variation** of a few points, so small differences don't mean much. And **no context**: each message is triaged without tenancy history or open jobs.

## 5. What would need to be true before I'd trust it with real tenants

1. **A real API run passes every gate.** That covers the model comparison plus the live path: provider routing, strict schemas and retries.
2. **Shadow mode.** Run it alongside PMs on real mail for several weeks, with PMs labelling a sample. Measure missed emergencies and missed escalations against their decisions.
3. **Agreed thresholds, in writing.** Zero missed emergencies over a meaningful real sample, and a missed-escalation rate the business accepts. Keyhook decides the emergency/urgent boundary.
4. **It assists and never acts.** At first it only sorts the queue, and a person reads everything. Emergencies page someone, not just sit at the top of a list. Any auto-handling of routine messages comes later, only once shadow-mode data supports it.
5. **Operations and privacy:**
   - provider fallback and alerting on fail-safe spikes
   - every decision logged with its prompt version
   - a privacy review of sending tenant personal data to a third-party model
   - every prompt or model change gated on the eval set, which grows from messages PMs re-triage

---

**Repository map:**
- `triage/`: agent, guardrails, prompts, eval harness, replay tools
- `data/` and `tenant_emails*.json`: the datasets and the label review
- `reports/`: eval reports
- [docs/EVALUATION.md](docs/EVALUATION.md): the full evaluation
- [ai-sessions/](ai-sessions/): AI session history
