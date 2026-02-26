"""
Signup access control and rating helpers.

Centralises "load signup + check party + redirect on deny" so route handlers
stay thin and duplication is removed (DRY).
"""
from flask import flash, redirect, url_for, request
from flask_login import current_user

from app.models import ListingSignup


def get_signup_for_business(signup_id):
    """
    Load signup by id and verify the current user owns the listing (business).
    Returns (signup, None) on success, or (None, redirect_response) on 404 or access denied.
    """
    signup = ListingSignup.query.get_or_404(signup_id)
    if signup.listing.business_id != current_user.id:
        flash('Access denied.', 'danger')
        return None, redirect(url_for('main.review_gallery'))
    return signup, None


def get_signup_for_developer(signup_id):
    """
    Load signup by id and verify the current user is the developer on the signup.
    Returns (signup, None) on success, or (None, redirect_response) on 404 or access denied.
    """
    signup = ListingSignup.query.get_or_404(signup_id)
    if signup.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return None, redirect(url_for('main.developer_joined_listings'))
    return signup, None


def apply_rating_and_redirect(signup, field_name, redirect_endpoint, flash_success_msg=None):
    """
    Parse rating from request.form (key 'rating'), validate 1–5, set on signup, commit, flash, redirect.
    field_name: 'business_rating_of_developer' or 'developer_rating_of_business'.
    redirect_endpoint: e.g. 'main.review_gallery' or 'main.developer_joined_listings'.
    """
    from app import db
    try:
        rating = int(request.form.get('rating', 0))
        if 1 <= rating <= 5:
            setattr(signup, field_name, rating)
            db.session.commit()
            if flash_success_msg:
                flash(flash_success_msg, 'success')
            else:
                flash(f'Rated {float(rating):.1f}/5.0 stars.', 'success')
        else:
            flash('Rating must be between 1 and 5.', 'warning')
    except (TypeError, ValueError):
        flash('Invalid rating.', 'warning')
    return redirect(url_for(redirect_endpoint))
