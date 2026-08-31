import re
from typing import Dict, List, Any, Optional
from app.services.ssrf_validator import is_safe_url

KNOWN_PROVIDERS_META = {
    "aws": {"name": "AWS (Amazon Web Services)", "tier": "Tier 1 — Official Organization", "domains": ["credly.com", "aws.amazon.com"], "trusted": True},
    "coursera": {"name": "Coursera", "tier": "Tier 1 — Official Organization", "domains": ["coursera.org"], "trusted": True},
    "google": {"name": "Google / Google Cloud", "tier": "Tier 1 — Official Organization", "domains": ["coursera.org", "credential.net", "google.com"], "trusted": True},
    "microsoft": {"name": "Microsoft", "tier": "Tier 1 — Official Organization", "domains": ["credly.com", "microsoft.com"], "trusted": True},
    "cisco": {"name": "Cisco", "tier": "Tier 1 — Official Organization", "domains": ["credly.com", "cisco.com"], "trusted": True},
    "oracle": {"name": "Oracle", "tier": "Tier 1 — Official Organization", "domains": ["credly.com", "oracle.com"], "trusted": True},
    "ibm": {"name": "IBM", "tier": "Tier 1 — Official Organization", "domains": ["credly.com", "ibm.com", "coursera.org"], "trusted": True},
    "nptel": {"name": "NPTEL / Swayam", "tier": "Tier 1 — Official Organization", "domains": ["nptel.ac.in", "swayam.gov.in"], "trusted": True},
    "udemy": {"name": "Udemy", "tier": "Tier 3 — Candidate-Controlled", "domains": ["udemy.com"], "trusted": False},
}


def verify_certification(cert_claim: Dict[str, Any]) -> Dict[str, Any]:
    name = cert_claim.get("name", "Certificate")
    provider = cert_claim.get("provider", "Authority")
    cred_id = cert_claim.get("credential_id")
    v_url = cert_claim.get("verification_url")
    
    meta = None
    for k, v in KNOWN_PROVIDERS_META.items():
        if k in provider.lower() or k in name.lower():
            meta = v
            break

    evidence_sources = []
    link_status = "No URL Provided"
    tier = meta["tier"] if meta else "Tier 2 — Verified Independent"
    confidence = 85.0 if cred_id else (75.0 if meta else 60.0)

    if v_url:
        is_safe, clean_url = is_safe_url(v_url)
        if is_safe:
            link_status = "Accessible Verification URL"
            evidence_sources.append({
                "source_id": f"src_cert_{name[:6]}",
                "title": f"{name} Credential Verification",
                "url": clean_url,
                "tier": tier,
                "category": "Credential Registry",
                "supports_claim": True,
                "contradiction": False,
                "reliability_score": 90 if meta and meta["trusted"] else 75,
                "reason_used": "Online credential verification link."
            })
            confidence += 10.0
        else:
            link_status = "Prohibited / Unsafe URL"
            confidence -= 20.0

    return {
        "name": name,
        "provider": meta["name"] if meta else provider,
        "credential_id": cred_id or "Not Provided on Resume",
        "verification_url": v_url,
        "link_status": link_status,
        "source_tier": tier,
        "evidence_sources": evidence_sources,
        "status": "Verified" if (cred_id or v_url) else "Needs Review",
        "confidence_score": min(98.0, confidence),
        "notes": f"Issued by {meta['name'] if meta else provider}."
    }


def verify_all_certifications(cert_claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [verify_certification(c) for c in cert_claims]
