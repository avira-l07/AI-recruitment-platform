import re
from typing import Dict, List, Set

# A larger canonical skill library. Keep this list practical for student/internship + HR demo use.
SKILLS_LIST = [
    "Python", "Java", "C++", "C#", "C", "JavaScript", "TypeScript",
    "React", "Angular", "Vue", "Node.js", "Express.js", "HTML", "CSS",
    "Tailwind CSS", "Bootstrap", "Responsive Design", "UI Development", "Figma",
    "FastAPI", "Django", "Flask", "REST API", "GraphQL", "Microservices",
    "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis", "NoSQL",
    "Machine Learning", "Deep Learning", "Artificial Intelligence", "Generative AI",
    "NLP", "Computer Vision", "Data Analysis", "Data Visualization", "Statistics",
    "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch", "Keras",
    "MLOps", "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Linux",
    "Git", "GitHub", "CI/CD", "OOP", "DSA", "Data Structures", "Algorithms",
    "Excel", "Power BI", "Tableau", "Hadoop", "Spark", "Kafka", "Hive", "HBase",
]

SKILL_ALIASES: Dict[str, List[str]] = {
    "JavaScript": ["js", "ecmascript"],
    "TypeScript": ["ts"],
    "React": ["reactjs", "react.js"],
    "Node.js": ["nodejs", "node js", "node"],
    "Express.js": ["expressjs", "express js", "express"],
    "REST API": ["restful api", "rest apis", "api integration", "apis"],
    "Machine Learning": ["ml", "machine-learning"],
    "Artificial Intelligence": ["ai", "artificial-intelligence"],
    "Generative AI": ["gen ai", "genai", "llm", "large language model"],
    "Natural Language Processing": ["nlp"],
    "Computer Vision": ["cv", "opencv"],
    "Scikit-learn": ["sklearn", "scikit learn"],
    "TensorFlow": ["tensorflow"],
    "PyTorch": ["pytorch"],
    "Tailwind CSS": ["tailwind"],
    "Responsive Design": ["responsive ui", "mobile responsive"],
    "Data Visualization": ["visualization", "visualisation"],
    "PostgreSQL": ["postgres"],
    "MongoDB": ["mongo"],
    "CI/CD": ["cicd", "continuous integration", "continuous deployment"],
    "OOP": ["object oriented", "object-oriented programming"],
    "DSA": ["data structures and algorithms"],
}

# Normalize alias canonical name used above.
SKILL_ALIASES["NLP"] = SKILL_ALIASES.pop("Natural Language Processing")


def _pattern_for_skill(skill: str) -> re.Pattern:
    escaped = re.escape(skill.lower())
    # C, C++, C# and Node.js need special handling; word boundary after plus/hash/dot is unreliable.
    if skill in {"C", "C++", "C#", "Node.js", "Express.js"}:
        return re.compile(r"(?<![a-z0-9+#.])" + escaped + r"(?![a-z0-9+#.])", re.IGNORECASE)
    return re.compile(r"\b" + escaped + r"\b", re.IGNORECASE)


def extract_skills(text: str) -> List[str]:
    """Extract canonical skills from resume/job text using exact phrase and alias matching."""
    if not text:
        return []

    text_lower = text.lower()
    found: Set[str] = set()

    for skill in SKILLS_LIST:
        if _pattern_for_skill(skill).search(text_lower):
            found.add(skill)
            continue

        for alias in SKILL_ALIASES.get(skill, []):
            if re.search(r"\b" + re.escape(alias.lower()) + r"\b", text_lower, re.IGNORECASE):
                found.add(skill)
                break

    # Keep stable order according to SKILLS_LIST.
    return [skill for skill in SKILLS_LIST if skill in found]


def normalize_skill_list(value) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        raw = value
    else:
        raw = re.split(r"[,;|\n]", str(value))

    normalized = []
    seen = set()
    for item in raw:
        skill = str(item).strip()
        if not skill:
            continue
        matched = extract_skills(skill)
        canonical = matched[0] if matched else skill
        key = canonical.lower()
        if key not in seen:
            seen.add(key)
            normalized.append(canonical)
    return normalized
