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

### Backend Structure

- **`backend/app/__init__.py`** — Flask app factory. Initializes all extensions (SQLAlchemy, Bcrypt, LoginManager, Flask-Mail, Flask-Migrate, Flask-Limiter), registers blueprints, injects Jinja2 filters (markdown, initials, rating), and registers CLI commands.
- **`backend/app/models.py`** — All SQLAlchemy models. Key models: `User`, `DeveloperProfile`, `SprintListing`, `ListingSignup`, `PrizePool`, `PrizePoolEntry`, `PrizePoolVote`.
- **`backend/app/routes.py`** — Single large blueprint (~1800 lines) containing all route handlers. Sections: auth, dashboards, developer profiles, sprint listings, prize pools, billing (Stripe), admin.
- **`backend/app/utils.py`** — Shared helpers: URL normalization, developer profile defaults, tech stack parsing, rating utilities.
- **`backend/app/forms.py`** — WTForms for auth (registration, login). Email validators are defined here as a shared constant.
- **`backend/app/profile_forms.py`** — WTForms for developer profile editing. Theme/animation/panel/background choices are defined here and must stay in sync with model defaults and `utils.py` constants.
- **`backend/app/signup_helpers.py`** — Contract creation and signup logic extracted from routes.
- **`backend/app/decorators.py`** — `@require_role('DEVELOPER'|'BUSINESS')`, `@require_verified`, `@require_prize_pool_admin`.
- **`backend/app/contract_pdf.py`** — ReportLab PDF contract generation blueprint.
- **`api/index.py`** — Vercel serverless entry point (imports `create_app()`, exposes `app`).

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
2. `routes.py` — read/write in relevant routes
3. `flask db migrate && flask db upgrade` — generate migration

When changing developer profile appearance options:
- `profile_forms.py` (form choices) and `models.py` (column default) and `utils.py` (default constants) must stay in sync.

### Deployment

Deployed on Vercel via `vercel.json`. All traffic rewrites to `api/index.py`. See `VERCEL_DEPLOYMENT.md` for full setup steps including PostgreSQL and cron job configuration.

## Agent Roles

When the user says "be the architect", "be the programmer", or similar — read the corresponding role file from the Obsidian vault and follow it strictly for the rest of the conversation (or until told to switch).

- **Obsidian vault:** `C:\Users\sampo\Documents\Obsidian Vault\Projects\JrDev\`
- **Architect role:** `Claude Roles/architect.md` — plans, reads code, writes task specs to `Active Work.md`, logs decisions. Never edits source code.
- **Programmer role:** `Claude Roles/programmer.md` — implements from the task spec in `Active Work.md`, writes code. Asks user before editing any Obsidian file.
- **Active Work:** `Active Work.md` — the handoff document. Architect writes tasks here, programmer reads and implements from here.
- **Decisions:** `Decisions/` folder — architect logs non-obvious architectural choices here.
