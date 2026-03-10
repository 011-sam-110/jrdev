"""
Seed script: creates a test business user, a test developer user, a sprint listing,
and a developer signup (join) for that listing.

Run: cd backend && python seed_sprint.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import User, DeveloperProfile, SprintListing, ListingSignup
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta

app = create_app()
bcrypt = Bcrypt(app)

with app.app_context():
    # --- Business user ---
    biz = User.query.filter_by(email='testbusiness@jrdev.io').first()
    if not biz:
        biz = User(
            username='TestBusiness',
            email='testbusiness@jrdev.io',
            password=bcrypt.generate_password_hash('Password123!').decode('utf-8'),
            role='BUSINESS',
            is_verified=True,
            registered_address='1 Business Lane, London, UK',
        )
        db.session.add(biz)
        db.session.flush()
        print(f'Created business user: {biz.email}')
    else:
        print(f'Business user already exists: {biz.email}')

    # --- Developer user ---
    dev = User.query.filter_by(email='testdev@jrdev.io').first()
    if not dev:
        dev = User(
            username='TestDev',
            email='testdev@jrdev.io',
            password=bcrypt.generate_password_hash('Password123!').decode('utf-8'),
            role='DEVELOPER',
            is_verified=True,
            registered_address='42 Dev Street, Manchester, UK',
        )
        db.session.add(dev)
        db.session.flush()
        profile = DeveloperProfile(
            user_id=dev.id,
            headline='Full-Stack Developer',
            bio='Passionate about building fast, useful prototypes.',
            location='Manchester, UK',
            availability='Open to Work',
            technologies='Python, Flask, React, TypeScript',
            contracts_attempted=0,
            contracts_won=0,
            prototypes_completed=0,
        )
        db.session.add(profile)
        print(f'Created developer user: {dev.email}')
    else:
        print(f'Developer user already exists: {dev.email}')

    db.session.commit()

    # --- Sprint listing ---
    listing = SprintListing.query.filter_by(
        business_id=biz.id, company_name='TestBusiness Sprint'
    ).first()
    if not listing:
        now = datetime.utcnow()
        listing = SprintListing(
            business_id=biz.id,
            company_name='TestBusiness Sprint',
            company_address='1 Business Lane, London, UK',
            max_talent_pool=3,
            pay_for_prototype=100.0,
            technologies_required='Python, Flask, React',
            deliverables='User authentication\nDashboard UI\nREST API',
            essential_deliverables='User authentication',
            essential_deliverables_count=1,
            sprint_timeline_days=7,
            signup_ends_at=now + timedelta(days=2),
            sprint_begins_at=now + timedelta(days=2),
            sprint_ends_at=now + timedelta(days=9),
            minimum_requirements_for_pay=2,
            status='open',
        )
        db.session.add(listing)
        db.session.flush()
        print(f'Created sprint listing id={listing.id}')
    else:
        print(f'Sprint listing already exists id={listing.id}')

    # --- Developer joins the sprint ---
    signup = ListingSignup.query.filter_by(
        listing_id=listing.id, user_id=dev.id
    ).first()
    if not signup:
        signup = ListingSignup(
            listing_id=listing.id,
            user_id=dev.id,
            status='pending',
        )
        profile = dev.developer_profile
        if profile:
            profile.contracts_attempted = (profile.contracts_attempted or 0) + 1
        db.session.add(signup)
        print(f'Developer {dev.username} joined sprint id={listing.id} (status=pending)')
    else:
        print(f'Signup already exists: developer {dev.username} → listing {listing.id} (status={signup.status})')

    db.session.commit()
    print('\nSeed complete.')
    print(f'  Business login: testbusiness@jrdev.io / Password123!')
    print(f'  Developer login: testdev@jrdev.io / Password123!')
    print(f'  Sprint listing id: {listing.id}')
    print(f'  Signup id: {signup.id}')
