"""Shared route utilities."""
from flask import redirect, url_for, request


def redirect_after_action(default_endpoint='main.home', allow_next=False):
    """
    Redirect after a successful action or denial.
    If allow_next and request.args has 'next', redirect there;
    otherwise default_endpoint.
    """
    if allow_next:
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
    return redirect(url_for(default_endpoint))
