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
Input Parser -> Agent Engine -> HTML Renderer -> Quality Gate -> PDF Export
IR contracts: backend/schemas/intent.py (input), backend/schemas/render_spec.py (output)
