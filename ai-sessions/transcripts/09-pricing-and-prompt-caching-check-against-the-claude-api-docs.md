# 9. Pricing and prompt-caching check against the Claude API docs

Claude Code session, Wed 14 Oct, 23:37 to 23:44 AEDT. 3 prompts, 0 subagents.

Prompts are quoted verbatim. Claude's replies are shown in full; tool calls are collapsed to one line each and tool output is left out.

### 23:37 · Prompt

> /claude-api check the Haiku 5.5 pricing and caching assumptions in README.md

<details><summary>5 tool calls (Bash ×5)</summary>

- Bash: Find pricing and caching mentions in README
- Bash: Read README cost section and caching reference
- Bash: Inspect config and request-building code
- Bash: Estimate system prompt share of input tokens
- Bash: Estimate prompt share and view request body

</details>

Checking how the replay harness counted the 3,376 input tokens, because the v5 system prompt alone comes out at about that size.

<details><summary>2 tool calls (Bash ×2)</summary>

- Bash: Inspect replay token estimator and replay file
- Bash: Find mean token counts in suite reports

</details>

The Haiku 5.5 list prices in README.md are right, but the cost estimate is too low and the caching claim only holds in some conditions. I also found a likely blocker: the config sends `temperature: 0`, which Haiku 5.5 may reject. I haven't edited anything.

## Pricing ([README.md:65-74](README.md#L65-L74))

**Correct:**
- **List prices:** $0.10 input / $0.50 output per million tokens matches Anthropic's first-party rate for `claude-haiku-5-5`. These prices apply to prompts of 100K tokens or fewer, and yours are about 4K, so the higher tier never applies.
- **Arithmetic:** the sums are right for the numbers used (3,376 × $0.10 + 348 × $0.50 ≈ $0.51 per 1,000).

**Problems:**
1. **The numbers come from the old prompt.** 3,376 in / 348 out are the v4 suite figures. `config.yaml` runs v5, and the v5 report shows 3,589 in / 353 out, which is $0.535 per 1,000. The Sonnet 5.5 "about $11" line already uses v5 numbers, so the section mixes two versions.
2. **The JSON schema isn't counted.** The table row says "system prompt, schema and message", but `ReplayClient.chat` only counts the `messages` ([triage/replay.py:61](triage/replay.py#L61)). The schema sent in `response_format` is roughly 750 more input tokens.
3. **Thinking tokens are missing.** Haiku 5.5 has adaptive thinking on by default, at medium effort. With `reasoning: null`, the request takes that default, and thinking is billed as output. The 348-token figure only covers the JSON answer.
4. **The token estimate may be low.** Haiku 5.5's tokenizer produces about 30% more tokens than Haiku 4.5 for the same text. Dividing bytes by 3.5 was a general rule of thumb, so it probably undercounts here.

Adding the schema alone gives about $0.61 per 1,000. I'd expect the real figure to land somewhere around $0.6–1.0 once thinking and the tokenizer are included. That's still cheap, but the README states $0.51 more precisely than the data supports.

## Caching ([README.md:74](README.md#L74))

- **The "about 95%" share holds for v5.** The v5 system prompt is about 3,381 of 3,589 tokens (94%). It's well above Haiku 5.5's 512-token minimum for caching.
- **The saving is real when every request hits the cache.** Cache reads cost 0.1× ($0.01 per million tokens). Caching the system prompt and schema would bring input cost from about $0.43 to about $0.06 per 1,000, so roughly $0.61 to $0.24 overall.
- **It isn't implemented.** [triage/client.py:77-98](triage/client.py#L77-L98) sends no `cache_control`. My understanding is that OpenRouter needs explicit breakpoints for Anthropic models, but that's worth confirming in their docs.
- **It only pays off with steady traffic.** The default cache expires 5 minutes after it was last used, and each fresh write costs 1.25×. A property-manager inbox where emails arrive more than 5 minutes apart would pay that write on almost every message, about 25% more than not caching. Eval runs and busy inboxes would benefit; quiet ones wouldn't. The README should state that condition.

## Likely blocker: `temperature: 0`

The README says "temperature 0", and `config.yaml` sends it on every call. On Haiku 5.5 and Sonnet 5.5, the API returns a 400 for any non-default sampling value. Through OpenRouter that probably means either a 400 or no eligible provider, since `require_parameters: true` is set. Then every message would fail safe, and `python -m triage.compare` would fail for both Anthropic models. I haven't confirmed this with a real call. The fix is to stop sending `temperature` for these models, which would change triage behaviour and so needs a `PROMPT_CHANGELOG.md` entry under the project rules.

I can update the README and make the temperature fix if you'd like. I could also get exact token counts from Anthropic's free token-counting endpoint, if you have an Anthropic key available.


### 23:40 · Prompt

> fix all of these issues

Starting with the code the fixes touch and the uncommitted changes from other sessions, so I don't overwrite their work.

<details><summary>1 tool call (Bash)</summary>

- Bash: Show git state, config loader and client code

</details>

Another session has uncommitted edits in README.md and PROMPT_CHANGELOG.md. I'll make targeted edits on top of their changes instead of rewriting either file.

<details><summary>4 tool calls (Bash ×4)</summary>

- Bash: Check README diff, eval cache key, credentials
- Bash: Fetch OpenRouter model pricing and supported parameters
- Bash: Inspect metadata plumbing, eval CLI and tests
- Bash: Read agent call loop, Meta, metrics, changelog tail

</details>

Now making the code changes, starting with config and the client.

<details><summary>1 tool call (Bash)</summary>

- Bash: Apply temperature, caching and replay-estimate code changes

</details>

Adding tests for the new behaviour, then running the full test suite.

<details><summary>2 tool calls (Bash ×2)</summary>

- Bash: Append client and replay tests
- Bash: Add Path import and run test suite

</details>

All 132 tests pass. Next I'm re-scoring the v5 suite from the recorded replay answers to get the corrected token counts. It writes into the scratchpad so no new report files land in the repo.

<details><summary>3 tool calls (Bash ×2, Read)</summary>

- Bash: Re-score v5 suite replay in scratch root
- Read: `~/Developer/keyhook-tech-test/README.md`
- Bash: Rewrite README model choice and cost section

</details>

Now the changelog entry. Re-checking the end of the file first in case another session has added to it.

<details><summary>2 tool calls (Bash ×2)</summary>

- Bash: Check changelog tail and update test count
- Bash: Append changelog entry and rerun tests

</details>

I've fixed everything I flagged, and the 132 offline tests pass. Nothing has been tested against the live API yet, and nothing is committed.

**Temperature (the blocker).** OpenRouter's public model list confirmed it, and it was wider than I first said. Haiku 5.5, Sonnet 5.5, `gpt-6-luna` and the judge model `gpt-6-sol` all reject `temperature`. Because the config requires providers to support every parameter sent, every live call to those four would have failed safe. `temperature` is now optional, set to `null` for the agent and judge, and the client only sends it when it's set ([triage/client.py](triage/client.py), [config.yaml](config.yaml)). The trade-off: Gemini and DeepSeek, which did accept `temperature: 0`, now run at their default sampling in the comparison, so their output is less repeatable.

**Prompt caching.** A new `prompt_cache: true` setting sends the system prompt as a cacheable block for Anthropic models. OpenAI and DeepSeek cache automatically, so they get the plain request. The cached-token count OpenRouter reports is now stored per message and averaged in the report. I'm fairly confident this is the request shape OpenRouter expects, but it hasn't been checked live. The first real run will show whether cached tokens come back above zero.

**Cost estimate.** Replay mode now counts the JSON schema (about 746 tokens) as input. I re-scored the v5 suite from the recorded answers in the scratchpad, so no new report files were written to the repo. The corrected figures are 4,335 input and 353 output tokens, about **$0.61 per 1,000 messages**, up from the stale v4-based $0.51.

**README cost section**, rewritten with the v5 numbers:
- **Thinking tokens:** a row saying they aren't measured, priced at about $0.05 per 1,000 messages for every 100 tokens.
- **Tokenizer:** a note that real token counts may be higher than the estimate.
- **Caching:** a table showing about $0.31 when messages arrive within 5 minutes of each other, $0.61 without caching, and $0.69 when every message misses. Caching pays off once more than about 1 in 5 messages is a hit.
- **Sonnet comparison:** about $12 per 1,000 (was $11).
- **Comparison run:** about US$2–4 (was $1.50), mostly Sonnet 5.5.

**Things to watch:**
- **The $3 spend cap.** The Sonnet 5.5 run alone costs about $3.10 without caching, so it could hit the per-run cap of $3 if caching misses or thinking is heavy.
- **Cached results.** Changing `temperature` changes the eval cache keys, so the replay runs and replay judges will re-run. That costs nothing, but other sessions will see reports under new names.
- **Other sessions' edits.** README.md, PROMPT_CHANGELOG.md, agent.py and eval.py already had another session's uncommitted changes. I made targeted edits on top and didn't touch theirs. I also changed the README's test count to 132, which was already out of date.

**Changelog.** There's a new post-freeze code-change entry at the end of `PROMPT_CHANGELOG.md` covering all of this. It notes that no blind or holdout results informed it.


### 23:44 · Prompt

> are we actually spending money right now??? i hope we arent because i said not to

<details><summary>1 tool call (Bash)</summary>

- Bash: Check spend ledger and running processes

</details>

No, we're not spending anything. I made no paid API calls in this session, and nothing is running now. I checked:

- **No recorded spend.** The spend ledger (`runs/spend_ledger.jsonl`) doesn't exist, and the harness only creates it when a real call costs money. So no paid call has ever been recorded in this repo.
- **Nothing running.** No triage processes are active.

What I did that touched a model or the network:

| What | Cost | Why it was free |
|---|---|---|
| Fetched OpenRouter's public model list (`/api/v1/models`) | $0 | It's a free public catalogue read, made without your API key. It just lists prices and supported parameters. |
| Re-scored the v5 suite | $0 | Replay mode reads the recorded answers in `replays/` and never calls the API. It printed "Spent this run: agent $0.0000". |
| Ran the 132 tests | $0 | The client tests use a fake network that never leaves the machine. |
| Anthropic API | not used | No Anthropic key is set up here, so I couldn't call it. |

Earlier I offered to get exact token counts from Anthropic's free token-counting endpoint. I didn't do that.

Nothing I changed spends money on its own. The new caching and temperature settings only take effect when you run the agent against the real API, for example with `python -m triage.compare`. That's still your call to make.
