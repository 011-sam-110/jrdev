"""
One-off script to add saved_signature and saved_contractor_address to developer_profile.
Run from backend directory: python add_saved_signature_columns.py [path/to/site.db]
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
cur.execute("PRAGMA table_info(developer_profile)")
cols = [r[1] for r in cur.fetchall()]

for col_name, col_type in [('saved_signature', 'TEXT'), ('saved_contractor_address', 'VARCHAR(255)')]:
    if col_name not in cols:
        cur.execute(f'ALTER TABLE developer_profile ADD COLUMN {col_name} {col_type}')
        print(f'Added developer_profile.{col_name}.')
    else:
        print(f'developer_profile.{col_name} already exists.')

conn.commit()
conn.close()
print('Done.')
