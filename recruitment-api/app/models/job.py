from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from datetime import datetime
from app.core.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    required_skills = Column(Text)
    experience_level = Column(String)
    education_requirement = Column(String)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Active")          # "Active" or "Closed"
    closed_reason = Column(Text, nullable=True)
    closed_at = Column(DateTime, nullable=True)