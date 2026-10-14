# AI session history

I built this project with Claude Code in three sittings on 14 and 15 October 2026 (AEDT), about 4 hours of active work in all: 14 Oct 16:36–17:18 (plan and build), 14 Oct 22:51–00:08 (prompt iterations, blind set, code and security reviews) and 15 Oct 08:25–10:45 (label check, review fixes, live model runs; about 30 minutes of that was waiting on API runs). Session times below run from a session's first to last message, so a session left open between sittings (session 1, for example) spans hours it wasn't in use. This folder holds every prompt I gave it and a readable transcript of every session.

- **[prompts.md](prompts.md)**: all the prompts on one page, grouped by session.
- **[senior_engineer_review.md](senior_engineer_review.md)**: the LLM code review written during the build, kept as a historical record.
- **[transcripts/](transcripts/)**: one file per session, with my prompts, Claude's replies, a one-line summary of each tool call, and the brief and final report of every subagent it delegated to.

## Tools and models

| Tool | Used for |
|---|---|
| Claude Code, Claude Opus 5.5 | All 12 working sessions: planning, building, reviewing and fixing |
| Claude Haiku 5.5 subagents (54) | Stand-in for the production model: they answered the exact system prompt and message the agent sends, so the eval ran without API spend |
| Claude Sonnet 5.5 subagents (22) | The LLM judge for `required_action`, a different model from the stand-in agent, and the Sonnet stand-in in the model comparison |
| Claude Opus 5.5 subagents (24) | Writing the 349-message edge-case suite and the 80-message Claude blind set, extracting labelling conventions, judging the Sonnet comparison, the simplify pass, and the senior-engineer, security and mock-Keyhook reviews |
| ChatGPT | Writing the 120-message blind test set from Keyhook's label definitions only. Claude wrote the prompt I gave ChatGPT (session 3); ChatGPT's output is in `data/blind_raw/` |

## How the work went

| # | Session | Time (AEDT) | Prompts | Subagents |
|---|---|---|---|---|
| 1 | [Architecture, build, evaluation harness and prompt iterations](transcripts/01-architecture-build-evaluation-harness-and-prompt-iterations.md) | 16:36 to 23:56 | 4 | 72 |
| 2 | [Generating the 349-message edge-case suite](transcripts/02-generating-the-349-message-edge-case-suite.md) | 16:43 to 16:53 | 1 | 10 |
| 3 | [README, ChatGPT blind test set and label review](transcripts/03-readme-chatgpt-blind-test-set-and-label-review.md) | 22:59 to 23:39 | 9 | 0 |
| 4 | [Prompt changelog tracking across sessions](transcripts/04-prompt-changelog-tracking-across-sessions.md) | 23:26 to 23:29 | 2 | 0 |
| 5 | [Claude skills, code review and security review](transcripts/05-claude-skills-code-review-and-security-review.md) | 23:28 to 23:40 | 4 | 1 |
| 6 | [Git repository setup](transcripts/06-git-repository-setup.md) | 23:34 to 23:35 | 1 | 0 |
| 7 | [Security review](transcripts/07-security-review.md) | 23:35 to 23:40 | 3 | 1 |
| 8 | [High-effort code review](transcripts/08-high-effort-code-review.md) | 23:37 to 23:45 | 2 | 1 |
| 9 | [Pricing and prompt-caching check against the Claude API docs](transcripts/09-pricing-and-prompt-caching-check-against-the-claude-api-docs.md) | 23:37 to 23:44 | 2 | 0 |
| 10 | [Status check, final fixes, label review and README rewrite](transcripts/10-status-check-final-fixes-label-review-and-readme-rewrite.md) | 23:47 to 00:08, then 08:25 to 09:03 next day | 11 | 10 |
| 11 | [Simplify pass over the whole project](transcripts/11-simplify-pass-over-the-whole-project.md) | 08:40 to 09:04 | 2 | 4 |
| 12 | [Mock Keyhook review, fixes, live model runs and this export](transcripts/12-mock-keyhook-review-fixes-live-model-runs-and-this-export.md) | 09:06 to 10:23 | 8 | 1 |

1. **Plan before code.** Claude read the brief and the 30 seed messages and proposed an architecture before writing anything (session 1).
2. **Edge-case suite.** In a parallel session, ten subagents each wrote about 30 labelled messages for one risk group: emergencies, non-English, injection, contradictions, noise and so on (session 2).
3. **Build and review.** Claude built the agent and harness, then an LLM "senior engineer" reviewed it. I asked for the work to be finished without paying for API calls, so the eval ran in replay mode: Haiku subagents answered as the model, and Sonnet subagents judged the actions (session 1).
4. **Blind test sets.** A fresh Claude subagent wrote an 80-message blind set (session 1). Because that set and the generated suite share a model family with the agent, Claude also wrote a prompt for ChatGPT to produce a 120-message blind set from Keyhook's label definitions only (session 3).
5. **Independent checks.** `/code-review`, `/security-review` and a `/claude-api` pricing check each ran in their own session, and their fixes were logged in `PROMPT_CHANGELOG.md` (sessions 4 to 9).
6. **Final pass.** A status check, the last fixes and the commit (session 10).
7. **Next morning.** A hand-check of the blind-set labels, a Haiku-vs-Sonnet comparison, a README rewrite and a simplify pass (sessions 10 and 11). Then a mock Keyhook review by me and an independent subagent, its fixes, a shorter README, the first live OpenRouter run of all five models (about $3.15), the model decision, and this full export (session 12).

Several sessions ran at the same time, so their times overlap. `CLAUDE.md` and `PROMPT_CHANGELOG.md` kept them coordinated.

## About this export

- **Complete.** Every prompt I typed into a main session is included verbatim, typos and all. That includes operational questions and the prompt where I first asked for a selective export. An earlier version of this folder was a selection (30 of 35 prompts, stopping at midnight); it was replaced by this complete one.
- **Not prompts:** subagent hand-backs and system notifications that arrive as messages are left out, as are slash-command boilerplate and IDE context.
- **Large pasted data**, the ChatGPT JSON, is replaced by a one-line summary. Other pasted text shows its first 15 lines.
- **Tool output** (file contents, command output, diffs) is left out for length. Each tool call keeps a one-line summary, and each subagent's full brief and final report are at the end of its session.
- **Housekeeping.** Home-directory paths are shortened to `~`, and anything shaped like an API key is redacted. Times are AEDT.
- **Source.** `python scripts/export_sessions.py ai-sessions` regenerates this folder from the Claude Code transcripts in `~/.claude/projects/`.
