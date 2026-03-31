"""Stepped training mode — works inside Claude Code without external API.

Splits the training loop into offline (Python) and online (Claude in CC) steps:
- Offline: corpus loading, rendering, screenshotting — no LLM needed
- Online: content generation, comparison, prompt optimization — Claude does it in-session

Usage:
  python train.py --step prepare     # Offline: PPTX → screenshots + text extraction
  python train.py --step render      # Offline: render specs → HTML → screenshots
  python train.py --step report      # Offline: generate comparison report from scores
"""

import json
from pathlib import Path

from backend.trainer.corpus import CorpusItem, load_corpus
from backend.quality_gate.gate import run_quality_gate
from backend.renderer.html_renderer import render_presentation
from backend.schemas.render_spec import PresentationRenderSpec


STEP_DIR = Path("./training_runs/current")


def step_prepare(corpus_dir: Path) -> dict:
    """Step 1 (offline): Load corpus, extract text, generate screenshots.

    Returns summary dict for Claude to use in the next step.
    """
    corpus = load_corpus(corpus_dir)
    STEP_DIR.mkdir(parents=True, exist_ok=True)

    items_data = []
    for i, item in enumerate(corpus):
        item_dir = STEP_DIR / f"item-{i:03d}"
        item_dir.mkdir(parents=True, exist_ok=True)

        # Save text summary for Claude to use
        (item_dir / "text_summary.txt").write_text(item.text_summary, encoding="utf-8")

        # Save metadata
        meta = {
            "index": i,
            "filename": item.pptx_path.name,
            "slide_count": item.metadata.get("slide_count", 0),
            "original_screenshots": [str(p) for p in item.original_screenshots],
            "text_summary_path": str(item_dir / "text_summary.txt"),
            "spec_path": str(item_dir / "spec.json"),  # Claude writes this
        }
        (item_dir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        items_data.append(meta)

    # Save run manifest
    manifest = {"corpus_dir": str(corpus_dir), "item_count": len(items_data), "items": items_data}
    (STEP_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\nPrepared {len(corpus)} items in {STEP_DIR}")
    print(f"Manifest: {STEP_DIR / 'manifest.json'}")
    print(f"\nNext: Claude generates spec.json for each item (see /ppt-train skill)")
    return manifest


def step_render() -> dict:
    """Step 3 (offline): Render all spec.json → HTML → screenshots.

    Runs after Claude has generated spec.json for each item.
    Returns paths to generated screenshots for comparison.
    """
    import asyncio
    from backend.renderer.pdf_exporter import export_pdf

    manifest_path = STEP_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    results = []
    for item_meta in manifest["items"]:
        item_dir = Path(item_meta["spec_path"]).parent
        spec_path = Path(item_meta["spec_path"])

        if not spec_path.exists():
            print(f"  SKIP {item_meta['filename']}: no spec.json (Claude hasn't generated it yet)")
            continue

        print(f"  Rendering {item_meta['filename']}...")
        spec_data = json.loads(spec_path.read_text(encoding="utf-8"))
        spec = PresentationRenderSpec.model_validate(spec_data)

        # Quality Gate
        qg = run_quality_gate(spec, skip_vlm=True)
        final = qg.fixed_spec or spec

        # Render HTML
        html_dir = render_presentation(final, item_dir / "html")

        # Screenshots
        screenshots_dir = item_dir / "gen_screenshots"
        screenshots = asyncio.run(export_pdf(
            html_dir, item_dir / "generated.pdf", screenshots_dir=screenshots_dir,
        ))

        result = {
            "index": item_meta["index"],
            "filename": item_meta["filename"],
            "html_dir": str(html_dir),
            "generated_screenshots": screenshots,
            "original_screenshots": item_meta["original_screenshots"],
            "qg_passed": qg.tier1_passed,
            "qg_rounds": qg.auto_fix_rounds,
        }
        results.append(result)

        # Save for Claude to compare
        (item_dir / "render_result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        print(f"    → {len(screenshots)} slides, QG: {'PASS' if qg.tier1_passed else 'FAIL'}")

    # Update manifest
    manifest["render_results"] = results
    (STEP_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\nRendered {len(results)}/{manifest['item_count']} items")
    print(f"Next: Claude compares original vs generated screenshots (see /ppt-train skill)")
    return manifest


def step_report() -> Path:
    """Step 5 (offline): Generate training report from scores.

    Runs after Claude has written comparison scores.
    """
    from backend.trainer.feedback import aggregate_feedback
    from backend.trainer.comparator import ComparisonResult
    from backend.trainer.report import generate_round_report
    from backend.trainer.optimizer import PromptVersion, load_history, save_history

    manifest = json.loads((STEP_DIR / "manifest.json").read_text(encoding="utf-8"))

    # Load comparison results
    comparisons = []
    for item_meta in manifest["items"]:
        item_dir = Path(item_meta["spec_path"]).parent
        score_path = item_dir / "comparison.json"
        if score_path.exists():
            data = json.loads(score_path.read_text(encoding="utf-8"))
            comparisons.append(ComparisonResult(**data))

    if not comparisons:
        print("No comparison results found. Claude needs to score the items first.")
        return STEP_DIR

    # Aggregate feedback
    feedback = aggregate_feedback(comparisons)

    # Load history
    history_path = STEP_DIR.parent / "history.json"
    history = load_history(history_path)
    round_num = len(history) + 1

    version = PromptVersion(
        version=round_num,
        prompt="(see prompt.txt in round dir)",
        avg_score=feedback.avg_score,
        dimension_scores=feedback.dimension_averages,
        changes_from_previous=["(CC-mode training)"],
    )
    history.append(version)
    save_history(history, history_path)

    # Generate report
    report_path = generate_round_report(
        round_num, comparisons, feedback, None, history, STEP_DIR,
    )

    # Save feedback summary for Claude to use in prompt optimization
    feedback_summary = {
        "avg_score": feedback.avg_score,
        "dimension_averages": feedback.dimension_averages,
        "worst_dimensions": feedback.worst_dimensions,
        "recurring_issues": feedback.recurring_issues,
        "recurring_strengths": feedback.recurring_strengths,
        "prompt_hints": feedback.prompt_hints,
        "critical_issues": feedback.all_critical_issues,
        "improvement_suggestions": feedback.all_improvement_suggestions,
    }
    feedback_path = STEP_DIR / "feedback_summary.json"
    feedback_path.write_text(json.dumps(feedback_summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nTraining Report: {report_path}")
    print(f"Average Score: {feedback.avg_score:.1f}/10")
    print(f"Feedback Summary: {feedback_path}")
    print(f"\nNext: Claude reads feedback_summary.json and optimizes backend/agent/prompts.py")
    return report_path
