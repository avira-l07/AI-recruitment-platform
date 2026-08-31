import os
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.core.rate_limit import rate_limiter
rate_limiter.dependency = MagicMock(return_value=lambda: None)

os.environ["SECRET_KEY"] = "test-only-secret-key-with-sufficient-length-for-hmac"
os.environ["DATABASE_URL"] = "sqlite:///./test_verif.db"
os.environ["SEED_DEFAULT_JOBS"] = "false"
os.environ["ALLOW_PUBLIC_HR_REGISTRATION"] = "true"

import app.models
from app.core.database import SessionLocal, Base, engine, get_db
from app.main import app
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.application import Application
from app.models.resume import Resume
from app.models.user import User
from app.models.verification import ExperienceVerification
from app.models.activity_event import ActivityEvent
from app.core.security import get_password_hash
from app.services.ssrf_validator import is_safe_url
from app.services.claim_extractor import extract_all_candidate_claims, parse_experience_claims, parse_project_claims
from app.services.company_verifier import verify_company_claim, verify_internship_authenticity
from app.services.project_verifier import verify_project_claim
from app.services.timeline_engine import build_timeline_intelligence
from app.services.trust_score_engine import calculate_trust_score
from app.services.resume_authenticity_analyzer import analyze_resume_authenticity

# Recreate clean tables
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
    engine.dispose()


@pytest.fixture(scope="module")
def setup_verif_data(client):
    db = SessionLocal()
    try:
        # Create HR User
        hr = User(
            full_name="HR Trust Auditor",
            email="hr_trust_auditor@example.com",
            hashed_password=get_password_hash("SecurePass123!"),
            role="hr",
            is_active=True,
            must_change_password=False
        )
        db.add(hr)
        db.commit()
        db.refresh(hr)
        hr_id = hr.id

        # Create Candidate User
        cand_user = User(
            full_name="Jordan VERIF_PERSON_99482 Lee",
            email="jordan.VERIF_PERSON_99482@example.com",
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
            full_name="Jordan VERIF_PERSON_99482 Lee",
            email="jordan.VERIF_PERSON_99482@example.com",
            phone="+1-555-TRUST-99",
            education="B.S. in Computer Science, Stanford University (2021-2025)",
            experience="Software Engineering Intern at Google LLC (June 2024 - August 2024)\nBuilt microservices with Python and FastAPI.\n\nBackend Developer at ABC Technologies (January 2024 - May 2024)\nDeveloped RESTful endpoints with PostgreSQL.",
            skills="Python, FastAPI, React, Docker, PostgreSQL, AWS",
            projects="Waste Management AI Platform: Built smart routing with React & FastAPI https://github.com/jordanlee/waste-ai https://waste-ai-demo.vercel.app\nCloud Monitor: Real-time telemetry dashboard in Go https://github.com/jordanlee/cloud-monitor",
            certifications="AWS Certified Solutions Architect ID: AWS-99482-ARCH https://credly.com/org/aws/jordan\nCoursera Deep Learning Specialization"
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        cand_id = candidate.id

        resume = Resume(
            candidate_id=candidate.id,
            file_name="Jordan_Lee_Resume.pdf",
            file_path="uploads/jordan_resume.pdf",
            extracted_text=f"{candidate.education}\n{candidate.experience}\n{candidate.skills}\n{candidate.projects}\n{candidate.certifications}",
            parsed_data=json.dumps({
                "name": candidate.full_name,
                "email": candidate.email,
                "phone": candidate.phone,
                "education": candidate.education,
                "experience": candidate.experience,
                "skills": ["Python", "FastAPI", "React", "Docker"],
                "projects": candidate.projects,
                "certifications": candidate.certifications
            }),
            status="completed"
        )
        db.add(resume)
        db.commit()

        # Login HR
        login_res = client.post("/auth/login", json={"email": "hr_trust_auditor@example.com", "password": "SecurePass123!"})
        assert login_res.status_code == 200
        hr_token = login_res.json()["access_token"]
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        return {
            "hr_id": hr_id,
            "hr_headers": hr_headers,
            "cand_id": cand_id,
            "cand_user_id": cand_user_id
        }
    finally:
        db.close()


def test_ssrf_validator_blocks_internal_ips():
    # Block internal and private IPs
    assert is_safe_url("http://127.0.0.1:8000/secret")[0] is False
    assert is_safe_url("http://localhost:5000/admin")[0] is False
    assert is_safe_url("http://169.254.169.254/latest/meta-data/")[0] is False
    assert is_safe_url("http://10.0.0.5/api")[0] is False
    assert is_safe_url("http://192.168.1.1/router")[0] is False
    assert is_safe_url("file:///etc/passwd")[0] is False

    # Safe public domains
    assert is_safe_url("https://github.com/facebook/react")[0] is True
    assert is_safe_url("https://credly.com/badges/sample")[0] is True


def test_claim_extraction():
    exp_text = "Software Engineering Intern at Google (June 2024 - August 2024)\nDeveloped Python services."
    claims = parse_experience_claims(exp_text)
    assert len(claims) == 1
    assert claims[0]["is_internship"] is True
    assert "Google" in claims[0]["company_name"]
    assert "June 2024" in claims[0]["claimed_dates"]

    proj_text = "AI Router: Smart routing engine in Python https://github.com/test/router https://router-demo.vercel.app"
    projs = parse_project_claims(proj_text)
    assert len(projs) == 1
    assert "AI Router" in projs[0]["project_name"]
    assert projs[0]["repository_url"] == "https://github.com/test/router"
    assert projs[0]["demo_url"] == "https://router-demo.vercel.app"


def test_company_and_source_tiering():
    # Tier 1 Official Org
    comp_res = verify_company_claim("Google", claimed_tech=["Python", "Go"])
    assert comp_res["verification_status"] == "Verified"
    assert comp_res["confidence_score"] >= 90.0
    assert "Tier 1" in comp_res["evidence_sources"][0]["tier"]

    # Internship consistency
    intern_res = verify_internship_authenticity(
        {"role_title": "Software Engineering Intern", "claimed_dates": "June 2024 - Aug 2024", "is_internship": True},
        comp_res
    )
    assert intern_res["status"] in ["Verified", "Consistent"]
    assert intern_res["duration_realistic"] is True


def test_private_internship_safe_outcome():
    # Private startup without public website: MUST return Needs Review, NEVER Fraud!
    comp_res = verify_company_claim("Acme Stealth AI Inc", claimed_urls=[])
    assert comp_res["verification_status"] == "Needs Review"
    assert comp_res["confidence_score"] >= 50.0

    intern_res = verify_internship_authenticity(
        {"role_title": "Founding Intern", "claimed_dates": "May 2024 - July 2024", "is_internship": True},
        comp_res
    )
    assert intern_res["status"] == "Needs HR Review"
    assert "HR" in intern_res["notes"]


def test_fraud_detection_signals():
    # Suspicious certificate maker / generator
    comp_res = verify_company_claim("FakeCert Generator Ltd", claimed_urls=["https://free-certificate-generator.xyz/bogus"])
    assert comp_res["verification_status"] == "High Risk"
    assert len(comp_res["fraud_signals"]) > 0

    # Zero-width text detection in resume analyzer
    hidden_text = "Normal Text\u200b\u200b\u200b\u200b\u200b\u200bPython Expert"
    auth_res = analyze_resume_authenticity(hidden_text)
    assert auth_res["hidden_text_detected"] is True
    assert auth_res["status"] == "Flagged for Review"


def test_project_and_repository_validation():
    proj = {
        "project_name": "Smart Waste Platform",
        "description": "High performance waste management in FastAPI and React",
        "technologies": ["FastAPI", "React"],
        "repository_url": "https://github.com/sample/waste-platform",
        "demo_url": "https://waste-demo.vercel.app",
        "urls": ["https://github.com/sample/waste-platform", "https://waste-demo.vercel.app"]
    }
    res = verify_project_claim(proj)
    assert res["repository_status"] == "Verified Repository"
    assert res["demo_status"] == "Live Demo Accessible"
    assert res["technology_match"] == "High Match"
    assert len(res["evidence_sources"]) == 2


def test_timeline_intelligence():
    exps = [
        {"role_title": "Intern", "company_name": "Google", "claimed_dates": "2024 - 2024", "is_internship": True, "raw_text": "2024 - 2024"},
        {"role_title": "Developer", "company_name": "ABC Tech", "claimed_dates": "2024 - 2024", "is_internship": False, "raw_text": "2024 - 2024"}
    ]
    tl = build_timeline_intelligence(exps, [], [], education_text="B.S. in CS 2021 - 2025")
    assert tl["total_events"] >= 3
    assert len(tl["overlaps"]) >= 1  # Detects concurrent experiences in 2024


def test_verification_api_endpoints_and_blind_mode(client, setup_verif_data):
    cand_id = setup_verif_data["cand_id"]
    headers = setup_verif_data["hr_headers"]

    # 1. Normal mode GET /verification/candidate/{id}
    res_normal = client.get(f"/verification/candidate/{cand_id}", headers=headers)
    assert res_normal.status_code == 200
    data_normal = res_normal.json()
    assert data_normal["trust_score"] >= 70.0
    assert data_normal["verification_outcome"] in ["strong_evidence", "needs_review"]
    assert "Jordan VERIF_PERSON_99482 Lee" in data_normal["candidate_name"]
    assert len(data_normal["evidence_sources"]) >= 2
    assert len(data_normal["trust_score_breakdown"]) >= 4

    # 2. Blind Mode GET /verification/candidate/{id}?blind_mode=true
    res_blind = client.get(f"/verification/candidate/{cand_id}?blind_mode=true", headers=headers)
    assert res_blind.status_code == 200
    data_blind = res_blind.json()
    assert data_blind["candidate_name"] == f"Candidate #C-{cand_id}"
    assert data_blind["candidate_email"] is None
    assert data_blind["candidate_phone"] is None
    assert "VERIF_PERSON_99482" not in res_blind.text

    # 3. Blind Mode via HTTP header
    blind_headers = {**headers, "X-Blind-Screening": "true"}
    res_header_blind = client.get(f"/verification/candidate/{cand_id}", headers=blind_headers)
    assert res_header_blind.status_code == 200
    assert "VERIF_PERSON_99482" not in res_header_blind.text


def test_hr_decision_workflow_and_audit(client, setup_verif_data):
    cand_id = setup_verif_data["cand_id"]
    headers = setup_verif_data["hr_headers"]

    # Fetch existing verification
    res = client.get(f"/verification/candidate/{cand_id}", headers=headers)
    assert res.status_code == 200
    verif_id = res.json()["id"]

    # 1. Record HR Decision: verified
    dec_res = client.post(
        f"/verification/{verif_id}/decision",
        headers=headers,
        json={"decision": "verified", "notes": "Checked GitHub and verified strong commits."}
    )
    assert dec_res.status_code == 200
    assert dec_res.json()["hr_decision"] == "verified"
    assert "Checked GitHub" in dec_res.json()["hr_decision_notes"]

    # 2. Re-verify experience (version increment)
    reverif_res = client.post(f"/verification/{verif_id}/reverify", headers=headers)
    assert reverif_res.status_code == 200
    reverif_data = reverif_res.json()
    assert reverif_data["verification_version"] >= 2
    assert len(reverif_data["history"]) >= 1

    # 3. Check activity events in database
    db = SessionLocal()
    try:
        events = db.query(ActivityEvent).filter(
            ActivityEvent.event_type.in_(["verification_started", "verification_completed", "verification_decision_updated", "verification_reverified"])
        ).all()
        assert len(events) >= 2
    finally:
        db.close()
