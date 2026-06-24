from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class JobCreate(BaseModel):
    title: str
    description: str
    required_skills: str
    experience_level: str
    education_requirement: str

class JobResponse(BaseModel):
    id: int
    title: str
    description: str
    required_skills: str
    experience_level: str
    education_requirement: str
    created_at: datetime
    status: str
    closed_reason: Optional[str] = None
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True