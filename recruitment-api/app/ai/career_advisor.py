import json
import os
import re
from typing import Any, Dict, List, Optional


CAREER_FIELDS = [
    {
        "career_field": "Frontend Developer",
        "related_skills": [
            "React", "JavaScript", "TypeScript", "HTML", "CSS",
            "Tailwind CSS", "Bootstrap", "UI Development", "REST API"
        ],
        "description": "Builds user interfaces, dashboards, landing pages, and web app screens."
    },
    {
        "career_field": "Backend Developer",
        "related_skills": [
            "Python", "FastAPI", "Django", "Flask", "SQL",
            "PostgreSQL", "MongoDB", "REST API", "Docker"
        ],
        "description": "Builds APIs, database systems, authentication, and server-side logic."
    },
    {
        "career_field": "Full Stack Developer",
        "related_skills": [
            "React", "JavaScript", "Python", "FastAPI",
            "Node.js", "SQL", "REST API", "MongoDB"
        ],
        "description": "Works on both frontend UI and backend APIs."
    },
    {
        "career_field": "AI/ML Intern",
        "related_skills": [
            "Python", "Machine Learning", "Deep Learning", "NLP",
            "Generative AI", "Artificial Intelligence", "Pandas",
            "NumPy", "Scikit-learn", "TensorFlow", "PyTorch"
        ],
        "description": "Works on AI models, ML workflows, NLP, data processing, and model evaluation."
    },
    {
        "career_field": "Data Analyst",
        "related_skills": [
            "Python", "SQL", "Pandas", "NumPy",
            "Data Analysis", "Excel", "Visualization"
        ],
        "description": "Analyzes data, creates reports, dashboards, and business insights."
    },
    {
        "career_field": "Software Developer",
        "related_skills": [
            "C", "C++", "Java", "Python", "DSA",
            "OOP", "Git", "GitHub", "SQL"
        ],
        "description": "Builds software applications, solves programming problems, and works with core logic."
    },
    {
        "career_field": "UI Developer",
        "related_skills": [
            "HTML", "CSS", "React", "Responsive Design",
            "UI Design", "JavaScript", "Figma"
        ],
        "description": "Focuses on visual design, responsive layouts, and polished user interfaces."
    },
]


def normalize_list(value: Any) -> List[str]:
    if not value:
        return []

    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    if isinstance(value, str):
        value = value.strip()

        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except Exception:
            pass

        return [item.strip() for item in value.split(",") if item.strip()]

    return []


def normalize_resume_data(resume_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "skills": normalize_list(resume_data.get("skills")),
        "education": resume_data.get("education", ""),
        "experience": resume_data.get("experience", ""),
        "certifications": resume_data.get("certifications", ""),
        "projects": resume_data.get("projects", ""),
    }


def skill_match(candidate_skills: List[str], related_skills: List[str]) -> List[str]:
    candidate_skill_set = {skill.lower().strip() for skill in candidate_skills}
    matched = []

    for skill in related_skills:
        if skill.lower().strip() in candidate_skill_set:
            matched.append(skill)

    return matched


def get_fit_label(score: int) -> str:
    if score >= 80:
        return "Strong Fit"
    if score >= 50:
        return "Good Fit"
    return "Explore"


def build_reason(field: str, matched: List[str], missing: List[str], score: int) -> str:
    if matched:
        matched_text = ", ".join(matched[:4])

        if score >= 80:
            return (
                f"Based on your skills in {matched_text}, you have a strong chance "
                f"in {field} roles."
            )

        if score >= 50:
            improve_text = ", ".join(missing[:3]) if missing else "advanced project experience"
            return (
                f"Your skills in {matched_text} make {field} a good direction. "
                f"Improve {improve_text} to become stronger."
            )

        improve_text = ", ".join(missing[:3]) if missing else "more related tools"
        return (
            f"You have some foundation for {field} through {matched_text}. "
            f"You can explore this path by learning {improve_text}."
        )

    return (
        f"You can explore {field}, but your resume currently does not show many direct skills "
        f"for this path. Start by learning {', '.join(missing[:4])}."
    )


def rule_based_career_suggestions(resume_data: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = normalize_resume_data(resume_data)
    candidate_skills = cleaned["skills"]

    suggestions = []

    for field in CAREER_FIELDS:
        related_skills = field["related_skills"]
        matched = skill_match(candidate_skills, related_skills)

        score = round((len(matched) / len(related_skills)) * 100) if related_skills else 0
        missing = [skill for skill in related_skills if skill not in matched]

        suggestions.append({
            "career_field": field["career_field"],
            "fit_score": score,
            "fit_label": get_fit_label(score),
            "matched_skills": matched,
            "recommended_skills": missing[:6],
            "reason": build_reason(field["career_field"], matched, missing, score),
            "description": field["description"],
        })

    suggestions.sort(key=lambda item: item["fit_score"], reverse=True)

    return {
        "source": "rule_based",
        "resume_skills": candidate_skills,
        "suggestions": suggestions[:5],
    }


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None

    cleaned = text.strip()
    cleaned = re.sub(r"```json", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"```", "", cleaned).strip()

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return None

    return None


def validate_ai_result(result: Dict[str, Any], fallback_result: Dict[str, Any]) -> Dict[str, Any]:
    suggestions = result.get("suggestions")

    if not isinstance(suggestions, list) or len(suggestions) == 0:
        return fallback_result

    cleaned_suggestions = []

    for item in suggestions[:5]:
        if not isinstance(item, dict):
            continue

        career_field = item.get("career_field") or "Career Path"
        fit_score = item.get("fit_score", 0)

        try:
            fit_score = int(fit_score)
        except Exception:
            fit_score = 0

        fit_score = max(0, min(100, fit_score))

        cleaned_suggestions.append({
            "career_field": career_field,
            "fit_score": fit_score,
            "fit_label": item.get("fit_label") or get_fit_label(fit_score),
            "matched_skills": normalize_list(item.get("matched_skills")),
            "recommended_skills": normalize_list(item.get("recommended_skills")),
            "reason": item.get("reason") or "Career suggestion generated from resume data.",
            "description": item.get("description") or "Suggested career direction based on your resume.",
        })

    if not cleaned_suggestions:
        return fallback_result

    cleaned_suggestions.sort(key=lambda item: item["fit_score"], reverse=True)

    return {
        "source": "gemini",
        "resume_skills": normalize_list(
            result.get("resume_skills") or fallback_result.get("resume_skills")
        ),
        "suggestions": cleaned_suggestions,
    }


def gemini_career_suggestions(
    resume_data: Dict[str, Any],
    fallback_result: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return None

    try:
        from google import genai
    except Exception:
        return None

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""
You are an AI career advisor inside a recruitment platform.

Analyze this parsed resume data and suggest the top 5 suitable career fields.

Rules:
- Return JSON only.
- Do not include markdown.
- Do not include extra explanation outside JSON.
- Fit score must be from 0 to 100.
- Suggest realistic fields from software, AI, data, web development, or related tech roles.
- Base the result only on skills, education, experience, certifications, and projects.
- Do not use age, gender, religion, caste, photo, address, or personal background.

Return JSON in this exact format:
{{
  "source": "gemini",
  "resume_skills": ["skill1", "skill2"],
  "suggestions": [
    {{
      "career_field": "AI/ML Intern",
      "fit_score": 85,
      "fit_label": "Strong Fit",
      "matched_skills": ["Python", "Machine Learning"],
      "recommended_skills": ["Scikit-learn", "Pandas"],
      "reason": "Short reason here",
      "description": "Short field description"
    }}
  ]
}}

Parsed resume data:
{json.dumps(resume_data, ensure_ascii=False)}
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        text = response.text if hasattr(response, "text") else ""
        parsed = extract_json_from_text(text)

        if not parsed:
            return None

        return validate_ai_result(parsed, fallback_result)

    except Exception as error:
        print(f"Gemini career suggestion failed: {error}")
        return None


def get_career_suggestions(resume_data: Dict[str, Any]) -> Dict[str, Any]:
    fallback_result = rule_based_career_suggestions(resume_data)

    gemini_result = gemini_career_suggestions(resume_data, fallback_result)

    if gemini_result:
        return gemini_result

    return fallback_result