from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import List
from app.core.database import get_db
from app.models.job import Job
from app.models.candidate import Candidate
from app.schemas.job_schema import JobCreate, JobResponse
from app.ai.job_matcher import calculate_hybrid_match
from app.ai.job_intelligence import analyze_job_description
from app.core.dependencies import get_current_user, require_roles, verify_candidate_ownership

router = APIRouter(prefix="/jobs", tags=["jobs"])

class CloseJobRequest(BaseModel):
    reason: str

class JobAnalyzeRequest(BaseModel):
    title: str
    description: str = ""
    required_skills: str = ""
    experience_level: str = ""


def safe_split(value):
    if not value:
        return []
    if isinstance(value, list):
        return [str(s).strip() for s in value if str(s).strip()]
    return [s.strip() for s in str(value).split(",") if s.strip()]


def seed_default_jobs(db: Session):
    if db.query(Job).count() == 0:
        jobs = [
            Job(title="ML/AI Engineer", description="Design, develop, and improve machine learning models and AI-powered products.", required_skills="Python, Machine Learning, Deep Learning, NLP, TensorFlow, PyTorch, Scikit-learn, Pandas, NumPy", experience_level="Mid", education_requirement="Bachelor's degree in Computer Science, Mathematics, or related field"),
            Job(title="Python Developer", description="Build dynamic, high-performing, and responsive applications using Python and web frameworks.", required_skills="Python, Django, Flask, FastAPI, REST API, SQL, PostgreSQL, Git, Linux", experience_level="Mid", education_requirement="Bachelor's degree in Computer Science or Computer Engineering"),
            Job(title="Frontend Developer", description="Build polished user interfaces, dashboards, and responsive web screens.", required_skills="React, JavaScript, HTML, CSS, Git, REST API, Responsive Design", experience_level="Entry", education_requirement="Bachelor in Computer Science or related"),
            Job(title="Backend Developer", description="Build APIs, authentication, database systems, and server-side logic.", required_skills="FastAPI, Python, SQL, PostgreSQL, REST API, Docker, Git", experience_level="Mid", education_requirement="Bachelor in Computer Science or related"),
            Job(title="Data Analyst", description="Analyze datasets, create dashboards, and generate business insights.", required_skills="Python, SQL, Pandas, NumPy, Data Analysis, Excel, Power BI", experience_level="Entry", education_requirement="Bachelor's degree in Computer Science, Statistics, or related"),
        ]
        db.add_all(jobs)
        db.commit()


@router.post("/analyze")
def analyze_job(payload: JobAnalyzeRequest, current_user = Depends(require_roles(["hr"]))):
    return analyze_job_description(payload.title, payload.description, payload.required_skills, payload.experience_level)


@router.get("/recommended/{user_id}")
def get_recommended_jobs(user_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    verify_candidate_ownership(user_id, current_user)
    candidate = db.query(Candidate).filter(Candidate.user_id == user_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found.")
    active_jobs = db.query(Job).filter(Job.status == "Active").all()
    recommended = []
    for job in active_jobs:
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
        if result["score"] >= 35:
            recommended.append({
                "job_id": job.id,
                "title": job.title,
                "description": job.description,
                "experience_level": job.experience_level,
                "education_requirement": job.education_requirement,
                "score": result["score"],
                "fitLabel": result["fit_label"],
                "matched_skills": result["matched_skills"],
                "semantic_matches": result["semantic_matches"],
                "missing_skills": result["missing_skills"],
                "aiSemanticAnalysis": result["ai_semantic_analysis"],
                "aiSource": result.get("ai_source", "hybrid_local_ai"),
            })
    recommended.sort(key=lambda j: j["score"], reverse=True)
    return recommended


@router.post("", response_model=JobResponse)
def create_job(job: JobCreate, db: Session = Depends(get_db), current_user = Depends(require_roles(["hr"]))):
    if len(safe_split(job.required_skills)) < 2:
        raise HTTPException(status_code=422, detail="Add at least two required skills for accurate matching.")
    new_job = Job(title=job.title, description=job.description, required_skills=job.required_skills, experience_level=job.experience_level, education_requirement=job.education_requirement, created_by=current_user.id)
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    from app.utils.activity_logger import publish_event
    publish_event(db, "job_created", None, current_user.id, {
        "job_id": new_job.id,
        "title": new_job.title,
        "required_skills": new_job.required_skills
    }, job_id=new_job.id)
    db.commit()
    return new_job


@router.get("", response_model=List[JobResponse])
def get_all_jobs(active_only: bool = Query(False), db: Session = Depends(get_db)):
    query = db.query(Job)
    if active_only:
        query = query.filter(Job.status == "Active")
    return query.order_by(Job.created_at.desc()).all()


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.put("/{job_id}/close", response_model=JobResponse)
def close_job(job_id: int, payload: CloseJobRequest, db: Session = Depends(get_db), current_user = Depends(require_roles(["hr"]))):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = "Closed"
    job.closed_reason = payload.reason
    job.closed_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    publish_event(db, "job_closed", None, current_user.id, {
        "job_id": job.id,
        "title": job.title,
        "reason": payload.reason
    }, job_id=job.id)
    db.commit()
    return job


@router.put("/{job_id}/reopen", response_model=JobResponse)
def reopen_job(job_id: int, db: Session = Depends(get_db), current_user = Depends(require_roles(["hr"]))):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = "Active"
    job.closed_reason = None
    job.closed_at = None
    db.commit()
    db.refresh(job)
    publish_event(db, "job_reopened", None, current_user.id, {
        "job_id": job.id,
        "title": job.title
    }, job_id=job.id)
    db.commit()
    return job
