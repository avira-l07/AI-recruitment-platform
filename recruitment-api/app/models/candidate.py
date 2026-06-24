from sqlalchemy import Column, Integer, String, Text, ForeignKey
from app.core.database import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    full_name = Column(String)
    email = Column(String)
    phone = Column(String, nullable=True)
    education = Column(Text, nullable=True)
    experience = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)
    projects = Column(Text, nullable=True)
    certifications = Column(Text, nullable=True)