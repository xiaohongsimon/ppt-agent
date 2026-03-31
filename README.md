# PPT-Agent

AI-powered presentation generation platform. Feed it text or an old PPTX — get back a polished, professional HTML presentation with automatic quality checks.

## Features

- **Multi-format input** — text/outline, PPTX file upload, screenshots (planned)
- **Quality Gate** — rule-based + VLM visual review, auto-fix loop before delivery
- **PDF export** — Playwright-based, pixel-perfect
- **Self-improvement loop** — feed it excellent PPTs, it learns and gets better automatically
- **HTML-first output** — scroll-snap navigation, responsive, offline-capable, keyboard shortcuts

## Quick Start

```bash
# 1. Clone
git clone https://github.com/leehom/ppt-agent.git
cd ppt-agent

# 2. Install (requires Python 3.11+ and uv)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# 3. Install Playwright browser
uv run playwright install chromium

# 4. Configure API key
cp .env.example .env
# Edit .env with your API key

# 5. Generate a presentation
uv run python cli.py "Q1算法团队述职：GPU利用率87%，模型准确率95%，延迟降低40%" \
  --output ./output/demo --scene quarterly_review

# 6. Open in browser
open ./output/demo/html/index.html
```

## Usage

### CLI

```bash
# Text input
uv run python cli.py "你的PPT内容描述" --output ./output/my-ppt

# PPTX input (redesign an existing PPT)
uv run python cli.py ./path/to/old.pptx --output ./output/redesigned

# With PDF export
uv run python cli.py "内容" --output ./output/my-ppt --pdf

# Specify scene and audience
uv run python cli.py "内容" --scene quarterly_review --audience "VP Engineering"
```

### REST API

```bash
# Start server
uv run uvicorn backend.main:app --reload --port 8000

# Generate
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"input_type": "text", "content": "Make a quarterly review presentation"}'
```

### Self-Improvement Training

Feed excellent PPTs to automatically improve generation quality:

```bash
# 1. Install dependencies for PPTX → screenshot conversion
brew install poppler libreoffice

# 2. Put excellent PPTs in corpus
cp ~/best-ppts/*.pptx ./backend/trainer/data/corpus/

# 3. Evaluate current quality (no prompt changes)
uv run python train.py --eval-only

# 4. Run 3 rounds of self-improvement
uv run python train.py --rounds 3

# 5. View progress
uv run python train.py --history
```

Each round: parse originals → regenerate → VLM compare → aggregate feedback → optimize prompt → repeat.

## Architecture

```
Text/PPTX → Input Parser → Agent Engine → Quality Gate → HTML Renderer → PDF Export
                                ↕
                          Template Library
                          User Profile (planned)
```

| Module | What it does |
|--------|-------------|
| Input Parser | Text, PPTX → unified PresentationIntent JSON |
| Agent Engine | LLM converts intent → SlideRenderSpec (render-ready) |
| Quality Gate | Tier 1 rules (ms) + Tier 2 VLM review (s) + auto-fix |
| HTML Renderer | Jinja2 templates + CSS design system → standalone HTML |
| PDF Exporter | Playwright screenshots → PDF |
| Trainer | Self-play loop: corpus → regen → compare → optimize prompt |

## Configuration

Copy `.env.example` to `.env` and fill in:

```bash
# Direct Anthropic API
ANTHROPIC_API_KEY=sk-ant-...

# Or via proxy/gateway (e.g., Zenmux)
ANTHROPIC_API_KEY=sk-...
ANTHROPIC_BASE_URL=https://your-gateway.com/api/anthropic
LLM_MODEL=anthropic/claude-sonnet-4.5
VLM_MODEL=anthropic/claude-sonnet-4.5
```

## Development

```bash
# Run tests (71 tests)
uv run pytest -v

# Lint
uv run ruff check .

# Run server with hot reload
uv run uvicorn backend.main:app --reload
```

## Project Structure

```
ppt-agent/
├── backend/
│   ├── api/routes.py              # REST API
│   ├── agent/engine.py            # LLM agent (Intent → RenderSpec)
│   ├── input_parser/
│   │   ├── text_parser.py         # Text → Intent
│   │   └── pptx_parser.py        # PPTX → structured data
│   ├── quality_gate/
│   │   ├── tier1_rules.py        # Rule-based checks
│   │   ├── tier2_vlm.py          # VLM visual review
│   │   └── gate.py               # Orchestrator + auto-fix
│   ├── renderer/
│   │   ├── html_renderer.py      # RenderSpec → HTML
│   │   ├── pdf_exporter.py       # HTML → PDF
│   │   ├── static/style.css      # Design system
│   │   ├── static/slides.js      # Navigation
│   │   └── templates/            # Jinja2 templates
│   ├── trainer/                  # Self-improvement loop
│   │   ├── loop.py               # Training orchestrator
│   │   ├── corpus.py             # PPTX corpus loader
│   │   ├── comparator.py         # VLM side-by-side comparison
│   │   ├── feedback.py           # Feedback aggregation
│   │   ├── optimizer.py          # Prompt auto-optimization
│   │   └── report.py             # Training reports
│   └── schemas/
│       ├── intent.py             # IR input contract
│       └── render_spec.py        # IR output contract
├── cli.py                        # CLI entry point
├── train.py                      # Training CLI
└── tests/                        # 71 tests
```

## Roadmap

- [x] Core pipeline (text/PPTX → HTML → QA → PDF)
- [x] Self-improvement training loop
- [ ] Two-Stage Best-of-2 (generate 2 versions, user picks)
- [ ] Web UI (React + Tailwind)
- [ ] Template Library (Super Skeletons: 5 layouts × 20 themes)
- [ ] User Profile Engine (learns your style preferences)
- [ ] PPTX export
- [ ] Screenshot input (photo of slides → redesign)

## License

MIT
