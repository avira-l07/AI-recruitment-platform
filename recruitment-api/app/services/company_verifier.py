import re
import urllib.parse
from typing import Dict, List, Any, Optional
from app.services.ssrf_validator import is_safe_url

KNOWN_VERIFIED_COMPANIES = {
    "google": {"name": "Google", "domain": "google.com", "tier": "Tier 1 — Official Organization", "tech": ["Python", "C++", "Java", "Go", "Kubernetes", "TensorFlow"]},
    "microsoft": {"name": "Microsoft", "domain": "microsoft.com", "tier": "Tier 1 — Official Organization", "tech": ["C#", ".NET", "Azure", "TypeScript", "Python"]},
    "amazon": {"name": "Amazon", "domain": "amazon.com", "tier": "Tier 1 — Official Organization", "tech": ["Java", "AWS", "Python", "React", "Docker"]},
    "meta": {"name": "Meta", "domain": "meta.com", "tier": "Tier 1 — Official Organization", "tech": ["React", "PyTorch", "Python", "GraphQL", "C++"]},
    "apple": {"name": "Apple", "domain": "apple.com", "tier": "Tier 1 — Official Organization", "tech": ["Swift", "Objective-C", "Python", "C++"]},
    "ibm": {"name": "IBM", "domain": "ibm.com", "tier": "Tier 1 — Official Organization", "tech": ["Java", "Python", "Cloud", "Kubernetes", "AI"]},
    "infosys": {"name": "Infosys", "domain": "infosys.com", "tier": "Tier 1 — Official Organization", "tech": ["Java", "Spring", "Python", "React", "SQL"]},
    "tcs": {"name": "Tata Consultancy Services", "domain": "tcs.com", "tier": "Tier 1 — Official Organization", "tech": ["Java", "SQL", "Python", "Cloud"]},
    "accenture": {"name": "Accenture", "domain": "accenture.com", "tier": "Tier 1 — Official Organization", "tech": ["Java", "Salesforce", "Cloud", "SAP"]},
    "wipro": {"name": "Wipro", "domain": "wipro.com", "tier": "Tier 1 — Official Organization", "tech": ["Java", "Python", "SQL", "Cloud"]},
    "cisco": {"name": "Cisco", "domain": "cisco.com", "tier": "Tier 1 — Official Organization", "tech": ["Networking", "Python", "C++", "Docker"]},
    "oracle": {"name": "Oracle", "domain": "oracle.com", "tier": "Tier 1 — Official Organization", "tech": ["Java", "SQL", "Oracle DB", "Cloud"]},
    "stripe": {"name": "Stripe", "domain": "stripe.com", "tier": "Tier 1 — Official Organization", "tech": ["Ruby", "Python", "Go", "React", "PostgreSQL"]},
    "netflix": {"name": "Netflix", "domain": "netflix.com", "tier": "Tier 1 — Official Organization", "tech": ["Java", "Node.js", "React", "AWS", "Python"]},
    "uber": {"name": "Uber", "domain": "uber.com", "tier": "Tier 1 — Official Organization", "tech": ["Go", "Java", "Python", "Kafka", "React"]},
}

SUSPICIOUS_DOMAINS_OR_PATTERNS = [
    "fakecert", "bogusintern", "cert-maker", "free-certificate-generator", "instant-internship",
    "diploma-mill", "fakecompany", "throwaway", "tempmail", "guerrillamail"
]


def normalize_company_name(name: str) -> str:
    if not name:
        return ""
    clean = re.sub(r"(?:Pvt\.?\s*Ltd\.?|Ltd\.?|Inc\.?|LLC|Corp\.?|Technologies|Solutions|Services|Systems)\b", "", name, flags=re.IGNORECASE)
    return clean.strip().lower()


def verify_company_claim(company_name: str, claimed_urls: List[str] = None, claimed_tech: List[str] = None) -> Dict[str, Any]:
    """
    Performs multi-signal company legitimacy verification.
    """
    claimed_urls = claimed_urls or []
    claimed_tech = claimed_tech or []
    c_clean = normalize_company_name(company_name)
    
    # 1. Check known verified company registry
    matching_known = None
    for key, data in KNOWN_VERIFIED_COMPANIES.items():
        if c_clean and c_clean == normalize_company_name(key):
            matching_known = data
            break

    evidence_sources = []
    fraud_signals = []
    
    # Check for suspicious keywords in company name or claimed URLs
    for susp in SUSPICIOUS_DOMAINS_OR_PATTERNS:
        if susp in company_name.lower():
            fraud_signals.append(f"Company name contains suspicious pattern: '{susp}'")
        for u in claimed_urls:
            if susp in u.lower():
                fraud_signals.append(f"Claimed URL matches known certificate/internship generator pattern: '{u}'")

    if matching_known:
        domain = matching_known["domain"]
        evidence_sources.append({
            "source_id": f"src_comp_{c_clean[:8]}",
            "title": f"{matching_known['name']} Official Web Presence",
            "url": f"https://www.{domain}",
            "tier": matching_known["tier"],
            "category": "Official Organization",
            "supports_claim": False,
            "contradiction": False,
            "reliability_score": 98,
            "reason_used": "Static company reference; candidate employment and live website validity have not been checked."
        })
        
        # Check technology alignment
        aligned_tech = [t for t in claimed_tech if any(t.lower() == kt.lower() for kt in matching_known["tech"])]
        tech_match_status = "High Alignment" if len(aligned_tech) >= 1 else "Standard Alignment"
        
        return {
            "company_name": matching_known["name"],
            "verification_status": "High Risk" if fraud_signals else "Known Organization",
            "domain": domain,
            "official_website": f"https://www.{domain}",
            "ssl_valid": None,
            "business_presence": "Strong Public Footprint",
            "company_identity_consistency": "Strong",
            "technology_alignment": tech_match_status,
            "aligned_technologies": aligned_tech,
            "fraud_signals": fraud_signals,
            "evidence_sources": evidence_sources,
            "confidence_score": 94.0 if not fraud_signals else 40.0,
            "notes": "Company is in the local reference list; candidate employment requires HR review."
        }

    # 2. Company not in predefined list: Analyze domain signals & URLs provided
    company_domain = None
    for u in claimed_urls:
        safe, clean_u = is_safe_url(u)
        if safe and not any(host in clean_u for host in ["github.com", "gitlab.com", "linkedin.com", "medium.com"]):
            parsed = urllib.parse.urlparse(clean_u)
            if parsed.hostname:
                company_domain = parsed.hostname
                evidence_sources.append({
                    "source_id": f"src_url_{parsed.hostname[:8]}",
                    "title": f"{company_name} Referenced Domain ({parsed.hostname})",
                    "url": clean_u,
                    "tier": "Tier 3 — Candidate-Controlled",
                    "category": "Web Domain",
                    "supports_claim": False,
                    "contradiction": False,
                    "reliability_score": 75,
                    "reason_used": "Candidate-supplied domain; association with the organization has not been checked."
                })
                break

    if fraud_signals:
        return {
            "company_name": company_name,
            "verification_status": "High Risk",
            "domain": company_domain or "None",
            "official_website": None,
            "ssl_valid": False,
            "business_presence": "Suspicious / Unverified",
            "company_identity_consistency": "Contradictory",
            "technology_alignment": "Unverified",
            "aligned_technologies": [],
            "fraud_signals": fraud_signals,
            "evidence_sources": evidence_sources,
            "confidence_score": 15.0,
            "notes": f"Potential risk signals detected: {'; '.join(fraud_signals)}"
        }

    if company_domain:
        return {
            "company_name": company_name,
            "verification_status": "Needs Review",
            "domain": company_domain,
            "official_website": f"https://{company_domain}",
            "ssl_valid": None,
            "business_presence": "Independent Domain Found",
            "company_identity_consistency": "Moderate",
            "technology_alignment": "Pending Review",
            "aligned_technologies": claimed_tech,
            "fraud_signals": [],
            "evidence_sources": evidence_sources,
            "confidence_score": 72.0,
            "notes": "Domain located. HR should verify candidate employment relationship."
        }

    # 3. Unindexed / Private Company
    return {
        "company_name": company_name,
        "verification_status": "Needs Review",
        "domain": "Not Publicly Discoverable",
        "official_website": None,
        "ssl_valid": None,
        "business_presence": "Private / Unindexed Organization",
        "company_identity_consistency": "Insufficient Public Evidence",
        "technology_alignment": "Unverified",
        "aligned_technologies": claimed_tech,
        "fraud_signals": [],
        "evidence_sources": evidence_sources,
        "confidence_score": 55.0,
        "notes": "Private entity or startup without major public web footprint. Absence of public listing is NOT evidence of fraud."
    }


def verify_internship_authenticity(experience_claim: Dict[str, Any], company_verification: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates internship claim against company evidence and consistency signals.
    """
    role = experience_claim.get("role_title", "Intern")
    dates = experience_claim.get("claimed_dates", "")
    tech = experience_claim.get("technologies", [])
    is_intern = experience_claim.get("is_internship", False)
    
    comp_status = company_verification.get("verification_status", "Needs Review")
    
    # Check duration realism
    duration_realistic = True
    if any(k in dates.lower() for k in ["10 years", "8 years", "7 years"]) and is_intern:
        duration_realistic = False

    evidence_found = comp_status in ["Verified", "Needs Review"] and duration_realistic
    
    if comp_status in {"Verified", "Known Organization"}:
        alignment = "Strong"
        status = "Needs HR Review"
        notes = f"Claimed role '{role}' is consistent with {company_verification.get('company_name')} technical hiring profile."
        confidence = 60.0
    elif comp_status == "High Risk":
        alignment = "Contradictory"
        status = "High Risk"
        notes = "Company verification failed with fraud indicators."
        confidence = 20.0
    else:
        alignment = "Moderate"
        status = "Needs HR Review"
        notes = "Internship program details require direct HR review (e.g. checking offer letter or supervisor reference)."
        confidence = 65.0

    return {
        "claimed_role": role,
        "is_internship": is_intern,
        "claimed_dates": dates,
        "program_evidence": "Found / Consistent" if evidence_found else "Private / Unindexed",
        "duration_realistic": duration_realistic,
        "role_consistency": alignment,
        "technology_consistency": "Consistent" if tech else "Not Specified",
        "status": status,
        "confidence": confidence,
        "notes": notes
    }
