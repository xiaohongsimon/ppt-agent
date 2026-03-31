"""Aggregate feedback from multiple comparisons into actionable training signals."""

from collections import Counter
from dataclasses import dataclass, field

from backend.trainer.comparator import ComparisonResult


@dataclass
class TrainingFeedback:
    avg_score: float = 0.0
    dimension_averages: dict[str, float] = field(default_factory=dict)
    worst_dimensions: list[tuple[str, float]] = field(default_factory=list)
    recurring_issues: list[str] = field(default_factory=list)
    recurring_strengths: list[str] = field(default_factory=list)
    all_improvement_suggestions: list[str] = field(default_factory=list)
    all_critical_issues: list[str] = field(default_factory=list)
    prompt_hints: list[str] = field(default_factory=list)
    sample_count: int = 0


def aggregate_feedback(comparisons: list[ComparisonResult]) -> TrainingFeedback:
    """Aggregate feedback from multiple comparisons into training signals.

    Args:
        comparisons: List of ComparisonResult from the batch.

    Returns:
        TrainingFeedback with averaged scores, recurring patterns, and hints.
    """
    if not comparisons:
        return TrainingFeedback()

    n = len(comparisons)
    fb = TrainingFeedback(sample_count=n)

    # Average overall score
    fb.avg_score = sum(c.overall_score for c in comparisons) / n

    # Average per-dimension
    dim_totals: dict[str, float] = {}
    dim_counts: dict[str, int] = {}
    for c in comparisons:
        for dim, score in c.dimensions.items():
            dim_totals[dim] = dim_totals.get(dim, 0) + score
            dim_counts[dim] = dim_counts.get(dim, 0) + 1

    fb.dimension_averages = {
        dim: dim_totals[dim] / dim_counts[dim]
        for dim in dim_totals
    }

    # Worst dimensions (sorted ascending)
    fb.worst_dimensions = sorted(fb.dimension_averages.items(), key=lambda x: x[1])

    # Find recurring patterns (mentioned 2+ times)
    issue_counter = Counter()
    strength_counter = Counter()

    for c in comparisons:
        for issue in c.what_original_does_better:
            issue_counter[issue] += 1
        for strength in c.what_generated_does_better:
            strength_counter[strength] += 1

    threshold = max(2, n // 3)  # At least 2 or 1/3 of samples
    fb.recurring_issues = [
        f"{issue} (mentioned {count}x)"
        for issue, count in issue_counter.most_common()
        if count >= threshold
    ]
    fb.recurring_strengths = [
        f"{s} (mentioned {count}x)"
        for s, count in strength_counter.most_common()
        if count >= threshold
    ]

    # Collect all suggestions and critical issues
    for c in comparisons:
        fb.all_improvement_suggestions.extend(c.improvement_suggestions)
        fb.all_critical_issues.extend(c.critical_issues)

    # Deduplicate suggestions
    fb.all_improvement_suggestions = list(dict.fromkeys(fb.all_improvement_suggestions))
    fb.all_critical_issues = list(dict.fromkeys(fb.all_critical_issues))

    # Generate prompt hints from the data
    fb.prompt_hints = _generate_prompt_hints(fb)

    return fb


def _generate_prompt_hints(fb: TrainingFeedback) -> list[str]:
    """Generate specific hints for prompt optimization."""
    hints = []

    # Worst dimension hints
    for dim, score in fb.worst_dimensions:
        if score < 6.0:
            hints.append(f"CRITICAL: '{dim}' scores only {score:.1f}/10 — needs major improvement")
        elif score < 7.5:
            hints.append(f"IMPROVE: '{dim}' scores {score:.1f}/10 — room for improvement")

    # Critical issues → direct rules
    for issue in fb.all_critical_issues[:5]:
        hints.append(f"FIX: {issue}")

    # Top suggestions
    for suggestion in fb.all_improvement_suggestions[:5]:
        hints.append(f"TRY: {suggestion}")

    return hints
