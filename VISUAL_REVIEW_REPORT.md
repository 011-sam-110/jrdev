# Visual Review Report — JrDev Platform (Strict)

Review conducted against the product vision (`.cursor/skills/vision.md`) and design system. Amendments have been applied where indicated.

---

## Visual Review: Billing & payment

**Screenshot:** Billing page with “Add payment method” card and “How billing works” section.

### Pass
- Dark theme and liquid-glass panels align with design system.
- Navigation and hierarchy are clear.
- “How billing works” bullets with checkmarks are consistent.

### Issues
1. **Warning** — Security message (“Secured by Stripe…”) too small and low prominence.
   - **Fix:** In `backend/app/templates/billing.html` increased text to `text-sm`, added `font-medium`, and made icon `text-lg` and `text-primary` for better visibility.

### Summary
Needs fixes → **Fixed.**

---

## Visual Review: Create Account (Register)

**Screenshot:** Registration form with username, email, role dropdown, password, terms checkbox.

### Pass
- Card layout and typography match auth layout.
- Primary CTA (Sign Up) is clear.

### Issues
1. **Warning** — “Register as” dropdown used dark background vs light inputs; inconsistent.
   - **Fix:** In `register.html` applied `liquid-glass-input` and `text-navy-900` to the role select so it matches other auth inputs.
2. **Nit** — Footer links (Privacy, Terms, Support) looked too muted vs in-card links.
   - **Fix:** Set footer links to `text-slate-400` with `hover:text-primary` for consistency.

### Summary
Needs fixes → **Fixed.**

---

## Visual Review: Login

**Screenshot:** Welcome Back form with email, password, Remember Me, Forgot Password, Login button.

### Pass
- Card and button styling match design system.
- “Get Started” CTA is clear.

### Issues
1. **Warning** — “Login” link in header when already on login page is redundant and inconsistent with “Get Started” button.
   - **Fix:** In `login.html` removed the “Login” nav link from the login page so only “Get Started” remains.
2. **Nit** — “Remember Me” checkbox and “Forgot Password?” link alignment.
   - **Fix:** Wrapped in a flex container with `items-center`, label uses `inline-flex items-center`, and “Forgot Password?” uses `inline-flex items-center` for baseline alignment.

### Summary
Needs fixes → **Fixed.**

---

## Visual Review: Joined Listings (Developer)

**Screenshot:** List of joined sprints with status badges, contract actions, deliverables section.

### Pass
- Status badges (Pending, Complete, Cancelled) are distinct.
- Liquid-glass panels and spacing are consistent.

### Issues
1. **Nit** — “X task(s)” should be singular when value is 1.
   - **Fix:** In `developer_joined_listings.html` changed to `{{ listing.minimum_requirements_for_pay }} task{{ 's' if listing.minimum_requirements_for_pay != 1 else '' }}`.

### Summary
Needs fixes → **Fixed.**  
*(Note: “Source code (GitHub)” pointing to a non-GitHub URL is user-submitted content; no template change.)*

---

## Visual Review: Edit Profile

**Screenshot:** Edit profile form with picture, identity, skills, appearance (themes), social links.

### Pass
- Sections and theme swatches match developer design system.
- Appearance options are clear.

### Issues
1. **Nit** — Skills hint (“Comma separated…”) risk of truncation.
   - **Fix:** In `edit_profile.html` added `break-words` to the hint paragraph.
2. **Nit** — Animations description used semicolons; less scannable.
   - **Fix:** Replaced with full stops: “Glow: … Shimmer: … Float: …”
3. **Warning** — Cancel button very low contrast.
   - **Fix:** In `edit_profile.html` gave Cancel `border border-white/20`, `text-slate-300`, and `hover:bg-white/10 hover:text-white`.

### Summary
Needs fixes → **Fixed.**

---

## Visual Review: Contract PDF (View)

**Screenshot:** First page of SOFTWARE DEVELOPMENT NON-DISCLOSURE & SPRINT AGREEMENT.

### Pass
- Sections (Parties, Sprint & Compensation, Deliverables, IP) are structured.
- Typography and margins are readable.

### Issues
1. **Critical** — Payment Trigger could say “at least 5 of the 3 Optional tasks” when min_tasks > total_count (impossible).
   - **Fix:** In `backend/app/contract_pdf.py` capped `min_tasks` at `total_count` for optional-only and mandatory+optional cases; same cap for legacy tasks.
2. **Warning** — Currency shown as “£20.0”; should use two decimals for consistency.
   - **Fix:** In `contract_pdf.py` format pay as `f"{pay_val:.2f}"` (e.g. £20.00).

### Summary
Needs fixes → **Fixed.**

---

## Visual Review: Your Listings (Business)

**Screenshot:** Sprint cards with developers who joined, progress & review, sidebar “Sprint Info & Legal”.

### Pass
- Phase messaging (waiting for start, awaiting contracts, review) is clear.
- Status badges and actions are consistent.

### Issues
1. **Warning** — When all signups are cancelled, “Progress & review” showed “No developers on this sprint yet,” which conflicts with “Developers who joined” above.
   - **Fix:** In `business_dashboard_your-developers.html` when `developers` is empty but `listing.signups` exists, show “No active developers on this sprint.” and “Developers who joined have withdrawn, been removed, or are still pending.”

### Summary
Needs fixes → **Fixed.**

---

## Visual Review: Sprint Creator (Business Dashboard)

**Screenshot:** Idea box, essential/optional deliverables, technologies, contract dates, Launch Sprint, Sprint Summary sidebar.

### Pass
- Sidebar sliders and totals match vision.
- Liquid-glass panels and hierarchy are correct.

### Issues
1. **Nit** — “Minimum 50 words recommended” is slightly awkward.
   - **Fix:** In `business_dashboard.html` changed to “At least 50 words recommended.”
2. **Warning** — “1 TASKS” in Sprint Summary should be “1 TASK” when value is 1.
   - **Fix:** In `business_dashboard.html` added class `min-requirements-label` and default text “task”. In `business_dashboard.js` added `minRequirementsLabel` and in `updateInvestmentDisplay` set label to “task” when value is 1, “tasks” otherwise.

### Summary
Needs fixes → **Fixed.**

---

## Visual Review: Terms & Conditions / Privacy Policy

**Screenshot:** Info pages with section headings and body text.

### Pass
- Dark content block and section structure are readable.
- Footer and header match info_layout.

### Summary
No code changes applied; icon/link consistency can be refined in a later pass if needed.

---

## Visual Review: Developer profile / Developer Listings / Home

**Screenshot:** Developer profile (dashboard), Open Listings, Home hero and 4-step.

### Pass
- Developer themes and glass panels align with vision.
- Home hero and CTA sections use correct layout.
- Listings use liquid-glass cards.

### Summary
Placeholder content (e.g. “dwadwa”, “Cheap labour”) is user data. Tag capitalization (Tech Stack vs Pinned Projects) and nav spacing can be standardized in a design-system pass. No critical template fixes applied in this round.

---

## Overall

- **Pages reviewed:** Billing, Register, Login, Joined Listings, Edit Profile, Contract PDF, Your Listings, Sprint Creator, Terms, Privacy, Developer profile, Developer Listings, Home.
- **Critical:** 1 (contract payment trigger logic) — **Fixed.**
- **Warnings:** 6 — **Fixed.**
- **Nits:** 5 — **Fixed.**

All listed fixes have been implemented in the codebase.
