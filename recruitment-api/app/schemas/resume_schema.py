from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class ParsedResumeData(BaseModel):
    name: str
    email: Optional[str]
    phone: Optional[str]
    skills: List[str]
    education: List[str]
    experience: List[str]
    projects: List[str]
    certifications: List[str]

class ResumeResponse(BaseModel):
    id: int
    candidate_id: int
    file_name: str
    uploaded_at: datetime
    parsed_data: Any

    class Config:
        from_attributes = True