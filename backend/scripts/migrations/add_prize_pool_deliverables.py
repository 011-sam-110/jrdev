"""One-off script: add essential_deliverables, optional_deliverables to prize_pool and requirements_met to prize_pool_entry."""
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

# prize_pool
cur.execute('PRAGMA table_info(prize_pool)')
cols = [row[1] for row in cur.fetchall()]
if 'essential_deliverables' not in cols:
    cur.execute('ALTER TABLE prize_pool ADD COLUMN essential_deliverables TEXT')
    conn.commit()
    print('Added prize_pool.essential_deliverables.')
else:
    print('prize_pool.essential_deliverables already exists.')
if 'optional_deliverables' not in cols:
    cur.execute('ALTER TABLE prize_pool ADD COLUMN optional_deliverables TEXT')
    conn.commit()
    print('Added prize_pool.optional_deliverables.')
else:
    print('prize_pool.optional_deliverables already exists.')

# prize_pool_entry
cur.execute('PRAGMA table_info(prize_pool_entry)')
cols = [row[1] for row in cur.fetchall()]
if 'requirements_met' not in cols:
    cur.execute('ALTER TABLE prize_pool_entry ADD COLUMN requirements_met VARCHAR(500)')
    conn.commit()
    print('Added prize_pool_entry.requirements_met.')
else:
    print('prize_pool_entry.requirements_met already exists.')

conn.close()
print('Migration complete.')
