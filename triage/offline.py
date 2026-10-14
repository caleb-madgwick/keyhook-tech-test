"""Produce replay files without the API: export the exact prompts, have any model answer them
(e.g. Claude Code subagents), import the answers as a replay file, then score with
`python -m triage.eval --replay <file>`.

    python -m triage.offline export --dataset tenant_emails_test_suite.json --out runs/offline/suite --chunk 25
    python -m triage.offline import --dir runs/offline/suite --out replays/suite_haiku_subagent.jsonl \
        --producer claude-haiku-subagent

Export writes NO labels: only ids and the exact user turn the agent would send, plus the system
prompt. Answer files are `answers_*.jsonl`, one line per message: {"id": ..., "output": {...}}.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agent import build_user_message, load_messages
from .config import ROOT, load_config
from .eval import split_of
from .guardrails import precheck
from .prompts import SYSTEM_PROMPTS
from .replay import input_key
from .schema import LLM_JSON_SCHEMA


def export(dataset: str, out: Path, chunk: int, split: str) -> None:
    cfg = load_config()
    messages = load_messages(ROOT / dataset)
    if split != "all":
        messages = [m for m in messages if split_of(m) == split]
    out.mkdir(parents=True, exist_ok=True)
    system = SYSTEM_PROMPTS[cfg.agent.prompt_version]
    (out / "system_prompt.md").write_text(
        system + "\n\n## Output format\nReturn ONLY a JSON object matching this JSON schema:\n"
        + json.dumps(LLM_JSON_SCHEMA, indent=1)
    )
    manifest = {"dataset": dataset, "prompt_version": cfg.agent.prompt_version, "keys": {}}
    for n in range(0, len(messages), chunk):
        with (out / f"batch_{n // chunk:03d}.jsonl").open("w") as f:
            for m in messages[n:n + chunk]:
                user = build_user_message(precheck(m))  # identical to what the agent sends
                manifest["keys"][m["id"]] = input_key(system, user)
                f.write(json.dumps({"id": m["id"], "user_message": user}, ensure_ascii=False) + "\n")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"Exported {len(messages)} messages in {(len(messages) + chunk - 1) // chunk} batches to {out}")


def export_judge(dataset: str, replay: str, out: Path, chunk: int) -> None:
    """Export judge prompts for an agent run that is already scored (cached), so a model can act as
    the action-quality judge offline. Requires the agent results to be in the eval cache."""
    from .eval import _load_jsonl, _prediction, run_dir_for
    from .judge import JUDGE_SCHEMA, JUDGE_SYSTEM, build_judge_user

    cfg = load_config(replay=replay)
    by_id = {m["id"]: m for m in load_messages(ROOT / dataset)}
    cached = _load_jsonl(run_dir_for(cfg, dataset) / "results.jsonl")
    if not cached:
        raise SystemExit("No cached agent results for this replay; run triage.eval --replay first.")
    out.mkdir(parents=True, exist_ok=True)
    (out / "system_prompt.md").write_text(
        JUDGE_SYSTEM + "\n\n## Output format\nReturn ONLY a JSON object matching this JSON schema:\n"
        + json.dumps(JUDGE_SCHEMA, indent=1)
    )
    manifest = {"dataset": dataset, "kind": "judge", "keys": {}}
    items = [(mid, rec) for (mid, k), rec in sorted(cached.items())
             if k == 0 and mid in by_id and by_id[mid].get("expected", {}).get("expected_action")]
    for n in range(0, len(items), chunk):
        with (out / f"batch_{n // chunk:03d}.jsonl").open("w") as f:
            for mid, rec in items[n:n + chunk]:
                final_action = _prediction(rec, by_id[mid], cfg)["required_action"]  # what a PM would see
                user = build_judge_user(by_id[mid], by_id[mid]["expected"]["expected_action"], final_action)
                manifest["keys"][mid] = input_key(JUDGE_SYSTEM, user)
                f.write(json.dumps({"id": mid, "user_message": user}, ensure_ascii=False) + "\n")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"Exported {len(items)} judge prompts in {(len(items) + chunk - 1) // chunk} batches to {out}")


def import_answers(directory: Path, out: Path, producer: str) -> None:
    manifest = json.loads((directory / "manifest.json").read_text())
    keys: dict[str, str] = manifest["keys"]
    seen: dict[str, dict] = {}
    bad = 0
    for path in sorted(directory.glob("answers_*.jsonl")):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                mid, output = rec["id"], rec["output"]
            except (json.JSONDecodeError, KeyError, TypeError):
                bad += 1
                continue
            if mid not in keys:
                bad += 1
                continue
            content = output if isinstance(output, str) else json.dumps(output, ensure_ascii=False)
            seen[mid] = {"input_key": keys[mid], "id": mid, "content": content, "producer": producer}
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        for mid in keys:
            if mid in seen:
                f.write(json.dumps(seen[mid], ensure_ascii=False) + "\n")
    missing = [m for m in keys if m not in seen]
    print(f"Imported {len(seen)}/{len(keys)} answers to {out}; {bad} unreadable lines; "
          f"{len(missing)} missing{': ' + ', '.join(missing[:20]) if missing else ''}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Export prompts / import answers for replay evaluation.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("--dataset", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--chunk", type=int, default=25)
    e.add_argument("--split", choices=["all", "dev", "holdout"], default="all")
    j = sub.add_parser("export-judge")
    j.add_argument("--dataset", required=True)
    j.add_argument("--replay", required=True, help="The agent replay file whose actions are judged")
    j.add_argument("--out", required=True)
    j.add_argument("--chunk", type=int, default=30)
    i = sub.add_parser("import")
    i.add_argument("--dir", required=True)
    i.add_argument("--out", required=True)
    i.add_argument("--producer", required=True)
    args = ap.parse_args()
    if args.cmd == "export":
        export(args.dataset, ROOT / args.out, args.chunk, args.split)
    elif args.cmd == "export-judge":
        export_judge(args.dataset, args.replay, ROOT / args.out, args.chunk)
    else:
        import_answers(ROOT / args.dir, ROOT / args.out, args.producer)


if __name__ == "__main__":
    main()
