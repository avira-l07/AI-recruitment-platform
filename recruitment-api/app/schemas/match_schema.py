from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MatchRequest(BaseModel):
    candidate_id: int
    job_id: int

class MatchResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    score: float
    matched_skills: str
    missing_skills: str
    explanation: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class StatusUpdate(BaseModel):
    status: str