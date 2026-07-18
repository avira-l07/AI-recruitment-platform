import pytest
import json
import hashlib
import os
import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.models.user import User
from app.models.candidate import Candidate
from app.models.resume import Resume
from app.models.job import Job
from app.models.match_score import MatchScore
from app.ai import career_advisor
from app.ai import resume_intelligence
from app.api import resumes

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_recruitment.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    try:
        Base.metadata.drop_all(bind=engine)
    except Exception:
        pass
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        cand1 = User(id=1, email="cand1@test.com", full_name="Candidate One", hashed_password="hashed_password", role="candidate")
        cand2 = User(id=2, email="cand2@test.com", full_name="Candidate Two", hashed_password="hashed_password", role="candidate")
        hr = User(id=3, email="hr@test.com", full_name="HR Manager", hashed_password="hashed_password", role="hr")
        
        db.add_all([cand1, cand2, hr])
        db.flush()
        
        c_prof1 = Candidate(id=1, user_id=1, full_name="Candidate One", email="cand1@test.com", skills="Python, SQL")
        c_prof2 = Candidate(id=2, user_id=2, full_name="Candidate Two", email="cand2@test.com", skills="React, HTML")
        
        db.add_all([c_prof1, c_prof2])
        
        job = Job(id=1, title="ML/AI Engineer", description="ML description", required_skills="Python, Machine Learning", experience_level="Mid", education_requirement="Bachelors", status="Active")
        db.add(job)
        
        db.commit()
    finally:
        db.close()
    yield
    engine.dispose()
    if os.path.exists("test_recruitment.db"):
        try:
            os.remove("test_recruitment.db")
        except Exception:
            pass

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def get_auth_headers(user_id: int, role: str):
    token = create_access_token({"user_id": user_id, "role": role})
    return {"Authorization": f"Bearer {token}"}

def ensure_resume_exists(db):
    resume = db.query(Resume).filter(Resume.candidate_id == 1).first()
    parsed_mock = {
        "name": "Candidate One",
        "email": "cand1@test.com",
        "skills": ["Python", "Machine Learning", "Deep Learning", "SQL", "Java"],
        "education": "BS CS",
        "experience": "1 year dev",
        "projects": "Project test",
        "certifications": "AWS Developer"
    }
    if not resume:
        resume = Resume(
            candidate_id=1,
            file_name="test.pdf",
            file_path="uploads/test.pdf",
            extracted_text="Python Machine Learning Deep Learning SQL Java BS CS 1 year dev",
            parsed_data=json.dumps(parsed_mock),
            resume_hash="initial_hash_1",
            status="local_ready",
            analysis_source="local"
        )
        db.add(resume)
    else:
        resume.parsed_data = json.dumps(parsed_mock)
        resume.extracted_text = "Python Machine Learning Deep Learning SQL Java BS CS 1 year dev"
        resume.local_analysis_json = None
        resume.combined_analysis_json = None
    db.commit()
    return resume

# ==============================================================================
# SEC 1-9: Authentication & Role Enforcement Tests
# ==============================================================================

def test_unauthenticated_candidates_route():
    response = client.get("/candidates")
    assert response.status_code == 401

def test_unauthenticated_resumes_route():
    response = client.get("/resumes/1")
    assert response.status_code == 401

def test_unauthenticated_jobs_mutation():
    response = client.post("/jobs", json={"title": "ML", "description": "desc", "required_skills": "Python, SQL", "experience_level": "Mid", "education_requirement": "Bachelors"})
    assert response.status_code == 401
    
    response = client.put("/jobs/1/close", json={"reason": "filled"})
    assert response.status_code == 401

def test_unauthenticated_matching_route():
    response = client.get("/matching/all")
    assert response.status_code == 401
    
    response = client.post("/matching/apply", json={"user_id": 1, "job_id": 1})
    assert response.status_code == 401

def test_unauthenticated_analytics_route():
    response = client.get("/analytics/overview")
    assert response.status_code == 401

def test_candidate_ownership_violation():
    headers = get_auth_headers(user_id=1, role="candidate")
    response = client.get("/resumes/2", headers=headers)
    assert response.status_code == 403

def test_candidate_attempting_hr_analytics():
    headers = get_auth_headers(user_id=1, role="candidate")
    response = client.get("/analytics/overview", headers=headers)
    assert response.status_code == 403

def test_candidate_attempting_job_mutation():
    headers = get_auth_headers(user_id=1, role="candidate")
    response = client.post("/jobs", json={"title": "ML", "description": "desc", "required_skills": "Python, SQL", "experience_level": "Mid", "education_requirement": "Bachelors"}, headers=headers)
    assert response.status_code == 403

def test_hr_authorized_candidate_listing():
    headers = get_auth_headers(user_id=3, role="hr")
    response = client.get("/candidates", headers=headers)
    assert response.status_code == 200

# ==============================================================================
# GEM 1-4: Gemini Request Control & Cache Behavior Tests
# ==============================================================================

def test_get_suggestions_makes_zero_gemini_calls(monkeypatch):
    db = TestingSessionLocal()
    ensure_resume_exists(db)
    db.close()

    def mock_call_gemini_json(prompt, model="gemini-2.5-flash"):
        pytest.fail("Gemini was called during GET suggestions!")

    monkeypatch.setattr(career_advisor, "call_gemini_json", mock_call_gemini_json)

    headers = get_auth_headers(user_id=1, role="candidate")
    response = client.get("/resumes/1/career-suggestions", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "local_ready"

def test_dashboard_read_flow_makes_zero_gemini_calls(monkeypatch):
    db = TestingSessionLocal()
    ensure_resume_exists(db)
    db.close()

    def mock_call_gemini_json(prompt, model="gemini-2.5-flash"):
        pytest.fail("Gemini was called during dashboard read flow!")

    monkeypatch.setattr(career_advisor, "call_gemini_json", mock_call_gemini_json)

    headers = get_auth_headers(user_id=1, role="candidate")
    
    res1 = client.get("/resumes/1/career-suggestions", headers=headers)
    assert res1.status_code == 200
    
    res2 = client.get("/matching/candidate/1", headers=headers)
    assert res2.status_code == 200

def test_resume_upload_makes_zero_automatic_gemini_calls(monkeypatch):
    def mock_call_gemini_json(prompt, model="gemini-2.5-flash"):
        pytest.fail("Gemini was called automatically during upload!")

    monkeypatch.setattr(resumes, "_extract_text", lambda path: "Some dummy long text to satisfy word count requirements. " * 20)
    monkeypatch.setattr(resumes, "parse_resume", lambda text: {
        "name": "Candidate One",
        "email": "c1@test.com",
        "phone": "555-1234",
        "skills": ["Python", "SQL", "Git", "Docker", "FastAPI"],
        "education": "BS CS",
        "experience": "2 years engineer",
        "projects": "Test Project",
        "certifications": "AWS",
        "word_count": 100
    })

    monkeypatch.setattr(career_advisor, "call_gemini_json", mock_call_gemini_json)
    monkeypatch.setattr(resume_intelligence, "call_gemini_json", mock_call_gemini_json)

    headers = get_auth_headers(user_id=1, role="candidate")
    
    import io
    dummy_file = io.BytesIO(b"%PDF-1.4\n" + b"This is dummy text data inside file stream" * 15)
    
    response = client.post(
        "/resumes/upload",
        data={"user_id": 1},
        files={"file": ("resume.pdf", dummy_file, "application/pdf")},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["parsedResult"]["name"] == "Candidate One"

def test_one_generation_action_makes_one_gemini_call(monkeypatch):
    db = TestingSessionLocal()
    ensure_resume_exists(db)
    db.close()

    gemini_calls = 0

    def mock_call_gemini_json(prompt, model="gemini-2.5-flash"):
        nonlocal gemini_calls
        gemini_calls += 1
        return {
            "candidateSummary": "Summary enhanced",
            "strengths": ["Strong coding"],
            "weaknesses": ["No UI design"],
            "resumeImprovementTips": ["Learn Figma"],
            "suggestions": [
                {
                    "career_field": "AI/ML Engineer",
                    "description": "ML Enhanced field",
                    "reason": "Tailored reason",
                    "ai_analysis": "Deep analysis text",
                    "roadmap": ["Step 1", "Step 2"]
                }
            ]
        }

    monkeypatch.setattr(career_advisor, "call_gemini_json", mock_call_gemini_json)

    headers = get_auth_headers(user_id=1, role="candidate")
    response = client.post("/resumes/1/career-suggestions/generate?force=true", headers=headers)
    assert response.status_code == 200
    assert gemini_calls == 1

def test_all_career_roles_sent_in_one_call(monkeypatch):
    db = TestingSessionLocal()
    ensure_resume_exists(db)
    # Force local_ready status
    db_res = db.query(Resume).filter(Resume.candidate_id == 1).first()
    db_res.status = "local_ready"
    db_res.combined_analysis_json = None
    db.commit()
    db.close()

    captured_prompt = None

    def mock_call_gemini_json(prompt, model="gemini-2.5-flash"):
        nonlocal captured_prompt
        captured_prompt = prompt
        return {
            "candidateSummary": "Enhanced Summary",
            "strengths": ["ML algorithms"],
            "weaknesses": ["Frontend"],
            "resumeImprovementTips": ["Learn design"],
            "suggestions": [
                {
                    "career_field": field.get("career_field"),
                    "description": "Enhanced",
                    "reason": "Matches",
                    "ai_analysis": "AI text",
                    "roadmap": ["Step 1"]
                } for field in career_advisor.CAREER_FIELDS[:5]
            ]
        }

    monkeypatch.setattr(career_advisor, "call_gemini_json", mock_call_gemini_json)

    headers = get_auth_headers(user_id=1, role="candidate")
    client.post("/resumes/1/career-suggestions/generate?force=true", headers=headers)
    
    print("CAPTURED PROMPT IS:")
    print(captured_prompt)
    assert captured_prompt is not None
    assert "AI/ML Engineer" in captured_prompt
    assert "Python Developer" in captured_prompt
    assert "Big Data Engineer" in captured_prompt

def test_completed_cache_avoids_gemini(monkeypatch):
    db = TestingSessionLocal()
    resume = ensure_resume_exists(db)
    # Artificially set cached complete state
    resume.status = "completed"
    resume.combined_analysis_json = json.dumps({
        "candidateSummary": "Cached summary",
        "strengths": ["ML"],
        "weaknesses": ["None"],
        "resumeImprovementTips": [],
        "suggestions": []
    })
    db.commit()
    db.close()

    def mock_call_gemini_json(prompt, model="gemini-2.5-flash"):
        pytest.fail("Gemini should not be called when cached result is completed and valid!")

    monkeypatch.setattr(career_advisor, "call_gemini_json", mock_call_gemini_json)

    headers = get_auth_headers(user_id=1, role="candidate")
    
    response = client.post("/resumes/1/career-suggestions/generate?force=false", headers=headers)
    assert response.status_code == 200
    assert response.json()["cache_status"] == "hit"

def test_changed_resume_invalidates_old_cache(monkeypatch):
    db = TestingSessionLocal()
    ensure_resume_exists(db)
    db_res = db.query(Resume).filter(Resume.candidate_id == 1).first()
    db_res.resume_hash = "entirely_new_resume_hash_value"
    db_res.status = "local_ready"
    db_res.combined_analysis_json = None
    db.commit()
    db.close()

    gemini_calls = 0

    def mock_call_gemini_json(prompt, model="gemini-2.5-flash"):
        nonlocal gemini_calls
        gemini_calls += 1
        return {
            "candidateSummary": "New Enhanced Summary",
            "strengths": ["New ML strengths"],
            "weaknesses": ["None"],
            "resumeImprovementTips": ["Tip 1"],
            "suggestions": [
                {
                    "career_field": "AI/ML Engineer",
                    "description": "New Enhanced",
                    "reason": "New Matches",
                    "ai_analysis": "New AI text",
                    "roadmap": ["New Step 1"]
                }
            ]
        }

    monkeypatch.setattr(career_advisor, "call_gemini_json", mock_call_gemini_json)

    headers = get_auth_headers(user_id=1, role="candidate")
    
    res_get = client.get("/resumes/1/career-suggestions", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["cache_status"] == "miss"
    assert res_get.json()["status"] == "local_ready"
    assert gemini_calls == 0

    res_gen = client.post("/resumes/1/career-suggestions/generate", headers=headers)
    assert res_gen.status_code == 200
    assert gemini_calls == 1

# ==============================================================================
# CONC 1-2: Concurrency & Stale State Recovery Tests
# ==============================================================================

def test_two_concurrent_generation_requests_make_one_provider_call():
    db = TestingSessionLocal()
    ensure_resume_exists(db)
    db_res = db.query(Resume).filter(Resume.candidate_id == 1).first()
    db_res.status = "generating"
    db_res.generation_started_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    db.commit()
    db.close()

    headers = get_auth_headers(user_id=1, role="candidate")
    response = client.post("/resumes/1/career-suggestions/generate", headers=headers)
    assert response.status_code == 409

def test_stale_processing_state_recovers(monkeypatch):
    db = TestingSessionLocal()
    ensure_resume_exists(db)
    db_res = db.query(Resume).filter(Resume.candidate_id == 1).first()
    db_res.status = "generating"
    db_res.generation_started_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - datetime.timedelta(minutes=6)
    db.commit()
    db.close()

    def mock_call_gemini_json(prompt, model="gemini-2.5-flash"):
        return {
            "candidateSummary": "Stale Recovered Summary",
            "strengths": ["ML coding"],
            "weaknesses": ["None"],
            "resumeImprovementTips": ["None"],
            "suggestions": [
                {
                    "career_field": "AI/ML Engineer",
                    "description": "Recovered Enhanced",
                    "reason": "Recovered Matches",
                    "ai_analysis": "Recovered AI text",
                    "roadmap": ["Recovered Step 1"]
                }
            ]
        }

    monkeypatch.setattr(career_advisor, "call_gemini_json", mock_call_gemini_json)

    headers = get_auth_headers(user_id=1, role="candidate")
    response = client.post("/resumes/1/career-suggestions/generate", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

# ==============================================================================
# ERR 1-5: Error Classification & Local-First Integrity Tests
# ==============================================================================

def test_quota_error_returns_complete_local_hybrid_output(monkeypatch):
    db = TestingSessionLocal()
    ensure_resume_exists(db)
    db_res = db.query(Resume).filter(Resume.candidate_id == 1).first()
    db_res.status = "local_ready"
    db.commit()
    db.close()

    def mock_call_gemini_json(prompt, model="gemini-2.5-flash"):
        raise Exception("API quota limit exhausted. ResourceHasBeenExhausted.")

    monkeypatch.setattr(career_advisor, "call_gemini_json", mock_call_gemini_json)

    headers = get_auth_headers(user_id=1, role="candidate")
    response = client.post("/resumes/1/career-suggestions/generate?force=true", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert data["error_type"] == "quota_exceeded"
    assert len(data["suggestions"]) > 0

def test_timeout_returns_complete_local_hybrid_output(monkeypatch):
    db = TestingSessionLocal()
    ensure_resume_exists(db)
    db_res = db.query(Resume).filter(Resume.candidate_id == 1).first()
    db_res.status = "local_ready"
    db.commit()
    db.close()

    def mock_call_gemini_json(prompt, model="gemini-2.5-flash"):
        raise Exception("Request timeout occurred connection closed.")

    monkeypatch.setattr(career_advisor, "call_gemini_json", mock_call_gemini_json)

    headers = get_auth_headers(user_id=1, role="candidate")
    response = client.post("/resumes/1/career-suggestions/generate?force=true", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert data["error_type"] == "timeout"
    assert len(data["suggestions"]) > 0

def test_invalid_key_returns_complete_local_hybrid_output(monkeypatch):
    db = TestingSessionLocal()
    ensure_resume_exists(db)
    db_res = db.query(Resume).filter(Resume.candidate_id == 1).first()
    db_res.status = "local_ready"
    db.commit()
    db.close()

    def mock_call_gemini_json(prompt, model="gemini-2.5-flash"):
        raise Exception("Invalid API key provided. Unauthorized access.")

    monkeypatch.setattr(career_advisor, "call_gemini_json", mock_call_gemini_json)

    headers = get_auth_headers(user_id=1, role="candidate")
    response = client.post("/resumes/1/career-suggestions/generate?force=true", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert data["error_type"] == "invalid_api_key"
    assert len(data["suggestions"]) > 0

def test_malformed_json_returns_complete_local_hybrid_output(monkeypatch):
    db = TestingSessionLocal()
    ensure_resume_exists(db)
    db_res = db.query(Resume).filter(Resume.candidate_id == 1).first()
    db_res.status = "local_ready"
    db.commit()
    db.close()

    def mock_call_gemini_json(prompt, model="gemini-2.5-flash"):
        return {"candidateSummary": "invalid schema data"}

    monkeypatch.setattr(career_advisor, "call_gemini_json", mock_call_gemini_json)

    headers = get_auth_headers(user_id=1, role="candidate")
    response = client.post("/resumes/1/career-suggestions/generate?force=true", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert len(data["suggestions"]) > 0

def test_gemini_response_cannot_alter_deterministic_scores(monkeypatch):
    db = TestingSessionLocal()
    cand = db.query(Candidate).filter(Candidate.user_id == 1).first()
    resume = db.query(Resume).filter(Resume.candidate_id == 1).first()
    print("DEBUG CANDIDATE:", cand.id if cand else "NONE")
    print("DEBUG RESUME:", resume.id if resume else "NONE", "CANDIDATE_ID:", resume.candidate_id if resume else "NONE")
    ensure_resume_exists(db)
    db_res = db.query(Resume).filter(Resume.candidate_id == 1).first()
    db_res.status = "local_ready"
    db.commit()
    db.close()

    def mock_call_gemini_json(prompt, model="gemini-2.5-flash"):
        return {
            "candidateSummary": "Summary",
            "strengths": ["ML"],
            "weaknesses": ["None"],
            "resumeImprovementTips": ["None"],
            "suggestions": [
                {
                    "career_field": "AI/ML Engineer",
                    "fit_score": 999, 
                    "fit_label": "Fake Strong Fit", 
                    "description": "Enhanced description text",
                    "reason": "Matches",
                    "ai_analysis": "AI text",
                    "roadmap": ["Step 1"]
                }
            ]
        }

    monkeypatch.setattr(career_advisor, "call_gemini_json", mock_call_gemini_json)

    headers = get_auth_headers(user_id=1, role="candidate")
    response = client.post("/resumes/1/career-suggestions/generate?force=true", headers=headers)
    print("STATUS:", response.status_code)
    print("JSON:", response.json())
    assert response.status_code == 200
    suggestions = response.json()["suggestions"]
    ml_sug = next(s for s in suggestions if s["career_field"] == "AI/ML Engineer")
    assert ml_sug["fit_score"] != 999
    assert ml_sug["fit_label"] != "Fake Strong Fit"

def test_old_and_new_response_fields_normalize_correctly(monkeypatch):
    db = TestingSessionLocal()
    ensure_resume_exists(db)
    db.close()

    headers = get_auth_headers(user_id=1, role="candidate")
    response = client.get("/resumes/1/career-suggestions", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    for sug in data["suggestions"]:
        assert "fit_score" in sug
        assert "fit_label" in sug

# ==============================================================================
# PASS 2: Real-Time SSE & ActivityEvent Logging Tests
# ==============================================================================

def test_unauthenticated_events_routes():
    res1 = client.get("/analytics/events")
    assert res1.status_code == 401

    res2 = client.get("/analytics/events/stream")
    assert res2.status_code == 401

def test_candidate_forbidden_events_routes():
    headers = get_auth_headers(user_id=1, role="candidate")
    headers["x-test-single-run"] = "true"
    res1 = client.get("/analytics/events", headers=headers)
    assert res1.status_code == 403

    res2 = client.get("/analytics/events/stream", headers=headers)
    assert res2.status_code == 403

def test_hr_authorized_events_routes(monkeypatch):
    monkeypatch.setattr("app.api.analytics.SessionLocal", TestingSessionLocal)
    headers = get_auth_headers(user_id=3, role="hr")
    res1 = client.get("/analytics/events", headers=headers)
    assert res1.status_code == 200

    headers["x-test-single-run"] = "true"
    res2 = client.get("/analytics/events/stream", headers=headers)
    assert res2.status_code == 200
    assert ": keepalive" in res2.text

def test_event_persistence_and_logging(monkeypatch):
    monkeypatch.setattr("app.api.analytics.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(resumes, "_extract_text", lambda path: "Some dummy long text to satisfy word count requirements. " * 20)
    monkeypatch.setattr(resumes, "parse_resume", lambda text: {
        "name": "Candidate One",
        "email": "c1@test.com",
        "phone": "555-1234",
        "skills": ["Python", "SQL", "Git", "Docker", "FastAPI"],
        "education": "BS CS",
        "experience": "2 years engineer",
        "projects": "Test Project",
        "certifications": "AWS",
        "word_count": 100
    })

    db = TestingSessionLocal()
    # Clean previous events to make assertion exact
    from app.models.activity_event import ActivityEvent
    db.query(ActivityEvent).delete()
    db.commit()
    db.close()

    headers = get_auth_headers(user_id=1, role="candidate")
    
    # Upload resume (should trigger resume_uploaded and resume_analyzed events)
    import io
    dummy_file = io.BytesIO(b"%PDF-1.4\n" + b"This is dummy text data inside file stream" * 15)
    response = client.post(
        "/resumes/upload",
        data={"user_id": 1},
        files={"file": ("resume.pdf", dummy_file, "application/pdf")},
        headers=headers
    )
    assert response.status_code == 200

    # Get events history as HR
    hr_headers = get_auth_headers(user_id=3, role="hr")
    events_res = client.get("/analytics/events", headers=hr_headers)
    assert events_res.status_code == 200
    events = events_res.json()
    
    # Verify that new lifecycle events are written to DB
    types = [e["event_type"] for e in events]
    assert "resume_parsing_started" in types
    assert "resume_parsed" in types
    assert "local_analysis_completed" in types

def test_stream_last_event_id_filter(monkeypatch):
    monkeypatch.setattr("app.api.analytics.SessionLocal", TestingSessionLocal)
    # Insert mock events
    db = TestingSessionLocal()
    from app.models.activity_event import ActivityEvent
    db.query(ActivityEvent).delete()
    
    ev1 = ActivityEvent(event_type="test_event_A", details_json="{}")
    ev2 = ActivityEvent(event_type="test_event_B", details_json="{}")
    ev3 = ActivityEvent(event_type="test_event_C", details_json="{}")
    db.add_all([ev1, ev2, ev3])
    db.commit()
    
    id1, id2, id3 = ev1.id, ev2.id, ev3.id
    db.close()

    hr_headers = get_auth_headers(user_id=3, role="hr")
    hr_headers["x-test-single-run"] = "true"
    
    # Connect to stream passing last_event_id = id2
    # Should only return events after id2 (i.e. test_event_C)
    response = client.get(f"/analytics/events/stream?last_event_id={id2}", headers=hr_headers)
    assert response.status_code == 200
    
    lines = response.text.split("\n")
    found = False
    for line_str in lines:
        line_str = line_str.strip()
        if line_str.startswith("data: "):
            event_data = json.loads(line_str[6:])
            assert event_data["id"] == id3
            assert event_data["event_type"] == "test_event_C"
            found = True
            break
    assert found


def test_ai_status_endpoint_creates_zero_gemini_calls(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("Gemini was called!")
    monkeypatch.setattr(career_advisor, "call_gemini_json", fail_if_called)

    hr_headers = get_auth_headers(user_id=3, role="hr")
    response = client.get("/analytics/ai-status", headers=hr_headers)
    assert response.status_code == 200
    assert response.json()["engine"] == "Gemini-2.5-Flash (Hybrid Mode)"


def test_hr_dashboard_overview_creates_zero_gemini_calls(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("Gemini was called!")
    monkeypatch.setattr(career_advisor, "call_gemini_json", fail_if_called)

    hr_headers = get_auth_headers(user_id=3, role="hr")
    response = client.get("/analytics/overview", headers=hr_headers)
    assert response.status_code == 200


def test_suggestions_retrieval_creates_zero_gemini_calls(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("Gemini was called!")
    monkeypatch.setattr(career_advisor, "call_gemini_json", fail_if_called)

    db = TestingSessionLocal()
    ensure_resume_exists(db)
    db.close()

    headers = get_auth_headers(user_id=1, role="candidate")
    response = client.get("/resumes/1/career-suggestions", headers=headers)
    assert response.status_code == 200


def test_verify_auth_endpoint():
    response = client.get("/auth/verify")
    assert response.status_code == 401

    headers = get_auth_headers(user_id=1, role="candidate")
    response = client.get("/auth/verify", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "valid"


def setup_test_resume(tmp_path, file_name="test.pdf", file_content=b"%PDF-1.4 test content"):
    db = TestingSessionLocal()
    temp_upload = tmp_path / "uploads"
    temp_upload.mkdir(exist_ok=True)
    os.environ["UPLOAD_DIR"] = str(temp_upload.resolve())
    
    test_file = temp_upload / file_name
    test_file.write_bytes(file_content)
    
    ensure_resume_exists(db)
    resume = db.query(Resume).filter(Resume.candidate_id == 1).first()
    resume.file_path = str(test_file.resolve())
    resume.file_name = file_name
    db.commit()
    db.close()
    return test_file


def test_anonymous_resume_download_returns_401():
    response = client.get("/resumes/1/download")
    assert response.status_code == 401


def test_invalid_token_download_returns_401():
    response = client.get("/resumes/1/download", headers={"Authorization": "Bearer invalidtoken123"})
    assert response.status_code == 401


def test_expired_token_download_returns_401():
    from jose import jwt
    from app.core.security import SECRET_KEY, ALGORITHM
    expire = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - datetime.timedelta(seconds=10)
    token = jwt.encode({"user_id": 1, "role": "candidate", "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
    response = client.get("/resumes/1/download", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_candidate_downloads_own_resume_successfully(tmp_path):
    setup_test_resume(tmp_path, "test.pdf", b"%PDF-1.4 test resume pdf content")
    headers = get_auth_headers(user_id=1, role="candidate")
    response = client.get("/resumes/1/download", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "inline" in response.headers["content-disposition"]
    assert "test.pdf" in response.headers["content-disposition"]
    assert response.content == b"%PDF-1.4 test resume pdf content"


def test_candidate_cannot_download_another_candidate_resume(tmp_path):
    setup_test_resume(tmp_path, "test.pdf")
    headers = get_auth_headers(user_id=2, role="candidate")
    response = client.get("/resumes/1/download", headers=headers)
    assert response.status_code == 403


def test_hr_can_download_candidate_resume(tmp_path):
    setup_test_resume(tmp_path, "test.pdf")
    headers = get_auth_headers(user_id=3, role="hr")
    response = client.get("/resumes/1/download", headers=headers)
    assert response.status_code == 200


def test_missing_resume_record_returns_404():
    headers = get_auth_headers(user_id=3, role="hr")
    response = client.get("/resumes/999/download", headers=headers)
    assert response.status_code == 404


def test_resume_record_exists_but_file_is_missing_on_disk():
    db = TestingSessionLocal()
    ensure_resume_exists(db)
    resume = db.query(Resume).filter(Resume.candidate_id == 1).first()
    resume.file_path = "uploads/nonexistent_file_path.pdf"
    db.commit()
    db.close()
    
    headers = get_auth_headers(user_id=3, role="hr")
    response = client.get("/resumes/1/download", headers=headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_pdf_media_type_and_inline_disposition(tmp_path):
    setup_test_resume(tmp_path, "my_resume.pdf")
    headers = get_auth_headers(user_id=3, role="hr")
    response = client.get("/resumes/1/download", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "inline" in response.headers["content-disposition"]


def test_docx_media_type_and_attachment_disposition(tmp_path):
    setup_test_resume(tmp_path, "my_resume.docx", b"PK\x03\x04 mock word content")
    headers = get_auth_headers(user_id=3, role="hr")
    response = client.get("/resumes/1/download", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert "attachment" in response.headers["content-disposition"]


def test_path_outside_upload_directory_is_rejected(tmp_path):
    # Enforce standard upload directory inside tmp_path
    temp_upload = tmp_path / "uploads"
    temp_upload.mkdir(exist_ok=True)
    os.environ["UPLOAD_DIR"] = str(temp_upload.resolve())

    outside_file = tmp_path / "outside_file.pdf"
    outside_file.write_bytes(b"%PDF-1.4 malicious outside path traversal")
    
    db = TestingSessionLocal()
    ensure_resume_exists(db)
    resume = db.query(Resume).filter(Resume.candidate_id == 1).first()
    resume.file_path = str(outside_file.resolve())
    resume.file_name = "outside_file.pdf"
    db.commit()
    db.close()
    
    headers = get_auth_headers(user_id=3, role="hr")
    response = client.get("/resumes/1/download", headers=headers)
    assert response.status_code == 403
    assert "invalid" in response.json()["detail"].lower()


def test_malicious_stored_filename_path_traversal_prevented(tmp_path):
    temp_upload = tmp_path / "uploads"
    temp_upload.mkdir(exist_ok=True)
    os.environ["UPLOAD_DIR"] = str(temp_upload.resolve())

    outside_file = tmp_path / "escape.pdf"
    outside_file.write_bytes(b"%PDF-1.4 malicious path traversal")
    
    db = TestingSessionLocal()
    ensure_resume_exists(db)
    resume = db.query(Resume).filter(Resume.candidate_id == 1).first()
    resume.file_path = str(temp_upload.resolve()) + "/../escape.pdf"
    resume.file_name = "escape.pdf"
    db.commit()
    db.close()
    
    headers = get_auth_headers(user_id=3, role="hr")
    response = client.get("/resumes/1/download", headers=headers)
    assert response.status_code == 403


def test_response_headers_does_not_expose_internal_filepath(tmp_path):
    test_file = setup_test_resume(tmp_path, "test.pdf")
    headers = get_auth_headers(user_id=3, role="hr")
    response = client.get("/resumes/1/download", headers=headers)
    assert response.status_code == 200
    
    for k, v in response.headers.items():
        assert str(test_file.resolve()) not in v
        assert "uploads" not in v.lower()


def test_download_endpoint_does_not_trigger_gemini(tmp_path, monkeypatch):
    setup_test_resume(tmp_path, "test.pdf")
    def fail_if_called(*args, **kwargs):
        raise AssertionError("Gemini was called!")
    monkeypatch.setattr(career_advisor, "call_gemini_json", fail_if_called)

    headers = get_auth_headers(user_id=3, role="hr")
    response = client.get("/resumes/1/download", headers=headers)
    assert response.status_code == 200


def test_download_endpoint_does_not_modify_resume_record(tmp_path):
    setup_test_resume(tmp_path, "test.pdf")
    db = TestingSessionLocal()
    resume_before = db.query(Resume).filter(Resume.candidate_id == 1).first()
    hash_before = resume_before.resume_hash
    status_before = resume_before.status
    db.close()

    headers = get_auth_headers(user_id=3, role="hr")
    client.get("/resumes/1/download", headers=headers)
    
    db = TestingSessionLocal()
    resume_after = db.query(Resume).filter(Resume.candidate_id == 1).first()
    assert resume_after.resume_hash == hash_before
    assert resume_after.status == status_before
    db.close()


def test_download_response_security_headers(tmp_path):
    setup_test_resume(tmp_path, "test.pdf")
    headers = get_auth_headers(user_id=3, role="hr")
    response = client.get("/resumes/1/download", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("cache-control") == "private, no-store"
    assert response.headers.get("x-content-type-options") == "nosniff"


def test_download_unsupported_type_raises_415(tmp_path):
    setup_test_resume(tmp_path, "my_resume.txt", b"some txt content")
    headers = get_auth_headers(user_id=3, role="hr")
    response = client.get("/resumes/1/download", headers=headers)
    assert response.status_code == 415




