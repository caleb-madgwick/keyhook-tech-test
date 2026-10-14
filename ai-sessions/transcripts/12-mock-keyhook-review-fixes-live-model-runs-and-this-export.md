# 12. Mock Keyhook review, fixes, live model runs and this export

Claude Code session, Thu 15 Oct, 09:06 to 10:23 AEDT. 8 prompts, 1 subagent.

Prompts are quoted verbatim. Claude's replies are shown in full; tool calls are collapsed to one line each and tool output is left out.

### 09:06 · Prompt

> I want you to pretend that you are keyhook and have never seen my solution before and judge its fit for purpose and make sure that it meets the criteria, I have not tested with the production api key, i will do it after this evaluation. I want you to do a first pass over everything like you have never seen anything that i have created before and judge the what has been created and give improvements in any areas and anything that would bring my score down in any aspects. you are a human as the judge and also use llm as a judge, this is the original email and the brief and json i was given:
>
>
> ```text
> Hi Caleb,
>
> Happy Wednesday. 
>
> As discussed, attached is the technical test from Aaron. 
> There is a PDF explaining the task, and a JSON file with some data for you to use in building their solution.
>
> You will also need the link below. Note that the link contain API keys and they expire after being viewed.
> The keys will expire on Oct 21, 2026, 2:34 PM, which gives you 7 days to complete the test from now (I am sure you will have it back to me a lot sooner than that). 
>
> Please only click on the link when you are ready to safely save the API key contained within it.
> ```

I'll start by looking at the repo as a reviewer would see it on first open.

<details><summary>4 tool calls (Bash ×4)</summary>

- Bash: List commits, tracked files, and line counts
- Bash: Read README, config, and setup files
- Bash: Read truncated README section and config files
- Bash: Read config and setup files

</details>

Running tests and launching an independent LLM-judge reviewer in parallel while I read the code myself.

<details><summary>13 tool calls (Bash ×12, Delegated to a subagent)</summary>

- Delegated to a subagent: *Independent LLM-judge review*
- Bash: Run test suite and peek at runs and review file
- Bash: Read agent and config modules
- Bash: Read client and schema modules
- Bash: Read guardrails and replay client factory
- Bash: Read eval harness first half
- Bash: Check OpenRouter public model list for configured models and prices
- Bash: Check prompt caching minimum and cost detail
- Bash: Locate prompt versions and read seed-set report
- Bash: Read the active v5 system prompt
- Bash: Inspect AI session history files
- Bash: Read compare script and eval spend/judge logic
- Bash: Scan for leaked keys, read changelog tail, count datasets

</details>

Checking one potential key reference in git history, then waiting on the independent reviewer.

<details><summary>4 tool calls (Bash ×4)</summary>

- Bash: Show the git history line mentioning an OpenRouter key prefix
- Bash: Check eval CLI flags and agent behaviour without a key
- Bash: Check replay reproduction works offline
- Bash: Revert the regenerated report to keep the tree clean

</details>

My own review pass is done. The documented replay command reproduces the Keyhook-30 report exactly, apart from its timestamp; I reverted that file so your tree is clean. I'm waiting for the independent LLM reviewer before I write up the combined verdict.

Before I rely on the reviewer's findings, I'm checking the three that matter most.

<details><summary>1 tool call (Bash)</summary>

- Bash: Verify baseline crash and label-notes behaviour

</details>

# Keyhook reviewer verdict

I reviewed the repo myself, as a human reviewer would. A separate LLM agent also graded it independently, with the brief and no access to my notes. We reached the same conclusion.

**Overall: lean hire as it stands, and a clear hire once the live run is done.** The design and evaluation thinking are senior-level. The biggest risk is that the system you submit has never run once.

## Scores (1–5)

| Criterion | Human | LLM judge | Main reason |
|---|---|---|---|
| Problem framing | 4 | 4 | The `issues[]` list, the escalation reasons and the "model extracts, code decides" split are excellent. You lose a point for ignoring the 2–4h scope. |
| Verification | 3 | 3 | The 154 tests pass and the reviews are thorough. But the configured pipeline has never made a real call, and an AI refactor broke a script while claiming nothing changed (issue 2 below). |
| Evaluation quality | 4 | 4 | You have safety gates, under- and over-triage counts, a pre-registered blind result, a keyword baseline and a failing exit code when a gate fails. Almost every label was written by AI, and the configured judge has never run. |
| Models and cost | 2 | 2 | The cost arithmetic is right: I checked the model IDs and prices against OpenRouter's live list. But no model was actually compared. |
| Production thinking | 4 | 4 | Failures escalate instead of being dropped, emergency wording is fixed in code, and you have spend caps, `data_collection: deny` and a shadow-mode plan. Nothing warns you if every message fails. |
| Honesty | 4 | 4 | Unusually candid. It loses a point for the missing time statement, the stale review in `reports/` and the incomplete session history. |

## What will lower your score, most damaging first

**1. Zero API usage, and the configured system has never run.** The brief says Keyhook will look at the key's usage, and right now it would show $0. The bigger danger is that they run your config on their unseen messages. If one setting is rejected, every message comes back `triage_failed`, and the process still exits 0. The risky settings are strict `json_schema` with `require_parameters`, the `cache_control` blocks and default thinking inside `max_tokens: 3000`. Your session 09 already found one setting like this (`temperature: 0`) just by reading docs.
- **Fix:** run a one-message smoke test, then the Keyhook 30, then `triage.compare --split dev` with the same judge for every model.
- Replace the README tables with the real numbers, and keep replay mode as a dev-time technique.
- Make the agent exit non-zero, or warn loudly, on a 401/404 or when more than half the messages fail.

**2. `python -m triage.baseline` crashes.** I confirmed it: `NameError: pct` at [baseline.py:69](triage/baseline.py#L69). The "Simplify" commit removed the import. That script produces the README's "keyword rules, no LLM" row, and it fails the first time a reviewer tries it. It is a one-line fix (`from .report import pct`), and it needs a test.

**3. Scope and length against "2h, 4h max" and a 1–2 page write-up.** Your session times show about 7.5 hours of wall-clock time plus the next morning. The README never says how long you spent. It is about 2,000 words (around 4 pages) and links to another 6,500 words.
- State your hands-on time honestly. Background subagents ran while you weren't there, so it may be less than the wall-clock time.
- Cut the README to about 1,000 words and move the tables to `docs/EVALUATION.md`.

**4. The AI session history is incomplete and curated.** The export stops at 00:04 and leaves out the 15 Oct morning sessions: the Haiku-vs-Sonnet comparison, the README rewrite and the refactor that broke the baseline. It also says it is a selection of 30 of your 35 prompts. The brief says "Raw is fine; don't tidy it up."
- Re-export everything and include the raw transcript files, after checking them for keys.

**5. The Haiku-over-Sonnet decision rests on thin evidence.** "Sonnet fails a safety gate" comes from one flag. Two different judges scored the two models (Sonnet judged Haiku, Opus judged Sonnet). Both "models" were Claude Code subagents answering batches of messages without schema enforcement. A reviewer will ask about this.
- Re-run the comparison for real, or present Haiku as the cost-driven choice pending that comparison.

**6. `reports/senior_engineer_review.md` is stale.** It says "51/51 tests", "Overall 6/10" and "no spend cap", most of which you have since fixed. Delete it, or move it into `ai-sessions/` with a note that it is historical.

**7. Small robustness gaps** if Keyhook's file differs slightly from yours:
- A label like `"Maintenance"` crashes the eval with a `KeyError` (`metrics.py:27`).
- A body stored under a key like `text` is triaged silently as "(empty)".
- `data/label_notes.json` is applied by message id to any dataset. If their ids reuse `msg_006`, their report shows irrelevant "disputed label" notes.
- Checking the input and labels up front, with clear error messages, covers all three.

**8. Interview questions to prepare for:**
- 57–69% of messages go to a person. What is the product value?
- Dev 76%, holdout 71%, blind 70%: is the prompt overfitted? It has very specific rules, such as the infant-formula fridge and "third time" repairs.
- Does an over-triaged message get the "call 111" text in its action?

## Advice for your upcoming live run

- **Order:** smoke test (one message), then `--dataset tenant_emails.json`, then the dev split. Don't start with the default, which is all 349 suite messages with the judge on.
- **Watch the judge's cost.** The judge is `openai/gpt-6-sol` at $2 / $10 per million tokens, with default reasoning. On the full suite it could reach your $3 per-run cap. Calls past the cap are skipped and the run fails its gates. Use `--no-judge` for comparisons, or set the judge's reasoning low.
- **Check four things in the first real results:** `structured_fallback`, `cached_input_tokens`, thinking tokens and the real cost per message. Then update the $0.61 per 1,000 estimate.

## What's already strong

- **Multi-issue handling and urgency.** Splitting each message into issues and taking the highest urgency in code is the best idea in the repo. It handles the gas smell buried in small talk (msg_014) by construction.
- **Failures go to a person.** Any failure becomes an escalated result, and code rules can only push a message towards a human.
- **Cheap re-scoring.** The eval caches raw model output and re-applies the policy at scoring time, so policy changes cost nothing to re-score.
- **The pre-registered blind result.** Reporting v4's 88% emergency recall as "the honest one" is exactly what the honesty criterion rewards.
- **Reproducible offline.** I re-ran the Keyhook-30 replay and got an identical report apart from the timestamp. I reverted that file, so your tree is clean.
- **Clean on secrets.** No key in the git history, and `.env` is gitignored.

I haven't changed anything. Want me to fix issues 2, 6 and 7 and add the smoke-test command and the warning when most messages fail, before your live run?


### 09:16 · Prompt

> yes

<details><summary>2 tool calls (Bash ×2)</summary>

- Bash: Read baseline, metrics head, and references to the stale review
- Bash: Find stale-review references and read eval run/main

</details>

I'll make the fixes now. First, a look at the existing tests so the new ones match their style.

<details><summary>1 tool call (Bash)</summary>

- Bash: Read test conventions, label notes, and review structure

</details>

Making the edits now: the baseline import, input checks in `load_messages`, and the smoke flag and exit code in the agent.

<details><summary>6 tool calls (Bash ×3, Edit ×3)</summary>

- Bash: Add the missing pct import to the baseline
- Edit: `~/Developer/keyhook-tech-test/triage/agent.py`
- Edit: `~/Developer/keyhook-tech-test/triage/agent.py`
- Edit: `~/Developer/keyhook-tech-test/triage/agent.py`
- Bash: Tidy the smoke constant comment and view the module docstring
- Bash: Document smoke flag and exit code in agent docstring

</details>

Now the eval side: label checks and scoping the disputed-label notes.

<details><summary>3 tool calls (Edit ×3)</summary>

- Edit: `~/Developer/keyhook-tech-test/triage/eval.py`
- Edit: `~/Developer/keyhook-tech-test/triage/eval.py`
- Edit: `~/Developer/keyhook-tech-test/triage/eval.py`

</details>

Now the stale review move, then the tests.

<details><summary>2 tool calls (Bash ×2)</summary>

- Bash: Check all datasets pass label checks and notes still apply
- Bash: Move the stale review into ai-sessions with a historical header

</details>

Now the tests for each fix.

<details><summary>2 tool calls (Bash ×2)</summary>

- Bash: Read test helpers to reuse in new tests
- Bash: Add tests for the new checks and run the suite

</details>

Tidying that baseline test to use `monkeypatch`, then checking the CLI paths end to end offline.

<details><summary>1 tool call (Bash)</summary>

- Bash: Run tests, baseline, and smoke/exit-code paths offline

</details>

The baseline runs again. Its suite-wide numbers don't obviously match the README's baseline row, so I'm finding which dataset that row came from.

<details><summary>4 tool calls (Bash ×4)</summary>

- Bash: Locate which dataset the README baseline row came from
- Bash: Reproduce the README baseline row on the ChatGPT set
- Bash: Check the end of the changelog before appending
- Bash: Append changelog entry for these code changes

</details>

Last, adding the smoke test to the README quickstart so reviewers see it.

<details><summary>2 tool calls (Edit, Bash)</summary>

- Edit: `~/Developer/keyhook-tech-test/README.md`
- Bash: Confirm README quickstart and final test run

</details>

I've fixed issues 2, 6 and 7 and added the smoke test and the warning for a broken setup. All 160 tests pass (154 before), and I checked each change offline with no API calls. Nothing is committed yet.

- **Baseline (issue 2):** `python -m triage.baseline` runs again; the "Simplify" commit had removed an import it needed ([baseline.py:18](triage/baseline.py#L18)). A test now runs it so this can't recur silently.
  - It reproduces the README's keyword-baseline row, which comes from the first 90 messages of the ChatGPT set. Every figure matches except the pass rate: it now gives 23% (21 of 90) against the 22% in the README. You may want to correct that and label the row with its dataset.
- **Stale review (issue 6):** it now lives at [ai-sessions/senior_engineer_review.md](ai-sessions/senior_engineer_review.md) with a note saying it describes the code mid-build. I updated the two changelog references to it.
- **Robustness (issue 7):**
  - A file that isn't `{"messages": [...]}` or a list of messages now stops with a clear error.
  - A message with no subject or body gets a warning listing the keys it does have, so text stored under `text` is easy to spot.
  - Labels are checked before any API spend. Case and spacing are cleaned up (`"Maintenance "` becomes `maintenance`), and invalid values are listed together instead of crashing the metrics.
  - Disputed-label notes now apply only when the message is the exact one the note was written about. If Keyhook's set reuses an id like `msg_006`, it no longer picks up your notes.
  - All four existing datasets pass the new checks unchanged, and the notes still apply to the same 16 messages.
- **Smoke test:** `python -m triage.agent --smoke` makes one real call on msg_002 (the burst pipe), costing about $0.001. It prints the model used, retries, whether strict JSON had to be dropped, tokens (including cached), cost and any error. It exits 2 if the message fails. It's now line 4 of the README quickstart.
- **Broken-setup warning:** `triage.agent` now exits 2 and lists the errors when more than half the messages fail. Before, a wrong model name or key produced fully escalated output and exited 0, so it looked like a normal run.

I added the required `PROMPT_CHANGELOG.md` entry; none of these changes alters triage output.

Still yours to do, from the review:
1. **The live run:** smoke test, then the Keyhook 30, then the model comparison on the dev split.
2. **Real numbers in the README** from that run, in place of the replay ones.
3. **A statement of your time spent**, and a shorter README.
4. **Re-export the 15 Oct morning sessions** into `ai-sessions/`.

Running the smoke test before anything else will catch a bad model name or key for a fraction of a cent.


### 09:22 · Prompt

> tell me when the smoke test it done, make the readme shorter snd stop mentioning old versions of the code ive created ie v4 v5, yes re export the session history and since i have not done the whole thing al in one go give a statement about time spent too. after this is done we will look into running a live test and making a plan for this to get details about the success rate and cost of different models ect for 1000 runs but make sure to do this in a cost effective way and stay well within our $15 budget

Starting with the smoke test, since everything else depends on whether the key is in place.

<details><summary>7 tool calls (Bash ×5, Read ×2)</summary>

- Bash: Check whether a key is set and list session files
- Bash: Summarise each session file's time span and first prompt
- Bash: Find which session built the export and any export script
- Bash: Check whether the original export scripts still exist
- Read: `/private/tmp/claude-501/-Users-calebmadgwick-Developer-keyhook-tech-test/d4e0b768-9fa3-4858-88b2-6b6458586401/scratchpad/sessions/export.py`
- Read: `/private/tmp/claude-501/-Users-calebmadgwick-Developer-keyhook-tech-test/d4e0b768-9fa3-4858-88b2-6b6458586401/scratchpad/sessions/extract.py`
- Bash: Compute work sittings and active time from session timestamps

</details>

Update: the timestamps show about 3 hours of actual work across three sittings, not one long day. Checking that figure holds under a looser idle threshold, then on to the export.

<details><summary>1 tool call (Bash)</summary>

- Bash: Check active-time sensitivity to idle threshold

</details>

The figure holds: about 2 hours 55 minutes of activity, whether idle gaps are cut at 5 or 30 minutes. Now mapping the morning prompts to their sessions so I can title them.

<details><summary>1 tool call (Bash)</summary>

- Bash: List prompts in the two sessions that ran into the morning

</details>

Session 10 ran on into the morning: label review, model comparison and README rewrite. Session 11 is the simplify pass, and this session is 12. Writing the re-runnable exporter with nothing omitted.

<details><summary>4 tool calls (Bash ×4)</summary>

- Bash: Bring the exporter into the repo with omission logic removed
- Bash: Run the exporter into scratch and compare with the current export
- Bash: Inspect this session's exported transcript and subagent models
- Bash: Read README results table and find version mentions

</details>

I have everything I need for the rewrite. The README is 2,043 words now; I'm aiming for about 1,000, with no prompt version numbers and the time statement added.

<details><summary>3 tool calls (Read, Write, Bash)</summary>

- Read: `~/Developer/keyhook-tech-test/README.md`
- Write: `~/Developer/keyhook-tech-test/README.md`
- Bash: Check README length and version mentions, note baseline fix in changelog

</details>

It's at 1,697 words, still too long for the 1–2 pages the brief asks for. Tightening each section.

<details><summary>1 tool call (Bash)</summary>

- Bash: Tighten README sections to bring it to about two pages

</details>

Down from 2,043 to 1,424 words, about 1,100 of them prose once the tables are excluded. That's about two pages. Now updating the session-history README to match the new export.

<details><summary>2 tool calls (Bash ×2)</summary>

- Bash: Get session times and subagent model counts for the index
- Bash: Update the session-history index for the complete export

</details>

All edits are done. Running the tests, then regenerating the session export last so it captures this session.

<details><summary>1 tool call (Bash)</summary>

- Bash: Run tests and regenerate the full session export into the repo

</details>

**The smoke test hasn't run.** Your `.env` is empty and no key is set, so there is nothing to call with. Put the key into `.env` yourself (please don't paste it here) and tell me, and I'll run it. It costs about $0.001.

The other three tasks are done. All 160 tests still pass, and nothing is committed yet.

**README** ([README.md](README.md))
- It's down from 2,043 to 1,424 words. About 1,100 of those are prose, the rest tables, so it's roughly two pages.
- It no longer mentions prompt versions. The earlier blind result is now described as "an earlier, frozen prompt"; the only "v4" left is in that results file's link and in a model's name (`deepseek-v4-flash`).
- The keyword baseline row is corrected to 23% and now says which dataset it comes from.

**Time statement**
- I worked this out from the session timestamps: about 2 hours 55 minutes of active work across three sittings (14 Oct 16:36–17:18, 14 Oct 22:51–00:08, and 15 Oct from 08:25). The figure is the same whether idle gaps are cut at 5 or 30 minutes.
- It's section 6 of the README, with a line saying where the time over 2 hours went.
- The earlier "7.5 hours" in my review was wrong: that was the wall-clock span, including a 5½-hour break.

**Session history** ([ai-sessions/](ai-sessions/))
- It now has all 12 sessions, all 48 of your prompts and all 100 subagents, with nothing selected out. That covers the morning sessions and this one.
- The export script is now in the repo as `scripts/export_sessions.py`. Run it again just before you submit so it includes the live-run work. I checked the export for keys and your email address and found none.
- **One thing to know before you submit:** a complete export includes your 23:58 prompt asking Claude to "omit anything that makes me look less favourably". The new `ai-sessions/README.md` openly says the earlier export was a selection and has been replaced. Leaving that prompt out would make the "complete" claim false, and I'd keep it in: being upfront about it reads better than being caught.

## Plan for the live test (for your go-ahead)

The idea is to measure on samples and scale the measured cost to 1,000 messages, rather than running 1,000 messages through each model. Costs below are estimated from list prices.

| Step | What runs | Est. cost |
|---|---|---|
| 0. Smoke | 1 call to each of the 5 models, to catch config errors and see real thinking-token usage | ~$0.02 |
| 1. Keyhook 30 | 5 models × 30 messages × 3 repeats, no judge (gives consistency between runs) | ~$1.40 |
| 2. Suite | the 4 cheap models on all 349 messages; Sonnet on holdout + Keyhook only (123) | ~$2.75 |
| 3. Blind sets | the chosen model on both blind sets (200) | ~$0.15 |
| 4. Judge | `gpt-6-sol` scores actions on Keyhook 30 for every model (150 calls) | ~$1.35 |
| **Total** | | **~$5.70**, worst case ~$9 if thinking tokens double it |

**Each model's results:** pass rate, emergency recall, escalation recall, unsafe actions, failure rate, latency, and real cost per 1,000 messages taken from OpenRouter's own cost figures.

**Keeping it cheap:**
- I'd avoid running the judge across the whole suite. At about $0.009 per call it would cost over $11 for five models.
- I'd stop after step 0 to check real token use before scaling up.
- The existing caps stay in place: $3 per run and $10 in total, which leaves at least $5 of the $15.

Want me to go ahead with this once the key is in `.env`?


### 09:29 · Prompt

> yes

<details><summary>1 tool call (Bash)</summary>

- Bash: Check whether the key has been added to .env

</details>

The key is in place. Starting step 0 with the smoke test on Haiku, the configured model.

<details><summary>3 tool calls (Bash ×3)</summary>

- Bash: Run the live smoke test on the configured Haiku model
- Bash: Smoke-test the four comparison models
- Bash: Run step 1: five models on Keyhook's 30 messages, 3 repeats

</details>

Step 1 is running in the background: 450 calls, an estimated $1–2. I'll report when it finishes.

<details><summary>4 tool calls (Bash ×4)</summary>

- Bash: Summarise step 1 results and spend
- Bash: Inspect per-model gate failures, tokens and consistency
- Bash: List under-triage, missed escalations and fail-safes per model
- Bash: Run step 2: cheap models on the full suite, Sonnet on holdout

</details>

Step 2 is running in the background: about 1,490 calls, estimated at $1.55.


### 09:58 · Prompt

> why is this taking so long?

<details><summary>1 tool call (Bash)</summary>

- Bash: Check step 2 progress per model

</details>

It's slow because the calls run 5 at a time, and the current model, DeepSeek, is the slowest at 8–13 seconds per call.

| Model | Suite progress | Cost |
|---|---|---|
| Haiku | done (348 of 349 cached; 1 call failed and was escalated) | $0.19 |
| GPT-6 Luna | done | $0.11 |
| Gemini | done | $0.63 |
| DeepSeek | 131 of 349 | running |

DeepSeek should finish in about 6–8 minutes, then Sonnet on the 93 holdout messages takes about 2 more. Total spend so far is **$1.79** of the $15 key.

If you'd rather not wait, I can stop DeepSeek now. It already failed two safety gates on Keyhook's 30, so its suite numbers won't change the model choice. Otherwise I'll report when it's done.


### 10:05 · Prompt

> report progress now

<details><summary>1 tool call (Bash)</summary>

- Bash: Report step 2 progress and finished-model results

</details>

DeepSeek is nearly done: 329 of 349 suite messages. Sonnet's 93 holdout messages run after that, about 2 minutes. Total spend so far is **$1.79** of $15.

Here are the results on the full 349-message suite for the three models that have finished:

| Model | Pass rate | Emergency recall | Escalation recall (missed) | Under / over-triage | Failed triage | $ per 1,000 | Safety gates |
|---|---|---|---|---|---|---|---|
| **GPT-6 Luna** | **80%** | 100% | 97% (6) | 5 / 18 | 0 | **$0.32** | **all pass** |
| Haiku 5.5 | 72% | 100% | **99.5% (1)** | **2** / 29 | 1 | $0.54 | 1 fails (that 1 failed triage) |
| Gemini Flash Lite | 72% | 90% | 97% (7) | 9 / 27 | 0 | $1.80 | 1 fails (missed emergencies) |

**What this shows so far:**
- **Luna is the surprise.** It is cheaper than Haiku, classifies better, and passes every gate on the suite. But it misses more escalations: 6 against Haiku's 1. It also rated the rent-withholding message (msg_027) routine in all 3 runs on Keyhook's 30.
- **Haiku is still the safest model.** It has the fewest missed escalations and the least under-triage. Its one failed gate is a single call that failed and was escalated as designed, not a wrong answer. I'll check that error next; failed calls aren't cached, so retrying it costs about $0.0005.
- **Gemini is out.** It missed 4 emergencies and doesn't use the prompt cache.
- **No sign of overfitting.** Real dev and holdout pass rates are close for Haiku (72% / 72%) and Luna (80% / 80%).

When step 2 finishes, the decision is between Haiku and Luna. My suggestion is to judge both models' actions on Keyhook's 30 (step 4, about $0.55) and run the blind sets on both (step 3, about $0.20). Even with all of that, total spend should stay around $3.

<details><summary>6 tool calls (Bash ×6)</summary>

- Bash: Get DeepSeek and Sonnet results and Haiku's fail-safe error
- Bash: Find Sonnet spend and the Haiku fail-safe error text
- Bash: Show the message Haiku failed on
- Bash: Retry Haiku's failed call and run the judge on Haiku's Keyhook 30
- Bash: Inspect the metadata of Haiku's failing call on msg_255
- Bash: Judge four models on Keyhook 30, then blind sets for Haiku and Luna

</details>

Steps 3 and 4 are running in the background: 120 judge calls plus 400 blind-set calls, about 5 minutes. I'll report when they finish.


### 10:14 · Prompt

> tell me the progress

<details><summary>1 tool call (Bash)</summary>

- Bash: Show judge and blind-set progress

</details>

Nearly finished. Only Luna's two blind sets are left, about 2 minutes. Total spend is **$3.07** of $15.

**Step 4: judge on Keyhook's 30, scoring the quality of each `required_action`** (`gpt-6-sol`, about $0.07 per model)

| Model | Action quality (0–2) | Unsafe actions | Gates on Keyhook 30 |
|---|---|---|---|
| Sonnet 5.5 | **1.63** | 0 | all pass |
| Haiku 5.5 | 1.43 | 0 | all pass |
| DeepSeek V4 Flash | 1.33 | **2** (msg_011 lockout, msg_017 auto-reply) | 2 fail |
| GPT-6 Luna | 1.30 | 0 | all pass |
| Gemini Flash Lite | 1.30 | 0 | all pass |

**Step 3: blind sets, which the prompt was never tuned on**

| Haiku 5.5 | Pass rate | Emergency recall | Escalation recall (missed) | Under-triage | $ per 1,000 |
|---|---|---|---|---|---|
| Claude blind set (80) | 80% | 100% | 100% (0) | 1 | $0.49 |
| ChatGPT blind set (120) | 77% | 100% | 98% (1) | 1 | $0.47 |

Haiku's one failed gate on the Claude blind set is another failed triage, which escalated as designed. I'll check whether it's the provider's content filter again.

**Where this is heading:** the choice is Haiku or Luna. Haiku misses the fewest escalations and writes better actions (1.43 against 1.30). Luna is cheaper, $0.32 against $0.54 per 1,000, and classifies better. Luna's blind-set numbers will settle it.

<details><summary>1 tool call (Bash)</summary>

- Bash: Show Luna blind-set results and locate Haiku blind run

</details>

Luna's blind results are in. Checking what caused Haiku's failed triage on the Claude blind set.

<details><summary>1 tool call (Bash)</summary>

- Bash: Identify Haiku's failed blind-set message and its finish reason

</details>

All steps are done. Haiku's failure on the Claude blind set has the same cause as before: on blind_066 the provider's content filter cut the answer off, and the message escalated as designed. I didn't read that message, so the blind set stays blind.

## Live results

Total spend is about **$3.15 of $15**. That's every live call so far: the smoke tests, 5 models on Keyhook's 30 × 3 repeats, 4 models on the full suite, Sonnet on the holdout, the judge on 5 models, and the blind sets for Haiku and Luna.

| | **Haiku 5.5** | **GPT-6 Luna** | Sonnet 5.5 | DeepSeek V4 Flash | Gemini Flash Lite |
|---|---|---|---|---|---|
| Keyhook 30 pass rate (3 repeats) | 86% | 90% | 92% | 86% | 80% |
| Suite pass rate (349) | 72% | 80% | 86% (holdout only) | 76% | 72% |
| Emergency recall, all sets | **100%** | **100%** | 100% | 95% | 90% |
| Missed escalations: suite / Claude blind / ChatGPT blind | **1 / 0 / 1** | 6 / 0 / 2 | 1 (holdout) | 17 / – / – | 7 / – / – |
| Under-triage: suite / Claude blind / ChatGPT blind | **2 / 1 / 1** | 5 / 2 / **9** | 0 (holdout) | 10 | 9 |
| Action quality (judge, 0–2) / unsafe actions | 1.43 / 0 | 1.30 / 0 | 1.63 / 0 | 1.33 / **2** | 1.30 / 0 |
| Failed triage | 2 (both the provider's content filter) | 0 | 0 | 2 | 0 |
| **Measured $ per 1,000 messages** | $0.40–0.54 | **$0.25–0.32** | $7.05–8.12 | $0.16–0.19 | $1.74–1.80 |

**Haiku's content-filter failures.** On about 2 of 549 messages, the provider's filter stops Haiku's answer partway through, and both messages escalate as designed. The code still makes a pointless second attempt when this happens. That's worth a small fix: either skip the retry, or send the message to a fallback model.

**The model choice is now a real decision.**
- **By your pre-stated rule (cheapest model that passes every gate), Luna wins.** It passed every gate on every dataset, and it costs about 40% less than Haiku.
- **Haiku is the safer model.** The gate it fails is "no failed triage", and both failures were safe outcomes: the messages went to a person. Luna's misses are silent. It under-triaged 9 messages on the ChatGPT blind set against Haiku's 1, rated the rent-withholding message routine in all 3 runs, and missed more escalations.

**My recommendation is Haiku.** Under-triage and missed escalations are the errors that hurt tenants, and the cost gap is about $0.20 per 1,000 messages. But choosing Haiku means changing the rule after seeing the results, and blind-set results informed the choice. Both facts must be stated in the README and changelog, which your `CLAUDE.md` requires anyway. Choosing Luna keeps the rule exactly as written, and the README would then list its under-triage as a known weakness.

Which model should go in `config.yaml`?

<details><summary>1 tool call (AskUserQuestion)</summary>

- AskUserQuestion

</details>

Haiku stays, which is already the setting in `config.yaml`. Now I'm pulling Haiku's exact live numbers per dataset for the README, including the truly blind ChatGPT slice.

<details><summary>1 tool call (Bash)</summary>

- Bash: Compute live per-dataset metrics for Haiku and Luna

</details>

I have the numbers. Rewriting README sections 2 and 3 around the live results.

<details><summary>4 tool calls (Bash ×3, Read)</summary>

- Read: `~/Developer/keyhook-tech-test/README.md`
- Bash: Rewrite README model, cost and results sections with live numbers
- Bash: Check the interval and the end of the changelog
- Bash: Note live results in EVALUATION.md and log the live run in the changelog

</details>

Changelog and docs are updated. Last steps: refresh the time statement and re-export the session history so it covers the live run.

<details><summary>5 tool calls (Bash ×5)</summary>

- Bash: Recompute active time including this morning's live run
- Bash: Show the current time-spent section
- Bash: Update time statement, session index and export title
- Bash: Regenerate session export and check for secrets
- Bash: Align session index with the exporter's counts

</details>

The live run is finished, and everything now uses its numbers. All of it, including the smoke tests, used **about $3.15 of the $15 key**. Haiku stays in `config.yaml`, as you chose. All 160 tests pass, and nothing is committed yet.

**What the live run found**
- **Smoke test:** passed on all five models. Each returned valid strict JSON on the first try.
- **Haiku's real cost:** about **$0.40 per 1,000 messages** when the prompt cache is warm, and about $1.00 when it isn't. Output tokens, mostly thinking, are now the biggest cost.
- **Haiku's real accuracy:**
  - no missed emergency on any dataset
  - 1 missed escalation across the 349-message suite
  - 86% pass rate on Keyhook's 30 over 3 repeats
  - dev and holdout scores within a point of each other (72% and 73%), so the prompt isn't overfitted to its tuning messages
- **New finding:** on 2 of 549 messages, both containing injection text, the provider's content filter cut Haiku's answer off. Both escalated to a person, as designed. The code still makes a pointless second attempt on these, so the cheap fix is to skip that retry or send the message to a fallback model.

**What I changed**
- **README sections 2 and 3:** rebuilt on the live results, with the five-model comparison and Haiku's per-dataset table. The replay numbers are gone from the README.
  - Section 2 states plainly that your original rule picks Luna, and that you chose Haiku after seeing the results, blind sets included. Haiku's failures went to a person; Luna's under-triage and missed escalations are silent.
  - Sections 4 and 5 now cover the content-filter issue, and section 5 marks the live run as done.
- **Time statement:** now about **4 hours across three sittings**, which includes this morning's work and the live runs.
- **`PROMPT_CHANGELOG.md`:** new entry for the live run, including that blind-set results informed the model choice, as your `CLAUDE.md` requires.
- **`docs/EVALUATION.md`:** a note at the top says its numbers are from replay runs and that the live ones are in the README.
- **Session history:** re-exported with all 52 prompts across 12 sessions and nothing omitted. I checked it for keys and your email address and found none.
- **New reports:** the live reports for each model, the model-comparison tables and the blind-set reports are new, untracked files in `reports/`.

**Before you submit**
1. **README length:** it's back up to 1,759 words because of the live comparison table. I can trim it towards 1,200, for example by moving the five-model table into `docs/EVALUATION.md` and keeping a three-line summary.
2. **Content-filter fix:** worth doing, about 10 lines plus a test.
3. **Commit and push**, then run `scripts/export_sessions.py` one last time so the history includes this final stretch.

Want me to do all three?


### 10:22 · Prompt

> yes do all 3 and then am i ready to submit?

Starting with the content-filter fix in `call_model`.

<details><summary>4 tool calls (Bash ×2, Edit ×2)</summary>

- Bash: Locate the truncation handling and its test
- Edit: `~/Developer/keyhook-tech-test/triage/agent.py`
- Edit: `~/Developer/keyhook-tech-test/tests/test_agent.py`
- Bash: Run tests and confirm the fix live on msg_255

</details>

The fix works live: msg_255 now fails closed after one attempt instead of two, with a clear reason. Next, the changelog entry, then trimming the README.

<details><summary>4 tool calls (Bash ×3, Read)</summary>

- Bash: Log the content-filter change and view sections to restructure
- Read: `~/Developer/keyhook-tech-test/README.md`
- Bash: Trim README section 2 and move the full table to EVALUATION.md
- Bash: Count README prose words excluding tables and code

</details>

Prose is at 1,260 words. A few more cuts will bring it to about 1,150.

<details><summary>1 tool call (Bash)</summary>

- Bash: Make final README trims and rerun tests

</details>

The README is down to about 1,250 words of prose plus three tables, roughly two pages. Now the final export, then the commit and push.

<details><summary>1 tool call (Bash)</summary>

- Bash: Check remote, re-export sessions, scan for secrets, review changes

</details>


---

## Subagents delegated in this session

Each subagent's full brief and final report.

### Independent LLM-judge review

*general-purpose* · `claude-opus-5-5` · started 09:07

<details><summary>Brief</summary>

```text
You are a hiring panel reviewer at Keyhook (a NZ property-management software company) grading a candidate's take-home for an "AI Product Engineer" role. You have never seen this submission before. The repo is at ~/Developer/keyhook-tech-test. Do NOT make any network/API calls and do NOT run anything that calls OpenRouter (no `triage.agent` without --offline-style flags, no `triage.eval` live, no `triage.compare`). You may read files and run `.venv/bin/python -m pytest -q`. Do not modify any files.

THE BRIEF (verbatim essentials):
- Time: around 2 hours, 4 hours max. Submit within 1 week. Model budget: US$15 OpenRouter key. Stack: candidate's choice. AI tools encouraged.
- Problem: property managers receive tenant messages (maintenance, rent questions, complaints, etc.). Build an agent that triages these messages, AND an evaluation harness that tells you, with evidence, how well it does.
- Provided: tenant_emails.json (~30 synthetic labelled messages, "some of it is messy"), OpenRouter key.
- Build 1) triage agent producing structured output: category (maintenance/arrears/complaint/enquiry/other), urgency (emergency/urgent/routine), required_action, escalate_to_human, reasoning. May adjust/extend schema with justification. Some messages contain multiple requests; decide how to handle. 2) Eval harness "something we can run" that measures performance against labelled data and reports results. 3) Short write-up, README fine, ~1-2 pages: approach & key decisions/trade-offs; model choice and why with estimated cost per 1,000 messages in production; eval results and what they do/don't tell you; where the agent fails/is weakest; what would need to be true before trusting it with real tenants.
- Using AI: include AI session history (raw is fine, don't tidy). "We want to see how you plan, check, and correct course." Be ready to explain any code.
- Key: hard spend limit $15, treat as production budget. Use it for agent and evals. Any OpenRouter model fair game. Never commit key; use env var + .env.example. "We can see the key's usage history (models called, volume and cost), and we'll look at it alongside your submission."
- Submit: repo/zip with agent, eval harness, clear run instructions; write-up; AI session history. "We'll also run your agent against some additional messages you haven't seen, using our own key and your chosen configuration, so please make the model and settings easy to change via config."
- Criteria: Problem framing (interpret brief, handle ambiguity); Verification (how you know the agent works, how much you trust what AI wrote); Evaluation quality (harness measures something meaningful); Judgement on models and cost (sensible for production, incl. knowing when LLM vs plain code is right); Production thinking (safety, failure handling, when a human is needed); Honesty (clear-eyed limitations beat inflated ones).

IMPORTANT CONTEXT: the candidate has NOT yet run anything with the real OpenRouter key; all results so far came from "replay mode" (Claude Code subagents answering the prompts). Factor this in, and also judge what would happen if it's submitted as-is.

YOUR TASK: Do a thorough first-impression-then-deep review as a skeptical but fair senior reviewer. Specifically:
1. First impression (first 5 minutes): what does a reviewer see opening the repo and README? Is it clear, within ~1-2 pages, easy to run?
2. Try to mentally (and where safe, actually, offline) follow the "Keyhook runs it on unseen messages with our own key" path: what input format does `triage.agent` accept? Would a messages file without `expected` labels work? What happens with missing fields (no subject, no from_name, no id)? Would `triage.eval` work on a new labelled file in the same format as tenant_emails.json? Check the code paths carefully and report any crash risk with file:line.
3. Read the core code (triage/agent.py, client.py, guardrails.py, schema.py, prompts.py (at least the active version), eval.py, metrics.py, config.py) and look for real bugs, over-engineering, and things the reviewer would ask about in an interview.
4. Score each of the 6 criteria 1-5 with one-paragraph justification, plus an overall hire signal.
5. List concrete things that would LOWER the score, ranked by impact, and concrete fixes.
Report back in a structured way, under ~1500 words, with file:line references.
```

</details>

