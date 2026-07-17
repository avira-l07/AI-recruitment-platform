from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint

from app.core.time import utc_now
from app.core.database import Base


class MatchScore(Base):
    __tablename__ = "match_scores"
    __table_args__ = (
        UniqueConstraint("application_id", name="uq_match_score_application"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    score = Column(Float, nullable=False, default=0)
    fit_label = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    confidence_label = Column(String, nullable=True)
    matched_skills = Column(Text, nullable=True)
    missing_skills = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    status = Column(String, nullable=True, default="Pending")
    ai_source = Column(String, nullable=False, default="local_ai")
    local_completed = Column(Boolean, nullable=False, default=True)
    gemini_completed = Column(Boolean, nullable=False, default=False)
    hybrid_completed = Column(Boolean, nullable=False, default=False)
    fallback_active = Column(Boolean, nullable=False, default=False)
    fallback_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
