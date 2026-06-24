from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import engine, Base, SessionLocal

import app.models.user
import app.models.candidate
import app.models.resume
import app.models.job
import app.models.match_score

from app.api import auth, candidates, resumes, jobs as jobs_api, matching, analytics

app = FastAPI(title="AI Recruitment Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(candidates.router)
app.include_router(resumes.router)
app.include_router(jobs_api.router)
app.include_router(matching.router)
app.include_router(analytics.router)

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if hasattr(jobs_api, "seed_default_jobs"):
            jobs_api.seed_default_jobs(db)
    finally:
        db.close()

@app.get("/")
def root():
    return {
        "message": "AI Recruitment Platform API is running",
        "status": "ok"
    }