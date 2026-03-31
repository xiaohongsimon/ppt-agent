"""Parse text/outline input into a PresentationIntent via LLM."""
import json
import anthropic
from backend.config import settings
from backend.schemas.intent import PresentationIntent

SYSTEM_PROMPT = """You are a presentation architect. Given user input (text, outline, bullet points),
produce a structured JSON that defines the presentation intent.

Output ONLY valid JSON matching this schema:
{
  "title": "string",
  "context": {"scene": "string", "audience": "string", "tone": "string"},
  "slides": [
    {
      "type": "title|data_driven|text|comparison|visual|closing",
      "heading": "string",
      "subheading": "string or null",
      "content": {object with type-specific data} or null,
      "takeaway": "string or null",
      "speaker_notes": "string or null"
    }
  ]
}

Guidelines:
- First slide should be type "title"
- Last slide should be type "closing" with action items
- Every data slide needs a "takeaway" field
- Aim for 8-15 slides for a typical presentation
- For data_driven slides, include key_metrics in content
- For text slides, include bullet_points in content
- Write in the same language as the user input"""


async def _call_llm(prompt: str) -> str:
    """Call the LLM and return the text response."""
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model=settings.llm_model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


async def parse_text(
    text: str,
    scene: str | None = None,
    audience: str | None = None,
) -> PresentationIntent:
    """Parse text input into a PresentationIntent."""
    parts = [f"Create a presentation from the following input:\n\n{text}"]
    if scene:
        parts.append(f"\nScene: {scene}")
    if audience:
        parts.append(f"\nAudience: {audience}")
    prompt = "\n".join(parts)

    raw = await _call_llm(prompt)

    # Strip markdown code fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()

    data = json.loads(cleaned)
    return PresentationIntent.model_validate(data)
