import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Literal

from app.core.database import get_db
from app.models.match_score import MatchScore
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.user import User
from app.api.jobs import safe_split
from app.ai.job_matcher import calculate_hybrid_match
from app.api.dependencies import get_current_user, require_roles, verify_candidate_ownership

router = APIRouter(prefix="/matching", tags=["matching"])

class StatusUpdate(BaseModel):
    status: Literal["Shortlisted", "Rejected", "Pending"]

class ApplyRequest(BaseModel):
    user_id: int
    job_id: int


def _parse_insight(explanation: str):
    if not explanation:
        return {}
    try:
        data = json.loads(explanation)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {"explanation": explanation}


def _match_payload(match: MatchScore, candidate: Candidate = None, job: Job = None, user: User = None):
    insight = _parse_insight(match.explanation)
    return {
        "id": match.id,
        "candidate_id": match.candidate_id,
        "user_id": candidate.user_id if candidate else None,
        "name": (user.full_name if user else None) or (candidate.full_name if candidate else None) or "Unknown Candidate",
        "email": (user.email if user else None) or (candidate.email if candidate else None) or "No email",
        "skills": safe_split(candidate.skills if candidate else None),
        "phone": candidate.phone if candidate else None,
        "education": candidate.education if candidate else None,
        "experience": candidate.experience if candidate else None,
        "projects": candidate.projects if candidate else None,
        "certifications": candidate.certifications if candidate else None,
        "job_id": match.job_id,
        "matchedJob": job.title if job else "Unknown Role",
        "jobTitle": job.title if job else "Unknown Role",
        "score": match.score,
        "status": match.status,
        "matchedSkills": safe_split(match.matched_skills),
        "missingSkills": safe_split(match.missing_skills),
        "explanation": insight.get("short_explanation") or insight.get("explanation") or match.explanation,
        "fitLabel": insight.get("fit_label"),
        "aiSemanticAnalysis": insight.get("ai_semantic_analysis"),
        "hrSummary": insight.get("hr_summary"),
        "roadmap": insight.get("roadmap", []),
        "interviewQuestions": insight.get("interview_questions", []),
        "riskFlags": insight.get("risk_flags", []),
        "recommendation": insight.get("recommendation"),
        "semanticMatches": insight.get("semantic_matches", []),
        "aiSource": insight.get("ai_source", "hybrid_local_ai"),
        "created_at": match.created_at,
    }


@router.get("/all")
def get_all_matches(db: Session = Depends(get_db), current_user = Depends(require_roles(["hr"]))):
    results = (
        db.query(MatchScore, Candidate, Job, User)
        .join(Candidate, MatchScore.candidate_id == Candidate.id)
        .join(Job, MatchScore.job_id == Job.id)
        .outerjoin(User, Candidate.user_id == User.id)
        .all()
    )
    return [_match_payload(match, candidate, job, user) for match, candidate, job, user in results]


@router.get("/candidate/{user_id}")
def get_candidate_matches(user_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    verify_candidate_ownership(user_id, current_user)
    candidate = db.query(Candidate).filter(Candidate.user_id == user_id).first()
    if not candidate:
        # Robust fallback: older frontend sometimes sent candidate_id instead of user_id.
        candidate = db.query(Candidate).filter(Candidate.id == user_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found.")
    user = db.query(User).filter(User.id == candidate.user_id).first()
    results = db.query(MatchScore, Job).outerjoin(Job, MatchScore.job_id == Job.id).filter(MatchScore.candidate_id == candidate.id).all()
    return [_match_payload(match, candidate, job, user) for match, job in results]


@router.get("/job/{job_id}")
def get_job_matches(job_id: int, db: Session = Depends(get_db), current_user = Depends(require_roles(["hr"]))):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    results = (
        db.query(MatchScore, Candidate, User)
        .join(Candidate, MatchScore.candidate_id == Candidate.id)
        .outerjoin(User, Candidate.user_id == User.id)
        .filter(MatchScore.job_id == job_id)
        .all()
    )
    return [_match_payload(match, candidate, user) for match, candidate, user in results]


@router.post("/apply")
def apply_to_job(payload: ApplyRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.role != "hr" and payload.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to apply on behalf of this candidate")
        
    candidate = db.query(Candidate).filter(Candidate.user_id == payload.user_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found. Upload/register as candidate first.")
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.status != "Active":
        raise HTTPException(status_code=400, detail="This job is no longer accepting applications.")

    existing = db.query(MatchScore).filter(MatchScore.candidate_id == candidate.id, MatchScore.job_id == job.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already applied to this job.")

    if not candidate.skills:
        raise HTTPException(status_code=422, detail="Upload a valid complete resume before applying.")

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
        "ai_source": result["ai_source"],
    }

    new_match = MatchScore(
        candidate_id=candidate.id,
        job_id=job.id,
        score=result["score"],
        matched_skills=", ".join(result["matched_skills"]),
        missing_skills=", ".join(result["missing_skills"]),
        explanation=json.dumps(insight_json),
        status="Pending",
    )
    db.add(new_match)
    db.commit()
    db.refresh(new_match)
    
    from app.models.resume import Resume
    resume = db.query(Resume).filter(Resume.candidate_id == candidate.id).first()
    resume_id = resume.id if resume else None

    from app.utils.activity_logger import publish_event
    publish_event(db, "matching_applied", candidate.id, payload.user_id, {
        "match_id": new_match.id,
        "job_id": job.id,
        "job_title": job.title,
        "score": new_match.score
    }, resume_id=resume_id, job_id=job.id)
    db.commit()
    return {"message": "Application submitted successfully", "match_id": new_match.id, "score": new_match.score, **insight_json}


@router.put("/{match_id}/status")
def update_match_status(match_id: int, payload: StatusUpdate, db: Session = Depends(get_db), current_user = Depends(require_roles(["hr"]))):
    match = db.query(MatchScore).filter(MatchScore.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    match.status = payload.status
    db.commit()
    db.refresh(match)
    
    from app.models.resume import Resume
    resume = db.query(Resume).filter(Resume.candidate_id == match.candidate_id).first()
    resume_id = resume.id if resume else None

    from app.utils.activity_logger import publish_event
    event_type = "matching_shortlisted" if payload.status == "Shortlisted" else "matching_rejected" if payload.status == "Rejected" else "matching_applied"
    publish_event(db, event_type, match.candidate_id, None, {
        "match_id": match.id,
        "job_id": match.job_id,
        "status": match.status
    }, resume_id=resume_id, job_id=match.job_id)
    db.commit()
    return {"message": "Status updated successfully", "status": match.status}
