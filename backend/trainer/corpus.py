"""Load PPTX corpus and convert to screenshots + structured data."""

import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from backend.input_parser.pptx_parser import parse_pptx


@dataclass
class CorpusItem:
    pptx_path: Path
    parsed_data: dict
    original_screenshots: list[Path] = field(default_factory=list)
    text_summary: str = ""
    metadata: dict = field(default_factory=dict)


def _pptx_to_pdf(pptx_path: Path, output_dir: Path) -> Path:
    """Convert PPTX to PDF via LibreOffice headless."""
    subprocess.run(
        [
            "soffice",
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(output_dir),
            str(pptx_path),
        ],
        check=True,
        capture_output=True,
        timeout=120,
    )
    return output_dir / f"{pptx_path.stem}.pdf"


async def _pdf_to_screenshots(pdf_path: Path, output_dir: Path) -> list[Path]:
    """Convert PDF pages to PNG screenshots via Playwright."""
    from playwright.async_api import async_playwright

    screenshots = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})

        await page.goto(f"file://{pdf_path.resolve()}")
        await page.wait_for_load_state("networkidle")

        # PDF viewer renders pages — take full page screenshot and split
        # Simpler: use pdf2image or just screenshot full page
        ss_path = output_dir / "full.png"
        await page.screenshot(path=str(ss_path), full_page=True)
        screenshots.append(ss_path)

        await browser.close()

    return screenshots


def _pptx_to_images_via_libreoffice(pptx_path: Path, output_dir: Path) -> list[Path]:
    """Convert PPTX directly to images via LibreOffice (one image per slide)."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # First convert to PDF
    pdf_path = _pptx_to_pdf(pptx_path, output_dir)

    # Then use sips/ImageMagick/poppler to split PDF into images
    # Using poppler's pdftoppm which is common on macOS (brew install poppler)
    try:
        subprocess.run(
            [
                "pdftoppm",
                "-png",
                "-r", "192",  # 192 DPI for good quality
                str(pdf_path),
                str(output_dir / "slide"),
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )
    except FileNotFoundError:
        # Fallback: try sips on macOS
        subprocess.run(
            [
                "sips",
                "-s", "format", "png",
                str(pdf_path),
                "--out", str(output_dir / "slide-1.png"),
            ],
            check=True,
            capture_output=True,
            timeout=60,
        )

    # Collect generated PNGs
    screenshots = sorted(output_dir.glob("slide-*.png"))
    return screenshots


def _build_text_summary(parsed_data: dict) -> str:
    """Build a text summary from parsed PPTX data."""
    parts = [f"Title: {parsed_data['title']}"]
    for slide in parsed_data["slides"]:
        parts.append(f"\nSlide {slide['index'] + 1}: {slide['title']}")
        if slide["text_content"]:
            parts.append(slide["text_content"])
        if slide["speaker_notes"]:
            parts.append(f"[Speaker notes: {slide['speaker_notes']}]")
    return "\n".join(parts)


def load_corpus(corpus_dir: Path) -> list[CorpusItem]:
    """Load all PPTX files from corpus directory.

    Args:
        corpus_dir: Directory containing .pptx files.

    Returns:
        List of CorpusItem with parsed data and screenshots.
    """
    corpus_dir = Path(corpus_dir)
    items = []

    for pptx_path in sorted(corpus_dir.glob("*.pptx")):
        print(f"  Loading: {pptx_path.name}")

        # Parse content
        parsed = parse_pptx(pptx_path)

        # Convert to screenshots
        screenshot_dir = corpus_dir / ".screenshots" / pptx_path.stem
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        # Check if screenshots already exist (cache)
        existing = sorted(screenshot_dir.glob("slide-*.png"))
        if existing:
            screenshots = existing
        else:
            try:
                screenshots = _pptx_to_images_via_libreoffice(pptx_path, screenshot_dir)
            except Exception as e:
                print(f"    Warning: screenshot conversion failed: {e}")
                screenshots = []

        item = CorpusItem(
            pptx_path=pptx_path,
            parsed_data=parsed,
            original_screenshots=screenshots,
            text_summary=_build_text_summary(parsed),
            metadata={
                "slide_count": parsed["slide_count"],
                "has_charts": any(s.get("has_chart") for s in parsed["slides"]),
                "has_images": any(s.get("has_image") for s in parsed["slides"]),
            },
        )
        items.append(item)
        print(f"    {parsed['slide_count']} slides, {len(screenshots)} screenshots")

    return items
