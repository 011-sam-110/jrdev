"""One-off migration: add prize_pool, prize_pool_entry, prize_pool_vote tables.
Run from backend directory: python add_prize_pool_tables.py [path/to/site.db]
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

# Check existing tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = {r[0] for r in cur.fetchall()}

if 'prize_pool' not in tables:
    cur.execute("""
        CREATE TABLE prize_pool (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) NOT NULL DEFAULT 'open',
            title VARCHAR(200) NOT NULL,
            description TEXT,
            technologies_required VARCHAR(500),
            pool_type VARCHAR(20) NOT NULL DEFAULT 'paid',
            entry_fee_gbp REAL,
            signup_ends_at DATETIME NOT NULL,
            submission_ends_at DATETIME NOT NULL,
            voting_ends_at DATETIME,
            review_ends_at DATETIME,
            max_participants INTEGER,
            created_by_id INTEGER,
            FOREIGN KEY (created_by_id) REFERENCES user(id)
        )
    """)
    print('Created prize_pool table.')
else:
    print('prize_pool table already exists.')
    # Fix: add created_by_id if missing (old migration used created_by)
    cur.execute("PRAGMA table_info(prize_pool)")
    cols = {r[1] for r in cur.fetchall()}
    if 'created_by_id' not in cols:
        cur.execute("ALTER TABLE prize_pool ADD COLUMN created_by_id INTEGER REFERENCES user(id)")
        if 'created_by' in cols:
            cur.execute("UPDATE prize_pool SET created_by_id = created_by")
        print('Added created_by_id column.')

if 'prize_pool_entry' not in tables:
    cur.execute("""
        CREATE TABLE prize_pool_entry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prize_pool_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            payment_intent_id VARCHAR(255),
            payment_completed_at DATETIME,
            demo_video_url VARCHAR(500),
            github_submission_url VARCHAR(500),
            submitted_at DATETIME,
            is_winner BOOLEAN DEFAULT 0,
            ai_review_result VARCHAR(20),
            FOREIGN KEY (prize_pool_id) REFERENCES prize_pool(id),
            FOREIGN KEY (user_id) REFERENCES user(id),
            UNIQUE(prize_pool_id, user_id)
        )
    """)
    print('Created prize_pool_entry table.')
else:
    print('prize_pool_entry table already exists.')

if 'prize_pool_vote' not in tables:
    cur.execute("""
        CREATE TABLE prize_pool_vote (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prize_pool_id INTEGER NOT NULL,
            voter_id INTEGER NOT NULL,
            entry_1_id INTEGER NOT NULL,
            entry_2_id INTEGER NOT NULL,
            entry_3_id INTEGER NOT NULL,
            rank_1_id INTEGER NOT NULL,
            rank_2_id INTEGER NOT NULL,
            rank_3_id INTEGER NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (prize_pool_id) REFERENCES prize_pool(id),
            FOREIGN KEY (voter_id) REFERENCES user(id),
            FOREIGN KEY (entry_1_id) REFERENCES prize_pool_entry(id),
            FOREIGN KEY (entry_2_id) REFERENCES prize_pool_entry(id),
            FOREIGN KEY (entry_3_id) REFERENCES prize_pool_entry(id),
            FOREIGN KEY (rank_1_id) REFERENCES prize_pool_entry(id),
            FOREIGN KEY (rank_2_id) REFERENCES prize_pool_entry(id),
            FOREIGN KEY (rank_3_id) REFERENCES prize_pool_entry(id),
            UNIQUE(prize_pool_id, voter_id)
        )
    """)
    print('Created prize_pool_vote table.')
else:
    print('prize_pool_vote table already exists.')

conn.commit()
conn.close()
print('Done.')
