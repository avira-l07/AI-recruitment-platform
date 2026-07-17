from pydantic import BaseModel, Field
from typing import List

class GeminiCareerSuggestion(BaseModel):
    career_field: str
    description: str
    reason: str
    ai_analysis: str
    roadmap: List[str]

class GeminiEnhancementResponse(BaseModel):
    candidateSummary: str
    strengths: List[str]
    weaknesses: List[str]
    resumeImprovementTips: List[str]
    suggestions: List[GeminiCareerSuggestion]
