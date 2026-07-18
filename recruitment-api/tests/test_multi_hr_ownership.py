import os
import pytest
from fastapi.testclient import TestClient

from unittest.mock import MagicMock
from app.core.rate_limit import rate_limiter
rate_limiter.dependency = MagicMock(return_value=lambda: None)

os.environ["SECRET_KEY"] = "test-only-secret-key-with-sufficient-length-for-hmac"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SEED_DEFAULT_JOBS"] = "false"
os.environ["ALLOW_PUBLIC_HR_REGISTRATION"] = "true"

import app.models
from app.core.database import SessionLocal, Base, engine
from app.main import app
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.application import Application
from app.models.resume import Resume
from app.models.user import User

# Recreate all tables cleanly
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

from app.core.database import get_db

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
def setup_data(client):
    db = SessionLocal()
    try:
        # Create HR1
        hr1_res = client.post("/auth/register", json={
            "full_name": "HR One", "email": "hr1@example.com", "password": "SecurePass123!", "role": "hr"
        })
        assert hr1_res.status_code == 200, f"HR1 registration failed: {hr1_res.status_code} - {hr1_res.text}"
        hr1_id = hr1_res.json()["user_id"]
        hr1_token_res = client.post("/auth/login", json={"email": "hr1@example.com", "password": "SecurePass123!"})
        assert hr1_token_res.status_code == 200, f"HR1 login failed: {hr1_token_res.text}"
        hr1_token = hr1_token_res.json()["access_token"]
        
        # Create HR2
        hr2_res = client.post("/auth/register", json={
            "full_name": "HR Two", "email": "hr2@example.com", "password": "SecurePass123!", "role": "hr"
        })
        assert hr2_res.status_code == 200, f"HR2 registration failed: {hr2_res.status_code} - {hr2_res.text}"
        hr2_id = hr2_res.json()["user_id"]
        hr2_token_res = client.post("/auth/login", json={"email": "hr2@example.com", "password": "SecurePass123!"})
        assert hr2_token_res.status_code == 200, f"HR2 login failed: {hr2_token_res.text}"
        hr2_token = hr2_token_res.json()["access_token"]
        
        # Create Candidate 1
        c1_res = client.post("/auth/register", json={
            "full_name": "Candidate One", "email": "cand1@example.com", "password": "SecurePass123!", "role": "candidate"
        })
        assert c1_res.status_code == 200, f"Candidate 1 registration failed: {c1_res.status_code} - {c1_res.text}"
        c1_id = c1_res.json()["user_id"]
        c1_token_res = client.post("/auth/login", json={"email": "cand1@example.com", "password": "SecurePass123!"})
        assert c1_token_res.status_code == 200, f"Candidate 1 login failed: {c1_token_res.text}"
        c1_token = c1_token_res.json()["access_token"]

        # Create Candidate 2
        c2_res = client.post("/auth/register", json={
            "full_name": "Candidate Two", "email": "cand2@example.com", "password": "SecurePass123!", "role": "candidate"
        })
        assert c2_res.status_code == 200, f"Candidate 2 registration failed: {c2_res.status_code} - {c2_res.text}"
        c2_id = c2_res.json()["user_id"]
        c2_token_res = client.post("/auth/login", json={"email": "cand2@example.com", "password": "SecurePass123!"})
        assert c2_token_res.status_code == 200, f"Candidate 2 login failed: {c2_token_res.text}"
        c2_token = c2_token_res.json()["access_token"]

        # Set up candidate skills so matching runs
        cand1 = db.query(Candidate).filter(Candidate.user_id == c1_id).first()
        cand1.skills = "Python, SQL, FastAPI"
        cand1.education = "BS Computer Science"
        cand1.experience = "FastAPI backend dev for 2 years"
        
        cand2 = db.query(Candidate).filter(Candidate.user_id == c2_id).first()
        cand2.skills = "React, CSS, JavaScript"
        cand2.education = "BS Software Engineering"
        cand2.experience = "Frontend developer for 3 years"
        
        # Seed resume files
        os.makedirs("uploads", exist_ok=True)
        r1_path = "uploads/resume_c1.pdf"
        with open(r1_path, "wb") as f:
            f.write(b"%PDF-1.4 mock resume file content")
            
        r2_path = "uploads/resume_c2.pdf"
        with open(r2_path, "wb") as f:
            f.write(b"%PDF-1.4 mock resume file content 2")
            
        resume1 = Resume(candidate_id=cand1.id, file_name="resume_c1.pdf", file_path=r1_path, status="completed")
        resume2 = Resume(candidate_id=cand2.id, file_name="resume_c2.pdf", file_path=r2_path, status="completed")
        db.add_all([resume1, resume2])
        db.commit()

        # Create jobs owned by HR1
        job1 = Job(title="Backend Dev", description="FastAPI role", required_skills="Python, FastAPI", status="Active", created_by=hr1_id)
        job1_inactive = Job(title="Legacy Dev", description="Old role", required_skills="Cobol", status="Inactive", created_by=hr1_id)
        
        # Create jobs owned by HR2
        job2 = Job(title="Frontend Dev", description="React role", required_skills="React, JavaScript", status="Active", created_by=hr2_id)
        
        db.add_all([job1, job1_inactive, job2])
        db.commit()

        return {
            "hr1_id": hr1_id,
            "hr1_token": hr1_token,
            "hr1_headers": {"Authorization": f"Bearer {hr1_token}"},
            "hr2_id": hr2_id,
            "hr2_token": hr2_token,
            "hr2_headers": {"Authorization": f"Bearer {hr2_token}"},
            "c1_id": c1_id,
            "c1_token": c1_token,
            "c1_headers": {"Authorization": f"Bearer {c1_token}"},
            "c2_id": c2_id,
            "c2_token": c2_token,
            "c2_headers": {"Authorization": f"Bearer {c2_token}"},
            "job1_id": job1.id,
            "job1_inactive_id": job1_inactive.id,
            "job2_id": job2.id,
            "resume1_id": resume1.id,
            "resume2_id": resume2.id
        }
    finally:
        db.close()


def test_candidate_applications_job_id_validation(client, setup_data):
    # Try applying with missing job_id
    res = client.post("/applications", headers=setup_data["c1_headers"], json={})
    assert res.status_code == 422

    # Try applying to non-existent job
    res = client.post("/applications", headers=setup_data["c1_headers"], json={"job_id": 99999})
    assert res.status_code == 404


def test_candidate_apply_inactive_job(client, setup_data):
    # Attempting to apply to inactive job should yield 400
    res = client.post("/applications", headers=setup_data["c1_headers"], json={"job_id": setup_data["job1_inactive_id"]})
    assert res.status_code == 400
    assert "no longer accepting applications" in res.json()["detail"]


def test_candidate_successful_application(client, setup_data):
    res = client.post("/applications", headers=setup_data["c1_headers"], json={"job_id": setup_data["job1_id"]})
    assert res.status_code == 200
    payload = res.json()
    assert payload["message"] == "Application submitted successfully."
    assert payload["status"] == "Manual Review"
    assert "application_id" in payload
    assert payload["job_id"] == setup_data["job1_id"]
    assert "created_at" in payload


def test_candidate_duplicate_application_yields_409(client, setup_data):
    # Repeat apply to same job should raise 409
    res = client.post("/applications", headers=setup_data["c1_headers"], json={"job_id": setup_data["job1_id"]})
    assert res.status_code == 409
    assert "already applied" in res.json()["detail"]


def test_hr_scoping_rules_list_routes(client, setup_data):
    # Candidate 2 applies to Job 2 (HR2)
    res = client.post("/applications", headers=setup_data["c2_headers"], json={"job_id": setup_data["job2_id"]})
    assert res.status_code == 200
    app2_id = res.json()["application_id"]

    # HR1 checks their own application list
    res_hr1 = client.get("/applications/hr/me", headers=setup_data["hr1_headers"])
    assert res_hr1.status_code == 200
    hr1_apps = res_hr1.json()
    # HR1 should only see applications for Job 1, not Job 2
    assert len(hr1_apps) == 1
    assert hr1_apps[0]["job_id"] == setup_data["job1_id"]
    assert hr1_apps[0]["email"] == "cand1@example.com"

    # HR2 checks their own application list
    res_hr2 = client.get("/applications/hr/me", headers=setup_data["hr2_headers"])
    assert res_hr2.status_code == 200
    hr2_apps = res_hr2.json()
    # HR2 should only see Candidate 2's application
    assert len(hr2_apps) == 1
    assert hr2_apps[0]["application_id"] == app2_id
    assert hr2_apps[0]["job_id"] == setup_data["job2_id"]
    assert hr2_apps[0]["email"] == "cand2@example.com"


def test_hr_scoping_rules_detail_route(client, setup_data):
    # HR1 retrieves Candidate 1's application detail (Job 1 is owned by HR1 -> 200)
    res_hr1_me = client.get("/applications/hr/me", headers=setup_data["hr1_headers"])
    app1_id = res_hr1_me.json()[0]["application_id"]
    
    res = client.get(f"/applications/{app1_id}", headers=setup_data["hr1_headers"])
    assert res.status_code == 200
    assert res.json()["email"] == "cand1@example.com"

    # HR2 attempts to retrieve Candidate 1's application detail -> 403 Forbidden
    res_hr2_steal = client.get(f"/applications/{app1_id}", headers=setup_data["hr2_headers"])
    assert res_hr2_steal.status_code == 403
    assert "do not have access" in res_hr2_steal.json()["detail"]


def test_hr_scoping_resume_download_routes(client, setup_data):
    res_hr1_me = client.get("/applications/hr/me", headers=setup_data["hr1_headers"])
    app1_id = res_hr1_me.json()[0]["application_id"]

    res_hr2_me = client.get("/applications/hr/me", headers=setup_data["hr2_headers"])
    app2_id = res_hr2_me.json()[0]["application_id"]

    # HR1 downloads Candidate 1 resume -> 200
    dl1 = client.get(f"/applications/{app1_id}/resume", headers=setup_data["hr1_headers"])
    assert dl1.status_code == 200
    assert dl1.headers["content-type"] == "application/pdf"

    # HR2 downloads Candidate 1 resume -> 403
    dl2 = client.get(f"/applications/{app1_id}/resume", headers=setup_data["hr2_headers"])
    assert dl2.status_code == 403

    # Mismatched role or anonymous attempts
    dl_anon = client.get(f"/applications/{app1_id}/resume")
    assert dl_anon.status_code == 401


def test_candidate_own_resume_download_routes(client, setup_data):
    # Candidate 1 downloads their own resume -> 200
    dl = client.get("/resumes/me/download", headers=setup_data["c1_headers"])
    assert dl.status_code == 200

    # HR tries to call Candidate's own route -> 403
    dl_hr = client.get("/resumes/me/download", headers=setup_data["hr1_headers"])
    assert dl_hr.status_code == 403


def test_status_update_ownership_validation(client, setup_data):
    res_hr1_me = client.get("/applications/hr/me", headers=setup_data["hr1_headers"])
    app1_id = res_hr1_me.json()[0]["application_id"]

    # HR1 updates candidate 1 status -> 200
    res = client.put(f"/matching/{app1_id}/status", headers=setup_data["hr1_headers"], json={"status": "Shortlisted"})
    assert res.status_code == 200
    assert res.json()["status"] == "Shortlisted"

    # HR2 tries to update candidate 1 status -> 403
    res_steal = client.put(f"/matching/{app1_id}/status", headers=setup_data["hr2_headers"], json={"status": "Interview"})
    assert res_steal.status_code == 403


def test_chatbot_grounding_scoping(client, setup_data):
    # HR1 asks chatbot about top candidates
    res1 = client.post("/ai/recruiter", headers=setup_data["hr1_headers"], json={
        "message": "Who are my top candidates?"
    })
    assert res1.status_code == 200
    # HR1 should see Candidate One but NOT Candidate Two
    assert "Candidate One" in res1.json()["answer"]
    assert "Candidate Two" not in res1.json()["answer"]

    # HR2 asks chatbot about top candidates
    res2 = client.post("/ai/recruiter", headers=setup_data["hr2_headers"], json={
        "message": "Who are my top candidates?"
    })
    assert res2.status_code == 200
    # HR2 should see Candidate Two but NOT Candidate One
    assert "Candidate Two" in res2.json()["answer"]
    assert "Candidate One" not in res2.json()["answer"]
