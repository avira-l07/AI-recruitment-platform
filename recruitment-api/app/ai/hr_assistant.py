import json
from typing import Dict, List
from app.ai.interview_generator import generate_interview_questions
from app.ai.roadmap_generator import build_learning_roadmap
from app.ai.gemini_client import call_gemini_json, get_gemini_health


def get_fit_label(score: int) -> str:
    if score >= 75:
        return "Strong Fit"
    if score >= 50:
        return "Good Fit"
    return "Explore"


def build_local_hr_insight(role: str, score: int, direct_matches: List[str], semantic_matches: List[Dict], missing_skills: List[str]) -> Dict:
    fit_label = get_fit_label(score)
    matched_text = ", ".join(direct_matches) if direct_matches else "no direct required skills"
    missing_text = ", ".join(missing_skills[:5]) if missing_skills else "no major required skills"

    if score >= 75:
        recommendation = "Shortlist"
        summary = f"{fit_label} for {role}. The candidate has strong direct skill coverage ({matched_text}) and can be considered for HR screening or technical interview."
    elif score >= 50:
        recommendation = "Review"
        summary = f"{fit_label} for {role}. The candidate has some useful match ({matched_text}) but still needs review because missing skills include {missing_text}."
    else:
        recommendation = "Do not shortlist yet"
        summary = f"{fit_label} for {role}. The candidate should not be treated as a strong match yet because direct skill coverage is low and missing skills include {missing_text}."

    semantic_text = ""
    if semantic_matches:
        semantic_bits = [f"{m['required_skill']} is partially related to {', '.join(m.get('evidence_skills', []))}" for m in semantic_matches]
        semantic_text = "Semantic relation found: " + "; ".join(semantic_bits[:4]) + "."
    else:
        semantic_text = "No strong semantic skill relation was found beyond direct matches."

    analysis = (
        f"The final score is controlled by transparent backend logic, not by free AI guessing. "
        f"Direct matches: {matched_text}. Missing: {missing_text}. {semantic_text}"
    )

    risks = []
    if len(direct_matches) <= 1:
        risks.append("Very low direct skill evidence; candidate may have keyword-level knowledge only.")
    if len(missing_skills) >= 4:
        risks.append("Several core requirements are missing from the resume.")
    if not risks:
        risks.append("No major risk detected from skill coverage; still verify practical experience in interview.")

    return {
        "fitLabel": fit_label,
        "hrSummary": summary,
        "aiSemanticAnalysis": analysis,
        "roadmap": build_learning_roadmap(role, missing_skills, direct_matches),
        "interviewQuestions": generate_interview_questions(role, direct_matches, missing_skills),
        "riskFlags": risks,
        "recommendation": recommendation,
        "aiSource": "local_ai",
        "fallbackReason": None,
    }


def enhance_hr_insight_with_gemini(base: Dict, role: str, score: int, direct_matches: List[str], semantic_matches: List[Dict], missing_skills: List[str]) -> Dict:
    prompt = f"""
You are an HR decision-support assistant.
You must NOT change score, fit label, matched skills, or missing skills.
Only improve the wording of HR summary, semantic analysis, roadmap, interview questions, risk flags, and recommendation.

Fixed controlled data:
Role: {role}
Score: {score}
Fit label: {base.get('fitLabel')}
Direct matches: {direct_matches}
Semantic matches: {semantic_matches}
Missing skills: {missing_skills}

Return JSON only with exactly these keys:
{{
  "hrSummary": "short HR-ready summary",
  "aiSemanticAnalysis": "clear analysis explaining candidate fit and risk",
  "roadmap": ["checkpoint 1", "checkpoint 2"],
  "interviewQuestions": ["question 1", "question 2"],
  "riskFlags": ["risk 1"],
  "recommendation": "Shortlist / Review / Do not shortlist yet"
}}
"""
    ai = call_gemini_json(prompt)
    if not ai:
        health = get_gemini_health()
        output = dict(base)
        if health.get("configured"):
            output["aiSource"] = "local_fallback"
            output["fallbackReason"] = health.get("last_error_message") or "Gemini was unavailable."
        return output

    # Guardrails: keep controlled values from backend.
    cleaned = dict(base)
    for key in ["hrSummary", "aiSemanticAnalysis", "roadmap", "interviewQuestions", "riskFlags", "recommendation"]:
        if key in ai and ai[key]:
            cleaned[key] = ai[key]
    cleaned["fitLabel"] = base.get("fitLabel")
    cleaned["aiSource"] = "hybrid"
    cleaned["fallbackReason"] = None
    return cleaned


def build_hr_insight(role: str, score: int, direct_matches: List[str], semantic_matches: List[Dict], missing_skills: List[str]) -> Dict:
    base = build_local_hr_insight(role, score, direct_matches, semantic_matches, missing_skills)
    return enhance_hr_insight_with_gemini(base, role, score, direct_matches, semantic_matches, missing_skills)
