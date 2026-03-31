"""IR Input: What the user wants to present (from Input Parser -> Agent Engine)."""
from pydantic import BaseModel


class SlideIntent(BaseModel):
    """A single slide's intent -- what information should appear."""
    type: str  # "title", "data_driven", "text", "comparison", "visual", "closing"
    heading: str
    subheading: str | None = None
    content: dict | None = None  # Flexible: key_metrics, bullet_points, chart_data, etc.
    takeaway: str | None = None
    speaker_notes: str | None = None


class PresentationIntent(BaseModel):
    """Complete presentation intent -- the contract from Input Parser to Agent Engine."""
    title: str
    context: dict  # scene, audience, tone
    slides: list[SlideIntent]
    source_analysis: dict | None = None
    user_profile_hints: dict | None = None
