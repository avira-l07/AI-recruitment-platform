from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.core.time import utc_now
from app.core.database import Base


class AIAnalysisJob(Base):
    __tablename__ = "ai_analysis_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True, index=True)
    operation = Column(String, nullable=False, default="candidate_job_match")
    requested_mode = Column(String, nullable=False, default="hybrid")
    actual_mode = Column(String, nullable=True)
    current_stage = Column(String, nullable=False, default="queued", index=True)
    local_status = Column(String, nullable=False, default="waiting")
    gemini_status = Column(String, nullable=False, default="waiting")
    hybrid_status = Column(String, nullable=False, default="waiting")
    fallback_active = Column(Boolean, nullable=False, default=False)
    fallback_reason = Column(Text, nullable=True)
    error_code = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    safe_error_message = Column(Text, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)


class AIActivity(Base):
    __tablename__ = "ai_activity"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_job_id = Column(Integer, ForeignKey("ai_analysis_jobs.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    event_type = Column(String, nullable=False, index=True)
    message = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="info")
    created_at = Column(DateTime, nullable=False, default=utc_now, index=True)
