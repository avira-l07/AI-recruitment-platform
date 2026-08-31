import json
import logging
from typing import Dict, List, Any, Optional
from app.ai.gemini_client import call_gemini_json
from app.services.prescreening.job_analyzer import analyze_job_requirements

logger = logging.getLogger(__name__)


def generate_local_hybrid_questions(requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Deterministically generates 4 role-specific questions based on analyzed job requirements.
    """
    title = requirements.get("title", "Software Engineer")
    tech_list = requirements.get("technical_skills", ["Python", "REST APIs"])
    primary_tech = tech_list[0] if tech_list else "Python"
    secondary_tech = tech_list[1] if len(tech_list) > 1 else "REST APIs"
    database_tech = next((t for t in tech_list if t.lower() in ["sql", "postgresql", "mongodb", "database"]), "PostgreSQL / SQL")
    
    questions = [
        {
            "question_text": f"Explain how you would design and structure a clean, production-ready backend service or API using {primary_tech} and {secondary_tech}. What key architectural patterns and validation techniques would you use?",
            "question_type": "technical",
            "category": "Technical Architecture",
            "scoring_criteria": f"Evaluates understanding of {primary_tech} fundamentals, modular design, schema validation, error handling, and RESTful principles.",
            "expected_concepts": [primary_tech, "Validation", "Error Handling", "Architecture", "API", "Modularity"],
            "weight": 1.25,
            "is_required": True,
            "order_index": 0
        },
        {
            "question_text": f"Your production service begins experiencing elevated latency and slow responses during peak database traffic on {database_tech}. What metrics, queries, and system bottlenecks would you investigate first?",
            "question_type": "scenario",
            "category": "System Reliability & Scaling",
            "scoring_criteria": f"Evaluates practical performance troubleshooting: database indexing, connection pooling, slow query analysis (EXPLAIN), caching, and resource monitoring.",
            "expected_concepts": ["Indexing", "Connection Pool", "Slow Queries", "Caching", "Latency", "Bottleneck"],
            "weight": 1.0,
            "is_required": True,
            "order_index": 1
        },
        {
            "question_text": f"Describe a significant project where you built software using {primary_tech}. What was the most technically challenging problem you solved, and how did you verify its correctness?",
            "question_type": "practical",
            "category": "Project Experience & Implementation",
            "scoring_criteria": "Evaluates hands-on engineering experience, problem-solving depth, testing methodologies (unit/integration tests), and code quality.",
            "expected_concepts": ["Project", "Testing", "Architecture", "Challenge", "Implementation", "Correctness"],
            "weight": 1.0,
            "is_required": True,
            "order_index": 2
        },
        {
            "question_text": "A deployed endpoint suddenly starts throwing intermittent 500 Internal Server Errors in production. Walk us step-by-step through your debugging and root-cause analysis approach.",
            "question_type": "problem_solving",
            "category": "Debugging & Root-Cause Analysis",
            "scoring_criteria": "Evaluates systematic troubleshooting: log inspection, stack trace analysis, reproducing in staging, rollback strategies, and adding observability.",
            "expected_concepts": ["Logs", "Stack Trace", "Root Cause", "Reproduce", "Monitoring", "Fix"],
            "weight": 1.0,
            "is_required": True,
            "order_index": 3
        }
    ]
    return questions


def generate_prescreening_questions(
    title: str,
    description: Optional[str] = "",
    required_skills: Optional[str] = "",
    experience_level: Optional[str] = "Mid",
    education_requirement: Optional[str] = ""
) -> List[Dict[str, Any]]:
    """
    Analyzes job requirements and generates 3-5 role-specific pre-screening questions using Gemini or local hybrid fallback.
    """
    reqs = analyze_job_requirements(
        title=title,
        description=description,
        required_skills=required_skills,
        experience_level=experience_level,
        education_requirement=education_requirement
    )

    local_fallback = generate_local_hybrid_questions(reqs)

    prompt = f"""
You are an expert technical recruiter and hiring engineer.
Analyze the following JOB REQUIREMENTS for the role "{title}":
- Role: {title} ({experience_level})
- Required Technical Skills: {', '.join(reqs.get('technical_skills', []))}
- Responsibilities: {json.dumps(reqs.get('responsibilities', []))}
- Key Concepts: {', '.join(reqs.get('important_concepts', []))}

Generate EXACTLY 4 high-quality, practical pre-screening questions:
1. Technical Concept Question: Framework/architecture design.
2. Production Scenario Question: Latency, scale, or failure handling.
3. Practical Project Question: Past concrete engineering challenge.
4. Problem Solving / Debugging Question: Root-cause analysis of 500/bug.

CRITICAL RULES:
- Questions must be grounded in the skills listed above. Do NOT invent unrelated technologies.
- Return a JSON object with key "questions" containing a list of objects with keys:
  - "question_text": str
  - "question_type": "technical" | "scenario" | "practical" | "problem_solving"
  - "category": str
  - "scoring_criteria": str
  - "expected_concepts": list[str]
  - "weight": float (between 1.0 and 1.5)
  - "is_required": bool (true)
"""

    gemini_resp = call_gemini_json(prompt)
    if gemini_resp and isinstance(gemini_resp, dict) and "questions" in gemini_resp and isinstance(gemini_resp["questions"], list):
        questions = gemini_resp["questions"]
        if len(questions) >= 3:
            for idx, q in enumerate(questions):
                q["order_index"] = idx
                if "weight" not in q:
                    q["weight"] = 1.0
                if "is_required" not in q:
                    q["is_required"] = True
            return questions[:5]

    return local_fallback
