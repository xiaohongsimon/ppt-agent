"""REST API routes for PPT-Agent."""
import uuid
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from backend.config import settings
from backend.input_parser.text_parser import parse_text
from backend.agent.engine import generate_render_spec
from backend.renderer.html_renderer import render_presentation
from backend.quality_gate.gate import run_quality_gate

router = APIRouter(prefix="/api/v1")


class GenerateRequest(BaseModel):
    input_type: str  # "text" or "pptx"
    content: str
    scene: str | None = None
    audience: str | None = None


class GenerateResponse(BaseModel):
    presentation_id: str
    html_path: str
    quality_gate: dict
    slides_count: int


@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    pres_id = str(uuid.uuid4())[:8]
    output_dir = Path(settings.output_dir) / pres_id

    # Step 1: Parse input
    intent = await parse_text(req.content, scene=req.scene, audience=req.audience)

    # Step 2: Agent -> RenderSpec
    render_spec = await generate_render_spec(intent)

    # Step 3: Quality Gate (Tier 1 only for speed)
    qg_result = run_quality_gate(render_spec, skip_vlm=True)
    final_spec = qg_result.fixed_spec or render_spec

    # Step 4: Render HTML
    html_dir = render_presentation(final_spec, output_dir / "html")

    return GenerateResponse(
        presentation_id=pres_id,
        html_path=str(html_dir),
        quality_gate={
            "tier1_passed": qg_result.tier1_passed,
            "auto_fix_rounds": qg_result.auto_fix_rounds,
            "issues": qg_result.tier1_result.issues if qg_result.tier1_result else [],
        },
        slides_count=len(final_spec.slides),
    )
