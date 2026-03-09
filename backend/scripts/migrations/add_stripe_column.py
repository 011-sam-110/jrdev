"""One-off script: add stripe_customer_id to user table if missing."""
import sqlite3
import os

# Default Flask instance path
instance_path = os.path.join(os.path.dirname(__file__), 'instance')
db_path = os.path.join(instance_path, 'site.db')
if not os.path.exists(db_path):
    db_path = os.path.join(os.path.dirname(__file__), 'site.db')
if not os.path.exists(db_path):
    print('Database not found at', db_path)
    exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute('PRAGMA table_info(user)')
columns = [row[1] for row in cur.fetchall()]
if 'stripe_customer_id' in columns:
    print('Column user.stripe_customer_id already exists.')
else:
    cur.execute('ALTER TABLE user ADD COLUMN stripe_customer_id VARCHAR(120)')
    conn.commit()
    print('Added column user.stripe_customer_id.')
conn.close()
