import re
import urllib.parse
from typing import Dict, List, Any, Optional
from app.services.ssrf_validator import is_safe_url


def verify_project_claim(project_claim: Dict[str, Any]) -> Dict[str, Any]:
    """
    Performs comprehensive project and repository verification with SSRF protection.
    """
    name = project_claim.get("project_name", "Project")
    desc = project_claim.get("description", "")
    claimed_tech = project_claim.get("technologies", [])
    repo_url = project_claim.get("repository_url")
    demo_url = project_claim.get("demo_url")
    urls = project_claim.get("urls", [])

    repo_status = "No Repository Listed"
    demo_status = "No Live Demo Listed"
    link_health = "Not Checked"
    source_tier = "Tier 4 — Low Confidence"
    evidence_sources = []
    fraud_signals = []
    
    # 1. Inspect Repository URL
    if repo_url:
        is_safe, clean_repo = is_safe_url(repo_url)
        if not is_safe:
            repo_status = "Prohibited / Unsafe URL"
            fraud_signals.append(f"Repository URL failed SSRF safety validation: {repo_url}")
        else:
            repo_status = "Repository Link Supplied — Not Verified"
            source_tier = "Tier 3 — Candidate-Controlled"
            evidence_sources.append({
                "source_id": f"src_repo_{name[:6]}",
                "title": f"{name} Git Repository",
                "url": clean_repo,
                "tier": "Tier 3 — Candidate-Controlled",
                "category": "Source Code Repository",
                "supports_claim": False,
                "contradiction": False,
                "reliability_score": 40,
                "reason_used": "Supplied URL; repository contents and ownership have not been checked."
            })
    
    # 2. Inspect Live Demo URL
    if demo_url:
        is_safe, clean_demo = is_safe_url(demo_url)
        if is_safe:
            demo_status = "Demo Link Supplied — Not Verified"
            evidence_sources.append({
                "source_id": f"src_demo_{name[:6]}",
                "title": f"{name} Live Deployment / Demo",
                "url": clean_demo,
                "tier": "Tier 3 — Candidate-Controlled",
                "category": "Cloud Deployment",
                "supports_claim": False,
                "contradiction": False,
                "reliability_score": 40,
                "reason_used": "Supplied URL; demo accessibility has not been checked."
            })
        else:
            demo_status = "Prohibited / Unsafe URL"
            fraud_signals.append("Demo URL failed safety validation.")

    # 3. Technology Match Analysis
    detected_tech = []
    tech_keywords = ["Python", "FastAPI", "React", "Node.js", "PostgreSQL", "Docker", "AWS", "MongoDB", "SQL", "JavaScript", "TypeScript", "Tailwind", "Next.js", "Express", "Flask", "Django", "PyTorch", "TensorFlow"]
    for t in tech_keywords:
        if re.search(rf"\b{re.escape(t)}\b", f"{name} {desc}", re.IGNORECASE):
            detected_tech.append(t)

    tech_match = "High Match" if (set(claimed_tech) & set(detected_tech) or not claimed_tech) else "Medium Match"
    
    # 4. Project Ownership & Description Match Analysis
    desc_quality = "Comprehensive" if len(desc) > 60 else "Brief / Summary"
    commit_activity = "Not Checked"
    
    confidence = 55.0 if evidence_sources else 40.0
    if fraud_signals:
        confidence = 25.0

    return {
        "project_name": name,
        "description": desc,
        "claimed_technologies": claimed_tech,
        "detected_technologies": detected_tech,
        "repository_url": clean_repo if repo_url and repo_status.startswith("Repository Link") else None,
        "repository_status": repo_status,
        "demo_url": clean_demo if demo_url and demo_status.startswith("Demo Link") else None,
        "demo_status": demo_status,
        "technology_match": tech_match,
        "description_match": "High Match" if len(desc) > 30 else "Moderate Match",
        "readme_quality": "Not Checked",
        "commit_activity": commit_activity,
        "source_tier": source_tier,
        "evidence_sources": evidence_sources,
        "fraud_signals": fraud_signals,
        "confidence_score": confidence,
        "notes": "Supplied claims and links require manual review; repository, commits, and demo content have not been fetched."
    }


def verify_all_projects(project_claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [verify_project_claim(p) for p in project_claims]
