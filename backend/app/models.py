"""
SQLAlchemy models: User, DeveloperProfile, PinnedProject, Project, SprintListing, ListingSignup.

User supports roles (DEVELOPER/BUSINESS), 2FA, and Stripe customer id.
SprintListing and ListingSignup implement the sprint/contract/signup flow.
"""
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from . import db, login_manager
from flask_login import UserMixin
import pyotp


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login: load user by id from session."""
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    """Platform user: developer or business; auth, 2FA, optional Stripe customer."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(64), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='DEVELOPER') # 'DEVELOPER' or 'BUSINESS'
    
    # Security Fields
    is_verified = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32), nullable=True)

    # Billing (Stripe) – for BUSINESS accounts
    stripe_customer_id = db.Column(db.String(120), nullable=True)
    
    # Relationships
    developer_profile = db.relationship('DeveloperProfile', backref='user', uselist=False, lazy=True, cascade='all, delete-orphan')
    projects = db.relationship('Project', backref='author', lazy=True, cascade='all, delete-orphan')

    def get_verification_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id}, salt='verification-salt')

    @staticmethod
    def verify_token(token, expires_sec=1800):
        """Verify email verification token; return User or None if invalid/expired."""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, salt='verification-salt', max_age=expires_sec)['user_id']
        except Exception:
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
    """Developer-specific profile: headline, tech stack, links, markdown, theme options, stats."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    # Identity
    headline = db.Column(db.String(100), default='Aspiring Developer')
    bio = db.Column(db.Text, nullable=True) # Short bio
    location = db.Column(db.String(50), default='Remote')
    availability = db.Column(db.String(20), default='Open to Work')
    
    # Skills & Links
    technologies = db.Column(db.String(255), default='Python,JavaScript') # Comma separated (names only; no +N)
    technologies_verified = db.Column(db.Text, nullable=True)  # JSON: {"python": 2, "react": 1} from completed sprints only
    github_link = db.Column(db.String(120))
    linkedin_link = db.Column(db.String(120))
    portfolio_link = db.Column(db.String(120))
    
    # Custom Content
    custom_markdown = db.Column(db.Text, default='# About Me\nI write code.')
    
    # Appearance (dashboard & public profile)
    profile_theme = db.Column(db.String(30), default='mint')   # mint, ocean, sunset, neon, rose, amber
    profile_animation = db.Column(db.String(30), default='glow')  # none, glow, shimmer, float
    profile_panel_style = db.Column(db.String(30), default='solid')  # solid, translucent (liquid glass)
    profile_background = db.Column(db.String(30), default='default')  # default, gradient, mesh, dots, glow
    
    # Stats
    contracts_attempted = db.Column(db.Integer, default=0)
    contracts_won = db.Column(db.Integer, default=0)
    prototypes_completed = db.Column(db.Integer, default=0)

    # Settings: saved signature & address for contracts (avoid re-entering each sprint)
    saved_signature = db.Column(db.Text, nullable=True)  # base64 PNG data URL
    saved_contractor_address = db.Column(db.String(255), nullable=True)

    # Relationships
    pinned_projects = db.relationship('PinnedProject', backref='profile', lazy=True)

class PinnedProject(db.Model):
    """Pinned project shown on developer profile (title, description, link, tags)."""
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('developer_profile.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    link = db.Column(db.String(200), nullable=True) # Repo or Demo
    tags = db.Column(db.String(100), nullable=True) # e.g. "Python,Flask"

class Project(db.Model):
    """Legacy project post (title, content, author)."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Project('{self.title}', '{self.date_posted}')"


class SprintListing(db.Model):
    """A prototype/sprint posting created by a business."""
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    company_name = db.Column(db.String(120), nullable=False)
    company_address = db.Column(db.String(255), nullable=True)
    max_talent_pool = db.Column(db.Integer, nullable=False, default=3)
    pay_for_prototype = db.Column(db.Integer, nullable=False, default=2000)  # stored in pence
    business_rating = db.Column(db.Float, nullable=True)
    technologies_required = db.Column(db.String(500), nullable=True)
    deliverables = db.Column(db.Text, nullable=True)  # Newline-separated optional contract deliverables
    essential_deliverables = db.Column(db.Text, nullable=True)  # Newline-separated required deliverables (must complete)
    essential_deliverables_count = db.Column(db.Integer, nullable=False, default=0)  # Number of essential (for validation)
    sprint_timeline_days = db.Column(db.Integer, nullable=False, default=7)
    signup_ends_at = db.Column(db.DateTime, nullable=False)
    sprint_begins_at = db.Column(db.DateTime, nullable=False)
    sprint_ends_at = db.Column(db.DateTime, nullable=False)
    minimum_requirements_for_pay = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='open', index=True)

    business = db.relationship('User', backref='sprint_listings')
    signups = db.relationship('ListingSignup', backref='listing', cascade='all, delete-orphan')

    @property
    def joined_count(self):
        return len(self.signups)

    @property
    def is_full(self):
        return self.joined_count >= self.max_talent_pool

    @property
    def essential_deliverables_list(self):
        """List of essential (required) deliverable strings."""
        if self.essential_deliverables:
            return [t.strip() for t in self.essential_deliverables.split('\n') if t.strip()]
        return []

    @property
    def optional_deliverables_list(self):
        """List of optional deliverable strings."""
        if self.deliverables:
            return [t.strip() for t in self.deliverables.split('\n') if t.strip()]
        return []

    @property
    def deliverables_list(self):
        """Full list for contract: essential first, then optional. Fallback to technologies if none."""
        essential = self.essential_deliverables_list
        optional = self.optional_deliverables_list
        if essential or optional:
            return essential + optional
        return [t.strip() for t in (self.technologies_required or '').split(',') if t.strip()]

    @property
    def has_deliverables(self):
        """True if this listing has actual deliverables (not just technologies)."""
        return bool(
            (self.essential_deliverables and self.essential_deliverables.strip())
            or (self.deliverables and self.deliverables.strip())
        )

    @property
    def deliverables_only_list(self):
        """Full deliverables list for checkboxes (essential + optional)."""
        return self.essential_deliverables_list + self.optional_deliverables_list


class ListingSignup(db.Model):
    """Developer joining a sprint listing. Business can accept/deny; both parties e-sign contract."""
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('sprint_listing.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    joined_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='pending', index=True)
    developer_signed_at = db.Column(db.DateTime, nullable=True)
    business_signed_at = db.Column(db.DateTime, nullable=True)
    developer_signature_image = db.Column(db.Text, nullable=True)  # base64 PNG data URL
    business_signature_image = db.Column(db.Text, nullable=True)  # base64 PNG data URL
    developer_registered_address = db.Column(db.String(255), nullable=True)  # provided when developer e-signs
    github_submission_url = db.Column(db.String(500), nullable=True)
    demo_video_url = db.Column(db.String(500), nullable=True)
    prototype_submitted_at = db.Column(db.DateTime, nullable=True)
    requirements_met = db.Column(db.String(500), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    flagged_for_review = db.Column(db.Boolean, default=False)
    signing_deadline_at = db.Column(db.DateTime, nullable=True)  # 2 days after accepted
    business_rating_of_developer = db.Column(db.Integer, nullable=True)  # 1-5
    developer_rating_of_business = db.Column(db.Integer, nullable=True)  # 1-5
    developer_withdrew = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref='listing_signups')

    @property
    def is_fully_signed(self):
        return self.developer_signed_at is not None and self.business_signed_at is not None


class PrizePool(db.Model):
    """Prize pool challenge: paid (entry fee, user voting) or free (AI review placeholder)."""
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='open', index=True)  # open, voting, closed
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    technologies_required = db.Column(db.String(500), nullable=True)
    pool_type = db.Column(db.String(20), nullable=False, default='paid')  # paid | free
    entry_fee_pence = db.Column(db.Integer, nullable=True)  # null = free pool, stored in pence
    signup_ends_at = db.Column(db.DateTime, nullable=False)
    submission_ends_at = db.Column(db.DateTime, nullable=False)
    voting_ends_at = db.Column(db.DateTime, nullable=True)  # for paid
    review_ends_at = db.Column(db.DateTime, nullable=True)  # for free, placeholder
    max_participants = db.Column(db.Integer, nullable=True)  # null = unlimited
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    essential_deliverables = db.Column(db.Text, nullable=True)  # Newline-separated required deliverables
    optional_deliverables = db.Column(db.Text, nullable=True)  # Newline-separated optional deliverables

    created_by = db.relationship('User', backref='created_prize_pools', foreign_keys=[created_by_id])
    entries = db.relationship('PrizePoolEntry', backref='prize_pool', cascade='all, delete-orphan')
    votes = db.relationship('PrizePoolVote', backref='prize_pool', cascade='all, delete-orphan')
    pairwise_votes = db.relationship('PrizePoolPairwiseVote', backref='prize_pool', cascade='all, delete-orphan')

    @property
    def entry_count(self):
        """Number of paid/joined entries (with payment_completed_at for paid pools)."""
        return len([e for e in self.entries if e.payment_completed_at is not None or self.pool_type == 'free'])

    @property
    def joined_count(self):
        return len([e for e in self.entries if e.payment_completed_at is not None or self.entry_fee_pence is None])

    @property
    def is_free(self):
        return self.pool_type == 'free' or self.entry_fee_pence is None

    @property
    def essential_deliverables_list(self):
        """List of essential (required) deliverable strings."""
        if self.essential_deliverables:
            return [t.strip() for t in self.essential_deliverables.split('\n') if t.strip()]
        return []

    @property
    def optional_deliverables_list(self):
        """List of optional deliverable strings."""
        if self.optional_deliverables:
            return [t.strip() for t in self.optional_deliverables.split('\n') if t.strip()]
        return []

    @property
    def deliverables_only_list(self):
        """Full deliverables list for checkboxes (essential + optional)."""
        return self.essential_deliverables_list + self.optional_deliverables_list


class PrizePoolEntry(db.Model):
    """Developer's entry in a prize pool. Payment required for paid pools."""
    __table_args__ = (
        db.UniqueConstraint('prize_pool_id', 'user_id', name='uq_prize_pool_entry_pool_user'),
    )
    id = db.Column(db.Integer, primary_key=True)
    prize_pool_id = db.Column(db.Integer, db.ForeignKey('prize_pool.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    joined_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    payment_intent_id = db.Column(db.String(255), nullable=True)  # Stripe
    payment_completed_at = db.Column(db.DateTime, nullable=True)
    demo_video_url = db.Column(db.String(500), nullable=True)
    github_submission_url = db.Column(db.String(500), nullable=True)
    submitted_at = db.Column(db.DateTime, nullable=True)
    requirements_met = db.Column(db.String(500), nullable=True)  # Comma-separated deliverables completed
    is_winner = db.Column(db.Boolean, default=False)
    ai_review_result = db.Column(db.String(20), nullable=True)  # pass/fail for free, placeholder

    user = db.relationship('User', backref='prize_pool_entries')

    @property
    def has_paid(self):
        return self.payment_completed_at is not None

    @property
    def has_submitted(self):
        return self.submitted_at is not None


class PrizePoolVote(db.Model):
    """Participant vote: ranks 3 entries (1st=best, 3rd=worst). Points: 1st=3, 2nd=2, 3rd=1."""
    id = db.Column(db.Integer, primary_key=True)
    prize_pool_id = db.Column(db.Integer, db.ForeignKey('prize_pool.id'), nullable=False)
    voter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    entry_1_id = db.Column(db.Integer, db.ForeignKey('prize_pool_entry.id'), nullable=False)
    entry_2_id = db.Column(db.Integer, db.ForeignKey('prize_pool_entry.id'), nullable=False)
    entry_3_id = db.Column(db.Integer, db.ForeignKey('prize_pool_entry.id'), nullable=False)
    rank_1_id = db.Column(db.Integer, db.ForeignKey('prize_pool_entry.id'), nullable=False)  # best
    rank_2_id = db.Column(db.Integer, db.ForeignKey('prize_pool_entry.id'), nullable=False)
    rank_3_id = db.Column(db.Integer, db.ForeignKey('prize_pool_entry.id'), nullable=False)  # worst
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    voter = db.relationship('User', backref='prize_pool_votes', foreign_keys=[voter_id])


class PrizePoolPairwiseVote(db.Model):
    """Pairwise comparison: voter chose winner_entry_id as best between entry_a and entry_b."""
    id = db.Column(db.Integer, primary_key=True)
    prize_pool_id = db.Column(db.Integer, db.ForeignKey('prize_pool.id'), nullable=False, index=True)
    voter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    entry_a_id = db.Column(db.Integer, db.ForeignKey('prize_pool_entry.id'), nullable=False)
    entry_b_id = db.Column(db.Integer, db.ForeignKey('prize_pool_entry.id'), nullable=False)
    winner_entry_id = db.Column(db.Integer, db.ForeignKey('prize_pool_entry.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    voter = db.relationship('User', backref='prize_pool_pairwise_votes', foreign_keys=[voter_id])


class PrizePoolPayout(db.Model):
    """Log of prize payouts when a pool closes. One row per winning entry (who won, how much)."""
    id = db.Column(db.Integer, primary_key=True)
    prize_pool_id = db.Column(db.Integer, db.ForeignKey('prize_pool.id'), nullable=False)
    prize_pool_entry_id = db.Column(db.Integer, db.ForeignKey('prize_pool_entry.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount_pence = db.Column(db.Integer, nullable=False, default=0)  # stored in pence
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)  # when actually paid out (manual/admin)
    notes = db.Column(db.String(500), nullable=True)

    prize_pool = db.relationship('PrizePool', backref=db.backref('payouts', lazy=True))
    prize_pool_entry = db.relationship('PrizePoolEntry', backref=db.backref('payout', uselist=False, lazy=True))
    user = db.relationship('User', backref='prize_pool_payouts', foreign_keys=[user_id])


class AdminEmail(db.Model):
    """Stores inbound and outbound emails for the three admin inboxes."""
    __tablename__ = 'admin_emails'
    id          = db.Column(db.Integer, primary_key=True)
    inbox       = db.Column(db.String(20), nullable=False, index=True)   # 'noreply' | 'support' | 'disputes'
    direction   = db.Column(db.String(8), nullable=False)                # 'inbound' | 'outbound'
    message_id  = db.Column(db.String(500), unique=True, nullable=True)  # email Message-ID header
    in_reply_to = db.Column(db.String(500), nullable=True)               # In-Reply-To header
    thread_id   = db.Column(db.String(500), nullable=True, index=True)   # = oldest message_id in thread
    from_addr   = db.Column(db.String(255), nullable=False)
    to_addrs    = db.Column(db.Text, nullable=False)                     # JSON list
    cc_addrs    = db.Column(db.Text, nullable=True)                      # JSON list
    bcc_addrs   = db.Column(db.Text, nullable=True)                      # JSON list (outbound only)
    subject     = db.Column(db.String(500))
    body_text   = db.Column(db.Text)
    body_html   = db.Column(db.Text)
    is_read     = db.Column(db.Boolean, default=False, nullable=False)
    sent_at     = db.Column(db.DateTime, nullable=True, index=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class AdminEmailTemplate(db.Model):
    """Reusable email templates with pre-filled subject and body content."""
    __tablename__ = 'admin_email_templates'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    category    = db.Column(db.String(50), nullable=True)   # 'general' | 'support' | 'disputes' | 'billing'
    subject     = db.Column(db.String(500), nullable=True)
    body_html   = db.Column(db.Text, nullable=False)        # content area only; wrapped in branded layout on send
    created_at  = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AdminEmailConfig(db.Model):
    """Singleton config row for global email settings (signature, default inbox)."""
    __tablename__ = 'admin_email_config'
    id              = db.Column(db.Integer, primary_key=True)  # always 1
    signature_html  = db.Column(db.Text, nullable=True)        # appended to every outbound email
    default_inbox   = db.Column(db.String(20), default='noreply', nullable=False)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @classmethod
    def get(cls):
        """Return the singleton config row, creating it if it doesn't exist."""
        row = cls.query.get(1)
        if not row:
            row = cls(id=1, signature_html='<p>Best regards,<br><strong>The JrDev Team</strong></p>', default_inbox='noreply')
            db.session.add(row)
            db.session.commit()
        return row
