"""One-off script: add deliverables column to sprint_listing if missing."""
import sqlite3
import os

instance_path = os.path.join(os.path.dirname(__file__), 'instance')
db_path = os.path.join(instance_path, 'site.db')
if not os.path.exists(db_path):
    db_path = os.path.join(os.path.dirname(__file__), 'site.db')
if not os.path.exists(db_path):
    print('Database not found at', db_path)
    exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute('PRAGMA table_info(sprint_listing)')
cols = [row[1] for row in cur.fetchall()]
if 'deliverables' not in cols:
    cur.execute('ALTER TABLE sprint_listing ADD COLUMN deliverables TEXT')
    conn.commit()
    print('Added sprint_listing.deliverables.')
else:
    print('sprint_listing.deliverables already exists.')
conn.close()
