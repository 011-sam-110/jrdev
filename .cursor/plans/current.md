## Plan: Pinned Projects Cap + Joined Listings Deliverables & Submission

### Context
1. Change pinned projects cap from 30 to 3.
2. Improve joined listings: show essential (non-optional) and optional deliverables separately; allow developers to submit work with checkboxes for each deliverable—matching the sprint submission flow. This applies to both sprint listings (ListingSignup) and prize pools (PrizePoolEntry).

### Files Affected
- `backend/app/routes.py` — PINNED_PROJECTS_MAX = 3; prize_pool_submit: allow free pools, accept requirements_met
- `backend/app/templates/developer_dashboard.html` — 30 → 3 in display and condition
- `backend/app/models.py` — PrizePool: add essential_deliverables, optional_deliverables; PrizePoolEntry: add requirements_met; add properties like SprintListing
- `backend/app/templates/developer_joined_listings.html` — Sprint: split deliverables into essential vs optional; Prize pool: show deliverables, add checkboxes + GitHub + demo to submit form
- `backend/app/templates/admin_prize_pools.html` — Add essential + optional deliverables fields to create form
- `backend/app/routes.py` (admin_prize_pools) — Save essential_deliverables, optional_deliverables when creating pool
- Migration script or add_prize_pool_deliverables.py — Add new columns to prize_pool and prize_pool_entry

### Steps
1. **Pinned cap**: In routes.py set PINNED_PROJECTS_MAX = 3. In developer_dashboard.html replace 30 with 3 (or use a template variable if we pass it).
2. **Sprint deliverables display**: In developer_joined_listings.html, replace the single "Deliverables (from contract)" block with two sections: "Essential (required)" (listing.essential_deliverables_list) and "Optional" (listing.optional_deliverables_list). Update the submit form checkboxes to iterate essential first, then optional, with clear labels.
3. **PrizePool model**: Add essential_deliverables (Text), optional_deliverables (Text) columns. Add essential_deliverables_list, optional_deliverables_list, deliverables_only_list properties (mirror SprintListing).
4. **PrizePoolEntry model**: Add requirements_met (String 500) column.
5. **Migration**: Create add_prize_pool_deliverables.py to add columns if missing.
6. **Admin form**: Add essential_deliverables and optional_deliverables textareas to admin_prize_pools.html create form. Update admin_prize_pools route to save them.
7. **prize_pool_submit route**: Remove the `pool.pool_type != 'paid'` block so free pools can submit. Add requirements_met handling (getlist, join, save). Fix redirect to developer_joined_listings.
8. **developer_joined_listings prize pool section**: When entry has joined (payment_completed_at for paid, or joined for free): show essential + optional deliverables. Replace the simple submit form with sprint-like form: checkboxes for deliverables, GitHub URL, demo video URL. For free pools, also show submit form (condition: entry.payment_completed_at or pool.pool_type == 'free' with entry existing). After submission, show submitted links and requirements_met like sprint.

### Dependencies
- Flask-Migrate or raw SQL migration for new columns.

### Risks / Notes
- prize_pool_submit currently redirects to developer_joined_prize_pools which redirects to developer_joined_listings—keep that.
- For free pools, entry is created with payment_completed_at=now when joining, so "has joined" = entry exists and (payment_completed_at or pool_type free).
- Seed script doesn't set deliverables; existing pools will have empty lists. Admin can edit via re-create or we add edit UI later.

### Feedback focus
Form CSRF, checkbox name/value matching, redirect targets, design tokens for new sections.
