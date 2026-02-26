"""
Route decorators for role-based access and email verification.

@require_role('DEVELOPER' | 'BUSINESS') enforces role; on failure returns
flash+redirect (HTML) or jsonify+403 when json_response=True.

@require_verified redirects to verify_email_sent if user is not email-verified.
Use after @login_required on routes that require full access.
"""
from functools import wraps
from flask import flash, jsonify, redirect, url_for, session
from flask_login import current_user

from app.utils import redirect_after_action


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
