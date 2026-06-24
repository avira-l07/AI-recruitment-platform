def calculate_match(candidate_skills: list, candidate_education: str,
                    candidate_experience: str, candidate_projects: str,
                    job_required_skills: str, job_experience_level: str,
                    job_education_requirement: str) -> dict:
                    
    job_skills = [s.strip().lower() for s in job_required_skills.split(',') if s.strip()]
    cand_skills_lower = [s.lower() for s in candidate_skills]
    
    matched = [skill for skill in job_skills if skill in cand_skills_lower]
    
    if not job_skills:
        skill_score = 60.0
    else:
        skill_score = (len(matched) / len(job_skills)) * 60.0

    education_score = 10.0
    if job_education_requirement and candidate_education:
        job_edu_words = job_education_requirement.lower().split()
        cand_edu_lower = candidate_education.lower()
        if any(word in cand_edu_lower for word in job_edu_words if len(word) > 3):
            education_score = 20.0
            
    experience_score = 10.0 if candidate_experience and candidate_experience.strip() else 0.0
    project_score = 10.0 if candidate_projects and candidate_projects.strip() else 5.0
    
    total_score = skill_score + education_score + experience_score + project_score
    total_score = min(total_score, 100.0)
    
    job_skills_original = [s.strip() for s in job_required_skills.split(',') if s.strip()]
    matched_skills_original = [s for s in job_skills_original if s.lower() in cand_skills_lower]
    missing_skills_original = [s for s in job_skills_original if s.lower() not in cand_skills_lower]
    
    matched_str = ", ".join(matched_skills_original) if matched_skills_original else "none"
    missing_str = ", ".join(missing_skills_original) if missing_skills_original else "none"
    
    explanation = f"Candidate scored {round(total_score)}% because they matched {matched_str}. Missing skills are {missing_str}."
    
    return {
        "score": round(total_score),
        "matched_skills": matched_skills_original,
        "missing_skills": missing_skills_original,
        "explanation": explanation
    }