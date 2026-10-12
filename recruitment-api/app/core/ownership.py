"""Shared recruiter scope checks for candidate and job resources."""

from fastapi import HTTPException
from app.models.application import Application
from app.models.job import Job


def hr_candidate_query(db, hr_id):
    return db.query(Application.candidate_id).join(
        Job, Application.job_id == Job.id
    ).filter(Job.created_by == hr_id)


def require_candidate_access(db, user, candidate):
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    if user.must_change_password:
        raise HTTPException(status_code=403, detail="Password change required before accessing this resource.")
    if user.role == "candidate" and candidate.user_id == user.id:
        return candidate
    if user.role == "hr" and hr_candidate_query(db, user.id).filter(
        Application.candidate_id == candidate.id
    ).first():
        return candidate
    raise HTTPException(status_code=403, detail="You cannot access this candidate profile.")


def require_job_owner(job, user):
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.created_by != user.id:
        raise HTTPException(status_code=403, detail="You cannot access another recruiter's job.")
    return job
