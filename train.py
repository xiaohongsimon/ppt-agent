"""PPT-Agent Training CLI — self-improvement loop."""

import argparse
import asyncio
import json
from pathlib import Path

from backend.trainer.loop import run_training_loop
from backend.trainer.optimizer import load_history


async def main():
    parser = argparse.ArgumentParser(description="PPT-Agent Self-Improvement Training")
    parser.add_argument("--corpus", default="./backend/trainer/data/corpus", help="PPTX corpus directory")
    parser.add_argument("--rounds", type=int, default=3, help="Number of training rounds")
    parser.add_argument("--output", default="./training_runs", help="Output directory for runs")
    parser.add_argument("--eval-only", action="store_true", help="Evaluate only, don't optimize prompts")
    parser.add_argument("--history", action="store_true", help="Show training history")
    parser.add_argument("--step", choices=["prepare", "render", "report"],
                        help="Run a single step (for Claude Code mode, no API needed)")
    args = parser.parse_args()

    # Stepped mode (for Claude Code — no API key needed)
    if args.step:
        from backend.trainer.steps import step_prepare, step_render, step_report
        if args.step == "prepare":
            step_prepare(Path(args.corpus))
        elif args.step == "render":
            step_render()
        elif args.step == "report":
            step_report()
        return

    if args.history:
        history = load_history(Path(args.output) / "history.json")
        if not history:
            print("No training history found.")
            return
        print(f"{'Version':<10} {'Score':<10} {'Changes'}")
        print("-" * 60)
        for v in history:
            changes = "; ".join(v.changes_from_previous[:2])
            if len(v.changes_from_previous) > 2:
                changes += f" (+{len(v.changes_from_previous) - 2} more)"
            print(f"v{v.version:<9} {v.avg_score:<10.1f} {changes}")
        return

    await run_training_loop(
        corpus_dir=Path(args.corpus),
        rounds=args.rounds,
        output_dir=Path(args.output),
        eval_only=args.eval_only,
    )


if __name__ == "__main__":
    asyncio.run(main())
