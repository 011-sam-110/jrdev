"""
Seed script — generates fake business accounts and sprint listings.
Run from the project root:  python fillListings.py

Options:
  python fillListings.py              — seed multiple fake businesses (legacy).
  python fillListings.py --reconfigure — drop DB tables, recreate, then create one user
                                         Test1234! (password Test1234!) with many listings.
"""

import sys, os, random, argparse
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app import create_app, db, bcrypt
from app.models import User, SprintListing

# ---------------------------------------------------------------------------
# Data pools
# ---------------------------------------------------------------------------

COMPANY_NAMES = [
    "NovaByte Labs", "Stratosphere AI", "Pinecone Digital", "Velox Systems",
    "Quantum Forge", "Helix Cloud", "Arcturus Tech", "BlueShift Studios",
    "TerraStack", "Nimbus Works", "ClearEdge Software", "Ironclad Data",
    "Pulse Analytics", "Verdant Logic", "SkyLoom", "CypherGrid",
    "BrightPath AI", "Cobalt Robotics", "ZenithWare", "Orion Platform",
]

TECH_POOL = [
    "Python", "JavaScript", "TypeScript", "React", "Next.js", "Vue.js",
    "Angular", "Node.js", "Express", "Flask", "Django", "FastAPI",
    "PostgreSQL", "MongoDB", "Redis", "Docker", "Kubernetes", "AWS",
    "GCP", "Tailwind CSS", "GraphQL", "Rust", "Go", "Swift",
    "Flutter", "Firebase", "Supabase", "Prisma", "SQLAlchemy", "Celery",
]

DELIVERABLE_TEMPLATES = [
    [
        "Build a responsive landing page with hero section",
        "Implement user sign-up and login flow",
        "Connect front-end to REST API",
        "Write unit tests for auth endpoints",
    ],
    [
        "Design database schema for multi-tenant SaaS",
        "Create CRUD API for tenant resources",
        "Add role-based access control middleware",
        "Deploy staging environment with Docker Compose",
    ],
    [
        "Prototype real-time chat using WebSockets",
        "Implement message persistence with PostgreSQL",
        "Add typing indicators and read receipts",
        "Write integration tests for the chat service",
    ],
    [
        "Build a dashboard with chart visualizations",
        "Integrate third-party analytics API",
        "Implement CSV / PDF export functionality",
        "Add date-range filter and caching layer",
    ],
    [
        "Create a CLI tool for data migration",
        "Parse and validate CSV / JSON input files",
        "Generate a migration summary report",
        "Handle rollback on partial failure",
    ],
    [
        "Build an image upload microservice",
        "Add automatic thumbnail generation",
        "Integrate cloud storage (S3 / GCS)",
        "Implement signed-URL access control",
    ],
    [
        "Set up CI/CD pipeline with GitHub Actions",
        "Write Dockerfile and docker-compose config",
        "Add automated linting and test stages",
        "Configure staging and production deploy targets",
    ],
    [
        "Build REST API for an e-commerce product catalog",
        "Implement search with filters and pagination",
        "Add shopping cart session management",
        "Write Swagger / OpenAPI documentation",
    ],
    [
        "Prototype a recommendation engine",
        "Collect and preprocess user interaction data",
        "Train a collaborative-filtering model",
        "Expose predictions via a FastAPI endpoint",
    ],
    [
        "Create a Slack bot for team standup reminders",
        "Store standup responses in a database",
        "Generate weekly summary reports",
        "Add slash-command configuration interface",
    ],
    [
        "Build a Kanban board with drag-and-drop",
        "Implement real-time sync across clients",
        "Add labels, due dates, and assignees",
        "Write end-to-end tests with Playwright",
    ],
    [
        "Develop a URL shortener service",
        "Track click analytics per link",
        "Add custom alias and expiration support",
        "Build a minimal analytics dashboard",
    ],
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _random_techs(min_n=2, max_n=5):
    return ",".join(random.sample(TECH_POOL, random.randint(min_n, max_n)))


def _random_deliverables():
    base = random.choice(DELIVERABLE_TEMPLATES)
    subset = base if random.random() > 0.3 else random.sample(base, k=random.randint(2, len(base)))
    return "\n".join(subset)


def _random_deliverables_with_essential():
    """Return (essential_newline, optional_newline) for essential_deliverables and deliverables."""
    base = random.choice(DELIVERABLE_TEMPLATES)
    subset = base if random.random() > 0.3 else random.sample(base, k=random.randint(2, len(base)))
    n = len(subset)
    num_essential = min(random.randint(1, max(1, n - 1)), n)
    essential_lines = subset[:num_essential]
    optional_lines = subset[num_essential:]
    return "\n".join(essential_lines), "\n".join(optional_lines) if optional_lines else ""


def _future_dt(days_min, days_max):
    return datetime.now(timezone.utc) + timedelta(
        days=random.randint(days_min, days_max),
        hours=random.randint(0, 12),
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

DEFAULT_PASSWORD = "Test1234!"
TEST_USERNAME = "Test1234!"
NUM_BUSINESSES = 10
LISTINGS_PER_BUSINESS = (1, 3)
LISTINGS_FOR_TEST_USER = 20  # when using --reconfigure


def _add_listing(user, company_name, **kwargs):
    signup_ends = _future_dt(2, 10)
    sprint_begins = signup_ends + timedelta(days=random.randint(1, 3))
    sprint_days = random.choice([5, 7, 10, 14])
    sprint_ends = sprint_begins + timedelta(days=sprint_days)
    essential, optional = _random_deliverables_with_essential()
    num_essential = len([x for x in essential.split("\n") if x.strip()])
    num_optional = len([x for x in optional.split("\n") if x.strip()])
    num_total = num_essential + num_optional
    listing = SprintListing(
        business_id=user.id,
        company_name=company_name,
        max_talent_pool=random.choice([3, 5, 8, 10]),
        pay_for_prototype=random.choice([20, 35, 50, 75, 100, 150]),
        technologies_required=_random_techs(),
        essential_deliverables=essential or None,
        essential_deliverables_count=num_essential,
        deliverables=optional or None,
        sprint_timeline_days=sprint_days,
        signup_ends_at=signup_ends,
        sprint_begins_at=sprint_begins,
        sprint_ends_at=sprint_ends,
        minimum_requirements_for_pay=max(1, num_total - 1),
        status="open",
        **kwargs,
    )
    db.session.add(listing)
    return listing


def seed_test_user():
    """Recreate DB and seed one business user Test1234! with many listings."""
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("  Database reconfigured (tables dropped and recreated).")
        hashed_pw = bcrypt.generate_password_hash(DEFAULT_PASSWORD).decode("utf-8")
        company = random.choice(COMPANY_NAMES)
        user = User(
            username=TEST_USERNAME,
            email=f"{TEST_USERNAME.lower().replace('!', '')}@test.dev",
            password=hashed_pw,
            role="BUSINESS",
            is_verified=True,
        )
        db.session.add(user)
        db.session.flush()
        for _ in range(LISTINGS_FOR_TEST_USER):
            _add_listing(user, company)
        db.session.commit()
        print(f"  Created user: {TEST_USERNAME} with {LISTINGS_FOR_TEST_USER} listings.")
        print(f"  Login: username {TEST_USERNAME}, password {DEFAULT_PASSWORD}\n")


def seed():
    """Legacy: seed multiple fake businesses with a few listings each."""
    app = create_app()
    with app.app_context():
        hashed_pw = bcrypt.generate_password_hash(DEFAULT_PASSWORD).decode("utf-8")
        created_users = 0
        created_listings = 0

        for i in range(NUM_BUSINESSES):
            company = COMPANY_NAMES[i % len(COMPANY_NAMES)]
            slug = company.lower().replace(" ", "")
            username = slug[:20]
            email = f"{slug}@fakebiz.dev"

            if User.query.filter_by(email=email).first():
                print(f"  SKIP  {username} (already exists)")
                continue

            user = User(
                username=username,
                email=email,
                password=hashed_pw,
                role="BUSINESS",
                is_verified=True,
            )
            db.session.add(user)
            db.session.flush()
            created_users += 1

            num_listings = random.randint(*LISTINGS_PER_BUSINESS)
            for _ in range(num_listings):
                deliverables = _random_deliverables()
                num_deliverables = len([d for d in deliverables.split("\n") if d.strip()])
                signup_ends = _future_dt(2, 10)
                sprint_begins = signup_ends + timedelta(days=random.randint(1, 3))
                sprint_days = random.choice([5, 7, 10, 14])
                sprint_ends = sprint_begins + timedelta(days=sprint_days)
                listing = SprintListing(
                    business_id=user.id,
                    company_name=company,
                    max_talent_pool=random.choice([3, 5, 8, 10]),
                    pay_for_prototype=random.choice([20, 35, 50, 75, 100, 150]),
                    technologies_required=_random_techs(),
                    deliverables=deliverables,
                    sprint_timeline_days=sprint_days,
                    signup_ends_at=signup_ends,
                    sprint_begins_at=sprint_begins,
                    sprint_ends_at=sprint_ends,
                    minimum_requirements_for_pay=max(1, num_deliverables - 1),
                    status="open",
                )
                db.session.add(listing)
                created_listings += 1

        db.session.commit()
        print(f"\n  Done — {created_users} businesses, {created_listings} listings created.")
        print(f"  Login with any fake email (e.g. novabytelabs@fakebiz.dev)")
        print(f"  Password for all accounts: {DEFAULT_PASSWORD}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed sprint listings and optional test user.")
    parser.add_argument("--reconfigure", action="store_true", help="Drop DB, recreate tables, seed user Test1234! with many listings.")
    args = parser.parse_args()
    if args.reconfigure:
        seed_test_user()
    else:
        seed()
