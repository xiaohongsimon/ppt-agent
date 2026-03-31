# Plan 1: Core Pipeline — Text/PPTX → HTML → Quality Gate → PDF

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working CLI + API that takes text or PPTX input, generates a high-quality HTML presentation, runs quality checks, and exports to PDF.

**Architecture:** FastAPI backend with 5 modules (Input Parser, Agent Engine, HTML Renderer, Quality Gate, PDF Export). Agent Engine starts as a lightweight LLM function-calling agent (Week 1-2 fallback-first approach — if PPTAgent integration proves viable in Week 2, we upgrade). HTML Renderer ports the proven presentation-as-code design system. Quality Gate runs rule-based checks + VLM visual review with auto-fix loop.

**Tech Stack:** Python 3.11+, FastAPI, uv, Pydantic, Jinja2, python-pptx, Playwright/Puppeteer, Claude/GPT-4o API, pytest

**Spec:** `docs/superpowers/specs/2026-03-31-ppt-agent-design.md`

**Scope:** This is Plan 1 of 3. Produces a working CLI tool + REST API.
- Plan 1 (this): Core pipeline — input → agent → render → QA → PDF
- Plan 2: Intelligence layer — Two-Stage Best-of-2, Session Manager, Web UI
- Plan 3: Knowledge moat — Template Library (Super Skeletons), User Profile Engine

---

## File Structure

```
ppt-agent/
├── backend/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app entry point
│   ├── config.py                    # Settings (API keys, model config)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── intent.py                # PresentationIntent Pydantic model (IR input)
│   │   └── render_spec.py           # SlideRenderSpec Pydantic model (IR output)
│   ├── input_parser/
│   │   ├── __init__.py
│   │   ├── text_parser.py           # Text/outline → PresentationIntent
│   │   └── pptx_parser.py           # PPTX → PresentationIntent
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── engine.py                # Agent: Intent → SlideRenderSpec
│   │   └── prompts.py               # System/user prompts for generation
│   ├── renderer/
│   │   ├── __init__.py
│   │   ├── html_renderer.py         # SlideRenderSpec → HTML files
│   │   ├── pdf_exporter.py          # HTML → PDF via Playwright
│   │   └── templates/               # Jinja2 templates
│   │       ├── base_slide.html.j2   # Slide template
│   │       ├── index.html.j2        # Entry point template
│   │       └── components/          # Reusable component partials
│   │           ├── card.html.j2
│   │           ├── chart.html.j2
│   │           ├── highlight_box.html.j2
│   │           └── flow.html.j2
│   ├── renderer/static/
│   │   ├── style.css                # Design system (ported from algo-insight)
│   │   └── slides.js                # Navigation (ported from algo-insight)
│   ├── quality_gate/
│   │   ├── __init__.py
│   │   ├── tier1_rules.py           # Rule-based checks (overflow, fonts, contrast)
│   │   ├── tier2_vlm.py             # VLM visual review
│   │   └── gate.py                  # Orchestrator: run tiers, auto-fix loop
│   └── api/
│       ├── __init__.py
│       └── routes.py                # REST endpoints
├── tests/
│   ├── conftest.py                  # Shared fixtures
│   ├── test_schemas.py              # IR contract tests
│   ├── test_text_parser.py
│   ├── test_pptx_parser.py
│   ├── test_agent_engine.py
│   ├── test_html_renderer.py
│   ├── test_quality_gate.py
│   ├── test_pdf_exporter.py
│   └── test_api.py                  # Integration tests
├── cli.py                           # CLI entry point
├── pyproject.toml                   # Project config + dependencies
├── CLAUDE.md                        # AI project config
└── .gitignore
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `backend/__init__.py`
- Create: `backend/config.py`
- Create: `backend/main.py`
- Create: `tests/conftest.py`
- Create: `.gitignore`
- Create: `CLAUDE.md`

- [ ] **Step 1: Initialize Python project with uv**

```bash
cd /Users/leehom/work/ppt-agent
uv init --python 3.11
```

- [ ] **Step 2: Write pyproject.toml**

```toml
[project]
name = "ppt-agent"
version = "0.1.0"
description = "AI-powered presentation generation platform"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn>=0.34.0",
    "pydantic>=2.10.0",
    "jinja2>=3.1.0",
    "python-pptx>=1.0.0",
    "httpx>=0.28.0",
    "anthropic>=0.42.0",
    "python-multipart>=0.0.18",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.8.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
```

- [ ] **Step 3: Create backend package and config**

```python
# backend/__init__.py
```

```python
# backend/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    llm_model: str = "claude-sonnet-4-5-20250514"
    vlm_model: str = "claude-sonnet-4-5-20250514"
    output_dir: str = "./output"

    class Config:
        env_file = ".env"


settings = Settings()
```

- [ ] **Step 4: Create minimal FastAPI app**

```python
# backend/main.py
from fastapi import FastAPI

app = FastAPI(title="PPT-Agent", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Create test conftest and verify project runs**

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)
```

```python
# tests/test_health.py
def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
```

- [ ] **Step 6: Create .gitignore and CLAUDE.md**

```gitignore
# .gitignore
__pycache__/
*.pyc
.env
.venv/
output/
node_modules/
.ruff_cache/
dist/
*.egg-info/
```

```markdown
# CLAUDE.md

## Project Overview
PPT-Agent: AI-powered presentation generation platform.
Spec: docs/superpowers/specs/2026-03-31-ppt-agent-design.md
Plan: docs/superpowers/plans/2026-03-31-plan1-core-pipeline.md

## Tech Stack
- Python 3.11+, FastAPI, Pydantic, Jinja2
- LLM: Claude API (anthropic SDK)
- Tests: pytest

## Commands
- Install: `uv sync`
- Test: `uv run pytest -v`
- Run server: `uv run uvicorn backend.main:app --reload`
- Lint: `uv run ruff check .`

## Architecture
Input Parser → Agent Engine → HTML Renderer → Quality Gate → PDF Export
IR contracts: backend/schemas/intent.py (input), backend/schemas/render_spec.py (output)
```

- [ ] **Step 7: Install dependencies and run tests**

Run: `uv sync && uv run pytest tests/test_health.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml backend/ tests/ cli.py .gitignore CLAUDE.md
git commit -m "feat: project scaffolding with FastAPI + pytest"
```

---

### Task 2: IR Contract Definition (Week 1 Critical Path)

**Files:**
- Create: `backend/schemas/__init__.py`
- Create: `backend/schemas/intent.py`
- Create: `backend/schemas/render_spec.py`
- Create: `tests/test_schemas.py`

The IR (Intermediate Representation) is the most important architectural decision — it defines the contract between Agent Engine output and HTML Renderer input. Every module depends on this.

- [ ] **Step 1: Write the failing tests for PresentationIntent**

```python
# tests/test_schemas.py
import json
from backend.schemas.intent import PresentationIntent, SlideIntent


def test_presentation_intent_minimal():
    intent = PresentationIntent(
        title="Q1 Review",
        context={"scene": "quarterly_review", "audience": "VP Engineering"},
        slides=[
            SlideIntent(type="title", heading="Q1 Review", subheading="Algorithm Team")
        ],
    )
    assert intent.title == "Q1 Review"
    assert len(intent.slides) == 1
    assert intent.slides[0].type == "title"


def test_presentation_intent_full():
    intent = PresentationIntent(
        title="Q1 Review",
        context={"scene": "quarterly_review", "audience": "VP", "tone": "data-driven"},
        slides=[
            SlideIntent(type="title", heading="Q1 Review"),
            SlideIntent(
                type="data_driven",
                heading="Key Metrics",
                content={"key_metrics": [{"label": "Revenue", "value": "$10M"}]},
                takeaway="Revenue grew 30% QoQ",
            ),
        ],
        source_analysis={"from_pptx": {"strengths": ["clear data"], "issues": ["too dense"]}},
    )
    assert len(intent.slides) == 2
    data = intent.model_dump()
    assert data["source_analysis"]["from_pptx"]["issues"] == ["too dense"]


def test_presentation_intent_serialization():
    intent = PresentationIntent(
        title="Test",
        context={"scene": "training"},
        slides=[SlideIntent(type="title", heading="Test")],
    )
    json_str = intent.model_dump_json()
    restored = PresentationIntent.model_validate_json(json_str)
    assert restored.title == intent.title
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_schemas.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implement PresentationIntent**

```python
# backend/schemas/__init__.py
from backend.schemas.intent import PresentationIntent, SlideIntent
from backend.schemas.render_spec import SlideRenderSpec, PresentationRenderSpec

__all__ = [
    "PresentationIntent",
    "SlideIntent",
    "SlideRenderSpec",
    "PresentationRenderSpec",
]
```

```python
# backend/schemas/intent.py
"""IR Input: What the user wants to present (from Input Parser → Agent Engine)."""

from pydantic import BaseModel


class SlideIntent(BaseModel):
    """A single slide's intent — what information should appear."""

    type: str  # "title", "data_driven", "text", "comparison", "visual", "closing"
    heading: str
    subheading: str | None = None
    content: dict | None = None  # Flexible: key_metrics, bullet_points, chart_data, etc.
    takeaway: str | None = None  # Key message for this slide
    speaker_notes: str | None = None


class PresentationIntent(BaseModel):
    """Complete presentation intent — the contract from Input Parser to Agent Engine."""

    title: str
    context: dict  # scene, audience, tone — flexible for extensibility
    slides: list[SlideIntent]
    source_analysis: dict | None = None  # From PPTX/screenshot input
    user_profile_hints: dict | None = None  # From User Profile Engine (Plan 3)
```

- [ ] **Step 4: Run intent tests**

Run: `uv run pytest tests/test_schemas.py::test_presentation_intent_minimal tests/test_schemas.py::test_presentation_intent_full tests/test_schemas.py::test_presentation_intent_serialization -v`
Expected: PASS

- [ ] **Step 5: Write failing tests for SlideRenderSpec**

Add to `tests/test_schemas.py`:

```python
from backend.schemas.render_spec import SlideRenderSpec, PresentationRenderSpec, Component


def test_slide_render_spec():
    slide = SlideRenderSpec(
        slide_index=0,
        layout="title",
        heading="Q1 Review",
        subheading="Algorithm Team",
        components=[],
        css_overrides={},
    )
    assert slide.layout == "title"
    assert slide.slide_index == 0


def test_presentation_render_spec():
    spec = PresentationRenderSpec(
        title="Q1 Review",
        theme={"accent_primary": "#4f6df5", "accent_secondary": "#7c3aed"},
        slides=[
            SlideRenderSpec(
                slide_index=0,
                layout="title",
                heading="Q1 Review",
                components=[],
            ),
            SlideRenderSpec(
                slide_index=1,
                layout="data_driven",
                heading="Key Metrics",
                components=[
                    Component(
                        type="card_grid",
                        props={
                            "columns": 3,
                            "cards": [
                                {"title": "Revenue", "value": "$10M", "change": "+30%"}
                            ],
                        },
                    ),
                    Component(
                        type="highlight_box",
                        props={"text": "Revenue grew 30% QoQ", "color": "green"},
                    ),
                ],
            ),
        ],
    )
    assert len(spec.slides) == 2
    assert spec.slides[1].components[0].type == "card_grid"
    assert spec.theme["accent_primary"] == "#4f6df5"


def test_component_types():
    """All supported component types should be valid."""
    valid_types = [
        "card_grid", "highlight_box", "bar_chart", "flow",
        "bullet_list", "quote_box", "comparison", "text_block",
        "chart_js", "image",
    ]
    for t in valid_types:
        c = Component(type=t, props={})
        assert c.type == t
```

- [ ] **Step 6: Implement SlideRenderSpec**

```python
# backend/schemas/render_spec.py
"""IR Output: Render-ready specification (from Agent Engine → HTML Renderer)."""

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
    css_overrides: dict | None = None  # Per-slide CSS variable overrides
    speaker_notes: str | None = None


class PresentationRenderSpec(BaseModel):
    """Complete render specification — the contract from Agent Engine to HTML Renderer."""

    title: str
    theme: dict  # CSS variable values: accent_primary, accent_secondary, font_family, etc.
    slides: list[SlideRenderSpec]
    metadata: dict | None = None  # Generation metadata (model used, timestamp, etc.)
```

- [ ] **Step 7: Run all schema tests**

Run: `uv run pytest tests/test_schemas.py -v`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add backend/schemas/ tests/test_schemas.py
git commit -m "feat: define IR contracts (PresentationIntent + SlideRenderSpec)"
```

---

### Task 3: HTML Renderer — Design System & Static Assets

**Files:**
- Create: `backend/renderer/__init__.py`
- Create: `backend/renderer/static/style.css`
- Create: `backend/renderer/static/slides.js`
- Create: `backend/renderer/templates/index.html.j2`
- Create: `backend/renderer/templates/base_slide.html.j2`
- Create: `backend/renderer/templates/components/card_grid.html.j2`
- Create: `backend/renderer/templates/components/highlight_box.html.j2`
- Create: `backend/renderer/templates/components/bar_chart.html.j2`
- Create: `backend/renderer/templates/components/bullet_list.html.j2`
- Create: `backend/renderer/templates/components/flow.html.j2`

- [ ] **Step 1: Port design system CSS from algo-insight**

```css
/* backend/renderer/static/style.css */
/* PPT-Agent Design System — ported from presentation-as-code (algo-insight) */

:root {
  /* Theme colors — overridden per presentation */
  --accent-primary: #4f6df5;
  --accent-secondary: #7c3aed;
  --accent-green: #10b981;
  --accent-orange: #f59e0b;
  --accent-red: #ef4444;
  --accent-pink: #db2777;

  /* Typography */
  --heading-color: #1a202c;
  --text-color: #2d3748;
  --text-muted: #718096;
  --bg-color: #ffffff;
  --card-bg: #f7fafc;

  /* Spacing (8px grid) */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;

  /* Font */
  --font-family: 'Noto Sans SC', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html {
  scroll-snap-type: y mandatory;
  scroll-behavior: smooth;
  font-size: clamp(16px, 1.9vw, 22px);
}

body {
  font-family: var(--font-family);
  color: var(--text-color);
  background: var(--bg-color);
  line-height: 1.6;
}

/* Slide container */
.slide {
  min-height: 100vh;
  scroll-snap-align: start;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 5vh 6vw;
  position: relative;
}

.slide::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: radial-gradient(ellipse at center, transparent 60%, rgba(0,0,0,0.03) 100%);
}

/* Typography */
h1 { font-size: 3em; font-weight: 900; color: var(--heading-color); line-height: 1.1; margin-bottom: var(--space-lg); }
h2 { font-size: 2em; font-weight: 700; color: var(--heading-color); line-height: 1.2; margin-bottom: var(--space-md); }
h3 { font-size: 1.3em; font-weight: 600; color: var(--heading-color); margin-bottom: var(--space-sm); }

.gradient-text {
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Tag */
.tag {
  display: inline-block;
  padding: 4px 14px;
  border-radius: 20px;
  font-size: 0.75em;
  font-weight: 600;
  letter-spacing: 0.5px;
  margin-bottom: var(--space-md);
  color: white;
  background: var(--accent-primary);
}

/* Card */
.card {
  background: white;
  border-radius: 12px;
  padding: var(--space-lg);
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  border-left: 4px solid var(--accent-primary);
}

/* Card grid */
.card-grid { display: grid; gap: var(--space-md); }
.card-grid.cols-2 { grid-template-columns: repeat(2, 1fr); }
.card-grid.cols-3 { grid-template-columns: repeat(3, 1fr); }
.card-grid.cols-4 { grid-template-columns: repeat(4, 1fr); }

/* Highlight box */
.highlight-box {
  padding: var(--space-md) var(--space-lg);
  border-radius: 8px;
  border-left: 4px solid var(--accent-green);
  background: #f0fdf4;
  margin-top: var(--space-lg);
  font-weight: 500;
}
.highlight-box.blue { border-color: var(--accent-primary); background: #eff6ff; }
.highlight-box.purple { border-color: var(--accent-secondary); background: #f5f3ff; }
.highlight-box.orange { border-color: var(--accent-orange); background: #fffbeb; }
.highlight-box.red { border-color: var(--accent-red); background: #fef2f2; }

/* Bar chart (CSS-only) */
.bar-chart { display: flex; flex-direction: column; gap: var(--space-sm); }
.bar-row { display: flex; align-items: center; gap: var(--space-md); }
.bar-label { width: 120px; text-align: right; font-size: 0.85em; font-weight: 500; }
.bar-track { flex: 1; height: 28px; background: #edf2f7; border-radius: 6px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 6px; background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary)); display: flex; align-items: center; padding-left: var(--space-sm); color: white; font-size: 0.8em; font-weight: 600; }

/* Flow (steps with arrows) */
.flow { display: flex; align-items: center; gap: var(--space-sm); flex-wrap: wrap; }
.flow-step {
  background: white;
  border: 2px solid var(--accent-primary);
  border-radius: 10px;
  padding: var(--space-sm) var(--space-md);
  font-weight: 500;
  font-size: 0.9em;
}
.flow-arrow { color: var(--accent-primary); font-size: 1.2em; }

/* Bullet list */
.bullet-list { list-style: none; padding: 0; }
.bullet-list li {
  padding: var(--space-sm) 0;
  padding-left: var(--space-lg);
  position: relative;
  font-size: 0.95em;
}
.bullet-list li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent-primary);
}

/* Quote box */
.quote-box {
  border-left: 4px solid var(--accent-secondary);
  padding: var(--space-md) var(--space-lg);
  background: #f5f3ff;
  border-radius: 0 8px 8px 0;
  font-style: italic;
}

/* Comparison (side-by-side) */
.comparison { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-lg); }

/* Navigation */
.nav-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(255,255,255,0.95);
  backdrop-filter: blur(10px);
  padding: var(--space-sm) var(--space-lg);
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 100;
  border-top: 1px solid #e2e8f0;
}
.slide-counter { font-size: 0.8em; color: var(--text-muted); font-weight: 500; }
.progress-bar { flex: 1; height: 3px; background: #e2e8f0; margin: 0 var(--space-lg); border-radius: 2px; }
.progress-fill { height: 100%; background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary)); border-radius: 2px; transition: width 0.3s; }

/* Print / PDF export */
@media print {
  html { scroll-snap-type: none; }
  .slide { min-height: auto; page-break-after: always; padding: 40px; }
  .nav-bar { display: none; }
}

/* Responsive */
@media (max-width: 768px) {
  .card-grid.cols-3, .card-grid.cols-4 { grid-template-columns: repeat(2, 1fr); }
  .comparison { grid-template-columns: 1fr; }
  .slide { padding: 3vh 4vw; }
}
```

- [ ] **Step 2: Port navigation script from algo-insight**

```javascript
/* backend/renderer/static/slides.js */
/* PPT-Agent Slide Navigation — ported from presentation-as-code (algo-insight) */
/* Zero dependencies, 77 lines */

(function () {
  const slides = document.querySelectorAll('.slide');
  if (!slides.length) return;

  let current = 0;
  const total = slides.length;

  const counter = document.querySelector('.slide-counter');
  const progressFill = document.querySelector('.progress-fill');

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const idx = Array.from(slides).indexOf(entry.target);
          if (idx >= 0) update(idx);
        }
      });
    },
    { threshold: 0.4 }
  );

  slides.forEach((s) => observer.observe(s));

  function update(idx) {
    current = idx;
    if (counter) counter.textContent = `${idx + 1} / ${total}`;
    if (progressFill) progressFill.style.width = `${((idx + 1) / total) * 100}%`;
  }

  function goTo(idx) {
    const target = Math.max(0, Math.min(idx, total - 1));
    slides[target].scrollIntoView({ behavior: 'smooth' });
  }

  document.addEventListener('keydown', (e) => {
    switch (e.key) {
      case 'ArrowRight':
      case 'ArrowDown':
      case ' ':
        e.preventDefault();
        goTo(current + 1);
        break;
      case 'ArrowLeft':
      case 'ArrowUp':
        e.preventDefault();
        goTo(current - 1);
        break;
      case 'Home':
        e.preventDefault();
        goTo(0);
        break;
      case 'End':
        e.preventDefault();
        goTo(total - 1);
        break;
    }
  });

  function setupButtons() {
    document.querySelectorAll('[data-dir]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const dir = parseInt(btn.dataset.dir, 10);
        goTo(current + dir);
      });
    });
  }

  update(0);
  setupButtons();
})();
```

- [ ] **Step 3: Create Jinja2 templates — index and base slide**

```html
{# backend/renderer/templates/index.html.j2 #}
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ title }}</title>
  <style>
    :root {
      {% for key, value in theme.items() %}
      --{{ key | replace("_", "-") }}: {{ value }};
      {% endfor %}
    }
  </style>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  {% for slide in slides %}
  {% include "base_slide.html.j2" %}
  {% endfor %}

  <nav class="nav-bar">
    <button data-dir="-1">&larr;</button>
    <span class="slide-counter">1 / {{ slides | length }}</span>
    <div class="progress-bar"><div class="progress-fill" style="width: {{ 100 / slides | length }}%"></div></div>
    <button data-dir="1">&rarr;</button>
  </nav>

  <script src="slides.js"></script>
</body>
</html>
```

```html
{# backend/renderer/templates/base_slide.html.j2 #}
<section class="slide" id="slide-{{ slide.slide_index }}">
  {% if slide.subheading %}
  <span class="tag">{{ slide.subheading }}</span>
  {% endif %}

  <h1{% if slide.slide_index == 0 %} class="gradient-text"{% endif %}>{{ slide.heading }}</h1>

  {% for component in slide.components %}
    {% if component.type == "card_grid" %}
      {% include "components/card_grid.html.j2" %}
    {% elif component.type == "highlight_box" %}
      {% include "components/highlight_box.html.j2" %}
    {% elif component.type == "bar_chart" %}
      {% include "components/bar_chart.html.j2" %}
    {% elif component.type == "bullet_list" %}
      {% include "components/bullet_list.html.j2" %}
    {% elif component.type == "flow" %}
      {% include "components/flow.html.j2" %}
    {% elif component.type == "text_block" %}
      <div class="text-block">{{ component.props.get("text", "") }}</div>
    {% elif component.type == "quote_box" %}
      <div class="quote-box">{{ component.props.get("text", "") }}</div>
    {% endif %}
  {% endfor %}
</section>
```

- [ ] **Step 4: Create component templates**

```html
{# backend/renderer/templates/components/card_grid.html.j2 #}
{% set cols = component.props.get("columns", 3) %}
<div class="card-grid cols-{{ cols }}">
  {% for card in component.props.get("cards", []) %}
  <div class="card">
    {% if card.get("title") %}<h3>{{ card.title }}</h3>{% endif %}
    {% if card.get("value") %}<div style="font-size: 2em; font-weight: 900; color: var(--accent-primary);">{{ card.value }}</div>{% endif %}
    {% if card.get("change") %}<div style="color: var(--accent-green); font-weight: 600;">{{ card.change }}</div>{% endif %}
    {% if card.get("description") %}<p style="color: var(--text-muted); font-size: 0.85em;">{{ card.description }}</p>{% endif %}
  </div>
  {% endfor %}
</div>
```

```html
{# backend/renderer/templates/components/highlight_box.html.j2 #}
{% set color = component.props.get("color", "green") %}
<div class="highlight-box {{ color }}">
  {{ component.props.get("text", "") }}
</div>
```

```html
{# backend/renderer/templates/components/bar_chart.html.j2 #}
<div class="bar-chart">
  {% for bar in component.props.get("bars", []) %}
  <div class="bar-row">
    <span class="bar-label">{{ bar.get("label", "") }}</span>
    <div class="bar-track">
      <div class="bar-fill" style="width: {{ bar.get('value', 0) }}%">
        {{ bar.get("display", "") }}
      </div>
    </div>
  </div>
  {% endfor %}
</div>
```

```html
{# backend/renderer/templates/components/bullet_list.html.j2 #}
<ul class="bullet-list">
  {% for item in component.props.get("items", []) %}
  <li>{{ item }}</li>
  {% endfor %}
</ul>
```

```html
{# backend/renderer/templates/components/flow.html.j2 #}
<div class="flow">
  {% for step in component.props.get("steps", []) %}
  {% if not loop.first %}<span class="flow-arrow">&rarr;</span>{% endif %}
  <div class="flow-step">{{ step }}</div>
  {% endfor %}
</div>
```

- [ ] **Step 5: Commit static assets and templates**

```bash
git add backend/renderer/
git commit -m "feat: port design system CSS, slides.js, and Jinja2 templates"
```

---

### Task 4: HTML Renderer — Python Engine

**Files:**
- Create: `backend/renderer/__init__.py`
- Create: `backend/renderer/html_renderer.py`
- Create: `tests/test_html_renderer.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_html_renderer.py
import os
import tempfile
from pathlib import Path

from backend.schemas.render_spec import PresentationRenderSpec, SlideRenderSpec, Component
from backend.renderer.html_renderer import render_presentation


def _make_spec() -> PresentationRenderSpec:
    return PresentationRenderSpec(
        title="Test Presentation",
        theme={"accent_primary": "#4f6df5", "accent_secondary": "#7c3aed"},
        slides=[
            SlideRenderSpec(
                slide_index=0,
                layout="title",
                heading="Welcome",
                subheading="PPT-Agent Demo",
                components=[],
            ),
            SlideRenderSpec(
                slide_index=1,
                layout="data_driven",
                heading="Key Metrics",
                components=[
                    Component(
                        type="card_grid",
                        props={
                            "columns": 3,
                            "cards": [
                                {"title": "Users", "value": "10K", "change": "+25%"},
                                {"title": "Revenue", "value": "$1M", "change": "+30%"},
                                {"title": "NPS", "value": "72", "change": "+5"},
                            ],
                        },
                    ),
                    Component(
                        type="highlight_box",
                        props={"text": "All metrics trending up", "color": "green"},
                    ),
                ],
            ),
        ],
    )


def test_render_creates_output_dir():
    spec = _make_spec()
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "presentation"
        render_presentation(spec, output_path)
        assert output_path.exists()
        assert (output_path / "index.html").exists()
        assert (output_path / "style.css").exists()
        assert (output_path / "slides.js").exists()


def test_render_html_contains_slides():
    spec = _make_spec()
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "presentation"
        render_presentation(spec, output_path)
        html = (output_path / "index.html").read_text()
        assert "Welcome" in html
        assert "Key Metrics" in html
        assert "10K" in html
        assert "highlight-box" in html
        assert "slide-0" in html
        assert "slide-1" in html


def test_render_theme_applied():
    spec = _make_spec()
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "presentation"
        render_presentation(spec, output_path)
        html = (output_path / "index.html").read_text()
        assert "#4f6df5" in html  # theme color in CSS variables
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_html_renderer.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement HTML renderer**

```python
# backend/renderer/__init__.py
```

```python
# backend/renderer/html_renderer.py
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
        autoescape=False,  # HTML templates — we control the content
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
```

- [ ] **Step 4: Run tests and verify they pass**

Run: `uv run pytest tests/test_html_renderer.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/renderer/html_renderer.py tests/test_html_renderer.py
git commit -m "feat: HTML renderer — SlideRenderSpec to standalone HTML"
```

---

### Task 5: Input Parser — Text

**Files:**
- Create: `backend/input_parser/__init__.py`
- Create: `backend/input_parser/text_parser.py`
- Create: `tests/test_text_parser.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_text_parser.py
import pytest
from unittest.mock import patch, AsyncMock

from backend.input_parser.text_parser import parse_text
from backend.schemas.intent import PresentationIntent


MOCK_LLM_RESPONSE = """{
  "title": "Q1 Algorithm Team Review",
  "context": {
    "scene": "quarterly_review",
    "audience": "VP Engineering",
    "tone": "data-driven"
  },
  "slides": [
    {"type": "title", "heading": "Q1 Algorithm Team Review", "subheading": "2026 Q1"},
    {"type": "data_driven", "heading": "Key Metrics", "content": {"key_metrics": [{"label": "GPU utilization", "value": "87%"}]}, "takeaway": "GPU utilization up 12%"},
    {"type": "text", "heading": "Key Achievements", "content": {"bullet_points": ["Launched model v3", "Reduced latency 40%"]}}
  ]
}"""


@pytest.mark.asyncio
async def test_parse_text_returns_intent():
    with patch("backend.input_parser.text_parser._call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = MOCK_LLM_RESPONSE
        intent = await parse_text("Q1 review for algorithm team: GPU util 87%, launched v3, reduced latency 40%")
        assert isinstance(intent, PresentationIntent)
        assert intent.title == "Q1 Algorithm Team Review"
        assert len(intent.slides) == 3
        assert intent.slides[0].type == "title"


@pytest.mark.asyncio
async def test_parse_text_passes_context():
    with patch("backend.input_parser.text_parser._call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = MOCK_LLM_RESPONSE
        await parse_text("Q1 review", scene="quarterly_review", audience="CTO")
        call_args = mock_llm.call_args[0][0]  # first positional arg = prompt
        assert "quarterly_review" in call_args
        assert "CTO" in call_args
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_text_parser.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement text parser**

```python
# backend/input_parser/__init__.py
```

```python
# backend/input_parser/text_parser.py
"""Parse text/outline input into a PresentationIntent via LLM."""

import json
import anthropic

from backend.config import settings
from backend.schemas.intent import PresentationIntent

SYSTEM_PROMPT = """You are a presentation architect. Given user input (text, outline, bullet points),
produce a structured JSON that defines the presentation intent.

Output ONLY valid JSON matching this schema:
{
  "title": "string",
  "context": {"scene": "string", "audience": "string", "tone": "string"},
  "slides": [
    {
      "type": "title|data_driven|text|comparison|visual|closing",
      "heading": "string",
      "subheading": "string or null",
      "content": {object with type-specific data} or null,
      "takeaway": "string or null",
      "speaker_notes": "string or null"
    }
  ]
}

Guidelines:
- First slide should be type "title"
- Last slide should be type "closing" with action items
- Every data slide needs a "takeaway" field
- Aim for 8-15 slides for a typical presentation
- For data_driven slides, include key_metrics in content
- For text slides, include bullet_points in content
- Write in the same language as the user input"""


async def _call_llm(prompt: str) -> str:
    """Call the LLM and return the text response."""
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model=settings.llm_model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


async def parse_text(
    text: str,
    scene: str | None = None,
    audience: str | None = None,
) -> PresentationIntent:
    """Parse text input into a PresentationIntent.

    Args:
        text: Raw text, outline, or bullet points from the user.
        scene: Optional scene hint (e.g., "quarterly_review").
        audience: Optional audience hint (e.g., "VP Engineering").

    Returns:
        PresentationIntent ready for the Agent Engine.
    """
    parts = [f"Create a presentation from the following input:\n\n{text}"]
    if scene:
        parts.append(f"\nScene: {scene}")
    if audience:
        parts.append(f"\nAudience: {audience}")
    prompt = "\n".join(parts)

    raw = await _call_llm(prompt)

    # Strip markdown code fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]  # remove first line
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()

    data = json.loads(cleaned)
    return PresentationIntent.model_validate(data)
```

- [ ] **Step 4: Run tests and verify they pass**

Run: `uv run pytest tests/test_text_parser.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/input_parser/ tests/test_text_parser.py
git commit -m "feat: text input parser — text/outline to PresentationIntent via LLM"
```

---

### Task 6: Agent Engine — Intent to RenderSpec

**Files:**
- Create: `backend/agent/__init__.py`
- Create: `backend/agent/engine.py`
- Create: `backend/agent/prompts.py`
- Create: `tests/test_agent_engine.py`

This is the "fallback-first" agent — a lightweight LLM function-calling agent. If PPTAgent fork proves viable in Week 2, we swap the internals while keeping the same interface.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_agent_engine.py
import json
import pytest
from unittest.mock import patch, AsyncMock

from backend.schemas.intent import PresentationIntent, SlideIntent
from backend.schemas.render_spec import PresentationRenderSpec
from backend.agent.engine import generate_render_spec


MOCK_AGENT_RESPONSE = """{
  "title": "Q1 Review",
  "theme": {
    "accent_primary": "#4f6df5",
    "accent_secondary": "#7c3aed"
  },
  "slides": [
    {
      "slide_index": 0,
      "layout": "title",
      "heading": "Q1 Algorithm Team Review",
      "subheading": "2026 Q1",
      "components": []
    },
    {
      "slide_index": 1,
      "layout": "data_driven",
      "heading": "Key Metrics",
      "components": [
        {
          "type": "card_grid",
          "props": {
            "columns": 3,
            "cards": [{"title": "GPU Util", "value": "87%", "change": "+12%"}]
          }
        },
        {
          "type": "highlight_box",
          "props": {"text": "GPU utilization up 12% QoQ", "color": "green"}
        }
      ]
    }
  ]
}"""


def _make_intent() -> PresentationIntent:
    return PresentationIntent(
        title="Q1 Review",
        context={"scene": "quarterly_review", "audience": "VP Engineering"},
        slides=[
            SlideIntent(type="title", heading="Q1 Review", subheading="2026 Q1"),
            SlideIntent(type="data_driven", heading="Key Metrics", takeaway="GPU up 12%"),
        ],
    )


@pytest.mark.asyncio
async def test_generate_render_spec():
    with patch("backend.agent.engine._call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = MOCK_AGENT_RESPONSE
        intent = _make_intent()
        spec = await generate_render_spec(intent)
        assert isinstance(spec, PresentationRenderSpec)
        assert spec.title == "Q1 Review"
        assert len(spec.slides) == 2
        assert spec.slides[1].components[0].type == "card_grid"


@pytest.mark.asyncio
async def test_generate_render_spec_has_theme():
    with patch("backend.agent.engine._call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = MOCK_AGENT_RESPONSE
        spec = await generate_render_spec(_make_intent())
        assert "accent_primary" in spec.theme
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_agent_engine.py -v`
Expected: FAIL

- [ ] **Step 3: Create agent prompts**

```python
# backend/agent/prompts.py
"""Prompts for the Agent Engine."""

SYSTEM_PROMPT = """You are a presentation designer AI. Given a PresentationIntent (what the user wants),
produce a PresentationRenderSpec (exactly how to render it as HTML).

Output ONLY valid JSON matching this schema:
{
  "title": "string",
  "theme": {
    "accent_primary": "#hex",
    "accent_secondary": "#hex"
  },
  "slides": [
    {
      "slide_index": integer,
      "layout": "title|data_driven|split_panel|full_visual|comparison",
      "heading": "string",
      "subheading": "string or null",
      "components": [
        {
          "type": "card_grid|highlight_box|bar_chart|bullet_list|flow|text_block|quote_box|comparison",
          "props": {type-specific properties}
        }
      ],
      "speaker_notes": "string or null"
    }
  ]
}

Component props reference:
- card_grid: {"columns": 2-4, "cards": [{"title": str, "value": str, "change": str, "description": str}]}
- highlight_box: {"text": str, "color": "green|blue|purple|orange|red"}
- bar_chart: {"bars": [{"label": str, "value": 0-100, "display": str}]}
- bullet_list: {"items": [str]}
- flow: {"steps": [str]}
- text_block: {"text": str}
- quote_box: {"text": str}
- comparison: {"left": {"title": str, "items": [str]}, "right": {"title": str, "items": [str]}}

Design rules:
- Every slide MUST have at least one component (except title slides)
- Every data slide MUST end with a highlight_box (key takeaway)
- Max 7 bullet points per bullet_list
- Max 4 cards per card_grid
- Choose theme colors that match the tone (professional → blue, growth → green, etc.)
- Use varied component types across slides — avoid repetitive layouts
- First slide: layout "title", minimal components
- Last slide: layout "title" or closing, with action items as bullet_list"""


def build_user_prompt(intent_json: str) -> str:
    return f"""Convert this PresentationIntent into a PresentationRenderSpec:

{intent_json}

Remember: output ONLY the JSON, no markdown fences, no explanation."""
```

- [ ] **Step 4: Implement agent engine**

```python
# backend/agent/__init__.py
```

```python
# backend/agent/engine.py
"""Agent Engine: converts PresentationIntent → PresentationRenderSpec via LLM."""

import json
import anthropic

from backend.config import settings
from backend.schemas.intent import PresentationIntent
from backend.schemas.render_spec import PresentationRenderSpec
from backend.agent.prompts import SYSTEM_PROMPT, build_user_prompt


async def _call_llm(prompt: str) -> str:
    """Call the LLM with the agent system prompt."""
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model=settings.llm_model,
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


async def generate_render_spec(intent: PresentationIntent) -> PresentationRenderSpec:
    """Generate a PresentationRenderSpec from a PresentationIntent.

    This is the "fallback-first" agent — lightweight LLM function-calling.
    If PPTAgent fork integration succeeds (Week 2 kill switch), the internals
    of this function get swapped while the interface stays the same.

    Args:
        intent: What the user wants to present.

    Returns:
        PresentationRenderSpec ready for the HTML Renderer.
    """
    intent_json = intent.model_dump_json(indent=2)
    prompt = build_user_prompt(intent_json)
    raw = await _call_llm(prompt)

    # Strip markdown code fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()

    data = json.loads(cleaned)
    return PresentationRenderSpec.model_validate(data)
```

- [ ] **Step 5: Run tests and verify they pass**

Run: `uv run pytest tests/test_agent_engine.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add backend/agent/ tests/test_agent_engine.py
git commit -m "feat: agent engine — PresentationIntent to PresentationRenderSpec via LLM"
```

---

### Task 7: Quality Gate — Tier 1 Rule-Based Checks

**Files:**
- Create: `backend/quality_gate/__init__.py`
- Create: `backend/quality_gate/tier1_rules.py`
- Create: `tests/test_quality_gate.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_quality_gate.py
from backend.schemas.render_spec import PresentationRenderSpec, SlideRenderSpec, Component
from backend.quality_gate.tier1_rules import check_tier1, Tier1Result


def test_tier1_passes_good_slide():
    spec = PresentationRenderSpec(
        title="Test",
        theme={"accent_primary": "#4f6df5"},
        slides=[
            SlideRenderSpec(
                slide_index=0,
                layout="title",
                heading="Hello",
                components=[],
            ),
            SlideRenderSpec(
                slide_index=1,
                layout="data_driven",
                heading="Metrics",
                components=[
                    Component(type="card_grid", props={"columns": 3, "cards": [
                        {"title": "A", "value": "1"},
                        {"title": "B", "value": "2"},
                    ]}),
                    Component(type="highlight_box", props={"text": "Key insight", "color": "green"}),
                ],
            ),
        ],
    )
    result = check_tier1(spec)
    assert result.passed
    assert len(result.issues) == 0


def test_tier1_catches_too_many_bullets():
    spec = PresentationRenderSpec(
        title="Test",
        theme={},
        slides=[
            SlideRenderSpec(
                slide_index=0,
                layout="text",
                heading="Too Much",
                components=[
                    Component(type="bullet_list", props={"items": [f"item {i}" for i in range(10)]}),
                ],
            ),
        ],
    )
    result = check_tier1(spec)
    assert not result.passed
    assert any("bullet" in issue.lower() or "density" in issue.lower() for issue in result.issues)


def test_tier1_catches_missing_takeaway():
    spec = PresentationRenderSpec(
        title="Test",
        theme={},
        slides=[
            SlideRenderSpec(
                slide_index=0,
                layout="data_driven",
                heading="Data",
                components=[
                    Component(type="card_grid", props={"columns": 2, "cards": [{"title": "A", "value": "1"}]}),
                    # Missing highlight_box
                ],
            ),
        ],
    )
    result = check_tier1(spec)
    assert not result.passed
    assert any("takeaway" in issue.lower() or "highlight" in issue.lower() for issue in result.issues)


def test_tier1_catches_too_many_cards():
    spec = PresentationRenderSpec(
        title="Test",
        theme={},
        slides=[
            SlideRenderSpec(
                slide_index=0,
                layout="data_driven",
                heading="Cards",
                components=[
                    Component(type="card_grid", props={"columns": 3, "cards": [
                        {"title": f"Card {i}", "value": str(i)} for i in range(7)
                    ]}),
                ],
            ),
        ],
    )
    result = check_tier1(spec)
    assert not result.passed
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_quality_gate.py -v`
Expected: FAIL

- [ ] **Step 3: Implement Tier 1 rules**

```python
# backend/quality_gate/__init__.py
```

```python
# backend/quality_gate/tier1_rules.py
"""Tier 1: Rule-based quality checks on PresentationRenderSpec (millisecond-level)."""

from dataclasses import dataclass, field

from backend.schemas.render_spec import PresentationRenderSpec, SlideRenderSpec

MAX_BULLET_ITEMS = 7
MAX_CARDS = 5
DATA_LAYOUTS = {"data_driven", "split_panel", "comparison"}


@dataclass
class Tier1Result:
    passed: bool
    issues: list[str] = field(default_factory=list)
    slide_issues: dict[int, list[str]] = field(default_factory=dict)


def _check_slide(slide: SlideRenderSpec) -> list[str]:
    """Check a single slide for rule violations."""
    issues = []

    for comp in slide.components:
        # Check bullet list density
        if comp.type == "bullet_list":
            items = comp.props.get("items", [])
            if len(items) > MAX_BULLET_ITEMS:
                issues.append(
                    f"Slide {slide.slide_index}: bullet_list has {len(items)} items "
                    f"(max {MAX_BULLET_ITEMS}). Information density too high."
                )

        # Check card count
        if comp.type == "card_grid":
            cards = comp.props.get("cards", [])
            if len(cards) > MAX_CARDS:
                issues.append(
                    f"Slide {slide.slide_index}: card_grid has {len(cards)} cards "
                    f"(max {MAX_CARDS}). Too many cards for readability."
                )

    # Data slides must have a highlight_box (takeaway)
    if slide.layout in DATA_LAYOUTS:
        has_highlight = any(c.type == "highlight_box" for c in slide.components)
        if not has_highlight:
            issues.append(
                f"Slide {slide.slide_index}: data slide (layout={slide.layout}) "
                f"missing highlight_box takeaway."
            )

    # No empty non-title slides
    if slide.layout != "title" and len(slide.components) == 0:
        issues.append(
            f"Slide {slide.slide_index}: non-title slide has no components."
        )

    return issues


def check_tier1(spec: PresentationRenderSpec) -> Tier1Result:
    """Run all Tier 1 rule-based checks on a PresentationRenderSpec.

    Returns:
        Tier1Result with passed=True if no issues found.
    """
    all_issues = []
    slide_issues = {}

    for slide in spec.slides:
        issues = _check_slide(slide)
        if issues:
            slide_issues[slide.slide_index] = issues
            all_issues.extend(issues)

    # Presentation-level checks
    if len(spec.slides) < 2:
        all_issues.append("Presentation has fewer than 2 slides.")
    if len(spec.slides) > 25:
        all_issues.append(f"Presentation has {len(spec.slides)} slides (max 25). Too long.")

    return Tier1Result(
        passed=len(all_issues) == 0,
        issues=all_issues,
        slide_issues=slide_issues,
    )
```

- [ ] **Step 4: Run tests and verify they pass**

Run: `uv run pytest tests/test_quality_gate.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/quality_gate/ tests/test_quality_gate.py
git commit -m "feat: Quality Gate Tier 1 — rule-based checks for density, takeaways, cards"
```

---

### Task 8: Quality Gate — Tier 2 VLM Visual Review

**Files:**
- Create: `backend/quality_gate/tier2_vlm.py`
- Modify: `tests/test_quality_gate.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_quality_gate.py`:

```python
import pytest
from unittest.mock import patch, AsyncMock
from backend.quality_gate.tier2_vlm import check_tier2_vlm, VLMResult


MOCK_VLM_RESPONSE = """{
  "overall_score": 8.2,
  "dimensions": {
    "visual_harmony": 8.5,
    "professional_look": 8.0,
    "information_clarity": 8.5,
    "template_adherence": 7.8
  },
  "issues": [],
  "suggestions": ["Consider adding more whitespace between sections"]
}"""

MOCK_VLM_FAIL_RESPONSE = """{
  "overall_score": 5.5,
  "dimensions": {
    "visual_harmony": 5.0,
    "professional_look": 6.0,
    "information_clarity": 5.5,
    "template_adherence": 5.5
  },
  "issues": ["Text overlaps with chart area", "Color contrast too low on slide 2"],
  "suggestions": ["Increase font size", "Use darker text color"]
}"""


@pytest.mark.asyncio
async def test_vlm_passes_good_presentation():
    with patch("backend.quality_gate.tier2_vlm._call_vlm", new_callable=AsyncMock) as mock:
        mock.return_value = MOCK_VLM_RESPONSE
        result = await check_tier2_vlm(
            html_dir="/tmp/fake",
            screenshot_paths=["/tmp/fake/slide0.png", "/tmp/fake/slide1.png"],
        )
        assert isinstance(result, VLMResult)
        assert result.passed
        assert result.overall_score >= 7.0


@pytest.mark.asyncio
async def test_vlm_fails_bad_presentation():
    with patch("backend.quality_gate.tier2_vlm._call_vlm", new_callable=AsyncMock) as mock:
        mock.return_value = MOCK_VLM_FAIL_RESPONSE
        result = await check_tier2_vlm(
            html_dir="/tmp/fake",
            screenshot_paths=["/tmp/fake/slide0.png"],
        )
        assert not result.passed
        assert result.overall_score < 7.0
        assert len(result.issues) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_quality_gate.py::test_vlm_passes_good_presentation tests/test_quality_gate.py::test_vlm_fails_bad_presentation -v`
Expected: FAIL

- [ ] **Step 3: Implement Tier 2 VLM**

```python
# backend/quality_gate/tier2_vlm.py
"""Tier 2: VLM-based visual quality review (seconds-level)."""

import base64
import json
from dataclasses import dataclass, field
from pathlib import Path

import anthropic

from backend.config import settings

PASS_THRESHOLD = 7.0

VLM_SYSTEM_PROMPT = """You are a professional presentation design reviewer.
Given screenshots of presentation slides, evaluate their visual quality.

Output ONLY valid JSON:
{
  "overall_score": float (1-10),
  "dimensions": {
    "visual_harmony": float (1-10),
    "professional_look": float (1-10),
    "information_clarity": float (1-10),
    "template_adherence": float (1-10)
  },
  "issues": ["list of specific visual problems"],
  "suggestions": ["list of specific improvements"]
}

Scoring guide:
- 9-10: Publication quality, could be from a top design firm
- 7-8: Professional, clean, would not embarrass in a meeting
- 5-6: Passable but has noticeable issues
- 3-4: Clearly AI-generated, unprofessional
- 1-2: Broken layout, unreadable"""


@dataclass
class VLMResult:
    passed: bool
    overall_score: float
    dimensions: dict[str, float] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


async def _call_vlm(screenshot_paths: list[str]) -> str:
    """Send screenshots to VLM for evaluation."""
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    content = [{"type": "text", "text": "Evaluate these presentation slides:"}]
    for path in screenshot_paths:
        img_data = Path(path).read_bytes()
        b64 = base64.b64encode(img_data).decode("utf-8")
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": b64},
        })

    message = await client.messages.create(
        model=settings.vlm_model,
        max_tokens=2048,
        system=VLM_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )
    return message.content[0].text


async def check_tier2_vlm(html_dir: str, screenshot_paths: list[str]) -> VLMResult:
    """Run VLM visual quality review on presentation screenshots.

    Args:
        html_dir: Path to the rendered HTML directory.
        screenshot_paths: Paths to screenshot images of each slide.

    Returns:
        VLMResult with pass/fail and detailed scores.
    """
    raw = await _call_vlm(screenshot_paths)

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()

    data = json.loads(cleaned)

    overall = data.get("overall_score", 0)
    return VLMResult(
        passed=overall >= PASS_THRESHOLD,
        overall_score=overall,
        dimensions=data.get("dimensions", {}),
        issues=data.get("issues", []),
        suggestions=data.get("suggestions", []),
    )
```

- [ ] **Step 4: Run tests and verify they pass**

Run: `uv run pytest tests/test_quality_gate.py::test_vlm_passes_good_presentation tests/test_quality_gate.py::test_vlm_fails_bad_presentation -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/quality_gate/tier2_vlm.py tests/test_quality_gate.py
git commit -m "feat: Quality Gate Tier 2 — VLM visual review with scoring"
```

---

### Task 9: Quality Gate — Orchestrator with Auto-Fix Loop

**Files:**
- Create: `backend/quality_gate/gate.py`
- Modify: `tests/test_quality_gate.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_quality_gate.py`:

```python
from backend.quality_gate.gate import QualityGateResult, run_quality_gate


def test_quality_gate_passes_clean_spec():
    spec = PresentationRenderSpec(
        title="Test",
        theme={"accent_primary": "#4f6df5"},
        slides=[
            SlideRenderSpec(slide_index=0, layout="title", heading="Hi", components=[]),
            SlideRenderSpec(
                slide_index=1,
                layout="data_driven",
                heading="Data",
                components=[
                    Component(type="card_grid", props={"columns": 2, "cards": [{"title": "A", "value": "1"}]}),
                    Component(type="highlight_box", props={"text": "Key insight", "color": "green"}),
                ],
            ),
        ],
    )
    result = run_quality_gate(spec, skip_vlm=True)
    assert result.tier1_passed


def test_quality_gate_auto_fixes_bullets():
    spec = PresentationRenderSpec(
        title="Test",
        theme={},
        slides=[
            SlideRenderSpec(
                slide_index=0,
                layout="text",
                heading="Long List",
                components=[
                    Component(type="bullet_list", props={"items": [f"item {i}" for i in range(10)]}),
                ],
            ),
        ],
    )
    result = run_quality_gate(spec, skip_vlm=True)
    # After auto-fix, the bullet list should be split
    fixed = result.fixed_spec
    total_items = 0
    for slide in fixed.slides:
        for comp in slide.components:
            if comp.type == "bullet_list":
                total_items += len(comp.props.get("items", []))
    assert total_items == 10  # all items preserved
    assert result.tier1_passed  # now passes
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_quality_gate.py::test_quality_gate_passes_clean_spec tests/test_quality_gate.py::test_quality_gate_auto_fixes_bullets -v`
Expected: FAIL

- [ ] **Step 3: Implement Quality Gate orchestrator**

```python
# backend/quality_gate/gate.py
"""Quality Gate orchestrator — runs Tier 1 + Tier 2, handles auto-fix loop."""

import copy
from dataclasses import dataclass, field

from backend.schemas.render_spec import (
    PresentationRenderSpec,
    SlideRenderSpec,
    Component,
)
from backend.quality_gate.tier1_rules import check_tier1, Tier1Result, MAX_BULLET_ITEMS


@dataclass
class QualityGateResult:
    tier1_passed: bool
    tier1_result: Tier1Result | None = None
    fixed_spec: PresentationRenderSpec | None = None
    auto_fix_rounds: int = 0


def _auto_fix_tier1(spec: PresentationRenderSpec) -> PresentationRenderSpec:
    """Apply auto-fix rules to resolve Tier 1 issues."""
    spec = PresentationRenderSpec.model_validate(spec.model_dump())  # deep copy
    new_slides: list[SlideRenderSpec] = []

    for slide in spec.slides:
        new_components: list[Component] = []
        extra_slides: list[SlideRenderSpec] = []

        for comp in slide.components:
            if comp.type == "bullet_list":
                items = comp.props.get("items", [])
                if len(items) > MAX_BULLET_ITEMS:
                    # Split into chunks
                    for i in range(0, len(items), MAX_BULLET_ITEMS):
                        chunk = items[i : i + MAX_BULLET_ITEMS]
                        if i == 0:
                            new_components.append(
                                Component(type="bullet_list", props={"items": chunk})
                            )
                        else:
                            extra_slides.append(
                                SlideRenderSpec(
                                    slide_index=len(spec.slides) + len(extra_slides),
                                    layout=slide.layout,
                                    heading=f"{slide.heading} (cont.)",
                                    components=[
                                        Component(type="bullet_list", props={"items": chunk})
                                    ],
                                )
                            )
                else:
                    new_components.append(comp)
            else:
                new_components.append(comp)

        # Add missing highlight_box for data slides
        if slide.layout in {"data_driven", "split_panel", "comparison"}:
            has_highlight = any(c.type == "highlight_box" for c in new_components)
            if not has_highlight:
                new_components.append(
                    Component(
                        type="highlight_box",
                        props={"text": f"Key takeaway for: {slide.heading}", "color": "blue"},
                    )
                )

        slide_copy = SlideRenderSpec(
            slide_index=slide.slide_index,
            layout=slide.layout,
            heading=slide.heading,
            subheading=slide.subheading,
            components=new_components,
            css_overrides=slide.css_overrides,
            speaker_notes=slide.speaker_notes,
        )
        new_slides.append(slide_copy)
        new_slides.extend(extra_slides)

    # Reindex slides
    for i, s in enumerate(new_slides):
        s.slide_index = i

    return PresentationRenderSpec(
        title=spec.title,
        theme=spec.theme,
        slides=new_slides,
        metadata=spec.metadata,
    )


def run_quality_gate(
    spec: PresentationRenderSpec,
    skip_vlm: bool = False,
    max_fix_rounds: int = 3,
) -> QualityGateResult:
    """Run the Quality Gate pipeline with auto-fix loop.

    Args:
        spec: The PresentationRenderSpec to verify.
        skip_vlm: Skip Tier 2 VLM check (for unit tests or cost saving).
        max_fix_rounds: Maximum auto-fix attempts for Tier 1.

    Returns:
        QualityGateResult with final spec and pass/fail status.
    """
    current_spec = spec
    rounds = 0

    for _ in range(max_fix_rounds):
        result = check_tier1(current_spec)
        if result.passed:
            return QualityGateResult(
                tier1_passed=True,
                tier1_result=result,
                fixed_spec=current_spec,
                auto_fix_rounds=rounds,
            )
        rounds += 1
        current_spec = _auto_fix_tier1(current_spec)

    # Final check after all fix rounds
    final_result = check_tier1(current_spec)
    return QualityGateResult(
        tier1_passed=final_result.passed,
        tier1_result=final_result,
        fixed_spec=current_spec,
        auto_fix_rounds=rounds,
    )
```

- [ ] **Step 4: Run tests and verify they pass**

Run: `uv run pytest tests/test_quality_gate.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/quality_gate/gate.py tests/test_quality_gate.py
git commit -m "feat: Quality Gate orchestrator with auto-fix loop"
```

---

### Task 10: PPTX Input Parser

**Files:**
- Create: `backend/input_parser/pptx_parser.py`
- Create: `tests/test_pptx_parser.py`
- Create: `tests/fixtures/sample.pptx` (generated in test setup)

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_pptx_parser.py
import tempfile
from pathlib import Path

import pytest
from pptx import Presentation as PptxPresentation
from pptx.util import Inches

from backend.input_parser.pptx_parser import parse_pptx
from backend.schemas.intent import PresentationIntent


def _create_sample_pptx(path: Path):
    """Create a minimal PPTX file for testing."""
    prs = PptxPresentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Title slide
    layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(layout)
    slide.shapes.title.text = "Q1 Review"
    slide.placeholders[1].text = "Algorithm Team"

    # Content slide
    layout = prs.slide_layouts[1]
    slide = prs.slides.add_slide(layout)
    slide.shapes.title.text = "Key Metrics"
    body = slide.placeholders[1]
    tf = body.text_frame
    tf.text = "GPU utilization: 87%"
    tf.add_paragraph().text = "Model accuracy: 95%"
    tf.add_paragraph().text = "Latency reduced by 40%"

    prs.save(str(path))


def test_parse_pptx_extracts_slides():
    with tempfile.TemporaryDirectory() as tmpdir:
        pptx_path = Path(tmpdir) / "sample.pptx"
        _create_sample_pptx(pptx_path)
        result = parse_pptx(pptx_path)
        assert result["title"] == "Q1 Review"
        assert len(result["slides"]) == 2


def test_parse_pptx_extracts_text():
    with tempfile.TemporaryDirectory() as tmpdir:
        pptx_path = Path(tmpdir) / "sample.pptx"
        _create_sample_pptx(pptx_path)
        result = parse_pptx(pptx_path)
        slide1 = result["slides"][1]
        assert "GPU utilization" in slide1["text_content"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_pptx_parser.py -v`
Expected: FAIL

- [ ] **Step 3: Implement PPTX parser**

```python
# backend/input_parser/pptx_parser.py
"""Parse PPTX files into structured data for PresentationIntent construction."""

from pathlib import Path

from pptx import Presentation as PptxPresentation
from pptx.util import Emu


def parse_pptx(pptx_path: Path) -> dict:
    """Extract structured content from a PPTX file.

    Args:
        pptx_path: Path to the .pptx file.

    Returns:
        Dict with title, slide dimensions, and per-slide extracted content.
        This raw extraction is then passed to an LLM to build a PresentationIntent.
    """
    prs = PptxPresentation(str(pptx_path))
    title = ""
    slides = []

    for i, slide in enumerate(prs.slides):
        slide_data = {
            "index": i,
            "text_content": "",
            "title": "",
            "bullet_points": [],
            "has_chart": False,
            "has_image": False,
            "has_table": False,
            "speaker_notes": "",
        }

        # Extract text from all shapes
        texts = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    text = paragraph.text.strip()
                    if text:
                        texts.append(text)
                        if paragraph.level > 0 or (shape != slide.shapes.title if hasattr(slide.shapes, 'title') else True):
                            slide_data["bullet_points"].append(text)

            if shape.has_chart:
                slide_data["has_chart"] = True
            if shape.shape_type == 13:  # Picture
                slide_data["has_image"] = True
            if shape.has_table:
                slide_data["has_table"] = True

        # Title extraction
        if slide.shapes.title:
            slide_data["title"] = slide.shapes.title.text.strip()
            if i == 0:
                title = slide_data["title"]

        slide_data["text_content"] = "\n".join(texts)

        # Speaker notes
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            slide_data["speaker_notes"] = slide.notes_slide.notes_text_frame.text.strip()

        slides.append(slide_data)

    return {
        "title": title,
        "slide_count": len(slides),
        "slide_width": prs.slide_width,
        "slide_height": prs.slide_height,
        "slides": slides,
    }
```

- [ ] **Step 4: Run tests and verify they pass**

Run: `uv run pytest tests/test_pptx_parser.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/input_parser/pptx_parser.py tests/test_pptx_parser.py
git commit -m "feat: PPTX input parser — extract text, charts, images, notes"
```

---

### Task 11: PDF Export via Playwright

**Files:**
- Create: `backend/renderer/pdf_exporter.py`
- Create: `tests/test_pdf_exporter.py`

- [ ] **Step 1: Add playwright dependency**

Add to pyproject.toml `dependencies`:
```
"playwright>=1.49.0",
```

Run: `uv sync && uv run playwright install chromium`

- [ ] **Step 2: Write the failing tests**

```python
# tests/test_pdf_exporter.py
import tempfile
from pathlib import Path

import pytest

from backend.schemas.render_spec import PresentationRenderSpec, SlideRenderSpec, Component
from backend.renderer.html_renderer import render_presentation
from backend.renderer.pdf_exporter import export_pdf


def _make_spec():
    return PresentationRenderSpec(
        title="PDF Test",
        theme={"accent_primary": "#4f6df5"},
        slides=[
            SlideRenderSpec(slide_index=0, layout="title", heading="Hello PDF", components=[]),
            SlideRenderSpec(
                slide_index=1,
                layout="data_driven",
                heading="Data",
                components=[
                    Component(type="highlight_box", props={"text": "Key insight", "color": "green"}),
                ],
            ),
        ],
    )


@pytest.mark.asyncio
async def test_export_pdf_creates_file():
    spec = _make_spec()
    with tempfile.TemporaryDirectory() as tmpdir:
        html_dir = Path(tmpdir) / "html"
        render_presentation(spec, html_dir)
        pdf_path = Path(tmpdir) / "output.pdf"
        await export_pdf(html_dir, pdf_path)
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0


@pytest.mark.asyncio
async def test_export_pdf_screenshots():
    spec = _make_spec()
    with tempfile.TemporaryDirectory() as tmpdir:
        html_dir = Path(tmpdir) / "html"
        render_presentation(spec, html_dir)
        screenshots_dir = Path(tmpdir) / "screenshots"
        screenshots = await export_pdf(html_dir, Path(tmpdir) / "output.pdf", screenshots_dir=screenshots_dir)
        assert len(screenshots) == 2
        for ss in screenshots:
            assert Path(ss).exists()
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_pdf_exporter.py -v`
Expected: FAIL

- [ ] **Step 4: Implement PDF exporter**

```python
# backend/renderer/pdf_exporter.py
"""Export HTML presentations to PDF via Playwright (per-slide screenshots stitched)."""

from pathlib import Path

from playwright.async_api import async_playwright


async def export_pdf(
    html_dir: Path,
    output_pdf: Path,
    screenshots_dir: Path | None = None,
) -> list[str]:
    """Export an HTML presentation to PDF.

    Takes per-slide screenshots and combines them into a single PDF.
    Also returns screenshot paths for use by Quality Gate Tier 2.

    Args:
        html_dir: Directory containing index.html + assets.
        output_pdf: Path to write the output PDF.
        screenshots_dir: Optional directory for individual slide screenshots.

    Returns:
        List of screenshot file paths (useful for VLM Quality Gate).
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

        # Count slides
        slide_count = await page.locator(".slide").count()

        # Take per-slide screenshots
        for i in range(slide_count):
            slide_selector = f"#slide-{i}"
            slide = page.locator(slide_selector)
            if await slide.count() == 0:
                slide_selector = f".slide:nth-child({i + 1})"
                slide = page.locator(slide_selector)

            if screenshots_dir:
                ss_path = screenshots_dir / f"slide-{i}.png"
                await slide.screenshot(path=str(ss_path))
                screenshot_paths.append(str(ss_path))

        # Generate PDF using Playwright's built-in print
        await page.pdf(
            path=str(output_pdf),
            format="A4",
            landscape=True,
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )

        await browser.close()

    return screenshot_paths
```

- [ ] **Step 5: Run tests and verify they pass**

Run: `uv run pytest tests/test_pdf_exporter.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add backend/renderer/pdf_exporter.py tests/test_pdf_exporter.py pyproject.toml
git commit -m "feat: PDF export via Playwright — per-slide screenshots + combined PDF"
```

---

### Task 12: REST API + CLI — End-to-End Integration

**Files:**
- Create: `backend/api/__init__.py`
- Create: `backend/api/routes.py`
- Modify: `backend/main.py`
- Create: `cli.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: Write integration test**

```python
# tests/test_api.py
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock

import pytest
from fastapi.testclient import TestClient

from backend.main import app

# Mock LLM responses for the full pipeline
MOCK_TEXT_PARSE = '{"title":"Test","context":{"scene":"demo"},"slides":[{"type":"title","heading":"Test"}]}'
MOCK_AGENT = '{"title":"Test","theme":{"accent_primary":"#4f6df5"},"slides":[{"slide_index":0,"layout":"title","heading":"Test","components":[]}]}'


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_generate_from_text():
    with (
        patch("backend.input_parser.text_parser._call_llm", new_callable=AsyncMock, return_value=MOCK_TEXT_PARSE),
        patch("backend.agent.engine._call_llm", new_callable=AsyncMock, return_value=MOCK_AGENT),
    ):
        client = TestClient(app)
        resp = client.post("/api/v1/generate", json={
            "input_type": "text",
            "content": "Make a test presentation",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "presentation_id" in data
        assert data["quality_gate"]["tier1_passed"] is True
```

- [ ] **Step 2: Implement API routes**

```python
# backend/api/__init__.py
```

```python
# backend/api/routes.py
"""REST API routes for PPT-Agent."""

import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel

from backend.config import settings
from backend.input_parser.text_parser import parse_text
from backend.agent.engine import generate_render_spec
from backend.renderer.html_renderer import render_presentation
from backend.quality_gate.gate import run_quality_gate

router = APIRouter(prefix="/api/v1")


class GenerateRequest(BaseModel):
    input_type: str  # "text" or "pptx"
    content: str  # text content or base64 PPTX (for simple text input)
    scene: str | None = None
    audience: str | None = None


class GenerateResponse(BaseModel):
    presentation_id: str
    html_path: str
    quality_gate: dict
    slides_count: int


@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    """Generate a presentation from text input."""
    pres_id = str(uuid.uuid4())[:8]
    output_dir = Path(settings.output_dir) / pres_id

    # Step 1: Parse input → PresentationIntent
    intent = await parse_text(req.content, scene=req.scene, audience=req.audience)

    # Step 2: Agent → PresentationRenderSpec
    render_spec = await generate_render_spec(intent)

    # Step 3: Quality Gate (Tier 1 only for now)
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
```

- [ ] **Step 3: Update main.py to include router**

```python
# backend/main.py
from fastapi import FastAPI
from backend.api.routes import router

app = FastAPI(title="PPT-Agent", version="0.1.0")
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Create CLI entry point**

```python
# cli.py
"""PPT-Agent CLI — generate presentations from the command line."""

import argparse
import asyncio
import sys
from pathlib import Path

from backend.config import settings
from backend.input_parser.text_parser import parse_text
from backend.input_parser.pptx_parser import parse_pptx
from backend.agent.engine import generate_render_spec
from backend.renderer.html_renderer import render_presentation
from backend.quality_gate.gate import run_quality_gate
from backend.schemas.intent import PresentationIntent


async def main():
    parser = argparse.ArgumentParser(description="PPT-Agent: AI Presentation Generator")
    parser.add_argument("input", help="Text content or path to .pptx file")
    parser.add_argument("-o", "--output", default="./output", help="Output directory")
    parser.add_argument("--scene", help="Scene hint (e.g., quarterly_review)")
    parser.add_argument("--audience", help="Audience hint (e.g., VP Engineering)")
    parser.add_argument("--pdf", action="store_true", help="Also export PDF")
    parser.add_argument("--skip-vlm", action="store_true", default=True, help="Skip VLM quality check")
    args = parser.parse_args()

    output_dir = Path(args.output)

    # Step 1: Parse input
    input_path = Path(args.input)
    if input_path.exists() and input_path.suffix == ".pptx":
        print(f"Parsing PPTX: {input_path}")
        pptx_data = parse_pptx(input_path)
        # Convert PPTX data to text for LLM processing
        text_summary = f"Title: {pptx_data['title']}\n"
        for slide in pptx_data["slides"]:
            text_summary += f"\nSlide {slide['index'] + 1}: {slide['title']}\n{slide['text_content']}\n"
        intent = await parse_text(text_summary, scene=args.scene, audience=args.audience)
    else:
        print("Parsing text input...")
        intent = await parse_text(args.input, scene=args.scene, audience=args.audience)

    print(f"Intent: {intent.title} ({len(intent.slides)} slides)")

    # Step 2: Generate render spec
    print("Generating presentation design...")
    render_spec = await generate_render_spec(intent)

    # Step 3: Quality Gate
    print("Running quality checks...")
    qg_result = run_quality_gate(render_spec, skip_vlm=args.skip_vlm)
    final_spec = qg_result.fixed_spec or render_spec
    if qg_result.tier1_passed:
        print(f"Quality Gate: PASSED (auto-fixed {qg_result.auto_fix_rounds} rounds)")
    else:
        print(f"Quality Gate: ISSUES REMAIN")
        for issue in (qg_result.tier1_result.issues if qg_result.tier1_result else []):
            print(f"  - {issue}")

    # Step 4: Render
    html_dir = render_presentation(final_spec, output_dir / "html")
    print(f"HTML output: {html_dir}/index.html")

    # Step 5: PDF export
    if args.pdf:
        from backend.renderer.pdf_exporter import export_pdf
        pdf_path = output_dir / "presentation.pdf"
        print("Exporting PDF...")
        await export_pdf(html_dir, pdf_path)
        print(f"PDF output: {pdf_path}")

    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 5: Run integration test**

Run: `uv run pytest tests/test_api.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add backend/api/ backend/main.py cli.py tests/test_api.py
git commit -m "feat: REST API + CLI — end-to-end text/PPTX to HTML pipeline"
```

---

### Task 13: End-to-End Smoke Test (Manual)

This is a manual verification that the entire pipeline works with real LLM calls.

- [ ] **Step 1: Create .env file with API key**

```bash
echo "ANTHROPIC_API_KEY=your-key-here" > .env
```

- [ ] **Step 2: Run CLI with text input**

```bash
uv run python cli.py "Make a quarterly review for an algorithm team. Key metrics: GPU util 87% (+12%), model accuracy 95%, latency reduced 40%. Achievements: launched model v3, built auto-labeling pipeline." --output ./output/test1 --scene quarterly_review --audience "VP Engineering"
```

Expected: HTML files in `./output/test1/html/`

- [ ] **Step 3: Open in browser and verify**

```bash
open ./output/test1/html/index.html
```

Expected: Multi-slide presentation with proper styling, navigation, and components.

- [ ] **Step 4: Test PDF export**

```bash
uv run python cli.py "Quick demo: 3 slides about AI trends" --output ./output/test2 --pdf
```

Expected: `./output/test2/presentation.pdf` exists and looks correct.

- [ ] **Step 5: Test PPTX input (if you have a sample PPTX)**

```bash
uv run python cli.py ./path/to/sample.pptx --output ./output/test3
```

Expected: Redesigned HTML presentation based on PPTX content.

- [ ] **Step 6: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests PASS

- [ ] **Step 7: Commit any fixes from smoke testing**

```bash
git add -A
git commit -m "fix: smoke test fixes for end-to-end pipeline"
```

---

## Dependency Graph

```
Task 1 (Scaffolding) ──────────────────────────────────┐
Task 2 (IR Contract) ─────────┬────────────────────────┤
                               │                        │
Task 3 (HTML Renderer Static) ─┤                        │
Task 4 (HTML Renderer Engine) ─┤                        │
                               │                        │
Task 5 (Text Parser) ──────────┤                        │
Task 6 (Agent Engine) ─────────┤                        │
                               │                        │
Task 7 (QG Tier 1) ────────────┤                        │
Task 8 (QG Tier 2) ────────────┤                        │
Task 9 (QG Orchestrator) ──────┤                        │
                               │                        │
Task 10 (PPTX Parser) ─────────┤                        │
Task 11 (PDF Export) ───────────┤                        │
                               │                        │
Task 12 (API + CLI) ◄──────────┘                        │
Task 13 (Smoke Test) ◄─────────────────────────────────┘
```

Tasks 3-4, 5-6, 7-9, 10, 11 can be parallelized across subagents after Tasks 1-2 complete.
