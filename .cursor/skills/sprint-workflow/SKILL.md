---
name: sprint-workflow
description: Orchestrates the full development cycle by running Vision Capture, Architect, Programmer, Feedback, and Polish in sequence. Use when the user requests a feature, change, fix, or improvement to the JrDev platform. This is the default workflow for all development tasks.
---

# Sprint Workflow — Development Orchestrator

This skill runs the full **Vision Capture → Architect → Programmer → Feedback → Polish** pipeline for every development task. Never skip phases. Never write code without a plan. Never ship without a review.

## The Loop

Every task follows this exact cycle. Repeat until the user is satisfied.

```
┌─────────────────────────────────────────────┐
│  USER REQUEST                               │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│  PHASE 0: VISION CAPTURE                    │
│  Chat to understand what to build →         │
│  Ask questions → Create/update vision.md    │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│  PHASE 1: ARCHITECT                         │
│  Read vision.md → Break into steps →        │
│  List files affected → Output plan          │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│  PHASE 2: PROGRAMMER                        │
│  Follow the plan → Edit files →             │
│  Run linter checks                          │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│  PHASE 3: FEEDBACK                          │
│  Review all changes → Run checklist →       │
│  Fix Critical/Warning issues immediately    │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│  PHASE 4: POLISH  (if public-facing)        │
│  Copy, trust signals, visual consistency,   │
│  UX friction, production readiness          │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│  REPORT TO USER                             │
│  Summary of what changed → Questions →      │
│  Wait for user input                        │
└──────────────────┬──────────────────────────┘
                   ▼
          User answers / approves
                   ▼
           Next iteration (or done)
```

## Phase 0: Vision Capture

Read `.cursor/skills/vision-capture/SKILL.md` for full instructions. In this phase:

1. **Conversation** — For new features: talk with the user, ask 2–5 focused questions (who, what, why, scope), reflect back and confirm. **For tiny fixes** (single typo, one-line change): one-sentence confirmation only; no questions.
2. **Create or update** `.cursor/skills/vision.md` so it accurately describes the product/feature. For small fixes, vision.md can stay unchanged.
3. **Hand off** — When the user confirms (or for tiny fixes, immediately), state that Vision Capture is done and the next phase is Architect. Do not write code or implementation plans.

**Do NOT write any code or file-level plans during this phase.** Understanding and vision only.

## Phase 1: Architect

Read `.cursor/skills/architect/SKILL.md` for full instructions. In this phase:

1. Read `.cursor/skills/vision.md` to understand current state.
2. Analyze the user's request against what already exists.
3. Produce a **numbered plan** with: Files affected (exact paths), what changes in each file, order of operations, risks or things to watch for.
4. **Save the plan to a file:** Write the full plan to `.cursor/plans/current.md` (default). If the user or a previous message references a named plan (e.g. `developer-dashboard-improvements.md`), use that file instead. Programmer and Feedback will read from this file.

**Do NOT write any code during this phase.** Planning only.

## Phase 2: Programmer

Read `.cursor/skills/programmer/SKILL.md` for full instructions. In this phase:

1. **Read the plan** from `.cursor/plans/current.md` (or the plan file referenced in chat). Follow only that plan.
2. Execute the plan step by step; read each file before editing.
3. Make the changes using the correct tools; run linter checks after editing.
4. If a step can't be done as planned, note the deviation.
5. **At the end of the phase,** output: **Files changed:** [list of file paths]. This is the list Feedback will review.

**Follow the plan. Don't add things the plan didn't mention.**

## Phase 3: Feedback

Read `.cursor/skills/feedback/SKILL.md` for full instructions. In this phase:

1. **Read the plan** (e.g. `.cursor/plans/current.md`) and the **Files changed** list from the Programmer. Your scope is those files only (and direct dependencies if you open them); do not review the entire codebase.
2. Re-read every file in the Files changed list and run through the Feedback checklist:
   - No extra/missing UI elements
   - CSS matches design system
   - JS selectors match HTML
   - Routes have correct guards
   - Forms have CSRF, correct action/method
   - Ratings use `|format_rating`
   - No placeholder text left behind
3. **Fix Critical and Warning issues immediately** — don't just report them. Make the edits.
4. For Nit-level issues, list them in the report but don't fix unless trivial.

## Phase 4: Polish

**Skip Polish** if the plan or Files changed contain **only** backend files (e.g. `routes.py`, `models.py`, `utils.py`, `forms.py`) and **no** templates, CSS, or static assets. Say: "Skipping Polish (backend-only change)." Then go to Report.

Otherwise, read `.cursor/skills/polish/SKILL.md` for full instructions. This phase runs when the change touches **any public-facing content**: home page, about, support, register, login, landing copy, CTAs, or page titles.

In this phase:

1. Re-read every modified template and CSS file.
2. Check copy: benefit-driven headlines, consistent terminology (use the vocabulary guide), no filler words, specific CTA labels.
3. Check trust signals: pricing clarity, refund messaging, contract/NDA reassurance, social proof structure.
4. Check visual polish: spacing, typography hierarchy, color usage, empty/error states, mobile responsiveness.
5. Check production readiness: no placeholder text, proper page titles, no debug output, image alt text.
6. **Fix Critical and Should Fix issues immediately.** Add copy rewrites directly.
7. List Nice to Have items in the report.

## Report to User

After all phases complete, present this summary:

```
## Iteration Complete

### What Changed
- [Bullet list of every file modified and what was done]

### Feedback Issues Found & Fixed
- [Any issues the Feedback phase caught and auto-fixed]

### Polish Changes (if applicable)
- [Copy rewrites, trust signal additions, visual fixes made by Polish phase]

### Remaining Nits (Optional)
- [Minor things that could be improved but aren't blocking]

### Questions Before Next Iteration
1. [Specific question about a decision that was made]
2. [Anything ambiguous that needs user input]
3. [Suggestion for what to do next]
```

### Rules for Questions

- Ask **2–4 focused questions** maximum. Don't overwhelm.
- Questions should be about decisions, preferences, or next steps — not "did I do this right?"
- If something looks like it might have a follow-on task, suggest it as a question: "Should I also update X to match?"
- If everything is clean and clear, just say "No questions — ready for the next task."

## After User Responds

When the user answers questions or gives the next instruction:

1. **New or changed product direction** → Return to Phase 0 (Vision Capture) to update vision.md, then continue to Architect.
2. **Same scope, plan tweaks** → Return to Phase 1 (Architect) to revise the plan, then Programmer.
3. **Small adjustments only** → Go straight to Phase 2 (Programmer) if the plan is still valid.
4. Run the full loop again as needed: Vision Capture → Plan → Build → Review → Polish → Report.
5. Each iteration should be getting closer to done, not expanding scope.

## Vision Updates

At the end of a successful iteration (user approves), update `.cursor/skills/vision.md`:

- Add new pages/routes/models to the appropriate tables.
- Move items from "Known Gaps" to implemented if applicable.
- Keep the document accurate as the single source of truth.

## Important

- **Never skip the Feedback phase.** This is what prevents weird UI bugs, extra buttons, and broken styling.
- **Never write code before the plan.** Even for "small" changes, state what you'll do first.
- **Keep iterations small.** One feature or fix per loop. Don't try to do everything in one pass.
- **The user is the final reviewer.** Your job is to hand them something clean to evaluate, not something they have to debug.

## Phase Transitions

When moving to a new phase, you **MUST** output exactly once:

**→ [PHASE NAME]**  
[One sentence: what this phase does and what it will produce.]

Then run the phase. Example: **→ ARCHITECT** — Reading vision.md and producing a numbered plan; saving to `.cursor/plans/current.md`. No code.

## Fast Path (Tiny Changes)

If the user's request is a **single, unambiguous change** (one typo, one-word copy change, single CSS fix, one linter fix) with no product/UX decisions:

1. **Vision Capture:** One-sentence confirmation (e.g. "Fixing the typo on the login page."). No vision.md change. Hand off immediately.
2. **Architect:** Produce a **micro-plan** (3–5 lines: file, change, done). Still write it to `.cursor/plans/current.md`.
3. **Programmer → Feedback** as usual. Polish only if the change touches public-facing content.

Do not ask multiple questions in Vision Capture for tiny fixes.

## Definition of Done (per phase)

- **Vision Capture:** vision.md updated (or explicitly unchanged) and user confirmation received.
- **Architect:** Plan written to `.cursor/plans/current.md` (or a named plan file if the user referenced one), with Files Affected and Steps.
- **Programmer:** All steps in the plan done, linter clean, **Files changed:** list emitted at end of phase.
- **Feedback:** All items in **Files changed** reviewed, Critical/Warning fixed, report produced.
- **Polish:** (If run) All modified public-facing assets reviewed, Critical/Should Fix fixed, report produced.
