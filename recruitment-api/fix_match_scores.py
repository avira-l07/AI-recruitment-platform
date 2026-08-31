"""Fix match_scores table to add missing columns from the restored backup database."""
from sqlalchemy import create_engine, inspect, text

engine = create_engine("sqlite:///./recruitment.db")
insp = inspect(engine)
existing = [c["name"] for c in insp.get_columns("match_scores")]
print("Existing match_scores columns:", existing)

needed = [
    ("application_id", "INTEGER"),
    ("fit_label", "VARCHAR"),
    ("confidence_score", "FLOAT"),
    ("confidence_label", "VARCHAR"),
    ("ai_source", "VARCHAR DEFAULT 'local_ai'"),
    ("local_completed", "BOOLEAN DEFAULT 1"),
    ("gemini_completed", "BOOLEAN DEFAULT 0"),
    ("hybrid_completed", "BOOLEAN DEFAULT 0"),
    ("fallback_active", "BOOLEAN DEFAULT 0"),
    ("fallback_reason", "TEXT"),
    ("updated_at", "DATETIME"),
]

with engine.connect() as conn:
    for col, dtype in needed:
        if col not in existing:
            conn.execute(text(f"ALTER TABLE match_scores ADD COLUMN {col} {dtype}"))
            print(f"Added column: {col}")
        else:
            print(f"Already exists: {col}")
    conn.commit()

print("Done. Final columns:", [c["name"] for c in inspect(engine).get_columns("match_scores")])
