from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.candidate import Candidate
from app.schemas.candidate_schema import CandidateResponse
from app.api.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/candidates", tags=["candidates"])

@router.get("", response_model=List[CandidateResponse])
def get_all_candidates(
    db: Session = Depends(get_db),
    _ = Depends(require_roles(["hr"]))
):
    candidates = db.query(Candidate).all()
    return candidates

@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    if current_user.role != "hr" and candidate.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this profile")
        
    return candidate
