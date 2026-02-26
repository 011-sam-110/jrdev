"""
WSGI entry point and development server.

Use: python run.py (or flask run with FLASK_APP=run.py).
Creates the app, ensures DB tables exist, and runs the dev server.
Set FLASK_ENV=development or DEBUG=1 for debug (never in production).

Loads .env from project root (parent of backend/) when present, so a root .env works.
"""
import os
try:
    from dotenv import load_dotenv
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(root_dir, '.env'))
    load_dotenv()
except ImportError:
    pass
from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    debug = (
        os.environ.get('FLASK_ENV') == 'development'
        or os.environ.get('DEBUG', '').lower() in ('1', 'true', 'yes')
    )
    app.run(debug=debug)
