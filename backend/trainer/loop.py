"""Main training loop — orchestrates corpus → regen → compare → feedback → optimize."""

from pathlib import Path

from backend.agent import prompts as agent_prompts
from backend.trainer.comparator import ComparisonResult, compare_slides
from backend.trainer.corpus import CorpusItem, load_corpus
from backend.trainer.feedback import TrainingFeedback, aggregate_feedback
from backend.trainer.optimizer import (
    OptimizedPrompt,
    PromptVersion,
    load_history,
    optimize_prompt,
    save_history,
)
from backend.trainer.regenerator import regenerate
from backend.trainer.report import generate_round_report


async def run_training_loop(
    corpus_dir: Path,
    rounds: int = 3,
    output_dir: Path = Path("./training_runs"),
    eval_only: bool = False,
):
    """Run the self-improvement training loop.

    Args:
        corpus_dir: Directory containing .pptx ground truth files.
        rounds: Number of training rounds.
        output_dir: Where to save run artifacts.
        eval_only: If True, evaluate only (no prompt optimization).
    """
    corpus_dir = Path(corpus_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    history_path = output_dir / "history.json"

    # Load corpus
    print(f"Loading corpus from {corpus_dir}...")
    corpus = load_corpus(corpus_dir)
    if not corpus:
        print("No PPTX files found in corpus directory.")
        return
    print(f"Loaded {len(corpus)} presentations.\n")

    # Load history
    history = load_history(history_path)
    start_version = len(history) + 1

    for round_num in range(start_version, start_version + rounds):
        print(f"{'='*60}")
        print(f"ROUND {round_num}")
        print(f"{'='*60}")

        round_dir = output_dir / f"round-{round_num:03d}"
        round_dir.mkdir(parents=True, exist_ok=True)

        # Save current prompt
        current_prompt = agent_prompts.SYSTEM_PROMPT
        (round_dir / "prompt.txt").write_text(current_prompt, encoding="utf-8")

        # Step 1: Regenerate each presentation
        print(f"\n[1/4] Regenerating {len(corpus)} presentations...")
        regen_results = []
        for i, item in enumerate(corpus):
            print(f"  [{i + 1}/{len(corpus)}] {item.pptx_path.name}")
            try:
                result = await regenerate(item, round_dir / f"regen-{i:03d}")
                regen_results.append((item, result))
                print(f"    → {len(result.screenshots)} slides generated")
            except Exception as e:
                print(f"    → FAILED: {e}")

        if not regen_results:
            print("No successful regenerations. Stopping.")
            return

        # Step 2: VLM comparison
        print(f"\n[2/4] Comparing original vs generated...")
        comparisons: list[ComparisonResult] = []
        for i, (item, result) in enumerate(regen_results):
            print(f"  [{i + 1}/{len(regen_results)}] {item.pptx_path.name}")
            try:
                comp = await compare_slides(
                    item.original_screenshots,
                    result.screenshots,
                )
                comparisons.append(comp)
                print(f"    → Score: {comp.overall_score:.1f}/10")
            except Exception as e:
                print(f"    → COMPARISON FAILED: {e}")

        if not comparisons:
            print("No successful comparisons. Stopping.")
            return

        # Step 3: Aggregate feedback
        print(f"\n[3/4] Aggregating feedback...")
        feedback = aggregate_feedback(comparisons)
        print(f"  Average score: {feedback.avg_score:.1f}/10")
        print(f"  Worst dimension: {feedback.worst_dimensions[0] if feedback.worst_dimensions else 'N/A'}")
        if feedback.prompt_hints:
            print(f"  Prompt hints:")
            for h in feedback.prompt_hints[:3]:
                print(f"    - {h}")

        # Step 4: Optimize prompt (unless eval-only)
        optimized: OptimizedPrompt | None = None
        if not eval_only:
            print(f"\n[4/4] Optimizing prompt...")
            try:
                optimized = await optimize_prompt(current_prompt, feedback, history)
                # Apply the new prompt
                agent_prompts.SYSTEM_PROMPT = optimized.new_prompt
                print(f"  Changes made:")
                for change in optimized.changes_made:
                    print(f"    - {change}")
            except Exception as e:
                print(f"  OPTIMIZATION FAILED: {e}")
        else:
            print(f"\n[4/4] Eval-only mode — skipping prompt optimization")

        # Save version to history
        version = PromptVersion(
            version=round_num,
            prompt=current_prompt if not optimized else optimized.new_prompt,
            avg_score=feedback.avg_score,
            dimension_scores=feedback.dimension_averages,
            changes_from_previous=optimized.changes_made if optimized else ["(eval only)"],
        )
        history.append(version)
        save_history(history, history_path)

        # Generate report
        report_path = generate_round_report(
            round_num, comparisons, feedback, optimized, history, round_dir,
        )
        print(f"\n  Report: {report_path}")

        # Summary
        print(f"\n  Round {round_num} summary: {feedback.avg_score:.1f}/10 avg")
        if len(history) > 1:
            prev = history[-2].avg_score
            delta = feedback.avg_score - prev
            emoji = "📈" if delta > 0 else "📉" if delta < 0 else "➡️"
            print(f"  {emoji} Change from previous: {delta:+.1f}")

    print(f"\n{'='*60}")
    print(f"Training complete. {rounds} rounds finished.")
    print(f"Final avg score: {history[-1].avg_score:.1f}/10")
    if len(history) > 1:
        total_delta = history[-1].avg_score - history[0].avg_score
        print(f"Total improvement: {total_delta:+.1f}")
    print(f"History: {history_path}")
    print(f"{'='*60}")
