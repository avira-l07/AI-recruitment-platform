import os
import json
import pytest
from fastapi.testclient import TestClient

from app.core.rate_limit import rate_limiter


import app.models
from app.core.database import SessionLocal, Base, engine, get_db
from app.main import app
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.application import Application
from app.models.match_score import MatchScore
from app.models.resume import Resume
from app.models.user import User
from app.models.activity_event import ActivityEvent
from app.core.security import get_password_hash
from app.services.blind_screening import (
    get_neutral_candidate_identifier,
    sanitize_education,
    sanitize_experience,
    redact_text_pii,
)

# Recreate all tables cleanly


def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)
    engine.dispose()


@pytest.fixture(scope="module")
def setup_blind_data(client):
    db = SessionLocal()
    try:
        # Create HR user
        hr_user = User(
            full_name="HR Evaluator",
            email="hr_evaluator@example.com",
            hashed_password=get_password_hash("SecurePass123!"),
            role="hr",
            is_active=True,
            must_change_password=False
        )
        db.add(hr_user)
        db.commit()
        db.refresh(hr_user)
        hr_id = hr_user.id

        # Create Candidate User & Candidate with unique token for leakage testing
        cand_user = User(
            full_name="Alex TEST_PERSON_UNIQUE_98421 Morgan",
            email="alex.TEST_PERSON_UNIQUE_98421@example.com",
            hashed_password=get_password_hash("SecurePass123!"),
            role="candidate",
            is_active=True,
            must_change_password=False
        )
        db.add(cand_user)
        db.commit()
        db.refresh(cand_user)
        cand_user_id = cand_user.id

        candidate = Candidate(
            user_id=cand_user.id,
            full_name="Alex TEST_PERSON_UNIQUE_98421 Morgan",
            email="alex.TEST_PERSON_UNIQUE_98421@example.com",
            phone="+1-555-TEST-98421",
            education="B.S. in Computer Science, Stanford University, 2022",
            experience="Senior Python Developer at Google LLC (2022-2025)",
            skills="Python, FastAPI, Docker, PostgreSQL, React",
            projects="Built real-time analytics streaming engine for high load",
            certifications="AWS Certified Solutions Architect"
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        cand_id = candidate.id

        # Create Job created by HR
        job = Job(
            title="Senior Backend Engineer",
            description="Looking for Python and FastAPI expert",
            required_skills="Python, FastAPI, Docker",
            experience_level="Senior",
            education_requirement="Bachelor",
            created_by=hr_user.id,
            status="Active"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = job.id

        # Create Application
        application = Application(
            candidate_id=candidate.id,
            job_id=job.id,
            status="Applied"
        )
        db.add(application)
        db.commit()
        db.refresh(application)
        app_id = application.id

        # Create Match Score
        match = MatchScore(
            application_id=application.id,
            candidate_id=candidate.id,
            job_id=job.id,
            score=92.5,
            matched_skills=json.dumps(["Python", "FastAPI", "Docker"]),
            missing_skills=json.dumps([]),
            explanation="Strong backend experience in Python and FastAPI",
            fit_label="Strong Fit",
            confidence_score=95.0,
            confidence_label="High",
            ai_source="hybrid"
        )
        db.add(match)

        # Create Resume
        parsed_data = {
            "name": "Alex TEST_PERSON_UNIQUE_98421 Morgan",
            "email": "alex.TEST_PERSON_UNIQUE_98421@example.com",
            "phone": "+1-555-TEST-98421",
            "education": "B.S. in Computer Science, Stanford University, 2022",
            "experience": "Senior Python Developer at Google LLC (2022-2025)",
            "skills": ["Python", "FastAPI", "Docker"],
            "projects": ["Built real-time analytics engine"],
            "certifications": ["AWS Certified Solutions Architect"],
            "summary": "Experienced engineer Alex TEST_PERSON_UNIQUE_98421 Morgan with strong background."
        }
        
        # Make a dummy physical file in uploads directory for resume download test
        upload_dir = os.environ["UPLOAD_DIR"]
        os.makedirs(upload_dir, exist_ok=True)
        dummy_file_path = os.path.join(upload_dir, "test_resume.pdf")
        with open(dummy_file_path, "wb") as f:
            f.write(b"%PDF-1.4 dummy pdf resume content for testing")

        resume = Resume(
            candidate_id=candidate.id,
            file_name="Alex_Morgan_Resume_98421.pdf",
            file_path=dummy_file_path,
            parsed_data=json.dumps(parsed_data),
            status="completed"
        )
        db.add(resume)
        db.commit()

        # Login HR
        hr_login = client.post("/auth/login", json={"email": "hr_evaluator@example.com", "password": "SecurePass123!"})
        assert hr_login.status_code == 200
        hr_token = hr_login.json()["access_token"]
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        return {
            "hr_id": hr_id,
            "hr_headers": hr_headers,
            "cand_user_id": cand_user_id,
            "cand_id": cand_id,
            "cand_name": "Alex TEST_PERSON_UNIQUE_98421 Morgan",
            "cand_email": "alex.TEST_PERSON_UNIQUE_98421@example.com",
            "job_id": job_id,
            "app_id": app_id,
        }
    finally:
        db.close()


def test_blind_screening_unit_helpers():
    # 1. Neutral identifier
    assert get_neutral_candidate_identifier(1042) == "Candidate #C-1042"
    assert get_neutral_candidate_identifier(1) == "Candidate #C-1"

    # 2. Education sanitization (keeps degree/major, strips university and graduation year)
    edu_raw = "B.S. in Computer Science, Stanford University, 2022"
    edu_clean = sanitize_education(edu_raw)
    assert "Stanford" not in edu_clean
    assert "2022" not in edu_clean
    assert "Computer Science" in edu_clean

    # 3. Experience sanitization
    exp_raw = "Senior Software Engineer at Google LLC (2020-2023)"
    exp_clean = sanitize_experience(exp_raw)
    assert "Google" not in exp_clean
    assert "Software Engineer" in exp_clean

    # 4. Redact PII in freeform text
    text = "Candidate Alex TEST_PERSON_UNIQUE_98421 Morgan is reachable at alex@example.com or 555-123-4567."
    redacted = redact_text_pii(
        text,
        candidate_name="Alex TEST_PERSON_UNIQUE_98421 Morgan",
        email="alex@example.com",
        phone="555-123-4567",
        candidate_id=99
    )
    assert "Alex" not in redacted
    assert "TEST_PERSON_UNIQUE_98421" not in redacted
    assert "alex@example.com" not in redacted
    assert "555-123-4567" not in redacted
    assert "Candidate #C-99" in redacted


def test_applications_normal_vs_blind_mode(client, setup_blind_data):
    headers = setup_blind_data["hr_headers"]
    cand_id = setup_blind_data["cand_id"]

    # 1. Normal mode request
    res_normal = client.get("/applications/hr/me", headers=headers)
    assert res_normal.status_code == 200
    normal_data = res_normal.json()
    assert len(normal_data) > 0
    first_normal = normal_data[0]
    assert "Alex TEST_PERSON_UNIQUE_98421 Morgan" in str(first_normal["name"])
    assert first_normal["email"] is not None
    assert "alex.TEST_PERSON_UNIQUE_98421@example.com" in str(first_normal["email"])

    # 2. Blind mode via query param
    res_blind_query = client.get("/applications/hr/me?blind_mode=true", headers=headers)
    assert res_blind_query.status_code == 200
    blind_data = res_blind_query.json()
    first_blind = blind_data[0]
    assert first_blind["name"] == f"Candidate #C-{cand_id}"
    assert first_blind["email"] is None
    assert "TEST_PERSON_UNIQUE_98421" not in res_blind_query.text

    # 3. Blind mode via HTTP header
    blind_headers = {**headers, "X-Blind-Screening": "true"}
    res_blind_header = client.get("/applications/hr/me", headers=blind_headers)
    assert res_blind_header.status_code == 200
    header_blind_data = res_blind_header.json()
    assert header_blind_data[0]["name"] == f"Candidate #C-{cand_id}"
    assert header_blind_data[0]["email"] is None
    assert "TEST_PERSON_UNIQUE_98421" not in res_blind_header.text


def test_network_boundary_pii_leakage_across_all_endpoints(client, setup_blind_data):
    cand_id = setup_blind_data["cand_id"]
    cand_user_id = setup_blind_data["cand_user_id"]
    app_id = setup_blind_data["app_id"]
    blind_headers = {**setup_blind_data["hr_headers"], "X-Blind-Screening": "true"}
    unique_marker = "TEST_PERSON_UNIQUE_98421"

    # Test /applications/hr/me
    r1 = client.get("/applications/hr/me", headers=blind_headers)
    assert r1.status_code == 200
    assert unique_marker not in r1.text

    # Test /applications/{id}
    r2 = client.get(f"/applications/{app_id}", headers=blind_headers)
    assert r2.status_code == 200
    assert unique_marker not in r2.text

    # Test /matching/all
    r3 = client.get("/matching/all", headers=blind_headers)
    assert r3.status_code == 200
    assert unique_marker not in r3.text

    # Test /matching/candidate/{cand_user_id}
    r4 = client.get(f"/matching/candidate/{cand_user_id}", headers=blind_headers)
    assert r4.status_code == 200
    assert unique_marker not in r4.text

    # Test /candidates
    r5 = client.get("/candidates", headers=blind_headers)
    assert r5.status_code == 200
    assert unique_marker not in r5.text

    # Test /candidates/{id}
    r6 = client.get(f"/candidates/{cand_id}", headers=blind_headers)
    assert r6.status_code == 200
    assert unique_marker not in r6.text

    # Test /resumes/{cand_user_id}
    r7 = client.get(f"/resumes/{cand_user_id}", headers=blind_headers)
    assert r7.status_code == 200
    assert unique_marker not in r7.text

    # Test /resumes/{cand_user_id}/intelligence
    r8 = client.get(f"/resumes/{cand_user_id}/intelligence", headers=blind_headers)
    assert r8.status_code == 200
    assert unique_marker not in r8.text


def test_score_identity_guarantee(client, setup_blind_data):
    headers = setup_blind_data["hr_headers"]
    blind_headers = {**headers, "X-Blind-Screening": "true"}

    res_normal = client.get("/matching/all", headers=headers).json()
    res_blind = client.get("/matching/all", headers=blind_headers).json()

    assert len(res_normal) == len(res_blind)
    for n, b in zip(res_normal, res_blind):
        # Match score, confidence must be exactly equal
        assert n["score"] == b["score"]
        assert n["match_score"] == b["match_score"]
        assert n["confidenceScore"] == b["confidenceScore"]
        assert n["confidenceLabel"] == b["confidenceLabel"]
        # AI source must be identical
        assert n["aiSource"] == b["aiSource"]
        # Blind identifier substituted
        assert b["name"].startswith("Candidate #C-")


def test_raw_resume_403_blocking_in_blind_mode(client, setup_blind_data):
    app_id = setup_blind_data["app_id"]
    headers = setup_blind_data["hr_headers"]

    # 1. Calling download with blind_mode=true -> 403 Forbidden
    res_blind_query = client.get(f"/applications/{app_id}/resume?blind_mode=true", headers=headers)
    assert res_blind_query.status_code == 403
    assert "Blind Screening" in res_blind_query.json()["detail"] or "restricted" in res_blind_query.json()["detail"]

    # 2. Calling download with X-Blind-Screening: true header -> 403 Forbidden
    blind_headers = {**headers, "X-Blind-Screening": "true"}
    res_blind_header = client.get(f"/applications/{app_id}/resume", headers=blind_headers)
    assert res_blind_header.status_code == 403

    # 3. Calling download in normal mode -> 200 OK with file content
    res_normal = client.get(f"/applications/{app_id}/resume", headers=headers)
    assert res_normal.status_code == 200
    assert b"%PDF" in res_normal.content


def test_ai_recruiter_blind_mode(client, setup_blind_data):
    headers = setup_blind_data["hr_headers"]
    blind_headers = {**headers, "X-Blind-Screening": "true"}
    cand_id = setup_blind_data["cand_id"]

    # Ask recruiter in blind mode
    res = client.post(
        "/ai/recruiter",
        headers=blind_headers,
        json={"message": "Who is the top candidate for the role?"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "is_blind_mode" in data and data["is_blind_mode"] is True
    assert "TEST_PERSON_UNIQUE_98421" not in str(data["answer"])
    assert f"Candidate #C-{cand_id}" in str(data["answer"])
    if data.get("actions"):
        for action in data["actions"]:
            assert "TEST_PERSON_UNIQUE_98421" not in action.get("label", "")


def test_search_pii_safety(client, setup_blind_data):
    headers = setup_blind_data["hr_headers"]
    blind_headers = {**headers, "X-Blind-Screening": "true"}
    cand_id = setup_blind_data["cand_id"]

    # 1. Searching by real name in normal mode -> finds candidate
    r_norm = client.get("/search?q=TEST_PERSON_UNIQUE_98421", headers=headers)
    assert r_norm.status_code == 200
    assert len(r_norm.json()["candidates"]) > 0

    # 2. Searching by real name in blind mode -> 0 candidate results (names are not indexed/searched)
    r_blind_name = client.get("/search?q=TEST_PERSON_UNIQUE_98421", headers=blind_headers)
    assert r_blind_name.status_code == 200
    assert len(r_blind_name.json()["candidates"]) == 0

    # 3. Searching by skill in blind mode -> finds candidate with neutral ID and masked email
    r_blind_skill = client.get("/search?q=FastAPI", headers=blind_headers)
    assert r_blind_skill.status_code == 200
    cand_results = r_blind_skill.json()["candidates"]
    assert len(cand_results) > 0
    first_c = cand_results[0]
    assert first_c["name"] == f"Candidate #C-{cand_id}"
    assert first_c["email"] is None
    assert "TEST_PERSON_UNIQUE_98421" not in r_blind_skill.text


def test_database_data_integrity_guarantee(client, setup_blind_data):
    db = SessionLocal()
    try:
        cand_id = setup_blind_data["cand_id"]
        cand_in_db = db.query(Candidate).filter(Candidate.id == cand_id).first()
        
        # Verify original database values are fully preserved
        assert cand_in_db.full_name == "Alex TEST_PERSON_UNIQUE_98421 Morgan"
        assert cand_in_db.email == "alex.TEST_PERSON_UNIQUE_98421@example.com"
        assert cand_in_db.phone == "+1-555-TEST-98421"
        assert "Stanford" in cand_in_db.education
        assert "Google" in cand_in_db.experience
    finally:
        db.close()


def test_audit_logging_blind_mode(client, setup_blind_data):
    headers = setup_blind_data["hr_headers"]

    # Toggle enabled
    r_enable = client.post("/activity/blind-screening-toggle", headers=headers, json={"enabled": True})
    assert r_enable.status_code == 200
    assert r_enable.json()["enabled"] is True

    # Toggle disabled
    r_disable = client.post("/activity/blind-screening-toggle", headers=headers, json={"enabled": False})
    assert r_disable.status_code == 200
    assert r_disable.json()["enabled"] is False

    # Check database event log
    db = SessionLocal()
    try:
        events = db.query(ActivityEvent).filter(
            ActivityEvent.event_type.in_(["blind_screening_enabled", "blind_screening_disabled"])
        ).order_by(ActivityEvent.id.desc()).all()
        assert len(events) >= 2
        event_types = [e.event_type for e in events]
        assert "blind_screening_enabled" in event_types
        assert "blind_screening_disabled" in event_types
    finally:
        db.close()
