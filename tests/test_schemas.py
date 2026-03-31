"""Comprehensive tests for IR contracts (PresentationIntent + SlideRenderSpec)."""
import json

import pytest

from backend.schemas import (
    Component,
    PresentationIntent,
    PresentationRenderSpec,
    SlideIntent,
    SlideRenderSpec,
)


# ---------------------------------------------------------------------------
# PresentationIntent tests
# ---------------------------------------------------------------------------

class TestPresentationIntentMinimal:
    """test_presentation_intent_minimal -- create with minimal fields."""

    def test_minimal_fields(self):
        intent = PresentationIntent(
            title="Q1 Review",
            context={"audience": "executives"},
            slides=[
                SlideIntent(type="title", heading="Q1 Review"),
            ],
        )
        assert intent.title == "Q1 Review"
        assert intent.context == {"audience": "executives"}
        assert len(intent.slides) == 1
        assert intent.source_analysis is None
        assert intent.user_profile_hints is None

    def test_slide_intent_minimal(self):
        slide = SlideIntent(type="text", heading="Overview")
        assert slide.type == "text"
        assert slide.heading == "Overview"
        assert slide.subheading is None
        assert slide.content is None
        assert slide.takeaway is None
        assert slide.speaker_notes is None


class TestPresentationIntentFull:
    """test_presentation_intent_full -- create with all fields including source_analysis."""

    def test_all_fields(self):
        intent = PresentationIntent(
            title="Annual Strategy",
            context={"scene": "board_meeting", "audience": "board", "tone": "formal"},
            slides=[
                SlideIntent(
                    type="title",
                    heading="Annual Strategy 2026",
                    subheading="Building the Future",
                    content={"subtitle": "Confidential"},
                    takeaway="We are on track",
                    speaker_notes="Open with confidence",
                ),
                SlideIntent(
                    type="data_driven",
                    heading="Revenue Growth",
                    content={"key_metrics": [{"label": "ARR", "value": "$120M"}]},
                    takeaway="Revenue up 35% YoY",
                ),
                SlideIntent(
                    type="comparison",
                    heading="Market Position",
                    content={"left": "Us", "right": "Competitor"},
                ),
            ],
            source_analysis={
                "file_type": "pdf",
                "page_count": 42,
                "key_topics": ["revenue", "strategy", "market"],
            },
            user_profile_hints={"preferred_style": "minimal", "brand_colors": ["#1a1a2e"]},
        )
        assert intent.title == "Annual Strategy"
        assert intent.context["tone"] == "formal"
        assert len(intent.slides) == 3
        assert intent.slides[0].speaker_notes == "Open with confidence"
        assert intent.slides[1].content["key_metrics"][0]["value"] == "$120M"
        assert intent.source_analysis["page_count"] == 42
        assert intent.user_profile_hints["preferred_style"] == "minimal"


class TestPresentationIntentSerialization:
    """test_presentation_intent_serialization -- JSON round-trip."""

    def test_json_round_trip(self):
        original = PresentationIntent(
            title="Round Trip Test",
            context={"audience": "engineers", "tone": "casual"},
            slides=[
                SlideIntent(
                    type="data_driven",
                    heading="Metrics",
                    content={"chart_data": [1, 2, 3]},
                    takeaway="Numbers are good",
                ),
            ],
            source_analysis={"source": "csv", "rows": 1000},
        )
        json_str = original.model_dump_json()
        restored = PresentationIntent.model_validate_json(json_str)
        assert restored == original

    def test_dict_round_trip(self):
        original = PresentationIntent(
            title="Dict Test",
            context={"audience": "all"},
            slides=[SlideIntent(type="title", heading="Hello")],
        )
        as_dict = original.model_dump()
        assert isinstance(as_dict, dict)
        restored = PresentationIntent.model_validate(as_dict)
        assert restored == original

    def test_json_includes_none_fields_when_excluded(self):
        """Verify model_dump(exclude_none=True) drops None fields."""
        intent = PresentationIntent(
            title="Sparse",
            context={},
            slides=[SlideIntent(type="title", heading="Hi")],
        )
        dumped = intent.model_dump(exclude_none=True)
        assert "source_analysis" not in dumped
        assert "user_profile_hints" not in dumped
        assert "subheading" not in dumped["slides"][0]


# ---------------------------------------------------------------------------
# SlideRenderSpec tests
# ---------------------------------------------------------------------------

class TestSlideRenderSpec:
    """test_slide_render_spec -- create a slide with layout."""

    def test_basic_slide(self):
        spec = SlideRenderSpec(
            slide_index=0,
            layout="title",
            heading="Welcome",
        )
        assert spec.slide_index == 0
        assert spec.layout == "title"
        assert spec.heading == "Welcome"
        assert spec.components == []
        assert spec.css_overrides is None

    def test_slide_with_components(self):
        spec = SlideRenderSpec(
            slide_index=1,
            layout="data_driven",
            heading="Key Metrics",
            subheading="Q1 2026",
            components=[
                Component(type="card_grid", props={"cards": [{"label": "ARR", "value": "120M"}]}),
                Component(type="bar_chart", props={"data": [10, 20, 30], "labels": ["A", "B", "C"]}),
            ],
            css_overrides={"--accent-color": "#ff6b35"},
            speaker_notes="Emphasize growth trajectory",
        )
        assert len(spec.components) == 2
        assert spec.components[0].type == "card_grid"
        assert spec.css_overrides["--accent-color"] == "#ff6b35"
        assert spec.speaker_notes == "Emphasize growth trajectory"


# ---------------------------------------------------------------------------
# PresentationRenderSpec tests
# ---------------------------------------------------------------------------

class TestPresentationRenderSpec:
    """test_presentation_render_spec -- create with theme, slides, components."""

    def test_full_presentation(self):
        spec = PresentationRenderSpec(
            title="Q1 Review Deck",
            theme={
                "--primary": "#1a1a2e",
                "--secondary": "#16213e",
                "--accent": "#e94560",
                "--font-heading": "Inter",
                "--font-body": "Inter",
            },
            slides=[
                SlideRenderSpec(
                    slide_index=0,
                    layout="title",
                    heading="Q1 Review",
                    subheading="Engineering Division",
                ),
                SlideRenderSpec(
                    slide_index=1,
                    layout="data_driven",
                    heading="Performance Metrics",
                    components=[
                        Component(type="highlight_box", props={"text": "35% growth", "color": "green"}),
                        Component(type="chart_js", props={"type": "line", "data": {}}),
                    ],
                ),
            ],
            metadata={"generated_at": "2026-03-30", "version": "1.0"},
        )
        assert spec.title == "Q1 Review Deck"
        assert spec.theme["--accent"] == "#e94560"
        assert len(spec.slides) == 2
        assert spec.slides[1].components[0].type == "highlight_box"
        assert spec.metadata["version"] == "1.0"

    def test_minimal_presentation(self):
        spec = PresentationRenderSpec(
            title="Minimal",
            theme={"--primary": "#000"},
            slides=[],
        )
        assert spec.title == "Minimal"
        assert spec.slides == []
        assert spec.metadata is None

    def test_serialization_round_trip(self):
        spec = PresentationRenderSpec(
            title="Serialization Test",
            theme={"--bg": "#fff"},
            slides=[
                SlideRenderSpec(
                    slide_index=0,
                    layout="full_visual",
                    heading="Visual Slide",
                    components=[
                        Component(type="image", props={"src": "hero.png", "alt": "Hero"}),
                    ],
                ),
            ],
        )
        json_str = spec.model_dump_json()
        restored = PresentationRenderSpec.model_validate_json(json_str)
        assert restored == spec


# ---------------------------------------------------------------------------
# Component types tests
# ---------------------------------------------------------------------------

class TestComponentTypes:
    """test_component_types -- verify all component types work."""

    COMPONENT_TYPES = [
        ("card_grid", {"cards": [{"label": "Revenue", "value": "$10M"}]}),
        ("highlight_box", {"text": "Key insight", "color": "blue"}),
        ("bar_chart", {"data": [10, 20, 30], "labels": ["Q1", "Q2", "Q3"]}),
        ("flow", {"steps": ["Collect", "Analyze", "Present"]}),
        ("bullet_list", {"items": ["Point A", "Point B", "Point C"]}),
        ("text_block", {"markdown": "## Hello\nSome **bold** text."}),
        ("quote_box", {"quote": "Innovation distinguishes...", "author": "Steve Jobs"}),
        ("comparison", {"left": {"title": "Before"}, "right": {"title": "After"}}),
        ("chart_js", {"type": "pie", "data": {"labels": ["A", "B"], "values": [60, 40]}}),
        ("image", {"src": "diagram.png", "alt": "Architecture diagram", "width": "100%"}),
    ]

    @pytest.mark.parametrize("comp_type,props", COMPONENT_TYPES)
    def test_component_creation(self, comp_type: str, props: dict):
        component = Component(type=comp_type, props=props)
        assert component.type == comp_type
        assert component.props == props

    @pytest.mark.parametrize("comp_type,props", COMPONENT_TYPES)
    def test_component_serialization(self, comp_type: str, props: dict):
        component = Component(type=comp_type, props=props)
        json_str = component.model_dump_json()
        restored = Component.model_validate_json(json_str)
        assert restored == component

    def test_all_component_types_in_slide(self):
        """Verify a slide can hold all component types simultaneously."""
        components = [
            Component(type=comp_type, props=props)
            for comp_type, props in self.COMPONENT_TYPES
        ]
        spec = SlideRenderSpec(
            slide_index=0,
            layout="full_visual",
            heading="All Components",
            components=components,
        )
        assert len(spec.components) == len(self.COMPONENT_TYPES)
        types_in_spec = {c.type for c in spec.components}
        expected_types = {ct for ct, _ in self.COMPONENT_TYPES}
        assert types_in_spec == expected_types
