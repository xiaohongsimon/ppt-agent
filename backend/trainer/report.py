"""Generate markdown training reports."""

from datetime import datetime
from pathlib import Path

from backend.trainer.comparator import ComparisonResult
from backend.trainer.feedback import TrainingFeedback
from backend.trainer.optimizer import OptimizedPrompt, PromptVersion


def generate_round_report(
    round_num: int,
    comparisons: list[ComparisonResult],
    feedback: TrainingFeedback,
    optimized: OptimizedPrompt | None,
    history: list[PromptVersion],
    output_dir: Path,
) -> Path:
    """Generate a markdown report for a training round.

    Returns:
        Path to the generated report file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"round-{round_num:03d}-report.md"

    lines = [
        f"# Training Round {round_num} Report",
        f"\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Samples:** {feedback.sample_count}",
        f"**Average Score:** {feedback.avg_score:.1f}/10",
        "",
    ]

    # Score trend
    if len(history) > 1:
        lines.append("## Score Trend\n")
        lines.append("| Round | Avg Score | Best Dim | Worst Dim |")
        lines.append("|-------|-----------|----------|-----------|")
        for v in history:
            if v.dimension_scores:
                best = max(v.dimension_scores.items(), key=lambda x: x[1])
                worst = min(v.dimension_scores.items(), key=lambda x: x[1])
                lines.append(
                    f"| {v.version} | {v.avg_score:.1f} | {best[0]} ({best[1]:.1f}) | {worst[0]} ({worst[1]:.1f}) |"
                )
            else:
                lines.append(f"| {v.version} | {v.avg_score:.1f} | - | - |")
        lines.append("")

    # Dimension breakdown
    lines.append("## Dimension Scores\n")
    lines.append("| Dimension | Score |")
    lines.append("|-----------|-------|")
    for dim, score in sorted(feedback.dimension_averages.items(), key=lambda x: -x[1]):
        emoji = "🟢" if score >= 7.5 else "🟡" if score >= 6.0 else "🔴"
        lines.append(f"| {emoji} {dim} | {score:.1f} |")
    lines.append("")

    # What original does better
    if feedback.recurring_issues:
        lines.append("## Original Does Better (Recurring)\n")
        for issue in feedback.recurring_issues:
            lines.append(f"- {issue}")
        lines.append("")

    # What generated does better
    if feedback.recurring_strengths:
        lines.append("## Generated Does Better (Recurring)\n")
        for s in feedback.recurring_strengths:
            lines.append(f"- {s}")
        lines.append("")

    # Critical issues
    if feedback.all_critical_issues:
        lines.append("## Critical Issues\n")
        for issue in feedback.all_critical_issues:
            lines.append(f"- ❌ {issue}")
        lines.append("")

    # Prompt changes
    if optimized:
        lines.append("## Prompt Changes This Round\n")
        for change in optimized.changes_made:
            lines.append(f"- {change}")
        lines.append(f"\n**Rationale:** {optimized.rationale}")
        lines.append("")

    # Per-sample scores
    lines.append("## Per-Sample Scores\n")
    lines.append("| # | Overall | Visual | Content | Design | Clarity |")
    lines.append("|---|---------|--------|---------|--------|---------|")
    for i, c in enumerate(comparisons):
        d = c.dimensions
        lines.append(
            f"| {i + 1} | {c.overall_score:.1f} "
            f"| {d.get('visual_fidelity', 0):.1f} "
            f"| {d.get('content_accuracy', 0):.1f} "
            f"| {d.get('design_quality', 0):.1f} "
            f"| {d.get('information_clarity', 0):.1f} |"
        )
    lines.append("")

    report_text = "\n".join(lines)
    report_path.write_text(report_text, encoding="utf-8")
    return report_path
