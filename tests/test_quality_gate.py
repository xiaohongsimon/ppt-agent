"""Tests for Quality Gate: Tier 1 rules, Tier 2 VLM, and orchestrator."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.schemas.render_spec import (
    Component,
    PresentationRenderSpec,
    SlideRenderSpec,
)
from backend.quality_gate.tier1_rules import (
    MAX_BULLET_ITEMS,
    Tier1Result,
    check_tier1,
)
from backend.quality_gate.tier2_vlm import (
    PASS_THRESHOLD,
    VLMResult,
    check_tier2_vlm,
)
from backend.quality_gate.gate import (
    QualityGateResult,
    run_quality_gate,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_theme() -> dict:
    return {"--primary": "#1a1a2e", "--accent": "#e94560"}


def _make_spec(slides: list[SlideRenderSpec]) -> PresentationRenderSpec:
    return PresentationRenderSpec(
        title="Test Deck",
        theme=_make_theme(),
        slides=slides,
    )


# ---------------------------------------------------------------------------
# Tier 1 Tests
# ---------------------------------------------------------------------------


class TestTier1Rules:

    def test_tier1_passes_good_slide(self):
        """Title + data_driven with card_grid + highlight_box passes."""
        spec = _make_spec([
            SlideRenderSpec(
                slide_index=0,
                layout="title",
                heading="Welcome",
            ),
            SlideRenderSpec(
                slide_index=1,
                layout="data_driven",
                heading="Key Metrics",
                components=[
                    Component(
                        type="card_grid",
                        props={"cards": [
                            {"label": "Revenue", "value": "$10M"},
                            {"label": "Users", "value": "50K"},
                        ]},
                    ),
                    Component(
                        type="highlight_box",
                        props={"text": "Revenue up 35%", "color": "green"},
                    ),
                ],
            ),
        ])
        result = check_tier1(spec)
        assert result.passed is True
        assert result.issues == []
        assert result.slide_issues == {}

    def test_tier1_catches_too_many_bullets(self):
        """10 bullet items should fail."""
        items = [f"Point {i}" for i in range(10)]
        spec = _make_spec([
            SlideRenderSpec(
                slide_index=0,
                layout="title",
                heading="Title",
            ),
            SlideRenderSpec(
                slide_index=1,
                layout="full_visual",
                heading="Long List",
                components=[
                    Component(
                        type="bullet_list",
                        props={"items": items},
                    ),
                ],
            ),
        ])
        result = check_tier1(spec)
        assert result.passed is False
        assert any("bullet_list" in issue for issue in result.issues)
        assert 1 in result.slide_issues

    def test_tier1_catches_missing_takeaway(self):
        """data_driven without highlight_box should fail."""
        spec = _make_spec([
            SlideRenderSpec(
                slide_index=0,
                layout="title",
                heading="Title",
            ),
            SlideRenderSpec(
                slide_index=1,
                layout="data_driven",
                heading="Data Slide",
                components=[
                    Component(
                        type="bar_chart",
                        props={"data": [10, 20, 30]},
                    ),
                ],
            ),
        ])
        result = check_tier1(spec)
        assert result.passed is False
        assert any("highlight_box" in issue for issue in result.issues)

    def test_tier1_catches_too_many_cards(self):
        """7 cards should fail (max 5)."""
        cards = [{"label": f"Card {i}", "value": str(i)} for i in range(7)]
        spec = _make_spec([
            SlideRenderSpec(
                slide_index=0,
                layout="title",
                heading="Title",
            ),
            SlideRenderSpec(
                slide_index=1,
                layout="data_driven",
                heading="Cards Slide",
                components=[
                    Component(
                        type="card_grid",
                        props={"cards": cards},
                    ),
                    Component(
                        type="highlight_box",
                        props={"text": "Takeaway", "color": "blue"},
                    ),
                ],
            ),
        ])
        result = check_tier1(spec)
        assert result.passed is False
        assert any("card_grid" in issue for issue in result.issues)


# ---------------------------------------------------------------------------
# Tier 2 VLM Tests (mocked)
# ---------------------------------------------------------------------------


class TestTier2VLM:

    @pytest.mark.asyncio
    async def test_vlm_passes_good_presentation(self):
        """Mock VLM returns score 8.2 -> passes."""
        mock_response = {
            "overall_score": 8.2,
            "dimensions": {
                "visual_harmony": 8.5,
                "professional_look": 8.0,
                "information_clarity": 8.3,
                "template_adherence": 8.0,
            },
            "issues": [],
            "suggestions": ["Consider adding more whitespace"],
        }

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=json.dumps(mock_response))]

        with patch("backend.quality_gate.tier2_vlm.anthropic") as mock_anthropic:
            mock_client = AsyncMock()
            mock_client.messages.create.return_value = mock_message
            mock_anthropic.AsyncAnthropic.return_value = mock_client

            from pathlib import Path
            from unittest.mock import mock_open

            # Mock Path.read_bytes to return fake PNG data
            with patch.object(Path, "read_bytes", return_value=b"\x89PNG\r\n\x1a\n"):
                result = await check_tier2_vlm(
                    screenshot_paths=[Path("/fake/slide1.png")],
                )

        assert result.passed is True
        assert result.overall_score == 8.2
        assert result.dimensions["visual_harmony"] == 8.5
        assert result.issues == []

    @pytest.mark.asyncio
    async def test_vlm_fails_bad_presentation(self):
        """Mock VLM returns score 5.5 -> fails with issues."""
        mock_response = {
            "overall_score": 5.5,
            "dimensions": {
                "visual_harmony": 5.0,
                "professional_look": 6.0,
                "information_clarity": 5.5,
                "template_adherence": 5.5,
            },
            "issues": ["Poor contrast ratio", "Inconsistent font sizes"],
            "suggestions": ["Increase contrast", "Standardize fonts"],
        }

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=json.dumps(mock_response))]

        with patch("backend.quality_gate.tier2_vlm.anthropic") as mock_anthropic:
            mock_client = AsyncMock()
            mock_client.messages.create.return_value = mock_message
            mock_anthropic.AsyncAnthropic.return_value = mock_client

            from pathlib import Path

            with patch.object(Path, "read_bytes", return_value=b"\x89PNG\r\n\x1a\n"):
                result = await check_tier2_vlm(
                    screenshot_paths=[Path("/fake/slide1.png")],
                )

        assert result.passed is False
        assert result.overall_score == 5.5
        assert len(result.issues) == 2
        assert "Poor contrast ratio" in result.issues


# ---------------------------------------------------------------------------
# Orchestrator Tests
# ---------------------------------------------------------------------------


class TestQualityGateOrchestrator:

    def test_quality_gate_passes_clean_spec(self):
        """Clean spec with skip_vlm=True -> tier1_passed."""
        spec = _make_spec([
            SlideRenderSpec(
                slide_index=0,
                layout="title",
                heading="Welcome",
            ),
            SlideRenderSpec(
                slide_index=1,
                layout="data_driven",
                heading="Metrics",
                components=[
                    Component(
                        type="card_grid",
                        props={"cards": [{"label": "ARR", "value": "$10M"}]},
                    ),
                    Component(
                        type="highlight_box",
                        props={"text": "Strong growth", "color": "green"},
                    ),
                ],
            ),
        ])
        result = run_quality_gate(spec, skip_vlm=True)

        assert result.tier1_passed is True
        assert result.tier1_result.passed is True
        assert result.fixed_spec is None
        assert result.auto_fix_rounds == 0

    def test_quality_gate_auto_fixes_bullets(self):
        """10 bullets -> auto-fixed to 7+3, all items preserved, passes after fix."""
        items = [f"Point {i}" for i in range(10)]
        spec = _make_spec([
            SlideRenderSpec(
                slide_index=0,
                layout="title",
                heading="Title",
            ),
            SlideRenderSpec(
                slide_index=1,
                layout="full_visual",
                heading="Long List",
                components=[
                    Component(
                        type="bullet_list",
                        props={"items": items},
                    ),
                ],
            ),
        ])

        # Verify it fails before fix
        pre_result = check_tier1(spec)
        assert pre_result.passed is False

        # Run orchestrator
        result = run_quality_gate(spec, skip_vlm=True)

        assert result.tier1_passed is True
        assert result.auto_fix_rounds >= 1
        assert result.fixed_spec is not None

        # Verify all original items are preserved across slides
        all_items: list[str] = []
        for slide in result.fixed_spec.slides:
            for comp in slide.components:
                if comp.type == "bullet_list":
                    all_items.extend(comp.props.get("items", []))

        assert sorted(all_items) == sorted(items)

        # Verify the split: first slide has 7, overflow has 3
        bullet_slides = [
            slide for slide in result.fixed_spec.slides
            if any(c.type == "bullet_list" for c in slide.components)
        ]
        assert len(bullet_slides) == 2

        first_bullets = [
            c for c in bullet_slides[0].components if c.type == "bullet_list"
        ][0]
        second_bullets = [
            c for c in bullet_slides[1].components if c.type == "bullet_list"
        ][0]
        assert len(first_bullets.props["items"]) == 7
        assert len(second_bullets.props["items"]) == 3
