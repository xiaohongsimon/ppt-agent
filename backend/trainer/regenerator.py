"""Regenerate presentations using our pipeline, for comparison with originals."""

from dataclasses import dataclass, field
from pathlib import Path

from backend.agent.engine import generate_render_spec
from backend.input_parser.text_parser import parse_text
from backend.quality_gate.gate import QualityGateResult, run_quality_gate
from backend.renderer.html_renderer import render_presentation
from backend.renderer.pdf_exporter import export_pdf
from backend.schemas.render_spec import PresentationRenderSpec
from backend.trainer.corpus import CorpusItem


@dataclass
class RegenResult:
    render_spec: PresentationRenderSpec
    html_dir: Path
    screenshots: list[Path] = field(default_factory=list)
    qg_result: QualityGateResult | None = None


async def regenerate(item: CorpusItem, output_dir: Path) -> RegenResult:
    """Regenerate a presentation from corpus item using our pipeline.

    Args:
        item: The corpus item (original PPT data).
        output_dir: Where to write generated output.

    Returns:
        RegenResult with render spec, HTML dir, screenshots, and QA result.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Parse extracted text → PresentationIntent
    intent = await parse_text(item.text_summary)

    # Step 2: Intent → RenderSpec
    render_spec = await generate_render_spec(intent)

    # Step 3: Quality Gate (Tier 1 only — fast, no VLM cost)
    qg_result = run_quality_gate(render_spec, skip_vlm=True)
    final_spec = qg_result.fixed_spec or render_spec

    # Step 4: Render HTML
    html_dir = render_presentation(final_spec, output_dir / "html")

    # Step 5: Screenshot generated slides
    screenshots_dir = output_dir / "screenshots"
    screenshots = await export_pdf(
        html_dir,
        output_dir / "generated.pdf",
        screenshots_dir=screenshots_dir,
    )

    return RegenResult(
        render_spec=final_spec,
        html_dir=html_dir,
        screenshots=[Path(s) for s in screenshots],
        qg_result=qg_result,
    )
