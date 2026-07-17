from typing import Dict
from app.ai.semantic_matcher import semantic_skill_match
from app.ai.hr_assistant import build_hr_insight, get_fit_label


def _has_text(value: str) -> bool:
    return bool(value and str(value).strip() and str(value).strip().lower() != "not specified")


def _education_score(candidate_education: str, job_education_requirement: str) -> int:
    if not _has_text(job_education_requirement):
        return 5
    if not _has_text(candidate_education):
        return 0
    cand = candidate_education.lower()
    job = job_education_requirement.lower()
    keywords = ["b.tech", "bca", "bachelor", "computer science", "ai", "ml", "engineering", "master", "m.tech"]
    return 10 if any(k in cand and k in job for k in keywords) or any(k in cand for k in keywords) else 4


def calculate_match(candidate_skills: list, candidate_education: str,
                    candidate_experience: str, candidate_projects: str,
                    job_required_skills: str, job_experience_level: str,
                    job_education_requirement: str) -> dict:
    return calculate_hybrid_match(
        candidate_skills=candidate_skills,
        candidate_education=candidate_education,
        candidate_experience=candidate_experience,
        candidate_projects=candidate_projects,
        job_required_skills=job_required_skills,
        job_experience_level=job_experience_level,
        job_education_requirement=job_education_requirement,
        role="Job Role",
    )


def calculate_hybrid_match(candidate_skills: list, candidate_education: str,
                           candidate_experience: str, candidate_projects: str,
                           job_required_skills: str, job_experience_level: str,
                           job_education_requirement: str, role: str = "Job Role") -> Dict:
    skill_result = semantic_skill_match(candidate_skills, job_required_skills)
    required = skill_result["required_skills"]
    direct = skill_result["direct_matches"]
    semantic = skill_result["semantic_matches"]
    missing = skill_result["missing_skills"]

    if not required:
        total_score = 0
    else:
        direct_points = skill_result["direct_ratio"] * 70
        semantic_points = min(skill_result["semantic_ratio"] * 15, 15)
        education_points = _education_score(candidate_education, job_education_requirement)
        experience_points = 5 if _has_text(candidate_experience) else 0
        project_points = 10 if _has_text(candidate_projects) else 0
        total_score = round(direct_points + semantic_points + education_points + experience_points + project_points)

        # Guardrails: semantic relation can help but cannot fake a strong fit.
        direct_ratio = skill_result["direct_ratio"]
        if direct_ratio < 0.20:
            total_score = min(total_score, 35)
        elif direct_ratio < 0.40:
            total_score = min(total_score, 55)
        elif direct_ratio < 0.60:
            total_score = min(total_score, 75)

    total_score = max(0, min(100, int(total_score)))
    insight = build_hr_insight(role, total_score, direct, semantic, missing)

    explanation = (
        f"{insight['fitLabel']} · {total_score}%. "
        f"Matched {len(direct)} of {len(required)} required skills directly. "
        f"Semantic support found for {len(semantic)} skill(s)."
    )

    return {
        "score": total_score,
        "fit_label": get_fit_label(total_score),
        "matched_skills": direct,
        "semantic_matches": semantic,
        "missing_skills": missing,
        "required_skills": required,
        "explanation": explanation,
        "hr_summary": insight.get("hrSummary"),
        "ai_semantic_analysis": insight.get("aiSemanticAnalysis"),
        "roadmap": insight.get("roadmap"),
        "interview_questions": insight.get("interviewQuestions"),
        "risk_flags": insight.get("riskFlags"),
        "recommendation": insight.get("recommendation"),
        "ai_source": insight.get("aiSource"),
    }
