from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_hr
from app.core.rate_limit import rate_limiter
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.user import User

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", dependencies=[Depends(rate_limiter.dependency(60, 60, "search"))])
def global_search(
    q: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(8, ge=1, le=20),
    db: Session = Depends(get_db),
    _: User = Depends(require_hr),
):
    term = f"%{q.strip()}%"
    candidates = (
        db.query(Candidate)
        .filter(or_(Candidate.full_name.ilike(term), Candidate.email.ilike(term), Candidate.skills.ilike(term)))
        .limit(limit)
        .all()
    )
    jobs = (
        db.query(Job)
        .filter(or_(Job.title.ilike(term), Job.required_skills.ilike(term), Job.description.ilike(term)))
        .limit(limit)
        .all()
    )
    application_results = []
    if q.strip().isdigit():
        application = db.query(Application).filter(Application.id == int(q.strip())).first()
        if application:
            application_results.append({
                "id": application.id,
                "status": application.status,
                "candidate_id": application.candidate_id,
                "job_id": application.job_id,
            })
    return {
        "candidates": [
            {"id": c.id, "user_id": c.user_id, "name": c.full_name, "email": c.email, "skills": c.skills}
            for c in candidates
        ],
        "jobs": [
            {"id": j.id, "title": j.title, "status": j.status, "required_skills": j.required_skills}
            for j in jobs
        ],
        "applications": application_results,
    }
