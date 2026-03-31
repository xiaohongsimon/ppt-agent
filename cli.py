"""PPT-Agent CLI -- generate presentations from the command line."""
import argparse
import asyncio
from pathlib import Path

from backend.config import settings
from backend.input_parser.text_parser import parse_text
from backend.input_parser.pptx_parser import parse_pptx
from backend.agent.engine import generate_render_spec
from backend.renderer.html_renderer import render_presentation
from backend.quality_gate.gate import run_quality_gate


async def main():
    parser = argparse.ArgumentParser(description="PPT-Agent: AI Presentation Generator")
    parser.add_argument("input", help="Text content or path to .pptx file")
    parser.add_argument("-o", "--output", default="./output", help="Output directory")
    parser.add_argument("--scene", help="Scene hint (e.g., quarterly_review)")
    parser.add_argument("--audience", help="Audience hint (e.g., VP Engineering)")
    parser.add_argument("--pdf", action="store_true", help="Also export PDF")
    parser.add_argument(
        "--skip-vlm", action="store_true", default=True, help="Skip VLM quality check"
    )
    args = parser.parse_args()

    output_dir = Path(args.output)
    input_path = Path(args.input)

    if input_path.exists() and input_path.suffix == ".pptx":
        print(f"Parsing PPTX: {input_path}")
        pptx_data = parse_pptx(input_path)
        text_summary = f"Title: {pptx_data['title']}\n"
        for slide in pptx_data["slides"]:
            text_summary += (
                f"\nSlide {slide['index'] + 1}: {slide['title']}\n{slide['text_content']}\n"
            )
        intent = await parse_text(text_summary, scene=args.scene, audience=args.audience)
    else:
        print("Parsing text input...")
        intent = await parse_text(args.input, scene=args.scene, audience=args.audience)

    print(f"Intent: {intent.title} ({len(intent.slides)} slides)")

    print("Generating presentation design...")
    render_spec = await generate_render_spec(intent)

    print("Running quality checks...")
    qg_result = run_quality_gate(render_spec, skip_vlm=args.skip_vlm)
    final_spec = qg_result.fixed_spec or render_spec
    if qg_result.tier1_passed:
        print(f"Quality Gate: PASSED (auto-fixed {qg_result.auto_fix_rounds} rounds)")
    else:
        print("Quality Gate: ISSUES REMAIN")
        for issue in qg_result.tier1_result.issues if qg_result.tier1_result else []:
            print(f"  - {issue}")

    html_dir = render_presentation(final_spec, output_dir / "html")
    print(f"HTML output: {html_dir}/index.html")

    if args.pdf:
        from backend.renderer.pdf_exporter import export_pdf

        pdf_path = output_dir / "presentation.pdf"
        print("Exporting PDF...")
        await export_pdf(html_dir, pdf_path)
        print(f"PDF output: {pdf_path}")

    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
