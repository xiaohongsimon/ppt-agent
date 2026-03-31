"""Tier 1 Quality Gate: deterministic rule-based checks on PresentationRenderSpec."""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.schemas.render_spec import PresentationRenderSpec, SlideRenderSpec

MAX_BULLET_ITEMS = 7
MAX_CARDS = 5
DATA_LAYOUTS = {"data_driven", "split_panel", "comparison"}

MIN_SLIDES = 2
MAX_SLIDES = 25


@dataclass
class Tier1Result:
    passed: bool
    issues: list[str] = field(default_factory=list)
    slide_issues: dict[int, list[str]] = field(default_factory=dict)


def _check_slide(slide: SlideRenderSpec) -> list[str]:
    """Run rule checks on a single slide and return a list of issue strings."""
    issues: list[str] = []

    for comp in slide.components:
        # Bullet list item count
        if comp.type == "bullet_list":
            items = comp.props.get("items", [])
            if len(items) > MAX_BULLET_ITEMS:
                issues.append(
                    f"bullet_list has {len(items)} items (max {MAX_BULLET_ITEMS})"
                )

        # Card grid card count
        if comp.type == "card_grid":
            cards = comp.props.get("cards", [])
            if len(cards) > MAX_CARDS:
                issues.append(
                    f"card_grid has {len(cards)} cards (max {MAX_CARDS})"
                )

    # Data layouts must have a highlight_box (takeaway)
    if slide.layout in DATA_LAYOUTS:
        has_highlight = any(c.type == "highlight_box" for c in slide.components)
        if not has_highlight:
            issues.append(
                f"layout '{slide.layout}' requires a highlight_box component"
            )

    # Non-title slides must have at least one component
    if slide.layout != "title" and len(slide.components) == 0:
        issues.append("non-title slide has no components")

    return issues


def check_tier1(spec: PresentationRenderSpec) -> Tier1Result:
    """Run all Tier 1 checks on a PresentationRenderSpec."""
    all_issues: list[str] = []
    slide_issues: dict[int, list[str]] = {}

    # Slide count range
    slide_count = len(spec.slides)
    if slide_count < MIN_SLIDES:
        all_issues.append(f"too few slides: {slide_count} (min {MIN_SLIDES})")
    if slide_count > MAX_SLIDES:
        all_issues.append(f"too many slides: {slide_count} (max {MAX_SLIDES})")

    # Per-slide checks
    for slide in spec.slides:
        issues = _check_slide(slide)
        if issues:
            slide_issues[slide.slide_index] = issues
            all_issues.extend(
                f"slide {slide.slide_index}: {issue}" for issue in issues
            )

    return Tier1Result(
        passed=len(all_issues) == 0,
        issues=all_issues,
        slide_issues=slide_issues,
    )
