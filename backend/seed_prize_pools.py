"""
Seed script for prize pools. Creates 1-2 sample paid pools for development/testing.

Run from backend/: python seed_prize_pools.py
"""
from datetime import datetime, timedelta, timezone, timezone
from app import create_app, db
from app.models import PrizePool, User

app = create_app()

with app.app_context():
    if PrizePool.query.first():
        print("Prize pools already exist. Skipping seed.")
    else:
        # Get first user as creator (or None)
        creator = User.query.first()
        now = datetime.now(timezone.utc)
        signup_ends = now + timedelta(days=7)
        submission_ends = now + timedelta(days=14)
        voting_ends = now + timedelta(days=21)

        pool1 = PrizePool(
            title="March 2025 Build Challenge",
            description="Build a **simple web app** that demonstrates your full-stack skills. Submit a YouTube demo and GitHub repo.",
            technologies_required="React, Python, Flask",
            pool_type="paid",
            entry_fee_gbp=10.0,
            signup_ends_at=signup_ends,
            submission_ends_at=submission_ends,
            voting_ends_at=voting_ends,
            max_participants=None,
            status="open",
            created_by_id=creator.id if creator else None,
        )
        db.session.add(pool1)

        pool2 = PrizePool(
            title="API Integration Sprint",
            description="Create an API integration (e.g. Stripe, Twilio, or any public API). Show working demo.",
            technologies_required="REST, JavaScript, Node or Python",
            pool_type="paid",
            entry_fee_gbp=5.0,
            signup_ends_at=signup_ends,
            submission_ends_at=submission_ends,
            voting_ends_at=voting_ends,
            max_participants=20,
            status="open",
            created_by_id=creator.id if creator else None,
        )
        db.session.add(pool2)

        db.session.commit()
        print("Created 2 prize pools: March 2025 Build Challenge, API Integration Sprint.")
