import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
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
from app.services.blind_screening import is_blind_mode_requested, build_blind_candidate_representation

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
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
    status: str | None = None,
    minimum_score: float | None = Query(None, ge=0, le=100),
    blind_mode: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr),
):
    blind = is_blind_mode_requested(request, blind_mode, current_user)
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
    results = []
    for row in rows:
        payload = _match_payload(*row)
        cand = row[2]
        usr = row[4]
        cand_name = (usr.full_name if usr else None) or (cand.full_name if cand else None)
        cand_email = (usr.email if usr else None) or (cand.email if cand else None)
        cand_phone = cand.phone if cand else None
        if blind:
            results.append(build_blind_candidate_representation(payload, candidate_id=cand.id if cand else None, candidate_name=cand_name, email=cand_email, phone=cand_phone))
        else:
            results.append(payload)
    return results


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
    request: Request,
    user_id: int,
    blind_mode: bool = Query(False),
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
    blind = current_user.role == "hr" and is_blind_mode_requested(request, blind_mode, current_user)
    results = []
    for row in rows:
        payload = _match_payload(*row)
        cand = row[2]
        usr = row[4]
        cand_name = (usr.full_name if usr else None) or (cand.full_name if cand else None)
        cand_email = (usr.email if usr else None) or (cand.email if cand else None)
        cand_phone = cand.phone if cand else None
        if blind:
            results.append(build_blind_candidate_representation(payload, candidate_id=cand.id if cand else None, candidate_name=cand_name, email=cand_email, phone=cand_phone))
        else:
            results.append(payload)
    return results


@router.get("/job/{job_id}")
def get_job_matches(
    request: Request,
    job_id: int,
    blind_mode: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to access this job's applications.")
    rows = _base_query(db).filter(Application.job_id == job_id).order_by(Application.applied_at.desc()).all()
    blind = is_blind_mode_requested(request, blind_mode, current_user)
    results = []
    for row in rows:
        payload = _match_payload(*row)
        cand = row[2]
        usr = row[4]
        cand_name = (usr.full_name if usr else None) or (cand.full_name if cand else None)
        cand_email = (usr.email if usr else None) or (cand.email if cand else None)
        cand_phone = cand.phone if cand else None
        if blind:
            results.append(build_blind_candidate_representation(payload, candidate_id=cand.id if cand else None, candidate_name=cand_name, email=cand_email, phone=cand_phone))
        else:
            results.append(payload)
    return results


from app.api.applications import submit_application

@router.post("/apply")
def apply_to_job(
    payload: ApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_candidate),
):
    return submit_application(db, payload.job_id, current_user)


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

    VALID_TRANSITIONS = {
        "Applied": {"AI Review", "Manual Review", "Shortlisted", "Interview", "Offer", "Hired", "Rejected", "Withdrawn"},
        "AI Review": {"Manual Review", "Shortlisted", "Interview", "Offer", "Hired", "Rejected", "Withdrawn"},
        "Manual Review": {"Shortlisted", "Interview", "Offer", "Hired", "Rejected", "Withdrawn"},
        "Shortlisted": {"Interview", "Offer", "Hired", "Rejected", "Withdrawn"},
        "Interview": {"Offer", "Hired", "Rejected", "Withdrawn"},
        "Offer": {"Hired", "Rejected", "Withdrawn"},
        "Hired": set(),
        "Rejected": set(),
        "Withdrawn": set(),
    }

    if payload.status != application.status:
        allowed = VALID_TRANSITIONS.get(application.status, set())
        if payload.status not in allowed:
            raise HTTPException(
                status_code=409,
                detail=f"Invalid status transition from '{application.status}' to '{payload.status}'."
            )

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
