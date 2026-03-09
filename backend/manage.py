from app import db, create_app, User, DeveloperProfile, Project
from flask.cli import with_appcontext, AppGroup
import click

app = create_app()

@app.cli.command("init_db")
def init_db():
    db.create_all()
    print("Initialized the database.")

if __name__ == '__main__':
    import os
    app.run(debug=os.environ.get('FLASK_ENV') == 'development')
