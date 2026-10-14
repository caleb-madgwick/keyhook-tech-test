"""Run the eval for several models and write a side-by-side table.

    python -m triage.compare [--models a,b,c] [--dataset path] [--split dev] [--repeats N] [--judge]

Each model's results are cached like a normal eval run, so re-running is free.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import ROOT, load_config
from .eval import run_eval


def _pct(v) -> str:
    return "n/a" if v is None else f"{v:.0%}"


def main() -> None:
    ap = argparse.ArgumentParser(description="Compare models on the eval set.")
    ap.add_argument("--models", help="Comma-separated; default: eval.compare_models in config.yaml")
    ap.add_argument("--dataset")
    ap.add_argument("--split", choices=["all", "dev", "holdout"], default="all")
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--judge", action="store_true", help="Also run the action judge (costs more)")
    args = ap.parse_args()

    base = load_config()
    models = args.models.split(",") if args.models else base.eval.compare_models
    dataset = args.dataset or base.eval.dataset

    rows = []
    for model in models:
        cfg = load_config(model=model)
        print(f"\n### {model}")
        s = run_eval(cfg, dataset, args.repeats, use_judge=args.judge, split=args.split)
        m = s["metrics"]
        rows.append((model, s, m))

    lines = [
        f"# Model comparison: `{dataset}` (split: {args.split}, repeats: {args.repeats}, "
        f"prompt {base.agent.prompt_version})",
        "",
        "| model | pass | category | urgency | under-triage | emergency recall | esc. recall | esc. precision "
        "| fail-safe | $/1k msgs | p50 latency | gates |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for model, s, m in rows:
        c, u, e, r = m["category"], m["urgency"], m["escalation"], m["reliability"]
        gates_failed = sum(not g["passed"] for g in s["gates"])
        lines.append(
            f"| `{model}` | {_pct(m['pass_rate'])} | {_pct(c['strict_accuracy'])} | {_pct(u['accuracy'])} | "
            f"{u['under_triage']} | {_pct(u['emergency_recall'])} | {_pct(e['recall'])} | {_pct(e['precision'])} | "
            f"{r['failsafe_count']} | ${r['mean_cost_usd'] * 1000:.2f} | {r['latency_p50_ms']} ms | "
            f"{'PASS' if gates_failed == 0 else f'{gates_failed} failed'} |"
        )
    out = ROOT / "reports" / f"model_comparison__{Path(dataset).stem}__{args.split}.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n" + "\n".join(lines))
    print(f"\nWritten to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
