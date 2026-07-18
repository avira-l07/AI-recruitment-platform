from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.match_score import MatchScore
from app.models.resume import Resume
from app.models.application import Application
from app.models.ai_analysis import AIAnalysisJob
from app.core.dependencies import require_roles
from collections import Counter

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _pipeline(db: Session, hr_id: int) -> dict:
    statuses = {
        name: db.query(Application).join(Job, Application.job_id == Job.id).filter(Job.created_by == hr_id, Application.status == name).count()
        for name in [
            "Applied",
            "AI Review",
            "Manual Review",
            "Shortlisted",
            "Interview",
            "Offer",
            "Hired",
            "Rejected",
            "Withdrawn",
        ]
    }
    total_applied = db.query(Application).join(Job, Application.job_id == Job.id).filter(Job.created_by == hr_id).count()
    total_ai_review = db.query(MatchScore).join(Job, MatchScore.job_id == Job.id).filter(Job.created_by == hr_id).count()
    return {
        "applied": total_applied,
        "ai_review": total_ai_review,
        "manual_review": statuses["Manual Review"],
        "shortlisted": statuses["Shortlisted"],
        "interview": statuses["Interview"],
        "offer": statuses["Offer"],
        "hired": statuses["Hired"],
        "rejected": statuses["Rejected"],
        "withdrawn": statuses["Withdrawn"],
    }


@router.get("/pipeline")
def get_pipeline(db: Session = Depends(get_db), current_user = Depends(require_roles(["hr"]))):
    return _pipeline(db, current_user.id)


@router.get("/overview")
def get_overview(db: Session = Depends(get_db), current_user = Depends(require_roles(["hr"]))):
    hr_id = current_user.id
    
    total_candidates = db.query(Candidate).join(Application, Candidate.id == Application.candidate_id).join(Job, Application.job_id == Job.id).filter(Job.created_by == hr_id).distinct().count()
    total_jobs = db.query(Job).filter(Job.created_by == hr_id).count()
    active_jobs = db.query(Job).filter(Job.created_by == hr_id, Job.status == "Active").count()
    total_applications = db.query(Application).join(Job, Application.job_id == Job.id).filter(Job.created_by == hr_id).count()

    avg_score_raw = db.query(func.avg(MatchScore.score)).join(Job, MatchScore.job_id == Job.id).filter(Job.created_by == hr_id).scalar()
    average_match_score = round(float(avg_score_raw), 1) if avg_score_raw is not None else 0.0
    avg_confidence_raw = db.query(func.avg(MatchScore.confidence_score)).join(Job, MatchScore.job_id == Job.id).filter(Job.created_by == hr_id).scalar()
    average_confidence = round(float(avg_confidence_raw), 1) if avg_confidence_raw is not None else None

    strong = db.query(MatchScore).join(Job, MatchScore.job_id == Job.id).filter(Job.created_by == hr_id, MatchScore.score >= 70).count()
    moderate = db.query(MatchScore).join(Job, MatchScore.job_id == Job.id).filter(Job.created_by == hr_id, MatchScore.score >= 40, MatchScore.score < 70).count()
    weak = db.query(MatchScore).join(Job, MatchScore.job_id == Job.id).filter(Job.created_by == hr_id, MatchScore.score < 40).count()

    skill_counter = Counter()
    skills_list = db.query(Candidate.skills).join(Application, Candidate.id == Application.candidate_id).join(Job, Application.job_id == Job.id).filter(Job.created_by == hr_id).all()
    for (skills_text,) in skills_list:
        if skills_text:
            skill_counter.update(s.strip() for s in skills_text.split(",") if s.strip())

    pipeline = _pipeline(db, hr_id)
    hybrid_analyses = db.query(MatchScore).join(Job, MatchScore.job_id == Job.id).filter(Job.created_by == hr_id, MatchScore.ai_source == "hybrid").count()
    fallback_analyses = db.query(MatchScore).join(Job, MatchScore.job_id == Job.id).filter(Job.created_by == hr_id, MatchScore.fallback_active.is_(True)).count()
    
    gemini_failures = db.query(AIAnalysisJob).join(Job, AIAnalysisJob.job_id == Job.id).filter(
        Job.created_by == hr_id,
        AIAnalysisJob.gemini_status.in_(["failed", "rate_limited", "authentication_failed", "unavailable"])
    ).count()
    completed_analyses = db.query(AIAnalysisJob).join(Job, AIAnalysisJob.job_id == Job.id).filter(
        Job.created_by == hr_id,
        AIAnalysisJob.current_stage.in_(["completed", "fallback_completed"])
    ).count()

    return {
        "total_candidates": total_candidates,
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "total_applications": total_applications,
        "shortlisted_candidates": pipeline["shortlisted"],
        "rejected_candidates": pipeline["rejected"],
        "interviews": pipeline["interview"],
        "offers": pipeline["offer"],
        "hired": pipeline["hired"],
        "manual_review": pipeline["manual_review"],
        "ai_analyses_completed": completed_analyses,
        "hybrid_analyses": hybrid_analyses,
        "fallback_analyses": fallback_analyses,
        "gemini_failures": gemini_failures,
        "average_match_score": average_match_score,
        "average_confidence": average_confidence,
        "top_skills": [skill for skill, _ in skill_counter.most_common(8)],
        "score_distribution": {"strong": strong, "moderate": moderate, "weak": weak},
        "pipeline": pipeline,
    }

@router.get("/ai-status")
def get_ai_status(db: Session = Depends(get_db), current_user = Depends(require_roles(["hr"]))):
    hr_id = current_user.id
    
    total_resumes = db.query(Resume).join(Candidate, Resume.candidate_id == Candidate.id).join(Application, Candidate.id == Application.candidate_id).join(Job, Application.job_id == Job.id).filter(Job.created_by == hr_id).distinct().count()
    completed = db.query(Resume).join(Candidate, Resume.candidate_id == Candidate.id).join(Application, Candidate.id == Application.candidate_id).join(Job, Application.job_id == Job.id).filter(Job.created_by == hr_id, Resume.status == "completed").distinct().count()
    generating = db.query(Resume).join(Candidate, Resume.candidate_id == Candidate.id).join(Application, Candidate.id == Application.candidate_id).join(Job, Application.job_id == Job.id).filter(Job.created_by == hr_id, Resume.status == "generating").distinct().count()
    failed = db.query(Resume).join(Candidate, Resume.candidate_id == Candidate.id).join(Application, Candidate.id == Application.candidate_id).join(Job, Application.job_id == Job.id).filter(Job.created_by == hr_id, Resume.status == "failed").distinct().count()
    not_generated = db.query(Resume).join(Candidate, Resume.candidate_id == Candidate.id).join(Application, Candidate.id == Application.candidate_id).join(Job, Application.job_id == Job.id).filter(Job.created_by == hr_id, Resume.status == "not_generated").distinct().count()
    
    quota_exceeded = db.query(Resume).join(Candidate, Resume.candidate_id == Candidate.id).join(Application, Candidate.id == Application.candidate_id).join(Job, Application.job_id == Job.id).filter(Job.created_by == hr_id, Resume.error_type == "quota_exceeded").distinct().count()
    timeouts = db.query(Resume).join(Candidate, Resume.candidate_id == Candidate.id).join(Application, Candidate.id == Application.candidate_id).join(Job, Application.job_id == Job.id).filter(Job.created_by == hr_id, Resume.error_type == "timeout").distinct().count()
    malformed = db.query(Resume).join(Candidate, Resume.candidate_id == Candidate.id).join(Application, Candidate.id == Application.candidate_id).join(Job, Application.job_id == Job.id).filter(Job.created_by == hr_id, Resume.error_type == "malformed_response").distinct().count()
    
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
