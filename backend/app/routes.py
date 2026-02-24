from flask import Blueprint, render_template, url_for, flash, redirect, request, session, jsonify
import os
from werkzeug.utils import secure_filename
from app import db, bcrypt, mail
from app.forms import RegistrationForm, LoginForm
from app.profile_forms import EditProfileForm, EditMarkdownForm, AddPinnedProjectForm
from app.models import User, DeveloperProfile, Project, PinnedProject, SprintListing, ListingSignup
from sqlalchemy.exc import IntegrityError
from app.decorators import require_role
from app.utils import redirect_after_action
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
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
@require_role('BUSINESS')
def review_gallery():
    import re
    my_listings = SprintListing.query.filter_by(business_id=current_user.id).all()
    listing_ids = [l.id for l in my_listings]
    signups = ListingSignup.query.filter(
        ListingSignup.listing_id.in_(listing_ids),
        ListingSignup.status.in_(['accepted', 'pending'])
    ).all() if listing_ids else []

    def youtube_embed(url):
        if not url:
            return None
        m = re.search(r'(?:v=|youtu\.be/)([\w-]+)', url)
        return f'https://www.youtube.com/embed/{m.group(1)}' if m else None

    def dev_avg_rating(user_id):
        rows = ListingSignup.query.filter(
            ListingSignup.user_id == user_id,
            ListingSignup.business_rating_of_developer.isnot(None)
        ).all()
        if not rows:
            return None
        return round(sum(r.business_rating_of_developer for r in rows) / len(rows), 1)

    def make_dev(s, listing):
        return type('Dev', (), {
            'user': s.user,
            'signup': s,
            'demo_video_embed_url': youtube_embed(s.demo_video_url),
            'video_due': listing.sprint_ends_at,
            'rating': dev_avg_rating(s.user_id),
            'github_submission_url': s.github_submission_url,
            'requirements_met': s.requirements_met,
            'prototype_submitted_at': s.prototype_submitted_at,
            'reviewed_at': s.reviewed_at,
            'flagged_for_review': s.flagged_for_review,
            'business_rating_of_developer': s.business_rating_of_developer,
            'developer_rating_of_business': s.developer_rating_of_business,
        })()

    now = datetime.utcnow()
    # Group signups by listing (project)
    listing_to_devs = {}
    for s in signups:
        listing = s.listing
        dev = make_dev(s, listing)
        if listing.id not in listing_to_devs:
            listing_to_devs[listing.id] = []
        listing_to_devs[listing.id].append(dev)

    # Build one entry per sprint (all of the business's listings), with devs and phase
    def phase_for(listing):
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
    projects = Project.query.all()
    return render_template('home.html', projects=projects, title='Home')

@main.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == 'DEVELOPER':
        profile = current_user.developer_profile
        md_html = markdown.markdown(profile.custom_markdown) if profile.custom_markdown else ""
        stack_list = [t.strip() for t in profile.technologies.split(',')] if profile.technologies else []
        form = AddPinnedProjectForm()

        rated = ListingSignup.query.filter(
            ListingSignup.user_id == current_user.id,
            ListingSignup.business_rating_of_developer.isnot(None)
        ).all()
        avg_rating = round(sum(r.business_rating_of_developer for r in rated) / len(rated), 1) if rated else None

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
        return render_template('business_dashboard.html', title='Business Dashboard', nav_active='sprint', my_listings=my_listings)
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
@require_role('DEVELOPER')
def edit_profile():
    form = EditProfileForm()
    profile = current_user.developer_profile
    
    if form.validate_on_submit():
        profile.headline = form.headline.data
        profile.location = form.location.data
        profile.availability = form.availability.data
        profile.technologies = form.technologies.data
        profile.github_link = form.github_link.data
        profile.linkedin_link = form.linkedin_link.data
        profile.portfolio_link = form.portfolio_link.data

        # Handle profile picture upload
        if form.picture.data:
            pic_file = form.picture.data
            filename = secure_filename(pic_file.filename)
            # Ensure unique filename
            _, ext = os.path.splitext(filename)
            filename = f"user_{current_user.id}{ext}"
            # Save to backend/static/profile_pics (not app/static/profile_pics)
            static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'profile_pics'))
            os.makedirs(static_dir, exist_ok=True)
            abs_pic_path = os.path.join(static_dir, filename)
            pic_file.save(abs_pic_path)
            current_user.image_file = filename
        db.session.commit()
        flash('Profile Updated!', 'success')
        return redirect(url_for('main.dashboard'))
    elif request.method == 'GET':
        form.headline.data = profile.headline
        form.location.data = profile.location
        form.availability.data = profile.availability
        form.technologies.data = profile.technologies
        form.github_link.data = profile.github_link
        form.linkedin_link.data = profile.linkedin_link
        form.portfolio_link.data = profile.portfolio_link
        
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@main.route("/update-markdown", methods=['POST'])
@login_required
@require_role('DEVELOPER', json_response=True)
def update_markdown():
    content = request.form.get('content')
    profile = current_user.developer_profile
    profile.custom_markdown = content
    db.session.commit()
    return redirect(url_for('main.dashboard'))

@main.route("/add-pinned-project", methods=['POST'])
@login_required
@require_role('DEVELOPER')
def add_pinned_project():
    title = request.form.get('title')
    desc = request.form.get('description')
    tags = request.form.get('tags')
    link = request.form.get('link')
    
    if title and desc:
        project = PinnedProject(
            profile_id=current_user.developer_profile.id,
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

@main.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect_after_action()
    form = RegistrationForm()
    
    # Pre-select role if provided in query params
    if request.method == 'GET':
        role = request.args.get('role')
        if role in ['DEVELOPER', 'BUSINESS']:
            form.role.data = role
            
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        totp_secret = pyotp.random_base32()
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, role=form.role.data, two_factor_secret=totp_secret)
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
        login_user(user)
        return redirect(url_for('main.setup_2fa'))
    return render_template('register.html', title='Register', form=form)

@main.route("/setup-2fa", methods=['GET', 'POST'])
@login_required
def setup_2fa():
    user = current_user
    
    # Generate URI for QR Code
    totp_uri = user.get_totp_uri()
    
    if request.method == 'POST':
        token = request.form.get('token')
        if user.verify_totp(token):
            # 2FA Verified
            # Now simulate email verification sending
            # In production: msg = Message(...); mail.send(msg)
            # For demo, we mark as verified for now or print token
            
            user.is_verified = True 
            db.session.commit()
            
            flash('2FA Setup Complete! Your account is secure.', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid Code. Please try again.', 'danger')
            
    # Generate QR Code Image
    img = qrcode.make(totp_uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_code = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return render_template('setup_2fa.html', qr_code=qr_code)

@main.route("/skip-2fa")
@login_required
def skip_2fa():
    current_user.is_verified = True
    db.session.commit()
    flash('2FA skipped. You can set it up later from account settings.', 'info')
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
            # 2FA is disabled for now; log in directly
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@main.route("/logout")
def logout():
    logout_user()
    return redirect_after_action()

@main.route("/account")
@login_required
def account():
    nav_active = 'account'
    return render_template('account.html', title='Account', nav_active=nav_active)

# ── Billing (Stripe) – BUSINESS only ──

def _stripe_available():
    return stripe is not None and os.environ.get('STRIPE_SECRET_KEY')

def _get_stripe_customer():
    """Get or create Stripe customer for current business user."""
    if not _stripe_available() or current_user.role != 'BUSINESS':
        return None
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    if current_user.stripe_customer_id:
        try:
            return stripe.Customer.retrieve(current_user.stripe_customer_id)
        except stripe.error.InvalidRequestError:
            current_user.stripe_customer_id = None
            db.session.commit()
    # Create new customer
    customer = stripe.Customer.create(
        email=current_user.email,
        name=current_user.username,
    )
    current_user.stripe_customer_id = customer.id
    db.session.commit()
    return customer

@main.route("/billing")
@login_required
@require_role('BUSINESS')
def billing():
    stripe_publishable_key = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
    card_last4 = None
    card_brand = None
    if _stripe_available() and current_user.stripe_customer_id:
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
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

@main.route("/billing/create-setup-intent", methods=['POST'])
@login_required
@require_role('BUSINESS')
def billing_create_setup_intent():
    if not _stripe_available():
        return jsonify({'error': 'Stripe is not configured'}), 503
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    customer = _get_stripe_customer()
    if not customer:
        return jsonify({'error': 'Could not create customer'}), 500
    try:
        intent = stripe.SetupIntent.create(
            customer=customer.id,
            payment_method_types=['card'],
            usage='off_session',
        )
        return jsonify({'client_secret': intent.client_secret})
    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400

@main.route("/developer/listings")
@login_required
@require_role('DEVELOPER')
def developer_listings():
    all_listings = SprintListing.query.filter_by(status='open').order_by(SprintListing.created_at.desc()).all()
    joined_listing_ids = {s.listing_id for s in ListingSignup.query.filter_by(user_id=current_user.id).all()}
    listings = [l for l in all_listings if l.id not in joined_listing_ids]
    form = AddPinnedProjectForm()
    return render_template('developer_listings.html', title='Available Listings', nav_active='listings', listings=listings, form=form)

@main.route("/developer/joined")
@login_required
@require_role('DEVELOPER')
def developer_joined_listings():
    signups = ListingSignup.query.filter_by(user_id=current_user.id).order_by(ListingSignup.joined_at.desc()).all()
    form = AddPinnedProjectForm()
    return render_template('developer_joined_listings.html', title='Joined Listings', nav_active='joined', signups=signups, form=form)

@main.route("/business/listings")
@login_required
@require_role('BUSINESS')
def business_my_listings():
    my_listings = SprintListing.query.filter_by(business_id=current_user.id).order_by(SprintListing.created_at.desc()).all()
    form = AddPinnedProjectForm()
    return render_template('business_my_listings.html', title='My Listings', nav_active='listings', my_listings=my_listings, form=form)

# ── Sprint Launch ──

@main.route("/launch-sprint", methods=['POST'])
@login_required
@require_role('BUSINESS')
def launch_sprint():
    company_name = request.form.get('company_name', '').strip()
    if not company_name:
        company_name = current_user.username + "'s Sprint"

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

    listing = SprintListing(
        business_id=current_user.id,
        company_name=company_name,
        max_talent_pool=int(request.form.get('max_talent_pool', 3)),
        pay_for_prototype=float(request.form.get('pay_for_prototype', 60)),
        technologies_required=request.form.get('technologies_required', ''),
        deliverables=(request.form.get('deliverables') or '').strip() or None,
        sprint_timeline_days=int(request.form.get('sprint_timeline_days', 7)),
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
    db.session.commit()
    flash('You have joined the sprint! Waiting for business approval.', 'success')
    return redirect(url_for('main.developer_joined_listings'))

# ── Business accepts / denies developer ──

@main.route("/signup/<int:id>/accept", methods=['POST'])
@login_required
@require_role('BUSINESS')
def signup_accept(id):
    signup = ListingSignup.query.get_or_404(id)
    if signup.listing.business_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.review_gallery'))
    signup.status = 'accepted'
    db.session.commit()
    flash(f'{signup.user.username} accepted.', 'success')
    return redirect(url_for('main.review_gallery'))

@main.route("/signup/<int:id>/deny", methods=['POST'])
@login_required
@require_role('BUSINESS')
def signup_deny(id):
    signup = ListingSignup.query.get_or_404(id)
    if signup.listing.business_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.review_gallery'))
    signup.status = 'denied'
    db.session.commit()
    flash(f'{signup.user.username} denied.', 'info')
    return redirect(url_for('main.review_gallery'))

# ── E-signing ──

@main.route("/signup/<int:id>/sign/developer", methods=['POST'])
@login_required
@require_role('DEVELOPER')
def signup_sign_developer(id):
    signup = ListingSignup.query.get_or_404(id)
    if signup.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.developer_joined_listings'))
    signup.developer_signed_at = datetime.utcnow()
    db.session.commit()
    flash('Contract signed by you. Waiting for business countersign.', 'success')
    return redirect(url_for('main.developer_joined_listings'))

@main.route("/signup/<int:id>/sign/business", methods=['POST'])
@login_required
@require_role('BUSINESS')
def signup_sign_business(id):
    signup = ListingSignup.query.get_or_404(id)
    if signup.listing.business_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.review_gallery'))
    signup.business_signed_at = datetime.utcnow()
    db.session.commit()
    flash('Contract countersigned. Sprint is now active!', 'success')
    return redirect(url_for('main.review_gallery'))

# ── Developer cancels signup ──

@main.route("/signup/<int:id>/cancel", methods=['POST'])
@login_required
@require_role('DEVELOPER')
def signup_cancel(id):
    signup = ListingSignup.query.get_or_404(id)
    if signup.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.developer_joined_listings'))
    signup.status = 'cancelled'
    db.session.commit()
    flash('You have withdrawn from this listing.', 'info')
    return redirect(url_for('main.developer_joined_listings'))

# ── Developer submits deliverables ──

@main.route("/signup/<int:id>/submit", methods=['POST'])
@login_required
@require_role('DEVELOPER')
def signup_submit_deliverables(id):
    signup = ListingSignup.query.get_or_404(id)
    if signup.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.developer_joined_listings'))
    signup.github_submission_url = request.form.get('github_submission_url', '').strip() or None
    signup.demo_video_url = request.form.get('demo_video_url', '').strip() or None
    reqs = request.form.getlist('requirements_met')
    signup.requirements_met = ', '.join(reqs) if reqs else None
    signup.prototype_submitted_at = datetime.utcnow()
    db.session.commit()
    flash('Prototype submitted! The business will review your work.', 'success')
    return redirect(url_for('main.developer_joined_listings'))

# ── Business reviews developer submissions ──

@main.route("/signup/<int:id>/mark-reviewed", methods=['POST'])
@login_required
@require_role('BUSINESS')
def signup_mark_reviewed(id):
    signup = ListingSignup.query.get_or_404(id)
    if signup.listing.business_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.review_gallery'))
    signup.reviewed_at = datetime.utcnow()
    profile = signup.user.developer_profile
    if profile:
        profile.prototypes_completed = (profile.prototypes_completed or 0) + 1
        profile.contracts_won = (profile.contracts_won or 0) + 1

        sprint_techs = [t.strip() for t in (signup.listing.technologies_required or '').split(',') if t.strip()]
        if sprint_techs:
            existing = {}
            for entry in (profile.technologies or '').split(','):
                entry = entry.strip()
                if not entry:
                    continue
                if '+' in entry:
                    parts = entry.rsplit('+', 1)
                    existing[parts[0].strip().lower()] = {'name': parts[0].strip(), 'count': int(parts[1])}
                else:
                    existing[entry.lower()] = {'name': entry, 'count': 1}
            for tech in sprint_techs:
                key = tech.lower()
                if key in existing:
                    existing[key]['count'] += 1
                else:
                    existing[key] = {'name': tech, 'count': 1}
            updated = []
            for info in existing.values():
                if info['count'] > 1:
                    updated.append(f"{info['name']}+{info['count']}")
                else:
                    updated.append(info['name'])
            profile.technologies = ','.join(updated)
    db.session.commit()
    flash(f'Marked as reviewed. You have been charged £{signup.listing.pay_for_prototype:.0f} for this developer.', 'success')
    return redirect(url_for('main.review_gallery'))

@main.route("/signup/<int:id>/flag", methods=['POST'])
@login_required
@require_role('BUSINESS')
def signup_flag_for_review(id):
    signup = ListingSignup.query.get_or_404(id)
    if signup.listing.business_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.review_gallery'))
    signup.flagged_for_review = True
    db.session.commit()
    flash('Flagged for review. Our team will contact you and the developer to resolve. No charge will be made until the sprint is marked complete.', 'info')
    return redirect(url_for('main.review_gallery'))

@main.route("/signup/<int:id>/unflag", methods=['POST'])
@login_required
@require_role('BUSINESS')
def signup_unflag(id):
    signup = ListingSignup.query.get_or_404(id)
    if signup.listing.business_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.review_gallery'))
    signup.flagged_for_review = False
    db.session.commit()
    flash('Removed flag.', 'info')
    return redirect(url_for('main.review_gallery'))

@main.route("/signup/<int:id>/rate-developer", methods=['POST'])
@login_required
@require_role('BUSINESS')
def signup_rate_developer(id):
    signup = ListingSignup.query.get_or_404(id)
    if signup.listing.business_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.review_gallery'))
    try:
        rating = int(request.form.get('rating', 0))
        if 1 <= rating <= 5:
            signup.business_rating_of_developer = rating
            db.session.commit()
            flash(f'Rated {signup.user.username} {rating}/5 stars.', 'success')
        else:
            flash('Rating must be between 1 and 5.', 'warning')
    except (TypeError, ValueError):
        flash('Invalid rating.', 'warning')
    return redirect(url_for('main.review_gallery'))

@main.route("/signup/<int:id>/rate-business", methods=['POST'])
@login_required
@require_role('DEVELOPER')
def signup_rate_business(id):
    signup = ListingSignup.query.get_or_404(id)
    if signup.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.developer_joined_listings'))
    try:
        rating = int(request.form.get('rating', 0))
        if 1 <= rating <= 5:
            signup.developer_rating_of_business = rating
            db.session.commit()
            flash(f'Rated {signup.listing.company_name} {rating}/5 stars.', 'success')
        else:
            flash('Rating must be between 1 and 5.', 'warning')
    except (TypeError, ValueError):
        flash('Invalid rating.', 'warning')
    return redirect(url_for('main.developer_joined_listings'))

@main.route("/signup/<int:id>/cannot-complete", methods=['POST'])
@login_required
@require_role('DEVELOPER')
def signup_cannot_complete(id):
    signup = ListingSignup.query.get_or_404(id)
    if signup.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.developer_joined_listings'))
    signup.developer_withdrew = True
    db.session.commit()
    flash('You have indicated you cannot complete this project. The business has been notified.', 'info')
    return redirect(url_for('main.developer_joined_listings'))

# ── Developer public profile view (for businesses) ──

@main.route("/developer/<int:user_id>")
@login_required
@require_role('BUSINESS')
def developer_profile_view(user_id):
    dev_user = User.query.get_or_404(user_id)
    if dev_user.role != 'DEVELOPER':
        flash('User is not a developer.', 'warning')
        return redirect(url_for('main.business_my_listings'))
    profile = dev_user.developer_profile
    md_html = markdown.markdown(profile.custom_markdown) if profile and profile.custom_markdown else ""
    stack_list = [t.strip() for t in profile.technologies.split(',')] if profile and profile.technologies else []
    pinned_projects = profile.pinned_projects if profile else []

    rated = ListingSignup.query.filter(
        ListingSignup.user_id == dev_user.id,
        ListingSignup.business_rating_of_developer.isnot(None)
    ).all()
    avg_rating = round(sum(r.business_rating_of_developer for r in rated) / len(rated), 1) if rated else None

    return render_template('developer_profile_view.html',
                           title=f'{dev_user.username} - Profile',
                           dev_user=dev_user,
                           profile=profile,
                           md_html=md_html,
                           stack_list=stack_list,
                           pinned_projects=pinned_projects,
                           avg_rating=avg_rating,
                           nav_active='listings')
