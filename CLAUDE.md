# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JrDev is a platform connecting junior developers with businesses for contract sprints and competitive prize pools. The primary UI is server-rendered Flask/Jinja2. The `frontend/` Next.js app is exploratory/early-stage.

## Commands

### Backend (primary app)

```bash
# Install dependencies
cd backend && pip install -r requirements.txt

# Run local dev server (http://localhost:5000)
cd backend && python run.py

# Seed database
cd backend && python scripts/seeds/seed_admin.py
cd backend && python scripts/seeds/seed_prize_pools.py

# Flask CLI commands (run from backend/)
flask process-review-deadlines   # Auto-release payments after 48h review window
flask process-prize-pools        # Transition pool statuses, compute winners
flask db migrate && flask db upgrade  # Run migrations
```

### Frontend (Next.js)

```bash
cd frontend && npm install
npm run dev    # http://localhost:3000
npm run build
npm run lint
```

## Architecture

> Full architecture reference (all routes, models, templates, file tree): `C:\Users\sampo\Documents\Obsidian Vault\Projects\JrDev\Architecture.md`

### File Map

> For the full file tree, all routes, and model columns see: `C:\Users\sampo\Documents\Obsidian Vault\Projects\JrDev\Architecture.md`
> Read it at the start of any task involving new files, routes, or models.

**Entry points:**
- `api/index.py` — Vercel serverless entry
- `backend/run.py` — Local dev server (loads .env, db.create_all())

**`backend/app/` — Python files:**
- `__init__.py` — App factory: all extensions, blueprints, Jinja2 filters, CLI commands, error handlers
- `models.py` — All models: User, DeveloperProfile, SprintListing, ListingSignup, PrizePool, PrizePoolEntry, PrizePoolVote, PrizePoolPairwiseVote, PrizePoolPayout, AdminEmail, PinnedProject
- `forms.py` — Auth forms: RegistrationForm, LoginForm
- `profile_forms.py` — Profile forms: EditProfileForm, EditMarkdownForm, AddPinnedProjectForm
- `utils.py` — sanitize_markdown(), is_safe_url(), redirect_after_action(), youtube_embed_url()
- `decorators.py` — @require_verified, @require_role, @require_admin, can_manage_prize_pools(), is_platform_admin()
- `signup_helpers.py` — get_signup_for_business/developer(), apply_rating_and_redirect()
- `admin_email.py` — sync_inbox(), send_admin_email() for 3 admin inboxes
- `contract_pdf.py` — PDF contract blueprint (`contract`); GET /contract/view/<id>, POST /contract/generate

**`backend/app/routes/` — Blueprint name `main`:**
- `_legacy.py` — all route handlers (~2200 lines, Phase 7 backlog splits this)
- `_helpers.py` — Stripe helpers, _fmt_rating
- `pages.py` — static pages (home, about, privacy, terms, support, sitemap)

### Key Domain Flows

**Sprint Listings:** Business creates listing → Developer joins (pending) → Business accepts/denies → Both e-sign contract → Developer submits prototype → Business reviews & rates.

**Prize Pools:** Admin creates pool (paid/free) → Developer joins (Stripe for paid) → Developer submits entry → Voting phase (ranked 3 + pairwise) → Winners computed → Payouts issued.

### Database

- **Local:** SQLite at `backend/instance/site.db`
- **Production:** PostgreSQL (set `DATABASE_URL` env var)
- Flask-Migrate handles schema migrations

### Environment Variables

Required vars (see `ENV_REFERENCE.md` for full docs):
- `SECRET_KEY` — Flask sessions/CSRF
- `DATABASE_URL` — PostgreSQL URI (production only; defaults to SQLite locally)
- `FLASK_ENV` — `development` or `production`
- `EMAIL_USER` / `EMAIL_PASS` — Gmail SMTP for verification emails
- `STRIPE_SECRET_KEY` / `STRIPE_PUBLISHABLE_KEY` — Stripe payments

### Status State Machines

**ListingSignup statuses:** `pending` → `accepted` or `denied`. After `accepted`, both parties must e-sign (`developer_signed_at` + `business_signed_at`) before sprint work begins. `developer_withdrew=True` is a soft flag layered on top of status.

**PrizePool statuses:** `open` → `voting` → `closed`. Transitions are triggered by `flask process-prize-pools` (checks `submission_ends_at` and `voting_ends_at` datetimes). `pool_type` is `paid` (entry fee + user voting) or `free` (no fee, AI review placeholder).

**SprintListing status:** `open` or `closed`. Listings become effectively closed when `is_full` (joined_count ≥ max_talent_pool) or manually closed.

### Route Auth Patterns

Every protected route uses `@require_verified` (email confirmed) plus optionally `@require_role('DEVELOPER'|'BUSINESS')` or `@require_prize_pool_admin`. `@require_verified` always comes before `@require_role`. Routes that return JSON use `@require_role(..., json_response=True)`.

### Common Multi-File Touch Points

When adding a new prize pool or listing field:
1. `models.py` — add column
2. `routes/_legacy.py` — read/write in relevant routes
3. `flask db migrate && flask db upgrade` — generate migration

When changing developer profile appearance options:
- `profile_forms.py` (form choices) and `models.py` (column default) and `utils.py` (default constants) must stay in sync.

### Deployment

Deployed on Vercel via `vercel.json`. All traffic rewrites to `api/index.py`. See `VERCEL_DEPLOYMENT.md` for full setup steps including PostgreSQL and cron job configuration.

### Keeping Architecture.md Current

`Architecture.md` in the Obsidian vault is the canonical reference. **Update it whenever you make a structural change:**

| Change made | What to update in Architecture.md |
|-------------|----------------------------------|
| New file created or deleted | Directory tree section |
| File moved or renamed | Directory tree section |
| New route added | Routes table (correct group) |
| Route deleted or URL changed | Routes table |
| New model or column added | Models section |
| New template created | Templates list |
| New JS/CSS file | Static section |

**Rule:** If you edit `models.py`, `routes/_legacy.py`, `routes/__init__.py`, or create/delete any file in `backend/app/` — update `Architecture.md` before considering the task done.

## Agent Roles

When the user says "be the architect", "be the programmer", or similar — read the corresponding role file from the Obsidian vault and follow it strictly for the rest of the conversation (or until told to switch).

- **Obsidian vault:** `C:\Users\sampo\Documents\Obsidian Vault\Projects\JrDev\`
- **Architect role:** `Claude Roles/architect.md` — plans, reads code, writes task specs to `Active Work.md`, logs decisions. Never edits source code.
- **Programmer role:** `Claude Roles/programmer.md` — implements from the task spec in `Active Work.md`, writes code. Asks user before editing any Obsidian file.
- **Active Work:** `Active Work.md` — the handoff document. Architect writes tasks here, programmer reads and implements from here.
- **Decisions:** `Decisions/` folder — architect logs non-obvious architectural choices here.
