"""Use LLM to optimize the agent's system prompt based on training feedback."""

import json
from dataclasses import dataclass
from pathlib import Path

import anthropic

from backend.config import settings
from backend.trainer.feedback import TrainingFeedback

OPTIMIZER_SYSTEM_PROMPT = """You are a prompt engineering expert. Your job is to improve an AI system prompt
based on concrete feedback from automated quality evaluation.

You will receive:
1. The CURRENT system prompt (used by a presentation generation AI)
2. FEEDBACK from comparing AI-generated presentations against high-quality originals
3. HISTORY of previous prompt versions and their scores (if any)

Your job:
- Analyze the feedback to understand what the current prompt does wrong
- Make TARGETED improvements — don't rewrite from scratch
- Each change should address a specific feedback signal
- Preserve what's working well (check the strengths)
- Be conservative — small improvements that compound are better than big rewrites

Output ONLY valid JSON:
{
  "new_prompt": "the full improved system prompt text",
  "changes_made": ["description of each specific change"],
  "rationale": "why these changes should improve scores"
}"""


@dataclass
class OptimizedPrompt:
    new_prompt: str
    changes_made: list[str]
    rationale: str


@dataclass
class PromptVersion:
    version: int
    prompt: str
    avg_score: float
    dimension_scores: dict[str, float]
    changes_from_previous: list[str]


async def optimize_prompt(
    current_prompt: str,
    feedback: TrainingFeedback,
    history: list[PromptVersion] | None = None,
) -> OptimizedPrompt:
    """Use LLM to rewrite the system prompt based on feedback.

    Args:
        current_prompt: The current SYSTEM_PROMPT text.
        feedback: Aggregated feedback from the comparison batch.
        history: Previous prompt versions with scores (for learning trajectory).

    Returns:
        OptimizedPrompt with the new prompt and explanation.
    """
    # Build context for the optimizer
    parts = [
        "## CURRENT SYSTEM PROMPT\n",
        f"```\n{current_prompt}\n```\n",
        "\n## FEEDBACK FROM THIS ROUND\n",
        f"Average score: {feedback.avg_score:.1f}/10\n",
        f"Sample count: {feedback.sample_count}\n",
        "\nDimension scores:\n",
    ]
    for dim, score in feedback.dimension_averages.items():
        parts.append(f"  - {dim}: {score:.1f}/10\n")

    if feedback.recurring_issues:
        parts.append("\nRecurring issues (original does better):\n")
        for issue in feedback.recurring_issues:
            parts.append(f"  - {issue}\n")

    if feedback.recurring_strengths:
        parts.append("\nRecurring strengths (generated does better):\n")
        for s in feedback.recurring_strengths:
            parts.append(f"  - {s}\n")

    if feedback.all_critical_issues:
        parts.append("\nCritical issues:\n")
        for issue in feedback.all_critical_issues[:10]:
            parts.append(f"  - {issue}\n")

    if feedback.all_improvement_suggestions:
        parts.append("\nImprovement suggestions:\n")
        for s in feedback.all_improvement_suggestions[:10]:
            parts.append(f"  - {s}\n")

    if feedback.prompt_hints:
        parts.append("\nDirect hints for prompt improvement:\n")
        for h in feedback.prompt_hints:
            parts.append(f"  - {h}\n")

    # Add history if available
    if history:
        parts.append("\n## PROMPT VERSION HISTORY\n")
        for v in history[-3:]:  # Last 3 versions
            parts.append(f"\nVersion {v.version}: avg score {v.avg_score:.1f}\n")
            for change in v.changes_from_previous:
                parts.append(f"  - {change}\n")

    prompt = "".join(parts)

    # Call LLM (use the best model for judgment)
    kwargs = {"api_key": settings.anthropic_api_key}
    if settings.anthropic_base_url:
        kwargs["base_url"] = settings.anthropic_base_url
    client = anthropic.AsyncAnthropic(**kwargs)

    message = await client.messages.create(
        model=settings.llm_model,
        max_tokens=8192,
        system=OPTIMIZER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]

    data = json.loads(raw.strip())

    return OptimizedPrompt(
        new_prompt=data["new_prompt"],
        changes_made=data.get("changes_made", []),
        rationale=data.get("rationale", ""),
    )


def save_history(history: list[PromptVersion], path: Path):
    """Save prompt version history to JSON."""
    data = [
        {
            "version": v.version,
            "prompt": v.prompt,
            "avg_score": v.avg_score,
            "dimension_scores": v.dimension_scores,
            "changes_from_previous": v.changes_from_previous,
        }
        for v in history
    ]
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_history(path: Path) -> list[PromptVersion]:
    """Load prompt version history from JSON."""
    path = Path(path)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        PromptVersion(
            version=d["version"],
            prompt=d["prompt"],
            avg_score=d["avg_score"],
            dimension_scores=d.get("dimension_scores", {}),
            changes_from_previous=d.get("changes_from_previous", []),
        )
        for d in data
    ]
