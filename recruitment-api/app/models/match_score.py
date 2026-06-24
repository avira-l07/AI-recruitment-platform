from sqlalchemy import Column, Integer, Float, String, Text, ForeignKey, DateTime
from datetime import datetime
from app.core.database import Base

class MatchScore(Base):
    __tablename__ = "match_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    score = Column(Float)
    matched_skills = Column(Text)
    missing_skills = Column(Text)
    explanation = Column(Text)
    status = Column(String, default="Pending")
    created_at = Column(DateTime, default=datetime.utcnow)