"""
Profile and dashboard forms: edit profile, markdown, pinned projects.

Theme/panel/background choices are defined here for consistency with models and templates.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, URL, Optional
from flask_wtf.file import FileField, FileAllowed

# Choices for developer profile appearance (must match model defaults / utils.PROFILE_*_DEFAULT)
THEME_CHOICES = [
    ('mint', 'Mint'),
    ('ocean', 'Ocean'),
    ('sunset', 'Sunset'),
    ('neon', 'Neon'),
    ('rose', 'Rose'),
    ('amber', 'Amber'),
]
ANIMATION_CHOICES = [
    ('none', 'None'),
    ('glow', 'Glow'),
    ('shimmer', 'Shimmer'),
    ('float', 'Float'),
]
PANEL_STYLE_CHOICES = [
    ('solid', 'Solid'),
    ('translucent', 'Liquid glass'),
]
BACKGROUND_CHOICES = [
    ('default', 'Default'),
    ('gradient', 'Gradient'),
    ('mesh', 'Mesh'),
    ('dots', 'Dots'),
    ('glow', 'Glow'),
]

class EditProfileForm(FlaskForm):
    """Edit developer profile: headline, location, tech stack, links, picture, theme options."""
    headline = StringField('Headline', validators=[DataRequired()])
    location = StringField('Location')
    availability = SelectField('Status', choices=[
        ('Open to Work', 'Open to Work'),
        ('Busy', 'Busy'),
        ('Hired', 'Hired'),
        ('On Prototype', 'On Prototype')
    ])
    technologies = StringField('Tech Stack (comma separated)', validators=[Optional()])
    github_link = StringField('GitHub URL', validators=[Optional()])
    linkedin_link = StringField('LinkedIn URL', validators=[Optional()])
    portfolio_link = StringField('Portfolio URL', validators=[Optional()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    profile_theme = SelectField('Profile theme', choices=THEME_CHOICES, validators=[Optional()])
    profile_animation = SelectField('Profile animation', choices=ANIMATION_CHOICES, validators=[Optional()])
    profile_panel_style = SelectField('Panel style', choices=PANEL_STYLE_CHOICES, validators=[Optional()])
    profile_background = SelectField('Background', choices=BACKGROUND_CHOICES, validators=[Optional()])
    submit = SubmitField('Update Profile')

class EditMarkdownForm(FlaskForm):
    """Edit the custom markdown bio/content on the developer dashboard."""
    markdown_content = TextAreaField('Content', validators=[DataRequired()]) 
    submit = SubmitField('Save Content')

class AddPinnedProjectForm(FlaskForm):
    """Add a pinned project to the developer profile (title, description, link, tags)."""
    title = StringField('Project Title', validators=[DataRequired()])
    description = StringField('Short Description', validators=[DataRequired()])
    link = StringField('Link (Repo/Demo)', validators=[Optional(), URL()])
    tags = StringField('Tags (e.g. Python, React)', validators=[Optional()])
    submit = SubmitField('Add Project')