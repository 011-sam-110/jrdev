# Plan: Developer Dashboard Improvements

## Context

Professional feedback: sharpen the developer dashboard from "personal project" to "production-ready product" while keeping the Neon/Liquid Glass aesthetic. Improvements cover profile fallbacks, empty states, information hierarchy, form polish, glow consistency, and mobile responsiveness.

---

## Files Affected

| File | Changes |
|------|--------|
| `backend/app/templates/developer_layout.html` | Nav profile avatar: use initials fallback when no custom image (same pattern as dashboard). |
| `backend/app/templates/developer_dashboard.html` | Profile card: initials/SVG fallback when no image; Stats: larger accent numbers; Pinned Projects: centered empty state with clear CTA; optional glow tweak for panels. |
| `backend/app/templates/edit_profile.html` | Profile picture area: show initials fallback when no image; ensure all inputs use shared focus border + placeholder styles. |
| `backend/app/templates/developer_joined_listings.html` | Deliverables list: increase line-height and spacing between items; Submit Work inputs: use shared form styles; success flash: show as celebratory toast when present. |
| `backend/app/static/css/developer_themes.css` | Stats: new class for stat number (larger, accent color); optional: unify card glow (subtle on all panels or remove from avatar ring / reserve for CTA). |
| `backend/app/static/css/liquid-glass.css` | Global form inputs: 1px border, brighter on `:focus`; placeholder contrast (readable but distinct). |
| `backend/app/static/css/main.css` | If developer form styles live here, add focus border and placeholder rules for developer forms; otherwise rely on liquid-glass + developer_themes. |
| `backend/app/utils.py` (or new template filter) | Optional: add `initials_from_username(username)` for avatar fallback (e.g. "John Doe" → "JD"). Can be done in template with Jinja. |
| New: `backend/app/templates/partials/avatar_fallback.html` or inline in templates | Reusable snippet: when no profile image, render circular SVG or div with initials (from `current_user.username`). |

---

## Steps

### 1. Profile image fallback (initials avatar)

- **Backend (optional):** In `utils.py` add a small helper or template filter `initials_from_username(name)` that returns up to 2 uppercase letters (e.g. first letter of first two words, or first two chars of username). If not added, derive initials in Jinja (e.g. first two chars of `current_user.username`).
- **Reusable fallback:** Add a partial or macro used by layout, dashboard, and edit_profile:
  - **When to show:** `current_user.image_file` is None, empty, or `'default.jpg'` (or when image fails to load — optional enhancement).
  - **What to show:** A circular container (same size as profile image) with stylized initials (e.g. "AD") using theme accent color, matching `dev-avatar-ring` / nav styling.
- **developer_layout.html:** In the nav profile block, when there is no custom image, replace the current icon div with the initials fallback (same circle size, link to logout or profile).
- **developer_dashboard.html:** Replace the profile card `<img>` with conditional: if user has custom image (and not default.jpg), use `<img>`; else render the initials fallback so the avatar ring and layout stay the same.
- **edit_profile.html:** In the "Profile Picture" section, when `current_user.image_file` is missing or default, show the initials fallback circle (e.g. 24×24 or 96×96) so users see a proper preview instead of blank or "Profile" text.

### 2. Pinned Projects empty state

- **developer_dashboard.html:** In the Pinned Projects section, when `not profile.pinned_projects`:
  - Replace the current small centered text + folder icon with a **more prominent empty state**: larger icon or simple illustration, short headline (e.g. "No projects pinned yet"), and a **primary CTA button in the center** (e.g. "Add your first project") that triggers the same "Add Project" flow (e.g. `id="toggle-add-project"` or scroll/focus to the add form). Keep the existing "Add Project" button in the header for consistency; the empty state CTA should be the main focus inside the card.

### 3. Stats card hierarchy

- **developer_themes.css:** Add a class for stat numbers, e.g. `.dev-stat-value`, with:
  - Larger font size (e.g. 1.5rem–2rem),
  - Color: theme accent (`var(--dev-accent)` or Mint/Neon),
  - Font weight bold.
- **developer_dashboard.html:** Apply this class to the three stat values (Prototypes Attempted, Prototypes Completed, Avg Rating) so the numbers are the visual focus; keep labels as secondary (current text-sm text-slate-400).

### 4. Deliverables readability (Joined Listings)

- **developer_joined_listings.html:** For the "Deliverables (from contract)" list (`listing.deliverables_only_list`):
  - Add **increased line-height** to the list items (e.g. `leading-relaxed` or 1.6),
  - Add **margin between items** (e.g. `space-y-3` instead of `space-y-1.5`) so long lines (e.g. marketplace UI description) are easier to scan.

### 5. Form input styling (global for developer forms)

- **liquid-glass.css:** Ensure inputs and textareas used in developer area have:
  - **1px border** (e.g. `border border-white/15` or similar) that **brightens on `:focus`** (e.g. border-color using primary-mint at higher opacity),
  - **Placeholder:** readable contrast (e.g. `text-slate-500`) but clearly distinct from filled text (e.g. `text-slate-200`).
- Apply these classes (or a single `.dev-input` / `.liquid-glass-input`) consistently on:
  - **developer_dashboard.html:** Add Project form inputs, markdown textarea.
  - **edit_profile.html:** All text inputs and textareas (headline, location, availability, technologies, etc.).
  - **developer_joined_listings.html:** GitHub URL, demo video URL, and any other inputs in the Submit Work form.
- If Tailwind is used inline, add utility classes for `focus:border-mint/50` and `placeholder:text-slate-500` where needed; otherwise extend `liquid-glass-input` in CSS.

### 6. Success feedback for "Upload Prototype"

- **Backend:** Already flashes `"Prototype submitted! The business will review your work."` with category `success` — no change required.
- **developer_joined_listings.html** (or developer_layout flash block): When the page loads with a success flash, show it in a **toast-style** treatment:
  - Option A: In `developer_layout.html`, style the existing flash container so success messages have a checkmark icon, slightly larger/prominent styling, and optional short auto-dismiss animation so the transition feels celebratory.
  - Option B: On `developer_joined_listings.html`, if `get_flashed_messages(with_categories=true)` includes a success, inject a small script or block that shows a brief "Success" toast (e.g. green/mint, checkmark) that fades in and then out, in addition to or instead of the standard flash position.
- Prefer Option A (reuse existing flash) with enhanced success styling and icon so all developer success messages (including after submit) feel celebratory without extra JS.

### 7. Glow consistency

- **developer_themes.css:** Today the profile **avatar ring** (`.dev-avatar-ring`) has a visible box-shadow glow; **About Me** and other panels get glow on hover when `data-animation="glow"`. Feedback: "About Me has a heavy purple outer glow, others don't — lopsided."
- **Decision:** Either (1) apply a **very subtle** glow to all `.dev-panel` / `.dev-card` (e.g. reduced box-shadow so all cards feel even), or (2) **reserve glow for active/CTA only** (e.g. remove or reduce glow from avatar ring and from default panel state; keep glow on hover for CTA buttons and maybe active nav item).
- **Implementation:** In `developer_themes.css`, adjust `.dev-avatar-ring` so its default glow is subtler (e.g. smaller spread, lower opacity), and ensure no single panel has a stronger default glow than others. If keeping "glow" animation, make hover glow consistent across all panels (same shadow value) so the page doesn’t feel lopsided.

### 8. Mobile & responsiveness (dashboard sidebar)

- **Current:** Dashboard uses `grid lg:grid-cols-12` with sidebar `lg:col-span-4` and main `lg:col-span-8`. On viewports below `lg`, the sidebar stacks above the main content (no left sidebar squashing). The **nav** is already a top bar with hamburger on small screens.
- **Check:** Confirm that below `lg` the layout is single-column and the "sidebar" (profile card, tech stack, stats) appears **above** the main content so nothing is squashed. If the layout already stacks, add a single **breakpoint check** and, if needed, ensure the left column has a clear visual order (e.g. `order-2` / `order-1` so main content can come first on mobile if desired).
- **If a true "drawer" is desired:** Add a breakpoint (e.g. `md` or `lg`) below which the dashboard shows a **collapsible drawer** for "Profile & stats" (button to open) instead of a full-width stacked block, so content area gets more room. This is a larger UX change; the plan prefers the simpler approach first: ensure stacking works and optionally add a "Show profile" toggle that reveals the sidebar block on small screens (accordion or slide-down) so the default view is content-first.
- **Steps:** (1) Verify current responsive behavior; (2) add or adjust breakpoints so sidebar content doesn’t squash main content; (3) if needed, add a small JS toggle to show/hide the sidebar section on small screens (e.g. "Profile & stats" collapsible section).

---

## Dependencies

- None. No new pip packages, env vars, or migrations. Optional: add a template filter in `app/__init__.py` or `utils.py` for `initials_from_username` if not doing initials in Jinja.

---

## Risks / Notes

- **Avatar fallback:** If `default.jpg` exists in `profile_pics/`, consider whether to still show initials (recommended: treat default.jpg as "no photo" and show initials for consistency).
- **Flash styling:** Enhancing the success flash in the layout affects all developer success messages (profile updated, project pinned, prototype submitted). Ensure danger/info flashes remain clearly distinct.
- **Glow:** Reducing avatar glow might make the profile area feel less "signature"; keep it subtle but present so the dashboard still feels on-brand.
- **Mobile drawer:** If the team later wants a full drawer (slide-over) for the dashboard sidebar, that can be a follow-up; this plan prioritizes correct stacking and optional collapsible section.
- **Feedback agent:** After implementation, check: (1) no broken profile images anywhere, (2) empty state CTA is obvious and works, (3) stat numbers are clearly the focus, (4) deliverables list is easy to scan, (5) inputs have visible focus and placeholders, (6) success after submit is clearly visible, (7) card glow is consistent, (8) small viewport layout is usable.
