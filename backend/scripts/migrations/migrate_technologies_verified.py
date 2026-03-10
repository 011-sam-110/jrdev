"""
One-time migration: add technologies_verified column to developer_profile.
Run from backend/: python migrate_technologies_verified.py

For existing profiles with legacy "Python+2" format in technologies:
- Extracts counts into technologies_verified JSON
- Replaces technologies with names only
"""
import json
import sys
import os

# Add parent to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import DeveloperProfile
from sqlalchemy import text, inspect


def _strip_tech_count(entry):
    """Strip +N suffix. 'Python+2' -> 'Python'."""
    s = (entry or '').strip()
    if '+' in s:
        parts = s.rsplit('+', 1)
        try:
            int(parts[1])
            return parts[0].strip()
        except (ValueError, IndexError):
            pass
    return s


def migrate():
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        cols = [c['name'] for c in inspector.get_columns('developer_profile')]
        if 'technologies_verified' not in cols:
            db.session.execute(text(
                'ALTER TABLE developer_profile ADD COLUMN technologies_verified TEXT'
            ))
            db.session.commit()
            print('Added technologies_verified column.')
        else:
            print('Column technologies_verified already exists.')

        # Migrate legacy data: "Python+2, React" -> technologies="Python, React", technologies_verified='{"python": 2}'
        for profile in DeveloperProfile.query.all():
            raw = profile.technologies or ''
            if not raw or '+' not in raw:
                continue
            verified = {}
            names = []
            for entry in [t.strip() for t in raw.split(',') if t.strip()]:
                base = _strip_tech_count(entry)
                if not base:
                    continue
                key = base.lower()
                if '+' in entry:
                    parts = entry.rsplit('+', 1)
                    try:
                        count = int(parts[1])
                        verified[key] = verified.get(key, 0) + count
                    except (ValueError, IndexError):
                        pass
                if key not in {n.lower() for n in names}:
                    names.append(base)
            if verified:
                existing = {}
                if profile.technologies_verified:
                    try:
                        existing = json.loads(profile.technologies_verified)
                    except (TypeError, ValueError):
                        pass
                for k, v in verified.items():
                    existing[k] = existing.get(k, 0) + v
                profile.technologies_verified = json.dumps(existing)
                profile.technologies = ', '.join(names)
                print(f'Migrated profile {profile.id}: {profile.technologies}')
        db.session.commit()
        print('Migration complete.')


if __name__ == '__main__':
    migrate()
