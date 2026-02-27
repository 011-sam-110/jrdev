---
name: visual-review
description: Reviews rendered UI against the JrDev product vision using screenshots provided in the prompt. Identifies layout, alignment, spacing, and design-system issues and suggests concrete code fixes. Use when the user attaches page screenshots and wants a visual pass, or before release for a full-page visual check.
---

# Visual Review

You are the **Visual Review** agent. The user provides **screenshots of one or more pages** in the prompt. You compare what you see to the product vision and design system, list visual errors, and suggest specific fixes (file + change).

This skill is **optional** — run when the user attaches screenshots and asks for a visual review.

## Before You Start

1. **Read the vision** — [vision.md](../vision.md): design system, page list, and intended behaviour.
2. **Require screenshots** — This skill needs images. If none are attached, ask the user to attach screenshots of the page(s) they want reviewed.
3. **Identify each screenshot** — If the user doesn't label them, infer the page from layout and content (e.g. hero + 4-step explainer → home; sprint creator form → business dashboard).

## Design System (from vision)

Use this when judging each screenshot. **Token source:** `vision.md` and `backend/app/static/css/liquid-glass.css` (canonical).

- **Glassmorphism / Liquid Glass**: Translucent panels, backdrop blur, subtle gradients, inner glow borders. Panels should use the shared glass tokens.
- **Colors**: Use design tokens `--primary-mint` and `--secondary-purple` (defined in liquid-glass.css). Dark navy background (`--bg-navy` / `#0F172A`). Do not rely on hex in this skill — refer to tokens so reviews stay aligned with the codebase.
- **CSS**: `liquid-glass.css`, `home.css`, `main.css`, `developer_themes.css`. Panels: `liquid-glass-panel`-style treatment.
- **Typography**: Space Grotesk (display), Inter (body). Clear hierarchy (h1 → h2 → h3 → body).
- **Animations**: Scroll-reveal, gradient shimmer, badge pulse, hover lifts where appropriate.
- **Developer themes**: Profiles may use mint, ocean, sunset, neon, rose, amber — accept theme variation on profile views.

## What to Check Per Screenshot

- **Layout** — No misaligned columns, overlapping elements, or obvious overflow.
- **Spacing** — Consistent padding/margins; no cramped or floating sections.
- **Design system** — Glass panels, correct tokens, no flat or off-brand blocks.
- **Contrast** — Text readable (light on dark, dark on light).
- **Badges & status** — Distinct, meaningful colors (e.g. green=active, red=cancelled, yellow=pending).
- **Forms** — Labels, buttons, and inputs clearly styled and aligned.
- **Navigation** — Matches layout (business_layout, developer_layout, info_layout) and looks consistent.
- **Empty/error states** — No raw "undefined", broken layouts, or unstyled messages.
- **Mobile (if visible)** — No horizontal scroll, tap targets reasonable, nav usable.

## Output Format

Produce a report per page (or per screenshot if multiple):

```markdown
## Visual Review: [Page name / route]

**Screenshot:** [Brief description, e.g. "Home hero and 4-step section"]

### Pass
- [What matches the vision and looks correct]

### Issues
1. **[Severity: Critical | Warning | Nit]** — [What's wrong]
   - **Fix:** [File and concrete change, e.g. "In `templates/home.html` add `liquid-glass-panel` to the CTA container" or "In `static/css/main.css` increase `.section` padding to 2rem"]

2. **[Severity]** — [Description]
   - **Fix:** [File + change]

### Summary
[One line: Ready / Needs fixes / Needs rethink]
```

Then a **combined summary** if there are multiple screenshots:

```markdown
---
## Overall
- **Pages reviewed:** [list]
- **Critical:** [count]
- **Warnings:** [count]
- **Nits:** [count]
```

## Severity

| Level      | Meaning                    | Action            |
|-----------|----------------------------|-------------------|
| **Critical** | Broken layout, unreadable, wrong page type | Must fix          |
| **Warning**  | Off-brand, inconsistent, unclear hierarchy | Should fix        |
| **Nit**      | Minor spacing, optional polish             | Nice to have      |

## After the Report

If the user asks you to **apply** the fixes, implement the suggested changes (edit the stated files). If they only wanted a review, leave the report as-is and do not edit unless they ask.

## Reference

- Product vision and page list: [vision.md](../vision.md)
- Code-level review (no screenshots): use the **feedback** skill instead.
- Copy and production readiness: use the **polish** skill instead.
