"""One-off migration: add developer_registered_address to listing_signup table.
Run from backend directory: python add_developer_registered_address.py [path/to/site.db]
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
        sys.exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("PRAGMA table_info(listing_signup)")
cols = [r[1] for r in cur.fetchall()]

if 'developer_registered_address' not in cols:
    cur.execute('ALTER TABLE listing_signup ADD COLUMN developer_registered_address VARCHAR(255)')
    print('Added listing_signup.developer_registered_address.')
else:
    print('listing_signup.developer_registered_address already exists.')

conn.commit()
conn.close()
print('Done.')
