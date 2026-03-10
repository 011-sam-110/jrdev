"""
Migration: add business_demo_confirmed_at to listing_signup
           and deposit_payment_intent_id to sprint_listing.
Run once: python add_demo_confirmed_deposit.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'site.db')

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

if not column_exists(cur, 'listing_signup', 'business_demo_confirmed_at'):
    cur.execute("ALTER TABLE listing_signup ADD COLUMN business_demo_confirmed_at DATETIME")
    print("Added listing_signup.business_demo_confirmed_at")
else:
    print("listing_signup.business_demo_confirmed_at already exists")

if not column_exists(cur, 'sprint_listing', 'deposit_payment_intent_id'):
    cur.execute("ALTER TABLE sprint_listing ADD COLUMN deposit_payment_intent_id VARCHAR(120)")
    print("Added sprint_listing.deposit_payment_intent_id")
else:
    print("sprint_listing.deposit_payment_intent_id already exists")

conn.commit()
conn.close()
print("Done.")
