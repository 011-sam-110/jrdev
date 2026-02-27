# Plan: Business Dashboard Improvements

## Context

Improve the business area based on user feedback: (1) Dashboard page — prioritize action with a hero metric, "Attention Required" block, and friendly empty states; (2) Developers (Your Listings) page — prominent search, quick filters, status pills, row hover; (3) Billing page — direct Download/View PDF pattern, prominent next billing info, card brand icon; (4) Global polish — stronger active nav, consistent card spacing, geometric sans (Inter) for dashboard. Vision is in `.cursor/skills/vision.md` (Business Dashboard Improvements).

---

## Files Affected

| File | Changes |
|------|--------|
| `backend/app/routes.py` | Dashboard route: compute and pass `attention_items`, `stats` (hero + secondary metrics). Optional: billing route pass `next_billing_*` / invoice list if we add placeholder data. |
| `backend/app/templates/business_dashboard.html` | Add at top: Attention Required block (only if items). Add stats row: one hero metric (e.g. Active Developers) 2× size, 2–3 smaller metric cards. Empty state for "Your Listings" when none (skeleton or Get Started CTA in panel). |
| `backend/app/templates/business_dashboard_your-developers.html` | Prominent search bar (top left/center). Quick filter pills (Active, Onboarding, Offboarding). Status pills with dot + low-opacity background. Row hover class on developer `<li>` rows. Optional: data attributes for JS filtering. |
| `backend/app/static/js/business_dashboard.js` | Optional: filter/search logic for developers page if we add a dedicated script for it, or inline in template. |
| `backend/app/templates/billing.html` | Card on file: add small Visa/Mastercard icon next to brand text. Add "Next billing date" / "When you're charged" prominent block. Add "Invoice history" section: table with empty state and visible "Download" / "View PDF" button column (placeholder rows or "No invoices yet" for now). |
| `backend/app/templates/business_layout.html` | Stronger active nav: high-contrast accent (e.g. vibrant blue/purple background or left border) for active link; ensure `nav_active` is passed and used. |
| `backend/app/static/css/liquid-glass.css` or new `backend/app/static/css/business_dashboard.css` | Consistent card spacing (e.g. `.business-card-spacing` or standardise `gap`/`padding` for panels). Row hover style for developer rows. Status pill styles (dot + pill). Optional: business layout overrides. |

---

## Steps

### Phase 1: Dashboard page (Sprint Creator) — action and hierarchy

1. **Backend: stats and attention items**
   - In `dashboard()` (business branch): query `SprintListing` and `ListingSignup` for current user. Compute:
     - `active_developers`: count of signups with status `accepted` and `is_fully_signed`.
     - `total_listings`, `open_listings` (or similar).
     - Optional: `total_spend` if we have payment data (otherwise omit or use "—").
   - Build `attention_items` list: e.g. "X Pending applicants" (signups pending), "X Awaiting your signature", "X Pending invoices" (if we add placeholder). Each item: `{ 'text': str, 'url': str, 'count': int }`.
   - Pass to template: `stats` (dict with hero + secondary), `attention_items`.

2. **Template: Attention Required**
   - At the very top of `business_dashboard.html` content (above "Kickstart Your Innovation"), add a conditional section: if `attention_items`, render a compact bar or card with short messages and links (e.g. "2 Pending applicants → Review", "1 Awaiting your signature → Sign"). Use existing liquid-glass panel styling.

3. **Template: Stats row with hero metric**
   - Below the header (or below Attention Required), add a row of metric cards:
     - One **hero** card: e.g. "Active Developers" with large number (2× font size), same panel style.
     - 2–3 **secondary** cards: e.g. Open Listings, Total Listings (or similar). Use same `liquid-glass-panel` but smaller typography.
   - Use consistent gap (e.g. `gap-4` or `gap-6`) between cards.

4. **Template: Empty states**
   - "Your Listings" section: when `my_listings` is empty, instead of hiding the section, show the panel with a "Get Started" message and CTA ("Launch your first sprint") and optional skeleton placeholder so the layout doesn’t look broken.
   - If stats are zero (e.g. 0 active developers), show the number as "0" with optional short line like "Developers will appear here once they join" so it doesn’t look like a missing value.

### Phase 2: Developers page (Your Listings) — search and filters

5. **Search and quick filters**
   - In `business_dashboard_your-developers.html`, add at the top of the main column (below header):
     - A search input (placeholder "Search developers by name or email"), prominent (e.g. max-w-md or full width on mobile).
     - Quick filter pills: "All", "Active", "Onboarding", "Offboarding". Map to: Active = accepted & fully signed; Onboarding = pending or awaiting signature; Offboarding = denied/cancelled/withdrew.
   - Use data attributes on listing/signup rows (e.g. `data-status`, `data-name`) so JS can filter, or implement server-side filter (new query params) for a second iteration. Prefer client-side for MVP so we don’t change route.

6. **Status indicators**
   - Replace or augment plain text status with **pills**: green dot + "Active" (low-opacity green bg), amber for Onboarding, red/gray for Offboarding. Use classes like `status-pill status-pill--active` and CSS for dot + background.

7. **Row hover**
   - On each developer row (`<li>` in "Developers who joined" and any other developer row), add a class (e.g. `developer-row`) and in CSS set `transition` and `hover:bg-white/10` (or similar) so the row highlights on hover.

8. **Filtering JS (optional)**
   - If client-side: in `business_dashboard.js` or a small inline block on the developers page, on input/filter change, show/hide rows or listing sections by name and status. Keep it simple (e.g. filter by text match and status class).

### Phase 3: Billing page — clarity and trust

9. **Card brand icon**
   - In `billing.html`, in the "Card on file" section: next to "Visa ending in **** 1234", add a small icon (SVG or inline icon for Visa/Mastercard/Amex). Use `card_brand` (lowercase) to choose which icon to show. Can use Material Symbol "credit_card" with a small brand logo via img or SVG sprite if available; otherwise a simple coloured badge or text icon.

10. **Next billing date / when you’re charged**
    - Add a prominent block (e.g. above or below "Card on file"): "When you’re charged" — "Your card is charged when you launch a sprint. No recurring fees." If we ever have subscription or next invoice date, display it here. For now, copy is enough.

11. **Invoice history**
    - Add a section "Invoice history". Table columns: Date, Description, Amount, Action (Download / View PDF). For now: no backend invoice list (Stripe charging not implemented), so show empty state "No invoices yet. Invoices will appear here after you complete sprints." When we add invoice data later, each row gets a visible **button** "Download" or icon (not inside a three-dot menu).

### Phase 4: General UI/UX polish (business area)

12. **Navigation active state**
    - In `business_layout.html`, change the active nav link style from only `text-primary border-b-2` to a **high-contrast** treatment: e.g. background `bg-primary/20` or `bg-white/10`, or left border `border-l-4 border-primary`, plus bold text so the current page is unmistakable. Ensure all business routes pass correct `nav_active` ('sprint', 'developers', 'billing').

13. **Consistent card spacing**
    - Audit `business_dashboard.html`, `business_dashboard_your-developers.html`, `billing.html`: use one spacing token for gaps between cards (e.g. `space-y-6` or `gap-6`). If some use `space-y-4` and others `space-y-8`, standardise to one value (e.g. `space-y-6`) so the eye doesn’t get inconsistent gaps.

14. **Typography**
    - Ensure `business_layout.html` (and thus all business pages) uses `font-body` (Inter). It’s already set on `body` in layout; confirm no override to system font. No new font file needed; vision says Inter for body.

---

## Dependencies

- No new pip packages.
- No new env vars.
- Optional: if we add invoice list later, we may need Stripe Invoice API or a local Invoice model; for this plan, invoice section is UI-only with empty state.

---

## Risks / Notes

- **Dashboard stats**: "Total Spend" requires payment/charge data. If we don’t have it, use "Active Developers" as hero and "Open Listings" / "Total Listings" as secondary to avoid misleading numbers.
- **Developers page**: The page is listing-centric (accordions). Search/filter can either (a) filter the visible list of signups inside each expanded listing, or (b) collapse/expand listings based on match. (a) is simpler: one flat list of "developers who joined" with search/filter that shows/hides rows. Current template has signups nested per listing; consider adding a single "All developers" flat list for power users, or apply filter per listing. Recommend: keep structure, add search that filters by name/email across all signups (JS hides non-matching rows in each section) and filter pills that show/hide by status.
- **Billing**: "Next billing date" — we have no subscription; copy should say "You’re charged when you launch a sprint." Invoice history is placeholder until charging is implemented.
- **Feedback**: After implementation, run Feedback skill to check for layout shifts, contrast, and consistency with design system.
