import sqlite3

def run_migration():
    conn = sqlite3.connect("recruitment.db")
    cursor = conn.cursor()

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
    conn.commit()
    conn.close()
    print("ActivityEvent table migration complete.")

if __name__ == "__main__":
    run_migration()
