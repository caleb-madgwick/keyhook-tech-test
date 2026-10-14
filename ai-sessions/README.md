# AI session history

I built this project with Claude Code over one day, 14 October 2026 (AEDT). This folder holds the prompts I gave it and a readable transcript of every session.

- **[prompts.md](prompts.md)**: all the prompts on one page, grouped by session.
- **[transcripts/](transcripts/)**: one file per session, with my prompts, Claude's replies, a one-line summary of each tool call, and the brief and final report of every subagent it delegated to.

## Tools and models

| Tool | Used for |
|---|---|
| Claude Code, Claude Opus 5.5 | All 10 working sessions: planning, building, reviewing and fixing |
| Claude Haiku 5.5 subagents (54) | Stand-in for the production model: they answered the exact system prompt and message the agent sends, so the eval ran without API spend |
| Claude Sonnet 5.5 subagents (16) | The LLM judge for `required_action`, a different model from the stand-in agent |
| Claude Opus 5.5 subagents (16) | Writing the 349-message edge-case suite and the 80-message Claude blind set, extracting labelling conventions, and the senior-engineer and security reviews |
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
| 10 | [Status check and final fixes](transcripts/10-status-check-and-final-fixes.md) | 23:47 to 00:04 | 2 | 1 |

1. **Plan before code.** Claude read the brief and the 30 seed messages and proposed an architecture before writing anything (session 1).
2. **Edge-case suite.** In a parallel session, ten subagents each wrote about 30 labelled messages for one risk group: emergencies, non-English, injection, contradictions, noise and so on (session 2).
3. **Build and review.** Claude built the agent and harness, then an LLM "senior engineer" reviewed it. I asked for the work to be finished without paying for API calls, so the eval ran in replay mode: Haiku subagents answered as the model, and Sonnet subagents judged the actions (session 1).
4. **Blind test sets.** A fresh Claude subagent wrote an 80-message blind set (session 1). Because that set and the generated suite share a model family with the agent, Claude also wrote a prompt for ChatGPT to produce a 120-message blind set from Keyhook's label definitions only (session 3).
5. **Independent checks.** `/code-review`, `/security-review` and a `/claude-api` pricing check each ran in their own session, and their fixes were logged in `PROMPT_CHANGELOG.md` (sessions 4 to 9).
6. **Final pass.** A status check, the last fixes and the commit (session 10).

Several sessions ran at the same time, so their times overlap. `CLAUDE.md` and `PROMPT_CHANGELOG.md` kept them coordinated.

## About this export

- **Prompts** are quoted verbatim, typos included. Large pasted data, the ChatGPT JSON, is replaced by a one-line summary.
- **Selection.** This is a selection, not a raw dump: 30 of the 35 prompts I typed are included. The 5 left out were short operational questions and troubleshooting, and Claude's replies to them are left out too. Nothing included has been reworded.
- **Tool output** (file contents, command output, diffs) is left out for length. Each tool call keeps a one-line summary.
- **Housekeeping.** Home-directory paths are shortened to `~`. Times are AEDT.
- **Source.** Generated from the Claude Code transcripts in `~/.claude/projects/` for this repository.
