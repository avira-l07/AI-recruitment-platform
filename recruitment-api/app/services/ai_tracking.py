from datetime import datetime
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.models.ai_analysis import AIAnalysisJob
from app.models.activity_event import ActivityEvent
from app.utils.activity_logger import publish_event


def add_activity(
    db: Session,
    event_type: str,
    message: str,
    status: str = "info",
    analysis_job_id: int | None = None,
    user_id: int | None = None,
) -> ActivityEvent:
    candidate_id = None
    job_id = None
    if analysis_job_id:
        job_record = db.query(AIAnalysisJob).filter(AIAnalysisJob.id == analysis_job_id).first()
        if job_record:
            candidate_id = job_record.candidate_id
            job_id = job_record.job_id

    details = {
        "message": message,
        "status": status,
        "analysis_job_id": analysis_job_id
    }
    return publish_event(
        db=db,
        event_type=event_type,
        candidate_id=candidate_id,
        user_id=user_id,
        details=details,
        job_id=job_id
    )


def start_analysis_job(
    db: Session,
    application_id: int,
    candidate_id: int,
    job_id: int,
    operation: str = "candidate_job_match",
) -> AIAnalysisJob:
    analysis = AIAnalysisJob(
        application_id=application_id,
        candidate_id=candidate_id,
        job_id=job_id,
        operation=operation,
        requested_mode="hybrid",
        current_stage="local_running",
        local_status="running",
        gemini_status="waiting",
        hybrid_status="waiting",
        started_at=utc_now(),
    )
    db.add(analysis)
    db.flush()
    add_activity(
        db,
        "analysis_started",
        "Local AI analysis started.",
        "running",
        analysis.id,
    )
    return analysis


def complete_analysis_job(
    db: Session,
    analysis: AIAnalysisJob,
    ai_source: str,
    fallback_reason: str | None = None,
) -> None:
    now = utc_now()
    analysis.local_status = "completed"
    analysis.completed_at = now
    analysis.duration_seconds = max(0.0, (now - analysis.started_at).total_seconds()) if analysis.started_at else None

    if ai_source == "hybrid":
        analysis.actual_mode = "hybrid"
        analysis.gemini_status = "completed"
        analysis.hybrid_status = "completed"
        analysis.current_stage = "completed"
        add_activity(db, "hybrid_completed", "Hybrid AI result completed.", "completed", analysis.id)
    elif ai_source == "gemini":
        analysis.actual_mode = "gemini"
        analysis.gemini_status = "completed"
        analysis.hybrid_status = "skipped"
        analysis.current_stage = "completed"
        add_activity(db, "gemini_completed", "Gemini analysis completed.", "completed", analysis.id)
    elif ai_source == "local_fallback":
        analysis.actual_mode = "local_fallback"
        analysis.gemini_status = "failed"
        analysis.hybrid_status = "skipped"
        analysis.fallback_active = True
        analysis.fallback_reason = fallback_reason or "Gemini was unavailable; Local AI output was used."
        analysis.current_stage = "fallback_completed"
        add_activity(db, "fallback_activated", analysis.fallback_reason, "warning", analysis.id)
    else:
        analysis.actual_mode = "local_ai"
        analysis.gemini_status = "skipped"
        analysis.hybrid_status = "skipped"
        analysis.current_stage = "completed"
        add_activity(db, "local_completed", "Local AI analysis completed.", "completed", analysis.id)


def fail_analysis_job(db: Session, analysis: AIAnalysisJob, code: str, message: str) -> None:
    now = utc_now()
    analysis.current_stage = "failed"
    analysis.error_code = code
    analysis.error_message = message[:500]
    analysis.safe_error_message = message[:500]
    analysis.completed_at = now
    analysis.duration_seconds = max(0.0, (now - analysis.started_at).total_seconds()) if analysis.started_at else None
    if analysis.local_status == "running":
        analysis.local_status = "failed"
    add_activity(db, "analysis_failed", message[:500], "failed", analysis.id)
