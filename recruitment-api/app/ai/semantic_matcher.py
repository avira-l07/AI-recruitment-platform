from typing import Dict, List, Tuple
from app.ai.skill_extractor import normalize_skill_list

SKILL_RELATIONS: Dict[str, List[str]] = {
    "JavaScript": ["React", "Node.js", "Express.js", "TypeScript"],
    "React": ["JavaScript", "HTML", "CSS", "REST API"],
    "HTML": ["React", "CSS", "UI Development", "Responsive Design"],
    "CSS": ["HTML", "React", "Tailwind CSS", "Bootstrap", "Responsive Design"],
    "REST API": ["FastAPI", "Django", "Flask", "Node.js", "React"],
    "Python": ["FastAPI", "Django", "Flask", "Pandas", "NumPy", "Machine Learning"],
    "FastAPI": ["Python", "REST API", "SQL"],
    "Django": ["Python", "REST API", "SQL"],
    "Flask": ["Python", "REST API"],
    "Machine Learning": ["Python", "Scikit-learn", "Pandas", "NumPy", "TensorFlow", "PyTorch"],
    "Deep Learning": ["Python", "TensorFlow", "PyTorch", "Keras", "Computer Vision", "NLP"],
    "NLP": ["Python", "Machine Learning", "Deep Learning", "Generative AI"],
    "Data Analysis": ["Python", "SQL", "Pandas", "NumPy", "Excel", "Power BI", "Tableau"],
    "SQL": ["PostgreSQL", "MySQL", "Data Analysis"],
    "NoSQL": ["MongoDB", "Redis"],
    "Docker": ["Kubernetes", "MLOps", "CI/CD"],
    "Kubernetes": ["Docker", "MLOps", "AWS"],
    "Git": ["GitHub", "CI/CD"],
    "GitHub": ["Git", "CI/CD"],
}


def _lower_map(items: List[str]) -> Dict[str, str]:
    return {str(item).lower().strip(): str(item).strip() for item in items if str(item).strip()}


def semantic_skill_match(candidate_skills, required_skills) -> Dict:
    candidate = normalize_skill_list(candidate_skills)
    required = normalize_skill_list(required_skills)
    candidate_map = _lower_map(candidate)

    direct = []
    semantic = []
    missing = []

    for req in required:
        key = req.lower().strip()
        if key in candidate_map:
            direct.append(req)
            continue

        related = SKILL_RELATIONS.get(req, [])
        evidence = [skill for skill in related if skill.lower().strip() in candidate_map]
        if evidence:
            semantic.append({"required_skill": req, "evidence_skills": evidence[:3]})
        else:
            missing.append(req)

    total = len(required)
    direct_ratio = len(direct) / total if total else 0
    semantic_ratio = len(semantic) / total if total else 0

    return {
        "required_skills": required,
        "candidate_skills": candidate,
        "direct_matches": direct,
        "semantic_matches": semantic,
        "missing_skills": missing,
        "direct_ratio": direct_ratio,
        "semantic_ratio": semantic_ratio,
    }
