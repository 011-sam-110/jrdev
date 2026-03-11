"""Add signing_deadline_at column to listing_signup table."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '../../instance/site.db')

def run():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(listing_signup)")
    cols = [row[1] for row in cur.fetchall()]
    if 'signing_deadline_at' not in cols:
        cur.execute("ALTER TABLE listing_signup ADD COLUMN signing_deadline_at DATETIME")
        conn.commit()
        print("Added signing_deadline_at column.")
    else:
        print("Column already exists.")
    conn.close()

if __name__ == '__main__':
    run()
