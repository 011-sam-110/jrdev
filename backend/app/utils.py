"""
Shared route and profile utilities.

Provides redirect helpers, URL/text parsing, developer profile helpers,
review deadline helpers, and a single source of truth for profile theme defaults.
"""
import re
from datetime import timedelta
from flask import redirect, url_for, request

REVIEW_DEADLINE_HOURS = 48


def review_deadline_from(submitted_at):
    """Return deadline (UTC) = submitted_at + REVIEW_DEADLINE_HOURS, or None."""
    if submitted_at is None:
        return None
    return submitted_at + timedelta(hours=REVIEW_DEADLINE_HOURS)


# -----------------------------------------------------------------------------
# Redirect helpers
# -----------------------------------------------------------------------------


def redirect_after_action(default_endpoint='main.home', allow_next=False):
    """
    Redirect after a successful action or denial.
    If allow_next and request.args has 'next', redirect there;
    otherwise redirect to default_endpoint.
    """
    if allow_next:
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
    return redirect(url_for(default_endpoint))


# -----------------------------------------------------------------------------
# URL and text parsing
# -----------------------------------------------------------------------------


def normalize_url(val):
    """
    Normalize an optional URL: strip whitespace; if non-empty and no scheme,
    prepend 'https://'. Returns None for empty or whitespace-only input.
    """
    if not val or not str(val).strip():
        return None
    val = str(val).strip()
    if val and not val.startswith(('http://', 'https://')):
        return 'https://' + val
    return val


def youtube_embed_url(url):
    """
    Convert a YouTube watch or youtu.be URL to the embed URL.
    Returns None if url is falsy or no video ID is found.
    """
    if not url:
        return None
    match = re.search(r'(?:v=|youtu\.be/)([\w-]+)', url)
    return f'https://www.youtube.com/embed/{match.group(1)}' if match else None


def parse_comma_separated(s):
    """
    Split a comma-separated string into a list of stripped non-empty strings.
    Returns [] for None or empty input.
    """
    if not s or not str(s).strip():
        return []
    return [t.strip() for t in str(s).split(',') if t.strip()]


# -----------------------------------------------------------------------------
# Developer profile helpers (single source of truth for stack, rating, theme)
# -----------------------------------------------------------------------------


def developer_stack_list(profile):
    """
    Return the developer's technology stack as a list of strings.
    Uses comma-separated parsing. Returns [] if profile or technologies missing.
    """
    if not profile or not getattr(profile, 'technologies', None):
        return []
    return parse_comma_separated(profile.technologies)


def developer_avg_rating(user_id):
    """
    Compute the average business rating of a developer (1–5) from all
    ListingSignups that have a rating. Returns None if no ratings exist.
    """
    from app.models import ListingSignup  # avoid circular import
    rows = ListingSignup.query.filter(
        ListingSignup.user_id == user_id,
        ListingSignup.business_rating_of_developer.isnot(None)
    ).all()
    if not rows:
        return None
    return round(sum(r.business_rating_of_developer for r in rows) / len(rows), 1)


# Default profile theme keys; used by dashboard, profile view, and edit form.
PROFILE_THEME_DEFAULT = 'mint'
PROFILE_ANIMATION_DEFAULT = 'glow'
PROFILE_PANEL_STYLE_DEFAULT = 'solid'
PROFILE_BACKGROUND_DEFAULT = 'default'


def developer_profile_theme_defaults(profile):
    """
    Return a dict of profile theme defaults for templates/forms.
    Keys: profile_theme, profile_animation, profile_panel_style, profile_background.
    Uses getattr(profile, ...) so missing columns do not break.
    """
    return {
        'profile_theme': (
            getattr(profile, 'profile_theme', None) or PROFILE_THEME_DEFAULT
        ),
        'profile_animation': (
            getattr(profile, 'profile_animation', None) or PROFILE_ANIMATION_DEFAULT
        ),
        'profile_panel_style': (
            getattr(profile, 'profile_panel_style', None) or PROFILE_PANEL_STYLE_DEFAULT
        ),
        'profile_background': (
            getattr(profile, 'profile_background', None) or PROFILE_BACKGROUND_DEFAULT
        ),
    }
