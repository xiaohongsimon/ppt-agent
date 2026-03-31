"""VLM side-by-side comparison of original vs generated presentations."""

import base64
import json
from dataclasses import dataclass, field
from pathlib import Path

import anthropic

from backend.config import settings

COMPARE_SYSTEM_PROMPT = """You are an expert presentation design judge. You will see pairs of slides:
the ORIGINAL (a real, well-designed presentation) and the GENERATED (an AI-recreated version).

Evaluate the GENERATED version against the ORIGINAL across these dimensions:

1. **visual_fidelity** (1-10): How well does the generated version capture the visual essence?
   Layout structure, whitespace, visual hierarchy, color harmony.
2. **content_accuracy** (1-10): Is the same information conveyed? Nothing lost or hallucinated?
3. **design_quality** (1-10): Pure design quality of the generated version.
   NOTE: It CAN score HIGHER than the original if the generated version is genuinely better designed.
4. **information_clarity** (1-10): How clearly does the generated version communicate the key message?

Output ONLY valid JSON:
{
  "overall_score": float,
  "dimensions": {
    "visual_fidelity": float,
    "content_accuracy": float,
    "design_quality": float,
    "information_clarity": float
  },
  "what_original_does_better": ["specific observations"],
  "what_generated_does_better": ["specific observations"],
  "improvement_suggestions": ["actionable suggestions for the generation system"],
  "critical_issues": ["any deal-breaker problems like overflow, unreadable text, etc."]
}"""


@dataclass
class ComparisonResult:
    overall_score: float = 0.0
    dimensions: dict[str, float] = field(default_factory=dict)
    what_original_does_better: list[str] = field(default_factory=list)
    what_generated_does_better: list[str] = field(default_factory=list)
    improvement_suggestions: list[str] = field(default_factory=list)
    critical_issues: list[str] = field(default_factory=list)


def _encode_image(path: Path) -> dict:
    """Encode image as base64 for Claude Vision API."""
    data = Path(path).read_bytes()
    b64 = base64.b64encode(data).decode("utf-8")
    suffix = Path(path).suffix.lower()
    media_type = "image/png" if suffix == ".png" else "image/jpeg"
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": media_type, "data": b64},
    }


async def compare_slides(
    original_screenshots: list[Path],
    generated_screenshots: list[Path],
) -> ComparisonResult:
    """Compare original vs generated presentations using VLM.

    Sends pairs of screenshots to Claude Vision for side-by-side evaluation.

    Args:
        original_screenshots: Screenshots of the original (ground truth) PPT.
        generated_screenshots: Screenshots of our generated version.

    Returns:
        ComparisonResult with scores and detailed feedback.
    """
    # Build the vision prompt with interleaved original/generated images
    content: list[dict] = [
        {"type": "text", "text": "Compare these presentations. ORIGINAL slides first, then GENERATED slides.\n\n--- ORIGINAL SLIDES ---"},
    ]

    for i, path in enumerate(original_screenshots[:10]):  # Cap at 10 slides
        if Path(path).exists():
            content.append({"type": "text", "text": f"Original slide {i + 1}:"})
            content.append(_encode_image(path))

    content.append({"type": "text", "text": "\n--- GENERATED SLIDES ---"})

    for i, path in enumerate(generated_screenshots[:10]):
        if Path(path).exists():
            content.append({"type": "text", "text": f"Generated slide {i + 1}:"})
            content.append(_encode_image(path))

    content.append({"type": "text", "text": "\nNow evaluate the GENERATED version against the ORIGINAL. Output JSON only."})

    # Call VLM
    kwargs = {"api_key": settings.anthropic_api_key}
    if settings.anthropic_base_url:
        kwargs["base_url"] = settings.anthropic_base_url
    client = anthropic.AsyncAnthropic(**kwargs)

    message = await client.messages.create(
        model=settings.vlm_model,
        max_tokens=2048,
        system=COMPARE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]

    data = json.loads(raw.strip())

    return ComparisonResult(
        overall_score=data.get("overall_score", 0),
        dimensions=data.get("dimensions", {}),
        what_original_does_better=data.get("what_original_does_better", []),
        what_generated_does_better=data.get("what_generated_does_better", []),
        improvement_suggestions=data.get("improvement_suggestions", []),
        critical_issues=data.get("critical_issues", []),
    )
