"""Add developer_withdrew column to listing_signup table."""
import sqlite3, os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'site.db')
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cols = [row[1] for row in cur.execute("PRAGMA table_info(listing_signup)").fetchall()]

if 'developer_withdrew' not in cols:
    cur.execute("ALTER TABLE listing_signup ADD COLUMN developer_withdrew BOOLEAN DEFAULT 0")
    print("Added developer_withdrew")
else:
    print("developer_withdrew already exists")

conn.commit()
conn.close()
print("Done.")
