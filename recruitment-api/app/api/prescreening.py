import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_hr
from app.core.time import utc_now
from app.models.job import Job
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.user import User
from app.models.prescreening import JobPrescreeningQuestion, ApplicationPrescreeningEvaluation
from app.services.prescreening.question_generator import generate_prescreening_questions
from app.services.prescreening.response_evaluator import evaluate_prescreening_responses
from app.services.blind_screening import is_blind_mode_requested, get_neutral_candidate_identifier, redact_text_pii

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/prescreening", tags=["prescreening"])


class QuestionCreateRequest(BaseModel):
    question_text: str = Field(..., min_length=5)
    question_type: str = Field(default="technical", pattern="^(technical|scenario|practical|problem_solving)$")
    category: Optional[str] = Field(default="Technical Skills")
    scoring_criteria: Optional[str] = Field(default=None)
    expected_concepts: Optional[List[str]] = Field(default_factory=list)
    weight: Optional[float] = Field(default=1.0, ge=0.5, le=3.0)
    is_required: Optional[bool] = Field(default=True)
    is_active: Optional[bool] = Field(default=True)


class BulkQuestionsUpdateRequest(BaseModel):
    questions: List[dict]


class CandidateAnswerItem(BaseModel):
    question_id: Optional[int] = None
    question_text: Optional[str] = None
    answer_text: str


class EvaluateAnswersRequest(BaseModel):
    answers: List[CandidateAnswerItem]


@router.get("/job/{job_id}/questions")
def get_job_prescreening_questions(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves all active pre-screening questions for a job.
    Accessible to candidates when applying and HR when reviewing.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    questions = db.query(JobPrescreeningQuestion).filter(
        JobPrescreeningQuestion.job_id == job_id,
        JobPrescreeningQuestion.is_active == True
    ).order_by(JobPrescreeningQuestion.order_index.asc(), JobPrescreeningQuestion.id.asc()).all()

    return [
        {
            "id": q.id,
            "job_id": q.job_id,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "category": q.category,
            "scoring_criteria": q.scoring_criteria,
            "expected_concepts": json.loads(q.expected_concepts) if q.expected_concepts else [],
            "weight": q.weight,
            "is_required": q.is_required,
            "order_index": q.order_index
        }
        for q in questions
    ]


@router.post("/job/{job_id}/generate")
def generate_questions_for_job(
    job_id: int,
    save_to_job: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr)
):
    """
    Generates AI pre-screening questions tailored to a specific job description.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    generated = generate_prescreening_questions(
        title=job.title,
        description=job.description or "",
        required_skills=job.required_skills or "",
        experience_level=job.experience_level or "Mid",
        education_requirement=job.education_requirement or ""
    )

    if save_to_job:
        # Deactivate previous questions and save new ones
        db.query(JobPrescreeningQuestion).filter(JobPrescreeningQuestion.job_id == job_id).update({"is_active": False})
        saved_questions = []
        for idx, q in enumerate(generated):
            new_q = JobPrescreeningQuestion(
                job_id=job_id,
                question_text=q["question_text"],
                question_type=q.get("question_type", "technical"),
                category=q.get("category", "Technical Skills"),
                scoring_criteria=q.get("scoring_criteria", ""),
                expected_concepts=json.dumps(q.get("expected_concepts", [])),
                weight=q.get("weight", 1.0),
                is_required=q.get("is_required", True),
                is_active=True,
                order_index=idx
            )
            db.add(new_q)
            saved_questions.append(new_q)
        db.commit()
        for sq in saved_questions:
            db.refresh(sq)

        return [
            {
                "id": sq.id,
                "job_id": sq.job_id,
                "question_text": sq.question_text,
                "question_type": sq.question_type,
                "category": sq.category,
                "scoring_criteria": sq.scoring_criteria,
                "expected_concepts": json.loads(sq.expected_concepts) if sq.expected_concepts else [],
                "weight": sq.weight,
                "is_required": sq.is_required,
                "order_index": sq.order_index
            }
            for sq in saved_questions
        ]

    return generated


@router.put("/job/{job_id}/questions")
def update_job_questions(
    job_id: int,
    payload: BulkQuestionsUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr)
):
    """
    Saves or updates HR-approved questions for a job.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Clear existing active questions for clean update
    db.query(JobPrescreeningQuestion).filter(JobPrescreeningQuestion.job_id == job_id).delete()
    
    saved_questions = []
    for idx, q in enumerate(payload.questions):
        concepts = q.get("expected_concepts", [])
        concepts_json = json.dumps(concepts) if isinstance(concepts, list) else concepts

        new_q = JobPrescreeningQuestion(
            job_id=job_id,
            question_text=q.get("question_text", ""),
            question_type=q.get("question_type", "technical"),
            category=q.get("category", "Technical Skills"),
            scoring_criteria=q.get("scoring_criteria", ""),
            expected_concepts=concepts_json,
            weight=float(q.get("weight", 1.0)),
            is_required=bool(q.get("is_required", True)),
            is_active=bool(q.get("is_active", True)),
            order_index=idx
        )
        db.add(new_q)
        saved_questions.append(new_q)

    db.commit()
    for sq in saved_questions:
        db.refresh(sq)

    return [
        {
            "id": sq.id,
            "job_id": sq.job_id,
            "question_text": sq.question_text,
            "question_type": sq.question_type,
            "category": sq.category,
            "scoring_criteria": sq.scoring_criteria,
            "expected_concepts": json.loads(sq.expected_concepts) if sq.expected_concepts else [],
            "weight": sq.weight,
            "is_required": sq.is_required,
            "order_index": sq.order_index
        }
        for sq in saved_questions
    ]


@router.get("/application/{application_id}")
def get_application_evaluation(
    request: Request,
    application_id: int,
    blind_mode: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr)
):
    """
    Retrieves the candidate's pre-screening questionnaire evaluation for an application.
    Supports Blind Screening / Fair Review Mode.
    """
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    candidate = db.query(Candidate).filter(Candidate.id == application.candidate_id).first()
    user = db.query(User).filter(User.id == candidate.user_id).first() if (candidate and candidate.user_id) else None
    
    is_blind = is_blind_mode_requested(request, blind_mode, current_user)
    neutral_id = get_neutral_candidate_identifier(candidate.id if candidate else 0)
    cand_name = neutral_id if is_blind else ((user.full_name if user else None) or candidate.full_name or neutral_id)

    eval_rec = db.query(ApplicationPrescreeningEvaluation).filter(
        ApplicationPrescreeningEvaluation.application_id == application_id
    ).first()

    if not eval_rec:
        return {
            "application_id": application_id,
            "has_evaluation": False,
            "overall_score": None,
            "overall_label": None,
            "evaluations": [],
            "summary": "No pre-screening assessment completed for this application."
        }

    evaluations = json.loads(eval_rec.evaluations_json) if eval_rec.evaluations_json else []
    summary = eval_rec.summary or ""
    if is_blind and summary:
        summary = redact_text_pii(summary, candidate_name=candidate.full_name if candidate else None, candidate_id=candidate.id if candidate else None)

    return {
        "id": eval_rec.id,
        "application_id": eval_rec.application_id,
        "candidate_id": eval_rec.candidate_id,
        "candidate_name": cand_name,
        "is_blind_mode": is_blind,
        "has_evaluation": True,
        "overall_score": eval_rec.overall_score,
        "overall_label": eval_rec.overall_label,
        "evaluations": evaluations,
        "summary": summary,
        "strengths_summary": eval_rec.strengths_summary,
        "gap_summary": eval_rec.gap_summary,
        "ai_source": eval_rec.ai_source,
        "created_at": eval_rec.created_at.isoformat() if eval_rec.created_at else None
    }
