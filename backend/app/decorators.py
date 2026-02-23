"""Route decorators for role-based access and redirects."""
from functools import wraps
from flask import flash, jsonify
from flask_login import current_user

from app.utils import redirect_after_action


def require_role(role, json_response=False):
    """Require current_user.role to match. On failure: flash+redirect or jsonify+403."""
    def decorator(f):
        @wraps(f)
        def inner(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                if json_response:
                    return jsonify({'error': 'Unauthorized'}), 403
                flash('Access denied. You must be logged in with the correct account (e.g. Business for listings, Developer for joined sprints).', 'danger')
                return redirect_after_action()
            return f(*args, **kwargs)
        return inner
    return decorator
