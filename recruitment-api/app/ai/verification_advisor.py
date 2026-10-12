import json
import logging
from typing import Dict, List, Any, Optional
from app.ai.gemini_client import call_gemini_json
from app.services.blind_screening import redact_text_pii, get_neutral_candidate_identifier

logger = logging.getLogger(__name__)


def generate_local_hybrid_reasoning(
    candidate_identifier: str,
    trust_score: float,
    outcome: str,
    company_verifications: List[Dict[str, Any]],
    internship_verifications: List[Dict[str, Any]],
    project_verifications: List[Dict[str, Any]],
    timeline_data: Dict[str, Any],
    certification_verifications: List[Dict[str, Any]],
    evidence_sources: List[Dict[str, Any]],
    fraud_flags: List[str]
) -> Dict[str, Any]:
    """
    Generates a deterministic, explainable reasoning payload when offline or Gemini is unavailable.
    """
    verified_facts = []
    supporting_evidence = []
    missing_evidence = []
    contradictions = fraud_flags.copy()
    hr_followup_questions = []
    suggested_interview_questions = []

    # 1. Company & Internship facts
    for comp in company_verifications:
        cname = comp.get("company_name", "Company")
        if comp.get("verification_status") == "Verified":
            verified_facts.append(f"Institutional existence of {cname} verified via official domain {comp.get('domain')}.")
            supporting_evidence.append(f"Official web presence confirmed for {cname} with matching technology stack.")
        elif comp.get("verification_status") == "Known Organization":
            supporting_evidence.append(f"{cname} appears in the local company reference list; employment is not verified.")
            missing_evidence.append(f"Candidate employment at {cname} requires independent confirmation.")
            hr_followup_questions.append(f"Request offer letter or supervisor reference for {cname}.")
        else:
            missing_evidence.append(f"Independent public listing for {cname} was not found (private entity / startup).")
            hr_followup_questions.append(f"Request offer letter or supervisor reference for internship at {cname}.")

    # 2. Project facts
    for proj in project_verifications:
        pname = proj.get("project_name", "Project")
        if proj.get("repository_url"):
            supporting_evidence.append(f"Candidate supplied a repository URL for '{pname}'; accessibility and ownership are not verified.")
            missing_evidence.append(f"Repository contents and activity for '{pname}' have not been checked.")
            suggested_interview_questions.append(f"Ask candidate to walk through the architecture and pull requests of project '{pname}'.")
        else:
            missing_evidence.append(f"No public repository link discovered on resume for project '{pname}'.")
            hr_followup_questions.append(f"Ask candidate to share a live demonstration or codebase for '{pname}'.")

    # 3. Certifications
    for cert in certification_verifications:
        cname = cert.get("name", "Certification")
        if cert.get("status") == "Verified":
            verified_facts.append(f"Professional credential '{cname}' issued by {cert.get('provider')} verified.")
        else:
            missing_evidence.append(f"Credential validity and ownership for '{cname}' require issuer or HR confirmation.")

    # 4. Summary & Risk
    if outcome == "strong_evidence":
        risk_explanation = "Low Risk. Candidate claims are well-supported by independent organizational domains and accessible repositories."
        summary = f"{candidate_identifier} presents a highly authentic profile with strong digital evidence across claimed experiences and technical repositories."
    elif outcome == "suspicious":
        risk_explanation = f"Elevated Risk. {len(contradictions)} anomaly/anomalies detected across links, domains, or timeline."
        summary = f"{candidate_identifier}'s profile contains potential contradictions or unreachable domains requiring detailed manual HR review."
    else:
        risk_explanation = "Moderate Risk / Standard Review. Claims correspond to private/unindexed organizations or offline projects."
        summary = f"{candidate_identifier} has submitted technical claims that require HR verification of supervisor references, credentials, and project code."

    return {
        "verified_facts": verified_facts if verified_facts else ["Basic technical profile extracted from submitted resume."],
        "supporting_evidence": supporting_evidence if supporting_evidence else ["Candidate-provided resume content."],
        "missing_evidence": missing_evidence if missing_evidence else ["No major evidence gaps identified."],
        "contradictions": contradictions,
        "hr_followup_questions": hr_followup_questions if hr_followup_questions else ["Confirm candidate start date availability."],
        "suggested_interview_questions": suggested_interview_questions if suggested_interview_questions else ["Ask candidate to describe their most challenging technical achievement."],
        "risk_explanation": risk_explanation,
        "summary": summary,
        "ai_source": "hybrid_trust_engine"
    }


def generate_grounded_verification_reasoning(
    candidate_id: int,
    candidate_name: str,
    trust_score: float,
    outcome: str,
    company_verifications: List[Dict[str, Any]],
    internship_verifications: List[Dict[str, Any]],
    project_verifications: List[Dict[str, Any]],
    timeline_data: Dict[str, Any],
    certification_verifications: List[Dict[str, Any]],
    evidence_sources: List[Dict[str, Any]],
    fraud_flags: List[str],
    is_blind_mode: bool = False
) -> Dict[str, Any]:
    """
    Generates explainable, grounded reasoning using Gemini (with fallback to local hybrid engine).
    Strictly grounded in discovered evidence records.
    """
    candidate_display = get_neutral_candidate_identifier(candidate_id) if is_blind_mode else (candidate_name or f"Candidate #C-{candidate_id}")
    
    # 1. First generate the deterministic local baseline
    local_baseline = generate_local_hybrid_reasoning(
        candidate_identifier=candidate_display,
        trust_score=trust_score,
        outcome=outcome,
        company_verifications=company_verifications,
        internship_verifications=internship_verifications,
        project_verifications=project_verifications,
        timeline_data=timeline_data,
        certification_verifications=certification_verifications,
        evidence_sources=evidence_sources,
        fraud_flags=fraud_flags
    )

    # 2. Attempt Gemini Grounded AI Call
    prompt = f"""
You are an Enterprise Trust & Experience Verification AI for HR recruitment.
Analyze the following STRUCTURED VERIFICATION EVIDENCE for {candidate_display}.
Trust Score: {trust_score}/100. Outcome: {outcome}.

EVIDENCE FACTS:
- Companies Verified: {json.dumps(company_verifications)}
- Internships / Experiences: {json.dumps(internship_verifications)}
- Projects & Repositories: {json.dumps(project_verifications)}
- Timeline Milestones: {json.dumps(timeline_data.get('events', []))}
- Certifications: {json.dumps(certification_verifications)}
- Discovered Sources: {json.dumps(evidence_sources)}
- Contradictions / Fraud Signals: {json.dumps(fraud_flags)}

CRITICAL INSTRUCTIONS:
1. ONLY reference evidence present in the data above. Do NOT invent URLs, companies, or facts. A supplied link or static reference is not proof of accessibility, employment, ownership, or certification. Respect supports_claim=false.
2. If evidence is missing for a private internship, note it constructively for HR review; never call absence of public listing "fraud".
3. Return STRICT JSON with the following keys:
   - "verified_facts": List[str]
   - "supporting_evidence": List[str]
   - "missing_evidence": List[str]
   - "contradictions": List[str]
   - "hr_followup_questions": List[str]
   - "suggested_interview_questions": List[str]
   - "risk_explanation": str
   - "summary": str
"""

    gemini_resp = call_gemini_json(prompt)
    if gemini_resp and isinstance(gemini_resp, dict) and "verified_facts" in gemini_resp and "summary" in gemini_resp:
        gemini_resp["ai_source"] = "gemini_grounded_trust"
        if is_blind_mode:
            gemini_resp["summary"] = redact_text_pii(gemini_resp.get("summary", ""), candidate_name=candidate_name, candidate_id=candidate_id)
        return gemini_resp

    return local_baseline
