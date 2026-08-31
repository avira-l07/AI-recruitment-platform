from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_candidate, require_hr
from app.models.candidate import Candidate
from app.models.user import User
from app.schemas.candidate_schema import CandidateResponse
from app.services.blind_screening import (
    is_blind_mode_requested,
    get_neutral_candidate_identifier,
    sanitize_education,
    sanitize_experience,
    sanitize_list_or_text,
)

router = APIRouter(prefix="/candidates", tags=["candidates"])


def _candidate_to_blind_dict(cand: Candidate) -> dict:
    neutral_id = get_neutral_candidate_identifier(cand.id)
    return {
        "id": cand.id,
        "user_id": None,
        "full_name": neutral_id,
        "email": None,
        "phone": None,
        "education": sanitize_education(cand.education),
        "experience": sanitize_experience(cand.experience),
        "skills": cand.skills,
        "projects": sanitize_list_or_text(cand.projects, candidate_name=cand.full_name, candidate_id=cand.id),
        "certifications": cand.certifications,
    }


@router.get("", response_model=list[CandidateResponse])
def get_all_candidates(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    blind_mode: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr),
):
    blind = is_blind_mode_requested(request, blind_mode, current_user)
    candidates = (
        db.query(Candidate)
        .order_by(Candidate.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    if blind:
        return [_candidate_to_blind_dict(c) for c in candidates]
    return candidates


@router.get("/me", response_model=CandidateResponse)
def get_my_candidate(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_candidate),
):
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found.")
    return candidate


@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(
    request: Request,
    candidate_id: int,
    blind_mode: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    if current_user.role != "hr" and candidate.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot access this candidate profile.")
    
    if current_user.role == "hr" and is_blind_mode_requested(request, blind_mode, current_user):
        return _candidate_to_blind_dict(candidate)
    return candidate
