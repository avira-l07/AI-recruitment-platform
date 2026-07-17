import json
import hashlib
from typing import Any, Dict, List
from app.ai.semantic_matcher import semantic_skill_match
from app.ai.hr_assistant import get_fit_label
from app.ai.roadmap_generator import build_learning_roadmap
from app.ai.gemini_client import call_gemini_json
from app.schemas.career_analysis import GeminiEnhancementResponse

CAREER_FIELDS = [
    {"career_field": "AI/ML Engineer", "related_skills": ["Python", "Machine Learning", "Deep Learning", "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch"], "description": "Builds and evaluates AI/ML models for real-world problems."},
    {"career_field": "Python Developer", "related_skills": ["Python", "OOP", "SQL", "FastAPI", "Django", "Flask", "Git", "REST API"], "description": "Builds Python applications, APIs, automation, and backend systems."},
    {"career_field": "Deep Learning Engineer", "related_skills": ["Python", "Deep Learning", "TensorFlow", "PyTorch", "Keras", "Computer Vision", "NLP", "MLOps"], "description": "Works on neural networks, model training, and deep learning deployment."},
    {"career_field": "NLP Data Engineer", "related_skills": ["Python", "NLP", "Machine Learning", "Pandas", "NumPy", "SQL", "Generative AI", "Data Analysis"], "description": "Builds text-processing pipelines and NLP-powered data products."},
    {"career_field": "Big Data Engineer", "related_skills": ["Python", "Java", "SQL", "Hadoop", "Spark", "Kafka", "Hive", "AWS"], "description": "Builds scalable data pipelines and big data systems."},
    {"career_field": "Frontend Developer", "related_skills": ["React", "JavaScript", "HTML", "CSS", "Git", "REST API", "Responsive Design"], "description": "Builds user interfaces, dashboards, and responsive web screens."},
    {"career_field": "Backend Developer", "related_skills": ["Python", "FastAPI", "Django", "Flask", "SQL", "PostgreSQL", "MongoDB", "REST API"], "description": "Builds APIs, database systems, authentication, and server logic."},
    {"career_field": "Full Stack Developer", "related_skills": ["React", "JavaScript", "Python", "FastAPI", "Node.js", "SQL", "REST API", "MongoDB"], "description": "Works across frontend UI, backend APIs, and databases."},
    {"career_field": "Data Analyst", "related_skills": ["Python", "SQL", "Pandas", "NumPy", "Data Analysis", "Excel", "Power BI", "Tableau"], "description": "Analyzes data, prepares dashboards, and creates business insights."},
    {"career_field": "Software Developer", "related_skills": ["C", "C++", "Java", "Python", "DSA", "OOP", "Git", "SQL"], "description": "Builds software applications and solves programming problems."},
]


def normalize_list(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
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


def create_resume_hash(resume_data: Dict[str, Any]) -> str:
    cleaned = normalize_resume_data(resume_data)
    serialized = json.dumps(cleaned, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _score_for_field(candidate_skills: List[str], related_skills: List[str]) -> Dict:
    result = semantic_skill_match(candidate_skills, related_skills)
    direct_ratio = result["direct_ratio"]
    semantic_ratio = result["semantic_ratio"]
    score = round((direct_ratio * 80) + (semantic_ratio * 15))
    if direct_ratio < 0.20:
        score = min(score, 35)
    elif direct_ratio < 0.40:
        score = min(score, 55)
    return {**result, "score": max(0, min(100, score))}


def rule_based_career_suggestions(resume_data: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = normalize_resume_data(resume_data)
    candidate_skills = cleaned["skills"]
    suggestions = []

    for field in CAREER_FIELDS:
        match = _score_for_field(candidate_skills, field["related_skills"])
        score = match["score"]
        missing = match["missing_skills"]
        matched = match["direct_matches"]
        semantic = match["semantic_matches"]

        suggestions.append({
            "career_field": field["career_field"],
            "fit_score": score,
            "fit_label": get_fit_label(score),
            "matched_skills": matched,
            "semantic_matches": semantic,
            "recommended_skills": missing[:6],
            "description": field["description"],
            "reason": f"Matched {len(matched)} direct skill(s), with {len(semantic)} semantic relation(s). Missing skills: {', '.join(missing[:4]) if missing else 'none'}.",
            "ai_analysis": f"This path is suggested because your resume skills overlap with {field['career_field']} requirements. The score is controlled by backend rules.",
            "roadmap": build_learning_roadmap(field["career_field"], missing, matched),
        })

    suggestions.sort(key=lambda item: item["fit_score"], reverse=True)
    return {"source": "local", "resume_skills": candidate_skills, "suggestions": suggestions[:5]}


def get_career_suggestions(resume_data: Dict[str, Any]) -> Dict[str, Any]:
    return rule_based_career_suggestions(resume_data)


def generate_gemini_career_suggestions(resume_data: Dict[str, Any], local_results: Dict[str, Any]) -> Dict[str, Any]:
    cleaned_resume = normalize_resume_data(resume_data)
    input_payload = {
        "resume": {
            "skills": cleaned_resume["skills"],
            "education": cleaned_resume["education"],
            "experience": cleaned_resume["experience"][:4000],
            "projects": cleaned_resume["projects"][:2500],
            "certifications": cleaned_resume["certifications"][:1500]
        },
        "local_results": [
            {
                "career_field": item["career_field"],
                "matched_skills": item["matched_skills"],
                "recommended_skills": item["recommended_skills"],
                "description": item["description"],
                "reason": item["reason"]
            } for item in local_results.get("suggestions", [])
        ]
    }

    prompt = f"""
You are an expert AI Career Advisor and HR Resume Evaluator.
Given the candidate's parsed resume details and a list of local career matching results, you must enhance the qualitative reports.

CRITICAL CONSTRAINTS:
1. Do NOT alter the candidate's name, contact info, skills list, experience details, or matching fit_scores.
2. For each career field in 'local_results', provide professional, highly tailored career suggestion descriptions, personalized explanations ('reason'), constructive AI assessments ('ai_analysis'), and step-by-step learning roadmaps ('roadmap').
3. Produce a consolidated summary of the resume ('candidateSummary'), standard strengths list, weakness areas, and practical improvement tips.
4. Return your entire response in structured JSON format matching the schema below.

JSON SCHEMA:
{{
  "candidateSummary": "A professional summary of the candidate's qualifications and potential.",
  "strengths": [
    "Strength 1 description",
    "Strength 2 description"
  ],
  "weaknesses": [
    "Weakness area 1",
    "Weakness area 2"
  ],
  "resumeImprovementTips": [
    "Actionable tip 1",
    "Actionable tip 2"
  ],
  "suggestions": [
    {{
      "career_field": "ML/AI Engineer (matches local_results career_field name exactly)",
      "description": "Enhanced overview of this career field role.",
      "reason": "Personalized reason why candidate matches based on their skills.",
      "ai_analysis": "Deep semantic review of candidate qualifications for this career path.",
      "roadmap": [
        "Step 1: Focus on learning PyTorch",
        "Step 2: Build deep learning projects"
      ]
    }}
  ]
}}

INPUT DATA:
{json.dumps(input_payload, ensure_ascii=False)}
"""
    ai_data = call_gemini_json(prompt)
    if not ai_data:
        return {}

    try:
        GeminiEnhancementResponse.model_validate(ai_data)
    except Exception as e:
        print("Pydantic validation failed for Gemini career enhancements:", e)
        return {}

    return ai_data


def merge_local_and_gemini_results(local_res: Dict[str, Any], ai_res: Dict[str, Any]) -> Dict[str, Any]:
    enhanced_suggestions = []
    ai_sug_map = {item.get("career_field"): item for item in ai_res.get("suggestions", []) if isinstance(item, dict)}

    for local_item in local_res.get("suggestions", []):
        item = dict(local_item)
        career = item.get("career_field")
        ai_item = ai_sug_map.get(career)

        if ai_item:
            for key in ["description", "reason", "ai_analysis", "roadmap"]:
                if ai_item.get(key):
                    item[key] = ai_item[key]
        enhanced_suggestions.append(item)

    return {
        "suggestions": enhanced_suggestions,
        "aiInsights": {
            "candidateSummary": ai_res.get("candidateSummary", ""),
            "strengths": ai_res.get("strengths", []),
            "weaknesses": ai_res.get("weaknesses", []),
            "resumeImprovementTips": ai_res.get("resumeImprovementTips", [])
        }
    }
