"""One-off migration: add first_name and last_name to user table.
Run from backend directory: python add_first_last_name.py [path/to/site.db]
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
cur.execute("PRAGMA table_info(user)")
cols = [r[1] for r in cur.fetchall()]

for col_name in ('first_name', 'last_name'):
    if col_name not in cols:
        cur.execute(f'ALTER TABLE user ADD COLUMN {col_name} VARCHAR(50)')
        print(f'Added user.{col_name}.')
    else:
        print(f'user.{col_name} already exists.')

conn.commit()
conn.close()
print('Done.')
