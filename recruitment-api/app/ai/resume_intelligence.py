from typing import Dict
from app.ai.gemini_client import call_gemini_json


def build_local_resume_intelligence(parsed: Dict, quality: Dict) -> Dict:
    skills = parsed.get("skills") or []
    name = parsed.get("name") if parsed.get("name") != "Not Found" else "Candidate"
    quality_score = quality.get("quality_score", 0)

    strengths = []
    if skills:
        strengths.append(f"Shows technical exposure in {', '.join(skills[:5])}.")
    if quality.get("signals", {}).get("has_projects"):
        strengths.append("Includes project information that can help HR judge practical ability.")
    if quality.get("signals", {}).get("has_education"):
        strengths.append("Education information is present.")
    if not strengths:
        strengths.append("No strong resume strength detected yet.")

    weaknesses = list(quality.get("reasons") or [])
    if len(skills) < 5:
        weaknesses.append("Skill evidence is limited; add more relevant technical skills only if genuinely known.")

    summary = (
        f"{name}'s resume quality score is {quality_score}%. "
        f"The resume is {'acceptable for matching' if quality.get('accepted') else 'not complete enough for matching'} based on identity, contact, sections, and readable content."
    )

    return {
        "source": "hybrid_local_ai",
        "candidateSummary": summary,
        "strengths": strengths[:5],
        "weaknesses": weaknesses[:5],
        "resumeImprovementTips": quality.get("tips", [])[:6],
        "qualityScore": quality_score,
        "accepted": quality.get("accepted"),
    }


def enhance_resume_intelligence(parsed: Dict, quality: Dict) -> Dict:
    base = build_local_resume_intelligence(parsed, quality)
    prompt = f"""
You are an AI resume reviewer for a recruitment platform.
Do not change accepted or qualityScore. Improve only wording and practical advice.
Return JSON only with keys candidateSummary, strengths, weaknesses, resumeImprovementTips.

Parsed resume: {parsed}
Quality result: {quality}
"""
    ai = call_gemini_json(prompt)
    if not ai:
        return base
    output = dict(base)
    for key in ["candidateSummary", "strengths", "weaknesses", "resumeImprovementTips"]:
        if ai.get(key):
            output[key] = ai[key]
    output["source"] = "gemini_text_enhanced"
    return output
