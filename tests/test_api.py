"""Tests for REST API routes -- end-to-end with mocked LLM calls."""
import json
from unittest.mock import AsyncMock, patch

import pytest

MOCK_TEXT_PARSE = json.dumps(
    {
        "title": "Test",
        "context": {"scene": "demo"},
        "slides": [
            {"type": "title", "heading": "Test"},
            {"type": "text", "heading": "Details", "content": {"bullet_points": ["A", "B"]}},
        ],
    }
)

MOCK_AGENT = json.dumps(
    {
        "title": "Test",
        "theme": {"accent_primary": "#4f6df5"},
        "slides": [
            {
                "slide_index": 0,
                "layout": "title",
                "heading": "Test",
                "components": [],
            },
            {
                "slide_index": 1,
                "layout": "text",
                "heading": "Details",
                "components": [
                    {
                        "type": "bullet_list",
                        "props": {"items": ["A", "B"]},
                    }
                ],
            },
        ],
    }
)


def test_health(client):
    """GET /health returns 200 with status ok."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_generate_from_text(client, tmp_path):
    """POST /api/v1/generate with mocked LLMs returns a valid response."""
    with (
        patch(
            "backend.input_parser.text_parser._call_llm",
            new_callable=AsyncMock,
            return_value=MOCK_TEXT_PARSE,
        ),
        patch(
            "backend.agent.engine._call_llm",
            new_callable=AsyncMock,
            return_value=MOCK_AGENT,
        ),
        patch("backend.config.settings") as mock_settings,
    ):
        mock_settings.output_dir = str(tmp_path)
        mock_settings.anthropic_api_key = ""
        mock_settings.llm_model = "test"

        resp = client.post(
            "/api/v1/generate",
            json={
                "input_type": "text",
                "content": "A test presentation about testing",
                "scene": "demo",
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "presentation_id" in data
    assert len(data["presentation_id"]) == 8
    assert data["slides_count"] == 2
    assert data["quality_gate"]["tier1_passed"] is True
    assert "html_path" in data
