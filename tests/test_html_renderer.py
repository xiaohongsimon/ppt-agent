"""Tests for the HTML renderer engine."""
import tempfile
from pathlib import Path

from backend.schemas.render_spec import (
    Component,
    PresentationRenderSpec,
    SlideRenderSpec,
)
from backend.renderer.html_renderer import render_presentation


def _make_spec() -> PresentationRenderSpec:
    """Build a 2-slide PresentationRenderSpec for testing."""
    return PresentationRenderSpec(
        title="Test Presentation",
        theme={
            "accent_primary": "#4f6df5",
            "accent_secondary": "#7c3aed",
            "accent_green": "#10b981",
            "heading_color": "#1a202c",
            "text_color": "#2d3748",
        },
        slides=[
            SlideRenderSpec(
                slide_index=0,
                layout="title",
                heading="Welcome",
                subheading="PPT-Agent Demo",
            ),
            SlideRenderSpec(
                slide_index=1,
                layout="data_driven",
                heading="Key Metrics",
                components=[
                    Component(
                        type="card_grid",
                        props={
                            "columns": 3,
                            "cards": [
                                {"title": "Users", "value": "10K", "change": "+25%"},
                                {"title": "Revenue", "value": "$1M", "change": "+30%"},
                                {"title": "NPS", "value": "72", "change": "+5"},
                            ],
                        },
                    ),
                    Component(
                        type="highlight_box",
                        props={
                            "text": "All metrics trending up",
                            "color": "green",
                        },
                    ),
                ],
            ),
        ],
    )


class TestRenderCreatesOutputDir:
    """test_render_creates_output_dir -- renders and checks output files exist."""

    def test_index_html_exists(self):
        spec = _make_spec()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = render_presentation(spec, Path(tmpdir) / "output")
            assert (out / "index.html").is_file()

    def test_style_css_exists(self):
        spec = _make_spec()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = render_presentation(spec, Path(tmpdir) / "output")
            assert (out / "style.css").is_file()

    def test_slides_js_exists(self):
        spec = _make_spec()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = render_presentation(spec, Path(tmpdir) / "output")
            assert (out / "slides.js").is_file()

    def test_output_dir_created(self):
        spec = _make_spec()
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "nested" / "output"
            out = render_presentation(spec, target)
            assert out.is_dir()
            assert out == target


class TestRenderHtmlContainsSlides:
    """test_render_html_contains_slides -- checks HTML contains expected content."""

    def test_contains_headings(self):
        spec = _make_spec()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = render_presentation(spec, Path(tmpdir) / "output")
            html = (out / "index.html").read_text(encoding="utf-8")
            assert "Welcome" in html
            assert "Key Metrics" in html

    def test_contains_subheading(self):
        spec = _make_spec()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = render_presentation(spec, Path(tmpdir) / "output")
            html = (out / "index.html").read_text(encoding="utf-8")
            assert "PPT-Agent Demo" in html

    def test_contains_slide_ids(self):
        spec = _make_spec()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = render_presentation(spec, Path(tmpdir) / "output")
            html = (out / "index.html").read_text(encoding="utf-8")
            assert 'id="slide-0"' in html
            assert 'id="slide-1"' in html

    def test_contains_card_content(self):
        spec = _make_spec()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = render_presentation(spec, Path(tmpdir) / "output")
            html = (out / "index.html").read_text(encoding="utf-8")
            assert "10K" in html
            assert "$1M" in html
            assert "72" in html
            assert "+25%" in html
            assert "+30%" in html

    def test_contains_highlight_box(self):
        spec = _make_spec()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = render_presentation(spec, Path(tmpdir) / "output")
            html = (out / "index.html").read_text(encoding="utf-8")
            assert "All metrics trending up" in html
            assert "highlight-box" in html

    def test_contains_card_grid(self):
        spec = _make_spec()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = render_presentation(spec, Path(tmpdir) / "output")
            html = (out / "index.html").read_text(encoding="utf-8")
            assert "card-grid" in html


class TestRenderThemeApplied:
    """test_render_theme_applied -- checks theme CSS variables appear in output HTML."""

    def test_theme_css_variables_in_html(self):
        spec = _make_spec()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = render_presentation(spec, Path(tmpdir) / "output")
            html = (out / "index.html").read_text(encoding="utf-8")
            # The Jinja2 template replaces underscores with hyphens for CSS variables
            assert "--accent-primary" in html
            assert "#4f6df5" in html
            assert "--accent-secondary" in html
            assert "#7c3aed" in html

    def test_all_theme_vars_present(self):
        spec = _make_spec()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = render_presentation(spec, Path(tmpdir) / "output")
            html = (out / "index.html").read_text(encoding="utf-8")
            for key, value in spec.theme.items():
                css_var = "--" + key.replace("_", "-")
                assert css_var in html, f"Missing CSS variable {css_var}"
                assert value in html, f"Missing theme value {value}"

    def test_title_in_head(self):
        spec = _make_spec()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = render_presentation(spec, Path(tmpdir) / "output")
            html = (out / "index.html").read_text(encoding="utf-8")
            assert "<title>Test Presentation</title>" in html
