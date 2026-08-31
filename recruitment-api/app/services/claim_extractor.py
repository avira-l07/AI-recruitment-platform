import re
import json
from typing import Dict, List, Any, Optional

URL_PATTERN = re.compile(r"https?://[^\s,;()'\"]+", re.IGNORECASE)
GITHUB_REPO_PATTERN = re.compile(r"https?://(?:www\.)?github\.com/([a-zA-Z0-9_\-]+)/([a-zA-Z0-9_\.\-]+)", re.IGNORECASE)
GITLAB_PATTERN = re.compile(r"https?://(?:www\.)?gitlab\.com/([a-zA-Z0-9_\-]+)/([a-zA-Z0-9_\.\-]+)", re.IGNORECASE)
FIGMA_PATTERN = re.compile(r"https?://(?:www\.)?figma\.com/(?:file|design|proto)/[^\s,;()'\"]+", re.IGNORECASE)
BEHANCE_PATTERN = re.compile(r"https?://(?:www\.)?(?:behance\.net|dribbble\.com)/[^\s,;()'\"]+", re.IGNORECASE)
STORE_PATTERN = re.compile(r"https?://(?:play\.google\.com/store/apps|apps\.apple\.com)/[^\s,;()'\"]+", re.IGNORECASE)
MONTH_NAME = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
DATE_POINT = rf"(?:{MONTH_NAME}(?:\s+\d{{2,4}})?|\d{{1,2}}/\d{{2,4}}|\d{{4}})"
DATE_END_POINT = rf"(?:{MONTH_NAME}(?:\s+\d{{2,4}})?|\d{{1,2}}/\d{{2,4}}|\d{{4}}|Present|Current|Ongoing)"
DATE_RANGE_PATTERN = re.compile(rf"\b({DATE_POINT})\s*(?:-|–|to)\s*({DATE_END_POINT})\b", re.IGNORECASE)
YEAR_ONLY_RANGE = re.compile(r"\b(20\d{2}|19\d{2})\s*(?:-|–|to)\s*(20\d{2}|19\d{2}|Present|Current)\b", re.IGNORECASE)

KNOWN_CERT_PROVIDERS = [
    "AWS", "Amazon Web Services", "Coursera", "Google Cloud", "Google", "Microsoft", "Azure",
    "Cisco", "Oracle", "IBM", "Meta", "NPTEL", "Udemy", "edX", "Stanford", "Harvard", "DeepLearning.AI", "HashiCorp", "Kubernetes", "Linux Foundation"
]

INTERNSHIP_KEYWORDS = ["intern", "internship", "trainee", "summer analyst", "fellow", "apprentice", "student researcher"]


def extract_urls(text: str) -> List[str]:
    if not text:
        return []
    matches = URL_PATTERN.findall(text)
    clean_urls = []
    for u in matches:
        u_clean = u.rstrip(".,;:)'\"")
        if u_clean and u_clean not in clean_urls:
            clean_urls.append(u_clean)
    return clean_urls


def categorize_url(url: str) -> Dict[str, Any]:
    url_lower = url.lower()
    if "github.com" in url_lower:
        gh_match = GITHUB_REPO_PATTERN.match(url)
        return {
            "url": url,
            "type": "github_repository",
            "provider": "GitHub",
            "owner": gh_match.group(1) if gh_match else None,
            "repo": gh_match.group(2).replace(".git", "") if gh_match else None,
            "tier": "Tier 3 — Candidate-Controlled"
        }
    elif "gitlab.com" in url_lower:
        gl_match = GITLAB_PATTERN.match(url)
        return {
            "url": url,
            "type": "gitlab_repository",
            "provider": "GitLab",
            "owner": gl_match.group(1) if gl_match else None,
            "repo": gl_match.group(2).replace(".git", "") if gl_match else None,
            "tier": "Tier 3 — Candidate-Controlled"
        }
    elif "figma.com" in url_lower:
        return {"url": url, "type": "figma_design", "provider": "Figma", "tier": "Tier 3 — Candidate-Controlled"}
    elif "behance.net" in url_lower or "dribbble.com" in url_lower:
        return {"url": url, "type": "design_portfolio", "provider": "Behance/Dribbble", "tier": "Tier 3 — Candidate-Controlled"}
    elif "play.google.com" in url_lower or "apps.apple.com" in url_lower:
        return {"url": url, "type": "app_store_listing", "provider": "App Store", "tier": "Tier 2 — Verified Independent"}
    elif any(d in url_lower for d in ["vercel.app", "netlify.app", "herokuapp.com", "render.com", "pages.dev", "github.io", "railway.app"]):
        return {"url": url, "type": "live_demo", "provider": "Cloud Deployment", "tier": "Tier 3 — Candidate-Controlled"}
    elif any(c in url_lower for c in ["coursera.org", "credly.com", "udemy.com", "verify", "certificate"]):
        return {"url": url, "type": "certification_verification", "provider": "Certificate Registry", "tier": "Tier 2 — Verified Independent"}
    else:
        return {"url": url, "type": "web_link", "provider": "Web", "tier": "Tier 4 — Low Confidence / Unclassified"}


def parse_experience_claims(experience_text: Optional[str]) -> List[Dict[str, Any]]:
    if not experience_text or experience_text.strip().lower() in ["not specified", "none", "n/a"]:
        return []

    lines = [l.strip() for l in experience_text.split("\n") if l.strip()]
    if len(lines) == 1 and len(experience_text) > 100:
        # Split on sentence or bullet punctuation
        lines = [seg.strip() for seg in re.split(r"[•|;]|\.\s+(?=[A-Z])", experience_text) if seg.strip()]

    claims = []
    current_entry = None
    
    for idx, line in enumerate(lines):
        # Check if line contains a company or role header
        date_match = DATE_RANGE_PATTERN.search(line) or YEAR_ONLY_RANGE.search(line)
        has_intern_keyword = any(k in line.lower() for k in INTERNSHIP_KEYWORDS)
        
        # Check if line introduces a new role / company block
        is_heading = bool(date_match) or (" at " in line.lower()) or (" - " in line and len(line) < 80) or has_intern_keyword
        
        if is_heading and (current_entry is None or len(current_entry["responsibilities"]) > 0 or date_match):
            if current_entry:
                claims.append(current_entry)
            
            # Extract company and role
            raw_title = line
            dates_str = date_match.group(0) if date_match else "Dates Not Specified"
            start_date = date_match.group(1) if date_match else None
            end_date = date_match.group(2) if (date_match and len(date_match.groups()) > 1) else None
            
            # Clean title line from dates
            title_clean = re.sub(DATE_RANGE_PATTERN, "", raw_title)
            title_clean = re.sub(YEAR_ONLY_RANGE, "", title_clean).strip(" -|,()")
            
            company = "Organization / Company"
            role = title_clean or ("Intern" if has_intern_keyword else "Software Engineer")
            
            if " at " in title_clean:
                parts = title_clean.split(" at ")
                role = parts[0].strip()
                company = parts[1].strip()
            elif " - " in title_clean:
                parts = title_clean.split(" - ")
                if len(parts) >= 2:
                    role = parts[0].strip()
                    company = parts[1].strip()
            elif has_intern_keyword:
                company_match = re.search(r"(?:at|with|for)\s+([A-Za-z0-9\s&.,]+?)(?:\s+as|\s+in|\s+during|\s*\(|$)", title_clean, re.IGNORECASE)
                if company_match:
                    company = company_match.group(1).strip()
            
            urls = extract_urls(line)
            
            current_entry = {
                "claim_id": f"exp_{len(claims) + 1}",
                "claim_type": "internship" if has_intern_keyword else "work_experience",
                "is_internship": has_intern_keyword,
                "company_name": company or "Company",
                "role_title": role or "Software Developer",
                "department": "Engineering",
                "claimed_dates": dates_str,
                "start_date": start_date,
                "end_date": end_date,
                "duration": dates_str,
                "responsibilities": [],
                "technologies": [],
                "claimed_urls": urls,
                "raw_text": line,
            }
        else:
            if current_entry is None:
                current_entry = {
                    "claim_id": "exp_1",
                    "claim_type": "work_experience",
                    "is_internship": any(k in line.lower() for k in INTERNSHIP_KEYWORDS),
                    "company_name": "Company Experience",
                    "role_title": "Software Engineer",
                    "department": "Engineering",
                    "claimed_dates": "Dates unspecified",
                    "start_date": None,
                    "end_date": None,
                    "duration": "Unspecified",
                    "responsibilities": [],
                    "technologies": [],
                    "claimed_urls": [],
                    "raw_text": "",
                }
            current_entry["responsibilities"].append(line)
            current_entry["claimed_urls"].extend(extract_urls(line))
            current_entry["raw_text"] += " " + line

    if current_entry:
        claims.append(current_entry)

    # Post-process technologies and deduplicate URLs
    for claim in claims:
        claim["claimed_urls"] = list(set(claim["claimed_urls"]))
        tech_words = ["Python", "FastAPI", "React", "Node.js", "JavaScript", "TypeScript", "Docker", "AWS", "SQL", "PostgreSQL", "MongoDB", "Java", "C++", "Kubernetes", "Redis", "GraphQL", "Machine Learning", "PyTorch", "TensorFlow"]
        found_tech = [t for t in tech_words if re.search(rf"\b{re.escape(t)}\b", claim["raw_text"], re.IGNORECASE)]
        claim["technologies"] = found_tech

    return claims


def parse_project_claims(projects_text: Optional[str], candidate_skills: Optional[str] = None) -> List[Dict[str, Any]]:
    if not projects_text or projects_text.strip().lower() in ["not specified", "none", "n/a"]:
        return []

    lines = [l.strip() for l in projects_text.split("\n") if l.strip()]
    if len(lines) == 1 and len(projects_text) > 80:
        lines = [seg.strip() for seg in re.split(r"[•|;]|\.\s+(?=[A-Z])", projects_text) if seg.strip()]

    projects = []
    current_proj = None

    for line in lines:
        urls = extract_urls(line)
        has_repo = any("github.com" in u.lower() or "gitlab.com" in u.lower() for u in urls)
        has_title_colon = ":" in line and len(line.split(":")[0]) < 45
        has_project_kw = "project" in line.lower() or "built" in line.lower() or "developed" in line.lower()

        if (has_title_colon or has_repo or len(projects) == 0) and (current_proj is None or len(current_proj["description"]) > 0):
            if current_proj:
                projects.append(current_proj)

            name = line.split(":")[0].strip(" -•*") if has_title_colon else line[:40].strip(" -•*")
            desc = line.split(":")[1].strip() if has_title_colon else line
            
            repo_url = next((u for u in urls if "github.com" in u.lower() or "gitlab.com" in u.lower()), None)
            demo_url = next((u for u in urls if u != repo_url and any(d in u.lower() for d in ["vercel", "netlify", "render", "herokuapp", "app", "demo", "io"])), None)
            
            current_proj = {
                "project_id": f"proj_{len(projects) + 1}",
                "project_name": name or f"Project {len(projects) + 1}",
                "description": desc,
                "technologies": [],
                "repository_url": repo_url,
                "demo_url": demo_url,
                "urls": urls,
                "raw_text": line,
            }
        else:
            if current_proj is None:
                current_proj = {
                    "project_id": "proj_1",
                    "project_name": "Technical Project",
                    "description": line,
                    "technologies": [],
                    "repository_url": next((u for u in urls if "github.com" in u.lower()), None),
                    "demo_url": None,
                    "urls": urls,
                    "raw_text": line,
                }
            else:
                current_proj["description"] += " " + line
                current_proj["urls"].extend(urls)
                if not current_proj["repository_url"]:
                    current_proj["repository_url"] = next((u for u in urls if "github.com" in u.lower() or "gitlab.com" in u.lower()), None)
                if not current_proj["demo_url"]:
                    current_proj["demo_url"] = next((u for u in urls if u != current_proj["repository_url"]), None)
                current_proj["raw_text"] += " " + line

    if current_proj:
        projects.append(current_proj)

    tech_words = ["Python", "FastAPI", "React", "Node.js", "JavaScript", "TypeScript", "Docker", "AWS", "SQL", "PostgreSQL", "MongoDB", "Java", "C++", "Kubernetes", "Redis", "GraphQL", "Tailwind", "Next.js", "Express", "Flask", "Django"]
    for proj in projects:
        proj["urls"] = list(set(proj["urls"]))
        proj["technologies"] = [t for t in tech_words if re.search(rf"\b{re.escape(t)}\b", proj["raw_text"], re.IGNORECASE)]

    return projects


def parse_certification_claims(cert_text: Optional[str]) -> List[Dict[str, Any]]:
    if not cert_text or cert_text.strip().lower() in ["not specified", "none", "n/a"]:
        return []

    lines = [l.strip() for l in cert_text.split("\n") if l.strip()]
    certs = []

    for idx, line in enumerate(lines):
        urls = extract_urls(line)
        provider = "Certification Authority"
        for p in KNOWN_CERT_PROVIDERS:
            if re.search(rf"\b{re.escape(p)}\b", line, re.IGNORECASE):
                provider = p
                break
        
        # Look for credential ID
        id_match = re.search(r"\b(?:ID|Credential ID|License|Certificate Number)[:\s#]*([a-zA-Z0-9_\-]+)\b", line, re.IGNORECASE)
        cert_id = id_match.group(1) if id_match else None
        
        # Look for date
        date_match = re.search(r"\b(20\d{2}|19\d{2}|[A-Za-z]+\s+20\d{2})\b", line)
        issue_date = date_match.group(0) if date_match else None

        certs.append({
            "certification_id": f"cert_{idx + 1}",
            "name": line[:60].strip(" -•*"),
            "provider": provider,
            "credential_id": cert_id,
            "verification_url": urls[0] if urls else None,
            "issue_date": issue_date,
            "raw_text": line,
        })

    return certs


def extract_all_candidate_claims(candidate: Any, resume_parsed_json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extracts all structured claims from Candidate model and Resume parsed data.
    """
    exp_text = getattr(candidate, "experience", None) or (resume_parsed_json.get("experience") if resume_parsed_json else "")
    proj_text = getattr(candidate, "projects", None) or (resume_parsed_json.get("projects") if resume_parsed_json else "")
    cert_text = getattr(candidate, "certifications", None) or (resume_parsed_json.get("certifications") if resume_parsed_json else "")
    edu_text = getattr(candidate, "education", None) or (resume_parsed_json.get("education") if resume_parsed_json else "")
    skills_text = getattr(candidate, "skills", None) or (resume_parsed_json.get("skills") if resume_parsed_json else "")

    experiences = parse_experience_claims(exp_text)
    projects = parse_project_claims(proj_text, candidate_skills=str(skills_text))
    certifications = parse_certification_claims(cert_text)

    # Collect all URLs referenced across the candidate profile
    all_raw_text = f"{exp_text} {proj_text} {cert_text} {edu_text} {skills_text}"
    all_urls = extract_urls(all_raw_text)
    categorized_urls = [categorize_url(u) for u in all_urls]

    return {
        "candidate_id": getattr(candidate, "id", None),
        "total_claims": len(experiences) + len(projects) + len(certifications),
        "experiences": experiences,
        "projects": projects,
        "certifications": certifications,
        "education": edu_text,
        "skills": skills_text,
        "discovered_urls": categorized_urls,
    }
