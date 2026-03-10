"""Shared helpers used across multiple route modules."""
import logging
import os

from flask import current_app
from flask_login import current_user

from app import db

logger = logging.getLogger(__name__)

try:
    import stripe
except ImportError:
    stripe = None


def _fmt_rating(v):
    """Format rating for flash message as X.X (safe for missing/invalid)."""
    try:
        return f'{float(v):.1f}' if v not in (None, '') else '0.0'
    except (TypeError, ValueError):
        return '0.0'


# ── Stripe helpers ──

def _stripe_secret_key():
    """Prefer app.config (set at startup) over os.environ for reliability."""
    return current_app.config.get('STRIPE_SECRET_KEY') or os.environ.get('STRIPE_SECRET_KEY', '')


def _stripe_publishable_key():
    return current_app.config.get('STRIPE_PUBLISHABLE_KEY') or os.environ.get('STRIPE_PUBLISHABLE_KEY', '')


def _stripe_available():
    return stripe is not None and bool(_stripe_secret_key())


def _business_has_card():
    """True if business has a payment method on file (Stripe). If Stripe unavailable, returns True (no block)."""
    if not _stripe_available() or current_user.role != 'BUSINESS' or not current_user.stripe_customer_id:
        return not _stripe_available()  # No Stripe = don't block
    stripe.api_key = _stripe_secret_key()
    try:
        pms = stripe.PaymentMethod.list(customer=current_user.stripe_customer_id, type='card')
        return bool(pms.data)
    except stripe.error.StripeError:
        return False


def _get_or_create_stripe_customer_for_developer():
    """Get or create Stripe customer for current developer user."""
    if not _stripe_available() or current_user.role != 'DEVELOPER':
        return None
    stripe.api_key = _stripe_secret_key()
    if current_user.stripe_customer_id:
        try:
            return stripe.Customer.retrieve(current_user.stripe_customer_id)
        except stripe.error.InvalidRequestError:
            current_user.stripe_customer_id = None
            db.session.commit()
    logger.info('Stripe API: Customer.create (developer)')
    customer = stripe.Customer.create(
        email=current_user.email,
        name=current_user.username,
    )
    current_user.stripe_customer_id = customer.id
    db.session.commit()
    return customer


def _get_stripe_customer():
    """Get or create Stripe customer for current business user."""
    if not _stripe_available() or current_user.role != 'BUSINESS':
        return None
    stripe.api_key = _stripe_secret_key()
    if current_user.stripe_customer_id:
        try:
            return stripe.Customer.retrieve(current_user.stripe_customer_id)
        except stripe.error.InvalidRequestError:
            current_user.stripe_customer_id = None
            db.session.commit()
    # Create new customer
    logger.info('Stripe API: Customer.create (business)')
    customer = stripe.Customer.create(
        email=current_user.email,
        name=current_user.username,
    )
    current_user.stripe_customer_id = customer.id
    db.session.commit()
    return customer
