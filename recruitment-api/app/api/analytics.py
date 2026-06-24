from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.match_score import MatchScore
from collections import Counter

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/overview")
def get_overview(db: Session = Depends(get_db)):
    total_candidates = db.query(Candidate).count()
    total_jobs = db.query(Job).count()
    shortlisted = db.query(MatchScore).filter(MatchScore.status == "Shortlisted").count()
    rejected = db.query(MatchScore).filter(MatchScore.status == "Rejected").count()
    
    avg_score_raw = db.query(func.avg(MatchScore.score)).scalar()
    average_match_score = round(avg_score_raw, 1) if avg_score_raw else 0.0
    
    strong = db.query(MatchScore).filter(MatchScore.score >= 70).count()
    moderate = db.query(MatchScore).filter(MatchScore.score >= 40, MatchScore.score < 70).count()
    weak = db.query(MatchScore).filter(MatchScore.score < 40).count()
    
    all_candidates = db.query(Candidate.skills).all()
    skill_counter = Counter()
    for row in all_candidates:
        if row[0]:
            skills = [s.strip() for s in row[0].split(',') if s.strip()]
            skill_counter.update(skills)
            
    top_skills = [skill for skill, count in skill_counter.most_common(8)]
    
    return {
        "total_candidates": total_candidates,
        "total_jobs": total_jobs,
        "shortlisted_candidates": shortlisted,
        "rejected_candidates": rejected,
        "average_match_score": average_match_score,
        "top_skills": top_skills,
        "score_distribution": {
            "strong": strong,
            "moderate": moderate,
            "weak": weak
        }
    }