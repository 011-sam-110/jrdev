"""
Seed script for prize pools. Creates sample paid and free pools for development/testing.

Run from backend/: python seed_prize_pools.py
"""
from datetime import datetime, timedelta, timezone
from app import create_app, db
from app.models import PrizePool, User

app = create_app()

with app.app_context():
    creator = User.query.first()
    now = datetime.now(timezone.utc)
    signup_ends = now + timedelta(days=7)
    submission_ends = now + timedelta(days=14)
    voting_ends = now + timedelta(days=21)

    # Add paid pools only if none exist
    if not PrizePool.query.filter_by(pool_type='paid').first():
        pool1 = PrizePool(
            title="March 2025 Build Challenge",
            description="Build a **simple web app** that demonstrates your full-stack skills. Submit a YouTube demo and GitHub repo.",
            technologies_required="React, Python, Flask",
            pool_type="paid",
            entry_fee_pence=1000,
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
            entry_fee_pence=500,
            signup_ends_at=signup_ends,
            submission_ends_at=submission_ends,
            voting_ends_at=voting_ends,
            max_participants=20,
            status="open",
            created_by_id=creator.id if creator else None,
        )
        db.session.add(pool2)
        print("Created 2 paid prize pools.")

    # Add free pools only if none exist (voting_ends_at set so "Voting ends" shows on listings)
    if not PrizePool.query.filter_by(pool_type='free').first():
        free1 = PrizePool(
            title="Portfolio Project Challenge",
            description="Build a **portfolio project** to showcase your skills. No entry fee—just submit a GitHub repo and short demo video. Great for building your CV.",
            technologies_required="Any",
            pool_type="free",
            entry_fee_pence=None,
            signup_ends_at=signup_ends,
            submission_ends_at=submission_ends,
            voting_ends_at=voting_ends,
            max_participants=None,
            status="open",
            created_by_id=creator.id if creator else None,
        )
        db.session.add(free1)

        free2 = PrizePool(
            title="First PR Challenge",
            description="Make your first open-source contribution. Submit a link to a merged PR on any public repo. Perfect for beginners.",
            technologies_required="Git, Any language",
            pool_type="free",
            entry_fee_pence=None,
            signup_ends_at=signup_ends,
            submission_ends_at=submission_ends,
            voting_ends_at=voting_ends,
            max_participants=50,
            status="open",
            created_by_id=creator.id if creator else None,
        )
        db.session.add(free2)

        free3 = PrizePool(
            title="Mini App Sprint",
            description="Build a **small utility app** (calculator, todo list, timer, etc.) in under 2 hours. Focus on clean code and a working demo.",
            technologies_required="HTML, CSS, JavaScript",
            pool_type="free",
            entry_fee_pence=None,
            signup_ends_at=signup_ends,
            submission_ends_at=submission_ends,
            voting_ends_at=voting_ends,
            max_participants=None,
            status="open",
            created_by_id=creator.id if creator else None,
        )
        db.session.add(free3)
        print("Created 3 free prize pools.")

    db.session.commit()
    print("Seed complete.")
