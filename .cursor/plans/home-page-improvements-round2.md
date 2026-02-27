# Plan: Home Page Improvements (Feedback Round 2)

## Context

Implement the latest external feedback captured in vision.md (Home Page Redesign): softer hero-to-body transition, clearer dual-audience segmentation, more prominent nav CTA, 4-Step Sprint visible at a glance (timeline or larger icons), better spacing and typography, payment clarity, quality/screening proof, and uniform testimonial cards.

---

## Files Affected

| File | Changes |
|------|--------|
| `backend/app/templates/home.html` | Nav: add "Are you a developer? Apply here" link; enlarge primary CTA and logo/links. Hero: optional audience toggle or developer CTA; tighten subheadline→CTA gap; strengthen subheadline weight/color. 4-Step: add vertical timeline or step labels so all steps visible; enlarge Step 2 (screening) mock. Why JrDev: reduce margin above "See JrDev in action"; add padding/line-height in cards. Payment: add one line "How it works" (per-sprint, you set budget). Testimonials: add class for min-height. For Students/For Businesses: stronger card border; larger bullet text. Section wrappers: use new light-lavender/grey background classes. |
| `backend/app/static/css/home.css` | New section background (e.g. `--section-light: #f5f3ff` or similar lavender-grey); hero→first-section gradient or transition; nav logo/link/CTA sizes; hero subheadline font-weight and color; hero CTA margin; sprint section padding and timeline styles; Why JrDev card padding and gap-to-video; testimonial card min-height; comparison card border and bullet font-size; any new utility classes. |
| `backend/app/static/js/home.js` | No structural change required; tab behavior stays. If timeline is clickable to switch steps, add click handlers on timeline steps that call existing setActive(index). |

---

## Steps

### Phase 1 — Nav, hero, spacing, and color

1. **Nav bar (home.html + home.css)**  
   - Add a clear developer entry: e.g. "Are you a developer? **Apply here**" as a text link in the top nav (desktop), and in the mobile menu, so students segment immediately.  
   - Increase size of logo (e.g. `text-2xl` → `text-3xl`), nav links (e.g. `text-base` → `text-lg` or `font-medium` + slightly larger), and especially the primary CTA: make "Hire Talent" larger (e.g. `px-6 py-3` → `px-8 py-3.5`), bolder, and ensure it uses `home-cta-primary` / `btn-gradient` so it pops.  
   - In `home.css`, add or adjust `.home-nav` rules so the primary CTA has a minimum size and stands out (e.g. font-size, padding) in both hero and scrolled states.

2. **Hero section (home.html + home.css)**  
   - Tighten the gap between the hero subheadline and the CTA buttons: reduce `mt-6` on the CTA wrapper to `mt-4` or `mt-5`, and ensure the "Starting at £50" line is still close below.  
   - Make the hero subheadline more readable: in `home.css`, for `.home-hero-subheadline`, increase `font-weight` (e.g. 500 or 600) and lighten color from `text-slate-200` to a brighter grey (e.g. `#e2e8f0` or use a class that sets a higher contrast). In `home.html`, ensure the subheadline uses that class.  
   - Keep "Students: get paid to build…" as a secondary line; optionally add a small "I'm a developer" link or pill next to the CTAs that scrolls to #students or links to register as DEVELOPER so the hero segments both audiences.

3. **Section backgrounds and hero→body transition (home.css + home.html)**  
   - Define a light lavender-grey token, e.g. `--home-section-light: #f5f3ff` or `#f1effa`, and use it for the first section after the hero (4-Step Sprint) and optionally for other light sections (Why JrDev, testimonials, etc.) so the page doesn’t go from dark hero to stark white.  
   - Add a short gradient or darker band between hero and first section: e.g. on `.sprint-section` or a wrapper, use `background: linear-gradient(180deg, rgba(15,23,42,0.98) 0%, var(--home-section-light) 100%)` or a 10–15vh transition strip so the "zebra" effect is softened.  
   - Replace `bg-slate-50` / `bg-slate-100` on alternating sections with the new lavender-grey where it fits the design system (vision: "very light lavender/grey for light sections").

4. **Why JrDev and "See JrDev in action" (home.html + home.css)**  
   - Reduce the gap between the Why JrDev cards and the "See JrDev in action" heading: in `home.html` reduce `mb-16` on the Why JrDev wrapper or add negative margin / reduce padding on `.home-trust` so the section spacing is smaller.  
   - Give Why JrDev card body text room to breathe: in `home.css`, add padding and/or line-height for `.home-glass-card p` (e.g. `padding-inline`, `line-height: 1.6`), and in `home.html` ensure cards use the same class.  
   - Slightly increase font size/weight of the body text inside Why JrDev cards if it’s still too small (e.g. `text-base` → `text-[1.0625rem]` and `font-medium: 400` → 500 for first line or keep 400 with larger size).

5. **Testimonials (home.html + home.css)**  
   - Add a shared class for testimonial cards (e.g. `home-review-card`) and in `home.css` set `min-height` (e.g. `min-height: 220px` or 240px) so all three cards are uniform height and the section feels symmetrical.

6. **For Students / For Businesses cards (home.html + home.css)**  
   - Strengthen card borders: change `border-2 border-slate-300` to a more visible border (e.g. `border-2 border-slate-300` with a darker shade, or add a subtle background tint so they don’t look floating). In `home.css`, add a rule so the cards have a clear border or background (e.g. `border-color: #cbd5e1` or `background: #fefefe` with border).  
   - Increase bullet point text size: for the `<p class="text-slate-600 ... text-sm">` inside the comparison cards, change to `text-base` (or add a class in `home.css` like `.home-comparison-card .card-desc { font-size: 1rem; }`) so the bullet descriptions are more readable.

### Phase 2 — 4-Step Sprint and conversion copy

7. **4-Step Sprint: visible at a glance (home.html + home.css + optional home.js)**  
   - Add a **vertical timeline** or a row of **four step labels with icons** above or beside the tab list so users see all four steps without clicking. Options:  
     - (A) A vertical timeline on the left (or top on mobile) with "Step 1", "Step 2", "Step 3", "Step 4" and one-line descriptions, and the existing tab content on the right (or below). Clicking a timeline step or tab updates the visible panel (reuse existing `home.js` setActive).  
     - (B) A horizontal strip of four larger blocks (icon + title) that are always visible; the active one is highlighted and the content panel below shows the corresponding step.  
   - Keep the existing tab list for accessibility and keyboard nav; ensure the new timeline/steps are either the same elements (styled differently) or trigger the same `setActive(index)` so the panel and visual update clearly when switching.  
   - Give the 4-Step section more room: increase `py-24` to `py-28` or `py-32` and ensure the step content and visual have enough padding so it doesn’t feel cramped.

8. **Developer Screening (Step 2) proof (home.html + home.css)**  
   - Make the Step 2 panel visual larger and readable: increase the mock window size (e.g. scale the font sizes inside the screening mock from `text-[10px]` / `text-xs` to `text-xs` / `text-sm` where possible, and make the container `lg:w-7/12` take more width or use a larger min-height).  
   - Add one short line of copy near Step 2 heading or in the panel: e.g. "Hand-picked talent — you review applicants and only onboard who fits" or "Quality oversight: you choose who builds your product" so the quality objection is addressed.

9. **Payment "How it works" (home.html)**  
   - Add a single sentence near the "Starting at £50" line or in the More Information / Pricing area: e.g. "You set the budget per developer when you launch a sprint — no hourly fees or subscription." So the financial model is clear and reduces click-fear.

### Phase 3 — Polish and consistency

10. **Copy pass (home.html)**  
    - Confirm "Cost-Effective" is used everywhere (no "Cheap"); ensure 4-Step step 1 copy is punchy (e.g. "We match you with the right developer in 24 hours" if accurate).  
    - No new templates or routes required.

11. **Feedback check**  
    - After implementation, run the Feedback skill: check nav on mobile, hero contrast, section transition, timeline/tabs on small screens, and that both roles (developer vs business) can see their path immediately.

---

## Dependencies

- None. No new pip packages, env vars, or migrations. Uses existing Tailwind and `home.css` / `home.js`.

---

## Risks / Notes

- **Timeline vs tabs**: If the 4-Step section becomes a vertical timeline on desktop, ensure mobile stacks cleanly (timeline above content or simplified to a dropdown/accordion) so the Feedback agent can verify no layout break.  
- **Contrast**: When lightening the hero subheadline, ensure it still passes contrast on the dark hero background (aim for at least AA).  
- **Design system**: Keep purple/indigo as primary; green only for success. Don’t introduce new accent colors.  
- **Video**: YouTube embed is already present; no change needed there.  
- **vision.md**: No new pages or models; no vision.md update required unless we add a new reusable component pattern (e.g. "home timeline") to the Design System section later.
