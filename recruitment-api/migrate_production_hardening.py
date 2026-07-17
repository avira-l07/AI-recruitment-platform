"""Idempotent SQLite migration for existing RecruitAI databases.

Back up recruitment.db before running:
    copy recruitment.db recruitment.backup.db
    python migrate_production_hardening.py

New installations should use Alembic (`alembic upgrade head`). This script exists
only to migrate databases created by older RecruitAI versions.
"""

import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.getenv("SQLITE_DB_PATH", "recruitment.db")


def columns(cursor, table):
    return {row[1] for row in cursor.execute(f"PRAGMA table_info({table})").fetchall()}


def add_column(cursor, table, definition):
    name = definition.split()[0]
    if name not in columns(cursor, table):
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")
        print(f"Added {table}.{name}")


def main():
    if not os.path.exists(DB_PATH):
        raise SystemExit(f"Database not found: {DB_PATH}")

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys=OFF")

    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'Applied',
            applied_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            reviewed_by INTEGER,
            reviewed_at DATETIME,
            rejection_reason TEXT,
            withdrawn_at DATETIME,
            FOREIGN KEY(candidate_id) REFERENCES candidates(id),
            FOREIGN KEY(job_id) REFERENCES jobs(id),
            FOREIGN KEY(reviewed_by) REFERENCES users(id),
            CONSTRAINT uq_application_candidate_job UNIQUE(candidate_id, job_id)
        );

        CREATE TABLE IF NOT EXISTS ai_analysis_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER,
            candidate_id INTEGER,
            job_id INTEGER,
            operation VARCHAR NOT NULL DEFAULT 'candidate_job_match',
            requested_mode VARCHAR NOT NULL DEFAULT 'hybrid',
            actual_mode VARCHAR,
            current_stage VARCHAR NOT NULL DEFAULT 'queued',
            local_status VARCHAR NOT NULL DEFAULT 'waiting',
            gemini_status VARCHAR NOT NULL DEFAULT 'waiting',
            hybrid_status VARCHAR NOT NULL DEFAULT 'waiting',
            fallback_active BOOLEAN NOT NULL DEFAULT 0,
            fallback_reason TEXT,
            error_code VARCHAR,
            error_message TEXT,
            safe_error_message TEXT,
            duration_seconds FLOAT,
            started_at DATETIME,
            completed_at DATETIME,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            FOREIGN KEY(application_id) REFERENCES applications(id)
        );

        CREATE TABLE IF NOT EXISTS ai_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_job_id INTEGER,
            user_id INTEGER,
            event_type VARCHAR NOT NULL,
            message TEXT NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'info',
            created_at DATETIME NOT NULL,
            FOREIGN KEY(analysis_job_id) REFERENCES ai_analysis_jobs(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title VARCHAR NOT NULL,
            message TEXT NOT NULL,
            type VARCHAR NOT NULL DEFAULT 'info',
            related_entity_type VARCHAR,
            related_entity_id INTEGER,
            is_read BOOLEAN NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL,
            read_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """
    )

    if "jobs" in {row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}:
        for definition in [
            "status VARCHAR DEFAULT 'Active'",
            "closed_reason TEXT",
            "closed_at DATETIME",
        ]:
            add_column(cursor, "jobs", definition)

    if "ai_analysis_jobs" in {row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}:
        for definition in [
            "safe_error_message TEXT",
        ]:
            add_column(cursor, "ai_analysis_jobs", definition)

    match_columns = columns(cursor, "match_scores")
    additions = [
        "application_id INTEGER",
        "fit_label VARCHAR",
        "confidence_score FLOAT",
        "confidence_label VARCHAR",
        "ai_source VARCHAR DEFAULT 'local_ai'",
        "local_completed BOOLEAN DEFAULT 1",
        "gemini_completed BOOLEAN DEFAULT 0",
        "hybrid_completed BOOLEAN DEFAULT 0",
        "fallback_active BOOLEAN DEFAULT 0",
        "fallback_reason TEXT",
        "updated_at DATETIME",
    ]
    for definition in additions:
        add_column(cursor, "match_scores", definition)

    rows = cursor.execute(
        "SELECT id, candidate_id, job_id, status, created_at, explanation FROM match_scores"
    ).fetchall()
    for match_id, candidate_id, job_id, old_status, created_at, explanation in rows:
        applied_at = created_at or datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        status = old_status or "Manual Review"
        cursor.execute(
            """
            INSERT OR IGNORE INTO applications
            (candidate_id, job_id, status, applied_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (candidate_id, job_id, status, applied_at, applied_at),
        )
        application_id = cursor.execute(
            "SELECT id FROM applications WHERE candidate_id=? AND job_id=?",
            (candidate_id, job_id),
        ).fetchone()[0]

        ai_source = "local_ai"
        if explanation and "gemini_text_enhanced" in explanation:
            ai_source = "hybrid"
        elif explanation and "hybrid_local_ai" in explanation:
            ai_source = "local_ai"

        cursor.execute(
            """
            UPDATE match_scores
            SET application_id=?, ai_source=?,
                local_completed=1,
                gemini_completed=?,
                hybrid_completed=?,
                updated_at=COALESCE(updated_at, created_at)
            WHERE id=?
            """,
            (
                application_id,
                ai_source,
                1 if ai_source == "hybrid" else 0,
                1 if ai_source == "hybrid" else 0,
                match_id,
            ),
        )

    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_match_score_application ON match_scores(application_id)"
    )
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_application_candidate_job_idx ON applications(candidate_id, job_id)"
    )
    connection.commit()
    connection.close()
    print("Production-hardening migration completed successfully.")


if __name__ == "__main__":
    main()
