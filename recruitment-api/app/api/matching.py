import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.ai.job_matcher import calculate_hybrid_match
from app.api.jobs import safe_split
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_candidate, require_hr
from app.models.ai_analysis import AIAnalysisJob
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.match_score import MatchScore
from app.models.user import User
from app.schemas.production_schema import ApplyRequest, StatusUpdate
from app.services.ai_tracking import complete_analysis_job, fail_analysis_job, start_analysis_job
from app.services.notification_service import create_notification, notify_all_hr
from app.utils.activity_logger import publish_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/matching", tags=["matching"])


def _parse_insight(explanation: str | None):
    if not explanation:
        return {}
    try:
        data = json.loads(explanation)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {"explanation": explanation}


def _confidence_from_evidence(result: dict) -> tuple[float | None, str | None]:
    required = result.get("required_skills") or []
    if not required:
        return None, None
    direct = len(result.get("matched_skills") or [])
    semantic = len(result.get("semantic_matches") or [])
    coverage = min(1.0, (direct + 0.5 * semantic) / max(1, len(required)))
    evidence_depth = min(1.0, len(required) / 5)
    score = round((0.75 * coverage + 0.25 * evidence_depth) * 100, 1)
    label = "High" if score >= 75 else "Medium" if score >= 50 else "Low"
    return score, label


def _match_payload(
    application: Application,
    match: MatchScore | None,
    candidate: Candidate | None = None,
    job: Job | None = None,
    user: User | None = None,
):
    insight = _parse_insight(match.explanation if match else None)
    return {
        "id": application.id,
        "application_id": application.id,
        "match_id": match.id if match else None,
        "candidate_id": application.candidate_id,
        "user_id": candidate.user_id if candidate else None,
        "name": (user.full_name if user else None) or (candidate.full_name if candidate else None) or "Unknown Candidate",
        "email": (user.email if user else None) or (candidate.email if candidate else None) or "No email",
        "skills": safe_split(candidate.skills if candidate else None),
        "phone": candidate.phone if candidate else None,
        "education": candidate.education if candidate else None,
        "experience": candidate.experience if candidate else None,
        "projects": candidate.projects if candidate else None,
        "certifications": candidate.certifications if candidate else None,
        "job_id": application.job_id,
        "matchedJob": job.title if job else "Unknown Role",
        "jobTitle": job.title if job else "Unknown Role",
        "score": match.score if match else 0,
        "match_score": match.score if match else 0,
        "status": application.status,
        "matchedSkills": safe_split(match.matched_skills if match else None),
        "missingSkills": safe_split(match.missing_skills if match else None),
        "explanation": insight.get("short_explanation") or insight.get("explanation") or (match.explanation if match else None),
        "fitLabel": (match.fit_label if match else None) or insight.get("fit_label"),
        "confidenceScore": match.confidence_score if match else None,
        "confidenceLabel": match.confidence_label if match else None,
        "aiSemanticAnalysis": insight.get("ai_semantic_analysis"),
        "hrSummary": insight.get("hr_summary"),
        "roadmap": insight.get("roadmap", []),
        "interviewQuestions": insight.get("interview_questions", []),
        "riskFlags": insight.get("risk_flags", []),
        "recommendation": insight.get("recommendation"),
        "semanticMatches": insight.get("semantic_matches", []),
        "aiSource": (match.ai_source if match else None) or insight.get("ai_source") or "local_ai",
        "fallbackActive": bool(match.fallback_active) if match else False,
        "fallbackReason": match.fallback_reason if match else None,
        "created_at": application.applied_at,
        "updated_at": application.updated_at,
    }


def _base_query(db: Session):
    return (
        db.query(Application, MatchScore, Candidate, Job, User)
        .join(Candidate, Application.candidate_id == Candidate.id)
        .join(Job, Application.job_id == Job.id)
        .outerjoin(MatchScore, MatchScore.application_id == Application.id)
        .outerjoin(User, Candidate.user_id == User.id)
    )


@router.get("/all")
def get_all_matches(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
    status: str | None = None,
    minimum_score: float | None = Query(None, ge=0, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr),
):
    query = _base_query(db).filter(Job.created_by == current_user.id)
    if status:
        query = query.filter(Application.status == status)
    if minimum_score is not None:
        query = query.filter(MatchScore.score >= minimum_score)
    rows = (
        query.order_by(Application.applied_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return [_match_payload(*row) for row in rows]


@router.get("/me")
def get_my_matches(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_candidate),
):
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found.")
    rows = _base_query(db).filter(Application.candidate_id == candidate.id).order_by(Application.applied_at.desc()).all()
    return [_match_payload(*row) for row in rows]


@router.get("/candidate/{user_id}")
def get_candidate_matches(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "hr" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You cannot access another candidate's applications.")
    candidate = db.query(Candidate).filter(Candidate.user_id == user_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found.")
    
    query = _base_query(db).filter(Application.candidate_id == candidate.id)
    if current_user.role == "hr":
        query = query.filter(Job.created_by == current_user.id)
        
    rows = query.order_by(Application.applied_at.desc()).all()
    return [_match_payload(*row) for row in rows]


@router.get("/job/{job_id}")
def get_job_matches(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to access this job's applications.")
    rows = _base_query(db).filter(Application.job_id == job_id).order_by(Application.applied_at.desc()).all()
    return [_match_payload(*row) for row in rows]


@router.post("/apply")
def apply_to_job(
    payload: ApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_candidate),
):
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found.")
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.status != "Active":
        raise HTTPException(status_code=400, detail="This job is no longer accepting applications.")
    if not candidate.skills:
        raise HTTPException(status_code=422, detail="Upload a valid complete resume before applying.")

    application = Application(candidate_id=candidate.id, job_id=job.id, status="AI Review")
    db.add(application)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="You have already applied to this job.")

    analysis = start_analysis_job(db, application.id, candidate.id, job.id)
    try:
        result = calculate_hybrid_match(
            candidate_skills=safe_split(candidate.skills),
            candidate_education=candidate.education or "",
            candidate_experience=candidate.experience or "",
            candidate_projects=candidate.projects or "",
            job_required_skills=job.required_skills or "",
            job_experience_level=job.experience_level or "",
            job_education_requirement=job.education_requirement or "",
            role=job.title,
        )
        confidence_score, confidence_label = _confidence_from_evidence(result)
        ai_source = result.get("ai_source") or "local_ai"
        fallback_reason = result.get("fallback_reason")
        insight_json = {
            "fit_label": result["fit_label"],
            "short_explanation": result["explanation"],
            "hr_summary": result["hr_summary"],
            "ai_semantic_analysis": result["ai_semantic_analysis"],
            "roadmap": result["roadmap"],
            "interview_questions": result["interview_questions"],
            "risk_flags": result["risk_flags"],
            "recommendation": result["recommendation"],
            "semantic_matches": result["semantic_matches"],
            "ai_source": ai_source,
        }
        match = MatchScore(
            application_id=application.id,
            candidate_id=candidate.id,
            job_id=job.id,
            score=result["score"],
            fit_label=result["fit_label"],
            confidence_score=confidence_score,
            confidence_label=confidence_label,
            matched_skills=", ".join(result["matched_skills"]),
            missing_skills=", ".join(result["missing_skills"]),
            explanation=json.dumps(insight_json),
            ai_source=ai_source,
            local_completed=True,
            gemini_completed=ai_source in {"gemini", "hybrid"},
            hybrid_completed=ai_source == "hybrid",
            fallback_active=ai_source == "local_fallback",
            fallback_reason=fallback_reason,
        )
        db.add(match)
        application.status = "Manual Review"
        complete_analysis_job(db, analysis, ai_source, fallback_reason)
        
        publish_event(db, "matching_applied", candidate.id, current_user.id, {
            "application_id": application.id,
            "score": match.score,
            "ai_source": ai_source
        }, job_id=job.id)

        notify_all_hr(
            db,
            "New application ready for review",
            f"{candidate.full_name or 'A candidate'} applied for {job.title}.",
            "application",
            "application",
            application.id,
        )
        create_notification(
            db,
            current_user.id,
            "Application submitted",
            f"Your application for {job.title} was analyzed successfully.",
            "success",
            "application",
            application.id,
        )
        db.commit()
        db.refresh(application)
        db.refresh(match)
        return {
            "message": "Application submitted successfully.",
            "application_id": application.id,
            "match_id": match.id,
            "score": match.score,
            "confidence_score": confidence_score,
            "confidence_label": confidence_label,
            **insight_json,
            "fallback_reason": fallback_reason,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Candidate-job analysis failed")
        fail_analysis_job(db, analysis, "analysis_failed", str(e))
        db.commit()
        raise HTTPException(status_code=500, detail="Application analysis could not be completed.")


@router.put("/{application_id}/status")
def update_match_status(
    application_id: int,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr),
):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")

    job = db.query(Job).filter(Job.id == application.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    # Scope security check
    if job.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to update this application status.")

    if application.status in {"Hired", "Rejected", "Withdrawn"} and payload.status != application.status:
        raise HTTPException(status_code=409, detail=f"Cannot change status of a completed/terminal '{application.status}' application.")

    application.status = payload.status
    application.reviewed_by = current_user.id
    application.reviewed_at = utc_now()
    if payload.status == "Rejected":
        application.rejection_reason = payload.reason
    if payload.status == "Withdrawn":
        application.withdrawn_at = utc_now()

    db.commit()
    db.refresh(application)

    candidate = db.query(Candidate).filter(Candidate.id == application.candidate_id).first()
    if candidate:
        publish_event(db, "application_status_updated", candidate.id, current_user.id, {
            "application_id": application.id,
            "status": payload.status
        }, job_id=application.job_id)

        if candidate.user_id:
            create_notification(
                db,
                candidate.user_id,
                "Application status updated",
                f"Your application status is now {payload.status}.",
                "application_status",
                "application",
                application.id,
            )
    return {"message": "Application status updated successfully.", "status": application.status}
