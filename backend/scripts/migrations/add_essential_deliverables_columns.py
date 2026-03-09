"""One-off script: add essential_deliverables and essential_deliverables_count to sprint_listing if missing."""
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

if 'essential_deliverables' not in cols:
    cur.execute('ALTER TABLE sprint_listing ADD COLUMN essential_deliverables TEXT')
    conn.commit()
    print('Added sprint_listing.essential_deliverables.')
else:
    print('sprint_listing.essential_deliverables already exists.')

if 'essential_deliverables_count' not in cols:
    cur.execute('ALTER TABLE sprint_listing ADD COLUMN essential_deliverables_count INTEGER NOT NULL DEFAULT 0')
    conn.commit()
    print('Added sprint_listing.essential_deliverables_count.')
else:
    print('sprint_listing.essential_deliverables_count already exists.')

conn.close()
