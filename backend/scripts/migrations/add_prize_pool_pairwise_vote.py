"""One-off migration: add prize_pool_pairwise_vote table.
Run from backend directory: python add_prize_pool_pairwise_vote.py [path/to/site.db]
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

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = {r[0] for r in cur.fetchall()}

if 'prize_pool_pairwise_vote' not in tables:
    cur.execute("""
        CREATE TABLE prize_pool_pairwise_vote (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prize_pool_id INTEGER NOT NULL,
            voter_id INTEGER NOT NULL,
            entry_a_id INTEGER NOT NULL,
            entry_b_id INTEGER NOT NULL,
            winner_entry_id INTEGER NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (prize_pool_id) REFERENCES prize_pool(id),
            FOREIGN KEY (voter_id) REFERENCES user(id),
            FOREIGN KEY (entry_a_id) REFERENCES prize_pool_entry(id),
            FOREIGN KEY (entry_b_id) REFERENCES prize_pool_entry(id),
            FOREIGN KEY (winner_entry_id) REFERENCES prize_pool_entry(id)
        )
    """)
    print('Created prize_pool_pairwise_vote table.')
else:
    print('prize_pool_pairwise_vote table already exists.')

conn.commit()
conn.close()
print('Done.')
