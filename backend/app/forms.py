"""
Authentication forms: registration and login.

Shared EMAIL_VALIDATORS keep email validation DRY across forms.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Regexp
from app.models import User

# Single source of truth for email validation (used by RegistrationForm and LoginForm)
EMAIL_VALIDATORS = [
    DataRequired(),
    Regexp(r'^.+@.+\..+$', message='Invalid email address.'),
]


class RegistrationForm(FlaskForm):
    """Register a new user (developer or business) with email/password and optional 2FA."""
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=EMAIL_VALIDATORS)
    password = PasswordField('Password', validators=[DataRequired()])
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
