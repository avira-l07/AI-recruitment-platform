import json
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, DateTime
from app.core.database import Base
from app.core.time import utc_now


class JobPrescreeningQuestion(Base):
    __tablename__ = "job_prescreening_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), index=True, nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String, default="technical", nullable=False)  # technical, scenario, practical, problem_solving
    category = Column(String, default="Technical Skills", nullable=False)
    scoring_criteria = Column(Text, nullable=True)                      # Guidelines on what a high-quality answer contains
    expected_concepts = Column(Text, nullable=True)                     # JSON list of expected keywords/concepts
    weight = Column(Float, default=1.0, nullable=False)                 # Relative scoring weight (e.g. 1.0, 1.5)
    is_required = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class ApplicationPrescreeningEvaluation(Base):
    __tablename__ = "application_prescreening_evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("applications.id"), unique=True, index=True, nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), index=True, nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), index=True, nullable=False)
    
    overall_score = Column(Float, default=0.0, nullable=False)          # 0 - 100
    overall_label = Column(String, default="Competent", nullable=False)  # Strong, Competent, Developing, Needs Review
    
    evaluations_json = Column(Text, nullable=True)                      # JSON list of per-question evaluations
    summary = Column(Text, nullable=True)                               # Executive summary of candidate responses
    strengths_summary = Column(Text, nullable=True)                     # Key demonstrated strengths
    gap_summary = Column(Text, nullable=True)                           # Technical gaps or unaddressed areas
    ai_source = Column(String, default="hybrid", nullable=False)        # gemini, local_ai, hybrid

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
