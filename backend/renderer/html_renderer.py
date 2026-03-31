"""Render a PresentationRenderSpec to standalone HTML files."""
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from backend.schemas.render_spec import PresentationRenderSpec

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_STATIC_DIR = Path(__file__).parent / "static"


def _get_jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=False,
    )


def render_presentation(spec: PresentationRenderSpec, output_dir: Path) -> Path:
    """Render a PresentationRenderSpec to a directory of HTML files.

    Args:
        spec: The render specification.
        output_dir: Directory to write output files.

    Returns:
        Path to the output directory.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy static assets
    for static_file in ["style.css", "slides.js"]:
        src = _STATIC_DIR / static_file
        if src.exists():
            shutil.copy2(src, output_dir / static_file)

    # Render index.html
    env = _get_jinja_env()
    template = env.get_template("index.html.j2")
    html = template.render(
        title=spec.title,
        theme=spec.theme,
        slides=spec.slides,
    )
    (output_dir / "index.html").write_text(html, encoding="utf-8")
    return output_dir
