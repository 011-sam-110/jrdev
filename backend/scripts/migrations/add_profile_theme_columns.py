"""Add profile_theme and profile_animation to developer_profile. Run from backend: python add_profile_theme_columns.py"""
import os
import sys
import sqlite3

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

db_name = 'site.db'
candidates = [
    os.path.join(backend_dir, db_name),
    os.path.join(backend_dir, 'instance', db_name),
    os.path.join(os.path.dirname(backend_dir), db_name),
]
db_path = next((p for p in candidates if os.path.exists(p)), None)
if not db_path:
    print('Database not found. Tried:', candidates)
    sys.exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("PRAGMA table_info(developer_profile)")
cols = [r[1] for r in cur.fetchall()]

for col_name, default in [('profile_theme', "'mint'"), ('profile_animation', "'glow'")]:
    if col_name not in cols:
        cur.execute(f"ALTER TABLE developer_profile ADD COLUMN {col_name} VARCHAR(30) DEFAULT {default}")
        print(f'Added developer_profile.{col_name}.')
    else:
        print(f'developer_profile.{col_name} already exists.')

conn.commit()
conn.close()
print('Done.')
