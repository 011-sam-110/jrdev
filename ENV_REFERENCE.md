# Environment variables for JrDev

Use a `.env` file in the **project root** (or in `backend/`). When you run the app with `python run.py` from `backend/`, the app loads `.env` from the project root first, so a single root `.env` works.

## Required for production

| Variable      | Description |
|---------------|-------------|
| `SECRET_KEY`  | Long random string for sessions and tokens. Generate with: `python -c "import secrets; print(secrets.token_hex(32))"` |

## Email verification (required for new signups)

To send verification emails (e.g. Gmail), set:

| Variable     | Description |
|--------------|-------------|
| `EMAIL_USER` | Sender email (e.g. `yourname@gmail.com`). For Gmail, use the same account you use to log in. |
| `EMAIL_PASS` | **App password**, not your normal password. For Gmail: Google Account → Security → 2-Step Verification → App passwords → generate one for "Mail". |

If these are not set, new users are still created but marked verified immediately (so they can log in without clicking a link). In production you should set them so verification emails are sent.

**Gmail tip:** Enable 2-Step Verification first; then create an App password and put it in `EMAIL_PASS`.

## Optional

| Variable               | Description |
|------------------------|-------------|
| `FLASK_ENV`            | `development` (debug on) or `production` (debug off). |
| `DEBUG`                | `1` / `true` to enable debug when not using `FLASK_ENV`. |
| `DATABASE_URL`         | Default: `sqlite:///site.db` in `backend/instance/`. Use PostgreSQL URL in production. |
| `STRIPE_SECRET_KEY`    | Stripe secret key for business billing. |
| `STRIPE_PUBLISHABLE_KEY` | Stripe publishable key for the billing page. |

See `backend/.env.example` for a copy-paste template.
