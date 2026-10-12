import pytest
from fastapi.testclient import TestClient
import app.models
from app.core.database import SessionLocal, Base, engine, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.user import User
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.application import Application
from app.models.prescreening import JobPrescreeningQuestion, ApplicationPrescreeningEvaluation
from app.services.prescreening.job_analyzer import analyze_job_requirements
from app.services.prescreening.question_generator import generate_prescreening_questions
from app.services.prescreening.response_evaluator import evaluate_prescreening_responses

# Recreate clean tables


@pytest.fixture(scope="function")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()



def test_job_analyzer_extracts_structured_requirements():
    reqs = analyze_job_requirements(
        title="Senior Python / FastAPI Engineer",
        description="Build high-concurrency microservices and optimize PostgreSQL queries. Design scalable APIs.",
        required_skills="Python, FastAPI, PostgreSQL, Docker, Git",
        experience_level="Senior",
        education_requirement="Bachelor's degree in CS"
    )
    assert "Python" in reqs["technical_skills"] or "FastAPI" in reqs["technical_skills"]
    assert len(reqs["technical_skills"]) >= 2
    assert len(reqs["important_concepts"]) >= 2
    assert reqs["role_complexity"] == "Senior"
    assert len(reqs["responsibilities"]) >= 1


def test_question_generator_produces_role_specific_questions():
    questions = generate_prescreening_questions(
        title="Backend Engineer",
        description="Design and maintain REST APIs using Python and SQL.",
        required_skills="Python, SQL, REST APIs, Git",
        experience_level="Mid"
    )
    assert len(questions) >= 3
    types = [q["question_type"] for q in questions]
    assert "technical" in types
    assert "scenario" in types
    for q in questions:
        assert "question_text" in q and len(q["question_text"]) > 10
        assert "scoring_criteria" in q
        assert "expected_concepts" in q


def test_response_evaluator_scores_candidate_answers():
    questions = [
        {
            "id": 1,
            "question_text": "Explain how you would design a REST API in FastAPI with validation.",
            "question_type": "technical",
            "scoring_criteria": "FastAPI, Pydantic, Validation, Dependency Injection",
            "expected_concepts": ["FastAPI", "Validation", "Pydantic", "Schema"],
            "weight": 1.0,
            "is_required": True
        }
    ]
    
    strong_answers = [
        {
            "question_id": 1,
            "answer_text": "I would structure the FastAPI service using Pydantic schemas for request and response validation, modular APIRouter instances, dependency injection for database sessions, and custom exception handlers for uniform error responses."
        }
    ]
    eval_strong = evaluate_prescreening_responses("FastAPI Developer", questions, strong_answers, "Candidate #C-1")
    assert eval_strong["overall_score"] >= 65
    assert eval_strong["overall_label"] in ["Strong", "Competent"]
    assert len(eval_strong["evaluations"]) == 1
    assert len(eval_strong["evaluations"][0]["key_strengths"]) >= 1

    minimal_answers = [
        {
            "question_id": 1,
            "answer_text": "I will write routes."
        }
    ]
    eval_minimal = evaluate_prescreening_responses("FastAPI Developer", questions, minimal_answers, "Candidate #C-1")
    assert eval_minimal["overall_score"] <= 60
    assert eval_minimal["overall_label"] in ["Developing", "Needs Review"]


def test_prescreening_api_and_application_integration(client, db_session):
    # Create HR user
    hr = User(id=987, email="hr_prescreen_unique@example.com", full_name="HR Lead Unique", role="hr", hashed_password="mock_hashed_pw")
    db_session.add(hr)
    
    # Create Candidate user
    cand_user = User(id=988, email="applicant_unique@example.com", full_name="Jane Applicant Unique", role="candidate", hashed_password="mock_hashed_pw")
    db_session.add(cand_user)
    
    # Create Candidate profile
    cand = Candidate(id=988, user_id=988, full_name="Jane Applicant Unique", email="applicant_unique@example.com", skills="Python, FastAPI, SQL")
    db_session.add(cand)

    # Create Job
    job = Job(id=989, title="FastAPI Engineer", description="Build APIs.", required_skills="Python, FastAPI, SQL", experience_level="Mid", created_by=987, status="Active")
    db_session.add(job)
    db_session.commit()

    hr_token = create_access_token({"sub": str(hr.id), "user_id": hr.id, "role": hr.role, "token_version": 1})
    cand_token = create_access_token({"sub": str(cand_user.id), "user_id": cand_user.id, "role": cand_user.role, "token_version": 1})

    # HR generates questions
    gen_res = client.post(f"/prescreening/job/{job.id}/generate?save_to_job=true", headers={"Authorization": f"Bearer {hr_token}"})
    assert gen_res.status_code == 200
    questions = gen_res.json()
    assert len(questions) >= 3

    # Candidate fetches questions
    get_res = client.get(f"/prescreening/job/{job.id}/questions", headers={"Authorization": f"Bearer {cand_token}"})
    assert get_res.status_code == 200
    assert len(get_res.json()) >= 3
    q1 = get_res.json()[0]

    # Candidate submits application with answers
    apply_res = client.post("/applications", json={
        "job_id": job.id,
        "prescreening_answers": [
            {
                "question_id": q["id"],
                "question_text": q["question_text"],
                "answer_text": "I design FastAPI microservices utilizing Pydantic models for strict data validation, dependency injection for SQLAlchemy sessions, and automated OpenAPI documentation."
            } for q in get_res.json()
        ]
    }, headers={"Authorization": f"Bearer {cand_token}"})
    assert apply_res.status_code == 200
    app_data = apply_res.json()
    assert app_data["has_prescreening"] is True
    assert app_data["prescreening_score"] is not None
    app_id = app_data["application_id"]

    # HR views evaluation in normal mode
    eval_res = client.get(f"/prescreening/application/{app_id}", headers={"Authorization": f"Bearer {hr_token}"})
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["has_evaluation"] is True
    assert eval_data["overall_score"] is not None
    assert "Jane Applicant Unique" in eval_data["candidate_name"]

    # HR views evaluation in Blind Screening mode
    blind_res = client.get(f"/prescreening/application/{app_id}", headers={"Authorization": f"Bearer {hr_token}", "X-Blind-Screening": "true"})
    assert blind_res.status_code == 200
    blind_data = blind_res.json()
    assert blind_data["is_blind_mode"] is True
    assert "Jane Applicant Unique" not in blind_data["candidate_name"]
    assert "Candidate #C-" in blind_data["candidate_name"]
