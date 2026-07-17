import sqlite3

def run_migration():
    conn = sqlite3.connect("recruitment.db")
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(resumes)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    new_columns = [
        ("resume_hash", "TEXT"),
        ("local_analysis_json", "TEXT"),
        ("gemini_analysis_json", "TEXT"),
        ("combined_analysis_json", "TEXT"),
        ("analysis_source", "TEXT DEFAULT 'local'"),
        ("status", "TEXT DEFAULT 'not_generated'"),
        ("error_type", "TEXT"),
        ("safe_error_message", "TEXT"),
        ("gemini_model", "TEXT"),
        ("generation_started_at", "TEXT"),
        ("generation_completed_at", "TEXT"),
        ("last_attempt_at", "TEXT"),
        ("last_success_at", "TEXT"),
        ("created_at", "TEXT"),
        ("updated_at", "TEXT")
    ]

    for col_name, col_type in new_columns:
        if col_name not in existing_columns:
            cursor.execute(f"ALTER TABLE resumes ADD COLUMN {col_name} {col_type}")
            print(f"Added column: {col_name}")
        else:
            print(f"Column '{col_name}' already exists, skipping")

    # Set default values for any rows
    cursor.execute("UPDATE resumes SET status = 'not_generated' WHERE status IS NULL")
    cursor.execute("UPDATE resumes SET analysis_source = 'local' WHERE analysis_source IS NULL")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    run_migration()
