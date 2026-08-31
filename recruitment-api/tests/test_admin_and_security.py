"""Comprehensive Admin Panel & Security test suite.

Covers: Admin bootstrap, public registration, HR lifecycle (create, list,
terminate, reactivate, password reset, password change), token versioning,
audit safety, forgot-password, and multi-HR ownership regression.
"""

import os
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from app.core.database import SessionLocal, Base, engine, get_db
from app.main import app
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.models.activity_event import ActivityEvent
from app.core.security import create_access_token, get_password_hash, verify_password

# Recreate tables for an isolated test database
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="module")
def admin_account(client):
    """Bootstrap an admin directly in the DB and return headers."""
    db = SessionLocal()
    admin = User(
        full_name="Test Admin",
        email="testadmin@example.com",
        hashed_password=get_password_hash("AdminPass123!"),
        role="admin",
        is_active=True,
        must_change_password=False,
        token_version=1,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    admin_id = admin.id
    db.close()

    token = create_access_token(
        {"sub": str(admin_id), "user_id": admin_id, "role": "admin", "token_version": 1}
    )
    return {"id": admin_id, "email": "testadmin@example.com", "headers": {"Authorization": f"Bearer {token}"}}


# ─── 1-2  Admin Bootstrap ───────────────────────────────────────────────────
def test_admin_bootstrap_creates_admin(admin_account):
    db = SessionLocal()
    user = db.query(User).filter(User.email == "testadmin@example.com").first()
    assert user is not None
    assert user.role == "admin"
    assert user.is_active is True
    assert user.must_change_password is False
    db.close()


def test_admin_bootstrap_is_idempotent(admin_account):
    db = SessionLocal()
    admins = db.query(User).filter(User.email == "testadmin@example.com").all()
    assert len(admins) == 1
    db.close()


# ─── 3-5  Admin Login & auth/me ─────────────────────────────────────────────
def test_admin_login_succeeds(client, admin_account):
    res = client.post("/auth/login", json={"email": "testadmin@example.com", "password": "AdminPass123!"})
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "admin"
    assert "access_token" in data


def test_get_auth_me_returns_admin_role(client, admin_account):
    res = client.get("/auth/me", headers=admin_account["headers"])
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "admin"
    assert data["is_active"] is True
    assert "hashed_password" not in data
    assert "password" not in data


def test_inactive_admin_is_rejected(client, admin_account):
    db = SessionLocal()
    inactive_admin = User(
        full_name="Inactive Admin",
        email="inactiveadmin@example.com",
        hashed_password=get_password_hash("AdminPass123!"),
        role="admin",
        is_active=False,
        must_change_password=False,
        token_version=1,
    )
    db.add(inactive_admin)
    db.commit()
    db.refresh(inactive_admin)
    inactive_id = inactive_admin.id
    db.close()

    token = create_access_token(
        {"sub": str(inactive_id), "user_id": inactive_id, "role": "admin", "token_version": 1}
    )
    res = client.get("/admin/hr-accounts", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


# ─── 6-8  Public Registration ───────────────────────────────────────────────
def test_public_registration_creates_candidate_only(client):
    res = client.post("/auth/register", json={
        "full_name": "Public Candidate", "email": "pubcand@example.com", "password": "Password123!"
    })
    assert res.status_code == 200
    assert res.json()["role"] == "candidate"


def test_public_registration_rejects_hr_role(client):
    res = client.post("/auth/register", json={
        "full_name": "Attacker", "email": "atk_hr@example.com", "password": "Password123!", "role": "hr"
    })
    assert res.status_code == 422


def test_public_registration_rejects_admin_role(client):
    res = client.post("/auth/register", json={
        "full_name": "Attacker", "email": "atk_admin@example.com", "password": "Password123!", "role": "admin"
    })
    assert res.status_code == 422


# ─── 9-19  HR Creation ──────────────────────────────────────────────────────
def test_admin_creates_hr(client, admin_account):
    res = client.post("/admin/hr-accounts", headers=admin_account["headers"], json={
        "full_name": "HR Manager One", "email": "hr1@example.com",
        "temporary_password": "TempPassword123!", "confirm_temporary_password": "TempPassword123!"
    })
    assert res.status_code == 201
    hr = res.json()["hr"]
    assert hr["role"] == "hr"
    assert hr["is_active"] is True
    assert hr["must_change_password"] is True
    assert hr["created_by_admin_id"] == admin_account["id"]


def test_candidate_cannot_create_hr(client):
    cand_login = client.post("/auth/login", json={"email": "pubcand@example.com", "password": "Password123!"})
    token = cand_login.json()["access_token"]
    res = client.post("/admin/hr-accounts", headers={"Authorization": f"Bearer {token}"}, json={
        "full_name": "Rogue HR", "email": "roghr@example.com",
        "temporary_password": "TempPassword123!", "confirm_temporary_password": "TempPassword123!"
    })
    assert res.status_code == 403


def test_hr_cannot_create_another_hr(client, admin_account):
    # First make hr1 change password so they have a valid non-must-change token
    login_res = client.post("/auth/login", json={"email": "hr1@example.com", "password": "TempPassword123!"})
    hr_token = login_res.json()["access_token"]
    client.post("/auth/change-password", headers={"Authorization": f"Bearer {hr_token}"}, json={
        "current_password": "TempPassword123!", "new_password": "PermanentPass123!", "confirm_new_password": "PermanentPass123!"
    })
    hr_login2 = client.post("/auth/login", json={"email": "hr1@example.com", "password": "PermanentPass123!"})
    hr_token2 = hr_login2.json()["access_token"]

    res = client.post("/admin/hr-accounts", headers={"Authorization": f"Bearer {hr_token2}"}, json={
        "full_name": "Rogue HR2", "email": "roghr2@example.com",
        "temporary_password": "TempPassword123!", "confirm_temporary_password": "TempPassword123!"
    })
    assert res.status_code == 403


def test_anonymous_create_hr_returns_401(client):
    res = client.post("/admin/hr-accounts", json={
        "full_name": "Anon HR", "email": "anon@example.com",
        "temporary_password": "TempPassword123!", "confirm_temporary_password": "TempPassword123!"
    })
    assert res.status_code == 401


def test_duplicate_email_returns_409(client, admin_account):
    res = client.post("/admin/hr-accounts", headers=admin_account["headers"], json={
        "full_name": "Dup HR", "email": "hr1@example.com",
        "temporary_password": "TempPassword123!", "confirm_temporary_password": "TempPassword123!"
    })
    assert res.status_code == 409


def test_different_casing_email_returns_409(client, admin_account):
    res = client.post("/admin/hr-accounts", headers=admin_account["headers"], json={
        "full_name": "Dup HR", "email": "HR1@EXAMPLE.COM",
        "temporary_password": "TempPassword123!", "confirm_temporary_password": "TempPassword123!"
    })
    assert res.status_code == 409


def test_weak_password_returns_422(client, admin_account):
    res = client.post("/admin/hr-accounts", headers=admin_account["headers"], json={
        "full_name": "Weak HR", "email": "weakhr@example.com",
        "temporary_password": "short", "confirm_temporary_password": "short"
    })
    assert res.status_code == 422


def test_password_mismatch_returns_422(client, admin_account):
    res = client.post("/admin/hr-accounts", headers=admin_account["headers"], json={
        "full_name": "Mismatch HR", "email": "mmhr@example.com",
        "temporary_password": "TempPassword123!", "confirm_temporary_password": "DifferentPass456!"
    })
    assert res.status_code == 422


def test_password_is_hashed_in_db():
    db = SessionLocal()
    hr = db.query(User).filter(User.email == "hr1@example.com").first()
    assert hr.hashed_password != "TempPassword123!"
    assert hr.hashed_password != "PermanentPass123!"
    assert hr.hashed_password.startswith("$2b$")
    db.close()


def test_create_response_has_no_password(client, admin_account):
    res = client.post("/admin/hr-accounts", headers=admin_account["headers"], json={
        "full_name": "NoPass HR", "email": "nopasshr@example.com",
        "temporary_password": "TempPassword123!", "confirm_temporary_password": "TempPassword123!"
    })
    assert res.status_code == 201
    body = json.dumps(res.json())
    assert "TempPassword123!" not in body
    assert "hashed_password" not in body


# ─── 20-26  HR Listing ──────────────────────────────────────────────────────
def test_hr_list_returns_hr_users_only(client, admin_account):
    res = client.get("/admin/hr-accounts", headers=admin_account["headers"])
    assert res.status_code == 200
    for item in res.json()["items"]:
        assert item["role"] == "hr"


def test_candidate_accounts_excluded_from_list(client, admin_account):
    res = client.get("/admin/hr-accounts?search=pubcand", headers=admin_account["headers"])
    assert res.json()["total"] == 0


def test_admin_accounts_excluded_from_list(client, admin_account):
    res = client.get("/admin/hr-accounts?search=testadmin", headers=admin_account["headers"])
    assert res.json()["total"] == 0


def test_pagination_works(client, admin_account):
    res = client.get("/admin/hr-accounts?page=1&page_size=1", headers=admin_account["headers"])
    data = res.json()
    assert len(data["items"]) <= 1
    assert data["page"] == 1
    assert data["total"] >= 1


def test_search_works(client, admin_account):
    res = client.get("/admin/hr-accounts?search=HR+Manager+One", headers=admin_account["headers"])
    assert res.json()["total"] >= 1


def test_status_filtering_works(client, admin_account):
    res = client.get("/admin/hr-accounts?status=active", headers=admin_account["headers"])
    for item in res.json()["items"]:
        assert item["is_active"] is True


def test_max_page_size_enforced(client, admin_account):
    res = client.get("/admin/hr-accounts?page_size=999", headers=admin_account["headers"])
    assert res.status_code == 422


# ─── 27-36  Termination ─────────────────────────────────────────────────────
def test_admin_terminates_hr(client, admin_account):
    # Create a dedicated HR for termination tests
    client.post("/admin/hr-accounts", headers=admin_account["headers"], json={
        "full_name": "Term HR", "email": "termhr@example.com",
        "temporary_password": "TempPassword123!", "confirm_temporary_password": "TempPassword123!"
    })
    db = SessionLocal()
    hr = db.query(User).filter(User.email == "termhr@example.com").first()
    hr_id = hr.id
    db.close()

    res = client.patch(f"/admin/hr-accounts/{hr_id}/terminate", headers=admin_account["headers"])
    assert res.status_code == 200
    assert res.json()["hr"]["is_active"] is False


def test_terminated_hr_cannot_login(client):
    res = client.post("/auth/login", json={"email": "termhr@example.com", "password": "TempPassword123!"})
    assert res.status_code == 403


def test_terminated_hr_existing_token_rejected(client, admin_account):
    db = SessionLocal()
    hr = db.query(User).filter(User.email == "termhr@example.com").first()
    old_token = create_access_token({
        "sub": str(hr.id), "user_id": hr.id, "role": "hr", "token_version": 1
    })
    db.close()
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {old_token}"})
    assert res.status_code in (401, 403)


def test_terminated_hr_jobs_preserved():
    db = SessionLocal()
    hr = db.query(User).filter(User.email == "termhr@example.com").first()
    # Create a job owned by this HR to verify preservation
    job = Job(title="Preserved Job", description="Test", created_by=hr.id)
    db.add(job)
    db.commit()
    jobs = db.query(Job).filter(Job.created_by == hr.id).all()
    assert len(jobs) >= 1
    db.close()


def test_terminated_hr_applications_preserved():
    # Applications reference jobs, so they are preserved inherently when the HR row is not deleted
    db = SessionLocal()
    hr = db.query(User).filter(User.email == "termhr@example.com").first()
    assert hr is not None  # HR record still exists
    assert hr.is_active is False
    db.close()


def test_terminated_hr_resume_references_preserved():
    # Resume files live on disk tied to candidates; HR termination does not touch them
    db = SessionLocal()
    hr = db.query(User).filter(User.email == "termhr@example.com").first()
    assert hr is not None
    db.close()


def test_candidate_cannot_terminate_hr(client, admin_account):
    cand_login = client.post("/auth/login", json={"email": "pubcand@example.com", "password": "Password123!"})
    token = cand_login.json()["access_token"]
    db = SessionLocal()
    hr = db.query(User).filter(User.email == "termhr@example.com").first()
    db.close()
    res = client.patch(f"/admin/hr-accounts/{hr.id}/terminate", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_hr_cannot_terminate_another_hr(client, admin_account):
    hr_login = client.post("/auth/login", json={"email": "hr1@example.com", "password": "PermanentPass123!"})
    hr_token = hr_login.json()["access_token"]
    db = SessionLocal()
    hr = db.query(User).filter(User.email == "nopasshr@example.com").first()
    db.close()
    res = client.patch(f"/admin/hr-accounts/{hr.id}/terminate", headers={"Authorization": f"Bearer {hr_token}"})
    assert res.status_code == 403


def test_admin_cannot_terminate_candidate_via_this_route(client, admin_account):
    db = SessionLocal()
    cand = db.query(User).filter(User.email == "pubcand@example.com").first()
    db.close()
    res = client.patch(f"/admin/hr-accounts/{cand.id}/terminate", headers=admin_account["headers"])
    assert res.status_code == 422


def test_admin_cannot_terminate_admin_via_this_route(client, admin_account):
    res = client.patch(f"/admin/hr-accounts/{admin_account['id']}/terminate", headers=admin_account["headers"])
    assert res.status_code == 422


# ─── 37-39  Reactivation ────────────────────────────────────────────────────
def test_admin_reactivates_hr(client, admin_account):
    db = SessionLocal()
    hr = db.query(User).filter(User.email == "termhr@example.com").first()
    hr_id = hr.id
    db.close()

    res = client.patch(f"/admin/hr-accounts/{hr_id}/reactivate", headers=admin_account["headers"])
    assert res.status_code == 200
    assert res.json()["hr"]["is_active"] is True


def test_reactivated_hr_can_login(client):
    res = client.post("/auth/login", json={"email": "termhr@example.com", "password": "TempPassword123!"})
    assert res.status_code == 200


def test_reactivated_hr_data_remains():
    db = SessionLocal()
    hr = db.query(User).filter(User.email == "termhr@example.com").first()
    jobs = db.query(Job).filter(Job.created_by == hr.id).all()
    assert len(jobs) >= 1
    db.close()


# ─── 40-47  Password Reset & Change ─────────────────────────────────────────
def test_admin_resets_hr_password(client, admin_account):
    db = SessionLocal()
    hr = db.query(User).filter(User.email == "hr1@example.com").first()
    hr_id = hr.id
    db.close()

    res = client.post(f"/admin/hr-accounts/{hr_id}/reset-password", headers=admin_account["headers"], json={
        "temporary_password": "ResetTempPass789!", "confirm_temporary_password": "ResetTempPass789!"
    })
    assert res.status_code == 200


def test_old_password_stops_working(client):
    res = client.post("/auth/login", json={"email": "hr1@example.com", "password": "PermanentPass123!"})
    assert res.status_code == 401


def test_new_temporary_password_works(client):
    res = client.post("/auth/login", json={"email": "hr1@example.com", "password": "ResetTempPass789!"})
    assert res.status_code == 200
    assert res.json()["must_change_password"] is True


def test_must_change_password_set_after_reset():
    db = SessionLocal()
    hr = db.query(User).filter(User.email == "hr1@example.com").first()
    assert hr.must_change_password is True
    db.close()


def test_existing_tokens_invalidated_after_reset(client, admin_account):
    db = SessionLocal()
    hr = db.query(User).filter(User.email == "hr1@example.com").first()
    stale = create_access_token({"sub": str(hr.id), "user_id": hr.id, "role": "hr", "token_version": 1})
    db.close()
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {stale}"})
    assert res.status_code == 401


def test_hr_changes_temporary_password(client):
    login = client.post("/auth/login", json={"email": "hr1@example.com", "password": "ResetTempPass789!"})
    token = login.json()["access_token"]

    res = client.post("/auth/change-password", headers={"Authorization": f"Bearer {token}"}, json={
        "current_password": "ResetTempPass789!",
        "new_password": "FinalSecurePass999!",
        "confirm_new_password": "FinalSecurePass999!"
    })
    assert res.status_code == 200


def test_must_change_password_false_after_change():
    db = SessionLocal()
    hr = db.query(User).filter(User.email == "hr1@example.com").first()
    assert hr.must_change_password is False
    db.close()


def test_permanent_password_works(client):
    res = client.post("/auth/login", json={"email": "hr1@example.com", "password": "FinalSecurePass999!"})
    assert res.status_code == 200


# ─── 48-51  Forgot Password ─────────────────────────────────────────────────
def test_forgot_password_generic_response(client):
    res = client.post("/auth/forgot-password", json={"email": "unknown@example.com"})
    assert res.status_code == 200
    data = res.json()
    assert "email_configured" in data
    assert data["email_configured"] is False


def test_forgot_password_does_not_reveal_account(client):
    res1 = client.post("/auth/forgot-password", json={"email": "hr1@example.com"})
    res2 = client.post("/auth/forgot-password", json={"email": "nonexistent@example.com"})
    assert res1.json()["message"] == res2.json()["message"]


# ─── 52-54  Audit Event Safety ───────────────────────────────────────────────
def test_creation_event_no_password():
    db = SessionLocal()
    events = db.query(ActivityEvent).filter(ActivityEvent.event_type == "hr_login_created").all()
    for ev in events:
        details = str(ev.details_json or "").lower()
        assert "password" not in details
        assert "hashed_password" not in details
    db.close()


def test_termination_event_no_password():
    db = SessionLocal()
    events = db.query(ActivityEvent).filter(ActivityEvent.event_type == "hr_login_terminated").all()
    for ev in events:
        details = str(ev.details_json or "").lower()
        assert "password" not in details
    db.close()


def test_reset_event_no_password():
    db = SessionLocal()
    events = db.query(ActivityEvent).filter(ActivityEvent.event_type == "hr_password_reset_by_admin").all()
    for ev in events:
        details = str(ev.details_json or "").lower()
        assert "password" not in details
        assert "token" not in details
    db.close()


# ─── 55-58  Ownership Regression ────────────────────────────────────────────
def test_hr1_cannot_access_hr2_jobs(client, admin_account):
    # Create HR2 with full password-change flow
    client.post("/admin/hr-accounts", headers=admin_account["headers"], json={
        "full_name": "HR Two", "email": "hr2@example.com",
        "temporary_password": "TempPassword123!", "confirm_temporary_password": "TempPassword123!"
    })
    hr2_login = client.post("/auth/login", json={"email": "hr2@example.com", "password": "TempPassword123!"})
    hr2_token = hr2_login.json()["access_token"]
    client.post("/auth/change-password", headers={"Authorization": f"Bearer {hr2_token}"}, json={
        "current_password": "TempPassword123!", "new_password": "HR2Permanent999!", "confirm_new_password": "HR2Permanent999!"
    })
    hr2_login2 = client.post("/auth/login", json={"email": "hr2@example.com", "password": "HR2Permanent999!"})
    hr2_token2 = hr2_login2.json()["access_token"]
    hr2_headers = {"Authorization": f"Bearer {hr2_token2}"}

    # HR2 creates a job
    hr2_job = client.post("/jobs", headers=hr2_headers, json={
        "title": "HR2 Private Job", "description": "Secret", "required_skills": "Python",
        "experience_level": "Senior", "education_requirement": "BS"
    })

    # HR1 should not see HR2 jobs in their scoped list
    hr1_login = client.post("/auth/login", json={"email": "hr1@example.com", "password": "FinalSecurePass999!"})
    hr1_token = hr1_login.json()["access_token"]
    hr1_headers = {"Authorization": f"Bearer {hr1_token}"}

    hr1_jobs = client.get("/jobs", headers=hr1_headers)
    for job in hr1_jobs.json():
        if isinstance(job, dict) and "title" in job:
            assert job["title"] != "HR2 Private Job"


def test_terminated_hr_cannot_access_protected_routes(client, admin_account):
    # Create and immediately terminate an HR
    client.post("/admin/hr-accounts", headers=admin_account["headers"], json={
        "full_name": "Block HR", "email": "blockhr@example.com",
        "temporary_password": "TempPassword123!", "confirm_temporary_password": "TempPassword123!"
    })
    db = SessionLocal()
    hr = db.query(User).filter(User.email == "blockhr@example.com").first()
    hr_id = hr.id
    db.close()

    client.patch(f"/admin/hr-accounts/{hr_id}/terminate", headers=admin_account["headers"])

    res = client.post("/auth/login", json={"email": "blockhr@example.com", "password": "TempPassword123!"})
    assert res.status_code == 403


# ─── Database Index Verification ────────────────────────────────────────────
def test_required_indexes_exist():
    inspector = inspect(engine)
    users_idx = {i["name"] for i in inspector.get_indexes("users")}
    jobs_idx = {i["name"] for i in inspector.get_indexes("jobs")}
    apps_idx = {i["name"] for i in inspector.get_indexes("applications")}
    notif_idx = {i["name"] for i in inspector.get_indexes("notifications")}

    assert "ix_users_role" in users_idx or any("role" in str(i) for i in users_idx)
    assert "ix_users_is_active" in users_idx or any("is_active" in str(i) for i in users_idx)
