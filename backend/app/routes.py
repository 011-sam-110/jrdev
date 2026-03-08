"""
Main application routes: auth, dashboards, listings, signups, billing, ratings.

Uses shared helpers from app.utils and app.signup_helpers to keep handlers thin and DRY.
"""
import logging
import os
from flask import Blueprint, render_template, url_for, flash, redirect, request, session, jsonify, current_app
from werkzeug.utils import secure_filename
from app import db, bcrypt, mail
from app.forms import RegistrationForm, LoginForm
from app.profile_forms import EditProfileForm, EditMarkdownForm, AddPinnedProjectForm
from app.models import User, DeveloperProfile, Project, PinnedProject, SprintListing, ListingSignup, PrizePool, PrizePoolEntry, PrizePoolVote, PrizePoolPairwiseVote
from sqlalchemy.exc import IntegrityError
from app.decorators import require_role, require_verified, require_prize_pool_admin
from app.utils import (
    redirect_after_action,
    normalize_url,
    youtube_embed_url,
    parse_comma_separated,
    developer_stack_list,
    developer_avg_rating,
    developer_profile_theme_defaults,
    technologies_for_edit,
    normalize_technologies_input,
    REVIEW_DEADLINE_HOURS,
    review_deadline_from,
)
from app.signup_helpers import (
    get_signup_for_business,
    get_signup_for_developer,
    apply_rating_and_redirect,
)

logger = logging.getLogger(__name__)
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message


def _fmt_rating(v):
    """Format rating for flash message as X.X (safe for missing/invalid)."""
    try:
        return f'{float(v):.1f}' if v not in (None, '') else '0.0'
    except (TypeError, ValueError):
        return '0.0'


from flask_wtf.csrf import generate_csrf
import pyotp
import qrcode
import io
import markdown
import base64
from datetime import datetime, timedelta

try:
    import stripe
except ImportError:
    stripe = None

main = Blueprint('main', __name__)

@main.route("/developers")
@login_required
@require_verified
@require_role('BUSINESS')
def review_gallery():
    """Business view: developers by listing (accepted & fully signed) with phase (before/during/after sprint)."""
    process_review_deadlines()
    my_listings = SprintListing.query.filter_by(business_id=current_user.id).all()
    listing_ids = [l.id for l in my_listings]
    signups = ListingSignup.query.filter(
        ListingSignup.listing_id.in_(listing_ids),
        ListingSignup.status.in_(['accepted', 'pending'])
    ).all() if listing_ids else []
    now = datetime.utcnow()

    def make_dev(s, listing):
        """Build a simple dev view object for the template (embed URL, rating from utils, review deadline)."""
        deadline = review_deadline_from(s.prototype_submitted_at) if (s.prototype_submitted_at and not s.reviewed_at and not s.flagged_for_review) else None
        hours_left = None
        if deadline and deadline > now:
            delta = deadline - now
            hours_left = max(0, delta.total_seconds() / 3600)
        elif deadline and deadline <= now:
            hours_left = 0
        return type('Dev', (), {
            'user': s.user,
            'signup': s,
            'demo_video_embed_url': youtube_embed_url(s.demo_video_url),
            'video_due': listing.sprint_ends_at,
            'rating': developer_avg_rating(s.user_id),
            'github_submission_url': s.github_submission_url,
            'requirements_met': s.requirements_met,
            'prototype_submitted_at': s.prototype_submitted_at,
            'reviewed_at': s.reviewed_at,
            'flagged_for_review': s.flagged_for_review,
            'business_rating_of_developer': s.business_rating_of_developer,
            'developer_rating_of_business': s.developer_rating_of_business,
            'review_deadline_at': deadline,
            'hours_left_to_review': round(hours_left, 1) if hours_left is not None else None,
        })()

    # Group signups by listing (project). Only show in Progress & review when contract is fully signed.
    listing_to_devs = {}
    for s in signups:
        if s.status != 'accepted' or not s.is_fully_signed:
            continue
        listing = s.listing
        dev = make_dev(s, listing)
        if listing.id not in listing_to_devs:
            listing_to_devs[listing.id] = []
        listing_to_devs[listing.id].append(dev)

    def phase_for(listing):
        """Return 'before' | 'during' | 'after' relative to sprint timeline."""
        if listing.sprint_ends_at and now > listing.sprint_ends_at:
            return 'after'
        if listing.sprint_begins_at and now >= listing.sprint_begins_at:
            return 'during'
        return 'before'

    developers_by_listing = []
    for listing in sorted(my_listings, key=lambda l: l.created_at, reverse=True):
        devs = listing_to_devs.get(listing.id, [])
        developers_by_listing.append((listing, devs, phase_for(listing)))

    form = AddPinnedProjectForm()
    return render_template('business_dashboard_your-developers.html',
                           title='Your Listings',
                           developers_by_listing=developers_by_listing,
                           form=form,
                           nav_active='developers')

@main.route("/")
@main.route("/home")
def home():
    """Landing and home: list of projects."""
    projects = Project.query.all()
    return render_template('home.html', projects=projects, title='Home')


@main.route("/dashboard")
@login_required
@require_verified
def dashboard():
    """Role-based dashboard: developer (profile, stack, rating) or business (listings)."""
    if current_user.role == 'DEVELOPER':
        profile = current_user.developer_profile
        md_html = markdown.markdown(profile.custom_markdown) if profile.custom_markdown else ""
        stack_list = developer_stack_list(profile)
        avg_rating = developer_avg_rating(current_user.id)
        form = AddPinnedProjectForm()

        return render_template('developer_dashboard.html',
                               title='Dashboard',
                               profile=profile,
                               md_html=md_html,
                               stack_list=stack_list,
                               form=form,
                               avg_rating=avg_rating,
                               nav_active='dashboard')
    elif current_user.role == 'BUSINESS':
        my_listings = SprintListing.query.filter_by(business_id=current_user.id).order_by(SprintListing.created_at.desc()).all()
        listing_ids = [l.id for l in my_listings]
        all_signups = ListingSignup.query.filter(ListingSignup.listing_id.in_(listing_ids)).all() if listing_ids else []
        active_developers = sum(1 for s in all_signups if s.status == 'accepted' and s.is_fully_signed and not s.developer_withdrew)
        open_listings = sum(1 for l in my_listings if not l.is_full and getattr(l, 'status', 'open') != 'closed')
        stats = {
            'active_developers': active_developers,
            'total_listings': len(my_listings),
            'open_listings': open_listings,
        }
        attention_items = []
        pending_count = sum(1 for s in all_signups if s.status == 'pending')
        if pending_count:
            attention_items.append({'text': 'Pending applicants', 'url': url_for('main.review_gallery'), 'count': pending_count})
        awaiting_business = sum(1 for s in all_signups if s.status == 'accepted' and not s.business_signed_at)
        if awaiting_business:
            attention_items.append({'text': 'Awaiting your signature', 'url': url_for('main.review_gallery'), 'count': awaiting_business})
        has_card = _business_has_card() if current_user.role == 'BUSINESS' else True
        return render_template('business_dashboard.html', title='Business Dashboard', nav_active='sprint', my_listings=my_listings, stats=stats, attention_items=attention_items, has_card=has_card)
    return redirect_after_action()

@main.route("/about")
def about():
    return render_template('about.html', title='About')

@main.route("/privacy")
def privacy():
    return render_template('privacy.html', title='Privacy Policy')

@main.route("/terms")
def terms():
    return render_template('terms.html', title='Terms & Conditions')

@main.route("/support")
def support():
    return render_template('support.html', title='Support')

@main.route("/edit-profile", methods=['GET', 'POST'])
@login_required
@require_verified
@require_role('DEVELOPER')
def edit_profile():
    form = EditProfileForm()
    profile = current_user.developer_profile
    
    if form.validate_on_submit():
        profile.headline = form.headline.data
        profile.location = form.location.data
        profile.availability = form.availability.data
        profile.technologies = normalize_technologies_input(form.technologies.data)
        profile.github_link = normalize_url(form.github_link.data)
        profile.linkedin_link = normalize_url(form.linkedin_link.data)
        profile.portfolio_link = normalize_url(form.portfolio_link.data)
        if form.profile_theme.data:
            profile.profile_theme = form.profile_theme.data
        if form.profile_animation.data:
            profile.profile_animation = form.profile_animation.data
        if form.profile_panel_style.data:
            profile.profile_panel_style = form.profile_panel_style.data
        if form.profile_background.data:
            profile.profile_background = form.profile_background.data

        # Handle profile picture upload (save to app/static/profile_pics so url_for('static', ...) serves it)
        if form.picture.data:
            pic_file = form.picture.data
            filename = secure_filename(pic_file.filename)
            _, ext = os.path.splitext(filename)
            filename = f"user_{current_user.id}{ext}"
            static_dir = os.path.join(current_app.static_folder, 'profile_pics')
            os.makedirs(static_dir, exist_ok=True)
            abs_pic_path = os.path.join(static_dir, filename)
            pic_file.save(abs_pic_path)
            current_user.image_file = filename
        db.session.commit()
        flash('Profile Updated!', 'success')
        return redirect(url_for('main.dashboard'))
    elif request.method == 'GET':
        defaults = developer_profile_theme_defaults(profile)
        form.headline.data = profile.headline
        form.location.data = profile.location
        form.availability.data = profile.availability
        form.technologies.data = technologies_for_edit(profile)
        form.github_link.data = profile.github_link
        form.linkedin_link.data = profile.linkedin_link
        form.portfolio_link.data = profile.portfolio_link
        form.profile_theme.data = defaults['profile_theme']
        form.profile_animation.data = defaults['profile_animation']
        form.profile_panel_style.data = defaults['profile_panel_style']
        form.profile_background.data = defaults['profile_background']

    return render_template('edit_profile.html', title='Edit Profile', form=form)

ABOUT_ME_MAX_LENGTH = 600
PINNED_PROJECTS_MAX = 3


@main.route("/update-markdown", methods=['POST'])
@login_required
@require_verified
@require_role('DEVELOPER', json_response=True)
def update_markdown():
    content = request.form.get('content') or ''
    if len(content) > ABOUT_ME_MAX_LENGTH:
        flash(f'About Me is limited to {ABOUT_ME_MAX_LENGTH} characters. You entered {len(content)}.', 'danger')
        return redirect(url_for('main.dashboard'))
    profile = current_user.developer_profile
    profile.custom_markdown = content
    db.session.commit()
    flash('About Me updated!', 'success')
    return redirect(url_for('main.dashboard'))

@main.route("/add-pinned-project", methods=['POST'])
@login_required
@require_verified
@require_role('DEVELOPER')
def add_pinned_project():
    profile = current_user.developer_profile
    if len(profile.pinned_projects) >= PINNED_PROJECTS_MAX:
        flash(f'You can pin at most {PINNED_PROJECTS_MAX} projects. Remove one to add another.', 'warning')
        return redirect(url_for('main.dashboard'))
    title = request.form.get('title')
    desc = request.form.get('description')
    tags = request.form.get('tags')
    link = request.form.get('link')
    if title and desc:
        project = PinnedProject(
            profile_id=profile.id,
            title=title,
            description=desc,
            tags=tags,
            link=link
        )
        db.session.add(project)
        db.session.commit()
        flash('Project Pinned!', 'success')
    return redirect(url_for('main.dashboard'))

@main.route("/pin-delete/<int:id>")
@login_required
@require_verified
@require_role('DEVELOPER')
def delete_pinned(id):
    project = PinnedProject.query.get_or_404(id)
    if project.profile.user_id != current_user.id:
        flash('Access Denied', 'danger')
        return redirect(url_for('main.dashboard'))
    db.session.delete(project)
    db.session.commit()
    flash('Project Removed', 'success')
    return redirect(url_for('main.dashboard'))

def _send_verification_email(user):
    """Send verification email to user. Returns True if sent, False if mail not configured or send failed."""
    username = current_app.config.get('MAIL_USERNAME')
    password = current_app.config.get('MAIL_PASSWORD')
    if not username or not password:
        logger.warning(
            'Email verification skipped: MAIL_USERNAME or MAIL_PASSWORD not set (check .env EMAIL_USER and EMAIL_PASS).'
        )
        return False
    token = user.get_verification_token()
    verify_url = url_for('main.verify_email', token=token, _external=True)
    msg = Message(
        subject='Verify your JrDev account',
        sender=username,
        recipients=[user.email],
        body=f'''Welcome to JrDev. Please verify your email by clicking the link below.

{verify_url}

This link expires in 30 minutes. If you did not create an account, you can ignore this email.

— JrDev Team''',
    )
    try:
        mail.send(msg)
        logger.info('Verification email sent to %s', user.email)
        return True
    except Exception as e:
        logger.exception('Verification email failed for %s: %s', user.email, e)
        return False


@main.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect_after_action()
    form = RegistrationForm()
    
    if request.method == 'GET':
        role = request.args.get('role')
        if role in ['DEVELOPER', 'BUSINESS']:
            form.role.data = role
            
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        totp_secret = pyotp.random_base32()
        user = User(
            username=form.username.data,
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            email=form.email.data,
            password=hashed_password,
            role=form.role.data,
            two_factor_secret=totp_secret,
        )
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('That email or username is already registered. Please use a different one or log in.', 'danger')
            return render_template('register.html', title='Register', form=form)
        if form.role.data == 'DEVELOPER':
            profile = DeveloperProfile(user_id=user.id)
            db.session.add(profile)
            db.session.commit()
        if _send_verification_email(user):
            session['verification_email_sent_to'] = user.email
            flash('Account created. Check your email for a verification link to activate your account.', 'success')
        else:
            user.is_verified = True
            db.session.commit()
            flash('Account created. Email verification is not configured on this server; you can log in now.', 'info')
            login_user(user)
            return redirect(url_for('main.dashboard'))
        return redirect(url_for('main.verify_email_sent'))
    return render_template('register.html', title='Register', form=form)

@main.route("/verify-email-sent")
def verify_email_sent():
    email = session.get('verification_email_sent_to') or session.get('unverified_email')
    if not email:
        return redirect(url_for('main.login'))
    return render_template('verify_email_sent.html', email=email)


@main.route("/verify-email/<token>")
def verify_email(token):
    user = User.verify_token(token)
    if not user:
        flash('Verification link is invalid or has expired. Please request a new one.', 'danger')
        return redirect(url_for('main.login'))
    user.is_verified = True
    db.session.commit()
    session.pop('verification_email_sent_to', None)
    session.pop('unverified_email', None)
    if current_user.is_authenticated and current_user.id == user.id:
        flash('Email verified. You’re all set.', 'success')
    else:
        login_user(user)
        flash('Email verified. Welcome to JrDev! You can set up 2FA from Account when you’re ready.', 'success')
    return redirect(url_for('main.dashboard'))


@main.route("/resend-verification", methods=['POST'])
def resend_verification():
    email = request.form.get('email') or session.get('verification_email_sent_to') or session.get('unverified_email')
    if not email:
        flash('Please enter your email address.', 'warning')
        return redirect(url_for('main.login'))
    user = User.query.filter_by(email=email).first()
    if user and not user.is_verified and _send_verification_email(user):
        session['verification_email_sent_to'] = email
        flash('Verification email sent. Check your inbox and spam folder.', 'success')
    elif user and user.is_verified:
        flash('This account is already verified. You can log in.', 'info')
        return redirect(url_for('main.login'))
    else:
        flash('We couldn’t send a verification email. Check the address or try again later.', 'warning')
    return redirect(url_for('main.verify_email_sent'))


@main.route("/setup-2fa", methods=['GET', 'POST'])
@login_required
@require_verified
def setup_2fa():
    user = current_user
    totp_uri = user.get_totp_uri()
    if request.method == 'POST':
        token = request.form.get('token')
        if user.verify_totp(token):
            flash('2FA set up. Your account is more secure.', 'success')
            return redirect(url_for('main.dashboard'))
        flash('Invalid code. Please try again.', 'danger')
    img = qrcode.make(totp_uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_code = base64.b64encode(buf.getvalue()).decode('utf-8')
    return render_template('setup_2fa.html', qr_code=qr_code)


@main.route("/skip-2fa")
@login_required
@require_verified
def skip_2fa():
    flash('You can set up 2FA anytime from Account settings.', 'info')
    return redirect(url_for('main.dashboard'))

@main.route("/verify-2fa", methods=['GET', 'POST'])
def verify_2fa():
    if not session.get('2fa_user_id'):
        return redirect(url_for('main.login'))
        
    if request.method == 'POST':
        token = request.form.get('token')
        u_id = session.get('2fa_user_id')
        user = User.query.get(u_id)
        
        if user:
            totp = pyotp.TOTP(user.two_factor_secret)
            if totp.verify(token):
                login_user(user)
                session.pop('2fa_user_id', None)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
            else:
                flash('Invalid 2FA Code', 'danger')
        else:
            session.pop('2fa_user_id', None)
            return redirect(url_for('main.login'))
            
    return render_template('verify_2fa.html')

@main.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_after_action()
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            if not user.is_verified:
                session['unverified_email'] = user.email
                flash('Please verify your email before logging in. Check your inbox or resend the link below.', 'warning')
                return redirect(url_for('main.verify_email_sent'))
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        flash('Login unsuccessful. Check email and password.', 'danger')
    return render_template('login.html', title='Login', form=form)

@main.route("/logout")
def logout():
    logout_user()
    return redirect_after_action()

@main.route("/account")
@login_required
@require_verified
def account():
    nav_active = 'account'
    return render_template('account.html', title='Account', nav_active=nav_active)

# ── Billing (Stripe) – BUSINESS only ──

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


@main.route("/billing/stripe-status")
@login_required
def billing_stripe_status():
    """Diagnostic: report whether Stripe is configured (for debugging)."""
    has_secret = bool(_stripe_secret_key())
    has_publishable = bool(_stripe_publishable_key())
    stripe_imported = stripe is not None
    configured = _stripe_available()
    return jsonify({
        'configured': configured,
        'stripe_module': stripe_imported,
        'STRIPE_SECRET_KEY_set': has_secret,
        'STRIPE_PUBLISHABLE_KEY_set': has_publishable,
    })


@main.route("/billing")
@login_required
@require_verified
@require_role('BUSINESS')
def billing():
    stripe_publishable_key = _stripe_publishable_key()
    card_last4 = None
    card_brand = None
    if _stripe_available() and current_user.stripe_customer_id:
        stripe.api_key = _stripe_secret_key()
        try:
            pms = stripe.PaymentMethod.list(customer=current_user.stripe_customer_id, type='card')
            if pms.data:
                pm = pms.data[0]
                card_last4 = pm.card.last4
                card_brand = (pm.card.brand or '').capitalize()
        except stripe.error.StripeError:
            pass
    return render_template('billing.html',
                           title='Billing',
                           nav_active='billing',
                           stripe_publishable_key=stripe_publishable_key,
                           card_last4=card_last4,
                           card_brand=card_brand,
                           csrf_token=generate_csrf())

@main.route("/developer/settings/create-setup-intent", methods=['POST'])
@login_required
@require_verified
@require_role('DEVELOPER')
def developer_settings_create_setup_intent():
    """Create SetupIntent for developer to add card (prize pool entry fees)."""
    if not _stripe_available():
        return jsonify({'error': 'Stripe is not configured'}), 503
    stripe.api_key = _stripe_secret_key()
    customer = _get_or_create_stripe_customer_for_developer()
    if not customer:
        return jsonify({'error': 'Could not create customer'}), 500
    try:
        logger.info('Stripe API: SetupIntent.create (developer) for customer %s', customer.id)
        intent = stripe.SetupIntent.create(
            customer=customer.id,
            payment_method_types=['card'],
            usage='off_session',
        )
        return jsonify({'client_secret': intent.client_secret})
    except stripe.error.StripeError as e:
        logger.warning('Stripe API error (developer SetupIntent): %s', e)
        return jsonify({'error': str(e)}), 400

@main.route("/billing/create-setup-intent", methods=['POST'])
@login_required
@require_verified
@require_role('BUSINESS')
def billing_create_setup_intent():
    if not _stripe_available():
        return jsonify({'error': 'Stripe is not configured'}), 503
    stripe.api_key = _stripe_secret_key()
    customer = _get_stripe_customer()
    if not customer:
        return jsonify({'error': 'Could not create customer'}), 500
    try:
        logger.info('Stripe API: SetupIntent.create (business) for customer %s', customer.id)
        intent = stripe.SetupIntent.create(
            customer=customer.id,
            payment_method_types=['card'],
            usage='off_session',
        )
        return jsonify({'client_secret': intent.client_secret})
    except stripe.error.StripeError as e:
        logger.warning('Stripe API error (business SetupIntent): %s', e)
        return jsonify({'error': str(e)}), 400

@main.route("/developer/listings")
@login_required
@require_verified
@require_role('DEVELOPER')
def developer_listings():
    all_listings = SprintListing.query.filter_by(status='open').order_by(SprintListing.created_at.desc()).all()
    joined_listing_ids = {s.listing_id for s in ListingSignup.query.filter_by(user_id=current_user.id).all()}
    listings = [l for l in all_listings if l.id not in joined_listing_ids]
    form = AddPinnedProjectForm()
    return render_template('developer_listings.html', title='Available Listings', nav_active='listings', listings=listings, form=form)

@main.route("/developer/joined")
@login_required
@require_verified
@require_role('DEVELOPER')
def developer_joined_listings():
    signups = ListingSignup.query.filter_by(user_id=current_user.id).order_by(ListingSignup.joined_at.desc()).all()
    signup_review_deadlines = {
        s.id: review_deadline_from(s.prototype_submitted_at)
        if s.prototype_submitted_at and not s.reviewed_at and not s.flagged_for_review else None
        for s in signups
    }
    prize_pool_entries = PrizePoolEntry.query.filter_by(user_id=current_user.id).order_by(PrizePoolEntry.joined_at.desc()).all()
    form = AddPinnedProjectForm()
    profile = current_user.developer_profile
    return render_template('developer_joined_listings.html', title='Joined Listings', nav_active='joined', signups=signups, signup_review_deadlines=signup_review_deadlines, prize_pool_entries=prize_pool_entries, form=form, saved_signature=profile.saved_signature if profile else None, saved_contractor_address=profile.saved_contractor_address if profile else None)


# ── Prize Pools ──

@main.route("/developer/prize-pools")
@login_required
@require_verified
@require_role('DEVELOPER')
def developer_prize_pools():
    """List available prize pools (paid + free placeholder). Include joined pools with badge."""
    all_pools = PrizePool.query.filter(PrizePool.status.in_(['open', 'voting'])).order_by(PrizePool.created_at.desc()).all()
    joined_pool_ids = {e.prize_pool_id for e in PrizePoolEntry.query.filter_by(user_id=current_user.id).all()}
    paid_pools = [p for p in all_pools if p.pool_type == 'paid']
    free_pools = [p for p in all_pools if p.pool_type == 'free']
    form = AddPinnedProjectForm()
    return render_template('developer_prize_pools.html', title='Prize Pools', nav_active='prize_pools', paid_pools=paid_pools, free_pools=free_pools, joined_pool_ids=joined_pool_ids, form=form)

@main.route("/developer/prize-pools/joined")
@login_required
@require_verified
@require_role('DEVELOPER')
def developer_joined_prize_pools():
    """Redirect to Joined Listings (prize pools are shown there)."""
    return redirect(url_for('main.developer_joined_listings'))


@main.route("/developer/settings", methods=['GET', 'POST'])
@login_required
@require_verified
@require_role('DEVELOPER')
def developer_settings():
    """Settings: saved signature, contractor address, and Stripe billing."""
    profile = current_user.developer_profile
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'save_signature':
            sig = (request.form.get('signature_data') or '').strip()
            addr = (request.form.get('contractor_address') or '').strip() or None
            profile.saved_signature = sig if (sig and sig.startswith('data:image')) else None
            profile.saved_contractor_address = addr
            db.session.commit()
            flash('Signature and address saved. They will be used when signing contracts.', 'success')
        elif action == 'billing_portal' and _stripe_available():
            stripe.api_key = _stripe_secret_key()
            cust_id = current_user.stripe_customer_id
            if not cust_id:
                try:
                    cust = stripe.Customer.create(email=current_user.email)
                    cust_id = cust.id
                    current_user.stripe_customer_id = cust_id
                    db.session.commit()
                except stripe.error.StripeError:
                    flash('Could not set up billing. Please try again.', 'danger')
                    return redirect(url_for('main.developer_settings'))
            try:
                session = stripe.billing_portal.Session.create(
                    customer=cust_id,
                    return_url=url_for('main.developer_settings', _external=True),
                )
                return redirect(session.url)
            except stripe.error.StripeError:
                flash('Could not open billing portal. Please try again.', 'danger')
        return redirect(url_for('main.developer_settings'))
    stripe_publishable_key = _stripe_publishable_key()
    card_last4 = None
    card_brand = None
    if _stripe_available() and current_user.stripe_customer_id:
        stripe.api_key = _stripe_secret_key()
        try:
            pms = stripe.PaymentMethod.list(customer=current_user.stripe_customer_id, type='card')
            if pms.data:
                pm = pms.data[0]
                card_last4 = pm.card.last4
                card_brand = (pm.card.brand or '').capitalize()
        except stripe.error.StripeError:
            pass
    return render_template('developer_settings.html',
                           title='Settings',
                           nav_active='settings',
                           profile=profile,
                           stripe_available=_stripe_available(),
                           stripe_publishable_key=stripe_publishable_key,
                           card_last4=card_last4,
                           card_brand=card_brand,
                           csrf_token=generate_csrf())


def _prize_pool_join_checkout(pool, user):
    """Create Stripe Checkout Session for prize pool entry fee. Returns session URL or None on error."""
    if not _stripe_available() or not pool.entry_fee_gbp or pool.entry_fee_gbp <= 0:
        return None
    stripe.api_key = _stripe_secret_key()
    try:
        session = stripe.checkout.Session.create(
            mode='payment',
            payment_method_types=['card'],
            customer=user.stripe_customer_id if user.stripe_customer_id else None,
            customer_email=user.email if not user.stripe_customer_id else None,
            line_items=[{
                'price_data': {
                    'currency': 'gbp',
                    'product_data': {
                        'name': f'Prize Pool: {pool.title}',
                        'description': f'Entry fee for {pool.title}',
                    },
                    'unit_amount': int(pool.entry_fee_gbp * 100),
                },
                'quantity': 1,
            }],
            metadata={'prize_pool_id': str(pool.id), 'user_id': str(user.id)},
            success_url=url_for('main.prize_pool_join_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('main.developer_prize_pools', _external=True),
        )
        return session.url
    except stripe.error.StripeError:
        return None


@main.route("/prize-pool/<int:pool_id>/join", methods=['POST'])
@login_required
@require_verified
@require_role('DEVELOPER')
def prize_pool_join(pool_id):
    """Join a prize pool. For paid pools, redirects to Stripe Checkout. For free, placeholder."""
    pool = PrizePool.query.get_or_404(pool_id)
    if pool.status not in ('open', 'voting'):
        flash('This prize pool is no longer accepting entries.', 'warning')
        return redirect(url_for('main.developer_prize_pools'))
    existing = PrizePoolEntry.query.filter_by(prize_pool_id=pool_id, user_id=current_user.id).first()
    if existing:
        flash('You have already joined this prize pool.', 'info')
        return redirect(url_for('main.developer_joined_prize_pools'))
    if pool.pool_type == 'free':
        entry = PrizePoolEntry(prize_pool_id=pool_id, user_id=current_user.id, payment_completed_at=datetime.utcnow())
        db.session.add(entry)
        db.session.commit()
        flash('You have joined this prize pool!', 'success')
        return redirect(url_for('main.developer_joined_prize_pools'))
    if pool.entry_fee_gbp and pool.entry_fee_gbp > 0:
        checkout_url = _prize_pool_join_checkout(pool, current_user)
        if checkout_url:
            return redirect(checkout_url)
        flash('Payment is not available. Please try again later.', 'danger')
        return redirect(url_for('main.developer_prize_pools'))
    else:
        entry = PrizePoolEntry(prize_pool_id=pool_id, user_id=current_user.id, payment_completed_at=datetime.utcnow())
        db.session.add(entry)
        db.session.commit()
        flash('You have joined this prize pool!', 'success')
    return redirect(url_for('main.developer_joined_prize_pools'))


@main.route("/prize-pool/join/success")
@login_required
@require_verified
@require_role('DEVELOPER')
def prize_pool_join_success():
    """Handle Stripe Checkout success: verify payment and create PrizePoolEntry."""
    session_id = request.args.get('session_id')
    if not session_id or not _stripe_available():
        flash('Invalid or missing payment session.', 'danger')
        return redirect(url_for('main.developer_prize_pools'))
    stripe.api_key = _stripe_secret_key()
    try:
        logger.info('Stripe API: checkout.Session.retrieve (session_id=%s)', session_id[:20] + '...' if len(session_id) > 20 else session_id)
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status != 'paid':
            flash('Payment was not completed.', 'warning')
            return redirect(url_for('main.developer_prize_pools'))
        pool_id = int(session.metadata.get('prize_pool_id', 0))
        user_id = int(session.metadata.get('user_id', 0))
        if user_id != current_user.id:
            flash('Session does not match your account.', 'danger')
            return redirect(url_for('main.developer_prize_pools'))
        pool = PrizePool.query.get(pool_id)
        if not pool:
            flash('Prize pool not found.', 'danger')
            return redirect(url_for('main.developer_prize_pools'))
        existing = PrizePoolEntry.query.filter_by(prize_pool_id=pool_id, user_id=user_id).first()
        if existing:
            if not existing.payment_completed_at:
                existing.payment_completed_at = datetime.utcnow()
                existing.payment_intent_id = session.payment_intent
                db.session.commit()
            flash('You have joined this prize pool!', 'success')
        else:
            entry = PrizePoolEntry(
                prize_pool_id=pool_id,
                user_id=user_id,
                payment_intent_id=session.payment_intent,
                payment_completed_at=datetime.utcnow(),
            )
            db.session.add(entry)
            db.session.commit()
            flash('You have joined this prize pool!', 'success')
    except stripe.error.StripeError:
        flash('Could not verify payment. Please contact support if you were charged.', 'danger')
    return redirect(url_for('main.developer_joined_prize_pools'))


@main.route("/prize-pool/<int:pool_id>/submit", methods=['POST'])
@login_required
@require_verified
@require_role('DEVELOPER')
def prize_pool_submit(pool_id):
    """Submit demo video and GitHub URL for a prize pool entry."""
    pool = PrizePool.query.get_or_404(pool_id)
    entry = PrizePoolEntry.query.filter_by(prize_pool_id=pool_id, user_id=current_user.id).first()
    if not entry or not entry.payment_completed_at:
        flash('You must join this prize pool before submitting.', 'danger')
        return redirect(url_for('main.developer_joined_listings'))
    if pool.submission_ends_at and datetime.utcnow() > pool.submission_ends_at:
        flash('Submission deadline has passed.', 'warning')
        return redirect(url_for('main.developer_joined_listings'))
    entry.demo_video_url = request.form.get('demo_video_url', '').strip() or None
    entry.github_submission_url = request.form.get('github_submission_url', '').strip() or None
    reqs = request.form.getlist('requirements_met')
    entry.requirements_met = ', '.join(reqs) if reqs else None
    entry.submitted_at = datetime.utcnow()
    db.session.commit()
    flash('Your work has been submitted!', 'success')
    return redirect(url_for('main.developer_joined_listings'))


def _get_next_pairwise_pair(pool_id, voter_id):
    """Return (entry_a, entry_b) for next pairwise comparison, or (None, None) if no more pairs.
    Excludes voter's entry, only entries with demo_video_url, prefers under-compared entries."""
    pool = PrizePool.query.get(pool_id)
    if not pool:
        return None, None
    eligible = [e for e in pool.entries if e.submitted_at and e.user_id != voter_id and e.demo_video_url and youtube_embed_url(e.demo_video_url)]
    if len(eligible) < 2:
        return None, None
    # Pairs this voter has already compared
    existing = PrizePoolPairwiseVote.query.filter_by(prize_pool_id=pool_id, voter_id=voter_id).all()
    compared = {(min(v.entry_a_id, v.entry_b_id), max(v.entry_a_id, v.entry_b_id)) for v in existing}
    # Count comparisons per entry (for coverage)
    from collections import Counter
    comp_count = Counter()
    for v in pool.pairwise_votes:
        comp_count[v.entry_a_id] += 1
        comp_count[v.entry_b_id] += 1
    # All possible pairs (excluding already compared by this voter)
    import itertools
    import random
    candidates = []
    for a, b in itertools.combinations(eligible, 2):
        key = (min(a.id, b.id), max(a.id, b.id))
        if key not in compared:
            score = -(comp_count[a.id] + comp_count[b.id])  # prefer less-compared
            candidates.append((score, a, b))
    if not candidates:
        return None, None
    candidates.sort(key=lambda x: x[0])
    best_score = candidates[0][0]
    best = [c for c in candidates if c[0] == best_score]
    _, ea, eb = random.choice(best)
    return ea, eb


@main.route("/prize-pool/<int:pool_id>/review/next-pair", methods=['GET'])
@login_required
@require_verified
@require_role('DEVELOPER')
def prize_pool_review_next_pair(pool_id):
    """Return next pairwise comparison as JSON, or null if no more pairs."""
    pool = PrizePool.query.get_or_404(pool_id)
    entry = PrizePoolEntry.query.filter_by(prize_pool_id=pool_id, user_id=current_user.id).first()
    if not entry or not entry.submitted_at:
        return jsonify({'error': 'Must submit before reviewing'}), 403
    ea, eb = _get_next_pairwise_pair(pool_id, current_user.id)
    if not ea or not eb:
        return jsonify({'pair': None})
    embed_a = youtube_embed_url(ea.demo_video_url, autoplay=True, mute=True)
    embed_b = youtube_embed_url(eb.demo_video_url, autoplay=True, mute=True)
    return jsonify({
        'pair': {
            'entry_a': {'id': ea.id, 'demo_video_url': ea.demo_video_url, 'embed_url': embed_a},
            'entry_b': {'id': eb.id, 'demo_video_url': eb.demo_video_url, 'embed_url': embed_b},
        }
    })


@main.route("/prize-pool/<int:pool_id>/review/vote", methods=['POST'])
@login_required
@require_verified
@require_role('DEVELOPER')
def prize_pool_review_vote(pool_id):
    """Submit pairwise vote: winner_entry_id, entry_a_id, entry_b_id."""
    pool = PrizePool.query.get_or_404(pool_id)
    entry = PrizePoolEntry.query.filter_by(prize_pool_id=pool_id, user_id=current_user.id).first()
    if not entry or not entry.submitted_at:
        return jsonify({'error': 'Must submit before reviewing'}), 403
    data = request.get_json() or {}
    winner_id = int(data.get('winner_entry_id', 0) or 0)
    entry_a_id = int(data.get('entry_a_id', 0) or 0)
    entry_b_id = int(data.get('entry_b_id', 0) or 0)
    if winner_id not in (entry_a_id, entry_b_id) or entry_a_id == entry_b_id:
        return jsonify({'error': 'Invalid vote'}), 400
    ea = PrizePoolEntry.query.get(entry_a_id)
    eb = PrizePoolEntry.query.get(entry_b_id)
    if not ea or not eb or ea.prize_pool_id != pool_id or eb.prize_pool_id != pool_id:
        return jsonify({'error': 'Invalid entries'}), 400
    a, b = min(entry_a_id, entry_b_id), max(entry_a_id, entry_b_id)
    existing = PrizePoolPairwiseVote.query.filter_by(
        prize_pool_id=pool_id, voter_id=current_user.id,
        entry_a_id=a, entry_b_id=b
    ).first()
    if existing:
        return jsonify({'error': 'Already voted for this pair'}), 400
    vote = PrizePoolPairwiseVote(
        prize_pool_id=pool_id,
        voter_id=current_user.id,
        entry_a_id=a,
        entry_b_id=b,
        winner_entry_id=winner_id,
    )
    db.session.add(vote)
    db.session.commit()
    return jsonify({'ok': True})


@main.route("/prize-pool/<int:pool_id>/vote", methods=['GET'])
@login_required
@require_verified
@require_role('DEVELOPER')
def prize_pool_vote_page(pool_id):
    """Show pairwise review UI: two videos side-by-side, 30s watch, Rank best. Participants only, must have submitted."""
    pool = PrizePool.query.get_or_404(pool_id)
    entry = PrizePoolEntry.query.filter_by(prize_pool_id=pool_id, user_id=current_user.id).first()
    if not entry or not entry.payment_completed_at:
        flash('You must join this prize pool before voting.', 'danger')
        return redirect(url_for('main.developer_joined_prize_pools'))
    if not entry.submitted_at:
        flash('You must submit your work before voting.', 'warning')
        return redirect(url_for('main.developer_joined_prize_pools'))
    submitted_with_video = [e for e in pool.entries if e.submitted_at and e.user_id != current_user.id and e.demo_video_url and youtube_embed_url(e.demo_video_url)]
    if len(submitted_with_video) < 2:
        form = AddPinnedProjectForm()
        return render_template('prize_pool_vote.html', pool=pool, can_vote=False, form=form,
                               title='Complete reviews', nav_active='prize_pools_joined', csrf_token=generate_csrf())
    form = AddPinnedProjectForm()
    return render_template('prize_pool_vote.html', pool=pool, can_vote=True, form=form,
                           title='Complete reviews', nav_active='prize_pools_joined', csrf_token=generate_csrf())


@main.route("/prize-pool/<int:pool_id>/vote", methods=['POST'])
@login_required
@require_verified
@require_role('DEVELOPER')
def prize_pool_vote_submit(pool_id):
    """Submit vote: rank_1_id, rank_2_id, rank_3_id (1st=best, 3rd=worst)."""
    pool = PrizePool.query.get_or_404(pool_id)
    entry = PrizePoolEntry.query.filter_by(prize_pool_id=pool_id, user_id=current_user.id).first()
    if not entry or not entry.submitted_at:
        flash('You must submit before voting.', 'warning')
        return redirect(url_for('main.developer_joined_prize_pools'))
    if PrizePoolVote.query.filter_by(prize_pool_id=pool_id, voter_id=current_user.id).first():
        flash('You have already voted.', 'info')
        return redirect(url_for('main.developer_joined_prize_pools'))
    rank_1_id = int(request.form.get('rank_1_id', 0) or 0)
    rank_2_id = int(request.form.get('rank_2_id', 0) or 0)
    rank_3_id = int(request.form.get('rank_3_id', 0) or 0)
    entry_ids_str = request.form.get('entry_ids', '')
    try:
        shown_ids = [int(x.strip()) for x in entry_ids_str.split(',') if x.strip()]
    except ValueError:
        shown_ids = []
    if len(shown_ids) != 3 or {rank_1_id, rank_2_id, rank_3_id} != set(shown_ids):
        flash('Invalid vote. Please rank exactly the 3 entries shown.', 'danger')
        return redirect(url_for('main.prize_pool_vote_page', pool_id=pool_id))
    entry_1_id, entry_2_id, entry_3_id = shown_ids[0], shown_ids[1], shown_ids[2]
    vote = PrizePoolVote(
        prize_pool_id=pool_id,
        voter_id=current_user.id,
        entry_1_id=entry_1_id,
        entry_2_id=entry_2_id,
        entry_3_id=entry_3_id,
        rank_1_id=rank_1_id,
        rank_2_id=rank_2_id,
        rank_3_id=rank_3_id,
    )
    db.session.add(vote)
    db.session.commit()
    flash('Your vote has been recorded.', 'success')
    return redirect(url_for('main.developer_joined_prize_pools'))


@main.route("/prize-pool/<int:pool_id>/results")
@login_required
@require_verified
@require_role('DEVELOPER')
def prize_pool_results(pool_id):
    """Show pool results: winners (top 10%) and all submitted entries."""
    pool = PrizePool.query.get_or_404(pool_id)
    entry = PrizePoolEntry.query.filter_by(prize_pool_id=pool_id, user_id=current_user.id).first()
    if not entry:
        flash('You must join this prize pool to view results.', 'danger')
        return redirect(url_for('main.developer_joined_prize_pools'))
    submitted = [e for e in pool.entries if e.submitted_at]
    winners = [e for e in submitted if e.is_winner]
    return render_template('prize_pool_results.html', pool=pool, winners=winners, submitted=submitted,
                           title='Results', nav_active='prize_pools_joined')


# ── Admin: Prize Pool Management ──

@main.route("/admin/prize-pools", methods=['GET', 'POST'])
@login_required
@require_verified
@require_prize_pool_admin
def admin_prize_pools():
    """Create and list prize pools (platform admin)."""
    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        if not title:
            flash('Title is required.', 'danger')
            return redirect(url_for('main.admin_prize_pools'))
        pool_type = request.form.get('pool_type', 'paid')
        entry_fee = None
        if pool_type == 'paid':
            try:
                entry_fee = float(request.form.get('entry_fee_gbp', 0) or 0)
            except (ValueError, TypeError):
                entry_fee = 0
        description = (request.form.get('description') or '').strip() or None
        technologies = (request.form.get('technologies_required') or '').strip() or None
        essential_deliverables = (request.form.get('essential_deliverables') or '').strip() or None
        optional_deliverables = (request.form.get('optional_deliverables') or '').strip() or None
        try:
            signup_ends = datetime.strptime(request.form.get('signup_ends_at', ''), '%Y-%m-%d')
            submission_ends = datetime.strptime(request.form.get('submission_ends_at', ''), '%Y-%m-%d')
        except (ValueError, TypeError):
            flash('Invalid dates. Use YYYY-MM-DD.', 'danger')
            return redirect(url_for('main.admin_prize_pools'))
        voting_ends = None
        if pool_type == 'paid':
            try:
                voting_ends = datetime.strptime(request.form.get('voting_ends_at', ''), '%Y-%m-%d')
            except (ValueError, TypeError):
                pass
        max_participants = None
        try:
            mp = request.form.get('max_participants', '').strip()
            if mp:
                max_participants = int(mp)
        except (ValueError, TypeError):
            pass
        pool = PrizePool(
            title=title,
            description=description,
            technologies_required=technologies,
            essential_deliverables=essential_deliverables,
            optional_deliverables=optional_deliverables,
            pool_type=pool_type,
            entry_fee_gbp=entry_fee if pool_type == 'paid' else None,
            signup_ends_at=signup_ends,
            submission_ends_at=submission_ends,
            voting_ends_at=voting_ends,
            max_participants=max_participants,
            status='open',
            created_by_id=current_user.id,
        )
        db.session.add(pool)
        db.session.commit()
        flash(f'Prize pool "{title}" created.', 'success')
        return redirect(url_for('main.admin_prize_pools'))
    pools = PrizePool.query.order_by(PrizePool.created_at.desc()).all()
    form = AddPinnedProjectForm()
    return render_template('admin_prize_pools.html', title='Prize Pool Admin', nav_active='admin_prize_pools',
                           pools=pools, form=form)


@main.route("/business/listings")
@login_required
@require_verified
@require_role('BUSINESS')
def business_my_listings():
    my_listings = SprintListing.query.filter_by(business_id=current_user.id).order_by(SprintListing.created_at.desc()).all()
    form = AddPinnedProjectForm()
    return render_template('business_my_listings.html', title='My Listings', nav_active='listings', my_listings=my_listings, form=form)

# ── Sprint Launch ──

@main.route("/launch-sprint", methods=['POST'])
@login_required
@require_verified
@require_role('BUSINESS')
def launch_sprint():
    company_name = request.form.get('company_name', '').strip() or (current_user.username + "'s Sprint")

    try:
        sprint_begins = datetime.strptime(request.form.get('sprint_begins_at', ''), '%Y-%m-%d')
        sprint_ends = datetime.strptime(request.form.get('sprint_ends_at', ''), '%Y-%m-%d')
        signup_ends = datetime.strptime(request.form.get('signup_ends_at', ''), '%Y-%m-%d')
    except (ValueError, TypeError):
        sprint_begins = datetime.utcnow() + timedelta(days=1)
        sprint_ends = sprint_begins + timedelta(days=7)
        signup_ends = sprint_begins

    if sprint_ends <= sprint_begins:
        flash('Sprint end date must be after the start date.', 'danger')
        return redirect(url_for('main.dashboard'))
    if sprint_begins.date() < datetime.utcnow().date():
        flash('Sprint start date cannot be in the past.', 'danger')
        return redirect(url_for('main.dashboard'))

    sprint_duration_days = (sprint_ends - sprint_begins).days
    if sprint_duration_days < 3:
        flash('Sprint duration must be at least 3 days.', 'danger')
        return redirect(url_for('main.dashboard'))
    if sprint_duration_days > 14:
        flash('Sprint duration cannot exceed 14 days (2 weeks).', 'danger')
        return redirect(url_for('main.dashboard'))

    technologies_required = (request.form.get('technologies_required') or '').strip()
    if not technologies_required:
        flash('Please add at least one technology before launching a sprint.', 'danger')
        return redirect(url_for('main.dashboard'))

    if _stripe_available() and not _business_has_card():
        flash('Please add a payment method before launching a sprint.', 'danger')
        return redirect(url_for('main.billing'))

    company_address = (request.form.get('company_address') or '').strip() or None
    listing = SprintListing(
        business_id=current_user.id,
        company_name=company_name,
        company_address=company_address,
        max_talent_pool=int(request.form.get('max_talent_pool', 3)),
        pay_for_prototype=float(request.form.get('pay_for_prototype', 60)),
        technologies_required=technologies_required,
        deliverables=(request.form.get('deliverables') or '').strip() or None,
        essential_deliverables=(request.form.get('essential_deliverables') or '').strip() or None,
        essential_deliverables_count=int(request.form.get('essential_deliverables_count', 0) or 0),
        sprint_timeline_days=sprint_duration_days,
        minimum_requirements_for_pay=int(request.form.get('minimum_requirements_for_pay', 1)),
        sprint_begins_at=sprint_begins,
        sprint_ends_at=sprint_ends,
        signup_ends_at=signup_ends,
    )
    db.session.add(listing)
    db.session.commit()
    flash('Sprint launched! Developers can now sign up.', 'success')
    return redirect(url_for('main.business_my_listings'))

# ── Developer joins a listing ──

@main.route("/listing/<int:id>/join", methods=['POST'])
@login_required
@require_verified
@require_role('DEVELOPER')
def join_listing(id):
    listing = SprintListing.query.get_or_404(id)
    existing = ListingSignup.query.filter_by(listing_id=id, user_id=current_user.id).first()
    if existing:
        flash('You have already joined this listing.', 'info')
        return redirect(url_for('main.developer_listings'))
    if listing.is_full:
        flash('This listing is full.', 'warning')
        return redirect(url_for('main.developer_listings'))

    signup = ListingSignup(listing_id=id, user_id=current_user.id)
    db.session.add(signup)
    profile = current_user.developer_profile
    if profile is not None:
        profile.contracts_attempted = (profile.contracts_attempted or 0) + 1
    db.session.commit()
    flash('You have joined the sprint! Waiting for business approval.', 'success')
    return redirect(url_for('main.developer_joined_listings'))

# ── Business accepts / denies developer ──

@main.route("/signup/<int:id>/accept", methods=['POST'])
@login_required
@require_verified
@require_role('BUSINESS')
def signup_accept(id):
    signup, err = get_signup_for_business(id)
    if err:
        return err
    signup.status = 'accepted'
    db.session.commit()
    flash(f'{signup.user.username} accepted.', 'success')
    return redirect(url_for('main.review_gallery'))


@main.route("/signup/<int:id>/deny", methods=['POST'])
@login_required
@require_verified
@require_role('BUSINESS')
def signup_deny(id):
    signup, err = get_signup_for_business(id)
    if err:
        return err
    signup.status = 'denied'
    db.session.commit()
    flash(f'{signup.user.username} denied.', 'info')
    return redirect(url_for('main.review_gallery'))

# ── E-signing ──

@main.route("/signup/<int:id>/sign/developer", methods=['POST'])
@login_required
@require_verified
@require_role('DEVELOPER')
def signup_sign_developer(id):
    signup, err = get_signup_for_developer(id)
    if err:
        return err
    signature_data = (request.form.get('signature_data') or '').strip()
    if signature_data and signature_data.startswith('data:image'):
        signup.developer_signature_image = signature_data
    contractor_address = (request.form.get('contractor_address') or '').strip() or None
    if contractor_address:
        signup.developer_registered_address = contractor_address
    signup.developer_signed_at = datetime.utcnow()
    db.session.commit()
    flash('Contract signed by you. Waiting for business countersign.', 'success')
    return redirect(url_for('main.developer_joined_listings'))


@main.route("/signup/<int:id>/sign/business", methods=['POST'])
@login_required
@require_verified
@require_role('BUSINESS')
def signup_sign_business(id):
    signup, err = get_signup_for_business(id)
    if err:
        return err
    signature_data = (request.form.get('signature_data') or '').strip()
    if signature_data and signature_data.startswith('data:image'):
        signup.business_signature_image = signature_data
    signup.business_signed_at = datetime.utcnow()
    db.session.commit()
    flash('Contract countersigned. Sprint is now active!', 'success')
    return redirect(url_for('main.review_gallery'))

# ── Developer cancels signup ──

@main.route("/signup/<int:id>/cancel", methods=['POST'])
@login_required
@require_verified
@require_role('DEVELOPER')
def signup_cancel(id):
    signup, err = get_signup_for_developer(id)
    if err:
        return err
    signup.status = 'cancelled'
    db.session.commit()
    flash('You have withdrawn from this listing.', 'info')
    return redirect(url_for('main.developer_joined_listings'))


# ── Developer submits deliverables ──


@main.route("/signup/<int:id>/submit", methods=['POST'])
@login_required
@require_verified
@require_role('DEVELOPER')
def signup_submit_deliverables(id):
    signup, err = get_signup_for_developer(id)
    if err:
        return err
    signup.github_submission_url = request.form.get('github_submission_url', '').strip() or None
    signup.demo_video_url = request.form.get('demo_video_url', '').strip() or None
    reqs = request.form.getlist('requirements_met')
    signup.requirements_met = ', '.join(reqs) if reqs else None
    signup.prototype_submitted_at = datetime.utcnow()
    db.session.commit()
    flash('Prototype submitted! The business will review your work.', 'success')
    return redirect(url_for('main.developer_joined_listings'))

# ── 48-hour review deadline & auto-release ──

def _apply_reviewed_state(signup):
    """Set reviewed_at and update developer profile stats (shared by mark-reviewed and auto-release). Caller must commit."""
    import json
    signup.reviewed_at = datetime.utcnow()
    profile = signup.user.developer_profile
    if profile:
        profile.prototypes_completed = (profile.prototypes_completed or 0) + 1
        profile.contracts_won = (profile.contracts_won or 0) + 1
        sprint_techs = parse_comma_separated(signup.listing.technologies_required)
        if sprint_techs:
            # Update technologies_verified (counts from completed sprints only; developers cannot fake these)
            raw = getattr(profile, 'technologies_verified', None)
            verified = {}
            if raw:
                try:
                    verified = json.loads(raw)
                except (TypeError, ValueError):
                    pass
            for tech in sprint_techs:
                key = tech.strip().lower()
                if key:
                    verified[key] = verified.get(key, 0) + 1
            profile.technologies_verified = json.dumps(verified)
            # Add new tech names to technologies (user's display list) if not already present
            from app.utils import _strip_tech_count
            existing_parts = [t for t in parse_comma_separated(profile.technologies or '') if _strip_tech_count(t)]
            existing_names = {_strip_tech_count(t).lower() for t in existing_parts}
            to_add = []
            for tech in sprint_techs:
                name = tech.strip()
                if name and name.lower() not in existing_names:
                    to_add.append(name)
                    existing_names.add(name.lower())
            if to_add:
                all_names = [_strip_tech_count(t) for t in existing_parts] + to_add
                profile.technologies = ', '.join(all_names)


def apply_auto_release(signup):
    """If signup is not yet reviewed, apply reviewed state (for 48h auto-release). Idempotent. Caller must commit."""
    if signup.reviewed_at is not None:
        return
    _apply_reviewed_state(signup)


def process_review_deadlines():
    """Find signups past the 48h review deadline and apply auto-release. Safe to call repeatedly (e.g. on each review_gallery load or via cron)."""
    now = datetime.utcnow()
    deadline_cutoff = now - timedelta(hours=REVIEW_DEADLINE_HOURS)
    overdue = ListingSignup.query.filter(
        ListingSignup.prototype_submitted_at.isnot(None),
        ListingSignup.reviewed_at.is_(None),
        ListingSignup.flagged_for_review == False,
        ListingSignup.prototype_submitted_at <= deadline_cutoff,
    ).all()
    for signup in overdue:
        apply_auto_release(signup)
        db.session.commit()


def process_prize_pool_winners():
    """Transition pool statuses (open->voting, voting->closed) and compute top 10% winners when voting ends. Safe to call via cron."""
    import math
    now = datetime.utcnow()
    # open -> voting when submission_ends_at passes
    open_pools = PrizePool.query.filter_by(status='open').all()
    for pool in open_pools:
        if pool.submission_ends_at and pool.submission_ends_at <= now:
            pool.status = 'voting'
            db.session.commit()
    # voting -> closed when voting_ends_at passes; compute top 10% winners
    voting_pools = PrizePool.query.filter_by(status='voting').all()
    for pool in voting_pools:
        if pool.voting_ends_at and pool.voting_ends_at <= now:
            pool.status = 'closed'
            # Aggregate pairwise wins: each winner_entry_id gets +1
            scores = {}
            for vote in pool.pairwise_votes:
                wid = vote.winner_entry_id
                scores[wid] = scores.get(wid, 0) + 1
            submitted = [e for e in pool.entries if e.submitted_at]
            if submitted and scores:
                n = len(submitted)
                top_count = max(1, math.ceil(0.1 * n))
                sorted_entries = sorted(submitted, key=lambda e: scores.get(e.id, 0), reverse=True)
                for e in pool.entries:
                    e.is_winner = False
                for e in sorted_entries[:top_count]:
                    e.is_winner = True
            db.session.commit()


# ── Business reviews developer submissions ──

@main.route("/signup/<int:id>/mark-reviewed", methods=['POST'])
@login_required
@require_verified
@require_role('BUSINESS')
def signup_mark_reviewed(id):
    signup, err = get_signup_for_business(id)
    if err:
        return err
    _apply_reviewed_state(signup)
    db.session.commit()
    flash(f'Marked as reviewed. You have been charged £{signup.listing.pay_for_prototype:.0f} for this developer.', 'success')
    return redirect(url_for('main.review_gallery'))

@main.route("/signup/<int:id>/flag", methods=['POST'])
@login_required
@require_verified
@require_role('BUSINESS')
def signup_flag_for_review(id):
    signup, err = get_signup_for_business(id)
    if err:
        return err
    signup.flagged_for_review = True
    db.session.commit()
    flash('Flagged for review. Our team will contact you and the developer to resolve. No charge will be made until the sprint is marked complete.', 'info')
    return redirect(url_for('main.review_gallery'))


@main.route("/signup/<int:id>/unflag", methods=['POST'])
@login_required
@require_verified
@require_role('BUSINESS')
def signup_unflag(id):
    signup, err = get_signup_for_business(id)
    if err:
        return err
    signup.flagged_for_review = False
    db.session.commit()
    flash('Removed flag.', 'info')
    return redirect(url_for('main.review_gallery'))


@main.route("/signup/<int:id>/rate-developer", methods=['POST'])
@login_required
@require_verified
@require_role('BUSINESS')
def signup_rate_developer(id):
    signup, err = get_signup_for_business(id)
    if err:
        return err
    return apply_rating_and_redirect(
        signup,
        'business_rating_of_developer',
        'main.review_gallery',
        flash_success_msg=f'Rated {signup.user.username} {_fmt_rating(request.form.get("rating"))}/5.0 stars.'
    )


@main.route("/signup/<int:id>/rate-business", methods=['POST'])
@login_required
@require_verified
@require_role('DEVELOPER')
def signup_rate_business(id):
    signup, err = get_signup_for_developer(id)
    if err:
        return err
    return apply_rating_and_redirect(
        signup,
        'developer_rating_of_business',
        'main.developer_joined_listings',
        flash_success_msg=f'Rated {signup.listing.company_name} {_fmt_rating(request.form.get("rating"))}/5.0 stars.'
    )


@main.route("/signup/<int:id>/cannot-complete", methods=['POST'])
@login_required
@require_verified
@require_role('DEVELOPER')
def signup_cannot_complete(id):
    signup, err = get_signup_for_developer(id)
    if err:
        return err
    signup.developer_withdrew = True
    db.session.commit()
    flash('You have indicated you cannot complete this project. The business has been notified.', 'info')
    return redirect(url_for('main.developer_joined_listings'))

# ── Developer public profile view (for businesses) ──


@main.route("/developer/<int:user_id>")
@login_required
@require_verified
@require_role('BUSINESS')
def developer_profile_view(user_id):
    """Business view: public developer profile (stack, rating, theme from utils)."""
    dev_user = User.query.get_or_404(user_id)
    if dev_user.role != 'DEVELOPER':
        flash('User is not a developer.', 'warning')
        return redirect(url_for('main.business_my_listings'))
    profile = dev_user.developer_profile
    md_html = markdown.markdown(profile.custom_markdown) if profile and profile.custom_markdown else ""
    stack_list = developer_stack_list(profile) if profile else []
    pinned_projects = profile.pinned_projects if profile else []
    avg_rating = developer_avg_rating(dev_user.id)
    theme_defaults = developer_profile_theme_defaults(profile) if profile else {}

    return render_template('developer_profile_view.html',
                           title=f'{dev_user.username} - Profile',
                           dev_user=dev_user,
                           profile=profile,
                           md_html=md_html,
                           stack_list=stack_list,
                           pinned_projects=pinned_projects,
                           avg_rating=avg_rating,
                           profile_theme=theme_defaults.get('profile_theme', 'mint'),
                           profile_animation=theme_defaults.get('profile_animation', 'glow'),
                           profile_panel_style=theme_defaults.get('profile_panel_style', 'solid'),
                           profile_background=theme_defaults.get('profile_background', 'default'),
                           back_url=url_for('main.review_gallery'),
                           back_text='Back to Your Listings',
                           nav_active='listings')


# Reserved path segments that must not be treated as usernames
_PROFILE_RESERVED = frozenset({
    'login', 'logout', 'register', 'account', 'billing', 'dashboard', 'developers',
    'developer', 'business', 'signup', 'listing', 'admin', 'prize-pool', 'static',
    'about', 'privacy', 'terms', 'support', 'home', 'edit-profile', 'verify-email',
    'setup-2fa', 'verify-2fa', 'skip-2fa', 'resend-verification', 'api'
})


@main.route("/<username>")
@login_required
@require_verified
def profile_by_username(username):
    """Public profile by username: /username. Developers see business view of their profile; business users see minimal profile."""
    if username.lower() in _PROFILE_RESERVED:
        return render_template('404.html'), 404
    user = User.query.filter_by(username=username).first_or_404()
    if user.role == 'DEVELOPER':
        profile = user.developer_profile
        if not profile:
            flash('Profile not found.', 'warning')
            return redirect(url_for('main.dashboard'))
        md_html = markdown.markdown(profile.custom_markdown) if profile.custom_markdown else ""
        stack_list = developer_stack_list(profile)
        pinned_projects = profile.pinned_projects
        avg_rating = developer_avg_rating(user.id)
        theme_defaults = developer_profile_theme_defaults(profile)
        is_own = current_user.id == user.id
        if is_own:
            back_url = url_for('main.dashboard')
            back_text = 'Back to Dashboard'
        else:
            back_url = url_for('main.review_gallery') if current_user.role == 'BUSINESS' else url_for('main.developer_listings')
            back_text = 'Back to Your Listings' if current_user.role == 'BUSINESS' else 'Back to Listings'
        return render_template('developer_profile_view.html',
                               title=f'{user.username} - Profile',
                               dev_user=user,
                               profile=profile,
                               md_html=md_html,
                               stack_list=stack_list,
                               pinned_projects=pinned_projects,
                               avg_rating=avg_rating,
                               profile_theme=theme_defaults.get('profile_theme', 'mint'),
                               profile_animation=theme_defaults.get('profile_animation', 'glow'),
                               profile_panel_style=theme_defaults.get('profile_panel_style', 'solid'),
                               profile_background=theme_defaults.get('profile_background', 'default'),
                               back_url=back_url,
                               back_text=back_text,
                               nav_active='listings')
    else:
        return render_template('business_profile_view.html',
                               title=f'{user.username} - Profile',
                               profile_user=user)
