"""Security and critical recruitment workflow regression tests."""

import os
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

TEST_DB = Path(tempfile.gettempdir()) / f"recruitai_{uuid4().hex}.db"
os.environ["SECRET_KEY"] = "test-only-secret-key-with-sufficient-length"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ.pop("GEMINI_API_KEY", None)
os.environ["SEED_DEFAULT_JOBS"] = "true"
os.environ["ALLOW_PUBLIC_HR_REGISTRATION"] = "true"

from app.core.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models.candidate import Candidate  # noqa: E402
from app.models.job import Job  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client
    from app.core.database import engine
    engine.dispose()
    TEST_DB.unlink(missing_ok=True)


@pytest.fixture(scope="session")
def accounts(client):
    suffix = uuid4().hex[:10]
    candidate_email = f"candidate-{suffix}@example.com"
    hr_email = f"hr-{suffix}@example.com"
    password = "SecurePass123!"

    candidate_register = client.post(
        "/auth/register",
        json={
            "full_name": "Workflow Candidate",
            "email": candidate_email,
            "password": password,
            "role": "candidate",
        },
    )
    assert candidate_register.status_code == 200, candidate_register.text

    hr_register = client.post(
        "/auth/register",
        json={
            "full_name": "Workflow Recruiter",
            "email": hr_email,
            "password": password,
            "role": "hr",
        },
    )
    assert hr_register.status_code == 200, hr_register.text

    candidate_login = client.post("/auth/login", json={"email": candidate_email, "password": password})
    hr_login = client.post("/auth/login", json={"email": hr_email, "password": password})
    assert candidate_login.status_code == 200, candidate_login.text
    assert hr_login.status_code == 200, hr_login.text

    return {
        "candidate_user_id": candidate_register.json()["user_id"],
        "candidate_headers": {"Authorization": f"Bearer {candidate_login.json()['access_token']}"},
        "hr_headers": {"Authorization": f"Bearer {hr_login.json()['access_token']}"},
    }


def test_sensitive_routes_require_authentication(client):
    assert client.get("/analytics/overview").status_code == 401
    assert client.get("/matching/all").status_code == 401
    assert client.get("/ai/status").status_code == 401


def test_role_authorization(client, accounts):
    candidate_headers = accounts["candidate_headers"]
    assert client.get("/analytics/overview", headers=candidate_headers).status_code == 403
    assert client.get("/matching/all", headers=candidate_headers).status_code == 403

    response = client.post(
        "/jobs",
        headers=candidate_headers,
        json={
            "title": "Unauthorized Job",
            "description": "This request must be rejected.",
            "required_skills": "Python, FastAPI",
            "experience_level": "Entry",
            "education_requirement": "Bachelor degree",
        },
    )
    assert response.status_code == 403


def test_candidate_application_and_hr_pipeline(client, accounts):
    with SessionLocal() as db:
        candidate = db.query(Candidate).filter(Candidate.user_id == accounts["candidate_user_id"]).first()
        assert candidate is not None
        candidate.skills = "Python, FastAPI, SQL, Git"
        candidate.education = "B.Tech Computer Science"
        candidate.experience = "One year of backend project experience"
        db.commit()
        job = db.query(Job).filter(Job.status == "Active").first()
        assert job is not None
        job_id = job.id

    apply_response = client.post(
        "/matching/apply",
        headers=accounts["candidate_headers"],
        json={"job_id": job_id},
    )
    assert apply_response.status_code == 200, apply_response.text
    payload = apply_response.json()
    assert payload["application_id"] > 0
    assert payload["score"] >= 0
    assert payload["confidence_label"] in {"Low", "Medium", "High"}
    assert payload["ai_source"] in {"local_ai", "local_fallback", "hybrid", "gemini"}

    duplicate = client.post(
        "/matching/apply",
        headers=accounts["candidate_headers"],
        json={"job_id": job_id},
    )
    assert duplicate.status_code == 409

    candidate_matches = client.get("/matching/me", headers=accounts["candidate_headers"])
    assert candidate_matches.status_code == 200
    assert len(candidate_matches.json()) == 1
    assert candidate_matches.json()[0]["application_id"] == payload["application_id"]

    hr_matches = client.get("/matching/all", headers=accounts["hr_headers"])
    assert hr_matches.status_code == 200
    assert any(item["application_id"] == payload["application_id"] for item in hr_matches.json())

    pipeline = client.get("/analytics/pipeline", headers=accounts["hr_headers"])
    assert pipeline.status_code == 200
    assert pipeline.json()["applied"] == 1
    assert pipeline.json()["ai_review"] == 1
    assert pipeline.json()["manual_review"] == 1

    status_update = client.put(
        f"/matching/{payload['application_id']}/status",
        headers=accounts["hr_headers"],
        json={"status": "Interview"},
    )
    assert status_update.status_code == 200, status_update.text
    assert status_update.json()["status"] == "Interview"

    updated_pipeline = client.get("/analytics/pipeline", headers=accounts["hr_headers"])
    assert updated_pipeline.json()["interview"] == 1


def test_ai_status_notifications_and_read_all(client, accounts):
    ai_status = client.get("/ai/status", headers=accounts["hr_headers"])
    assert ai_status.status_code == 200
    data = ai_status.json()
    assert data["local_ai"]["available"] is True
    assert data["gemini"]["status"] in {
        "not_configured",
        "configured_not_tested",
        "available",
        "rate_limited",
        "authentication_failed",
        "temporarily_unavailable",
        "request_failed",
        "timeout",
        "invalid_response",
    }

    notifications = client.get("/notifications", headers=accounts["hr_headers"])
    assert notifications.status_code == 200
    assert notifications.json()["total"] >= 1

    mark_all = client.put("/notifications/read-all", headers=accounts["hr_headers"])
    assert mark_all.status_code == 200, mark_all.text
    assert mark_all.json()["updated"] >= 1

    after = client.get("/notifications", headers=accounts["hr_headers"])
    assert after.json()["unread_count"] == 0
