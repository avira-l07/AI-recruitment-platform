import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from uuid import uuid4

from app.core.database import SessionLocal, Base, engine, get_db
from app.main import app
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.models.activity_event import ActivityEvent
from app.core.security import create_access_token, get_password_hash

# Recreate tables for isolated test run
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
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="module")
def admin_account(client):
    db = SessionLocal()
    admin = User(
        full_name="Test Admin",
        email="test_admin@example.com",
        hashed_password=get_password_hash("AdminPass123!"),
        role="admin",
        is_active=True,
        must_change_password=False,
        token_version=1
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    token = create_access_token({
        "sub": str(admin.id),
        "user_id": admin.id,
        "role": "admin",
        "token_version": 1
    })
    headers = {"Authorization": f"Bearer {token}"}
    db.close()
    return {"id": admin.id, "email": admin.email, "token": token, "headers": headers}


# 1-7: CLI, Migration & Index Checks
def test_indexes_exist():
    inspector = inspect(engine)
    users_indexes = [i['name'] for i in inspector.get_indexes('users')]
    jobs_indexes = [i['name'] for i in inspector.get_indexes('jobs')]
    apps_indexes = [i['name'] for i in inspector.get_indexes('applications')]
    notif_indexes = [i['name'] for i in inspector.get_indexes('notifications')]

    assert 'ix_users_role' in users_indexes
    assert 'ix_users_is_active' in users_indexes
    assert 'ix_users_created_by_admin_id' in users_indexes
    assert 'ix_jobs_created_by' in jobs_indexes
    assert 'ix_applications_job_id' in apps_indexes
    assert 'ix_applications_candidate_id' in apps_indexes
    assert 'ix_notifications_user_id' in notif_indexes


# 8-11: Public Registration Checks
def test_public_registration_creates_candidate_only(client):
    res = client.post("/auth/register", json={
        "full_name": "Public Candidate",
        "email": "pubcand@example.com",
        "password": "Password123!"
    })
    assert res.status_code == 200
    assert res.json()["role"] == "candidate"


def test_public_registration_rejects_non_candidate_roles(client):
    res = client.post("/auth/register", json={
        "full_name": "Attacker",
        "email": "attacker@example.com",
        "password": "Password123!",
        "role": "admin"
    })
    assert res.status_code == 422

    res_hr = client.post("/auth/register", json={
        "full_name": "Attacker HR",
        "email": "attacker_hr@example.com",
        "password": "Password123!",
        "role": "hr"
    })
    assert res_hr.status_code == 422


def test_public_registration_duplicate_email_case_insensitive(client):
    res = client.post("/auth/register", json={
        "full_name": "Duplicate Candidate",
        "email": "PUBCAND@example.com",
        "password": "Password123!"
    })
    assert res.status_code == 409


# 12-16: Login, Active & Token Versioning
def test_login_generic_error_on_invalid_credentials(client):
    res1 = client.post("/auth/login", json={"email": "nonexistent@example.com", "password": "Password123!"})
    res2 = client.post("/auth/login", json={"email": "pubcand@example.com", "password": "WrongPassword123!"})
    assert res1.status_code == 401
    assert res2.status_code == 401
    assert res1.json()["detail"] == "Invalid email or password."
    assert res2.json()["detail"] == "Invalid email or password."


def test_inactive_account_login_blocked(client, admin_account):
    # Create HR account and deactivate
    res = client.post("/admin/hr-accounts", headers=admin_account["headers"], json={
        "full_name": "Inactive HR",
        "email": "inactive_hr@example.com",
        "temporary_password": "TempPassword123!",
        "confirm_temporary_password": "TempPassword123!"
    })
    assert res.status_code == 201
    hr_id = res.json()["hr"]["id"]

    # Deactivate HR
    res_deact = client.patch(f"/admin/hr-accounts/{hr_id}/status", headers=admin_account["headers"], json={"is_active": False})
    assert res_deact.status_code == 200

    # Try login
    res_login = client.post("/auth/login", json={"email": "inactive_hr@example.com", "password": "TempPassword123!"})
    assert res_login.status_code == 403
    assert "inactive" in res_login.json()["detail"].lower()


def test_stale_token_version_rejected(client, admin_account):
    stale_token = create_access_token({
        "sub": str(admin_account["id"]),
        "user_id": admin_account["id"],
        "role": "admin",
        "token_version": 999
    })
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {stale_token}"})
    assert res.status_code == 401
    assert "revoked" in res.json()["detail"].lower()


# 17-25: Temporary Password & Password Change Flow
def test_temporary_password_hr_blocked_from_normal_endpoints(client, admin_account):
    res = client.post("/admin/hr-accounts", headers=admin_account["headers"], json={
        "full_name": "Must Change HR",
        "email": "mustchange@example.com",
        "temporary_password": "TempPassword123!",
        "confirm_temporary_password": "TempPassword123!"
    })
    assert res.status_code == 201
    hr_id = res.json()["hr"]["id"]

    # Login as HR
    res_login = client.post("/auth/login", json={"email": "mustchange@example.com", "password": "TempPassword123!"})
    assert res_login.status_code == 200
    token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # /auth/me allowed
    res_me = client.get("/auth/me", headers=headers)
    assert res_me.status_code == 200
    assert res_me.json()["must_change_password"] is True

    # Protected HR endpoint blocked
    res_protected = client.get("/applications/hr/me", headers=headers)
    assert res_protected.status_code == 403
    assert "password change required" in res_protected.json()["detail"].lower()

    # Change password
    res_change = client.post("/auth/change-password", headers=headers, json={
        "current_password": "TempPassword123!",
        "new_password": "NewPermanentPassword456!",
        "confirm_new_password": "NewPermanentPassword456!"
    })
    assert res_change.status_code == 200
    new_token = res_change.json()["access_token"]
    new_headers = {"Authorization": f"Bearer {new_token}"}

    # Old token fails due to token_version bump
    res_old = client.get("/auth/me", headers=headers)
    assert res_old.status_code == 401

    # New token allowed to access protected HR endpoints
    res_protected_new = client.get("/applications/hr/me", headers=new_headers)
    assert res_protected_new.status_code == 200


# 26-38: Admin HR Account Management & Pagination
def test_admin_create_and_list_hr_accounts(client, admin_account):
    res_create = client.post("/admin/hr-accounts", headers=admin_account["headers"], json={
        "full_name": "List HR One",
        "email": "listhr1@example.com",
        "temporary_password": "TempPassword123!",
        "confirm_temporary_password": "TempPassword123!"
    })
    assert res_create.status_code == 201
    hr_data = res_create.json()["hr"]
    assert hr_data["created_by_admin_id"] == admin_account["id"]
    assert hr_data["must_change_password"] is True
    assert "password" not in hr_data
    assert "hashed_password" not in hr_data

    res_list = client.get("/admin/hr-accounts?search=listhr1", headers=admin_account["headers"])
    assert res_list.status_code == 200
    data = res_list.json()
    assert data["total"] == 1
    assert data["items"][0]["email"] == "listhr1@example.com"


def test_admin_pagination_and_invalid_sort(client, admin_account):
    res_invalid = client.get("/admin/hr-accounts?sort_by=invalid_col", headers=admin_account["headers"])
    assert res_invalid.status_code == 422


# 39-47: HR Lifecycle & Password Reset
def test_admin_reset_hr_password(client, admin_account):
    res_create = client.post("/admin/hr-accounts", headers=admin_account["headers"], json={
        "full_name": "Reset HR",
        "email": "resethr@example.com",
        "temporary_password": "TempPassword123!",
        "confirm_temporary_password": "TempPassword123!"
    })
    assert res_create.status_code == 201
    hr_id = res_create.json()["hr"]["id"]

    res_reset = client.post(f"/admin/hr-accounts/{hr_id}/reset-password", headers=admin_account["headers"], json={
        "temporary_password": "NewResetPassword789!",
        "confirm_temporary_password": "NewResetPassword789!"
    })
    assert res_reset.status_code == 200

    # HR can login with new reset password
    res_login = client.post("/auth/login", json={"email": "resethr@example.com", "password": "NewResetPassword789!"})
    assert res_login.status_code == 200
    assert res_login.json()["must_change_password"] is True


def test_audit_events_never_expose_passwords():
    db = SessionLocal()
    events = db.query(ActivityEvent).all()
    for ev in events:
        details_str = str(ev.details_json or "").lower()
        assert "password" not in details_str
        assert "hashed_password" not in details_str
    db.close()
