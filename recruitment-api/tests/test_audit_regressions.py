"""Regression coverage for access, privacy, input, and evidence audit findings."""
import json
import socket
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.main import app
from app.core.database import SessionLocal
from app.core.rate_limit import InMemoryRateLimiter
from app.core.security import create_access_token
from app.models.user import User
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.application import Application
from app.models.resume import Resume
from app.models.notification import Notification
from app.models.activity_event import ActivityEvent
from app.models.verification import ExperienceVerification
from app.models.prescreening import JobPrescreeningQuestion, ApplicationPrescreeningEvaluation
from app.services.ssrf_validator import is_safe_url
from app.services.company_verifier import verify_company_claim
from app.services.certification_verifier import verify_certification
from app.services.prescreening.response_evaluator import evaluate_prescreening_responses


@pytest.fixture
def data():
    suffix = uuid4().hex
    with SessionLocal() as db:
        users = [User(full_name=name, email=f'{role}-{i}-{suffix}@example.com', role=role, hashed_password='unused')
                 for i, (name, role) in enumerate([('Owner Recruiter', 'hr'), ('Other Recruiter', 'hr'), ('Private Person', 'candidate')])]
        db.add_all(users)
        db.flush()
        owner, other, person = users
        cand = Candidate(user_id=person.id, full_name=person.full_name, email=person.email, skills='Python, SQL')
        job = Job(title='Audit Job', created_by=owner.id, status='Active', required_skills='Python, SQL')
        db.add_all([cand, job])
        db.flush()
        application = Application(candidate_id=cand.id, job_id=job.id)
        question = JobPrescreeningQuestion(job_id=job.id, question_text='Explain Python validation', scoring_criteria='Private rubric', expected_concepts='["validation"]')
        v = ExperienceVerification(candidate_id=cand.id, claims_json=json.dumps({'_verification_engine_version': 2, 'nested': [person.full_name, person.email, 'https://github.com/private-person']}), history_json=json.dumps([{'notes': person.full_name}]))
        db.add_all([application, question, v])
        db.flush()
        db.add(ApplicationPrescreeningEvaluation(application_id=application.id, candidate_id=cand.id, job_id=job.id,
               evaluations_json=json.dumps([{'candidate_answer': person.full_name + ' ' + person.email}]), strengths_summary=person.full_name, gap_summary=person.email))
        db.add(Resume(candidate_id=cand.id, status='completed', combined_analysis_json=json.dumps({'suggestions': [{'name': person.full_name}], 'aiInsights': {'nested': [person.email]}})))
        db.add_all([ActivityEvent(event_type='owned', candidate_id=cand.id, job_id=job.id, details_json=json.dumps({'candidate_name': person.full_name})),
                    ActivityEvent(event_type='unrelated', user_id=other.id, details_json='{}')])
        db.add(Notification(user_id=owner.id, title='New application', message=person.full_name + ' applied.', type='info', related_entity_type='application', related_entity_id=application.id))
        db.commit()
        def headers(user, **extra):
            token = create_access_token({'sub': str(user.id), 'user_id': user.id, 'token_version': user.token_version})
            return {'Authorization': f'Bearer {token}', **extra}
        yield {'owner': headers(owner), 'other': headers(other), 'candidate': headers(person), 'candidate_id': cand.id,
               'user_id': person.id, 'job_id': job.id, 'app_id': application.id, 'verif_id': v.id,
               'question_id': question.id, 'email': person.email, 'owner_id': owner.id}


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


@pytest.mark.parametrize('route', ['candidates', 'resumes', 'career', 'verification', 'evaluation', 'questions'])
def test_other_recruiter_cannot_read_private_resources(client, data, route):
    urls = {'candidates': f"/candidates/{data['candidate_id']}", 'resumes': f"/resumes/{data['user_id']}",
            'career': f"/resumes/{data['user_id']}/career-suggestions", 'verification': f"/verification/candidate/{data['candidate_id']}",
            'evaluation': f"/prescreening/application/{data['app_id']}", 'questions': f"/prescreening/job/{data['job_id']}/questions"}
    assert client.get(urls[route], headers=data['other']).status_code == 403


@pytest.mark.parametrize('action', ['generate', 'update', 'verify', 'decision', 'reverify'])
def test_other_recruiter_cannot_mutate_private_resources(client, data, action):
    if action == 'update':
        response = client.put(f"/prescreening/job/{data['job_id']}/questions", headers=data['other'], json={'questions': []})
    else:
        urls = {'generate': f"/prescreening/job/{data['job_id']}/generate", 'verify': f"/verification/candidate/{data['candidate_id']}/verify",
                'decision': f"/verification/{data['verif_id']}/decision", 'reverify': f"/verification/{data['verif_id']}/reverify"}
        response = client.post(urls[action], headers=data['other'], json={'decision': 'verified'} if action == 'decision' else None)
    assert response.status_code == 403


def test_candidate_and_event_lists_are_scoped(client, data):
    assert data['candidate_id'] in [row['id'] for row in client.get('/candidates', headers=data['owner']).json()]
    assert data['candidate_id'] not in [row['id'] for row in client.get('/candidates', headers=data['other']).json()]
    events = client.get('/analytics/events', headers=data['owner']).json()
    assert any(e['event_type'] == 'owned' for e in events)
    assert all(e['event_type'] != 'unrelated' for e in events)


@pytest.mark.parametrize('route', ['verification', 'evaluation', 'career', 'events', 'decision', 'notifications'])
def test_blind_mode_redacts_nested_private_details(client, data, route):
    headers = {**data['owner'], 'X-Blind-Screening': 'true'}
    urls = {'verification': f"/verification/candidate/{data['candidate_id']}", 'evaluation': f"/prescreening/application/{data['app_id']}",
            'career': f"/resumes/{data['user_id']}/career-suggestions", 'events': '/analytics/events', 'notifications': '/notifications'}
    response = (client.post(f"/verification/{data['verif_id']}/decision", headers=headers, json={'decision': 'needs_review', 'notes': 'Private Person'})
                if route == 'decision' else client.get(urls[route], headers=headers))
    assert response.status_code == 200
    assert 'Private Person' not in response.text
    assert data['email'] not in response.text
    assert 'github.com/private-person' not in response.text


def test_decision_audit_is_committed(client, data):
    response = client.post(f"/verification/{data['verif_id']}/decision", headers=data['owner'], json={'decision': 'needs_review'})
    assert response.status_code == 200
    with SessionLocal() as db:
        assert db.query(ActivityEvent).filter(ActivityEvent.event_type == 'verification_decision_updated', ActivityEvent.candidate_id == data['candidate_id']).count() == 1


def test_question_rubric_is_private_and_updates_preserve_history(client, data):
    url = f"/prescreening/job/{data['job_id']}/questions"
    candidate_questions = client.get(url, headers=data['candidate']).json()
    assert 'expected_concepts' not in candidate_questions[0]
    assert 'scoring_criteria' not in candidate_questions[0]
    assert client.put(url, headers=data['owner'], json={'questions': [{'question_text': 'Explain SQL indexing', 'weight': -1}]}).status_code == 422
    assert client.put(url, headers=data['owner'], json={'questions': [{'question_text': 'Explain SQL indexing'}]}).status_code == 200
    with SessionLocal() as db:
        assert db.get(JobPrescreeningQuestion, data['question_id']).is_active is False


@pytest.mark.parametrize('answers', [None, [], [{'question_id': 9999999, 'answer_text': 'Fake question'}], [{'question_id': 1, 'answer_text': 42}]])
def test_applications_reject_missing_or_forged_answers(client, data, answers):
    # Use a fresh job so duplicate-application checks do not mask validation.
    with SessionLocal() as db:
        job = Job(title='Required assessment', created_by=data['owner_id'], status='Active')
        db.add(job); db.flush()
        db.add(JobPrescreeningQuestion(job_id=job.id, question_text='Explain data validation'))
        db.commit(); job_id = job.id
    response = client.post('/applications', headers=data['candidate'], json={'job_id': job_id, 'prescreening_answers': answers})
    assert response.status_code == 422
    with SessionLocal() as db:
        assert db.query(Application).filter(Application.job_id == job_id).count() == 0


def test_tokens_without_session_version_are_rejected(client, data):
    token = create_access_token({'user_id': data['user_id']})
    assert client.get('/auth/me', headers={'Authorization': f'Bearer {token}'}).status_code == 401


def test_rate_limit_remains_active_with_test_client(monkeypatch):
    limiter = InMemoryRateLimiter()
    limited = FastAPI()
    @limited.get('/', dependencies=[Depends(limiter.dependency(2, 60, 'audit'))])
    def endpoint():
        return {'ok': True}
    with TestClient(limited) as client:
        assert client.get('/').status_code == 200
        assert client.get('/').status_code == 200
        response = client.get('/')
        assert response.status_code == 429
        assert int(response.headers['retry-after']) > 0


@pytest.mark.parametrize('url', ['https://example.com:bad/path', 'http://[::ffff:127.0.0.1]/', 'http://[2001:db8::1]/', 'https://user:pass@example.com/', 'https://localhost./', 'file:///secret'])
def test_invalid_or_internal_urls_fail_closed(url):
    assert is_safe_url(url)[0] is False


def test_dns_failure_and_mixed_addresses_fail_closed(monkeypatch):
    def fail(*args, **kwargs):
        raise socket.gaierror('DNS failed')
    monkeypatch.setattr(socket, 'getaddrinfo', fail)
    assert is_safe_url('https://unresolved.example')[0] is False
    monkeypatch.setattr(socket, 'getaddrinfo', lambda *a, **kw: [(2, 1, 6, '', ('8.8.8.8', 443)), (2, 1, 6, '', ('10.1.1.1', 443))])
    assert is_safe_url('https://mixed.example')[0] is False


def test_unverified_credentials_and_partial_company_names_are_not_verified():
    assert verify_company_claim('')['verification_status'] == 'Needs Review'
    assert verify_company_claim('Go')['verification_status'] == 'Needs Review'
    cert = verify_certification({'name': 'AWS Certificate', 'credential_id': 'made-up', 'verification_url': 'http://127.0.0.1/'})
    assert cert['status'] == 'Needs Review'
    assert cert['verification_url'] is None


def test_ai_cannot_replace_local_assessment_score(monkeypatch):
    monkeypatch.setattr('app.services.prescreening.response_evaluator.call_gemini_json', lambda *args: {'overall_score': 100, 'overall_label': 'Strong', 'summary': 'AI opinion'})
    result = evaluate_prescreening_responses('Engineer', [{'id': 1, 'question_text': 'Explain SQL', 'expected_concepts': ['SQL']}], [{'question_id': 1, 'answer_text': 'no'}])
    assert result['overall_score'] < 60
    assert result['overall_label'] != 'Strong'


def test_same_candidate_does_not_expose_other_recruiters_job_events(client, data):
    with SessionLocal() as db:
        other = db.query(User).filter(User.role == 'hr', User.id != data['owner_id']).order_by(User.id.desc()).first()
        job = Job(title='Other recruiter job', created_by=other.id)
        db.add(job); db.flush()
        db.add(ActivityEvent(event_type='private_other_job', candidate_id=data['candidate_id'], job_id=job.id, user_id=other.id, details_json='{}'))
        db.commit()
    assert 'private_other_job' not in client.get('/analytics/events', headers=data['owner']).text


def test_stream_session_rechecks_revocation(data):
    from starlette.requests import Request
    from app.services.activity_visibility import stream_session_valid
    request = Request({'type': 'http', 'headers': [(b'authorization', data['owner']['Authorization'].encode())]})
    with SessionLocal() as original_db, SessionLocal() as update_db:
        user = original_db.get(User, data['owner_id'])
        assert stream_session_valid(update_db, user, request)
        current = update_db.get(User, user.id)
        current.token_version += 1
        update_db.commit()
        assert not stream_session_valid(update_db, user, request)


def test_changed_resume_refreshes_evidence_and_archives_old_decision(client, data):
    client.post(f"/verification/{data['verif_id']}/decision", headers=data['owner'], json={'decision': 'verified', 'notes': 'Old evidence'})
    with SessionLocal() as db:
        resume = db.query(Resume).filter(Resume.candidate_id == data['candidate_id']).first()
        resume.resume_hash = 'changed-content'
        db.commit()
    response = client.get(f"/verification/candidate/{data['candidate_id']}", headers=data['owner'])
    assert response.status_code == 200
    assert response.json()['verification_version'] == 2
    assert response.json()['hr_decision'] is None
    assert response.json()['history'][-1]['hr_decision'] == 'verified'


def test_corrupt_resume_is_rejected_and_file_is_cleaned(client, data, monkeypatch):
    from app.api import resumes
    before = set(resumes.UPLOAD_DIR.glob('*'))
    def corrupt(*args):
        raise ValueError('Corrupt PDF')
    monkeypatch.setattr(resumes, '_extract_text', corrupt)
    response = client.post('/resumes/upload', headers=data['candidate'], data={'user_id': data['user_id']}, files={'file': ('bad.pdf', b'%PDF' + b'x' * 300, 'application/pdf')})
    assert response.status_code == 422
    assert set(resumes.UPLOAD_DIR.glob('*')) == before
