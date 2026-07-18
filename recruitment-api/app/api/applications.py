import json
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_candidate, require_hr
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.match_score import MatchScore
from app.models.resume import Resume
from app.models.user import User
from app.schemas.production_schema import ApplyRequest
from app.ai.job_matcher import calculate_hybrid_match
from app.utils.file_handler import get_file_extension
from app.utils.activity_logger import publish_event
from app.services.notification_service import create_notification

router = APIRouter(prefix="/applications", tags=["applications"])


def safe_split(val):
    if not val:
        return []
    if isinstance(val, list):
        return val
    return [x.strip() for x in str(val).split(",") if x.strip()]


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


@router.post("")
def create_application(
    payload: ApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_candidate)
):
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found.")
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.status != "Active":
        raise HTTPException(status_code=400, detail="This job is no longer accepting applications.")
    
    # Check if duplicate application
    existing_app = db.query(Application).filter(
        Application.candidate_id == candidate.id,
        Application.job_id == job.id
    ).first()
    if existing_app:
        raise HTTPException(status_code=409, detail="You have already applied to this job.")
        
    application = Application(candidate_id=candidate.id, job_id=job.id, status="Applied")
    db.add(application)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="You have already applied to this job.")
        
    # Calculate hybrid match
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
    
    # Notify only the job-owning HR
    if job.created_by:
        create_notification(
            db,
            job.created_by,
            "New application ready for review",
            f"{candidate.full_name or 'A candidate'} applied for {job.title}.",
            "info",
            "application",
            application.id
        )
        
    create_notification(
        db,
        current_user.id,
        "Application submitted",
        f"Your application for {job.title} was submitted successfully.",
        "success",
        "application",
        application.id
    )
    
    # Publish event
    publish_event(db, "matching_applied", candidate.id, current_user.id, {
        "application_id": application.id,
        "score": match.score,
        "ai_source": ai_source
    }, job_id=job.id)
    
    db.commit()
    db.refresh(application)
    
    return {
        "message": "Application submitted successfully.",
        "application_id": application.id,
        "job_id": job.id,
        "status": application.status,
        "created_at": application.applied_at.isoformat() if hasattr(application.applied_at, "isoformat") else str(application.applied_at)
    }


@router.get("/hr/me")
def get_my_hr_applications(
    status: str | None = None,
    minimum_score: float | None = Query(None, ge=0, le=100),
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr),
):
    query = (
        db.query(Application, MatchScore, Candidate, Job, User)
        .join(Job, Application.job_id == Job.id)
        .join(Candidate, Application.candidate_id == Candidate.id)
        .outerjoin(MatchScore, MatchScore.application_id == Application.id)
        .outerjoin(User, Candidate.user_id == User.id)
        .filter(Job.created_by == current_user.id)
    )
    
    if status and status != "All":
        query = query.filter(Application.status == status)
    if minimum_score is not None:
        query = query.filter(MatchScore.score >= minimum_score)
    if search:
        search_clause = f"%{search}%"
        query = query.filter(
            or_(
                User.full_name.like(search_clause),
                User.email.like(search_clause),
                Job.title.like(search_clause)
            )
        )
        
    rows = query.order_by(Application.applied_at.desc()).all()
    
    results = []
    for app, match, cand, job, usr in rows:
        resume = db.query(Resume).filter(Resume.candidate_id == cand.id).first()
        resume_available = bool(resume and resume.file_path)
        insight = _parse_insight(match.explanation if match else None)
        
        results.append({
            "id": app.id,
            "application_id": app.id,
            "candidate_id": cand.id,
            "name": usr.full_name or cand.full_name or "Unknown Candidate",
            "email": usr.email or cand.email or "No email",
            "skills": safe_split(cand.skills),
            "phone": cand.phone,
            "education": cand.education,
            "experience": cand.experience,
            "projects": cand.projects,
            "certifications": cand.certifications,
            "job_id": app.job_id,
            "matchedJob": job.title,
            "jobTitle": job.title,
            "score": match.score if match else 0,
            "match_score": match.score if match else 0,
            "status": app.status,
            "matchedSkills": safe_split(match.matched_skills if match else None),
            "missingSkills": safe_split(match.missing_skills if match else None),
            "explanation": insight.get("short_explanation") or insight.get("explanation") or (match.explanation if match else None),
            "fitLabel": (match.fit_label if match else None) or insight.get("fit_label"),
            "confidenceScore": match.confidence_score if match else None,
            "confidenceLabel": match.confidence_label if match else None,
            "aiSource": (match.ai_source if match else None) or insight.get("ai_source") or "local_ai",
            "created_at": app.applied_at.isoformat() if hasattr(app.applied_at, "isoformat") else str(app.applied_at),
            "updated_at": app.updated_at.isoformat() if hasattr(app.updated_at, "isoformat") else str(app.updated_at),
            "resume_available": resume_available
        })
    return results


@router.get("/{application_id}")
def get_application_detail(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = (
        db.query(Application, MatchScore, Candidate, Job, User)
        .join(Job, Application.job_id == Job.id)
        .join(Candidate, Application.candidate_id == Candidate.id)
        .outerjoin(MatchScore, MatchScore.application_id == Application.id)
        .outerjoin(User, Candidate.user_id == User.id)
        .filter(Application.id == application_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Application not found.")
        
    app, match, cand, job, usr = row
    
    if current_user.role == "candidate":
        if cand.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You are not authorized to view this application.")
    elif current_user.role == "hr":
        if job.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="You do not have access to this application.")
    else:
        raise HTTPException(status_code=403, detail="Invalid role.")
        
    resume = db.query(Resume).filter(Resume.candidate_id == cand.id).first()
    resume_available = bool(resume and resume.file_path)
    insight = _parse_insight(match.explanation if match else None)
    
    return {
        "id": app.id,
        "application_id": app.id,
        "candidate_id": cand.id,
        "name": usr.full_name or cand.full_name or "Unknown Candidate",
        "email": usr.email or cand.email or "No email",
        "skills": safe_split(cand.skills),
        "phone": cand.phone,
        "education": cand.education,
        "experience": cand.experience,
        "projects": cand.projects,
        "certifications": cand.certifications,
        "job_id": app.job_id,
        "matchedJob": job.title,
        "jobTitle": job.title,
        "score": match.score if match else 0,
        "match_score": match.score if match else 0,
        "status": app.status,
        "matchedSkills": safe_split(match.matched_skills if match else None),
        "missingSkills": safe_split(match.missing_skills if match else None),
        "explanation": insight.get("short_explanation") or insight.get("explanation") or (match.explanation if match else None),
        "fitLabel": (match.fit_label if match else None) or insight.get("fit_label"),
        "confidenceScore": match.confidence_score if match else None,
        "confidenceLabel": match.confidence_label if match else None,
        "aiSource": (match.ai_source if match else None) or insight.get("ai_source") or "local_ai",
        "created_at": app.applied_at.isoformat() if hasattr(app.applied_at, "isoformat") else str(app.applied_at),
        "updated_at": app.updated_at.isoformat() if hasattr(app.updated_at, "isoformat") else str(app.updated_at),
        "resume_available": resume_available
    }


@router.get("/{application_id}/resume")
def download_application_resume(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr),
):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")
        
    job = db.query(Job).filter(Job.id == app.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
        
    if job.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to view the resume for this application.")
        
    resume = db.query(Resume).filter(Resume.candidate_id == app.candidate_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume record not found.")
        
    if not resume.file_path or not os.path.exists(resume.file_path):
        raise HTTPException(status_code=404, detail="Resume file not found on disk")
        
    upload_root = Path(os.getenv("UPLOAD_DIR", "uploads")).resolve()
    stored_path = Path(resume.file_path)
    if stored_path.is_absolute():
        resume_path = stored_path.resolve()
    else:
        resume_path = (upload_root / stored_path).resolve()
        
    try:
        resume_path.relative_to(upload_root)
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid resume file path.")
        
    ext = get_file_extension(resume.file_name).lower()
    if ext == ".pdf":
        media_type = "application/pdf"
        disposition_type = "inline"
    elif ext == ".docx":
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        disposition_type = "attachment"
    else:
        raise HTTPException(status_code=415, detail="Unsupported resume file format.")
        
    original_filename = os.path.basename(resume.file_name)
    original_filename = "".join(c for c in original_filename if c not in "\r\n\0")
    original_filename = os.path.basename(original_filename)

    headers = {
        "Cache-Control": "private, no-store",
        "X-Content-Type-Options": "nosniff"
    }
    return FileResponse(
        path=resume_path,
        media_type=media_type,
        filename=original_filename,
        content_disposition_type=disposition_type,
        headers=headers
    )
