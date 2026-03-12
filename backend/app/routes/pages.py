"""Static pages, dashboard redirect, robots.txt, sitemap."""
from flask import render_template, url_for, redirect, Response
from flask_login import login_required, current_user

from app import db
from app.models import Project, SprintListing, ListingSignup
from app.profile_forms import AddPinnedProjectForm
from app.decorators import require_verified, require_role
from app.utils import (
    sanitize_markdown, developer_stack_list, developer_avg_rating,
    developer_profile_theme_defaults, redirect_after_action,
)
from app.routes import main
from app.routes._helpers import _business_has_card


@main.route('/robots.txt')
def robots_txt():
    return Response(
        'User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /api/\nSitemap: ' + url_for('main.sitemap_xml', _external=True) + '\n',
        mimetype='text/plain',
    )


@main.route('/sitemap.xml')
def sitemap_xml():
    pages = [
        {'url': url_for('main.home', _external=True), 'priority': '1.0'},
        {'url': url_for('main.about', _external=True), 'priority': '0.8'},
        {'url': url_for('main.login', _external=True), 'priority': '0.6'},
        {'url': url_for('main.register', _external=True), 'priority': '0.6'},
    ]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for page in pages:
        xml += f'  <url><loc>{page["url"]}</loc><priority>{page["priority"]}</priority></url>\n'
    xml += '</urlset>'
    return Response(xml, mimetype='application/xml')


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
        md_html = sanitize_markdown(profile.custom_markdown) if profile.custom_markdown else ""
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

@main.route("/reference")
def reference():
    return render_template('reference.html', title='The Team')
