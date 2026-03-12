"""
Flask application factory and extensions.

Creates the app, binds SQLAlchemy, Bcrypt, LoginManager, Mail, Migrate;
registers blueprints (main, contract), injects CSRF and contract_view_url,
registers 404 handler, and creates DB tables in context.
"""
import logging
import os
from datetime import timedelta
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'
mail = Mail()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])


def create_app():
    """Create and configure the Flask application. Use for WSGI and development."""
    # Load .env early so env vars are available regardless of entry point (run.py, flask run, gunicorn)
    _log = logging.getLogger(__name__)
    try:
        from dotenv import load_dotenv
        _root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        _env_path = os.path.join(_root, '.env')
        _backend_env = os.path.join(_root, 'backend', '.env')
        for _p in (_env_path, _backend_env):
            if os.path.isfile(_p):
                load_dotenv(_p)
                break
        load_dotenv()  # Also load from cwd (e.g. backend/.env when running from backend/)
    except ImportError:
        pass

    # Vercel's filesystem is read-only except /tmp; Flask-SQLAlchemy always
    # calls os.makedirs(instance_path) on init, so we must point it at /tmp.
    _instance_path = '/tmp' if os.environ.get('VERCEL') else None
    app = Flask(__name__, **({"instance_path": _instance_path} if _instance_path else {}))
    is_production = os.environ.get('FLASK_ENV') == 'production'
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        if is_production:
            raise RuntimeError('SECRET_KEY environment variable must be set in production')
        import secrets
        secret_key = secrets.token_hex(32)
        _log.warning('Using random dev SECRET_KEY. Set SECRET_KEY env var for persistent sessions.')
    app.config['SECRET_KEY'] = secret_key

    # Session security
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = is_production
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

    # File upload limit
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

    database_url = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
    # Vercel/Heroku use postgres:// but SQLAlchemy 1.4+ requires postgresql://
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    if database_url.startswith('postgresql'):
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_size': 10,
            'pool_recycle': 300,
        }

    # Mail (development/production: set EMAIL_USER, EMAIL_PASS, MAIL_SERVER in env)
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.ionos.co.uk')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
    app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'JrDev <noreply@jr-dev.uk>')
    # Platform (JRDEV Ltd) for contract PDF
    app.config['PLATFORM_COMPANY_NUMBER'] = os.environ.get('PLATFORM_COMPANY_NUMBER', '[_______]')
    app.config['PLATFORM_ADDRESS'] = os.environ.get('PLATFORM_ADDRESS', '[Address]')
    _log = logging.getLogger(__name__)
    if app.config['MAIL_USERNAME'] and app.config['MAIL_PASSWORD']:
        _log.info('Mail configured (sender: %s). Email verification enabled.', app.config['MAIL_USERNAME'])
    else:
        _log.warning(
            'Mail not configured: set EMAIL_USER and EMAIL_PASS in .env for verification emails.'
        )

    # Stripe: store keys in app.config so they're available even if os.environ is unreliable at request time
    _sk = (os.environ.get('STRIPE_SECRET_KEY') or '').strip()
    _pk = (os.environ.get('STRIPE_PUBLISHABLE_KEY') or '').strip()
    app.config['STRIPE_SECRET_KEY'] = _sk
    app.config['STRIPE_PUBLISHABLE_KEY'] = _pk
    try:
        import stripe as _stripe_mod
        if _sk and _pk:
            _log.info('Stripe: configured (secret key present, publishable key present)')
        else:
            _log.warning(
                'Stripe: not configured. STRIPE_SECRET_KEY=%s, STRIPE_PUBLISHABLE_KEY=%s. '
                'Set both in .env to enable payments.',
                'set' if _sk else 'missing',
                'set' if _pk else 'missing',
            )
    except ImportError:
        _log.warning('Stripe: stripe package not installed. Run: pip install stripe')

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        if is_production:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    from app.routes import main
    app.register_blueprint(main)

    from app.contract_pdf import contract, contract_view_url
    app.register_blueprint(contract)
    app.add_template_global(contract_view_url, 'contract_view_url')

    def format_rating(value):
        """Format rating as X.X/5.0 for display; returns '—' if value is None."""
        if value is None:
            return '—'
        try:
            n = float(value)
            return f'{n:.1f}/5.0'
        except (TypeError, ValueError):
            return '—'

    app.add_template_filter(format_rating, 'format_rating')

    def initials(name):
        """Return up to 2 uppercase letters for avatar fallback (e.g. 'John Doe' -> 'JD')."""
        if not name or not str(name).strip():
            return '?'
        s = str(name).strip()
        parts = s.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return (s[:2] if len(s) >= 2 else s[0]).upper()

    app.add_template_filter(initials, 'initials')

    def markdown_filter(text):
        """Render markdown to HTML for templates. Sanitizes output to prevent XSS."""
        from markupsafe import Markup
        from app.utils import sanitize_markdown
        return Markup(sanitize_markdown(text))

    app.add_template_filter(markdown_filter, 'markdown')

    from app.utils import youtube_embed_url
    app.add_template_filter(youtube_embed_url, 'youtube_embed_url')

    @app.context_processor
    def inject_unread_message_count():
        from flask_login import current_user
        try:
            if current_user.is_authenticated and current_user.is_verified:
                from app.models import SprintMessage, ListingSignup, SprintListing
                if current_user.role == 'DEVELOPER':
                    signup_ids = [s.id for s in ListingSignup.query.filter_by(user_id=current_user.id).all()]
                else:
                    listing_ids = [l.id for l in SprintListing.query.filter_by(business_id=current_user.id).all()]
                    signup_ids = [s.id for s in ListingSignup.query.filter(ListingSignup.listing_id.in_(listing_ids)).all()] if listing_ids else []
                if signup_ids:
                    unread = SprintMessage.query.filter(
                        SprintMessage.signup_id.in_(signup_ids),
                        SprintMessage.sender_id != current_user.id,
                        SprintMessage.is_read == False,
                    ).count()
                else:
                    unread = 0
                return {'unread_message_count': unread}
        except Exception:
            pass
        return {'unread_message_count': 0}

    @app.context_processor
    def inject_admin_disputed_count():
        from flask_login import current_user
        try:
            from app.decorators import is_platform_admin
            if current_user.is_authenticated and is_platform_admin():
                from app.models import ListingSignup
                return {'admin_disputed_count': ListingSignup.query.filter_by(flagged_for_review=True).count()}
        except Exception:
            pass
        return {'admin_disputed_count': 0}

    @app.context_processor
    def inject_csrf_token():
        from app.decorators import can_manage_prize_pools, is_platform_admin
        from flask_wtf.csrf import generate_csrf
        return {'csrf_token': generate_csrf, 'can_manage_prize_pools': can_manage_prize_pools, 'is_platform_admin': is_platform_admin}

    with app.app_context():
        from app import models  # noqa: F401 - load models so db.create_all() sees them
        db.create_all()

    @app.cli.command('process-signing-deadlines')
    def process_signing_deadlines_cmd():
        """Deny accepted signups where developer hasn't signed within 2 days. Run via cron (e.g. hourly): flask process-signing-deadlines"""
        from app.routes import process_signing_deadlines
        n = process_signing_deadlines()
        import click
        click.echo(f'Signing deadlines processed: {n} signup(s) denied.')

    @app.cli.command('process-review-deadlines')
    def process_review_deadlines_cmd():
        """Process 48-hour review deadlines: auto-release payment for signups past the deadline. Run via cron (e.g. hourly): flask process-review-deadlines"""
        from app.routes import process_review_deadlines
        process_review_deadlines()
        import click
        click.echo('Review deadlines processed.')

    @app.cli.command('process-prize-pools')
    def process_prize_pools_cmd():
        """Transition prize pool statuses and compute top 10% winners when voting ends. Run via cron: flask process-prize-pools"""
        from app.routes import process_prize_pool_winners
        process_prize_pool_winners()
        import click
        click.echo('Prize pools processed.')

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template('500.html'), 500

    return app
