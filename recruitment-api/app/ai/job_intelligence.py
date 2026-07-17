from typing import Dict
from app.ai.skill_extractor import extract_skills, normalize_skill_list
from app.ai.gemini_client import call_gemini_json


def analyze_job_description(title: str, description: str, required_skills: str, experience_level: str = "") -> Dict:
    text = f"{title}\n{description}\n{required_skills}"
    extracted = extract_skills(text)
    required = normalize_skill_list(required_skills) or extracted

    lower = text.lower()
    if any(k in lower for k in ["machine learning", "deep learning", "nlp", "ai", "tensorflow", "pytorch"]):
        category = "AI/Data"
    elif any(k in lower for k in ["react", "frontend", "html", "css", "ui"]):
        category = "Frontend"
    elif any(k in lower for k in ["api", "backend", "fastapi", "django", "database"]):
        category = "Backend"
    else:
        category = "Software"

    base = {
        "source": "hybrid_local_ai",
        "jobCategory": category,
        "coreSkills": required[:8],
        "niceToHaveSkills": [s for s in extracted if s not in required][:6],
        "difficultyLevel": experience_level or "Not specified",
        "interviewFocus": [f"Practical knowledge of {s}" for s in required[:5]],
        "jobQualityWarnings": [] if len(required) >= 3 else ["Add at least 3-5 clear required skills for better matching."],
        "aiSummary": f"This job looks like a {category} role. Matching will prioritize direct required skills and use semantic AI only as a small supporting signal.",
    }

    prompt = f"""
Analyze this job for HR. Do not remove required skills. Return JSON with jobCategory, coreSkills, niceToHaveSkills, difficultyLevel, interviewFocus, jobQualityWarnings, aiSummary.
Title: {title}
Description: {description}
Required skills: {required_skills}
Experience level: {experience_level}
"""
    ai = call_gemini_json(prompt)
    if ai:
        for key in ["jobCategory", "niceToHaveSkills", "difficultyLevel", "interviewFocus", "jobQualityWarnings", "aiSummary"]:
            if ai.get(key):
                base[key] = ai[key]
        base["source"] = "gemini_text_enhanced"
    return base
