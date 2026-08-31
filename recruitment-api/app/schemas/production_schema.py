from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict

ApplicationStatus = Literal[
    "Applied",
    "AI Review",
    "Manual Review",
    "Shortlisted",
    "Interview",
    "Offer",
    "Hired",
    "Rejected",
    "Withdrawn",
]


class ApplyRequest(BaseModel):
    job_id: int = Field(..., gt=0)
    prescreening_answers: Optional[list[dict]] = Field(default=None)



class StatusUpdate(BaseModel):
    status: ApplicationStatus
    reason: Optional[str] = Field(default=None, max_length=500)


class ApplicationResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    status: str
    applied_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIProviderStatus(BaseModel):
    status: str
    available: bool
    configured: Optional[bool] = None
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    error_code: Optional[str] = None


class HybridStatus(BaseModel):
    status: str


class AIStatusResponse(BaseModel):
    mode: str
    current_stage: str
    local_ai: AIProviderStatus
    gemini: AIProviderStatus
    hybrid: HybridStatus
    fallback_active: bool
    fallback_reason: Optional[str] = None
    analysis_id: Optional[int] = None
    average_analysis_time: Optional[float] = None
    last_updated: datetime


class RecruiterAssistantRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=1000)
    conversation_id: Optional[str] = Field(default=None, max_length=80)


class RecruiterAction(BaseModel):
    type: str
    label: str
    candidate_id: Optional[int] = None
    job_id: Optional[int] = None


class RecruiterAssistantResponse(BaseModel):
    answer: str
    source: str
    conversation_id: str
    actions: list[RecruiterAction] = Field(default_factory=list)


class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    type: str
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel):
    items: list[Any]
    page: int
    page_size: int
    total: int
    pages: int
