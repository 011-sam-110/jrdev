"""
Routes package: splits the main blueprint across domain-specific modules.

Each sub-module imports `main` from here and registers routes on it.
The blueprint name stays 'main' so all url_for('main.xxx') calls in
templates continue to work without changes.
"""
from flask import Blueprint

main = Blueprint('main', __name__)

# _legacy contains the full monolithic routes.py until the sub-module split
# is completed (auth, billing, profile, listings, prize_pools).
# pages.py and future modules are progressively extracted from _legacy.
from app.routes import _legacy   # noqa: F401, E402

# Expose helpers that app/__init__.py CLI commands import
from app.routes._legacy import process_review_deadlines   # noqa: F401, E402
from app.routes._legacy import process_prize_pool_winners  # noqa: F401, E402
from app.routes._legacy import process_signing_deadlines   # noqa: F401, E402
