"""Tests for the self-improvement training loop modules."""

from backend.trainer.comparator import ComparisonResult
from backend.trainer.feedback import TrainingFeedback, aggregate_feedback
from backend.trainer.optimizer import PromptVersion


def _make_comparison(score: float, **dims) -> ComparisonResult:
    defaults = {
        "visual_fidelity": score,
        "content_accuracy": score + 0.5,
        "design_quality": score - 0.5,
        "information_clarity": score,
    }
    defaults.update(dims)
    return ComparisonResult(
        overall_score=score,
        dimensions=defaults,
        what_original_does_better=["better whitespace", "cleaner fonts"],
        what_generated_does_better=["more data viz"],
        improvement_suggestions=["add more whitespace"],
        critical_issues=[] if score > 6 else ["text overflow"],
    )


def test_aggregate_feedback_avg_score():
    comps = [_make_comparison(7.0), _make_comparison(8.0), _make_comparison(6.0)]
    fb = aggregate_feedback(comps)
    assert fb.sample_count == 3
    assert abs(fb.avg_score - 7.0) < 0.01


def test_aggregate_feedback_dimensions():
    comps = [_make_comparison(7.0), _make_comparison(9.0)]
    fb = aggregate_feedback(comps)
    assert "visual_fidelity" in fb.dimension_averages
    assert abs(fb.dimension_averages["visual_fidelity"] - 8.0) < 0.01


def test_aggregate_feedback_recurring_issues():
    comps = [_make_comparison(7.0), _make_comparison(7.5), _make_comparison(8.0)]
    fb = aggregate_feedback(comps)
    # "better whitespace" and "cleaner fonts" appear in all 3
    assert len(fb.recurring_issues) >= 1


def test_aggregate_feedback_prompt_hints():
    comps = [_make_comparison(4.0), _make_comparison(5.0)]
    fb = aggregate_feedback(comps)
    # Low scores should generate prompt hints
    assert len(fb.prompt_hints) > 0
    assert any("CRITICAL" in h or "IMPROVE" in h or "FIX" in h for h in fb.prompt_hints)


def test_aggregate_feedback_empty():
    fb = aggregate_feedback([])
    assert fb.sample_count == 0
    assert fb.avg_score == 0.0


def test_prompt_version_dataclass():
    v = PromptVersion(
        version=1,
        prompt="test prompt",
        avg_score=7.5,
        dimension_scores={"visual": 8.0},
        changes_from_previous=["added rule"],
    )
    assert v.version == 1
    assert v.avg_score == 7.5
