from typing import Dict, List


def _has_real_text(value) -> bool:
    if not value:
        return False
    if isinstance(value, list):
        return any(_has_real_text(v) for v in value)
    text = str(value).strip().lower()
    return text not in {"not specified", "not found", "none", "null", ""} and len(text) >= 8


def validate_resume_quality(parsed: Dict, extracted_text: str) -> Dict:
    """Reject fake/empty resumes like a PDF containing only 'Java SQL'."""
    reasons: List[str] = []
    warnings: List[str] = []
    tips: List[str] = []

    word_count = int(parsed.get("word_count") or 0)
    skills = parsed.get("skills") or []
    has_name = _has_real_text(parsed.get("name")) and parsed.get("name") != "Not Found"
    has_email = _has_real_text(parsed.get("email"))
    has_phone = _has_real_text(parsed.get("phone"))
    has_education = _has_real_text(parsed.get("education"))
    has_experience = _has_real_text(parsed.get("experience"))
    has_projects = _has_real_text(parsed.get("projects"))
    has_certifications = _has_real_text(parsed.get("certifications"))

    score = 0
    if word_count >= 80:
        score += 25
    elif word_count >= 45:
        score += 18
    elif word_count >= 25:
        score += 8
    else:
        reasons.append("Resume has too little readable text. Add a complete resume, not only keywords.")

    if has_name:
        score += 15
    else:
        reasons.append("Candidate name was not found.")

    if has_email or has_phone:
        score += 15
    else:
        reasons.append("No contact detail was found. Add email or phone number.")

    content_sections = sum([has_education, has_experience, has_projects, has_certifications])
    score += min(content_sections * 12, 30)
    if content_sections == 0:
        reasons.append("No real education, experience, project, or certification section was found.")

    if len(skills) >= 5:
        score += 15
    elif len(skills) >= 2:
        score += 8
        warnings.append("Only a few skills were found. A professional resume should include projects and education too.")
    else:
        reasons.append("Not enough technical skills were found.")

    # Hard professional rejection rules.
    accepted = True
    if word_count < 35:
        accepted = False
    if not has_name and not (has_email or has_phone):
        accepted = False
    if content_sections == 0:
        accepted = False
    if score < 55:
        accepted = False

    if not has_name:
        tips.append("Add your full name at the top of the resume.")
    if not (has_email or has_phone):
        tips.append("Add email or phone number so HR can contact you.")
    if not has_education:
        tips.append("Add an Education section.")
    if not has_projects and not has_experience:
        tips.append("Add Projects or Experience with 2-3 bullet points.")
    if len(skills) < 5:
        tips.append("Add a clear Skills section with relevant technologies.")

    if not reasons and accepted:
        reasons.append("Resume passed professional completeness checks.")

    return {
        "accepted": accepted,
        "quality_score": max(0, min(100, score)),
        "reasons": reasons,
        "warnings": warnings,
        "tips": tips[:6],
        "signals": {
            "word_count": word_count,
            "has_name": has_name,
            "has_contact": bool(has_email or has_phone),
            "has_education": has_education,
            "has_experience": has_experience,
            "has_projects": has_projects,
            "has_certifications": has_certifications,
            "skill_count": len(skills),
        }
    }
