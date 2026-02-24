# DRY Analysis & Refactoring Roadmap

This document provides a **pattern recognition** of duplicated code, **abstraction strategies** for each cluster, and a **prioritized to-do list** to move the project toward a **modular architecture** with a single source of truth.

---

## 1. Pattern Recognition — Logical Clusters

### Cluster A: Role-based access guard (Python)

**Location:** `backend/app/routes.py`

| Route / handler        | Lines   | Pattern |
|------------------------|---------|--------|
| `review_gallery()`      | 20–22   | `if current_user.role != 'BUSINESS': flash + redirect` |
| `edit_profile()`        | 55–58   | `if current_user.role != 'DEVELOPER': flash + redirect` |
| `update_markdown()`     | 103–104 | `if current_user.role != 'DEVELOPER': return jsonify + 403` |
| `add_pinned_project()`  | 114–115 | `if current_user.role != 'DEVELOPER': redirect` (no flash) |
| `delete_pinned()`       | 140–142 | Ownership check + flash + redirect |

**Observation:** Same “check role (or ownership), flash/respond, redirect” logic repeated with small variations (flash vs jsonify, different roles).

---

### Cluster B: Post-action redirect to home (Python)

**Location:** `backend/app/routes.py`

Multiple routes end with `return redirect(url_for('main.home'))`:

- Lines 88, 110, 116, 134, 146 (edit_profile, update_markdown, add_pinned_project, delete_pinned, setup_2fa success)
- Lines 205, 261 (verify_2fa fallback, logout)

**Observation:** “Redirect to home after success/deny” is repeated; some routes might later want `next` or dashboard. No single helper yet.

---

### Cluster C: Auth page chrome (HTML)

**Files (full standalone documents):**

- `backend/app/templates/login.html` (lines 1–78: head + tailwind + styles + navbar + hero shell)
- `backend/app/templates/register.html` (1–78)
- `backend/app/templates/setup_2fa.html` (1–78)
- `backend/app/templates/verify_2fa.html` (1–78)

**Duplicated blocks:**

- **`<head>`:** meta, Tailwind CDN, same fonts, Material Icons, identical `tailwind.config` (primary/secondary, background-*, fontFamily, backgroundImage).
- **`<style>`:** `.glass`, `.text-glow`, `.hero::before`, `.btn-gradient`, `@keyframes gradientShift` — same ~40 lines in each file.
- **Navbar:** fixed bar, logo link to home, Login / Get Started (or minimal nav for 2FA).
- **Hero shell:** `flex-grow flex items-center justify-center pt-32 pb-20`, same background blobs, `max-w-md` card wrapper with `.glass`.

**Observation:** Four auth pages each carry a full copy of head, theme, and layout. Changing theme or navbar requires editing four files.

---

### Cluster D: Flash message block (HTML)

**Files and approximate lines:**

- `login.html` — 107–115  
- `register.html` — 107–115  
- `verify_2fa.html` — 104–112  

**Snippet (identical):**

```html
{% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
        {% for category, message in messages %}
            <div class="mb-6 p-4 rounded-lg bg-{{ category }}/10 border border-{{ category }}/20 text-{{ category }} ...">
                {{ message }}
            </div>
        {% endfor %}
    {% endif %}
{% endwith %}
```

**Observation:** Same flash markup in three templates; `setup_2fa.html` can use the same block once it uses the shared auth layout.

---

### Cluster E: Form field + error markup (HTML)

**Files:** `login.html`, `register.html`

**Pattern (repeated per field):** Label, then `{% if form.<field>.errors %}`: input with error border + error div; `{% else %}`: normal input. Same input classes (`w-full px-4 py-3 rounded-xl bg-black/20 border ...`, error ring/border).

**Observation:** 3–4 fields per page with the same structure; a Jinja macro or include would reduce duplication and keep styling consistent.

---

### Cluster F: Business dashboard layout (HTML)

**Files:**

- `backend/app/templates/business_dashboard.html` (nav, Tailwind config, styles, body shell)
- `backend/app/templates/business_dashboard_your-developers.html` (same nav/structure, different content)

**Duplicated:**

- Nav: logo `<>`, “Sprint Creator” / “Your Developers” / “Billing”, notifications icon, avatar.
- Tailwind/theme: similar palette (mint, purple, navy) and glass styles; variable names differ (`--primary-mint` vs `--mint`, etc.).
- Footer / chrome: same overall structure.

**Observation:** Two full-page business templates; nav and chrome are copy-pasted. One base “business” layout would give a single place for nav and theme.

---

### Cluster G: Developer cards (HTML)

**File:** `backend/app/templates/business_dashboard_your-developers.html`

**Blocks:** ~lines 90–142 (first card) and ~144–195 (second card).

**Structure (repeated):** Video placeholder + play button → avatar + name + subtitle → Fit % + dots → Tech Specs / Deliverables boxes → “Hire Developer” button. Only content (name, fit %, deliverables text, icon) differs.

**Observation:** Two nearly identical card blocks; should be one loop over data + a single card partial (or include/macro).

---

### Cluster H: Requirement buffet + contract sync (JavaScript)

**File:** `backend/app/static/js/business_dashboard.js`

**Issue 1 — Order of execution:**  
`updateContractTasks()` and the block that uses `reqAddBtn`, `reqInput`, `reqList` (lines 6–25) run **before** `reqInput`, `reqAddBtn`, `reqList` are defined (lines 27–29). So when the first block runs, those variables are `undefined` and the contract-task sync never attaches.

**Issue 2 — Selector vs template:**  
JS uses `document.querySelector('input[placeholder^="Add a milestone"]')`. The template `business_dashboard.html` has `placeholder="Add a deliverable (e.g. Stripe integration, User Auth...)"`. The selector never matches.

**Observation:** One “requirement buffet” concern (add/remove tags + sync to contract inputs) is split and the DOM references are used before definition; plus selector doesn’t match HTML.

---

### Cluster I: Email validation (Python/Forms)

**File:** `backend/app/forms.py`

- `RegistrationForm.email` (lines 9–10): `validators=[DataRequired(), Regexp(r'^.+@.+\..+$', message='Invalid email address.')]`
- `LoginForm.email` (lines 29–30): same validators.

**Observation:** Same email validation list in two form classes; one shared list or helper avoids drift (e.g. if you switch to `Email()` or change the regex).

---

### Cluster J: Missing import (Python)

**File:** `backend/app/routes.py`  
**Line:** 104  

`update_markdown()` returns `jsonify({'error': 'Unauthorized'}), 403` but `jsonify` is not imported (only `Blueprint, render_template, url_for, flash, redirect, request, session` from Flask). This will raise `NameError` when the branch is hit.

---

## 2. Abstraction Strategy (per cluster)

| Cluster | Proposed abstraction | Type |
|--------|------------------------|------|
| **A**  | `@require_role('DEVELOPER'|'BUSINESS')` decorator (or `require_role_or_owner` for delete_pinned) that flashes/redirects or returns JSON for API-style routes | Decorator / small helper |
| **B**  | Optional helper e.g. `redirect_after_action(default='main.home', allow_next=False)` used by relevant routes; keeps behavior in one place | Utility function |
| **C**  | `templates/auth_layout.html`: base with head (Tailwind, fonts, icons), shared `<style>`, navbar, hero shell; blocks: `title`, `content` (card inner), optional `footer` | Base template |
| **D**  | `templates/partials/flash_messages.html` (or `components/flash_messages.html`) included where needed | Include partial |
| **E**  | Jinja macro e.g. `macros/render_field.html` → `{{ render_field(form.email) }}` with consistent classes and error markup | Macro |
| **F**  | `templates/business_layout.html`: nav, Tailwind/theme, script tag for dashboard JS; block `content`. `business_dashboard.html` and `business_dashboard_your-developers.html` extend it | Base template |
| **G**  | `templates/partials/developer_card.html` (or macro) taking developer object; page passes list and `{% for developer in developers %}` | Include / macro |
| **H**  | In `business_dashboard.js`: define `reqInput`, `reqAddBtn`, `reqList` once at top of `DOMContentLoaded`; use a stable selector (e.g. `#requirement-buffet-input` or `[data-role="requirement-buffet"]`). Single block that (1) attaches add/remove tag behavior, (2) attaches sync to contract tasks | Refactor script + template attribute |
| **I**  | In `forms.py`: e.g. `EMAIL_VALIDATORS = [DataRequired(), Regexp(r'^.+@.+\..+$', message='Invalid email address.')]` and use in both form classes | Shared constant / validator list |
| **J**  | Add `jsonify` to Flask imports in `routes.py` | Import fix |

---

## 3. The DRY Roadmap — Prioritized To-Do List

### P0 — Fix broken behavior (do first)

| # | Task | Files | Single source of truth | Steps |
|---|------|--------|-------------------------|--------|
| 1 | Fix `jsonify` and requirement-buffet JS | `routes.py`, `business_dashboard.js`, `business_dashboard.html` | — | (1) In `routes.py` add `jsonify` to the Flask import. (2) In `business_dashboard.js` move the three lines that define `reqInput`, `reqAddBtn`, `reqList` to the top of `DOMContentLoaded`, then keep one block that attaches both “add/remove tags” and “sync to contract tasks”. (3) In `business_dashboard.html` either set the deliverable input’s placeholder to start with “Add a milestone” or (preferred) add `id="requirement-buffet-input"` and in JS use `document.getElementById('requirement-buffet-input')` (and derive add btn + list from DOM structure) so selector is stable. |

---

### P1 — High impact: auth layout + shared partials

| # | Task | Files | Single source of truth | Steps |
|---|------|--------|-------------------------|--------|
| 2 | Auth base template | New: `templates/auth_layout.html`. Edit: `login.html`, `register.html`, `setup_2fa.html`, `verify_2fa.html` | `auth_layout.html`: full `<head>` (meta, Tailwind, fonts, icons), one `tailwind.config`, one `<style>` block (`.glass`, `.text-glow`, `.hero::before`, `.btn-gradient`, `gradientShift`), navbar, hero wrapper with blobs; blocks: `title`, `card_title`, `content`, optional `footer` | (1) Create `auth_layout.html` with the shared head, config, styles, navbar, hero shell and empty blocks. (2) In each of the four auth templates, replace everything above/below the card content with `{% extends 'auth_layout.html' %}` and fill only the blocks (title, card_title, form/content). (3) Remove duplicated head/style/nav/hero from each auth template. (4) Manually test login, register, setup_2fa, verify_2fa. |
| 3 | Flash messages partial | New: `templates/partials/flash_messages.html`. Edit: `login.html`, `register.html`, `verify_2fa.html` (and `setup_2fa.html` when using auth_layout) | `partials/flash_messages.html`: the single `{% with messages = get_flashed_messages(with_categories=true) %}...` block | (1) Create `partials/flash_messages.html` with the existing flash loop. (2) In each auth template (and later in auth_layout if you move the block there), replace the inline flash block with `{% include 'partials/flash_messages.html' %}`. (3) Verify flash appears on login error, register error, 2FA error. |
| 4 | Form field macro (optional but recommended) | New: `templates/macros/render_field.html`. Edit: `login.html`, `register.html` | Macro `render_field(form, field_name)` rendering label + conditional error state + input classes | (1) Add `macros/render_field.html` with a macro that outputs the repeated label/input/error structure. (2) Replace each repeated field block in login and register with `{{ render_field(form, 'email') }}` etc. (3) Keep accessibility (labels, ids) and existing classes. |

---

### P2 — Backend: role guard and redirects

| # | Task | Files | Single source of truth | Steps |
|---|------|--------|-------------------------|--------|
| 5 | Role-required decorator | New: `backend/app/decorators.py` (or `utils/auth.py`). Edit: `routes.py` | `@require_role('DEVELOPER')` / `@require_role('BUSINESS')` that returns flash+redirect for HTML; optional `json_response=True` for `update_markdown` (jsonify+403) | (1) Create decorator that checks `current_user.role` (and optionally ownership for delete_pinned). (2) Apply to review_gallery (BUSINESS), edit_profile, update_markdown, add_pinned_project (DEVELOPER), and delete_pinned (ownership). (3) Remove inline role/ownership checks from those view bodies. (4) Add `jsonify` to routes imports if not already. |
| 6 | Shared email validators | `backend/app/forms.py` | `EMAIL_VALIDATORS = [DataRequired(), Regexp(...)]` used by both RegistrationForm and LoginForm | (1) Define `EMAIL_VALIDATORS` at module level. (2) Set `email = StringField('Email', validators=EMAIL_VALIDATORS)` in both forms. (3) Run form tests or manual register/login. |

---

### P3 — Business dashboard layout and cards

| # | Task | Files | Single source of truth | Steps |
|---|------|--------|-------------------------|--------|
| 7 | Business layout base | New: `templates/business_layout.html`. Edit: `business_dashboard.html`, `business_dashboard_your-developers.html` | `business_layout.html`: nav (logo, Sprint Creator, Your Developers, Billing, notifications, avatar), one Tailwind config and glass styles, `<script>` for `business_dashboard.js`, `{% block content %}` | (1) Extract from one of the two dashboards the common head, nav, and script into `business_layout.html`. (2) Make both dashboard templates extend it and put only main content in `{% block content %}`. (3) Unify theme variable names (e.g. mint, purple, navy) in the base. (4) Test both dashboard pages. |
| 8 | Developer card partial | New: `templates/partials/developer_card.html`. Edit: `business_dashboard_your-developers.html` | Single partial/macro that receives a developer object (name, role, fit_pct, demo_duration, tech_specs_link, deliverables_text, accent) and renders one card | (1) Add a list of developer dicts in the view (or keep static for now) and pass to template. (2) Create `partials/developer_card.html` with one card markup parameterized by that object. (3) Replace the two card blocks with `{% for developer in developers %}{% include 'partials/developer_card.html' %}{% endfor %}`. (4) Verify layout and links. |

---

### P4 — Optional consistency (redirect helper)

| # | Task | Files | Single source of truth | Steps |
|---|------|--------|-------------------------|--------|
| 9 | Post-action redirect helper | New: `backend/app/utils.py` (or inside `decorators.py`). Edit: `routes.py` | e.g. `redirect_after_action(default='main.home')` used by edit_profile, update_markdown, add_pinned_project, delete_pinned, setup_2fa, logout, verify_2fa fallback | (1) Implement a small helper that returns `redirect(url_for(default))` (and optionally respects `next`). (2) Replace the repeated `return redirect(url_for('main.home'))` with the helper. (3) Keeps future “redirect after action” behavior in one place. |

---

## 4. Structural Goal: Modular Architecture

- **Core logic vs implementation:**  
  - **Routes:** Keep view logic thin; move “require role” and “redirect after action” into decorators/helpers so route handlers only handle form/data and rendering.  
  - **Templates:** Use a small hierarchy: `layout.html` (main app), `auth_layout.html` (auth flows), `business_layout.html` (business dashboards). Keep shared UI in `partials/` and `macros/`.  
  - **Forms:** Shared validators (e.g. email) live in one place; form classes stay in `forms.py` / `profile_forms.py`.  
  - **Frontend:** One JS entry per “app” (e.g. business_dashboard.js), with DOM references and event binding defined in one order and stable selectors (id or data-*).

- **Result:**  
  - Theme and layout changes touch one base or partial.  
  - Role and redirect behavior live in one decorator/helper.  
  - New auth or business pages only fill blocks or data, reducing copy-paste and drift.

---

## 5. Summary Table

| Priority | Task summary | Main files |
|----------|----------------|------------|
| P0      | Fix jsonify import; fix JS order and selector for requirement buffet | `routes.py`, `business_dashboard.js`, `business_dashboard.html` |
| P1      | Auth layout; flash partial; form field macro | New auth_layout + partials; `login.html`, `register.html`, `setup_2fa.html`, `verify_2fa.html` |
| P2      | Role decorator; shared email validators | New `decorators.py`; `routes.py`, `forms.py` |
| P3      | Business layout; developer card partial | New `business_layout.html`, `partials/developer_card.html`; both business dashboard templates |
| P4      | Redirect-after-action helper | New `utils.py`; `routes.py` |

Completing P0 and P1 gives the largest immediate benefit (no broken code, single auth and flash UI). P2 and P3 decouple access control and business UI. P4 is a small cleanup for consistency.
