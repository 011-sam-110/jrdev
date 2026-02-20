from datetime import datetime
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from . import db, login_manager
from flask_login import UserMixin
import pyotp

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(64), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='DEVELOPER') # 'DEVELOPER' or 'BUSINESS'
    
    # Security Fields
    is_verified = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32), nullable=True)
    
    # Relationships
    developer_profile = db.relationship('DeveloperProfile', backref='user', uselist=False, lazy=True)
    projects = db.relationship('Project', backref='author', lazy=True)

    def get_verification_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id}, salt='verification-salt')

    @staticmethod
    def verify_token(token, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, salt='verification-salt', max_age=expires_sec)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def get_totp_uri(self):
        return pyotp.totp.TOTP(self.two_factor_secret).provisioning_uri(
            name=self.email, 
            issuer_name='JrDev Platform'
        )

    def verify_totp(self, token):
        return pyotp.TOTP(self.two_factor_secret).verify(token)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role}')"

class DeveloperProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Identity
    headline = db.Column(db.String(100), default='Aspiring Developer')
    bio = db.Column(db.Text, nullable=True) # Short bio
    location = db.Column(db.String(50), default='Remote')
    availability = db.Column(db.String(20), default='Open to Work')
    
    # Skills & Links
    technologies = db.Column(db.String(255), default='Python,JavaScript') # Comma separated
    github_link = db.Column(db.String(120))
    linkedin_link = db.Column(db.String(120))
    portfolio_link = db.Column(db.String(120))
    
    # Custom Content
    custom_markdown = db.Column(db.Text, default='# About Me\nI write code.')
    
    # Stats
    contracts_attempted = db.Column(db.Integer, default=0)
    contracts_won = db.Column(db.Integer, default=0)
    
    # Relationships
    pinned_projects = db.relationship('PinnedProject', backref='profile', lazy=True)

class PinnedProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('developer_profile.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    link = db.Column(db.String(200), nullable=True) # Repo or Demo
    tags = db.Column(db.String(100), nullable=True) # e.g. "Python,Flask"

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Project('{self.title}', '{self.date_posted}')"
