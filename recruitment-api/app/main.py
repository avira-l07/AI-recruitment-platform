import os
from contextlib import asynccontextmanager
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("uploads", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if hasattr(jobs_api, "seed_default_jobs"):
            jobs_api.seed_default_jobs(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title="AI Recruitment Intelligence Platform API",
    version="2.0.0",
    lifespan=lifespan
)

origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,https://ai-recruitment-frontend-wg2t.onrender.com").split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.onrender\.com",
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

@app.get("/")
def root():
    return {"message": "AI Recruitment Intelligence Platform API is running", "status": "ok", "version": "2.0.0"}
