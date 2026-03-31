"""Tests for the agent engine (PresentationIntent -> PresentationRenderSpec via LLM)."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from backend.agent.engine import generate_render_spec
from backend.schemas.intent import PresentationIntent, SlideIntent

# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

MOCK_LLM_RESPONSE = json.dumps(
    {
        "title": "Q1 Review",
        "theme": {
            "accent_primary": "#4f6df5",
            "accent_secondary": "#7c3aed",
        },
        "slides": [
            {
                "slide_index": 0,
                "layout": "title",
                "heading": "Q1 Algorithm Team Review",
                "subheading": "2026 Q1",
                "components": [],
            },
            {
                "slide_index": 1,
                "layout": "data_driven",
                "heading": "Key Metrics",
                "components": [
                    {
                        "type": "card_grid",
                        "props": {
                            "columns": 3,
                            "cards": [
                                {"title": "GPU Util", "value": "87%", "change": "+12%"},
                            ],
                        },
                    },
                    {
                        "type": "highlight_box",
                        "props": {"text": "GPU utilization up 12% QoQ", "color": "green"},
                    },
                ],
            },
        ],
    }
)


def _make_intent() -> PresentationIntent:
    """Create a PresentationIntent fixture for testing."""
    return PresentationIntent(
        title="Q1 Review",
        context={"scene": "team_meeting", "audience": "engineering_leads", "tone": "professional"},
        slides=[
            SlideIntent(
                type="title",
                heading="Q1 Algorithm Team Review",
                subheading="2026 Q1",
            ),
            SlideIntent(
                type="data_driven",
                heading="Key Metrics",
                content={
                    "key_metrics": [
                        {"label": "GPU Utilization", "value": "87%", "change": "+12%"},
                    ]
                },
                takeaway="GPU utilization up 12% QoQ",
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_render_spec():
    """Verify generate_render_spec returns a valid PresentationRenderSpec."""
    intent = _make_intent()

    with patch("backend.agent.engine._call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = MOCK_LLM_RESPONSE
        spec = await generate_render_spec(intent)

    assert spec.title == "Q1 Review"
    assert len(spec.slides) == 2

    # Title slide
    assert spec.slides[0].layout == "title"
    assert spec.slides[0].heading == "Q1 Algorithm Team Review"
    assert spec.slides[0].components == []

    # Data slide
    assert spec.slides[1].layout == "data_driven"
    component_types = [c.type for c in spec.slides[1].components]
    assert "card_grid" in component_types
    assert "highlight_box" in component_types


@pytest.mark.asyncio
async def test_generate_render_spec_has_theme():
    """Verify the generated spec has a theme with accent_primary."""
    intent = _make_intent()

    with patch("backend.agent.engine._call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = MOCK_LLM_RESPONSE
        spec = await generate_render_spec(intent)

    assert "accent_primary" in spec.theme
    assert spec.theme["accent_primary"] == "#4f6df5"


@pytest.mark.asyncio
async def test_generate_render_spec_strips_code_fences():
    """Verify markdown code fences are stripped from LLM output."""
    intent = _make_intent()
    fenced_response = f"```json\n{MOCK_LLM_RESPONSE}\n```"

    with patch("backend.agent.engine._call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = fenced_response
        spec = await generate_render_spec(intent)

    assert spec.title == "Q1 Review"
    assert len(spec.slides) == 2
