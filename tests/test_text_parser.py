"""Tests for backend.input_parser.text_parser."""
import pytest
from unittest.mock import AsyncMock, patch

from backend.input_parser.text_parser import parse_text
from backend.schemas.intent import PresentationIntent

MOCK_LLM_RESPONSE = '{"title":"Q1 Algorithm Team Review","context":{"scene":"quarterly_review","audience":"VP Engineering","tone":"data-driven"},"slides":[{"type":"title","heading":"Q1 Algorithm Team Review","subheading":"2026 Q1"},{"type":"data_driven","heading":"Key Metrics","content":{"key_metrics":[{"label":"GPU utilization","value":"87%"}]},"takeaway":"GPU utilization up 12%"},{"type":"text","heading":"Key Achievements","content":{"bullet_points":["Launched model v3","Reduced latency 40%"]}}]}'


@pytest.mark.asyncio
async def test_parse_text_returns_intent():
    """parse_text should return a PresentationIntent with correct title, slide count, and types."""
    with patch(
        "backend.input_parser.text_parser._call_llm",
        new_callable=AsyncMock,
        return_value=MOCK_LLM_RESPONSE,
    ):
        result = await parse_text("Q1 review for algorithm team")

    assert isinstance(result, PresentationIntent)
    assert result.title == "Q1 Algorithm Team Review"
    assert len(result.slides) == 3
    assert result.slides[0].type == "title"
    assert result.slides[1].type == "data_driven"
    assert result.slides[2].type == "text"


@pytest.mark.asyncio
async def test_parse_text_passes_context():
    """parse_text should include scene and audience in the prompt sent to the LLM."""
    mock_llm = AsyncMock(return_value=MOCK_LLM_RESPONSE)
    with patch(
        "backend.input_parser.text_parser._call_llm",
        mock_llm,
    ):
        await parse_text(
            "Q1 review",
            scene="quarterly_review",
            audience="VP Engineering",
        )

    prompt_arg = mock_llm.call_args[0][0]
    assert "quarterly_review" in prompt_arg
    assert "VP Engineering" in prompt_arg
