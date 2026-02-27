# Plan: Home Page Redesign (Startup Website)

## Context

Redesign the JrDev landing page so it feels more professional, trustworthy, and conversion-focused, based on external feedback. Vision is captured in `.cursor/skills/vision.md` (Home Page Redesign + Content Decisions). Key goals: balance audience (students + businesses), tighten layout, improve nav/sprint UX, add video embed + pricing + reviews placeholder, fix copy/contrast/colour hierarchy.

---

## Files Affected

| File | Changes |
|------|--------|
| `backend/app/templates/home.html` | Nav (larger logo/links), hero (tighter spacing; student value hint; pricing "Starting at £50"; quality line), "Cheap" → "Cost-Effective", Why JrDev text size, 4-step punchier copy, video → YouTube embed, reviews section (placeholder), alternating section backgrounds, comparison card borders, footer CTA hierarchy (purple primary). |
| `backend/app/static/css/home.css` | Alternating section backgrounds (zigzag), nav logo/link size, hero spacing, sprint panel transition (fade/slide so step change is obvious), Why JrDev card body text size, comparison card border/contrast. |
| `backend/app/static/js/home.js` | Optional: light transition when switching panels (e.g. trigger class for CSS fade-in) so the visual change is clearer. |

---

## Steps

1. **Navigation**
   - In `home.html`: increase logo size (e.g. `text-xl` → `text-2xl`, icon one step up) and nav link text (e.g. `text-sm` → `text-base`) for desktop and ensure mobile menu matches.
   - In `home.css`: add/override `.home-nav` styles so logo and `.nav-link-animated` are larger at high resolution if needed.

2. **Hero**
   - Reduce vertical gap between subheadline and CTA buttons (e.g. `mt-10` → `mt-6` or similar in `home.html`).
   - Add a short “for students” line or badge near the CTAs (e.g. “Get paid to build real projects” or “Join as Developer” with a one-line benefit) so student value is visible without hunting.
   - Add “Starting at £50” near the primary CTA (e.g. below the buttons or as a small line).
   - Add one line about quality / hand-picked talent (e.g. “Hand-picked student developers” or “Quality oversight on every sprint”) near hero or Why JrDev.

3. **Section grounding (zigzag)**
   - In `home.html`: assign alternating background classes to sections. Example: hero (dark, keep); sprint-section (keep or light); Why JrDev section → add e.g. `bg-slate-50 dark:bg-slate-900/30`; trust/video section → no bg or white; comparison section already has `bg-slate-100`; More Information → keep or alternate; final CTA section → no bg or subtle.
   - In `home.css`: ensure one consistent “alt” background token (e.g. subtle off-gray) so the zigzag is clear.

4. **Sprint section**
   - In `home.html`: replace Step 1 copy with punchier line where relevant (e.g. “We match you with the right developer” / “Get matched in 24 hours” — align with actual process).
   - In `home.css`: replace instant hide with a short transition: e.g. `.sprint-panel` opacity/transform and `.sprint-panel--hidden` with transition so when `home.js` toggles panels, the new panel fades or slides in (duration ~200–300ms).
   - Optionally in `home.js`: when `setActive(index)` runs, add a temporary class to the newly visible panel for a brief “entered” animation (e.g. fade-in); remove after transition.

5. **Why JrDev**
   - In `home.html`: change “Cheap Prototyping” to “Cost-Effective” or “Budget-Friendly” and keep the rest of the card copy.
   - In `home.html` + `home.css`: increase body text size/weight in the three value cards (e.g. `text-slate-600` paragraph to `text-base` or slightly larger) so it’s consistent with headers.

6. **Video**
   - In `home.html`: replace the gray video placeholder (`.home-video-placeholder` block with play button) with a responsive YouTube embed for `https://www.youtube.com/watch?v=ujdFPoCeFM4` (e.g. 16/9 wrapper, `iframe` with `embed` URL). Keep the section heading “See JrDev in action” (or similar).

7. **Reviews section**
   - In `home.html`: add a new “Reviews” or “What people say” section (e.g. after trust/video or after comparison). Structure: heading, 1–3 placeholder review cards (quote, name, role/context, optional star rating). Use placeholder text (e.g. “Review from a business after their first sprint.”) and a clear structure so you can fill in real testimonials/ratings later. Style with existing design tokens (glass or cards).

8. **Trust / risk**
   - Keep or refine the “Trusted by universities and startups” bar; ensure the new reviews section is the main “proof” block. Add or keep one line about quality/vetting (if not already in hero) in Why JrDev or near the video.

9. **For Students / For Businesses cards**
   - In `home.html` + `home.css`: strengthen the comparison cards so they’re not “floaty”—e.g. slightly stronger border (`border-slate-300` or `border-white/20` in dark) or a subtle background tint so the cards have clear edges.

10. **Colour hierarchy**
    - In `home.html`: ensure hero and footer CTAs are consistent: primary = purple (“Hire Talent” / “Post a Sprint”), secondary = “Join as Developer” (outline or secondary style, not green). In footer, change “Join as Developer” from green/teal to a secondary style (e.g. outline or muted) and make “Post a Sprint” / “Hire Talent” the single dominant purple CTA where applicable.
    - In `home.css`: use green only for success states (e.g. checkmarks, success messages), not for primary CTAs.

11. **Pricing link**
    - Ensure the nav “Pricing” link points to `#pricing` or a pricing block on the page. If there is no pricing page yet, add an in-page anchor (e.g. `id="pricing"`) near “Starting at £50” so the nav works.

---

## Dependencies

- None (no new packages or env vars). YouTube embed is static iframe; no backend change.

---

## Risks / Notes

- **Feedback**: After implementation, run the Feedback skill to check contrast, mobile nav, and CTA hierarchy.
- **Reviews**: Placeholder content only; copy should make it obvious that real reviews will appear later (e.g. “What our users say” with one generic placeholder card).
- **Sprint copy**: “Match in 24 hours” is an example; align with actual business process (e.g. “We match you with developers who fit your stack” if timing differs).
