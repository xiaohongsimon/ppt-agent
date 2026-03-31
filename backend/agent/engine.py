"""Agent Engine: converts PresentationIntent -> PresentationRenderSpec via LLM."""

import json

import anthropic

from backend.agent.prompts import SYSTEM_PROMPT, build_user_prompt
from backend.config import settings
from backend.schemas.intent import PresentationIntent
from backend.schemas.render_spec import PresentationRenderSpec


async def _call_llm(prompt: str) -> str:
    """Call the Anthropic API with the system prompt and user prompt."""
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model=settings.llm_model,
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


async def generate_render_spec(intent: PresentationIntent) -> PresentationRenderSpec:
    """Generate a PresentationRenderSpec from a PresentationIntent via LLM."""
    intent_json = intent.model_dump_json(indent=2)
    prompt = build_user_prompt(intent_json)
    raw = await _call_llm(prompt)

    # Strip markdown code fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()

    data = json.loads(cleaned)
    return PresentationRenderSpec.model_validate(data)
