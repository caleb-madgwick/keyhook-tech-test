# Tenant Message Triage Agent

An LLM agent that triages tenant messages for a property manager (PM), and a harness that scores it against labelled data. Each message gets a category, urgency, next action, whether a person must review it first (and why), and reasoning. It assumes NZ tenancies and only recommends; it never acts.

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env                               # add OPENROUTER_API_KEY
.venv/bin/python -m pytest -q                      # offline tests, no API calls
.venv/bin/python -m triage.agent --smoke           # one live call (~$0.001)
.venv/bin/python -m triage.agent --input tenant_emails.json --out results.jsonl
.venv/bin/python -m triage.eval --dataset tenant_emails.json   # exits 1 if a gate fails
```

Settings: [config.yaml](config.yaml). Input: `{"messages": [...]}` or a list with `subject` and `body`. More: [docs/EVALUATION.md](docs/EVALUATION.md), [PROMPT_CHANGELOG.md](PROMPT_CHANGELOG.md).

## 1. Approach and trade-offs

- **The model extracts facts; code decides.** The model lists each issue with its category and urgency, plus review reasons and confidence; [triage/guardrails.py](triage/guardrails.py) derives the final fields: urgency is the highest of any issue (a gas smell buried in small talk stays an emergency), and any review reason escalates. Code can only push a message towards a person.
- **Schema additions:** `issues[]` for multi-request messages, `escalation_reasons[]` so the PM sees why a message is in their queue, `confidence` so uncertain answers escalate, and `languages` for a translation check.
- **Plain code where it beats a model:** an injection regex backstop, hidden-text handling, business hours, validation, retries, spend caps, and fixed emergency wording ("call 111 now"), because the model once made a 111 call conditional. Any model error or invalid output fails closed: escalated as `triage_failed`.
- **Main trade-off: recall over PM workload.** Medium- and low-confidence answers escalate, so missed escalations are near zero but more reach a person (52% of Keyhook's 30 vs 50% labelled). Low-only is one config line.

## 2. Model choice and cost

**`anthropic/claude-haiku-5.5`**, chosen from five models run live through the same pipeline:

| Live, 349-message suite | Emergency recall | Missed escalations | Under-triage* | Pass rate | $ per 1,000 |
|---|---|---|---|---|---|
| **Haiku 5.5** | 100% | **1** | **4** | 72% | $0.40–0.54 |
| GPT-6 Luna | 100% | 6 | 16 | 80% | $0.25–0.32 |
| Sonnet 5.5 (93 holdout only) | 100% | 1 | 0 | 86% | $7.05–8.12 |
| DeepSeek V4 Flash | 95% | 17 | 10 | 76% | $0.16–0.19 |
| Gemini 3.5 Flash Lite | 90% | 7 | 9 | 72% | $1.74–1.80 |

\*Haiku and Luna: suite plus both blind sets.

**A disclosed change of rule.** My pre-stated rule, *the cheapest model that passes every safety gate*, picks Luna, because the provider's content filter stopped Haiku on 2 of 549 messages (both went to a person). But Luna's errors are silent: 4 times Haiku's under-triage, and rent withholding rated routine in all 3 runs. I chose Haiku after seeing these results, blind sets included: an unassessed escalation is safe; an under-triage is not. Sonnet costs 15× more; DeepSeek and Gemini miss emergencies.

**Cost: about US$0.40 per 1,000 messages** with a warm prompt cache (5,437 input tokens per message, 5,181 cached, plus 651 output), and about $1.00 when messages arrive more than 5 minutes apart. I'd budget **$1 per 1,000**. All live runs used about $3.15 of the $15 key.

## 3. Eval results, and what they do and don't tell you

**Data:** Keyhook's 30 (the only real ground truth); a generated suite of those 30 plus 319 edge cases (256 *dev* for tuning, 93 *holdout*); and blind sets from models that never saw the prompt (80 from a separate Claude agent, 120 from ChatGPT given only Keyhook's label definitions). Pass = category, urgency and escalation all correct; the 2 content-filtered messages are excluded. Haiku 5.5, live ([reports/](reports/)):

| Dataset | Pass | Emergency recall | Escalation recall / precision | Under / over-triage |
|---|---|---|---|---|
| **Keyhook's 30 (3 repeats)** | 86% | 100% (6 of 6) | 100% / 96% | 0 / 7 |
| Suite, dev (256) | 72% | 100% (30) | 100% / 78% | 2 / 21 |
| Suite, holdout (93) | 73% | 100% (11) | 98% / 79% | 0 / 7 |
| Claude blind set (80) | 81% | 100% (8) | 100% / 83% | 1 / 4 |
| **ChatGPT, last 30 (truly blind)** | 67% | 100% (1) | 92% / 65% | 1 / 2 |
| Keyword rules only (90) | 23% | 19% | 23% / 80% | 23 / 9 |

**The pre-registered result is the honest one.** A frozen earlier prompt, scored on the first 90 ChatGPT messages before I read them, missed 2 of 16 emergencies and 10% of escalations ([frozen result](reports/FROZEN_blind_test_set_v4.json)). The final prompt was written after reading those failures, so its 100% there is post-hoc.

**What they tell you:** no labelled emergency was missed on any dataset, escalations almost never are, and under-triage is at most 2 per set. Dev and holdout match, so the prompt isn't overfitted. **What they don't:** real-world accuracy. Only 30 labels are Keyhook's, they are in-sample (95% interval roughly 77–91%), and 2 emergencies prove little. Generated labels measure consistency, not correctness, and the action judge is uncalibrated against human ratings.

## 4. Where it fails or is weakest

- **Emergency vs urgent is a labelling convention.** An unlockable door is *urgent* in Keyhook's example but *emergency* in ChatGPT's after a burglary. Keyhook needs to set the line.
- **Over-escalation.** About 1 in 5 escalations is unnecessary: deliberate, but it costs PM time.
- **Complaint vs request.** A gripe that contains a request is often filed as the request.
- **Novel prompt injection.** The regex catches about a third of attacks; the model handles the rest.
- **Fixed text needs review too.** My first emergency wording said to phone a family-violence victim who had asked not to be called. The judge caught it.
- **No context, some variance.** No tenancy history or open jobs, and 13% of Keyhook's messages changed a decision between repeat runs.

## 5. What would need to be true before I'd trust it with real tenants

1. **Weeks of shadow mode** beside PMs, with written thresholds: zero missed emergencies over a meaningful sample, and a missed-escalation rate the business accepts.
2. **It assists, never acts.** A person reads everything, and emergencies page someone.
3. **Operations and privacy:** a fallback model for content-filtered messages, alerts on failure spikes, decisions logged with their prompt version, evals grown from PM corrections, and a privacy review of sending tenant data to a provider.

**Time and AI use.** About **4 hours of active work** in three sittings on 14–15 Oct, over the suggested 2 hours; the generated suite and blind sets took the extra time, and I'd cut them first if timeboxed. Built with Claude Code: [ai-sessions/](ai-sessions/) has every prompt and a transcript of every session.
