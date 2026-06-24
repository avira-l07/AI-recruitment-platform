import sqlite3

conn = sqlite3.connect("recruitment.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(jobs)")
existing_columns = [row[1] for row in cursor.fetchall()]

if "status" not in existing_columns:
    cursor.execute("ALTER TABLE jobs ADD COLUMN status TEXT DEFAULT 'Active'")
    print("Added column: status")
else:
    print("Column 'status' already exists, skipping")

if "closed_reason" not in existing_columns:
    cursor.execute("ALTER TABLE jobs ADD COLUMN closed_reason TEXT")
    print("Added column: closed_reason")
else:
    print("Column 'closed_reason' already exists, skipping")

if "closed_at" not in existing_columns:
    cursor.execute("ALTER TABLE jobs ADD COLUMN closed_at TEXT")
    print("Added column: closed_at")
else:
    print("Column 'closed_at' already exists, skipping")

cursor.execute("UPDATE jobs SET status = 'Active' WHERE status IS NULL")

conn.commit()
conn.close()

print("Migration complete.")