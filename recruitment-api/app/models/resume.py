from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from datetime import datetime
from app.core.database import Base

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    file_name = Column(String)
    file_path = Column(String)
    extracted_text = Column(Text, nullable=True)
    parsed_data = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)