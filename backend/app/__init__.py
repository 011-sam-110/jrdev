"""
Flask application factory and extensions.

Creates the app, binds SQLAlchemy, Bcrypt, LoginManager, Mail, Migrate;
registers blueprints (main, contract), injects CSRF and contract_view_url,
registers 404 handler, and creates DB tables in context.
"""
import logging
import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import generate_csrf

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'
mail = Mail()
migrate = Migrate()


def create_app():
    """Create and configure the Flask application. Use for WSGI and development."""
    app = Flask(__name__)
    secret_key = os.environ.get('SECRET_KEY', '5791628bb0b13ce0c676dfde280ba245')
    if not os.environ.get('SECRET_KEY') and os.environ.get('FLASK_ENV') == 'production':
        import warnings
        warnings.warn('SECRET_KEY not set; use a strong secret in production.', UserWarning)
    app.config['SECRET_KEY'] = secret_key
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'sqlite:///site.db'
    )

    # Mail (development/production: set EMAIL_USER, EMAIL_PASS in env)
    app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
    app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
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

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

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

    @app.context_processor
    def inject_csrf_token():
        return {'csrf_token': generate_csrf()}

    with app.app_context():
        from app import models  # noqa: F401 - load models so db.create_all() sees them
        db.create_all()

    @app.cli.command('process-review-deadlines')
    def process_review_deadlines_cmd():
        """Process 48-hour review deadlines: auto-release payment for signups past the deadline. Run via cron (e.g. hourly): flask process-review-deadlines"""
        from app.routes import process_review_deadlines
        process_review_deadlines()
        import click
        click.echo('Review deadlines processed.')

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    return app
