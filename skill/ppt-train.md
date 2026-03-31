---
name: ppt-train
description: Run self-improvement training loop for PPT-Agent within Claude Code. No API key needed. Use when user says "训练", "train", "improve prompts", "/ppt-train".
user_invocable: true
---

# PPT-Agent Training Skill (Claude Code Mode)

Train the PPT generation system using excellent PPT samples — all within Claude Code, zero external API cost.

## Prerequisites

- PPTX files in `backend/trainer/data/corpus/`
- `brew install poppler libreoffice` (for PPTX → screenshot conversion)

## The 5-Step Loop

Each training round has 5 steps. Steps 1, 3, 5 are Python (offline). Steps 2, 4 are YOU (Claude).

### Step 1: Prepare corpus (Python, offline)

```bash
cd /Users/leehom/work/ppt-agent
uv run python train.py --step prepare --corpus ./backend/trainer/data/corpus
```

This extracts text + generates screenshots from each PPTX. No LLM needed.

### Step 2: Generate RenderSpec for each item (YOU, Claude)

Read the manifest to see what needs generating:

```bash
cat ./training_runs/current/manifest.json
```

For each item, read the text summary:

```bash
cat ./training_runs/current/item-000/text_summary.txt
```

Then generate a `spec.json` following the PresentationRenderSpec schema (same as /ppt skill).
Write it to `./training_runs/current/item-000/spec.json`.

Repeat for all items.

### Step 3: Render and screenshot (Python, offline)

```bash
uv run python train.py --step render
```

This renders each spec.json → HTML → screenshots. No LLM needed.

### Step 4: Compare original vs generated (YOU, Claude)

For each item, READ the original screenshots and generated screenshots:

- Original: paths in `./training_runs/current/item-000/meta.json` → `original_screenshots`
- Generated: paths in `./training_runs/current/item-000/render_result.json` → `generated_screenshots`

Use the Read tool to view both sets of images. Then write a comparison score:

```json
// Write to ./training_runs/current/item-000/comparison.json
{
  "overall_score": 7.5,
  "dimensions": {
    "visual_fidelity": 7.0,
    "content_accuracy": 8.0,
    "design_quality": 7.5,
    "information_clarity": 7.5
  },
  "what_original_does_better": ["better whitespace", "more professional typography"],
  "what_generated_does_better": ["cleaner data visualization", "better color consistency"],
  "improvement_suggestions": ["increase whitespace between sections", "use larger heading fonts"],
  "critical_issues": []
}
```

### Step 5: Generate report + optimize prompt (Python + YOU)

```bash
uv run python train.py --step report
```

Then read the feedback:

```bash
cat ./training_runs/current/feedback_summary.json
```

Based on the feedback, read and improve `backend/agent/prompts.py`:
- Add rules that address recurring issues
- Strengthen instructions for weak dimensions
- Remove rules that aren't helping

Commit the improved prompt, then start the next round from Step 1.

## Quick Reference

```bash
# Full round in Claude Code:
uv run python train.py --step prepare       # 1. Extract corpus
# (Claude generates specs for each item)     # 2. YOU generate
uv run python train.py --step render         # 3. Render + screenshot
# (Claude compares and scores)               # 4. YOU compare
uv run python train.py --step report         # 5. Report + feedback
# (Claude optimizes prompts.py)              # 5b. YOU optimize

# Check progress across rounds:
uv run python train.py --history
```
