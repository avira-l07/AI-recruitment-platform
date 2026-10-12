from typing import Dict, List, Any, Optional


def calculate_trust_score(
    company_verifications: List[Dict[str, Any]],
    internship_verifications: List[Dict[str, Any]],
    project_verifications: List[Dict[str, Any]],
    timeline_data: Dict[str, Any],
    certification_verifications: List[Dict[str, Any]],
    resume_authenticity: Dict[str, Any],
    all_evidence_sources: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Computes a weighted, deterministic, explainable Trust Score (0-100).
    Never invents arbitrary numbers; every point contribution is itemized.
    """
    breakdown = []
    total_score = 0.0

    # 1. Company Legitimacy Component (Max 25 pts)
    comp_score = 0.0
    if company_verifications:
        avg_comp = sum(c.get("confidence_score", 50.0) for c in company_verifications) / len(company_verifications)
        comp_score = round((avg_comp / 100.0) * 25.0, 1)
        breakdown.append({
            "component": "Company Legitimacy",
            "points_earned": comp_score,
            "max_points": 25.0,
            "explanation": f"Average company confidence across {len(company_verifications)} claimed organization(s)."
        })
    else:
        comp_score = 15.0
        breakdown.append({
            "component": "Company Legitimacy",
            "points_earned": comp_score,
            "max_points": 25.0,
            "explanation": "No company claims listed; neutral baseline."
        })
    total_score += comp_score

    # 2. Internship & Experience Authenticity (Max 25 pts)
    intern_score = 0.0
    if internship_verifications:
        avg_intern = sum(i.get("confidence", 60.0) for i in internship_verifications) / len(internship_verifications)
        intern_score = round((avg_intern / 100.0) * 25.0, 1)
        breakdown.append({
            "component": "Internship & Experience Authenticity",
            "points_earned": intern_score,
            "max_points": 25.0,
            "explanation": f"Role, department, and duration consistency across {len(internship_verifications)} claim(s)."
        })
    else:
        intern_score = 15.0
        breakdown.append({
            "component": "Internship & Experience Authenticity",
            "points_earned": intern_score,
            "max_points": 25.0,
            "explanation": "No internship/experience claim listed; neutral baseline."
        })
    total_score += intern_score

    # 3. Project & Repository Verification (Max 25 pts)
    proj_score = 0.0
    if project_verifications:
        avg_proj = sum(p.get("confidence_score", 60.0) for p in project_verifications) / len(project_verifications)
        proj_score = round((avg_proj / 100.0) * 25.0, 1)
        breakdown.append({
            "component": "Project & Repository Verification",
            "points_earned": proj_score,
            "max_points": 25.0,
            "explanation": f"Code repositories, live demos, and tech matches for {len(project_verifications)} project(s)."
        })
    else:
        proj_score = 15.0
        breakdown.append({
            "component": "Project & Repository Verification",
            "points_earned": proj_score,
            "max_points": 25.0,
            "explanation": "No project claims listed; neutral baseline."
        })
    total_score += proj_score

    # 4. Timeline & Authenticity Consistency (Max 15 pts)
    tl_conf = timeline_data.get("timeline_consistency_score", 90.0)
    auth_conf = resume_authenticity.get("authenticity_score", 90.0)
    tl_score = round(((tl_conf + auth_conf) / 200.0) * 15.0, 1)
    breakdown.append({
        "component": "Timeline & Layout Authenticity",
        "points_earned": tl_score,
        "max_points": 15.0,
        "explanation": "Chronological coherence and resume structural integrity."
    })
    total_score += tl_score

    # 5. Certifications & Discovered Evidence Depth (Max 10 pts)
    independent_sources = [s for s in all_evidence_sources if s.get("supports_claim") is True and ("Tier 1" in s.get("tier", "") or "Tier 2" in s.get("tier", ""))]
    candidate_sources = [s for s in all_evidence_sources if "Tier 3" in s.get("tier", "")]
    
    verified_certs = [c for c in certification_verifications if c.get("status") == "Verified"]
    cert_pts = min(6.0, len(verified_certs) * 3.0)
    evidence_pts = min(4.0, len(independent_sources) * 2.0 + len(candidate_sources) * 0.5)
    cred_score = round(cert_pts + evidence_pts, 1)
    breakdown.append({
        "component": "Credentials & Evidence Diversity",
        "points_earned": cred_score,
        "max_points": 10.0,
        "explanation": f"{len(independent_sources)} independent source(s), {len(candidate_sources)} candidate-controlled source(s), {len(verified_certs)} verified cert(s)."
    })
    total_score += cred_score

    # 6. Check Contradictions & Fraud Deductions
    all_fraud_flags = []
    for c in company_verifications:
        all_fraud_flags.extend(c.get("fraud_signals", []))
    for p in project_verifications:
        all_fraud_flags.extend(p.get("fraud_signals", []))
    all_fraud_flags.extend(resume_authenticity.get("fraud_flags", []))

    if all_fraud_flags:
        deduction = min(40.0, len(all_fraud_flags) * 15.0)
        total_score -= deduction
        breakdown.append({
            "component": "Fraud & Risk Penalty",
            "points_earned": -deduction,
            "max_points": 0.0,
            "explanation": f"Risk penalty for {len(all_fraud_flags)} detected contradiction(s) or suspicious signal(s)."
        })

    final_score = max(5.0, min(99.0, round(total_score, 1)))

    # Determine Primary Outcome State
    if all_fraud_flags or final_score < 40.0:
        outcome = "suspicious"
        conf_label = "Low"
    elif final_score >= 80.0 and len(independent_sources) >= 2:
        outcome = "strong_evidence"
        conf_label = "High"
    elif len(all_evidence_sources) == 0:
        outcome = "insufficient_evidence"
        conf_label = "Low"
    else:
        outcome = "needs_review"
        conf_label = "Medium"

    return {
        "trust_score": final_score,
        "outcome": outcome,
        "confidence_label": conf_label,
        "breakdown": breakdown,
        "signals_count": len(all_evidence_sources),
        "contradictions_count": len(all_fraud_flags),
        "independent_sources_count": len(independent_sources),
        "candidate_controlled_sources_count": len(candidate_sources),
        "fraud_flags": all_fraud_flags
    }


def build_evidence_graph(
    candidate_id: int,
    candidate_name: str,
    company_verifications: List[Dict[str, Any]],
    project_verifications: List[Dict[str, Any]],
    certification_verifications: List[Dict[str, Any]],
    evidence_sources: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Builds nodes and edges representing the Candidate ↔ Company ↔ Project ↔ Evidence graph.
    """
    nodes = []
    edges = []

    # 1. Candidate Node (Center)
    cand_node_id = f"node_cand_{candidate_id}"
    nodes.append({
        "id": cand_node_id,
        "label": candidate_name or f"Candidate #C-{candidate_id}",
        "type": "candidate",
        "category": "Subject",
        "color": "#3B82F6"
    })

    # 2. Company Nodes & Edges
    for idx, c in enumerate(company_verifications):
        c_node_id = f"node_comp_{idx}"
        nodes.append({
            "id": c_node_id,
            "label": c.get("company_name", "Company"),
            "type": "company",
            "status": c.get("verification_status", "Needs Review"),
            "category": "Organization",
            "color": "#10B981" if c.get("verification_status") == "Verified" else "#F59E0B"
        })
        edges.append({
            "from": cand_node_id,
            "to": c_node_id,
            "label": "Claimed Experience / Internship",
            "type": "worked_at"
        })

    # 3. Project Nodes & Edges
    for idx, p in enumerate(project_verifications):
        p_node_id = f"node_proj_{idx}"
        nodes.append({
            "id": p_node_id,
            "label": p.get("project_name", "Project"),
            "type": "project",
            "status": p.get("repository_status", "No Repository"),
            "category": "Technical Project",
            "color": "#8B5CF6"
        })
        edges.append({
            "from": cand_node_id,
            "to": p_node_id,
            "label": "Built / Developed",
            "type": "created"
        })

    # 4. Evidence Source Nodes
    for idx, s in enumerate(evidence_sources[:6]):
        s_node_id = f"node_src_{idx}"
        nodes.append({
            "id": s_node_id,
            "label": s.get("title", "Evidence"),
            "type": "evidence",
            "tier": s.get("tier", "Tier 2"),
            "category": "Verification Source",
            "color": "#06B6D4"
        })
        edges.append({
            "from": s_node_id,
            "to": cand_node_id,
            "label": "Validates",
            "type": "evidence_for"
        })

    return {
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges)
    }
