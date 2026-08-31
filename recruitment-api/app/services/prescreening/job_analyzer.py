import re
from typing import Dict, List, Any, Optional

TECH_KEYWORDS_MAP = {
    "python": ["Python", "AsyncIO", "OOP", "Data Structures", "Type Hinting", "GIL", "Generators"],
    "fastapi": ["FastAPI", "Pydantic", "Dependency Injection", "OpenAPI", "Async Routes", "Starlette"],
    "django": ["Django", "ORM", "Django REST Framework", "Middleware", "Signals"],
    "flask": ["Flask", "WSGI", "Blueprints", "Jinja2"],
    "react": ["React", "Hooks", "State Management", "Component Lifecycle", "Virtual DOM", "Context API"],
    "javascript": ["JavaScript", "ES6+", "Event Loop", "Promises", "Async/Await", "Closures"],
    "typescript": ["TypeScript", "Generics", "Interfaces", "Type Safety", "Utility Types"],
    "node": ["Node.js", "Express", "Event Emitter", "Streams", "NPM"],
    "sql": ["SQL", "Queries", "Joins", "Indexing", "Transactions", "ACID", "Normalization"],
    "postgresql": ["PostgreSQL", "Query Optimization", "JSONB", "Connection Pooling", "EXPLAIN"],
    "mongodb": ["MongoDB", "Aggregation Pipeline", "Indexing", "Document Modeling", "Mongoose"],
    "docker": ["Docker", "Containers", "Dockerfile", "Multi-stage Builds", "Compose"],
    "kubernetes": ["Kubernetes", "Pods", "Deployments", "Services", "Ingress", "ConfigMaps"],
    "aws": ["AWS", "S3", "EC2", "Lambda", "IAM", "ECS", "CloudWatch"],
    "rest": ["REST APIs", "HTTP Status Codes", "Statelessness", "CRUD", "Idempotency"],
    "git": ["Git", "Branching", "Pull Requests", "Rebase", "Merge Conflicts"],
    "machine learning": ["Machine Learning", "Model Training", "Evaluation Metrics", "Feature Engineering", "Scikit-Learn"],
    "deep learning": ["Deep Learning", "Neural Networks", "PyTorch", "TensorFlow", "Backpropagation"],
    "nlp": ["NLP", "Transformers", "Tokenization", "Embeddings", "LLMs"],
}

SOFT_SKILLS_KEYWORDS = [
    "communication", "problem solving", "teamwork", "collaboration", "debugging",
    "critical thinking", "agile", "scrum", "mentorship", "leadership", "time management", "ownership"
]


def analyze_job_requirements(
    title: str,
    description: Optional[str] = "",
    required_skills: Optional[str] = "",
    experience_level: Optional[str] = "Mid",
    education_requirement: Optional[str] = ""
) -> Dict[str, Any]:
    """
    Analyzes a job posting and extracts structured technical and domain requirements.
    """
    full_text = f"{title} {description} {required_skills} {experience_level} {education_requirement}".lower()
    
    # Extract Technical Skills
    matched_tech = set()
    important_concepts = set()
    
    # Process explicit skills string
    if required_skills:
        for s in re.split(r"[,;|]+", required_skills):
            s_clean = s.strip()
            if s_clean:
                matched_tech.add(s_clean)
                for k, concepts in TECH_KEYWORDS_MAP.items():
                    if k in s_clean.lower():
                        important_concepts.update(concepts[:4])

    # Scan full text for known tech stacks
    for k, concepts in TECH_KEYWORDS_MAP.items():
        if re.search(rf"\b{re.escape(k)}\b", full_text):
            matched_tech.add(concepts[0])
            important_concepts.update(concepts[:3])

    # Extract Soft Skills
    matched_soft = []
    for soft in SOFT_SKILLS_KEYWORDS:
        if re.search(rf"\b{re.escape(soft)}\b", full_text):
            matched_soft.append(soft.title())

    # Extract Responsibilities from text lines
    responsibilities = []
    if description:
        lines = [l.strip(" -•*") for l in description.split("\n") if l.strip()]
        for line in lines:
            if any(verb in line.lower() for verb in ["build", "design", "develop", "implement", "maintain", "create", "collaborate", "lead", "manage", "optimize", "architect"]):
                if 15 < len(line) < 160:
                    responsibilities.append(line)

    if not responsibilities:
        responsibilities = [
            f"Develop and maintain reliable {title} software systems and RESTful APIs.",
            f"Write clean, maintainable code using {', '.join(list(matched_tech)[:3]) or 'modern frameworks'}.",
            "Collaborate with engineering teams on code reviews and system architecture."
        ]

    # Domain Requirements
    domain = []
    if any(k in full_text for k in ["fintech", "payment", "banking"]):
        domain.append("Fintech & Payments")
    if any(k in full_text for k in ["ai", "machine learning", "llm", "deep learning"]):
        domain.append("Artificial Intelligence & Machine Learning")
    if any(k in full_text for k in ["cloud", "devops", "infrastructure", "kubernetes"]):
        domain.append("Cloud & Distributed Systems")
    if any(k in full_text for k in ["frontend", "ui", "ux", "react", "web"]):
        domain.append("Web Application Architecture")
    if not domain:
        domain.append("Software Engineering")

    return {
        "title": title,
        "technical_skills": list(matched_tech) if matched_tech else ["Python", "Software Engineering"],
        "soft_skills": matched_soft if matched_soft else ["Problem Solving", "Debugging", "Communication"],
        "responsibilities": responsibilities[:5],
        "experience_requirements": [experience_level or "Mid-level experience (1-3 years)"],
        "domain_requirements": domain,
        "important_concepts": list(important_concepts) if important_concepts else ["Data Structures", "System Design", "REST APIs"],
        "role_complexity": experience_level or "Mid"
    }
