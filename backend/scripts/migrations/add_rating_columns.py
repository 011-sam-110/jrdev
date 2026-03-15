"""One-off script: add rating and prototypes_completed columns if missing."""
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

# developer_profile.prototypes_completed
cur.execute('PRAGMA table_info(developer_profile)')
cols = [row[1] for row in cur.fetchall()]
if 'prototypes_completed' not in cols:
    cur.execute('ALTER TABLE developer_profile ADD COLUMN prototypes_completed INTEGER DEFAULT 0')
    conn.commit()
    print('Added developer_profile.prototypes_completed.')
else:
    print('developer_profile.prototypes_completed already exists.')

# listing_signup.business_rating_of_developer, developer_rating_of_business
cur.execute('PRAGMA table_info(listing_signup)')
cols = [row[1] for row in cur.fetchall()]
for col in ('business_rating_of_developer', 'developer_rating_of_business'):
    if col not in cols:
        cur.execute(f'ALTER TABLE listing_signup ADD COLUMN {col} INTEGER')
        conn.commit()
        print(f'Added listing_signup.{col}.')
    else:
        print(f'listing_signup.{col} already exists.')

conn.close()
