from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, URL, Optional
from flask_wtf.file import FileField, FileAllowed

class EditProfileForm(FlaskForm):
    headline = StringField('Headline', validators=[DataRequired()])
    location = StringField('Location')
    availability = SelectField('Status', choices=[
        ('Open to Work', 'Open to Work'),
        ('Busy', 'Busy'),
        ('Hired', 'Hired'),
        ('On Prototype', 'On Prototype')
    ])
    technologies = StringField('Tech Stack (comma separated)', validators=[Optional()])
    github_link = StringField('GitHub URL', validators=[Optional(), URL()])
    linkedin_link = StringField('LinkedIn URL', validators=[Optional(), URL()])
    portfolio_link = StringField('Portfolio URL', validators=[Optional(), URL()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Update Profile')

class EditMarkdownForm(FlaskForm):
    markdown_content = TextAreaField('Content', validators=[DataRequired()]) 
    submit = SubmitField('Save Content')

class AddPinnedProjectForm(FlaskForm):
    title = StringField('Project Title', validators=[DataRequired()])
    description = StringField('Short Description', validators=[DataRequired()])
    link = StringField('Link (Repo/Demo)', validators=[Optional(), URL()])
    tags = StringField('Tags (e.g. Python, React)', validators=[Optional()])
    submit = SubmitField('Add Project')