import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.resume import Resume
from app.models.user import User
from app.models.verification import ExperienceVerification
from app.services.claim_extractor import extract_all_candidate_claims
from app.services.company_verifier import verify_company_claim, verify_internship_authenticity
from app.services.project_verifier import verify_all_projects
from app.services.timeline_engine import build_timeline_intelligence
from app.services.certification_verifier import verify_all_certifications
from app.services.resume_authenticity_analyzer import analyze_resume_authenticity
from app.services.trust_score_engine import calculate_trust_score, build_evidence_graph
from app.ai.verification_advisor import generate_grounded_verification_reasoning
from app.utils.activity_logger import publish_event
from app.core.time import utc_now

logger = logging.getLogger(__name__)


def run_full_verification_pipeline(
    db: Session,
    candidate_id: int,
    initiated_by_user_id: Optional[int] = None,
    is_blind_mode: bool = False,
    is_reverification: bool = False
) -> ExperienceVerification:
    """
    Orchestrates the entire enterprise experience verification workflow.
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise ValueError(f"Candidate with ID {candidate_id} not found.")

    user = db.query(User).filter(User.id == candidate.user_id).first() if candidate.user_id else None
    cand_name = (user.full_name if user else None) or candidate.full_name or f"Candidate #C-{candidate_id}"

    resume = db.query(Resume).filter(Resume.candidate_id == candidate.id).order_by(Resume.id.desc()).first()
    resume_parsed = None
    if resume and resume.parsed_data:
        try:
            resume_parsed = json.loads(resume.parsed_data)
        except Exception:
            pass

    # Publish audit event: started
    event_type = "verification_reverified" if is_reverification else "verification_started"
    publish_event(
        db,
        event_type=event_type,
        candidate_id=candidate.id,
        user_id=initiated_by_user_id,
        details={"candidate_id": candidate.id, "candidate_name": cand_name, "is_blind_mode": is_blind_mode}
    )

    # 1. Extract Structured Claims
    raw_claims = extract_all_candidate_claims(candidate, resume_parsed)
    raw_claims["_verification_engine_version"] = 2
    raw_claims["_resume_hash"] = resume.resume_hash if resume else None
    experiences = raw_claims.get("experiences", [])
    projects = raw_claims.get("projects", [])
    certifications = raw_claims.get("certifications", [])

    # 2. Company Legitimacy & Internship Authenticity Verification
    company_verifications = []
    internship_verifications = []
    all_evidence_sources = []

    for exp in experiences:
        comp_res = verify_company_claim(
            company_name=exp.get("company_name", "Company"),
            claimed_urls=exp.get("claimed_urls", []),
            claimed_tech=exp.get("technologies", [])
        )
        company_verifications.append(comp_res)
        all_evidence_sources.extend(comp_res.get("evidence_sources", []))

        intern_res = verify_internship_authenticity(exp, comp_res)
        internship_verifications.append(intern_res)

    # 3. Project & Repository Verification
    project_verifications = verify_all_projects(projects)
    for p in project_verifications:
        all_evidence_sources.extend(p.get("evidence_sources", []))

    # 4. Certification Verification
    certification_verifications = verify_all_certifications(certifications)
    for c in certification_verifications:
        all_evidence_sources.extend(c.get("evidence_sources", []))

    # 5. Timeline Intelligence
    timeline_data = build_timeline_intelligence(
        experiences=experiences,
        projects=projects,
        certifications=certifications,
        education_text=raw_claims.get("education")
    )

    # 6. Resume Authenticity Analysis
    raw_resume_text = resume.extracted_text if (resume and resume.extracted_text) else f"{candidate.experience} {candidate.projects} {candidate.skills}"
    resume_authenticity = analyze_resume_authenticity(raw_resume_text)

    # 7. Deduplicate Evidence Sources
    seen_urls = set()
    unique_sources = []
    for s in all_evidence_sources:
        u = s.get("url")
        if u and u not in seen_urls:
            seen_urls.add(u)
            unique_sources.append(s)

    # 8. Compute Trust Score & Outcome
    trust_result = calculate_trust_score(
        company_verifications=company_verifications,
        internship_verifications=internship_verifications,
        project_verifications=project_verifications,
        timeline_data=timeline_data,
        certification_verifications=certification_verifications,
        resume_authenticity=resume_authenticity,
        all_evidence_sources=unique_sources
    )

    trust_score = trust_result["trust_score"]
    outcome = trust_result["outcome"]
    conf_label = trust_result["confidence_label"]
    fraud_flags = trust_result["fraud_flags"]

    # 9. Build Evidence Graph
    evidence_graph = build_evidence_graph(
        candidate_id=candidate.id,
        candidate_name=cand_name,
        company_verifications=company_verifications,
        project_verifications=project_verifications,
        certification_verifications=certification_verifications,
        evidence_sources=unique_sources
    )

    # 10. AI Grounded Reasoning
    ai_reasoning = generate_grounded_verification_reasoning(
        candidate_id=candidate.id,
        candidate_name=cand_name,
        trust_score=trust_score,
        outcome=outcome,
        company_verifications=company_verifications,
        internship_verifications=internship_verifications,
        project_verifications=project_verifications,
        timeline_data=timeline_data,
        certification_verifications=certification_verifications,
        evidence_sources=unique_sources,
        fraud_flags=fraud_flags,
        is_blind_mode=is_blind_mode
    )

    # 11. Check Existing Verification Record for Versioning & History
    existing = db.query(ExperienceVerification).filter(ExperienceVerification.candidate_id == candidate.id).first()
    
    history_list = []
    prev_score = None
    version = 1

    if existing:
        prev_score = existing.trust_score
        version = (existing.verification_version or 1) + 1
        if existing.history_json:
            try:
                history_list = json.loads(existing.history_json)
            except Exception:
                pass
        
        # Archive previous snapshot
        history_list.append({
            "version": existing.verification_version,
            "trust_score": existing.trust_score,
            "outcome": existing.verification_outcome,
            "hr_decision": existing.hr_decision,
            "hr_decision_notes": existing.hr_decision_notes,
            "hr_decided_by": existing.hr_decided_by,
            "hr_decided_at": existing.hr_decided_at.isoformat() if existing.hr_decided_at else None,
            "verified_at": existing.updated_at.isoformat() if existing.updated_at else str(utc_now())
        })

    verification_rec = existing or ExperienceVerification(candidate_id=candidate.id)
    verification_rec.verification_version = version
    verification_rec.status = "completed"
    verification_rec.stage = "completed"
    verification_rec.previous_trust_score = prev_score
    verification_rec.trust_score = trust_score
    verification_rec.verification_outcome = outcome
    verification_rec.confidence_label = conf_label
    # A decision about a previous evidence snapshot must be reviewed again.
    verification_rec.hr_decision = None
    verification_rec.hr_decision_notes = None
    verification_rec.hr_decided_by = None
    verification_rec.hr_decided_at = None
    
    verification_rec.claims_json = json.dumps(raw_claims)
    verification_rec.company_verifications_json = json.dumps(company_verifications)
    verification_rec.internship_verifications_json = json.dumps(internship_verifications)
    verification_rec.project_verifications_json = json.dumps(project_verifications)
    verification_rec.timeline_intelligence_json = json.dumps(timeline_data)
    verification_rec.certification_verifications_json = json.dumps(certification_verifications)
    verification_rec.resume_authenticity_json = json.dumps(resume_authenticity)
    verification_rec.evidence_sources_json = json.dumps(unique_sources)
    verification_rec.evidence_graph_json = json.dumps(evidence_graph)
    verification_rec.trust_score_breakdown_json = json.dumps(trust_result["breakdown"])
    verification_rec.ai_reasoning_json = json.dumps(ai_reasoning)
    verification_rec.history_json = json.dumps(history_list)
    verification_rec.updated_at = utc_now()

    if not existing:
        db.add(verification_rec)
    
    db.commit()
    db.refresh(verification_rec)

    # Publish audit event: completed
    publish_event(
        db,
        event_type="verification_completed",
        candidate_id=candidate.id,
        user_id=initiated_by_user_id,
        details={
            "candidate_id": candidate.id,
            "verification_id": verification_rec.id,
            "trust_score": trust_score,
            "outcome": outcome,
            "version": version
        }
    )
    db.commit()
    return verification_rec
