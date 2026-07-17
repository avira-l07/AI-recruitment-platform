import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.activity_event import ActivityEvent

def publish_event(
    db: Session,
    event_type: str,
    candidate_id: int | None,
    user_id: int | None,
    details: dict,
    resume_id: int | None = None,
    job_id: int | None = None
):
    try:
        event = ActivityEvent(
            event_type=event_type,
            candidate_id=candidate_id,
            user_id=user_id,
            resume_id=resume_id,
            job_id=job_id,
            details_json=json.dumps(details),
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        db.add(event)
        db.flush()
        return event
    except Exception as e:
        print(f"Error publishing activity event: {e}")
        return None
