# Working rules

## PROMPT_CHANGELOG.md must stay complete
Several Claude sessions work in this repo, often at the same time. Every one of them keeps `PROMPT_CHANGELOG.md` up to date:

- **Prompt changes.** Any change to a system prompt in `triage/prompts.py` gets a new version (`SYSTEM_PROMPTS["vN"]`; never edit a version that has been run) and a `## vN` entry: what triggered it, what changed, and the results it was based on.
- **Behaviour changes in code.** Any code or config change that alters triage output without changing the prompt gets a `### Post-freeze code change: ... (no prompt change)` entry. This covers `guardrails.apply_policy`, `policy.*` in `config.yaml`, schema escalation reasons and the language backstop.
- **Blind and holdout data.** Note it whenever a decision was informed by holdout or blind-set results, so those numbers aren't claimed as blind.
- **When to write it.** Write the entry in the same piece of work as the change, not later. Check the end of the file first, because another session may have just added to it.
