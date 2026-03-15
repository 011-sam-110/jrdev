"""
Route decorators for role-based access and email verification.

@require_role('DEVELOPER' | 'BUSINESS') enforces role; on failure returns
flash+redirect (HTML) or jsonify+403 when json_response=True.

@require_verified redirects to verify_email_sent if user is not email-verified.
Use after @login_required on routes that require full access.
"""
import os
from functools import wraps
from flask import flash, jsonify, redirect, url_for, session
from flask_login import current_user

from app.utils import redirect_after_action


def _prize_pool_admin_emails():
    """Return set of emails allowed to manage prize pools (from ADMIN_EMAILS env)."""
    s = os.environ.get('ADMIN_EMAILS', '').strip()
    return {e.strip().lower() for e in s.split(',') if e.strip()}


def can_manage_prize_pools():
    """True if current user can manage prize pools (admin emails or BUSINESS role when no ADMIN_EMAILS)."""
    if not current_user.is_authenticated:
        return False
    admin_emails = _prize_pool_admin_emails()
    if admin_emails:
        return (current_user.email or '').strip().lower() in admin_emails
    return current_user.role == 'BUSINESS'


def require_prize_pool_admin(f):
    """Require current user to be a prize pool admin (ADMIN_EMAILS or BUSINESS when unset)."""
    @wraps(f)
    def inner(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('main.login'))
        if not can_manage_prize_pools():
            flash('Access denied. Only platform admins can manage prize pools.', 'danger')
            return redirect_after_action()
        return f(*args, **kwargs)
    return inner


def is_platform_admin():
    """True if current user's email is in ADMIN_EMAILS env var (strict check, no fallback)."""
    if not current_user.is_authenticated:
        return False
    admin_emails = _prize_pool_admin_emails()
    if not admin_emails:
        return False
    return (current_user.email or '').strip().lower() in admin_emails


def require_admin(f):
    """Require current user to be a platform admin (email in ADMIN_EMAILS). No role fallback."""
    @wraps(f)
    def inner(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('main.login'))
        if not is_platform_admin():
            flash('Access denied. This area is restricted to platform admins.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return inner


def require_verified(f):
    """Require current_user to be email-verified; else redirect to verify_email_sent."""
    @wraps(f)
    def inner(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('main.login'))
        if not current_user.is_verified:
            session['unverified_email'] = current_user.email
            flash('Please verify your email address to continue.', 'warning')
            return redirect(url_for('main.verify_email_sent'))
        return f(*args, **kwargs)
    return inner


def require_role(role, json_response=False):
    """Require current_user.role to match. On failure: flash+redirect or jsonify+403."""
    def decorator(f):
        @wraps(f)
        def inner(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                if json_response:
                    return jsonify({'error': 'Unauthorized'}), 403
                flash(
                    'Access denied. Log in with the correct account type '
                    '(Business for listings, Developer for joined sprints).',
                    'danger',
                )
                return redirect_after_action()
            return f(*args, **kwargs)
        return inner
    return decorator
