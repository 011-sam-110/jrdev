from app import create_app, db, bcrypt
from app.models import User, DeveloperProfile
import pyotp

app = create_app()

with app.app_context():
    if not User.query.filter_by(email='admin@admin').first():
        hashed_password = bcrypt.generate_password_hash('admin').decode('utf-8')
        totp_secret = pyotp.random_base32()
        user = User(
            username='admin',
            email='admin@admin',
            password=hashed_password,
            role='DEVELOPER',
            two_factor_secret=totp_secret,
            is_verified=True
        )
        db.session.add(user)
        db.session.commit()
        profile = DeveloperProfile(
            user_id=user.id,
            headline='Full Stack Developer',
            bio='Admin account for testing.',
            technologies='Python, Flask, React'
        )
        db.session.add(profile)
        db.session.commit()
        print("Admin user created successfully.")
    else:
        print("Admin user already exists.")
