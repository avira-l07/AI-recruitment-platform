"""Scope activity feeds and re-check long-lived stream sessions."""
import json
from sqlalchemy import or_
from app.core.ownership import hr_candidate_query
from app.core.security import verify_token
from app.models.activity_event import ActivityEvent
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.user import User
from app.services.blind_screening import is_blind_mode_requested, sanitize_list_or_text


def visible_events(db, user):
    query = db.query(ActivityEvent)
    if user.role == "hr":
        jobs = db.query(Job.id).filter(Job.created_by == user.id)
        query = query.filter(or_(
            ActivityEvent.job_id.in_(jobs),
            ActivityEvent.job_id.is_(None) & ActivityEvent.candidate_id.in_(hr_candidate_query(db, user.id)),
            ActivityEvent.user_id == user.id,
        ))
    elif user.role == "candidate":
        ids = db.query(Candidate.id).filter(Candidate.user_id == user.id)
        query = query.filter(or_(ActivityEvent.candidate_id.in_(ids), ActivityEvent.user_id == user.id))
    elif user.role != "admin":
        query = query.filter(False)
    return query


def serialize_event(db, event, user, request):
    try:
        details = json.loads(event.details_json or "{}")
    except (ValueError, TypeError):
        details = {}
    result = {
        "id": event.id, "event_type": event.event_type,
        "candidate_id": event.candidate_id, "user_id": event.user_id,
        "details": details, "created_at": event.created_at.isoformat(),
    }
    if user.role == "hr" and is_blind_mode_requested(request, None, user):
        candidate = db.query(Candidate).filter(Candidate.id == event.candidate_id).first()
        if candidate:
            result = sanitize_list_or_text(result, candidate_name=candidate.full_name, candidate_id=candidate.id, email=candidate.email, phone=candidate.phone)
        result["user_id"] = None
        if isinstance(result["details"], dict) and "file_name" in result["details"]:
            result["details"]["file_name"] = "Resume [Concealed]"
    return result


def stream_session_valid(db, user, request):
    current = db.query(User).filter(User.id == user.id).first()
    token = request.headers.get("authorization", "").split(" ", 1)[-1]
    return bool(current and current.is_active and not current.must_change_password
                and current.token_version == user.token_version and verify_token(token))
