from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.match_score import MatchScore
from app.models.resume import Resume
from app.api.dependencies import require_roles
from collections import Counter

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/overview")
def get_overview(db: Session = Depends(get_db), current_user = Depends(require_roles(["hr"]))):
    total_candidates = db.query(Candidate).count()
    total_jobs = db.query(Job).count()
    shortlisted = db.query(MatchScore).filter(MatchScore.status == "Shortlisted").count()
    rejected = db.query(MatchScore).filter(MatchScore.status == "Rejected").count()
    
    avg_score_raw = db.query(func.avg(MatchScore.score)).scalar()
    average_match_score = round(avg_score_raw, 1) if avg_score_raw else 0.0
    
    strong = db.query(MatchScore).filter(MatchScore.score >= 70).count()
    moderate = db.query(MatchScore).filter(MatchScore.score >= 40, MatchScore.score < 70).count()
    weak = db.query(MatchScore).filter(MatchScore.score < 40).count()
    
    all_candidates = db.query(Candidate.skills).all()
    skill_counter = Counter()
    for row in all_candidates:
        if row[0]:
            skills = [s.strip() for s in row[0].split(',') if s.strip()]
            skill_counter.update(skills)
            
    top_skills = [skill for skill, count in skill_counter.most_common(8)]
    
    return {
        "total_candidates": total_candidates,
        "total_jobs": total_jobs,
        "shortlisted_candidates": shortlisted,
        "rejected_candidates": rejected,
        "average_match_score": average_match_score,
        "top_skills": top_skills,
        "score_distribution": {
            "strong": strong,
            "moderate": moderate,
            "weak": weak
        }
    }

@router.get("/ai-status")
def get_ai_status(db: Session = Depends(get_db), current_user = Depends(require_roles(["hr"]))):
    total_resumes = db.query(Resume).count()
    completed = db.query(Resume).filter(Resume.status == "completed").count()
    generating = db.query(Resume).filter(Resume.status == "generating").count()
    failed = db.query(Resume).filter(Resume.status == "failed").count()
    not_generated = db.query(Resume).filter(Resume.status == "not_generated").count()
    
    quota_exceeded = db.query(Resume).filter(Resume.error_type == "quota_exceeded").count()
    timeouts = db.query(Resume).filter(Resume.error_type == "timeout").count()
    malformed = db.query(Resume).filter(Resume.error_type == "malformed_response").count()
    
    return {
        "engine": "Gemini-2.5-Flash (Hybrid Mode)",
        "total_resumes_tracked": total_resumes,
        "completed_analyses": completed,
        "active_generations": generating,
        "failed_analyses": failed,
        "not_generated_resumes": not_generated,
        "errors": {
            "quota_exceeded": quota_exceeded,
            "timeouts": timeouts,
            "malformed_responses": malformed
        }
    }

import json
import asyncio
from fastapi.responses import StreamingResponse
from app.models.activity_event import ActivityEvent
from app.core.database import SessionLocal

@router.get("/events")
def get_events(limit: int = 50, db: Session = Depends(get_db), current_user = Depends(require_roles(["hr"]))):
    events = db.query(ActivityEvent).order_by(ActivityEvent.id.desc()).limit(limit).all()
    result = []
    for e in events:
        try:
            details = json.loads(e.details_json or "{}") if e.details_json else {}
        except Exception:
            details = {}
        result.append({
            "id": e.id,
            "event_type": e.event_type,
            "candidate_id": e.candidate_id,
            "user_id": e.user_id,
            "details": details,
            "created_at": e.created_at.isoformat()
        })
    return result

@router.get("/events/stream")
def stream_events(request: Request, last_event_id: int = 0, current_user = Depends(require_roles(["hr"]))):
    async def event_generator():
        last_seen_id = last_event_id
        yield ": keepalive\n\n"
        while True:
            db = SessionLocal()
            try:
                events = db.query(ActivityEvent).filter(ActivityEvent.id > last_seen_id).order_by(ActivityEvent.id.asc()).all()
                for e in events:
                    last_seen_id = e.id
                    try:
                        details = json.loads(e.details_json or "{}") if e.details_json else {}
                    except Exception:
                        details = {}
                    payload = {
                        "id": e.id,
                        "event_type": e.event_type,
                        "candidate_id": e.candidate_id,
                        "user_id": e.user_id,
                        "details": details,
                        "created_at": e.created_at.isoformat()
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
            except Exception as ex:
                print(f"SSE loop error: {ex}")
            finally:
                db.close()
            
            if await request.is_disconnected() or request.headers.get("x-test-single-run") == "true":
                break
            await asyncio.sleep(0.5)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")
