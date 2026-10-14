# 8. High-effort code review

Claude Code session, Wed 14 Oct, 23:37 to 23:45 AEDT. 2 prompts, 1 subagent.

Prompts are quoted verbatim. Claude's replies are shown in full; tool calls are collapsed to one line each and tool output is left out.

### 23:37 · Prompt

> /code-review high


### 23:40 · Prompt

> fix all issues

I'll start by reading the relevant code.

<details><summary>4 tool calls (Bash ×4)</summary>

- Bash: Show diff stats and guardrails module
- Bash: Show code diff, eval judge section, changelog tail
- Bash: Show eval/judge diff and judge section of eval
- Bash: Inspect eval hashing, refresh, judge config, changelog tail

</details>

Finding 7 looks already fixed in the working tree, since the `\b` is gone. Before editing, I'll check the tests, the original `ZERO_WIDTH`, and the judge cache files on disk.

<details><summary>1 tool call (Bash)</summary>

- Bash: Show guardrails and test diffs

</details>

Next I'll check whether the judge caches on disk still hold legacy `action_hash` records, and whether any dataset contains delimiter-like text, bidi marks or tag characters.

<details><summary>6 tool calls (Bash ×6)</summary>

- Bash: Count legacy judge records and scan datasets
- Bash: Snapshot per-message input hashes before edits
- Bash: Run snapshot with repo on the path
- Bash: Include root datasets in the snapshot
- Bash: Find usages and related schema/tests
- Bash: Find usages of guardrail constants

</details>

Now editing `guardrails.py`: first the delimiter pattern, then the invisible-character handling, the timestamp and the fail-safe.

<details><summary>4 tool calls (Edit ×4)</summary>

- Edit: `~/Developer/keyhook-tech-test/triage/guardrails.py`
- Edit: `~/Developer/keyhook-tech-test/triage/guardrails.py`
- Edit: `~/Developer/keyhook-tech-test/triage/guardrails.py`
- Edit: `~/Developer/keyhook-tech-test/triage/guardrails.py`

</details>

Next, the invisible-character classes. The current regex holds literal invisible characters, so I'll swap that block with a short script.

<details><summary>3 tool calls (Bash ×3)</summary>

- Bash: Replace invisible-character regex block
- Bash: Check whether the escapes were written literally
- Bash: Show the new lines as ASCII escapes

</details>

The `\u` escapes were written as literal invisible characters. They work, but I'll rewrite them as escapes so they're readable.

<details><summary>1 tool call (Bash)</summary>

- Bash: Rewrite character classes as readable escapes

</details>

Now the pre-check that uses these classes, and the fail-safe wording.

<details><summary>5 tool calls (Edit ×4, Read)</summary>

- Read: `~/Developer/keyhook-tech-test/triage/guardrails.py`
- Edit: `~/Developer/keyhook-tech-test/triage/guardrails.py`
- Edit: `~/Developer/keyhook-tech-test/triage/guardrails.py`
- Edit: `~/Developer/keyhook-tech-test/triage/guardrails.py`
- Edit: `~/Developer/keyhook-tech-test/triage/guardrails.py`

</details>

Now the eval harness: reuse legacy verdicts for a live judge, and compute each key's action once.

<details><summary>1 tool call (Edit)</summary>

- Edit: `~/Developer/keyhook-tech-test/triage/eval.py`

</details>

`--refresh` also deletes the cached agent results, so pointing people at it would cost agent calls. I'll name the judge file in the message instead.

<details><summary>1 tool call (Edit)</summary>

- Edit: `~/Developer/keyhook-tech-test/triage/eval.py`

</details>

Next, the tests: update the ones whose expected behaviour changed and add regression tests for each finding.

<details><summary>3 tool calls (Bash ×3)</summary>

- Bash: Read affected test sections
- Bash: Update and add guardrail and eval tests
- Bash: Run the test suite

</details>

These failures are a mistake in my test, not the code: the intro line also contains `<tenant_message>`. I'll fix the count.

<details><summary>1 tool call (Bash)</summary>

- Bash: Fix test tag count and rerun tests

</details>

The tests pass. Now I'll rerun the before/after snapshot to confirm no dataset message's input, injection hits or judge input changed.

<details><summary>1 tool call (Bash)</summary>

- Bash: Compare per-message snapshot before and after

</details>

No dataset message's input, injection hits, obfuscation flag or judge input changed. One more check: whether any current report contains fail-safe rows, which the new fail-safe wording would change.

<details><summary>1 tool call (Bash)</summary>

- Bash: Look for reports containing fail-safe rows

</details>

No report has any fail-safe rows, so no scored result changes. Now the changelog entry. I'll check the end of the file first in case another session has added to it.

<details><summary>1 tool call (Bash)</summary>

- Bash: Check the end of the changelog

</details>

Another session has added an entry since my last look, so I'll append mine after it.

<details><summary>1 tool call (Bash)</summary>

- Bash: Append changelog entry for these fixes

</details>

I'll check whether the README describes the fail-safe or obfuscation behaviour I just changed.

<details><summary>2 tool calls (Bash ×2)</summary>

- Bash: Search README for affected behaviour
- Bash: Update README note, rerun tests, show diff stats

</details>

I fixed all 8 findings. All 151 tests pass, and I ran the pre-check and prompt-building code over all 579 dataset messages before and after: no input hash, injection hit, obfuscation flag or judge input changed. No current report has a fail-safe row either, so the new fail-safe wording changes no score.

1. **Delimiter eating tenant text (finding 1):** `_DELIMITER` now matches only the tag head plus any letters joined to it. `</tenant_message I have a gas leak…` now becomes `[removed tag] I have a gas leak…`, so the text after the tag survives. Only text shaped like a tag matches (a closing slash, a joined name, or a spaced name closed by `>`), so "rent < tenant message limit" is no longer flagged.
2. **False emergencies in the fail-safe (finding 2):** a keyword hit still puts the message at the top of the queue (urgency `emergency`). It no longer gets the `emergency` reason or the definite 111 directive. Instead it gets a new fixed text, `FAILSAFE_HAZARD_ACTION`, which says what to do *if* it describes a current danger. This partly reverses what the earlier changelog entry said about fail-safe emergencies.
3. **Timestamp crash (finding 3):** if converting `received_at` to NZ time overflows, the prompt now says "unknown (unreadable timestamp)" instead of raising `OverflowError`. One such message can no longer abort a whole eval run.
4. **Invisible characters (finding 4):** directional marks (LRM, RLM and the bidi controls) are still stripped but no longer count as obfuscation, so RTL email isn't flagged. Scotland/Wales-style flag emoji are left intact. Other tag characters are still stripped and counted.
5. **Judge cache (finding 5):** a live (paid) judge reuses old verdicts that only have `action_hash`, as long as the action still matches. The run prints how many it reused and which file to delete to re-judge them. The catch is that those old verdicts can't notice a corrected label. A replay judge still re-judges them, which is free and leaves current results unchanged; every judge cache on disk today is a replay judge.
6. **Duplicate pattern (finding 6):** `INJECTION_PATTERNS` now uses `_DELIMITER.pattern`, so there is only one copy.
7. **Word-character variants (finding 7):** the `\b` had already been removed in the working tree. `</tenant_messages>`, `</tenant_message_>`, `<tenantmessage>` and `<tenant-message>` are now covered by tests.
8. **Repeated work in eval (finding 8):** each key's final action is now computed once per run instead of up to three times.

I added regression tests for each finding and updated the tests whose expected behaviour changed (the fail-safe test and the invisible-character tests) in [tests/test_guardrails.py](tests/test_guardrails.py) and [tests/test_eval.py](tests/test_eval.py). I appended a changelog entry at the end of [PROMPT_CHANGELOG.md](PROMPT_CHANGELOG.md), after the prompt-caching entry another session had just added, and updated the obfuscation line in [README.md:47](README.md#L47). That session's changes to `client.py`, `config.py` and `replay.py` are in the working tree too; I didn't touch them.


---

## Subagents delegated in this session

Each subagent's full brief and final report.

### Subagent (no description)

*general-purpose* · `claude-opus-5-5` · started 23:37

<details><summary>Brief</summary>

```text
`high effort → 8 inline angles → dedup (no verify) → ≤10 findings`

You are reviewing for **recall** at high effort: catch every real bug a careful
reviewer would catch in one sitting. At this level, catching real bugs matters
more than avoiding false positives. Err on the side of surfacing.

## Phase 0 — Gather the diff

Run `git diff @{upstream}...HEAD` (or `git diff main...HEAD` / `git diff HEAD~1`
if there's no upstream) to get the unified diff under review. If there are
uncommitted changes, or the range diff is empty, also run `git diff HEAD` and
include the working-tree changes in scope — the review often runs before the
commit. If a PR number, branch name, or file path was passed as an argument,
review that target instead. Treat this diff as the review scope.

## Phase 1 — Find candidates (3 correctness angles + 3 cleanup angles + 1 altitude angle + 1 conventions angle, up to 6 each)

Run **8 independent finder angles** in sequence yourself, in THIS context — do NOT spawn subagents for them. Each
surfaces **up to 6 candidate findings** with `file`, `line`, a one-line
`summary`, and a concrete `failure_scenario`.

### Angle A — line-by-line diff scan

Read every hunk in the diff, line by line. Then Read the enclosing function for
each hunk — bugs in unchanged lines of a touched function are in scope (the PR
re-exposes or fails to fix them). For every line ask: what input, state, timing,
or platform makes this line wrong? Look for inverted/wrong conditions,
off-by-one, null/undefined deref, missing `await`, falsy-zero checks,
wrong-variable copy-paste, error swallowed in catch, unescaped regex metachars.

### Angle B — removed-behavior auditor

For every line the diff DELETES or replaces, name the invariant or behavior it
enforced, then search the new code for where that invariant is re-established.
If you can't find it, that's a candidate: a removed guard, a dropped error
path, a narrowed validation, a deleted test that was covering a real case.

### Angle C — cross-file tracer

For each function the diff changes, find its callers (Grep for the symbol) and
check whether the change breaks any call site: a new precondition, a changed
return shape, a new exception, a timing/ordering dependency. Also check callees:
does a parallel change in the same PR make a call unsafe?

### Reuse

The angles above hunt for bugs; this one and the next two hunt for cleanup in
the changed code. Flag new code that re-implements something the codebase
already has — Grep shared/utility modules and files adjacent to the change,
and name the existing helper to call instead.

### Simplification

Flag unnecessary complexity the diff adds: redundant or derivable state,
copy-paste with slight variation, deep nesting, dead code left behind. Name
the simpler form that does the same job.

### Efficiency

Flag wasted work the diff introduces: redundant computation or repeated I/O,
independent operations run sequentially, blocking work added to startup or
hot paths. Also flag long-lived objects built from closures or captured
environments — they keep the entire enclosing scope alive for the object's
lifetime (a memory leak when that scope holds large values); prefer a
class/struct that copies only the fields it needs. Name the cheaper
alternative.

### Altitude

Check that each change fixes the root cause at the right depth rather than
patching a symptom with a fragile bandaid. Special cases layered on shared
infrastructure are a sign the fix isn't deep enough — prefer the simpler, more
general change to the underlying mechanism over adding special cases, and name
that change.

### Conventions (CLAUDE.md)

Find the CLAUDE.md files that govern the changed code: the user-level
~/.claude/CLAUDE.md, the repo-root CLAUDE.md, plus any CLAUDE.md or
CLAUDE.local.md in a directory that is an ancestor of a changed file (a
directory's CLAUDE.md only applies to files at or below it). Read each one
that exists, then check the diff for clear violations of the rules they state.

Only flag a violation when you can quote the exact rule and the exact line
that breaks it — no style preferences, no vague "spirit of the doc"
inferences. In the finding, name the CLAUDE.md path and quote the rule so the
report can cite it. If no CLAUDE.md applies, return nothing for this angle.

Cleanup, altitude, and conventions candidates use the same
`file`/`line`/`summary` shape; in `failure_scenario`, state the concrete
cost (what is duplicated, wasted, harder to maintain, or which CLAUDE.md rule
is broken) instead of a crash. Correctness bugs always outrank cleanup,
altitude, and conventions findings when the output cap forces a cut.

Pass every candidate with a nameable failure scenario through — finders that
silently drop half-believed candidates are the dominant cause of misses.

## Phase 2 — Dedup only (no verify)

Pool all candidates. Dedup near-duplicates only (same defect, same location, same reason → keep one). Do NOT run verifiers; do NOT re-judge. Sort by severity.

## Output

Target **at least 5 findings**. If fewer genuine findings exist, emit what you have — do not invent to hit the floor.

Return findings as a JSON array of at most 10 objects:

ˋˋˋjson
[
  {
    "file": "path/to/file.ext",
    "line": 123,
    "summary": "one-sentence statement of the bug",
    "failure_scenario": "concrete inputs/state → wrong output/crash"
  }
]
ˋˋˋ

Ranked most-severe first. If more than 10 survive, keep the 10 most
severe. If nothing survives, return `[]`. Do not call the
ReportFindings tool even if it is available - this review's
output contract is the JSON block above.
```

</details>

<details><summary>Report</summary>

```json
[
  {
    "file": "triage/guardrails.py",
    "line": 176,
    "summary": "In `_DELIMITER`, the `>` is optional and up to 100 non-bracket characters are matched greedily, so `_neutralise` deletes real tenant text as well as the fake tag.",
    "failure_scenario": "Body `</tenant_message I have a gas leak and the kitchen is filling with smell please call` becomes just `[removed tag]` (checked against the working tree). The model never sees 'gas leak', so it can rate the message routine/other. The injection hit still escalates it, but at the wrong urgency, so it is not at the top of the human queue. Prose like 'rent < tenant message limit' also matches the backstop and is wrongly escalated."
  },
  {
    "file": "triage/guardrails.py",
    "line": 300,
    "summary": "The fail-safe now adds the 111/'phone the tenant now' `EMERGENCY_PREAMBLE` and the `emergency` reason whenever `EMERGENCY_HINTS` matches. That regex is described as deliberately over-matching, which was only acceptable while it just set the queue position.",
    "failure_scenario": "A model timeout on 'Question about my gas bill' or 'smoke alarm battery is chirping' produces a required_action that starts 'EMERGENCY - phone the tenant now ... call 111 (or the gas emergency line) immediately', plus an `emergency` escalation reason. The PM gets a false emergency directive, and the comment on EMERGENCY_HINTS (lines 64-66) no longer holds."
  },
  {
    "file": "triage/guardrails.py",
    "line": 163,
    "summary": "`describe_received_at` only catches `ValueError`. A sender-controlled timestamp that parses but overflows when moved to NZ time raises `OverflowError`, even though the changelog says non-string or bad values no longer crash.",
    "failure_scenario": "`received_at = '0001-01-01T00:00:00+05:00'` or `'9999-12-31T23:59:59-05:00'` raises `OverflowError: date value out of range` (checked). In eval, `_input_hash` runs for every message up front with no try, and `judge_input_hash` now formats the message too, so one such message aborts the whole eval run. In production it becomes a fail-safe instead of a normal triage."
  },
  {
    "file": "triage/guardrails.py",
    "line": 76,
    "summary": "`ZERO_WIDTH` now also strips and counts LRM/RLM, bidi embeddings and isolates, and Unicode tag characters. These appear legitimately in RTL-language email and in subdivision flag emoji, and they count toward the obfuscation threshold of 10.",
    "failure_scenario": "Two Scotland/Wales flag emoji (6 tag characters each) give `obfuscated=True` (checked). The message is escalated as `obfuscated_content`, the model is told it is 'likely an attempt to hide text from filters', and the flags are turned into plain black flags. An Arabic or Hebrew email written in Outlook or on a phone with a dozen RLM marks is flagged the same way."
  },
  {
    "file": "triage/eval.py",
    "line": 275,
    "summary": "The judge-cache field was renamed from `action_hash` to `judge_input_hash` with no fallback. Every judge verdict already on disk now fails the filter and is thrown away.",
    "failure_scenario": "The next eval with the real API judge re-judges every cached key across the suite (349), blind sets (80+120) and seed set: hundreds of paid judge calls, counted against the budget cap, for inputs that have not changed. If the cap is hit partway, the remaining judge calls are skipped and those messages are scored without a verdict. The changelog only covers replay mode ('costs nothing')."
  },
  {
    "file": "triage/guardrails.py",
    "line": 50,
    "summary": "The delimiter pattern appears twice as a literal (once in `INJECTION_PATTERNS`, once as `_DELIMITER` at line 176), held together only by a 'kept in step' comment.",
    "failure_scenario": "A later fix to one copy (for example the content-eating issue above) does not reach the other. Then neutralisation and detection disagree: a variant is stripped but not flagged, or flagged but left in the prompt. Defining `_DELIMITER` first and using `_DELIMITER.pattern` in the list removes the risk."
  },
  {
    "file": "triage/guardrails.py",
    "line": 176,
    "summary": "The `\\b` straight after `message` means delimiter near-variants that continue with word characters are neither neutralised nor flagged.",
    "failure_scenario": "`</tenant_message_>` or `</tenant_messages>` is not matched, because `_` and `s` are word characters, so there is no word boundary after 'message'. The tag reaches the model inside the untrusted block and can still read as a close of the delimiter, which is the near-variant gap this change was meant to close."
  },
  {
    "file": "triage/eval.py",
    "line": 292,
    "summary": "For each judged key, `judge_input_hash` calls `final_action` again, which reruns the full `_prediction` (precheck, finalize and the policy), on top of the call made for the judge request and the one made during cache filtering.",
    "failure_scenario": "Each judged message runs precheck, finalize and `format_message_for_llm` about three times, which is wasted CPU on every run of several hundred messages. Computing the action once in `judge_one` and passing it to both the judge call and the hash avoids this."
  }
]
```

The working tree changed while I was reviewing. `PROMPT_CHANGELOG.md` and the tests were updated mid-review: the `test_non_english_no_action_not_escalated` failure I first saw is gone (125 tests pass) and a post-freeze changelog entry now exists. I dropped both of those candidate findings.

</details>

