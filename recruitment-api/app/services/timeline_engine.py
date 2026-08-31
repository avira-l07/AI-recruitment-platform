import re
from datetime import datetime
from typing import Dict, List, Any, Optional

YEAR_PATTERN = re.compile(r"\b(19\d{2}|20\d{2})\b")


def extract_years(text: str) -> List[int]:
    if not text:
        return []
    matches = YEAR_PATTERN.findall(text)
    return [int(y) for y in matches]


def build_timeline_intelligence(
    experiences: List[Dict[str, Any]],
    projects: List[Dict[str, Any]],
    certifications: List[Dict[str, Any]],
    education_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Builds chronological event timeline and detects overlaps, impossible dates, and sanity alerts.
    """
    events = []
    anomalies = []
    overlaps = []
    
    # 1. Add Education Event
    if education_text:
        edu_years = extract_years(education_text)
        start_year = edu_years[0] if edu_years else 2020
        end_year = edu_years[1] if len(edu_years) > 1 else (start_year + 4)
        events.append({
            "event_id": "evt_edu_1",
            "type": "Education",
            "title": "Academic Degree / Studies",
            "subtitle": education_text[:50],
            "start_year": start_year,
            "end_year": end_year,
            "display_dates": f"{start_year} - {end_year}",
            "status": "Consistent"
        })

    # 2. Add Experience Events
    for idx, exp in enumerate(experiences):
        dates_str = exp.get("claimed_dates", "")
        exp_years = extract_years(dates_str) or extract_years(exp.get("raw_text", ""))
        start_y = exp_years[0] if exp_years else 2023
        end_y = exp_years[1] if len(exp_years) > 1 else start_y
        
        # Check impossible dates (e.g. end year < start year)
        if len(exp_years) > 1 and exp_years[1] < exp_years[0]:
            anomalies.append(f"Inverted date range detected for {exp.get('company_name')}: {dates_str}")

        events.append({
            "event_id": f"evt_exp_{idx + 1}",
            "type": "Internship" if exp.get("is_internship") else "Work Experience",
            "title": exp.get("role_title", "Role"),
            "subtitle": exp.get("company_name", "Company"),
            "start_year": start_y,
            "end_year": end_y,
            "display_dates": dates_str or f"{start_y} - {end_y}",
            "status": "Consistent" if not anomalies else "Needs Review"
        })

    # 3. Add Project Events
    for idx, proj in enumerate(projects):
        p_years = extract_years(proj.get("raw_text", ""))
        proj_year = p_years[0] if p_years else 2024
        events.append({
            "event_id": f"evt_proj_{idx + 1}",
            "type": "Project",
            "title": proj.get("project_name", "Project"),
            "subtitle": ", ".join(proj.get("technologies", [])[:3]) or "Software Build",
            "start_year": proj_year,
            "end_year": proj_year,
            "display_dates": str(proj_year),
            "status": "Verified" if proj.get("repository_url") else "Consistent"
        })

    # 4. Check for Concurrent Overlaps between experiences
    exp_events = [e for e in events if e["type"] in ["Internship", "Work Experience"]]
    for i in range(len(exp_events)):
        for j in range(i + 1, len(exp_events)):
            e1, e2 = exp_events[i], exp_events[j]
            if e1["start_year"] == e2["start_year"] and e1["end_year"] == e2["end_year"]:
                overlaps.append(f"Concurrent experiences in {e1['start_year']}: '{e1['title']}' at {e1['subtitle']} and '{e2['title']}' at {e2['subtitle']}.")

    # Sort chronological
    events.sort(key=lambda x: x["start_year"])

    timeline_score = 95.0
    if anomalies:
        timeline_score -= 40.0
    if overlaps:
        timeline_score -= 10.0

    return {
        "events": events,
        "total_events": len(events),
        "anomalies": anomalies,
        "overlaps": overlaps,
        "timeline_consistency_score": max(20.0, timeline_score),
        "status": "Consistent" if not anomalies else "Needs HR Review",
        "notes": f"Timeline analyzed with {len(events)} milestones across academic and professional history."
    }
