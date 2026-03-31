"""Export HTML presentations to PDF via Playwright."""
from pathlib import Path

from playwright.async_api import async_playwright


async def export_pdf(
    html_dir: Path,
    output_pdf: Path,
    screenshots_dir: Path | None = None,
) -> list[str]:
    """Export an HTML presentation to PDF.

    Takes per-slide screenshots and combines into a single PDF.

    Returns list of screenshot file paths (for Quality Gate Tier 2).
    """
    html_dir = Path(html_dir)
    output_pdf = Path(output_pdf)
    index_path = html_dir / "index.html"

    if screenshots_dir:
        screenshots_dir = Path(screenshots_dir)
        screenshots_dir.mkdir(parents=True, exist_ok=True)

    screenshot_paths: list[str] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        await page.goto(f"file://{index_path.resolve()}")
        await page.wait_for_load_state("networkidle")

        slide_count = await page.locator(".slide").count()

        for i in range(slide_count):
            slide = page.locator(f"#slide-{i}")
            if await slide.count() == 0:
                slide = page.locator(f".slide:nth-child({i + 1})")
            if screenshots_dir and await slide.count() > 0:
                ss_path = screenshots_dir / f"slide-{i}.png"
                await slide.screenshot(path=str(ss_path))
                screenshot_paths.append(str(ss_path))

        await page.pdf(
            path=str(output_pdf),
            format="A4",
            landscape=True,
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        await browser.close()

    return screenshot_paths
