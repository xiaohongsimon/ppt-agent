"""Tier 2 Quality Gate: VLM-based visual review via Claude Vision API."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from pathlib import Path

import anthropic

PASS_THRESHOLD = 7.0

VLM_SYSTEM_PROMPT = """\
You are a presentation design reviewer. Evaluate the provided slide screenshots.
Return ONLY valid JSON with this exact schema:
{
  "overall_score": <float 1.0-10.0>,
  "dimensions": {
    "visual_harmony": <float 1.0-10.0>,
    "professional_look": <float 1.0-10.0>,
    "information_clarity": <float 1.0-10.0>,
    "template_adherence": <float 1.0-10.0>
  },
  "issues": ["<string>", ...],
  "suggestions": ["<string>", ...]
}
Score generously for clean designs. Deduct for clutter, poor contrast, or inconsistency."""


@dataclass
class VLMResult:
    passed: bool
    overall_score: float
    dimensions: dict[str, float] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


def _encode_image(path: Path) -> tuple[str, str]:
    """Read an image file and return (base64_data, media_type)."""
    suffix = path.suffix.lower()
    media_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
    media_type = media_map.get(suffix, "image/png")
    data = path.read_bytes()
    return base64.standard_b64encode(data).decode("ascii"), media_type


async def _call_vlm(screenshot_paths: list[Path]) -> dict:
    """Send screenshots to Claude Vision API and return the parsed JSON response."""
    client = anthropic.AsyncAnthropic()

    # Build image content blocks
    content: list[dict] = []
    for p in screenshot_paths:
        b64_data, media_type = _encode_image(p)
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": b64_data,
                },
            }
        )
    content.append({"type": "text", "text": "Review these presentation slides."})

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=VLM_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )

    # Extract text from response
    raw_text = response.content[0].text
    # Strip code fences if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1]
        if raw_text.endswith("```"):
            raw_text = raw_text[: raw_text.rfind("```")]
    return json.loads(raw_text)


async def check_tier2_vlm(
    html_dir: Path | None = None,
    screenshot_paths: list[Path] | None = None,
) -> VLMResult:
    """Run Tier 2 VLM visual review on rendered screenshots.

    Args:
        html_dir: Directory containing rendered HTML (reserved for future use).
        screenshot_paths: Paths to slide screenshot images.

    Returns:
        VLMResult with scores, issues, and suggestions.
    """
    if not screenshot_paths:
        return VLMResult(
            passed=False,
            overall_score=0.0,
            issues=["no screenshots provided for VLM review"],
        )

    result = await _call_vlm(screenshot_paths)

    overall_score = float(result.get("overall_score", 0.0))
    dimensions = result.get("dimensions", {})
    issues = result.get("issues", [])
    suggestions = result.get("suggestions", [])

    return VLMResult(
        passed=overall_score >= PASS_THRESHOLD,
        overall_score=overall_score,
        dimensions=dimensions,
        issues=issues,
        suggestions=suggestions,
    )
