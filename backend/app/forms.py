"""
Authentication forms: registration and login.

Shared EMAIL_VALIDATORS keep email validation DRY across forms.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, RadioField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Regexp
from app.models import User

# Single source of truth for email validation (used by RegistrationForm and LoginForm)
EMAIL_VALIDATORS = [
    DataRequired(),
    Regexp(r'^.+@.+\..+$', message='Invalid email address.'),
]


class RegistrationForm(FlaskForm):
    """Register a new user (developer or business) with email/password and optional 2FA."""
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=1, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=1, max=50)])
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=EMAIL_VALIDATORS)
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters.'),
        Regexp(r'(?=.*[A-Za-z])(?=.*\d)', message='Password must contain at least one letter and one number.'),
    ])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Register as:', choices=[('DEVELOPER', 'Developer'), ('BUSINESS', 'Business')], validators=[DataRequired()])
    accept_terms = BooleanField('I agree to the Terms & Conditions and Privacy Policy',
                                validators=[DataRequired(message='You must agree to the Terms & Conditions to register.')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')


class LoginForm(FlaskForm):
    """Login with email and password; optional remember-me."""
    email = StringField('Email', validators=EMAIL_VALIDATORS)
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class ForgotPasswordForm(FlaskForm):
    """Request a password reset via magic link or 6-digit code."""
    email = StringField('Email', validators=EMAIL_VALIDATORS)
    method = RadioField(
        'How would you like to reset?',
        choices=[('magic', 'Magic link — click a link in your email'), ('code', 'Code — enter a 6-digit code')],
        default='magic',
        validators=[DataRequired()],
    )
    submit = SubmitField('Send Reset')


class ResetCodeForm(FlaskForm):
    """Enter the 6-digit OTP code sent to the user's email."""
    code = StringField('6-Digit Code', validators=[
        DataRequired(),
        Length(min=6, max=6, message='Code must be exactly 6 digits.'),
        Regexp(r'^\d{6}$', message='Code must be 6 digits.'),
    ])
    submit = SubmitField('Verify Code')


class NewPasswordForm(FlaskForm):
    """Set a new password after identity has been verified."""
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters.'),
        Regexp(r'(?=.*[A-Za-z])(?=.*\d)', message='Password must contain at least one letter and one number.'),
    ])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Set New Password')
