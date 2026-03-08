"""
Vercel serverless entry point for the JrDev Flask app.

Vercel routes all traffic here via vercel.json rewrites. This module adds the
backend directory to the path and exposes the Flask app for Vercel's Python runtime.
"""
import os
import sys

# Add backend to path so we can import the app package
_backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
sys.path.insert(0, _backend_dir)
os.chdir(_backend_dir)

# Load .env from project root if present (Vercel uses env vars from dashboard)
try:
    from dotenv import load_dotenv
    root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    load_dotenv(os.path.join(root_dir, '.env'))
except ImportError:
    pass

from app import create_app

# Vercel detects Flask apps by the `app` variable
app = create_app()
