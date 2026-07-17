from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_candidate, require_hr
from app.models.candidate import Candidate
from app.models.user import User
from app.schemas.candidate_schema import CandidateResponse

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get("", response_model=list[CandidateResponse])
def get_all_candidates(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_hr),
):
    return (
        db.query(Candidate)
        .order_by(Candidate.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )


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
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    if current_user.role != "hr" and candidate.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot access this candidate profile.")
    return candidate
