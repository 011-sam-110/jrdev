"""
Seed script for testing the prize pool pairwise review flow.

Creates fake developer accounts with pre-filled submissions so you can log into
each account and complete the rating process without multiple real users.

Run from backend/: python seed_review_test.py

Credentials after seeding (dev1@test.dev .. dev5@test.dev, password Test1234!):
  dev1@test.dev, dev2@test.dev, ... dev5@test.dev
  Password: Test1234!
"""

from datetime import datetime, timedelta, timezone
from app import create_app, db, bcrypt
from app.models import User, DeveloperProfile, PrizePool, PrizePoolEntry

DEFAULT_PASSWORD = "Test1234!"
DEMO_VIDEO_URL = "https://www.youtube.com/watch?v=ujdFPoCeFM4"
NUM_DEVS = 5


def seed():
    app = create_app()
    with app.app_context():
        now = datetime.now(timezone.utc)
        hashed_pw = bcrypt.generate_password_hash(DEFAULT_PASSWORD).decode("utf-8")
        created_users = 0
        created_entries = 0

        # 1. Create developer users
        dev_users = []
        for i in range(1, NUM_DEVS + 1):
            username = f"dev{i}"
            email = f"dev{i}@test.dev"
            if User.query.filter_by(email=email).first():
                user = User.query.filter_by(email=email).first()
                dev_users.append(user)
                continue
            user = User(
                username=username,
                email=email,
                password=hashed_pw,
                role="DEVELOPER",
                is_verified=True,
            )
            db.session.add(user)
            db.session.flush()
            if not DeveloperProfile.query.filter_by(user_id=user.id).first():
                profile = DeveloperProfile(
                    user_id=user.id,
                    headline="Test Developer " + str(i),
                    bio="Fake account for testing prize pool reviews.",
                    technologies="Python, JavaScript, React",
                )
                db.session.add(profile)
            dev_users.append(user)
            created_users += 1

        db.session.commit()

        # 2. Get or create a free prize pool in voting status
        pool = PrizePool.query.filter_by(pool_type="free").first()
        if not pool:
            creator = User.query.first()
            signup_ends = now + timedelta(days=7)
            # Past so we can set voting
            submission_ends = now - timedelta(days=1)
            voting_ends = now + timedelta(days=7)
            pool = PrizePool(
                title="Review Test Pool",
                description="Free pool for testing the pairwise review flow.",
                technologies_required="Any",
                pool_type="free",
                entry_fee_pence=None,
                signup_ends_at=signup_ends,
                submission_ends_at=submission_ends,
                voting_ends_at=voting_ends,
                max_participants=None,
                status="voting",
                created_by_id=creator.id if creator else None,
            )
            db.session.add(pool)
            db.session.commit()
            print("Created free pool 'Review Test Pool' (status=voting).")
        else:
            pool.status = "voting"
            if not pool.voting_ends_at:
                pool.voting_ends_at = now + timedelta(days=7)
            db.session.commit()
            print("Using existing free pool '%s' (set status=voting)." % pool.title)

        # 3. Create entries with pre-filled submissions for each dev
        for user in dev_users:
            existing = PrizePoolEntry.query.filter_by(
                prize_pool_id=pool.id, user_id=user.id
            ).first()
            if existing:
                if not existing.submitted_at:
                    existing.demo_video_url = DEMO_VIDEO_URL
                    existing.github_submission_url = "https://github.com"
                    existing.submitted_at = now
                    pc = existing.payment_completed_at or now
                    existing.payment_completed_at = pc
                    db.session.commit()
                    created_entries += 1
                continue
            entry = PrizePoolEntry(
                prize_pool_id=pool.id,
                user_id=user.id,
                payment_completed_at=now,
                demo_video_url=DEMO_VIDEO_URL,
                github_submission_url="https://github.com",
                submitted_at=now,
            )
            db.session.add(entry)
            created_entries += 1

        db.session.commit()

        print("\nSeed complete. Created %d users, %d entries." % (created_users, created_entries))
        print("Login: dev1@test.dev .. dev5@test.dev, password Test1234!")
        print("Go to Your Listings -> Vote on submissions to test.\n")


if __name__ == "__main__":
    seed()
