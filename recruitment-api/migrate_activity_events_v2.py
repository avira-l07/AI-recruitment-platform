import sqlite3

def run_migration():
    conn = sqlite3.connect("recruitment.db")
    cursor = conn.cursor()

    # Create table if not exists first
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type VARCHAR(100) NOT NULL,
            candidate_id INTEGER,
            user_id INTEGER,
            details_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Try adding new columns if they do not exist
    try:
        cursor.execute("ALTER TABLE activity_events ADD COLUMN resume_id INTEGER;")
        print("Added resume_id column.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("resume_id column already exists.")
        else:
            raise e

    try:
        cursor.execute("ALTER TABLE activity_events ADD COLUMN job_id INTEGER;")
        print("Added job_id column.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("job_id column already exists.")
        else:
            raise e

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_events_created_at ON activity_events(created_at);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_events_event_type ON activity_events(event_type);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_events_candidate_id ON activity_events(candidate_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_events_resume_id ON activity_events(resume_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_events_job_id ON activity_events(job_id);")
    print("Created database indexes.")

    conn.commit()
    conn.close()
    print("ActivityEvent table migration v2 complete.")

if __name__ == "__main__":
    run_migration()
