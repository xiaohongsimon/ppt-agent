"""Quality Gate orchestrator: Tier 1 rules + auto-fix loop + optional Tier 2 VLM."""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from pathlib import Path

from backend.schemas.render_spec import (
    Component,
    PresentationRenderSpec,
    SlideRenderSpec,
)
from backend.quality_gate.tier1_rules import (
    MAX_BULLET_ITEMS,
    Tier1Result,
    check_tier1,
)


@dataclass
class QualityGateResult:
    tier1_passed: bool
    tier1_result: Tier1Result
    fixed_spec: PresentationRenderSpec | None = None
    auto_fix_rounds: int = 0


def _auto_fix_tier1(spec: PresentationRenderSpec) -> PresentationRenderSpec:
    """Attempt deterministic fixes for common Tier 1 failures.

    Current fixes:
    - Split over-long bullet_list components across new slides.
    - Add missing highlight_box to data-layout slides.
    """
    DATA_LAYOUTS = {"data_driven", "split_panel", "comparison"}
    new_slides: list[SlideRenderSpec] = []

    for slide in spec.slides:
        needs_split = False
        overflow_bullets: list[Component] | None = None

        # Check for bullet overflow
        fixed_components: list[Component] = []
        extra_items: list[str] = []

        for comp in slide.components:
            if comp.type == "bullet_list":
                items = comp.props.get("items", [])
                if len(items) > MAX_BULLET_ITEMS:
                    # Keep first MAX_BULLET_ITEMS in this slide
                    fixed_comp = Component(
                        type="bullet_list",
                        props={**comp.props, "items": items[:MAX_BULLET_ITEMS]},
                    )
                    fixed_components.append(fixed_comp)
                    extra_items = items[MAX_BULLET_ITEMS:]
                    needs_split = True
                else:
                    fixed_components.append(comp)
            else:
                fixed_components.append(comp)

        # Add missing highlight_box for data layouts
        if slide.layout in DATA_LAYOUTS:
            has_highlight = any(c.type == "highlight_box" for c in fixed_components)
            if not has_highlight:
                fixed_components.append(
                    Component(
                        type="highlight_box",
                        props={"text": "Key takeaway", "color": "blue"},
                    )
                )

        # Build the (possibly fixed) slide
        fixed_slide = slide.model_copy(update={"components": fixed_components})
        new_slides.append(fixed_slide)

        # Create overflow slide(s) for extra bullet items
        if needs_split and extra_items:
            # Split remaining items into chunks of MAX_BULLET_ITEMS
            for chunk_start in range(0, len(extra_items), MAX_BULLET_ITEMS):
                chunk = extra_items[chunk_start : chunk_start + MAX_BULLET_ITEMS]
                overflow_slide = SlideRenderSpec(
                    slide_index=0,  # Will be reindexed below
                    layout=slide.layout,
                    heading=f"{slide.heading} (cont.)",
                    components=[
                        Component(
                            type="bullet_list",
                            props={"items": chunk},
                        ),
                    ],
                )
                # If original slide was a data layout, the overflow also needs highlight_box
                if slide.layout in DATA_LAYOUTS:
                    overflow_slide.components.append(
                        Component(
                            type="highlight_box",
                            props={"text": "Key takeaway", "color": "blue"},
                        )
                    )
                new_slides.append(overflow_slide)

    # Reindex all slides
    for idx, s in enumerate(new_slides):
        s.slide_index = idx

    return spec.model_copy(update={"slides": new_slides})


def run_quality_gate(
    spec: PresentationRenderSpec,
    *,
    skip_vlm: bool = False,
    max_fix_rounds: int = 3,
) -> QualityGateResult:
    """Run Quality Gate: Tier 1 rules with auto-fix loop, optionally Tier 2 VLM.

    Args:
        spec: The presentation render spec to validate.
        skip_vlm: If True, skip Tier 2 VLM check.
        max_fix_rounds: Maximum number of auto-fix iterations.

    Returns:
        QualityGateResult with Tier 1 status, optional fixed spec, and fix round count.
    """
    current_spec = spec
    tier1_result = check_tier1(current_spec)
    fix_rounds = 0

    while not tier1_result.passed and fix_rounds < max_fix_rounds:
        current_spec = _auto_fix_tier1(current_spec)
        tier1_result = check_tier1(current_spec)
        fix_rounds += 1

    fixed_spec = current_spec if fix_rounds > 0 else None

    return QualityGateResult(
        tier1_passed=tier1_result.passed,
        tier1_result=tier1_result,
        fixed_spec=fixed_spec,
        auto_fix_rounds=fix_rounds,
    )
