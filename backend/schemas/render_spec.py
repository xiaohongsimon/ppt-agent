"""IR Output: Render-ready specification (from Agent Engine -> HTML Renderer)."""
from pydantic import BaseModel


class Component(BaseModel):
    """A visual component within a slide."""
    type: str  # card_grid, highlight_box, bar_chart, flow, bullet_list, etc.
    props: dict  # Type-specific properties


class SlideRenderSpec(BaseModel):
    """Render specification for a single slide."""
    slide_index: int
    layout: str  # "title", "data_driven", "split_panel", "full_visual", "comparison"
    heading: str
    subheading: str | None = None
    components: list[Component] = []
    css_overrides: dict | None = None
    speaker_notes: str | None = None


class PresentationRenderSpec(BaseModel):
    """Complete render specification -- the contract from Agent Engine to HTML Renderer."""
    title: str
    theme: dict  # CSS variable values
    slides: list[SlideRenderSpec]
    metadata: dict | None = None
