# PPT-Agent: AI-Powered Presentation Generation Platform

**Date:** 2026-03-31
**Status:** Revised — Post multi-model debate (5 models: Opus, Grok 4, Gemini 3.1, Kimi K2.5, Qwen-3.5-Plus)
**Author:** leehom + Claude

## 1. Vision & Positioning

### One-liner
An open-source, AI-powered presentation platform that generates high-quality HTML presentations through agentic workflows, learns from every user interaction, and builds an ever-growing knowledge moat.

### Why now
- AI PPT market: $2B (2025) → $10B (2033), 25% CAGR
- Every existing tool has the same fatal flaw: generates "looks okay" slides that embarrass you in front of your boss
- No tool solves the **iteration problem** — presentations are refined 5-10 times before delivery, yet all tools optimize for one-shot generation
- Open-source space is early: Presenton (4.5k stars), PPTAgent (3.9k stars) — room for a differentiated player

### Core differentiators
1. **Quality Gate** — AI doesn't just generate, it self-reviews and auto-fixes before delivery
2. **Two-Stage Best-of-2** — lightweight outline+preview comparison first, full generation only for the winner; "recommended + alternative" UI reduces decision fatigue while collecting preference data
3. **Living knowledge base** — templates, user profiles, and design knowledge compound over time
4. **PPTX/Screenshot input** — "upload your ugly PPT, get a beautiful one back"
5. **HTML preview + PDF/PPTX export** — best-in-class rendering flexibility with enterprise-compatible output

## 2. Target Users

**Primary:** Non-technical professionals — PMs, managers, TLs, operations, marketing, executives
**Secondary:** Technical leads who need to present to non-technical stakeholders
**Tertiary:** Developers building PPT generation into their own workflows (API/SDK, Phase 3)

**User personas:**

| Persona | Need | Frequency |
|---------|------|-----------|
| Team Lead doing weekly report | Fast, consistent, data-driven slides | Weekly |
| Manager doing quarterly review | Polished storytelling, executive-ready | Quarterly |
| Trainer creating learning materials | Interactive, engaging, visual-heavy | Monthly |
| IC preparing tech sharing | Code-friendly, diagram-heavy | Ad-hoc |

## 3. System Architecture

### 3.1 High-level overview

> **Post-debate revision:** Architecture updated based on 5-model debate consensus.
> Key changes: Agent Engine split (+ Session Manager), HTML as preview layer with PDF/PPTX export,
> Two-Stage Best-of-2, Super Skeletons cold start strategy.

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web UI (React + Tailwind)                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ Input     │  │ Iteration│  │ Live      │  │ Template       │  │
│  │ Panel     │  │ Chat     │  │ Preview   │  │ Browser        │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬─────────┘  │
└───────┼──────────────┼──────────────┼──────────────┼────────────┘
        │              │              │              │
┌───────▼──────────────▼──────────────▼──────────────▼────────────┐
│                      API Gateway (FastAPI)                        │
└──┬──────────┬──────────┬──────────┬──────────┬──────────┬───────┘
   │          │          │          │          │          │
┌──▼───┐ ┌───▼────┐ ┌───▼───┐ ┌───▼────┐ ┌───▼───┐ ┌───▼──────┐
│Input │ │Session │ │Agent  │ │Quality │ │HTML   │ │User      │
│Parser│ │Manager │ │Engine │ │Gate    │ │Render │ │Profile   │
│      │ │        │ │       │ │        │ │+ PDF  │ │Engine    │
│      │ │• 会话  │ │PPTAgent│ │        │ │Export │ │          │
│• 文本│ │  管理  │ │fork   │ │3-tier  │ │       │ │• 画像    │
│• PDF │ │• 迭代  │ │       │ │verify  │ │• HTML │ │• 偏好    │
│• PPTX│ │  编排  │ │20+工具│ │        │ │• PDF  │ │• diff    │
│• 截图│ │• 多轮  │ │sandbox│ │        │ │(Pupp.)│ │  学习    │
│• 语音│ │  上下文│ │MCP    │ │        │ │• PPTX │ │          │
└──────┘ └────────┘ └───┬───┘ └────────┘ │(P2)  │ └──────────┘
                        │                └───────┘
                  ┌─────▼──────┐
                  │Template    │
                  │Library     │
                  │(Super      │
                  │ Skeletons) │
                  └────────────┘
```

### 3.2 Module specifications

#### Module 1: Input Parser

**Purpose:** Accept any input format and convert to a unified structured representation.

**Supported inputs:**

| Input type | Processing pipeline | Tech |
|------------|-------------------|------|
| Text / outline | LLM structuring → JSON | LLM API |
| PDF document | MinerU / PyMuPDF → text extraction → LLM structuring | Python |
| PPTX file | python-pptx → extract text, charts, images, layout, colors + VLM screenshot analysis → merge | python-pptx + VLM |
| Screenshot(s) | VLM analysis → extract content structure + design intent + issues | Claude/GPT-4o vision |
| Voice (Phase 2) | Whisper → text → LLM structuring | Whisper API |

**Unified output format (Presentation Intent JSON):**

```json
{
  "title": "Q1 2026 Algorithm Team Review",
  "context": {
    "scene": "quarterly_review",
    "audience": "VP Engineering",
    "tone": "data-driven, concise"
  },
  "slides": [
    {
      "type": "title",
      "heading": "...",
      "subheading": "..."
    },
    {
      "type": "data_driven",
      "heading": "...",
      "key_metrics": [...],
      "chart_data": {...},
      "takeaway": "..."
    }
  ],
  "source_analysis": {
    "from_pptx": { "strengths": [...], "issues": [...] },
    "from_screenshot": { "design_intent": "...", "improvement_areas": [...] }
  },
  "user_profile_hints": {
    "preferred_style": "minimal-data",
    "audience_preferences": "likes ROI numbers"
  }
}
```

**PPTX input deep-dive:**

When a user uploads a .pptx file, the system performs dual-path analysis:

1. **Structural extraction** (python-pptx):
   - Text content with hierarchy (title, subtitle, body, bullet levels)
   - Chart data (raw values from bar/pie/line charts)
   - Images (extract and save)
   - Layout metadata (slide dimensions, placeholder positions)
   - Color scheme and font information
   - Speaker notes

2. **Visual understanding** (VLM):
   - Render each slide as image → send to VLM
   - Extract: visual intent, design quality assessment, specific issues
   - Identify: what works (keep) vs what's broken (fix)

3. **Merge**: Structural data provides accuracy; VLM provides design judgment. Agent uses both to decide what to preserve and what to redesign.

#### Module 2: Agent Engine (PPTAgent fork)

**Purpose:** The "brain" — understands user intent, plans narrative structure, orchestrates generation, handles multi-turn iteration.

**Base:** Fork of [icip-cas/PPTAgent](https://github.com/icip-cas/PPTAgent) (3.9k stars, EMNLP 2025, MIT license)

**What we keep from PPTAgent:**
- Agentic framework with tool sandbox (20+ built-in tools)
- Two-stage generation approach (plan → generate → edit)
- MCP (Model Context Protocol) server support
- Context management for long presentations

**What we replace/extend:**
- **Output pipeline**: Replace PPTX renderer with HTML renderer + PDF export (Puppeteer)
- **New tools**: Template Library query, User Profile lookup, Quality Gate invocation (`quality_check` tool called by Agent, not a callback — keeps single-direction dependency), Design Knowledge query
- **Two-Stage Best-of-2 orchestration**: Agent generates 2 lightweight outlines + 1-2 page visual previews first; only the winner proceeds to full generation (saves ~50% LLM cost vs full dual-track)
- **Iteration handling**: Managed by Session Manager (split from Agent Engine to avoid "god module" — see debate revision). Agent focuses on single generation/edit execution.

> **Debate revision (Opus):** Agent Engine was a "god module" handling intent, narrative, dual-track, iteration, and tools. Split out Session Manager for multi-turn context and iteration orchestration. Agent Engine now handles single-generation execution only.

**Agent workflow (revised — Two-Stage Best-of-2):**

```
1. Session Manager receives Presentation Intent JSON from Input Parser
2. Session Manager queries User Profile → understand personal/audience preferences
3. Agent Engine queries Template Library → find top matching templates
4. STAGE 1 — Lightweight comparison (fast, cheap):
   a. Agent generates 2 different narrative outlines + CSS theme
   b. Agent renders 1-2 preview slides per outline (title + key content page only)
   c. Both previews pass Tier 1 Quality Gate (rule checks only)
   d. Web UI shows "Recommended" version (based on User Profile) + collapsed "Alternative style"
   e. User picks one → record choice → update User Profile + Template scores
5. STAGE 2 — Full generation (only for winner):
   a. Agent generates all slides for selected outline
   b. Full Quality Gate (Tier 1 + Tier 2 + Tier 3)
   c. Auto-fix if rejected (max 3 rounds)
   d. Deliver to user with quality score
6. Session Manager handles iteration loop (user requests → Agent edits → QG → preview)
```

> **Debate revision (Gemini):** Two-Stage Best-of-2 reduces LLM cost by ~40-50% compared to full dual-track generation. The comparison happens at the outline+preview level, not full presentation level.
> **Debate revision (Kimi):** UI shows "Recommended + Alternative" instead of equal side-by-side, reducing decision fatigue for non-technical users.

**LLM strategy:**

| Task | Model | Reason |
|------|-------|--------|
| Content generation | Claude Opus / GPT-4o | Best quality for narrative |
| Visual QA | Claude with vision / GPT-4o | Multimodal needed |
| Iteration edits | Claude Sonnet / GPT-4o-mini | Fast enough, cheaper |
| Template matching | Embedding model + local | Low latency, no cost |

#### Module 3: Quality Gate Engine

**Purpose:** Ensure every slide meets professional standards before user sees it. The difference between "AI-generated" and "professionally made."

**Three-tier verification:**

**Tier 1: Rule-based checks (milliseconds, automated)**

| Check | Rule | Auto-fix |
|-------|------|----------|
| Content overflow | Text must not exceed container bounds | Reduce font size or split content |
| Font hierarchy | Max 3 font sizes per slide, logical hierarchy | Normalize to design system |
| Alignment | Elements must snap to grid (8px grid system) | Auto-snap |
| Color contrast | WCAG AA minimum (4.5:1 for text) | Adjust colors |
| Information density | Max 7 bullet points, max 40 words per point | Split into two slides |
| Chart readability | Labels must not overlap, axes must be labeled | Adjust spacing/font |
| Whitespace | Minimum 10% margin on all sides | Adjust layout |

**Tier 2: VLM visual review (seconds, AI-powered)**

- Render each slide as screenshot → send to VLM
- Scoring dimensions (each 1-10):
  - **Visual harmony**: Do colors, fonts, spacing work together?
  - **Professional look**: Would this pass as human-made?
  - **Information clarity**: Can you understand the key message in 3 seconds?
  - **Template adherence**: Does it match the selected template's intent?
- Overall score = weighted average
- **Pass threshold**: 7.0/10 per slide, 7.5/10 overall
- If fail → generate specific fix instructions → Agent auto-fixes → re-check

**Tier 3: User Profile alignment (fast, rule-based)**

- Compare generated output against user's historical preferences
- Flag deviations: "This user always uses blue accent, but we generated green"
- Suggest adjustments to match audience preferences

**Auto-fix loop:**

```
Generate → Tier 1 check
  → Fail? → Auto-fix rules → Re-check (max 3 rounds)
  → Pass → Tier 2 VLM check
    → Fail? → Agent receives fix instructions → Regenerate specific slides → Re-check (max 2 rounds)
    → Pass → Tier 3 Profile check
      → Deviations? → Apply adjustments
      → Done → Deliver to user with quality score
```

**Quality knowledge accumulation:**
- Every failure + fix pair → stored in Design Knowledge Base
- Pattern detection: "slides with >5 metrics always fail overflow check" → proactive rule
- Weekly aggregation: top 10 most common issues → feed back to Agent as generation constraints

#### Module 4: HTML Renderer

**Purpose:** Convert Agent output to high-quality, standalone HTML presentations.

**Base:** User's proven `presentation-as-code` design system (validated with 40 non-technical legal professionals).

**Architecture:**
```
presentation-output/
  index.html            # Entry point, loads modules
  00-opening.html       # Each section = standalone HTML module
  01-section-a.html
  02-section-b.html
  ...
  style.css             # Design system (CSS variables)
  slides.js             # Navigation (~77 lines, zero dependencies)
  assets/               # Charts, images, icons
```

**Design system (CSS variables):**
```css
:root {
  /* Accent palette — overridden per template */
  --accent-blue: #4f6df5;     --accent-purple: #7c3aed;
  --accent-green: #10b981;    --accent-orange: #f59e0b;
  --accent-red: #ef4444;      --accent-pink: #db2777;

  /* Typography */
  --heading: #1a202c;
  --text: #2d3748;
  --text-muted: #718096;
  --bg: #ffffff;

  /* Spacing (8px grid) */
  --space-xs: 4px;  --space-sm: 8px;  --space-md: 16px;
  --space-lg: 24px; --space-xl: 32px; --space-2xl: 48px;
}
```

**Component library (proven in production):**
- `.tag` — Module identifier (colored pill)
- `.card` — Information blocks (white bg, accent border, shadow)
- `.highlight-box` — Key takeaway (colored bg + left border)
- `.badge` — Inline labels
- `.bar-chart` — Horizontal comparison with gradient fills
- `.flow` — Sequential steps with arrows
- `.card-grid.cols-N` — CSS grid layout
- `.quote-box` — Citations
- Phone/terminal mockups (CSS-only, no images)

**Key principles (learned from failures):**
- Offline-first: zero CDN dependencies
- Multi-file per module, not single monolith
- Light theme with color accents (dark theme failed with non-tech audiences)
- Scroll-snap + keyboard navigation
- One gradient-text title per slide maximum
- Every slide must have a highlight-box with key takeaway
- Works at 768px width (mobile responsive)

**Template parameterization:**
Templates are HTML files with CSS variable slots. Changing a template = swapping CSS variable values + component layout, not rewriting HTML structure.

**Export pipeline (debate revision — all 5 models flagged HTML-only as #1 risk):**

> HTML is the preview/editing layer. Final delivery supports PDF (P0 MVP) and PPTX (Phase 2).

| Format | How | When | Use case |
|--------|-----|------|----------|
| HTML (preview) | Native rendering in Web UI | Always | Real-time editing, live preview |
| PDF export | Puppeteer headless screenshot of HTML slides | P0 (MVP) | Email attachment, DingTalk/Feishu sharing, archival |
| PPTX export | python-pptx reconstruction from IR | Phase 2 | Enterprise editing workflow |

```
HTML Renderer → Puppeteer → PDF (P0)
                            ↓
IR (JSON) → python-pptx → PPTX (Phase 2)
```

#### Module 5: Template Library

**Purpose:** A comprehensive, ever-growing collection of presentation templates — the platform's core asset and competitive moat.

**Taxonomy:**

```
Templates are tagged along 3 axes:
├── Scene:    quarterly_review | weekly_report | training | proposal |
│             competitive_analysis | okr | product_launch | tech_sharing |
│             incident_review | onboarding | ...
├── Industry: tech | finance | education | healthcare | government | ...
└── Style:    minimal | data_driven | narrative | visual_impact |
              corporate | creative | academic | ...
```

**Template structure:**

```json
{
  "id": "tmpl_quarterly_tech_data",
  "name": "Data-Driven Quarterly Review",
  "tags": {
    "scene": "quarterly_review",
    "industry": "tech",
    "style": "data_driven"
  },
  "files": {
    "html_template": "templates/quarterly-data/template.html",
    "css_variables": "templates/quarterly-data/variables.css",
    "preview_image": "templates/quarterly-data/preview.png",
    "thumbnail": "templates/quarterly-data/thumb.png"
  },
  "metadata": {
    "slide_count_range": [8, 15],
    "recommended_for": ["team_leads", "managers"],
    "usage_count": 1247,
    "avg_rating": 8.3,
    "created_by": "community" | "system" | "ai_derived",
    "variants": ["tmpl_quarterly_tech_data_v2_blue", "tmpl_quarterly_tech_data_v2_dark"]
  }
}
```

**Cold start strategy — Super Skeletons (debate revision, Gemini):**

> Instead of hand-crafting 30 complete templates, we craft 5 structural skeletons × AI-generate 20+ theme packs = 100+ high-quality combinations instantly.

**Step 1: 5 Super Skeletons (hand-crafted, production-quality)**

| Skeleton | Layout | Best for |
|----------|--------|----------|
| `minimal` | Title + 3-5 bullet points + highlight box | Weekly reports, quick updates |
| `data-driven` | Title + chart area + key metrics grid + takeaway | Quarterly reviews, OKR |
| `split-panel` | Left text + right visual (chart/image/mockup) | Training, tech sharing |
| `full-visual` | Full-bleed image/chart with overlay text | Product launches, executive keynotes |
| `comparison` | Side-by-side columns + diff highlights | Competitive analysis, A/B results |

**Step 2: AI Theme Generation**
- VLM crawls top design references (Stripe, Apple, Notion, Linear, etc.) → extract color palettes, typography ratios, spacing relationships
- Each extraction → CSS Variables theme pack
- 5 skeletons × 20 themes = **100 template combinations** at launch
- Each combination auto-verified through Quality Gate (score >= 7.5)

**Growth mechanisms:**

| Channel | How | When |
|---------|-----|------|
| **AI theme generation** | VLM extracts visual DNA from design references → CSS theme packs | Phase 1 (MVP cold start) |
| Manual skeleton curation | Team designs new structural skeletons | Phase 1 ongoing |
| Web crawling | Scrape Dribbble/Behance/SlidesCarnival → VLM analysis → new skeletons + themes | Phase 2 |
| Community contribution | Users/designers upload → review pipeline → publish | Phase 2 |
| AI derivation | High-rated combos → AI generates variants | Phase 2 |
| Best-of-2 learning | Losing version analyzed for what didn't work → improve templates | Continuous |

**Ranking algorithm:**
```
score = 0.4 * avg_user_rating
      + 0.3 * win_rate_in_best_of_2
      + 0.2 * usage_frequency_normalized
      + 0.1 * recency_bonus
```

Templates below score threshold for 30 days → auto-archived (not deleted).

#### Module 6: User Profile Engine

**Purpose:** Build a deep understanding of each user — not just preferences, but behavioral patterns — so the system gets better with every interaction.

**Profile data model:**

```json
{
  "user_id": "usr_001",
  "basic": {
    "role": "Algorithm Team Lead",
    "industry": "tech",
    "team_size": 40,
    "primary_audience": ["VP Engineering", "CTO"]
  },
  "style_preferences": {
    "color_tendency": { "blue": 0.6, "green": 0.25, "purple": 0.15 },
    "info_density": "concise",       // learned from choices
    "viz_preference": "chart_heavy", // learned from iterations
    "layout_preference": "structured_cards",
    "font_size_preference": "large"  // learned from iteration diffs
  },
  "audience_profiles": {
    "vp_engineering": {
      "likes": ["ROI numbers", "team efficiency metrics", "action items"],
      "dislikes": ["too much technical detail", "walls of text"],
      "attention_span": "short"
    }
  },
  "iteration_patterns": {
    "common_additions": ["data charts", "key takeaway boxes"],
    "common_removals": ["background context slides", "agenda slides"],
    "common_edits": ["reduce text per slide", "add specific numbers"]
  },
  "org_shared": {
    "brand_colors": ["#1a73e8", "#34a853"],
    "logo_url": "/assets/org/logo.svg",
    "standard_chart_style": "minimal_grid"
  },
  "best_of_2_history": [
    {
      "timestamp": "2026-03-15T10:30:00Z",
      "winner_template": "tmpl_quarterly_tech_data",
      "loser_template": "tmpl_quarterly_tech_narrative",
      "context": "quarterly_review"
    }
  ]
}
```

**Learning mechanisms:**

1. **Explicit preferences**: User sets in profile (role, audience, brand colors)
2. **Best-of-2 choices**: Which version wins → update template scores + style tendency vectors
3. **Iteration diff analysis**: What did user change after generation?
   - Added a chart → increase `viz_preference` toward `chart_heavy`
   - Deleted 3 text-heavy slides → increase `info_density` toward `concise`
   - Changed blue to green → update `color_tendency`
4. **Cross-session patterns**: Over 10+ uses, detect stable patterns vs one-off deviations

**Privacy design:**
- All user data stored locally (no cloud sync in open-source version)
- Explicit opt-in for data collection
- User can export/delete their profile at any time
- Organization-level profiles require admin consent

## 4. Two-Stage Best-of-2 Competition Mechanism

> **Debate revision:** Redesigned from full dual-track to two-stage approach based on Gemini (cost reduction) and Kimi (UX improvement) feedback. All 5 models flagged the original full-dual-track as too expensive and slow.

This is a first-class architectural concept, not a feature bolted on.

### How it works (Two-Stage)

```
STAGE 1 — Lightweight comparison (~15s, ~30% of full generation cost)
  User request arrives
  → Agent creates 2 generation strategies (meaningfully different)
  → For each: generate narrative outline + 1-2 preview slides (title + key content only)
  → Tier 1 Quality Gate on previews
  → Web UI presents "Recommended + Alternative":
      ┌─────────────────────────────────────────────────┐
      │  ★ Recommended (based on your preferences)       │
      │  ┌─────────────────────────────────────────────┐ │
      │  │ [Title slide preview] [Key content preview] │ │
      │  │ Outline: 12 slides, data-driven narrative   │ │
      │  │ Score: 8.5                                  │ │
      │  │                      [Use This →]           │ │
      │  └─────────────────────────────────────────────┘ │
      │                                                   │
      │  ▸ See alternative style                          │
      │    (collapsed — click to expand)                  │
      │  ┌─────────────────────────────────────────────┐ │
      │  │ [Title preview] [Content preview]           │ │
      │  │ Outline: 8 slides, storytelling narrative   │ │
      │  │ Score: 8.2                                  │ │
      │  │                      [Use This Instead]     │ │
      │  └─────────────────────────────────────────────┘ │
      └─────────────────────────────────────────────────┘

STAGE 2 — Full generation (only for selected version, ~45s)
  → Agent generates all slides for chosen outline
  → Full Quality Gate (Tier 1 + 2 + 3)
  → Auto-fix loop if needed
  → Deliver with quality score
  → Enter iteration mode
```

### Strategy selection for 2 paths

Same as before — Agent picks 2 **meaningfully different** strategies:

| Differentiation axis | Example |
|---------------------|---------|
| Skeleton | data-driven vs split-panel |
| Theme | minimal-blue vs visual-impact-gradient |
| Narrative arc | Metrics-first vs Problem-solution |
| Information density | Concise (8 slides) vs Detailed (15 slides) |

The Agent uses User Profile history to:
- Pre-rank the "Recommended" version (the one most aligned with user's past choices)
- Avoid showing styles the user has consistently rejected

### When NOT to use Two-Stage Best-of-2

- Iteration edits (user says "change slide 3") → single path, direct edit
- User explicitly requests a specific template → single path
- "Emergency mode" (Kimi suggestion): user says "just give me the best one fast" → single path, recommended only

### Cost comparison

| Approach | LLM calls | Latency | User decisions |
|----------|-----------|---------|----------------|
| Full dual-track (original) | 2x full | ~120s | 1 (side-by-side) |
| **Two-Stage (revised)** | **1.3x** (2 outlines + 1 full) | **~60s** | **1 (recommended + alt)** |
| Single path | 1x | ~45s | 0 |

### Data value

Every choice still generates rich learning data:
- Template A vs B preference signal → template ranking
- Style preference signal → user profile
- Context-specific data → "for quarterly reviews, this user prefers data-driven"
- Aggregate data → "across all users, data-driven wins 67% for quarterly reviews"
- **New signal**: Whether user expanded "alternative" at all → measures curiosity/uncertainty

## 5. Self-Evolution Mechanisms

### 5.1 Three knowledge systems

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ Template     │     │ User Profile │     │ Design       │
│ Library      │     │ Engine       │     │ Knowledge    │
│              │     │              │     │ Base         │
│ "What works" │     │ "Who you are"│     │ "How to do   │
│              │     │              │     │  it right"   │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                    ┌───────▼────────┐
                    │ Agent Engine   │
                    │ queries all 3  │
                    │ before every   │
                    │ generation     │
                    └────────────────┘
```

### 5.2 Evolution channels

| Channel | What it feeds | Frequency |
|---------|---------------|-----------|
| Best-of-2 choices | Template ranking + User preferences | Every generation |
| Iteration diffs | User behavior patterns + Design rules | Every edit |
| Quality Gate failures | Design Knowledge (anti-patterns) | Every check |
| Web crawling (Phase 2) | Templates + Design trends | Weekly |
| Community uploads (Phase 2) | Templates | Continuous |
| AI auto-derivation (Phase 2) | Template variants | Monthly |

### 5.3 Feedback loop

```
Generate → Quality Gate → User sees result → User iterates
    ↑                                              │
    │         ┌────────────────────────────────────┘
    │         │
    │         ▼
    │    Diff analysis:
    │    ├── What changed? → User Profile update
    │    ├── Was it a quality issue? → Design KB update
    │    └── Did user switch template? → Template ranking update
    │         │
    └─────────┘ (next generation is better)
```

## 6. Monetization Strategy

### 6.1 Revenue model

```
┌─────────────────────────────────────────────────────┐
│              Free (Open Source Core)                  │
│  • Basic generation (3 presentations/day)            │
│  • Community templates                               │
│  • Local deployment with own API keys                │
│  • Single-path generation (no Best-of-2)             │
├─────────────────────────────────────────────────────┤
│              Pro ($9-15/month individual)             │
│  • Unlimited generation                              │
│  • Best-of-2 competition                             │
│  • Full template library access                      │
│  • User Profile + personalization                    │
│  • Priority model access                             │
│  • PPTX export (Phase 2)                             │
├─────────────────────────────────────────────────────┤
│              Team ($25/user/month)                    │
│  • Everything in Pro                                 │
│  • Organization brand kit                            │
│  • Team-shared user profiles                         │
│  • Admin dashboard                                   │
│  • Collaboration features                            │
├─────────────────────────────────────────────────────┤
│              Enterprise (custom pricing)              │
│  • Private deployment                                │
│  • SSO / LDAP integration                            │
│  • Custom model hosting (on-prem LLM)                │
│  • SLA + dedicated support                           │
│  • API/SDK access                                    │
│  • Custom template design service                    │
└─────────────────────────────────────────────────────┘
```

### 6.2 Template Marketplace (Phase 2)

- Designers upload premium templates
- Platform takes 30% commission
- Designers earn recurring revenue from usage
- Creates a creator ecosystem (supply-side moat)

### 6.3 API/SDK (Phase 3)

- Per-call pricing for developers embedding PPT generation in their products
- Use case: SaaS tools that need "export as presentation" feature
- Revenue scales with platform adoption

### 6.4 Data flywheel as moat

```
More users → More Best-of-2 data → Better template ranking
  → Higher quality output → More users → ...

More templates → Better matching → Higher satisfaction
  → More designers contribute → More templates → ...

Deeper user profiles → Better personalization → Higher retention
  → More usage data → Deeper profiles → ...
```

Three flywheels spinning simultaneously. Late entrants can copy the code but not the accumulated data.

## 7. Technical Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| **Frontend** | React + Tailwind CSS | Largest ecosystem, template components reusable |
| **Backend** | FastAPI (Python) | Same language as PPTAgent, best AI/ML ecosystem |
| **Agent framework** | PPTAgent fork | Agentic architecture, MCP support, EMNLP-backed |
| **HTML renderer** | Custom (presentation-as-code) | Proven in production, validated design system |
| **LLM (content)** | Claude Opus / GPT-4o | Best narrative quality |
| **VLM (visual QA)** | Claude Vision / GPT-4o Vision | Multimodal slide review |
| **LLM (iteration)** | Claude Sonnet / GPT-4o-mini | Fast + cheap for edits |
| **Embedding** | Local model (e5-large / bge) | Template matching, zero API cost |
| **Database** | SQLite (MVP) → PostgreSQL | Light start, proven migration path |
| **Vector store** | ChromaDB (MVP) → Milvus | Template/knowledge retrieval |
| **PPTX parsing** | python-pptx | Standard library, well-maintained |
| **PDF parsing** | MinerU / PyMuPDF | PPTAgent already integrates MinerU |
| **Task queue** | Celery + Redis (if needed) | Parallel Best-of-2 generation |

## 8. MVP Scope (Phase 1)

**Target:** 3-month development cycle. Usable by the team daily.

### 8.1 In scope (revised post-debate)

> **Key changes from debate:** Screenshot input → P1; Best-of-2 → Two-Stage; PDF export → P0; Super Skeletons replaces hand-crafted templates.

| Feature | Description | Priority |
|---------|-------------|----------|
| Text input → HTML | Input outline/bullet points → generate multi-slide HTML presentation | P0 |
| PPTX input → redesign | Upload .pptx → extract content → regenerate with better design | P0 |
| Web UI v1 | Input panel + live preview + iteration chat | P0 |
| Two-Stage Best-of-2 | Outline+preview comparison → recommended+alternative UI → full generation for winner | P0 |
| Quality Gate v1 | Rule-based checks (Tier 1) + VLM visual review (Tier 2) + auto-fix loop | P0 |
| **PDF export** | Puppeteer-based PDF generation from HTML slides | **P0** |
| Iteration loop | User requests changes via chat → Session Manager → Agent edits → QG → re-render | P0 |
| **IR contract definition** | Week 1 deliverable: Agent output → Renderer input JSON contract | **P0 (Week 1)** |
| Template Library v1 (Super Skeletons) | 5 hand-crafted skeletons × 20 AI-generated themes = 100+ combinations | P1 |
| User Profile v1 | Record Best-of-2 choices + iteration diffs + basic preferences | P1 |
| Screenshot input → redesign | Upload photo of slides → VLM analysis → regenerate | **P1** (moved from P0) |

### 8.2 Out of scope (Phase 2+)

| Feature | Phase |
|---------|-------|
| Voice input (Whisper) | Phase 2 |
| PPTX export (python-pptx from IR) | Phase 2 |
| Template Marketplace | Phase 2 |
| Web crawling for templates/trends | Phase 2 |
| Community contribution pipeline | Phase 2 |
| Enterprise SSO / brand kit | Phase 3 |
| API/SDK | Phase 3 |
| Multi-language support | Phase 3 |

### 8.3 PPTAgent Fork Strategy (debate addition)

> **Kill switch at Week 2** (Opus + Grok consensus): If PPTAgent codebase proves too complex to integrate by end of Week 2, immediately fall back to lightweight agent based on LLM function calling (no MCP/tool sandbox). This is the single highest execution risk.

| Week | Milestone | Kill switch? |
|------|-----------|-------------|
| Week 1 | Fork PPTAgent, define IR contract, run existing examples | — |
| Week 2 | Replace output pipeline with HTML renderer, add 1 custom tool | **If fails → fallback to function-calling agent** |
| Week 3-4 | Integrate Quality Gate, Session Manager | — |

**Fallback agent architecture (if kill switch triggered):**
```
LLM with function calling (Claude/GPT-4o)
  → Tools: template_query, user_profile_read, quality_check, render_html
  → No sandbox, no MCP, simpler but functional
  → Can always add PPTAgent patterns later when mature
```

### 8.4 Pre-MVP Validation (debate addition, Qwen)

> Before full MVP build, validate the riskiest assumptions:

| Assumption | Validation method | Target | Timeline |
|------------|------------------|--------|----------|
| HTML+PDF accepted by target users | Send 50 users HTML demo + PDF export, track satisfaction | 70%+ say "good enough" | Week 1 |
| VLM visual QA is reliable | Build 100-slide test set, compare VLM scores vs designer ratings | >80% agreement | Week 2 |
| PPTAgent fork is viable | See kill switch above | Working HTML output by Week 2 | Week 2 |

### 8.5 Success criteria for MVP

- [ ] Team of 5+ people use it weekly for real presentations
- [ ] Quality Gate catches 90%+ of visual defects before user sees them
- [ ] Two-Stage Best-of-2 data collection working (preferences accumulating)
- [ ] Average Quality Gate score >= 7.5/10
- [ ] End-to-end latency: text input → preview < 60 seconds (including Two-Stage comparison)
- [ ] PPTX input → redesigned preview < 90 seconds
- [ ] PDF export works reliably across DingTalk/Feishu/email

## 9. Project Structure

```
ppt-agent/
├── docs/
│   └── superpowers/specs/          # Design documents
├── frontend/                        # React + Tailwind web app
│   ├── src/
│   │   ├── components/             # UI components
│   │   ├── pages/                  # Routes
│   │   └── hooks/                  # Custom hooks
│   └── package.json
├── backend/                         # FastAPI server
│   ├── api/                        # REST endpoints
│   ├── agent/                      # PPTAgent fork integration
│   ├── input_parser/               # Multi-format input processing
│   ├── quality_gate/               # QA engine
│   ├── renderer/                   # HTML generation
│   ├── templates/                  # Template library
│   ├── user_profile/               # User profile engine
│   └── knowledge/                  # Design knowledge base
├── templates/                       # Template files (HTML + CSS)
├── tests/                           # Test suite
├── scripts/                         # CLI tools, migrations
├── CLAUDE.md                        # Project AI config
├── README.md                        # Project documentation
└── docker-compose.yml               # Local deployment
```

## 10. Open Questions (updated post-debate)

1. ~~**PPTAgent fork depth**~~ → Resolved: Fork entire repo, 2-week kill switch. See Section 8.3.
2. ~~**Template format standardization**~~ → Resolved: IR contract is Week 1 P0 deliverable. See Section 8.1.
3. ~~**Best-of-2 cost management**~~ → Resolved: Two-Stage approach reduces cost by ~40-50%. See Section 4.
4. **Offline vs cloud-first**: MVP is local-first, but SaaS monetization requires cloud. Need to design the abstraction layer early.
5. **Chinese vs English first**: Given primary user base, should templates and UI default to Chinese with i18n support?
6. **Puppeteer PDF fidelity**: Need to verify that Puppeteer-generated PDFs preserve CSS grid layouts, Chart.js visualizations, and scroll-snap slides correctly. May need per-slide screenshot stitching.
7. **VLM model selection for Quality Gate**: Claude Vision vs GPT-4o for Tier 2 visual QA — need to benchmark consistency and cost. (Qwen flagged inter-model scoring inconsistency as risk.)

## Appendix A: Competitive Landscape

| Tool | Stars | Approach | Weakness we exploit |
|------|-------|----------|-------------------|
| Gamma | - | Template + AI text | PPTX export breaks; no iteration |
| Presenton | 4.5k | Template-driven | Not agentic; limited personalization |
| PPTAgent | 3.9k | Agentic + PPTX | Design quality; no knowledge moat |
| Presentations.AI | - | SaaS | Can't self-host; no learning |
| Beautiful.ai | - | Design automation | No AI content; expensive |

Our positioning: **The only tool that generates, self-reviews, learns, and gets better with every use.**

## Appendix B: Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| PPTAgent codebase too complex to fork | High | Evaluate during first 2 weeks; fallback to extracting agent patterns only |
| LLM API costs too high for Best-of-2 | Medium | Use cheaper models for one path; implement response caching |
| HTML not accepted by enterprise users | Medium | Add PPTX export in Phase 2; position HTML as "modern alternative" |
| Template cold start too slow | Medium | Invest heavily in first 20 templates; consider AI batch generation |
| Open source doesn't gain traction | Low | Focus on dogfooding first; open source is marketing, not the product |

## Appendix C: Multi-Model Debate Report

**Date:** 2026-03-31
**Preset:** debate | **Stakes:** high

### Model Dispatch

| # | Model | Lab | Role | Status | Size |
|---|-------|-----|------|--------|------|
| 1 | Claude Opus 4.6 | Anthropic | Proposer A (架构师) | ✓ | 5.0KB |
| 2 | Grok 4 | xAI | Red Team (攻击者) | ✓ | 5.5KB |
| 3 | Gemini 3.1 Pro | Google | Proposer B (替代方案) | ✓ | 5.1KB |
| 4 | Kimi K2.5 | Moonshot | User Advocate (用户代言) | ✓ | 3.8KB |
| 5 | Qwen-3.5-Plus | Alibaba | Counter-Proposer (假设挑战) | ✓ | 3.0KB |

### Consensus Points (agreed by 3+ models)

1. **HTML-only output is the #1 risk** (all 5 models) → Added PDF export as P0
2. **MVP scope too ambitious for 3 months** (Opus, Grok, Gemini) → Reduced scope, added kill switch
3. **Full dual-track Best-of-2 too expensive** (Grok, Gemini, Qwen) → Redesigned as Two-Stage
4. **PPTAgent fork needs escape hatch** (Opus, Grok) → 2-week kill switch added
5. **Quality Gate is strongest differentiator** (Opus, Gemini) → Confirmed, prioritized
6. **Cold start needs more than 20 handcrafted templates** (Opus, Gemini) → Super Skeletons strategy

### Key Revisions Made

| # | Revision | Source model(s) |
|---|----------|----------------|
| 1 | HTML as preview, PDF export P0 | All 5 models |
| 2 | Two-Stage Best-of-2 (outline+preview, then full) | Gemini |
| 3 | "Recommended + Alternative" UI (not equal side-by-side) | Kimi |
| 4 | Screenshot input → P1 (from P0) | Opus |
| 5 | PPTAgent 2-week kill switch + fallback agent | Opus, Grok |
| 6 | Super Skeletons cold start (5 × 20 = 100+ combos) | Gemini |
| 7 | Agent Engine split → Session Manager + Agent Engine | Opus |
| 8 | IR contract as Week 1 deliverable | Opus |
| 9 | Pre-MVP validation gates (HTML acceptance, VLM accuracy) | Qwen |
| 10 | Free tier: limit templates not generation count | Opus |

### Risks Not Fully Mitigated

| Risk | Raised by | Status |
|------|-----------|--------|
| Microsoft Copilot / Canva competitive threat | Grok | Acknowledged, no architectural change — differentiate on iteration + learning |
| VLM scoring inconsistency across models | Grok, Qwen | Open question #7 — needs benchmark |
| Open source users fork to avoid paying | Grok | Partially mitigated by template/profile limits in free tier |
| Data flywheel needs >1000 users to spin | Opus, Grok | Accepted — focus on dogfooding first, flywheel is Phase 2+ |

### Opus Decision: REVISED
7 structural changes applied to spec based on debate consensus.
