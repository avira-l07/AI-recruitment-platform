import json
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.ai.gemini_client import call_gemini_json, get_gemini_health
from app.core.database import get_db
from app.core.dependencies import require_hr
from app.core.rate_limit import rate_limiter
from app.models.ai_analysis import AIAnalysisJob
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.match_score import MatchScore
from app.models.user import User
from app.schemas.production_schema import RecruiterAssistantRequest
from app.services.blind_screening import is_blind_mode_requested, get_neutral_candidate_identifier, redact_text_pii

router = APIRouter(prefix="/ai", tags=["ai"])


def _provider_status_from_job(job: AIAnalysisJob | None, field: str, default: str) -> str:
    return getattr(job, field, None) or default


@router.get("/status")
def get_ai_status(db: Session = Depends(get_db), _: User = Depends(require_hr)):
    latest = db.query(AIAnalysisJob).order_by(AIAnalysisJob.updated_at.desc()).first()
    health = get_gemini_health()
    average_duration = db.query(func.avg(AIAnalysisJob.duration_seconds)).filter(
        AIAnalysisJob.duration_seconds.isnot(None)
    ).scalar()

    gemini_status = _provider_status_from_job(latest, "gemini_status", health.get("status", "not_configured"))
    if not health.get("configured"):
        gemini_status = "not_configured"
    elif not latest or latest.current_stage in {"completed", "fallback_completed", "failed"}:
        if health.get("status") in {"available", "not_configured", "configured_not_tested", "rate_limited", "authentication_failed", "temporarily_unavailable", "request_failed", "timeout", "invalid_response"}:
            gemini_status = health.get("status")

    return {
        "mode": latest.actual_mode if latest and latest.actual_mode else "idle",
        "current_stage": latest.current_stage if latest else "idle",
        "local_ai": {
            "status": _provider_status_from_job(latest, "local_status", "available"),
            "available": True,
        },
        "gemini": {
            "status": gemini_status,
            "available": health.get("status") == "available",
            "configured": health.get("configured", False),
            "last_success_at": health.get("last_success_at"),
            "last_failure_at": health.get("last_failure_at"),
            "error_code": health.get("last_error_code"),
        },
        "hybrid": {
            "status": _provider_status_from_job(latest, "hybrid_status", "idle"),
        },
        "fallback_active": bool(latest.fallback_active) if latest else False,
        "fallback_reason": latest.fallback_reason if latest else None,
        "analysis_id": latest.id if latest else None,
        "average_analysis_time": round(float(average_duration), 2) if average_duration is not None else None,
        "last_updated": latest.updated_at if latest else utc_now(),
    }


@router.get("/jobs/{analysis_id}")
def get_analysis_job(
    analysis_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_hr),
):
    job = db.query(AIAnalysisJob).filter(AIAnalysisJob.id == analysis_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="AI analysis job not found.")
    return {
        column.name: getattr(job, column.name)
        for column in AIAnalysisJob.__table__.columns
    }


def _ground_recruiter_answer(message: str, db: Session, hr_user: User, blind: bool = False):
    lower = message.lower()
    actions = []

    if any(word in lower for word in ["best", "top", "strongest", "candidate"]):
        rows = (
            db.query(Application, MatchScore, Candidate, Job)
            .join(MatchScore, MatchScore.application_id == Application.id)
            .join(Candidate, Application.candidate_id == Candidate.id)
            .join(Job, Application.job_id == Job.id)
            .filter(Job.created_by == hr_user.id)
            .order_by(MatchScore.score.desc())
            .limit(5)
            .all()
        )
        if not rows:
            return "There are no analyzed applications yet.", [], {"candidates": []}
        facts = []
        for application, match, candidate, job in rows:
            display_name = get_neutral_candidate_identifier(candidate.id) if blind else candidate.full_name
            facts.append({
                "candidate_id": candidate.id,
                "name": display_name,
                "job": job.title,
                "score": match.score,
                "status": application.status,
                "ai_source": match.ai_source,
            })
            actions.append({"type": "open_candidate", "candidate_id": candidate.id, "label": f"View {display_name}"})
        answer = "Top analyzed candidates: " + "; ".join(
            f"{f['name']} — {f['job']} ({round(f['score'])}%, {f['status']})" for f in facts
        )
        return answer, actions, {"candidates": facts}

    if "job" in lower:
        jobs = db.query(Job).filter(Job.created_by == hr_user.id).order_by(Job.created_at.desc()).limit(8).all()
        active = [job for job in jobs if job.status == "Active"]
        answer = f"There are {len(active)} active jobs."
        actions = [{"type": "open_job", "job_id": job.id, "label": f"Open {job.title}"} for job in active[:5]]
        return answer, actions, {"active_jobs": [{"id": j.id, "title": j.title} for j in active]}

    total = db.query(Application).join(Job, Application.job_id == Job.id).filter(Job.created_by == hr_user.id).count()
    manual = db.query(Application).join(Job, Application.job_id == Job.id).filter(Job.created_by == hr_user.id, Application.status == "Manual Review").count()
    shortlisted = db.query(Application).join(Job, Application.job_id == Job.id).filter(Job.created_by == hr_user.id, Application.status == "Shortlisted").count()
    answer = f"Recruitment overview: {total} applications, {manual} awaiting manual review, and {shortlisted} shortlisted."
    return answer, [], {"total_applications": total, "manual_review": manual, "shortlisted": shortlisted}


@router.post(
    "/recruiter",
    dependencies=[Depends(rate_limiter.dependency(20, 3600, "ai_recruiter"))],
)
def ask_recruiter(
    request: Request,
    payload: RecruiterAssistantRequest,
    blind_mode: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr),
):
    blind = is_blind_mode_requested(request, blind_mode, current_user)
    grounded_answer, actions, facts = _ground_recruiter_answer(payload.message, db, current_user, blind=blind)
    source = "local_ai"
    prompt = f"""
You are RecruitAI, an HR decision-support assistant. Use only the supplied database facts.
Do not invent people, scores, counts, jobs, or hiring decisions. Keep the response under 120 words.
{"In Blind Review Mode, always refer to candidates by their Neutral Identifier (e.g. Candidate #C-123) and never reveal personal names." if blind else ""}
User question: {payload.message}
Database facts: {json.dumps(facts, ensure_ascii=False)}
Deterministic answer: {grounded_answer}
Return JSON only: {{"answer": "clear HR response"}}
"""
    enhanced = call_gemini_json(prompt)
    health = get_gemini_health()
    answer = grounded_answer
    if enhanced and enhanced.get("answer"):
        answer = str(enhanced["answer"]).strip()
        source = "hybrid"
    elif health.get("configured") and health.get("status") != "available":
        source = "local_fallback"

    if blind:
        answer = redact_text_pii(answer)

    return {
        "answer": answer,
        "source": source,
        "conversation_id": payload.conversation_id or uuid4().hex,
        "actions": actions,
        "is_blind_mode": blind,
    }
