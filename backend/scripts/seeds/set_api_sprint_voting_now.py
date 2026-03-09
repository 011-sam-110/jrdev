"""
One-off script: set "API Integration Sprint" prize pool so voting begins now.
- Sets submission_ends_at to now (so submission period is over).
- Sets status to 'voting' so the pool is immediately in voting phase.

Run from backend/: python set_api_sprint_voting_now.py
"""
import os
import sys
from datetime import datetime, timezone

# Load .env from project root
try:
    from dotenv import load_dotenv
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(root_dir, '.env'))
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import create_app, db
from app.models import PrizePool

def main():
    app = create_app()
    with app.app_context():
        pool = PrizePool.query.filter(PrizePool.title.ilike('%API Integration Sprint%')).first()
        if not pool:
            print('No prize pool found with title containing "API Integration Sprint".')
            return 1
        now = datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC for DB
        pool.submission_ends_at = now
        pool.status = 'voting'
        db.session.commit()
        print(f'Updated "{pool.title}" (id={pool.id}): submission_ends_at -> now, status -> voting.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
