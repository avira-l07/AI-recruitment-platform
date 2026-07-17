from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from datetime import datetime, timezone
from app.core.database import Base

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    file_name = Column(String)
    file_path = Column(String)
    extracted_text = Column(Text, nullable=True)
    parsed_data = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    # Cache and Career Analysis fields
    resume_hash = Column(String, nullable=True, index=True)
    local_analysis_json = Column(Text, nullable=True)
    gemini_analysis_json = Column(Text, nullable=True)
    combined_analysis_json = Column(Text, nullable=True)
    analysis_source = Column(String, default="local")
    status = Column(String, default="not_generated")
    error_type = Column(String, nullable=True)
    safe_error_message = Column(Text, nullable=True)
    gemini_model = Column(String, nullable=True)
    generation_started_at = Column(DateTime, nullable=True)
    generation_completed_at = Column(DateTime, nullable=True)
    last_attempt_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
