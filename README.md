# Tenant Message Triage Agent

An LLM agent that triages tenant messages for a property manager (PM), and an evaluation harness that scores it against labelled data. For each message it returns a category, an urgency, a next action, whether a person must review it first and why, and its reasoning.

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env                               # add OPENROUTER_API_KEY
.venv/bin/python -m pytest -q                      # offline tests, no API calls
.venv/bin/python -m triage.agent --smoke           # one real call (~$0.001): checks model, key and provider settings
.venv/bin/python -m triage.agent --input tenant_emails.json --out results.jsonl
.venv/bin/python -m triage.eval --dataset tenant_emails.json    # exits 1 if a safety gate fails
```

Model, policy and spend caps live in [config.yaml](config.yaml). Input is `{"messages": [...]}` or a bare list; only `subject` and `body` are needed. The detail is in [docs/EVALUATION.md](docs/EVALUATION.md), and [PROMPT_CHANGELOG.md](PROMPT_CHANGELOG.md) logs every prompt and policy change.

## 1. Approach and trade-offs

- **The model extracts facts; code decides.** The model lists each issue with its own category and urgency, plus review reasons and its confidence. [triage/guardrails.py](triage/guardrails.py) derives the final fields: urgency is the highest of any issue (so a gas smell buried in small talk stays an emergency), the primary category comes from the most urgent issue, and any review reason escalates. Code rules can only push a message towards a person.
- **Schema additions.** `issues[]` handles multi-request messages; `escalation_reasons[]` tells the PM why a message is in their queue; `confidence` lets uncertain answers escalate; `languages` sends non-English mail for a translation check.
- **Plain code where it beats a model:** an injection regex backstop, invisible-character and base64 handling, NZ business hours, validation, retries, spend caps, and fixed emergency wording ("call 111 now"), since the model once made a 111 call conditional.
- **Fail closed.** Any model error, invalid output or content-filter stop escalates as `triage_failed`; if most of a run fails, the CLI exits non-zero.
- **Main trade-off: recall over PM workload.** Medium- and low-confidence answers escalate, so missed escalations are near zero but more messages reach a person: 52% of Keyhook's 30 (Keyhook's labels escalate 50%) and 72% of the harder generated suite. Low-only escalation is one config line.
- **Assumptions.** NZ tenancies (toby, WINZ, +12:00). The agent recommends; it never acts or makes promises.

## 2. Model choice and cost

**Choice: `anthropic/claude-haiku-5.5`.** Triage is short extraction against a long rulebook, which suits a small model with reliable structured output. I ran five models live through the same pipeline ([full comparison](docs/EVALUATION.md#live-model-comparison-15-oct-2026)):

| Live, 349-message suite | Emergency recall | Missed escalations | Under-triage* | Pass rate | $ per 1,000 |
|---|---|---|---|---|---|
| **Haiku 5.5** | 100% | **1** | **4** | 72% | $0.40–0.54 |
| GPT-6 Luna | 100% | 6 | 16 | 80% | $0.25–0.32 |
| Sonnet 5.5 (holdout 93 only) | 100% | 1 | 0 | 86% | $7.05–8.12 |
| DeepSeek V4 Flash | 95% | 17 | 10 | 76% | $0.16–0.19 |
| Gemini 3.5 Flash Lite | 90% | 7 | 9 | 72% | $1.74–1.80 |

\*Haiku and Luna: suite plus both blind sets.

**Why Haiku, and a disclosed change of rule.** My pre-stated rule, *the cheapest model that passes every safety gate*, picks Luna. Haiku failed one gate ("no failed triage") on 2 of 549 messages, where the provider's content filter cut its answer off and the message went to a person as designed. Luna's errors are silent: 4 times Haiku's under-triage (9 on the ChatGPT blind set alone), more missed escalations, and the rent-withholding message rated routine in all 3 runs. I chose Haiku after seeing these results, blind sets included, because an unassessed escalation is safe and an under-triage is not. Sonnet is most accurate but costs 15 times more; DeepSeek and Gemini miss emergencies.

**Production cost: about US$0.40 per 1,000 messages** with a warm prompt cache (5,437 input tokens per message, 5,181 from cache, plus 651 output tokens including thinking), and about **$1.00** when messages arrive more than 5 minutes apart. I'd budget **$1 per 1,000**. The judge runs only in evaluation. All live runs used about **$3.15 of the $15 key**.

## 3. Eval results, and what they do and don't tell you

**Data:** Keyhook's 30 (the only real ground truth); a 349-message generated suite (Keyhook's 30 plus 319 edge cases: 256 *dev* used for tuning, 93 *holdout*); and two blind sets from models that never saw the prompt (80 from a separate Claude agent, 120 from ChatGPT given only Keyhook's label definitions). I developed in a free *replay mode* (Claude subagents answering the exact prompts); every number here is live.

**Haiku 5.5, live:**

| Dataset | Pass rate | Emergency recall | Escalation recall / precision | Under / over-triage |
|---|---|---|---|---|
| **Keyhook's 30 (3 repeats)** | 86% | 100% (6 of 6) | 100% / 96% | 0 / 7 |
| Suite, dev (256) | 72% | 100% (30) | 100% / 78% | 2 / 21 |
| Suite, holdout (93) | 73% | 100% (11) | 98% / 79% | 0 / 7 |
| Claude blind set (80) | 81% | 100% (8) | 100% / 83% | 1 / 4 |
| **ChatGPT set, last 30 (truly blind)** | 67% | 100% (1) | 92% / 65% | 1 / 2 |
| Keyword rules, no LLM (ChatGPT first 90) | 23% | 19% | 23% / 80% | 23 / 9 |

Pass rate means category, urgency and escalation all correct. The 2 messages stopped by the content filter (one holdout, one Claude blind) were escalated and are left out of these rows. Every safety gate passed on Keyhook's 30.

**The pre-registered result is the honest one.** An earlier, frozen prompt scored on the first 90 ChatGPT messages before I read them got 88% emergency recall (2 of 16 missed), 90% escalation recall and 2 unsafe actions. The final prompt was written after reading those failures, so its 100% there now is post-hoc ([frozen result](reports/FROZEN_blind_test_set_v4.json)).

**What they tell you:** no labelled emergency was missed on any dataset, escalations almost never are, and under-triage is at most 2 per set, including sets written by another model family. Dev and holdout match (72% and 73%), so the prompt isn't overfitted to its tuning messages. Keyword rules alone are far worse.

**What they don't tell you:** real-world accuracy. Only 30 labels are Keyhook's, they are in-sample (I read them throughout; 95% interval roughly 77–91%), and 2 emergencies prove little. Generated labels measure consistency, not correctness. The truly blind slice is tiny (12 escalations, 1 emergency), and the judge is uncalibrated against human ratings.

## 4. Where it fails or is weakest

- **The emergency/urgent line is a labelling convention.** An unlockable door is *urgent* in Keyhook's example but *emergency* in ChatGPT's after a burglary. Keyhook needs to set the line.
- **Over-escalation.** About 1 in 5 escalations is unnecessary: deliberate, but it costs PM time.
- **Complaint vs request.** A gripe containing a request is often filed as the request (70–80% accuracy there).
- **Novel prompt injection.** The regex catches about a third of the suite's attacks; the model handles the rest. New phrasing is the biggest unknown.
- **Fixed text needs review too.** My first emergency wording told staff to phone a family-violence victim who had asked not to be called. The judge caught it.
- **Provider content filtering.** On 2 of 549 messages, both containing injection text, the provider's filter stopped Haiku's answer. They fail closed after one call, which is safe but gives the PM nothing to work with.
- **No context and some variance.** No tenancy history or open jobs; 13% of Keyhook's messages changed a decision between repeat runs.

## 5. What would need to be true before I'd trust it with real tenants

1. **Done: a live run** of five models through OpenRouter, with strict schemas, caching and real cost. Still needed: route content-filtered messages to a fallback model instead of only escalating them.
2. **Weeks of shadow mode** beside PMs, who label a sample, measuring missed emergencies and escalations against their decisions.
3. **Written thresholds:** zero missed emergencies over a meaningful sample, and a missed-escalation rate the business accepts.
4. **It assists, never acts.** It sorts the queue and a person reads everything; emergencies page someone.
5. **Operations and privacy:** provider fallback, alerts on failed-triage spikes, decisions logged with their prompt version, a privacy review of sending tenant data to a model provider, and every change gated on an eval set grown from PM corrections.

## 6. Time spent

I didn't do this in one sitting. Session timestamps show about **4 hours of active work across three sittings**: 14 Oct 16:36–17:18 (plan and build), 14 Oct 22:51–00:08 (prompt iterations, blind set, code and security reviews), and 15 Oct 08:25–10:45 (label check, mock review and fixes, live model runs, of which about 30 minutes was waiting on API runs). That is over the brief's 2 hours and near the 4-hour maximum; the generated suite and blind sets took the extra time, and I'd cut them first if timeboxed. The [session history](ai-sessions/) has every prompt.

**Repository:** `triage/` (agent, guardrails, prompts, eval, replay), `data/` and `tenant_emails*.json` (datasets), `reports/` (eval reports), [ai-sessions/](ai-sessions/) (AI session history, regenerated by `scripts/export_sessions.py`).
