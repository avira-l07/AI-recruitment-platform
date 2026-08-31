import json
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, DateTime
from app.core.database import Base
from app.core.time import utc_now


class ExperienceVerification(Base):
    __tablename__ = "experience_verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), index=True, nullable=False)
    verification_version = Column(Integer, default=1, nullable=False)
    status = Column(String, default="completed", nullable=False)  # queued, in_progress, completed, failed
    stage = Column(String, default="completed", nullable=False)   # queued, searching_company, validating_links, analyzing_projects, building_timeline, generating_ai_summary, completed
    
    # Trust Score & Primary Outcome
    trust_score = Column(Float, default=0.0, nullable=False)      # 0 - 100
    previous_trust_score = Column(Float, nullable=True)
    verification_outcome = Column(String, default="needs_review", nullable=False)  # strong_evidence, needs_review, suspicious, insufficient_evidence
    confidence_label = Column(String, default="Medium", nullable=False) # High, Medium, Low
    
    # Structured JSON Fields
    claims_json = Column(Text, nullable=True)                      # Extracted structured claims (internships, jobs, projects, certs)
    company_verifications_json = Column(Text, nullable=True)       # Company legitimacy, domain, SSL, tier
    internship_verifications_json = Column(Text, nullable=True)    # Internship authenticity & program checks
    project_verifications_json = Column(Text, nullable=True)       # GitHub/GitLab, demo, commit & README analysis
    timeline_intelligence_json = Column(Text, nullable=True)       # Visual timeline events, overlaps, gaps, sanity alerts
    certification_verifications_json = Column(Text, nullable=True) # Certification issuer & link validation
    resume_authenticity_json = Column(Text, nullable=True)         # AI resume analysis, formatting, white text checks
    evidence_sources_json = Column(Text, nullable=True)            # Evidence items with TIER 1 - 4 classification
    evidence_graph_json = Column(Text, nullable=True)              # Relationship graph (nodes, edges)
    trust_score_breakdown_json = Column(Text, nullable=True)       # Itemized points & explanation for score
    ai_reasoning_json = Column(Text, nullable=True)                # Grounded RecruitAI reasoning & interview questions
    
    # HR Manual Decision & Audit
    hr_decision = Column(String, nullable=True)                    # verified, needs_review, suspicious
    hr_decision_notes = Column(Text, nullable=True)
    hr_decided_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    hr_decided_at = Column(DateTime, nullable=True)
    
    # Versioning & Reverification History
    history_json = Column(Text, nullable=True)                     # List of previous verification snapshots
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
