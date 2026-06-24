from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Literal

from app.core.database import get_db
from app.models.match_score import MatchScore
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.user import User
from app.api.jobs import calculate_skill_overlap, safe_split

router = APIRouter(prefix="/matching", tags=["matching"])

class StatusUpdate(BaseModel):
    status: Literal["Shortlisted", "Rejected", "Pending"]

class ApplyRequest(BaseModel):
    user_id: int
    job_id: int


@router.get("/all")
def get_all_matches(db: Session = Depends(get_db)):
    results = (
        db.query(MatchScore, Candidate, Job, User)
        .join(Candidate, MatchScore.candidate_id == Candidate.id)
        .join(Job, MatchScore.job_id == Job.id)
        .outerjoin(User, Candidate.user_id == User.id)
        .all()
    )
    
    output = []
    for match, candidate, job, user in results:
        output.append({
            "id": match.id,
            "candidate_id": match.candidate_id,
            "name": getattr(user, 'full_name', "Unknown") if user else "Unknown",
            "email": user.email if user else "No email",
            "skills": safe_split(candidate.skills),
            "job_id": match.job_id,
            "matchedJob": job.title if job else "Various",
            "score": match.score, 
            "status": match.status
        })
    return output

@router.get("/candidate/{user_id}")
def get_candidate_matches(user_id: int, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.user_id == user_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found.")
        
    results = (
        db.query(MatchScore, Job)
        .outerjoin(Job, MatchScore.job_id == Job.id)
        .filter(MatchScore.candidate_id == candidate.id)
        .all()
    )
    
    output = []
    for match, job in results:
        output.append({
            "id": match.id,
            "job_id": match.job_id,
            "jobTitle": job.title if job else "Unknown Role",
            "score": match.score,
            "status": match.status,
            "explanation": match.explanation,
            "missingSkills": safe_split(getattr(match, 'missing_skills', None)),
            "matchedSkills": safe_split(getattr(match, 'matched_skills', None))
        })
    return output


@router.post("/apply")
def apply_to_job(payload: ApplyRequest, db: Session = Depends(get_db)):
    """
    Candidate applies to a specific job. Recalculates the score fresh
    (in case skills changed since the recommendation was shown) and creates
    the official MatchScore row, making this candidate visible to HR.
    """
    candidate = db.query(Candidate).filter(Candidate.user_id == payload.user_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found.")

    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    if job.status != "Active":
        raise HTTPException(status_code=400, detail="This job is no longer accepting applications.")

    existing = db.query(MatchScore).filter(
        MatchScore.candidate_id == candidate.id,
        MatchScore.job_id == job.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already applied to this job.")

    candidate_skills = safe_split(candidate.skills)
    job_skills = safe_split(job.required_skills)
    result = calculate_skill_overlap(candidate_skills, job_skills)

    new_match = MatchScore(
        candidate_id=candidate.id,
        job_id=job.id,
        score=result["score"],
        matched_skills=", ".join(result["matched"]),
        missing_skills=", ".join(result["missing"]),
        explanation=f"Applied directly. {len(result['matched'])} of {len(job_skills)} required skills matched.",
        status="Pending"
    )
    db.add(new_match)
    db.commit()
    db.refresh(new_match)

    return {
        "message": "Application submitted successfully",
        "match_id": new_match.id,
        "score": new_match.score
    }


@router.put("/{match_id}/status")
def update_match_status(match_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    match = db.query(MatchScore).filter(MatchScore.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    match.status = payload.status
    db.commit()
    db.refresh(match)
    return {"message": "Status updated successfully", "status": match.status}