# Deploying JrDev to Vercel

This guide explains how to deploy the JrDev Flask app to Vercel.

## Project Structure

```
JrDev/
├── api/
│   └── index.py          # Vercel entry point (imports Flask app from backend)
├── backend/
│   ├── app/              # Flask application (routes, models, templates, static)
│   ├── requirements.txt  # Python dependencies
│   └── run.py            # Local development server
├── vercel.json           # Vercel config (rewrites, install command)
└── VERCEL_DEPLOYMENT.md  # This file
```

## Prerequisites

1. **Database**: SQLite does **not** work on Vercel (ephemeral filesystem). You must use a hosted PostgreSQL database:
   - [Vercel Postgres](https://vercel.com/docs/storage/vercel-postgres)
   - [Neon](https://neon.tech)
   - [Supabase](https://supabase.com)
   - [Railway](https://railway.app)

2. **Environment variables**: Set these in the Vercel project dashboard (Settings → Environment Variables).

## Required Environment Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Flask secret key (generate a random string) |
| `DATABASE_URL` | PostgreSQL connection string (e.g. `postgresql://user:pass@host:5432/db`) |
| `STRIPE_SECRET_KEY` | For prize pool payments |
| `STRIPE_PUBLISHABLE_KEY` | For Stripe.js |
| `EMAIL_USER` | SMTP sender email (for verification emails) |
| `EMAIL_PASS` | SMTP password |

### Optional

| Variable | Description |
|----------|-------------|
| `PLATFORM_COMPANY_NUMBER` | Company number for contract PDFs |
| `PLATFORM_ADDRESS` | Platform address for contract PDFs |

## Deployment Steps

### 1. Connect to Vercel

- Push your code to GitHub/GitLab/Bitbucket
- Go to [vercel.com/new](https://vercel.com/new)
- Import your repository
- Vercel will auto-detect the configuration from `vercel.json`

### 2. Set Environment Variables

In your Vercel project → **Settings** → **Environment Variables**, add all required variables. Apply to Production, Preview, and Development as needed.

### 3. Set Up the Database

1. Create a PostgreSQL database (e.g. Vercel Postgres or Neon)
2. Copy the connection string
3. If it starts with `postgres://`, the app will convert it to `postgresql://` automatically
4. Add it as `DATABASE_URL` in Vercel

### 4. Run Migrations

After the first deploy, you need to run migrations to create tables. Options:

**Option A – Vercel Postgres (if using Vercel Postgres)**  
Tables may be created automatically via `db.create_all()` on first request. For migrations, use the Vercel CLI:

```bash
vercel env pull .env.local
cd backend
flask db upgrade
```

**Option B – Manual SQL**  
Export your SQLite schema and run it against the new PostgreSQL database, or use Flask-Migrate locally with `DATABASE_URL` pointing to your production DB.

### 5. Deploy

```bash
vercel
```

Or push to your connected Git branch; Vercel will deploy automatically.

## Local Testing with Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Run locally (simulates Vercel)
vercel dev
```

## Troubleshooting

- **"Application error"**: Check Vercel Function logs. Often caused by missing `DATABASE_URL` or `SECRET_KEY`.
- **Static files not loading**: Flask serves static files. If issues persist, consider moving assets to a `public/` folder (see Vercel docs).
- **Database connection fails**: Ensure `DATABASE_URL` is set and uses `postgresql://` (the app converts `postgres://` automatically).
- **Import errors**: The `api/index.py` adds `backend/` to `sys.path` before importing. Ensure the `backend` directory is in the repo root.

## Notes

- The Flask app runs as a single Vercel Function (Fluid compute)
- Each request may hit a cold start; consider Vercel Pro for better performance
- Cron jobs (e.g. `process-review-deadlines`, `process-prize-pools`) need to be set up separately via Vercel Cron or an external scheduler
