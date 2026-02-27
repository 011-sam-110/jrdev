# Plan: 48-Hour Review Deadline & Auto-Release

## Context

From vision: the business has **48 hours** from when a developer submits their prototype to take a review action (mark as reviewed or flag for dispute). If they take **no action** within 48 hours, **payment is automatically released to the developer** (i.e. the submission is treated as reviewed so the developer is paid). This creates urgency for the business and predictable pay for developers. Actual Stripe charging is not yet implemented; this plan implements the deadline logic, state update (set `reviewed_at` when 48h passes), and UI so that when payments are wired later, auto-release can trigger the same flow as "mark as reviewed".

---

## Files Affected

| File | Changes |
|------|--------|
| `backend/app/routes.py` | Add shared function to process overdue signups (set `reviewed_at`, update developer profile stats); call it at start of `review_gallery`; optionally expose via CLI. |
| `backend/app/__init__.py` or new `backend/app/cli.py` | Register Flask CLI command `process-review-deadlines` that runs the same processing (for cron). |
| `backend/app/templates/partials/developer_card.html` | When prototype submitted and not reviewed/flagged: show "Review within 48 hours or payment auto-releases" and countdown (e.g. "X hours left"). |
| `backend/app/templates/developer_joined_listings.html` | When prototype submitted and under review: show "Business has until [date/time] to review; then payment auto-releases." |
| `backend/app/utils.py` (optional) | Helper to compute `review_deadline_at` from `prototype_submitted_at` (e.g. `deadline = submitted_at + timedelta(hours=48)`) for use in templates and logic. |
| `.cursor/skills/vision.md` | No structural change; Known Gaps already references the 48h rule. After implementation, optionally add a note that the deadline logic is in place (auto-release state change; Stripe still TBD). |

---

## Steps

### 1. Define the 48-hour constant and "overdue" query

- In `routes.py` (or `utils.py`), define `REVIEW_DEADLINE_HOURS = 48` and a helper that, given a `ListingSignup`, returns whether it is past the deadline: `prototype_submitted_at` is set, `reviewed_at` is None, `flagged_for_review` is False, and `prototype_submitted_at + timedelta(hours=48) <= utcnow()`.
- No new model fields required: deadline is computed from `prototype_submitted_at + 48 hours`.

### 2. Shared logic: apply "auto-release" to a signup

- Extract or mirror the effect of `signup_mark_reviewed`: set `signup.reviewed_at = datetime.utcnow()`, update the developer's `DeveloperProfile` (`prototypes_completed`, `contracts_won`, technology counts) so the platform state is identical to a business-approved review. Put this in a function e.g. `apply_auto_release(signup)` in `routes.py` (or a small `app/review_deadlines.py` module if preferred) that takes one signup and commits after updating (or receives `db.session` and the caller commits once for many).
- Ensure it is idempotent: if `reviewed_at` is already set, do nothing.

### 3. Process all overdue signups

- Add a function `process_review_deadlines()` that:
  - Queries `ListingSignup` where `prototype_submitted_at` is not None, `reviewed_at` is None, `flagged_for_review` is False, and `prototype_submitted_at + timedelta(hours=48) <= utcnow()`.
  - For each, calls `apply_auto_release(signup)` (or equivalent), then `db.session.commit()` per signup (or one commit after all).
- Call `process_review_deadlines()` at the **start** of the `review_gallery` view (before building `developers_by_listing`). That way, whenever the business (or anyone) loads the review gallery, any signups that have passed the 48h mark are automatically marked as reviewed and the UI shows the correct state without requiring cron.

### 4. Optional: Flask CLI command for cron

- Register a Flask CLI command, e.g. `flask process-review-deadlines`, that runs `process_review_deadlines()` inside an app context. This allows production to run the same logic on a schedule (e.g. every 15–60 minutes) if desired, so auto-release happens even if no one visits the review gallery. Document in the plan or in a short comment in code that cron can be set up as: `0 * * * * cd /path && flask process-review-deadlines` (hourly).

### 5. Business UI: 48h countdown on developer card

- In `backend/app/templates/partials/developer_card.html`, when the developer has submitted a prototype (`developer.prototype_submitted_at`) and is **not** yet reviewed (`not developer.reviewed_at`) and **not** flagged (`not developer.flagged_for_review`):
  - Compute or receive `review_deadline_at` = `prototype_submitted_at + 48 hours`. (Pass it from the view via `make_dev()` so the template receives e.g. `developer.review_deadline_at` and, if desired, `developer.hours_left_to_review` or a simple `past_review_deadline` boolean.)
  - Show a short line: e.g. "Review within 48 hours or payment auto-releases." and a countdown like "X hours left" (or "Due by [date/time]"). If the deadline has passed, the next page load will run `process_review_deadlines()` and the card will show as reviewed, so the template only needs to handle the "before deadline" case for the countdown; optionally show "Deadline passed — processing..." if you want to handle the race where the user is viewing the page at the exact moment the deadline passes.
- Ensure the copy is clear and matches the vision (urgency for the business, auto-release if they don’t act).

### 6. Developer UI: when payment will auto-release

- In `backend/app/templates/developer_joined_listings.html`, for a signup that has submitted a prototype and is "under review" (status like "Prototype uploaded · Under review"):
  - Show a line such as: "Business has until [date/time] to review; then payment auto-releases." using `signup.prototype_submitted_at + 48 hours` (computed in the route and passed to the template, or via a Jinja filter or template variable). Use the same `REVIEW_DEADLINE_HOURS` constant so the displayed deadline is always 48h from submission.

### 7. Pass deadline into templates

- In `review_gallery`, extend `make_dev(s, listing)` to set `review_deadline_at` (and optionally `hours_left` or `past_review_deadline`) on the dev object when `s.prototype_submitted_at` is set and not reviewed/flagged. Use the same 48h constant.
- In the `developer_joined_listings` route, ensure each signup in the list has a computed `review_deadline_at` (or equivalent) when the developer has submitted and is awaiting review, and pass it so the template can show the "Business has until …" text.

### 8. Edge cases and idempotency

- If the business flags for dispute at 47h, the signup is excluded from the overdue query (`flagged_for_review` True), so auto-release never applies. No change needed.
- If the business marks as reviewed at 47h, `reviewed_at` is set; the overdue query excludes it. No change needed.
- Running `process_review_deadlines()` multiple times (e.g. on every review_gallery load) must be safe: only signups that are still unreviewed and past the deadline are updated; once `reviewed_at` is set, they are not selected again.

---

## Dependencies

- None. Uses existing `datetime`, Flask app context, and DB. No new pip packages. No migrations (no new columns).

---

## Risks / Notes

- **Stripe**: Actual payment release (charging the business / paying the developer) is not in scope. This plan only updates platform state (`reviewed_at` + profile stats) so that when Stripe is integrated, the same "mark as reviewed" path can be used for both manual and auto-release (and a future job can iterate over `reviewed_at` set in the last N hours to trigger payouts).
- **Timezone**: Use UTC consistently (`datetime.utcnow()`, and store/compare `prototype_submitted_at` in UTC). Display deadline in user’s local time if desired (optional; can be a follow-up).
- **Feedback**: After implementation, verify (1) business sees the 48h message and countdown, (2) developer sees "Business has until …", (3) after 48h (or after running the CLI / loading review gallery), the signup shows as reviewed and developer profile stats update, (4) flagged signups are never auto-released.
