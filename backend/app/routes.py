from flask import Blueprint, render_template, url_for, flash, redirect, request, session
import os
from werkzeug.utils import secure_filename
from app import db, bcrypt, mail
from app.forms import RegistrationForm, LoginForm
from app.profile_forms import EditProfileForm, EditMarkdownForm, AddPinnedProjectForm
from app.models import User, DeveloperProfile, Project, PinnedProject
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
import pyotp
import qrcode
import io
import markdown
import base64

main = Blueprint('main', __name__)

@main.route("/")
@main.route("/home")
def home():
    if current_user.is_authenticated:
        if current_user.role == 'DEVELOPER':
            profile = current_user.developer_profile
            # Convert markdown to HTML for display
            md_html = markdown.markdown(profile.custom_markdown) if profile.custom_markdown else ""
            # Parse tech stack
            stack_list = [t.strip() for t in profile.technologies.split(',')] if profile.technologies else []
            
            form = AddPinnedProjectForm()
            
            return render_template('developer_dashboard.html', 
                                   title='Dashboard', 
                                   profile=profile, 
                                   md_html=md_html,
                                   stack_list=stack_list,
                                   form=form)
        # We can add BUSINESS dashboard later
        # elif current_user.role == 'BUSINESS':
        #     return render_template('business_dashboard.html')
            
    projects = Project.query.all()
    return render_template('home.html', projects=projects, title='Home')

@main.route("/about")
def about():
    return render_template('about.html', title='About')

@main.route("/edit-profile", methods=['GET', 'POST'])
@login_required
def edit_profile():
    if current_user.role != 'DEVELOPER':
        flash('Access Denied', 'danger')
        return redirect(url_for('main.home'))
        
    form = EditProfileForm()
    profile = current_user.developer_profile
    
    if form.validate_on_submit():
        profile.headline = form.headline.data
        profile.location = form.location.data
        profile.availability = form.availability.data
        profile.technologies = form.technologies.data
        profile.github_link = form.github_link.data
        profile.linkedin_link = form.linkedin_link.data
        profile.portfolio_link = form.portfolio_link.data

        # Handle profile picture upload
        if form.picture.data:
            pic_file = form.picture.data
            filename = secure_filename(pic_file.filename)
            # Ensure unique filename
            _, ext = os.path.splitext(filename)
            filename = f"user_{current_user.id}{ext}"
            # Save to backend/static/profile_pics (not app/static/profile_pics)
            static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'profile_pics'))
            os.makedirs(static_dir, exist_ok=True)
            abs_pic_path = os.path.join(static_dir, filename)
            pic_file.save(abs_pic_path)
            current_user.image_file = filename
        db.session.commit()
        flash('Profile Updated!', 'success')
        return redirect(url_for('main.home'))
    elif request.method == 'GET':
        form.headline.data = profile.headline
        form.location.data = profile.location
        form.availability.data = profile.availability
        form.technologies.data = profile.technologies
        form.github_link.data = profile.github_link
        form.linkedin_link.data = profile.linkedin_link
        form.portfolio_link.data = profile.portfolio_link
        
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@main.route("/update-markdown", methods=['POST'])
@login_required
def update_markdown():
    if current_user.role != 'DEVELOPER':
        return jsonify({'error': 'Unauthorized'}), 403
    
    content = request.form.get('content')
    profile = current_user.developer_profile
    profile.custom_markdown = content
    db.session.commit()
    return redirect(url_for('main.home')) # Simple redirect for now

@main.route("/add-pinned-project", methods=['POST'])
@login_required
def add_pinned_project():
    if current_user.role != 'DEVELOPER':
        return redirect(url_for('main.home'))
    
    title = request.form.get('title')
    desc = request.form.get('description')
    tags = request.form.get('tags')
    link = request.form.get('link')
    
    if title and desc:
        project = PinnedProject(
            profile_id=current_user.developer_profile.id,
            title=title,
            description=desc,
            tags=tags,
            link=link
        )
        db.session.add(project)
        db.session.commit()
        flash('Project Pinned!', 'success')
    return redirect(url_for('main.home'))

@main.route("/pin-delete/<int:id>")
@login_required
def delete_pinned(id):
    project = PinnedProject.query.get_or_404(id)
    if project.profile.user_id != current_user.id:
        flash('Access Denied', 'danger')
        return redirect(url_for('main.home'))
    db.session.delete(project)
    db.session.commit()
    flash('Project Removed', 'success')
    return redirect(url_for('main.home'))

@main.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    
    # Pre-select role if provided in query params
    if request.method == 'GET':
        role = request.args.get('role')
        if role in ['DEVELOPER', 'BUSINESS']:
            form.role.data = role
            
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        # Generate 2FA Secret
        totp_secret = pyotp.random_base32()
        
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, role=form.role.data, two_factor_secret=totp_secret)
        db.session.add(user)
        db.session.commit()
        
        # If developer, create profile
        if form.role.data == 'DEVELOPER':
            profile = DeveloperProfile(user_id=user.id)
            db.session.add(profile)
            db.session.commit()
            
        # Send Verification Email (Mocking for now as SMPT needs setup)
        # send_verification_email(user)
        # flash('A verification email has been sent to ' + user.email, 'info')

        # Log user in to complete 2FA setup
        login_user(user)
        return redirect(url_for('main.setup_2fa'))
        
    return render_template('register.html', title='Register', form=form)

@main.route("/setup-2fa", methods=['GET', 'POST'])
@login_required
def setup_2fa():
    user = current_user
    
    # Generate URI for QR Code
    totp_uri = user.get_totp_uri()
    
    if request.method == 'POST':
        token = request.form.get('token')
        if user.verify_totp(token):
            # 2FA Verified
            # Now simulate email verification sending
            # In production: msg = Message(...); mail.send(msg)
            # For demo, we mark as verified for now or print token
            
            user.is_verified = True 
            db.session.commit()
            
            flash('2FA Setup Complete! (Email verification skipped for demo). Your account is secure.', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Invalid Code. Please try again.', 'danger')
            
    # Generate QR Code Image
    img = qrcode.make(totp_uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_code = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return render_template('setup_2fa.html', qr_code=qr_code)

@main.route("/verify-2fa", methods=['GET', 'POST'])
def verify_2fa():
    if not session.get('2fa_user_id'):
        return redirect(url_for('main.login'))
        
    if request.method == 'POST':
        token = request.form.get('token')
        u_id = session.get('2fa_user_id')
        user = User.query.get(u_id)
        
        if user:
            totp = pyotp.TOTP(user.two_factor_secret)
            if totp.verify(token):
                login_user(user)
                session.pop('2fa_user_id', None)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('main.home'))
            else:
                flash('Invalid 2FA Code', 'danger')
        else:
            session.pop('2fa_user_id', None)
            return redirect(url_for('main.login'))
            
    return render_template('verify_2fa.html')

@main.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            # 2FA is disabled for now; log in directly
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@main.route("/account")
@login_required
def account():
    return render_template('account.html', title='Account')
