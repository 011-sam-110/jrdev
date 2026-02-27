# Multi-Agent Design Optimization

Recommendations to maximise **clarity**, **speed**, and **quality** of your sprint-workflow pipeline (Vision Capture → Architect → Programmer → Feedback → Polish → Report).

---

## 1. Clarity

### 1.1 Persist the Architect plan to a file

**Current:** The plan lives in chat. Programmer and Feedback must infer “the plan” from context.

**Change:** In the Architect phase, always write the plan to a file, e.g.:

- `.cursor/plans/current.md` (overwritten each task), or  
- `.cursor/plans/<slug-from-request>.md` (e.g. `developer-dashboard-improvements.md`)

**In sprint-workflow and architect SKILL:**

- Architect: “Output your plan as `## Architect Plan` and **save it to** `.cursor/plans/current.md` (or a named plan file).”
- Programmer: “Before coding, read `.cursor/plans/current.md` (or the plan file referenced in chat). Follow only that plan.”
- Feedback: “Read the plan in `.cursor/plans/current.md` to know what was intended; review all files listed there.”

**Why:** Stable, single reference. No re-reading long threads. Clear handoff.

---

### 1.2 Explicit phase announcements

**Current:** Rule says “announce your current skill when switching” but it’s easy to skip.

**Change:** In **sprint-workflow**, add a short mandatory transition block, e.g.:

```markdown
## Phase transitions

When moving to a new phase, you MUST output exactly once:

**→ [PHASE NAME]**  
[One sentence: what this phase does and what it will produce.]

Then run the phase.
```

Example: “**→ ARCHITECT** — Reading vision.md and producing a numbered plan with files and steps. No code.”

**Why:** Reduces role confusion and prevents the agent from mixing phases (e.g. writing code in Architect).

---

### 1.3 Input/Output contract per skill

**Current:** Each skill describes responsibilities but not the exact input it expects and output it must produce.

**Change:** Add a short “Contract” section to each phase SKILL (vision-capture, architect, programmer, feedback, polish):

| Phase          | Input (you receive)              | Output (you produce)                          |
|----------------|----------------------------------|-----------------------------------------------|
| Vision Capture | User request (possibly vague)    | Updated vision.md + one-paragraph summary     |
| Architect      | vision.md + user request         | Plan in `.cursor/plans/current.md` (or named) |
| Programmer     | Plan file + list of files        | Code edits + “Files changed: …” list           |
| Feedback       | Plan file + changed files        | Feedback report + fixes for Critical/Warning  |
| Polish         | Changed templates/CSS + plan     | Polish report + fixes for Critical/Should Fix |

**Why:** Next phase (or the orchestrator) knows what to pass and what to expect; fewer “what was I supposed to do?” moments.

---

### 1.4 When NOT to use the full pipeline

**Current:** development-workflow says “when the user asks you to build, change, fix…” → always sprint-workflow. Some requests don’t need the full loop.

**Change:** In **development-workflow.mdc**, add:

- “If the user **only** asks for an explanation, search, or reading (no code change), answer directly; do not run Vision Capture or Architect.”
- “If the user attaches **screenshots** and asks for a **visual review only**, use the **visual-review** skill; do not run the full sprint-workflow unless they then ask to implement fixes.”

**Why:** Right tool for the job; avoids unnecessary phases and token use.

---

## 2. Speed

### 2.1 Fast path for tiny changes

**Current:** Every request goes Vision Capture → Architect → … even for “fix typo on X”.

**Change:** In **sprint-workflow** and **vision-capture**:

- Define a **fast path**: e.g. “If the user’s request is a single, unambiguous change (typo, one-word copy change, single CSS fix, one linter fix) and requires no product/UX decisions:
  1. Vision Capture: one-sentence confirmation (e.g. ‘Fixing the typo on the login page.’), no vision.md change.
  2. Architect: produce a **micro-plan** (3–5 lines: file, change, done). Optionally skip writing to a separate plan file if the micro-plan is in chat.
  3. Then Programmer → Feedback as usual.”
- In **vision-capture**: “For tiny fixes, confirm in one sentence and hand off to Architect; do not ask multiple questions.”

**Why:** Fewer turns and less context for trivial tasks while keeping Feedback.

---

### 2.2 Programmer: end with “Files changed”

**Current:** Feedback says “Re-read every file that was modified” but doesn’t get an explicit list.

**Change:** In **programmer SKILL**, add:

- “At the end of the phase, output a short block: **Files changed:** [list of paths]. This is the list Feedback will review.”

**Why:** Feedback can iterate over a known set; no guessing and fewer missed files.

---

### 2.3 Feedback: scope to changed files + plan

**Current:** “Re-read every file that was modified” — could mean re-reading huge files.

**Change:** In **feedback SKILL**:

- “Your scope is (1) the plan file (e.g. `.cursor/plans/current.md`) and (2) the **Files changed** list from Programmer. Review only those files (and their direct dependencies if you open them). Do not review the entire codebase.”

**Why:** Faster, more predictable reviews.

---

### 2.4 Skip Polish explicitly when backend-only

**Current:** “Skip [Polish] only for purely internal/backend changes with no user-visible impact.”

**Change:** In **sprint-workflow**:

- After Feedback, add: “If the plan or Files changed contain **only** backend files (e.g. `routes.py`, `models.py`, `utils.py`) and **no** templates, CSS, or static assets, skip Polish and say: ‘Skipping Polish (backend-only change).’ Then go to Report.”

**Why:** Avoids running Polish when it can’t add value; saves time and tokens.

---

## 3. Quality

### 3.1 Feedback vs Polish: one-line distinction

**Current:** Both “review” but the boundary can blur.

**Change:** Add one sentence at the top of each SKILL:

- **Feedback:** “You review for **correctness and consistency**: does it work, does it match the design system and existing code, are guards and forms correct?”
- **Polish:** “You review for **customer trust and conversion**: copy, trust signals, professionalism, and production readiness. You do not re-check implementation correctness (Feedback does that).”

**Why:** Clear separation of concerns; less overlap and fewer duplicate comments.

---

### 3.2 Architect: “Feedback focus” line

**Current:** Feedback runs a full checklist every time.

**Change:** In **architect SKILL**, add to the plan template:

- **Feedback focus:** [Optional] “For this change, Feedback should pay special attention to: [e.g. form CSRF and redirects / glassmorphism and tokens / role guards].”

**Why:** Feedback can prioritise what matters for this task; better use of attention.

---

### 3.3 Design tokens and vision alignment

**Current:** Polish says “Primary mint (#14F195), Purple (#8B5CF6)”. Visual-review says “Primary mint (indigo), secondary purple (teal)” with different hex. Codebase uses `--primary-mint: #4f46e5`, `--secondary-purple: #0d9488`. vision.md doesn’t lock hex values.

**Change:**

1. Pick a single source of truth (e.g. `liquid-glass.css` or vision.md) and document the canonical tokens and hex values.
2. In **vision.md**, add a short “Design tokens” line, e.g. “Primary: `--primary-mint` (#4f46e5), Secondary: `--secondary-purple` (#0d9488). See liquid-glass.css.”
3. In **polish** and **visual-review** SKILLs, replace any hardcoded hex with: “Use design tokens from vision.md / liquid-glass.css (--primary-mint, --secondary-purple).”

**Why:** All agents and future you judge “correct” styling against the same tokens; no conflicting colour advice.

---

### 3.4 Definition of Done per phase

**Current:** Phases end when the agent “feels” done.

**Change:** In **sprint-workflow**, add a “Definition of Done” for each phase, e.g.:

- Vision Capture: vision.md updated (or explicitly unchanged) and user confirmation received.
- Architect: Plan written to `.cursor/plans/current.md` (or named file), with Files Affected and Steps.
- Programmer: All steps in plan done, linter clean, “Files changed” list emitted.
- Feedback: All items in “Files changed” reviewed, Critical/Warning fixed, report produced.
- Polish: (If run) All modified public-facing assets reviewed, Critical/Should Fix fixed, report produced.

**Why:** Reduces premature handoffs and ensures each phase actually completes its job.

---

## 4. Optional structural improvements

### 4.1 Plan file naming

You already have `.cursor/plans/*.md` (e.g. `developer-dashboard-improvements.md`). To avoid ambiguity:

- In **sprint-workflow**: “Architect writes the plan to `.cursor/plans/current.md` by default. If the user or a previous message references a named plan (e.g. `developer-dashboard-improvements.md`), use that file instead.”
- Optionally keep `current.md` as a symlink or copy of “this session’s plan” so Programmer/Feedback always have one place to look.

### 4.2 Visual-review in the pipeline

**Current:** visual-review is standalone (user attaches screenshots).

**Change:** In **sprint-workflow**, add an optional step: “After Polish (for public-facing changes), if the user has attached a screenshot of the changed page, run **visual-review** once and apply any Critical/Warning fixes. If no screenshot, skip.”

**Why:** Catches rendered-only issues without making screenshots mandatory every time.

---

## 5. Priority summary

| Priority | Change                                      | Impact                    |
|----------|---------------------------------------------|---------------------------|
| High     | Persist Architect plan to `.cursor/plans/`   | Clarity + speed           |
| High     | Programmer outputs “Files changed”          | Speed + quality (Feedback) |
| High     | Align design tokens (vision / Polish / visual-review) | Quality            |
| Medium   | Explicit phase transitions                  | Clarity                   |
| Medium   | Fast path for tiny fixes                    | Speed                     |
| Medium   | Feedback scope = plan + Files changed       | Speed                     |
| Medium   | One-line Feedback vs Polish distinction     | Quality                   |
| Low      | Input/Output contract per skill             | Clarity                   |
| Low      | “When NOT to use pipeline” in rule          | Clarity + speed           |
| Low      | Architect “Feedback focus”                  | Quality                   |
| Low      | Definition of Done per phase                | Quality                   |

Implementing the High and Medium items will give the largest gain in agent clarity, speed, and quality. The rest can be added incrementally.
