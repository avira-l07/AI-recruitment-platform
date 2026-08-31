from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_hr
from app.core.rate_limit import rate_limiter
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.user import User
from app.services.blind_screening import is_blind_mode_requested, get_neutral_candidate_identifier

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", dependencies=[Depends(rate_limiter.dependency(60, 60, "search"))])
def global_search(
    request: Request,
    q: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(8, ge=1, le=20),
    blind_mode: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr),
):
    blind = is_blind_mode_requested(request, blind_mode, current_user)
    term = f"%{q.strip()}%"
    
    cand_query = (
        db.query(Candidate)
        .join(Application, Candidate.id == Application.candidate_id)
        .join(Job, Application.job_id == Job.id)
        .filter(Job.created_by == current_user.id)
    )
    
    if blind:
        # In blind mode, do not search or match on candidate personal names or emails
        cand_query = cand_query.filter(
            or_(
                Candidate.skills.ilike(term),
                Candidate.projects.ilike(term),
                Candidate.certifications.ilike(term)
            )
        )
    else:
        cand_query = cand_query.filter(
            or_(
                Candidate.full_name.ilike(term),
                Candidate.email.ilike(term),
                Candidate.skills.ilike(term)
            )
        )
        
    candidates = cand_query.distinct().limit(limit).all()
    jobs = (
        db.query(Job)
        .filter(Job.created_by == current_user.id)
        .filter(or_(Job.title.ilike(term), Job.required_skills.ilike(term), Job.description.ilike(term)))
        .limit(limit)
        .all()
    )
    application_results = []
    if q.strip().isdigit():
        application = (
            db.query(Application)
            .join(Job, Application.job_id == Job.id)
            .filter(Job.created_by == current_user.id)
            .filter(Application.id == int(q.strip()))
            .first()
        )
        if application:
            application_results.append({
                "id": application.id,
                "status": application.status,
                "candidate_id": application.candidate_id,
                "job_id": application.job_id,
            })
            
    if blind:
        candidate_results = [
            {
                "id": c.id,
                "user_id": None,
                "name": get_neutral_candidate_identifier(c.id),
                "email": None,
                "skills": c.skills,
                "is_blind_mode": True,
            }
            for c in candidates
        ]
    else:
        candidate_results = [
            {"id": c.id, "user_id": c.user_id, "name": c.full_name, "email": c.email, "skills": c.skills}
            for c in candidates
        ]
        
    return {
        "candidates": candidate_results,
        "jobs": [
            {"id": j.id, "title": j.title, "status": j.status, "required_skills": j.required_skills}
            for j in jobs
        ],
        "applications": application_results,
    }
