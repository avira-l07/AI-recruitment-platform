import re
from typing import Any, Optional
from fastapi import Request

# Neutral identifier format
def get_neutral_candidate_identifier(candidate_id: int | None) -> str:
    if candidate_id is not None:
        return f"Candidate #C-{candidate_id}"
    return "Candidate #C-Unknown"


def is_blind_mode_requested(
    request: Optional[Request] = None,
    blind_mode_query: Optional[bool] = None,
    user: Optional[Any] = None,
) -> bool:
    # Explicit query parameter takes precedence
    if blind_mode_query is True:
        return True
    if blind_mode_query is False and request is None:
        return False
    # Check X-Blind-Screening header if request is available
    if request is not None:
        header_val = request.headers.get("X-Blind-Screening", "").strip().lower()
        if header_val in ("true", "1", "yes", "on"):
            return True
        # Check query param from request directly as fallback
        query_val = request.query_params.get("blind_mode", "").strip().lower()
        if query_val in ("true", "1", "yes", "on"):
            return True
    return False


# Regex patterns for PII detection and redaction
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{10}\b|\b\d{5}[-\s]\d{5}\b")
YEAR_PATTERN = re.compile(r"\b(19\d{2}|20\d{2})\b")
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+|github\.com/\S+|linkedin\.com/\S+", re.IGNORECASE)

# University / College indicators
INSTITUTION_KEYWORDS = [
    r"university", r"college", r"institute", r"school", r"academy", r"campus",
    r"polytechnic", r"faculty", r"department", r"iit", r"nit", r"bits", r"mit", r"stanford",
    r"harvard", r"berkeley", r"oxford", r"cambridge"
]
INSTITUTION_PATTERN = re.compile(r"\b(?:" + "|".join(INSTITUTION_KEYWORDS) + r")\b.*?(?=[,\n\.]|$)", re.IGNORECASE)


def sanitize_education(education_text: Optional[str]) -> Optional[str]:
    if not education_text or not str(education_text).strip():
        return education_text
    
    # Split items by comma, semicolon, or newline
    chunks = re.split(r"[,;\n|]+", str(education_text))
    cleaned_chunks = []
    
    for chunk in chunks:
        c = chunk.strip()
        if not c:
            continue
        # Check if chunk contains an institution keyword
        has_institution = any(re.search(rf"\b{kw}\b", c, re.IGNORECASE) for kw in INSTITUTION_KEYWORDS)
        if has_institution:
            # If chunk has "at Institution" or "from Institution", strip only the institution portion
            c = re.sub(r"(?:at|from)\s+.*$", "", c, flags=re.IGNORECASE).strip()
            if not c or any(re.search(rf"\b{kw}\b", c, re.IGNORECASE) for kw in INSTITUTION_KEYWORDS):
                continue
        # Strip years and graduation markers
        c = re.sub(r"\(?\s*(?:19\d{2}|20\d{2})\s*(?:-|–|to)?\s*(?:19\d{2}|20\d{2})?\s*\)?", "", c)
        c = re.sub(r"\b(?:Class of|Graduated|Batch of|Passing Year|Graduation Year:?)\s*(?:19\d{2}|20\d{2})?\b", "", c, flags=re.IGNORECASE)
        c = c.strip().strip("-").strip()
        if len(c) > 1:
            cleaned_chunks.append(c)
            
    if cleaned_chunks:
        return " | ".join(cleaned_chunks)
    return "Degree in Technical Field"


def sanitize_experience(experience_text: Optional[str]) -> Optional[str]:
    if not experience_text or not str(experience_text).strip():
        return experience_text
    
    text = str(experience_text)
    # Remove specific company indicators while preserving roles, responsibilities and duration
    text = re.sub(r"(?:at|for|with)\s+[A-Z][A-Za-z0-9\s\.,&]+?(?:Pvt\.?\s*Ltd\.?|Ltd\.?|Inc\.?|LLC|Corp\.?|Technologies|Solutions|Services|Systems)\b", "at Organization", text)
    # Remove email or contact info if accidentally embedded
    text = EMAIL_PATTERN.sub("[Concealed]", text)
    text = PHONE_PATTERN.sub("[Concealed]", text)
    return text.strip()


def redact_text_pii(
    text: Optional[str],
    candidate_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    candidate_id: Optional[int] = None,
) -> Optional[str]:
    if not text or not isinstance(text, str):
        return text
    
    neutral_id = get_neutral_candidate_identifier(candidate_id)
    sanitized = text
    
    # Redact full name if provided
    if candidate_name and candidate_name.strip() and candidate_name.strip().lower() not in ("unknown candidate", "unknown", "none"):
        name_clean = candidate_name.strip()
        sanitized = re.sub(re.escape(name_clean), neutral_id, sanitized, flags=re.IGNORECASE)
        # Also redact first/last name parts if they are distinct tokens >= 3 chars
        parts = [p for p in name_clean.split() if len(p) >= 3 and p.lower() not in ("mr", "ms", "mrs", "dr", "the", "and")]
        for p in parts:
            sanitized = re.sub(rf"\b{re.escape(p)}\b", neutral_id, sanitized, flags=re.IGNORECASE)
            
    # Redact email
    if email and email.strip() and "@" in email:
        sanitized = re.sub(re.escape(email.strip()), "[Concealed]", sanitized, flags=re.IGNORECASE)
    sanitized = EMAIL_PATTERN.sub("[Concealed]", sanitized)
    
    # Redact phone
    if phone and phone.strip():
        sanitized = re.sub(re.escape(phone.strip()), "[Concealed]", sanitized)
    sanitized = PHONE_PATTERN.sub("[Concealed]", sanitized)
    
    # Redact personal URLs
    sanitized = URL_PATTERN.sub("[Link Concealed]", sanitized)
    
    return sanitized


def sanitize_list_or_text(val: Any, candidate_name: Optional[str] = None, candidate_id: Optional[int] = None) -> Any:
    if isinstance(val, str):
        return redact_text_pii(val, candidate_name=candidate_name, candidate_id=candidate_id)
    if isinstance(val, list):
        return [sanitize_list_or_text(item, candidate_name=candidate_name, candidate_id=candidate_id) for item in val]
    if isinstance(val, dict):
        return {k: sanitize_list_or_text(v, candidate_name=candidate_name, candidate_id=candidate_id) for k, v in val.items()}
    return val


def build_blind_candidate_representation(
    payload: dict,
    candidate_id: Optional[int] = None,
    candidate_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> dict:
    """
    Constructs an explicit, server-side allowlisted candidate representation.
    Only permitted professional evaluation fields are returned.
    All PII is strictly excluded or anonymized.
    """
    cid = candidate_id or payload.get("candidate_id") or payload.get("id")
    cname = candidate_name or payload.get("name") or payload.get("full_name")
    cemail = email or payload.get("email")
    cphone = phone or payload.get("phone")
    neutral_id = get_neutral_candidate_identifier(cid)
    
    # Explicit Allowlist Construction
    blind_rep = {
        "id": payload.get("id") or cid,
        "application_id": payload.get("application_id") or payload.get("id"),
        "match_id": payload.get("match_id"),
        "candidate_id": cid,
        "user_id": None,  # Suppress internal user_id
        "display_id": neutral_id,
        "name": neutral_id,
        "full_name": neutral_id,
        "candidate_name": neutral_id,
        "email": None,
        "phone": None,
        "is_blind_mode": True,
        
        # Professional Qualifications
        "skills": payload.get("skills") or [],
        "education": sanitize_education(payload.get("education")),
        "experience": sanitize_experience(payload.get("experience")),
        "projects": sanitize_list_or_text(payload.get("projects"), candidate_name=cname, candidate_id=cid),
        "certifications": payload.get("certifications"),
        
        # Job & Match Information
        "job_id": payload.get("job_id"),
        "matchedJob": payload.get("matchedJob") or payload.get("jobTitle") or "Role Evaluation",
        "jobTitle": payload.get("jobTitle") or payload.get("matchedJob") or "Role Evaluation",
        "score": payload.get("score") if payload.get("score") is not None else payload.get("match_score", 0),
        "match_score": payload.get("match_score") if payload.get("match_score") is not None else payload.get("score", 0),
        "status": payload.get("status") or "Applied",
        "matchedSkills": payload.get("matchedSkills") or payload.get("matched_skills") or [],
        "missingSkills": payload.get("missingSkills") or payload.get("missing_skills") or [],
        "fitLabel": payload.get("fitLabel") or payload.get("fit_label"),
        "confidenceScore": payload.get("confidenceScore") or payload.get("confidence_score"),
        "confidenceLabel": payload.get("confidenceLabel") or payload.get("confidence_label"),
        "aiSource": payload.get("aiSource") or payload.get("ai_source") or "local_ai",
        "fallbackActive": payload.get("fallbackActive") or payload.get("fallback_active") or False,
        "fallbackReason": payload.get("fallbackReason") or payload.get("fallback_reason"),
        
        # Sanitized AI / Analysis Fields
        "explanation": redact_text_pii(payload.get("explanation"), candidate_name=cname, email=cemail, phone=cphone, candidate_id=cid),
        "hrSummary": redact_text_pii(payload.get("hrSummary") or payload.get("hr_summary"), candidate_name=cname, email=cemail, phone=cphone, candidate_id=cid),
        "aiSemanticAnalysis": redact_text_pii(payload.get("aiSemanticAnalysis") or payload.get("ai_semantic_analysis"), candidate_name=cname, email=cemail, phone=cphone, candidate_id=cid),
        "roadmap": sanitize_list_or_text(payload.get("roadmap") or [], candidate_name=cname, candidate_id=cid),
        "interviewQuestions": sanitize_list_or_text(payload.get("interviewQuestions") or payload.get("interview_questions") or [], candidate_name=cname, candidate_id=cid),
        "riskFlags": sanitize_list_or_text(payload.get("riskFlags") or payload.get("risk_flags") or [], candidate_name=cname, candidate_id=cid),
        "recommendation": redact_text_pii(payload.get("recommendation"), candidate_name=cname, email=cemail, phone=cphone, candidate_id=cid),
        "semanticMatches": payload.get("semanticMatches") or payload.get("semantic_matches") or [],
        
        # Timestamps & Metadata
        "created_at": payload.get("created_at"),
        "updated_at": payload.get("updated_at"),
        "applied_at": payload.get("applied_at") or payload.get("created_at"),
        "resume_available": bool(payload.get("resume_available")),
        "raw_resume_restricted": True,
        "prescreening_score": payload.get("prescreening_score"),
        "prescreening_label": payload.get("prescreening_label"),
        "has_prescreening": payload.get("has_prescreening", False),
    }
    return blind_rep


def sanitize_parsed_resume(parsed_data: dict, candidate_id: Optional[int] = None) -> dict:
    """
    Sanitizes parsed resume structure for blind review.
    """
    neutral_id = get_neutral_candidate_identifier(candidate_id)
    original_name = parsed_data.get("name")
    original_email = parsed_data.get("email")
    original_phone = parsed_data.get("phone")
    
    sanitized = {
        "name": neutral_id,
        "email": None,
        "phone": None,
        "location": None,
        "links": [],
        "skills": parsed_data.get("skills") or [],
        "education": sanitize_education(parsed_data.get("education")),
        "experience": sanitize_experience(parsed_data.get("experience")),
        "projects": sanitize_list_or_text(parsed_data.get("projects"), candidate_name=original_name, candidate_id=candidate_id),
        "certifications": parsed_data.get("certifications"),
        "quality": parsed_data.get("quality") or {},
        "ai_insights": sanitize_list_or_text(parsed_data.get("ai_insights") or {}, candidate_name=original_name, candidate_id=candidate_id),
        "raw_text_preview": redact_text_pii(
            parsed_data.get("raw_text_preview") or "",
            candidate_name=original_name,
            email=original_email,
            phone=original_phone,
            candidate_id=candidate_id,
        ),
        "is_blind_mode": True,
    }
    return sanitized
