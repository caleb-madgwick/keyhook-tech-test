# 4. Prompt changelog tracking across sessions

Claude Code session, Wed 14 Oct, 23:26 to 23:29 AEDT. 2 prompts, 0 subagents.

Prompts are quoted verbatim. Claude's replies are shown in full; tool calls are collapsed to one line each and tool output is left out.

### 23:26 · Prompt

> the prompt change log has been recording across all chats right?

<details><summary>4 tool calls (Bash ×4)</summary>

- Bash: Inspect changelog file and any recording mechanism
- Bash: Compare changelog tail with prompt versions and file timestamps
- Bash: Check which sessions touched the changelog and blind set mentions
- Bash: See which sessions edited prompt-related files

</details>

No, nothing is recording it automatically. There's no hook, no CLAUDE.md and no saved memory telling sessions to update [PROMPT_CHANGELOG.md](PROMPT_CHANGELOG.md). It's been written by hand, as a convention the sessions working on the prompt followed.

That said, it does cover every prompt change so far:

- **All prompt versions are logged.** [triage/prompts.py](triage/prompts.py) defines v1 to v4, and each has an entry, including the in-place v2 amendments and the post-freeze safety preamble (a code change, not a prompt change).
- **The sessions that changed the prompt also wrote the log.** Of the four chats in this project, the one that edited `prompts.py` also wrote most of the changelog, and one other chat added to it. The fourth chat never edited the prompt.
- **The timing fits.** `prompts.py` was last edited at 23:09 and the changelog at 23:19.

Two gaps:

1. **Later code changes aren't confirmed as logged.** `agent.py`, `guardrails.py`, `eval.py`, `schema.py`, `config.py` and `offline.py` were all modified at 23:23, after the last changelog write. The changelog is only meant to track prompt changes, so this may be fine. But if any of those edits change triage behaviour, like the emergency preamble did, they probably deserve a "post-freeze code change" entry too.
2. **A new chat won't know to keep the log.** Adding a short CLAUDE.md would fix that, with a rule like "any change to `triage/prompts.py` or post-model policy code gets a new version and an entry in PROMPT_CHANGELOG.md". I can write it if you want, or I can check whether the 23:23 changes need logging.


### 23:28 · Prompt

> well make sure all of this is tracked and is noted in memory

<details><summary>3 tool calls (Bash ×3)</summary>

- Bash: List recent file edits across sessions with timestamps
- Bash: List all recent tool calls across sessions
- Bash: Show tool calls in the 23:15–23:29 window

</details>

The other session (56b8…) is still active and is creating a v5 prompt right now. Let me look at the untracked 23:23 change before touching anything.

<details><summary>5 tool calls (Bash ×3, ToolSearch, ListAgents)</summary>

- Bash: Read the other session's recent policy change and decisions
- Bash: Check policy setting and current changelog state
- ToolSearch: `select:SendMessage`
- ListAgents
- Bash: Get start time of each session transcript

</details>

That session is `keyhook-tech-test-73`. Now I'll add the policy entry to the changelog.

<details><summary>2 tool calls (Read, Edit)</summary>

- Read: `~/Developer/keyhook-tech-test/PROMPT_CHANGELOG.md`
- Edit: `~/Developer/keyhook-tech-test/PROMPT_CHANGELOG.md`

</details>

Next, a CLAUDE.md so every new chat follows the rule automatically:

<details><summary>2 tool calls (Write, SendMessage)</summary>

- Write: `~/Developer/keyhook-tech-test/CLAUDE.md`
- SendMessage

</details>

Now the memory:

<details><summary>2 tool calls (Write ×2)</summary>

- Write: `~/.claude/projects/-Users-calebmadgwick-Developer-keyhook-tech-test/memory/prompt-changelog-tracking.md`
- Write: `~/.claude/projects/-Users-calebmadgwick-Developer-keyhook-tech-test/memory/MEMORY.md`

</details>

Everything that's finished is now tracked. The one piece still open is the v5 entry, which the session building v5 will write once its results are in.

- **Logged the missing change.** I added a [PROMPT_CHANGELOG.md](PROMPT_CHANGELOG.md) entry for the 23:23 change: messages the model rates "medium" confidence now go to a person too. The entry covers the reason (escalation recall was 89% on your ChatGPT blind set, below the 90% gate), the trade-off (about 6–13% more PM reviews) and that the ChatGPT blind set is no longer fully blind for this setting.
- **v5 is handed off.** The session `keyhook-tech-test-73` created prompt v5 at 23:28 to fix the 5 safety misses on your blind set, and is scoring it now. I've messaged it to write the `## v5` entry once it has results, and to note that v4 is no longer the frozen prompt. I didn't write that entry myself, because its results don't exist yet and we'd risk two sessions writing the same entry. Check the changelog once that session finishes.
- **Added a rule for new chats.** I created [CLAUDE.md](CLAUDE.md), which every session in this repo reads at the start. It says every new prompt version and every code or config change that alters triage output gets a changelog entry. It also says to flag any decision based on blind-set results, and to check the end of the file before adding to it.
- **Saved to memory.** I added a note that you want this tracked across all chats. It also says that when you ask "is it all tracked?", the answer comes from checking file timestamps and the other chats' history against the changelog, not from assuming.
