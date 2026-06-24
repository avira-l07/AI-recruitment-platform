from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import List
from app.core.database import get_db
from app.models.job import Job
from app.models.candidate import Candidate
from app.schemas.job_schema import JobCreate, JobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


class CloseJobRequest(BaseModel):
    reason: str


def safe_split(value):
    if not value:
        return []
    return [s.strip() for s in value.split(",") if s.strip()]


def calculate_skill_overlap(candidate_skills: list, job_skills: list) -> dict:
    """
    Simple % overlap: how many of the job's required skills the candidate has.
    Case-insensitive comparison.
    """
    candidate_set = {s.lower().strip() for s in candidate_skills}
    job_set_original = [s.strip() for s in job_skills if s.strip()]

    if not job_set_original:
        return {"score": 0, "matched": [], "missing": []}

    matched = [s for s in job_set_original if s.lower() in candidate_set]
    missing = [s for s in job_set_original if s.lower() not in candidate_set]

    score = round((len(matched) / len(job_set_original)) * 100)

    return {"score": score, "matched": matched, "missing": missing}


def seed_default_jobs(db: Session):
    if db.query(Job).count() == 0:
        jobs = [
            Job(
                title="Frontend Developer",
                description="We are looking for a frontend developer.",
                required_skills="React, JavaScript, HTML, CSS, Git, REST API",
                experience_level="Mid",
                education_requirement="Bachelor in Computer Science or related"
            ),
            Job(
                title="AI/ML Intern",
                description="Looking for an intern passionate about AI.",
                required_skills="Python, Machine Learning, NLP, Pandas, NumPy, Scikit-learn",
                experience_level="Entry",
                education_requirement="B.Tech or BCA in CS, AI, or ML"
            ),
            Job(
                title="Backend Developer",
                description="Strong backend developer needed.",
                required_skills="FastAPI, Python, SQL, PostgreSQL, REST API",
                experience_level="Mid",
                education_requirement="Bachelor in Computer Science or related"
            )
        ]
        db.add_all(jobs)
        db.commit()


@router.post("", response_model=JobResponse)
def create_job(job: JobCreate, created_by: int = Query(...), db: Session = Depends(get_db)):
    new_job = Job(
        title=job.title,
        description=job.description,
        required_skills=job.required_skills,
        experience_level=job.experience_level,
        education_requirement=job.education_requirement,
        created_by=created_by
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job


@router.get("", response_model=List[JobResponse])
def get_all_jobs(active_only: bool = Query(False), db: Session = Depends(get_db)):
    query = db.query(Job)
    if active_only:
        query = query.filter(Job.status == "Active")
    return query.all()


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.put("/{job_id}/close", response_model=JobResponse)
def close_job(job_id: int, payload: CloseJobRequest, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = "Closed"
    job.closed_reason = payload.reason
    job.closed_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    return job


@router.put("/{job_id}/reopen", response_model=JobResponse)
def reopen_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = "Active"
    job.closed_reason = None
    job.closed_at = None
    db.commit()
    db.refresh(job)
    return job


@router.get("/recommended/{user_id}")
def get_recommended_jobs(user_id: int, db: Session = Depends(get_db)):
    """
    Returns active jobs where the candidate's skills overlap >= 50% with
    the job's required_skills. Does NOT create a MatchScore row - this is
    just a preview. The candidate must call /matching/apply to officially apply.
    """
    candidate = db.query(Candidate).filter(Candidate.user_id == user_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found.")

    candidate_skills = safe_split(candidate.skills)
    active_jobs = db.query(Job).filter(Job.status == "Active").all()

    recommended = []
    for job in active_jobs:
        job_skills = safe_split(job.required_skills)
        result = calculate_skill_overlap(candidate_skills, job_skills)

        if result["score"] >= 50:
            recommended.append({
                "job_id": job.id,
                "title": job.title,
                "description": job.description,
                "experience_level": job.experience_level,
                "education_requirement": job.education_requirement,
                "score": result["score"],
                "matched_skills": result["matched"],
                "missing_skills": result["missing"],
            })

    recommended.sort(key=lambda j: j["score"], reverse=True)
    return recommended