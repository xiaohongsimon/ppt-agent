"""Tests for PDF export via Playwright."""
import tempfile
from pathlib import Path

import pytest

from backend.renderer.html_renderer import render_presentation
from backend.renderer.pdf_exporter import export_pdf
from backend.schemas.render_spec import (
    Component,
    PresentationRenderSpec,
    SlideRenderSpec,
)


def _make_spec() -> PresentationRenderSpec:
    """Build a 2-slide PresentationRenderSpec for testing."""
    return PresentationRenderSpec(
        title="PDF Export Test",
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
                heading="Title Slide",
                subheading="Testing PDF Export",
            ),
            SlideRenderSpec(
                slide_index=1,
                layout="data_driven",
                heading="Data Slide",
                components=[
                    Component(
                        type="card_grid",
                        props={
                            "columns": 2,
                            "cards": [
                                {"title": "Metric A", "value": "100", "change": "+10%"},
                                {"title": "Metric B", "value": "200", "change": "+20%"},
                            ],
                        },
                    ),
                    Component(
                        type="highlight_box",
                        props={
                            "text": "All systems operational",
                            "color": "green",
                        },
                    ),
                ],
            ),
        ],
    )


@pytest.mark.asyncio
async def test_export_pdf_creates_file():
    """Render HTML, export PDF, assert PDF exists and size > 0."""
    spec = _make_spec()
    with tempfile.TemporaryDirectory() as tmpdir:
        html_dir = Path(tmpdir) / "html"
        render_presentation(spec, html_dir)

        pdf_path = Path(tmpdir) / "output.pdf"
        await export_pdf(html_dir, pdf_path)

        assert pdf_path.is_file()
        assert pdf_path.stat().st_size > 0


@pytest.mark.asyncio
async def test_export_pdf_screenshots():
    """Render HTML, export PDF with screenshots_dir, assert 2 screenshots exist."""
    spec = _make_spec()
    with tempfile.TemporaryDirectory() as tmpdir:
        html_dir = Path(tmpdir) / "html"
        render_presentation(spec, html_dir)

        pdf_path = Path(tmpdir) / "output.pdf"
        ss_dir = Path(tmpdir) / "screenshots"
        screenshot_paths = await export_pdf(html_dir, pdf_path, screenshots_dir=ss_dir)

        assert len(screenshot_paths) == 2
        for ss_path in screenshot_paths:
            p = Path(ss_path)
            assert p.is_file()
            assert p.stat().st_size > 0
