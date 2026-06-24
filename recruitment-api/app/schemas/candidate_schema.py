from pydantic import BaseModel
from typing import Optional

class CandidateResponse(BaseModel):
    id: int
    user_id: Optional[int]
    full_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    education: Optional[str]
    experience: Optional[str]
    skills: Optional[str]
    projects: Optional[str]
    certifications: Optional[str]

    class Config:
        from_attributes = True

class CandidateUpdate(BaseModel):
    phone: Optional[str] = None
    education: Optional[str] = None
    experience: Optional[str] = None
    skills: Optional[str] = None
    projects: Optional[str] = None
    certifications: Optional[str] = None