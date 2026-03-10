"""
One-off script to add status and signature columns to listing_signup table.
Run from backend directory: python add_signup_columns.py [path/to/site.db]
If no path given, looks for site.db in backend, backend/instance, and project root.
"""
import os
import sys
import sqlite3

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

if len(sys.argv) > 1:
    db_path = os.path.abspath(sys.argv[1])
    if not os.path.exists(db_path):
        print('File not found:', db_path)
        sys.exit(1)
else:
    db_name = 'site.db'
    candidates = [
        os.path.join(backend_dir, db_name),
        os.path.join(backend_dir, 'instance', db_name),
        os.path.join(os.path.dirname(backend_dir), db_name),
    ]
    db_path = None
    for p in candidates:
        if os.path.exists(p):
            db_path = p
            break
    if not db_path:
        print('Database not found. Tried:', candidates)
        print('Run: python add_signup_columns.py <path-to-site.db>')
        print('Or run Flask from backend so site.db is created, then run this script again.')
        sys.exit(1)

with sqlite3.connect(db_path) as conn:
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(listing_signup)")
    cols = [row[1] for row in cur.fetchall()]

    for col, typ, default in [
        ('status', 'VARCHAR(20)', "'pending'"),
        ('developer_signed_at', 'DATETIME', 'NULL'),
        ('business_signed_at', 'DATETIME', 'NULL'),
        ('github_submission_url', 'VARCHAR(500)', 'NULL'),
        ('demo_video_url', 'VARCHAR(500)', 'NULL'),
        ('prototype_submitted_at', 'DATETIME', 'NULL'),
        ('requirements_met', 'VARCHAR(500)', 'NULL'),
        ('reviewed_at', 'DATETIME', 'NULL'),
        ('flagged_for_review', 'BOOLEAN', '0'),
    ]:
        if col not in cols:
            cur.execute(f"ALTER TABLE listing_signup ADD COLUMN {col} {typ} DEFAULT {default}")
            print(f'Added column: {col}')
        else:
            print(f'Column already exists: {col}')

print('Done.')
