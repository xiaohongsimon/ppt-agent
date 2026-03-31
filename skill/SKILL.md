---
name: ppt
description: Generate professional HTML presentations from text descriptions. Use when user says "做PPT", "make a presentation", "create slides", "/ppt", or asks to generate any presentation.
user_invocable: true
---

# PPT-Agent Skill

Generate a professional HTML presentation directly in Claude Code. No external API needed — YOU are the LLM.

## How It Works

1. You (Claude) generate a `PresentationRenderSpec` JSON based on the user's request
2. The CLI renders it to HTML + optional PDF
3. Zero API cost — uses the current Claude Code subscription

## Workflow

### Step 1: Understand the request

Ask the user (if not clear):
- What is this presentation about?
- Who is the audience?
- What scene? (quarterly review, training, proposal, etc.)

### Step 2: Generate the RenderSpec JSON

Create a JSON file following this schema. This is the MOST IMPORTANT step — the quality of the presentation depends entirely on this JSON.

```json
{
  "title": "Presentation Title",
  "theme": {
    "accent_primary": "#4f6df5",
    "accent_secondary": "#7c3aed"
  },
  "slides": [
    {
      "slide_index": 0,
      "layout": "title",
      "heading": "Main Title",
      "subheading": "Subtitle or tag",
      "components": []
    },
    {
      "slide_index": 1,
      "layout": "data_driven",
      "heading": "Slide Heading",
      "subheading": "SECTION TAG",
      "components": [
        {
          "type": "card_grid",
          "props": {
            "columns": 3,
            "cards": [
              {"title": "Metric", "value": "87%", "change": "+12%", "description": "Details"}
            ]
          }
        },
        {
          "type": "highlight_box",
          "props": {"text": "Key takeaway message", "color": "green"}
        }
      ]
    }
  ]
}
```

**Available layouts:** `title`, `data_driven`, `split_panel`, `full_visual`, `comparison`

**Available component types:**

| Type | Props |
|------|-------|
| `card_grid` | `columns` (2-4), `cards` (list of {title, value, change, description}) |
| `highlight_box` | `text`, `color` (green/blue/purple/orange/red) |
| `bar_chart` | `bars` (list of {label, value (0-100), display}) |
| `bullet_list` | `items` (list of strings, max 7) |
| `flow` | `steps` (list of strings) |
| `text_block` | `text` |
| `quote_box` | `text` |
| `comparison` | `left` {title, items}, `right` {title, items} |

**Design rules:**
- First slide: layout `title`, minimal components
- Every data slide MUST end with a `highlight_box` (key takeaway)
- Max 7 items per `bullet_list`, max 4-5 cards per `card_grid`
- Use varied component types across slides
- Choose theme colors matching the tone (professional → blue, growth → green)
- 8-15 slides for a typical presentation
- Last slide: closing with action items or Q&A

### Step 3: Save and render

```bash
# Write JSON to temp file, render to HTML
cat > /tmp/ppt-spec.json << 'EOF'
{your generated JSON}
EOF

cd /Users/leehom/work/ppt-agent && uv run python cli.py /tmp/ppt-spec.json --output ./output/latest --pdf
open ./output/latest/html/index.html
```

### Step 4: Iterate

If the user wants changes:
- Read the current JSON: `cat /tmp/ppt-spec.json`
- Modify the specific slides/components
- Re-render

## Quality Checklist

Before rendering, verify your JSON:
- [ ] First slide is layout "title"
- [ ] Every data_driven/split_panel slide has a highlight_box
- [ ] No bullet_list exceeds 7 items
- [ ] Theme colors are set
- [ ] slide_index values are sequential (0, 1, 2, ...)
- [ ] Content is in the same language as the user's request
