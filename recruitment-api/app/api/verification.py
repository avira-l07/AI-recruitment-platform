import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_hr
from app.core.time import utc_now
from app.models.candidate import Candidate
from app.models.user import User
from app.models.verification import ExperienceVerification
from app.services.verification_orchestrator import run_full_verification_pipeline
from app.services.blind_screening import is_blind_mode_requested, get_neutral_candidate_identifier, redact_text_pii
from app.utils.activity_logger import publish_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/verification", tags=["verification"])


class DecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(verified|needs_review|suspicious)$")
    notes: Optional[str] = Field(default=None, max_length=1000)


def _format_verification_response(v: ExperienceVerification, candidate: Candidate, user: Optional[User], is_blind: bool) -> dict:
    cand_id = candidate.id
    neutral_id = get_neutral_candidate_identifier(cand_id)
    cand_name = neutral_id if is_blind else ((user.full_name if user else None) or candidate.full_name or neutral_id)
    cand_email = None if is_blind else ((user.email if user else None) or candidate.email)
    cand_phone = None if is_blind else candidate.phone

    claims = json.loads(v.claims_json) if v.claims_json else {}
    companies = json.loads(v.company_verifications_json) if v.company_verifications_json else []
    internships = json.loads(v.internship_verifications_json) if v.internship_verifications_json else []
    projects = json.loads(v.project_verifications_json) if v.project_verifications_json else []
    timeline = json.loads(v.timeline_intelligence_json) if v.timeline_intelligence_json else {}
    certifications = json.loads(v.certification_verifications_json) if v.certification_verifications_json else []
    authenticity = json.loads(v.resume_authenticity_json) if v.resume_authenticity_json else {}
    sources = json.loads(v.evidence_sources_json) if v.evidence_sources_json else []
    graph = json.loads(v.evidence_graph_json) if v.evidence_graph_json else {}
    breakdown = json.loads(v.trust_score_breakdown_json) if v.trust_score_breakdown_json else []
    ai_reasoning = json.loads(v.ai_reasoning_json) if v.ai_reasoning_json else {}
    history = json.loads(v.history_json) if v.history_json else []

    if is_blind and ai_reasoning.get("summary"):
        ai_reasoning["summary"] = redact_text_pii(ai_reasoning["summary"], candidate_name=candidate.full_name, candidate_id=cand_id)

    # Sanitize graph in blind mode
    if is_blind and graph.get("nodes"):
        for node in graph["nodes"]:
            if node.get("type") == "candidate":
                node["label"] = neutral_id

    return {
        "id": v.id,
        "candidate_id": cand_id,
        "candidate_name": cand_name,
        "candidate_email": cand_email,
        "candidate_phone": cand_phone,
        "is_blind_mode": is_blind,
        "verification_version": v.verification_version,
        "status": v.status,
        "stage": v.stage,
        "trust_score": v.trust_score,
        "previous_trust_score": v.previous_trust_score,
        "verification_outcome": v.verification_outcome,
        "confidence_label": v.confidence_label,
        "claims": claims,
        "company_verifications": companies,
        "internship_verifications": internships,
        "project_verifications": projects,
        "timeline_intelligence": timeline,
        "certification_verifications": certifications,
        "resume_authenticity": authenticity,
        "evidence_sources": sources,
        "evidence_graph": graph,
        "trust_score_breakdown": breakdown,
        "ai_reasoning": ai_reasoning,
        "hr_decision": v.hr_decision,
        "hr_decision_notes": v.hr_decision_notes,
        "hr_decided_at": v.hr_decided_at.isoformat() if v.hr_decided_at else None,
        "history": history,
        "created_at": v.created_at.isoformat() if v.created_at else None,
        "updated_at": v.updated_at.isoformat() if v.updated_at else None,
    }


@router.get("/candidate/{candidate_id}")
def get_candidate_verification(
    request: Request,
    candidate_id: int,
    blind_mode: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr)
):
    """
    Retrieves or runs verification for a specific candidate.
    Supports Blind Screening / Fair Review Mode.
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    user = db.query(User).filter(User.id == candidate.user_id).first() if candidate.user_id else None
    is_blind = is_blind_mode_requested(request, blind_mode, current_user)

    v = db.query(ExperienceVerification).filter(ExperienceVerification.candidate_id == candidate_id).first()
    if not v:
        # Generate automatically on first review
        v = run_full_verification_pipeline(
            db=db,
            candidate_id=candidate_id,
            initiated_by_user_id=current_user.id,
            is_blind_mode=is_blind,
            is_reverification=False
        )

    return _format_verification_response(v, candidate, user, is_blind)


@router.post("/candidate/{candidate_id}/verify")
def run_verification(
    request: Request,
    candidate_id: int,
    blind_mode: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr)
):
    """
    Initiates or forces reverification for a candidate.
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    user = db.query(User).filter(User.id == candidate.user_id).first() if candidate.user_id else None
    is_blind = is_blind_mode_requested(request, blind_mode, current_user)

    v = run_full_verification_pipeline(
        db=db,
        candidate_id=candidate_id,
        initiated_by_user_id=current_user.id,
        is_blind_mode=is_blind,
        is_reverification=True
    )

    return _format_verification_response(v, candidate, user, is_blind)


@router.post("/{verification_id}/decision")
def record_hr_decision(
    verification_id: int,
    payload: DecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr)
):
    """
    Records HR's manual evaluation decision for a verification run.
    """
    v = db.query(ExperienceVerification).filter(ExperienceVerification.id == verification_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Verification record not found")

    v.hr_decision = payload.decision
    v.hr_decision_notes = payload.notes
    v.hr_decided_by = current_user.id
    v.hr_decided_at = utc_now()
    db.commit()
    db.refresh(v)

    # Publish audit event
    publish_event(
        db,
        event_type="verification_decision_updated",
        candidate_id=v.candidate_id,
        user_id=current_user.id,
        details={
            "verification_id": v.id,
            "candidate_id": v.candidate_id,
            "hr_decision": payload.decision,
            "notes": payload.notes
        }
    )

    candidate = db.query(Candidate).filter(Candidate.id == v.candidate_id).first()
    user = db.query(User).filter(User.id == candidate.user_id).first() if (candidate and candidate.user_id) else None

    return _format_verification_response(v, candidate, user, is_blind=False)


@router.post("/{verification_id}/reverify")
def reverify_experience(
    request: Request,
    verification_id: int,
    blind_mode: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr)
):
    """
    Re-runs verification for a specific record.
    """
    v = db.query(ExperienceVerification).filter(ExperienceVerification.id == verification_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Verification record not found")

    is_blind = is_blind_mode_requested(request, blind_mode, current_user)
    updated_v = run_full_verification_pipeline(
        db=db,
        candidate_id=v.candidate_id,
        initiated_by_user_id=current_user.id,
        is_blind_mode=is_blind,
        is_reverification=True
    )

    candidate = db.query(Candidate).filter(Candidate.id == updated_v.candidate_id).first()
    user = db.query(User).filter(User.id == candidate.user_id).first() if (candidate and candidate.user_id) else None

    return _format_verification_response(updated_v, candidate, user, is_blind)
