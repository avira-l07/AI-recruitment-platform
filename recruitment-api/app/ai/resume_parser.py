import re
from typing import Dict, List
from app.ai.skill_extractor import extract_skills

EMAIL_PATTERN = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
PHONE_PATTERN = r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3,5}\)?[\s.-]?)?\d{3,5}[\s.-]?\d{3,5}"

SECTION_HEADERS = {
    "education": ["education", "academic", "qualification", "qualifications"],
    "experience": ["experience", "work experience", "internship", "employment", "professional experience"],
    "projects": ["projects", "project", "portfolio", "practical exposure", "projects & practical exposure"],
    "certifications": ["certifications", "certification", "certificates", "training", "courses"],
}

NOISE_NAME_WORDS = {
    "resume", "curriculum", "vitae", "cv", "profile", "skills", "education", "experience",
    "project", "projects", "java", "python", "sql", "react", "developer", "engineer"
}


def clean_text(text: str) -> str:
    text = text or ""
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_lines(text: str) -> List[str]:
    return [line.strip() for line in clean_text(text).split("\n") if line.strip()]


def extract_email(text: str):
    match = re.search(EMAIL_PATTERN, text or "")
    return match.group(0) if match else None


def extract_phone(text: str):
    matches = re.findall(PHONE_PATTERN, text or "")
    for value in matches:
        digits = re.sub(r"\D", "", value)
        if 10 <= len(digits) <= 13:
            return value.strip()
    return None


def is_probable_name(line: str) -> bool:
    if not line:
        return False
    value = re.sub(r"[^A-Za-z .'-]", "", line).strip()
    words = [w for w in value.split() if w]
    if not (2 <= len(words) <= 4):
        return False
    lower_words = {w.lower() for w in words}
    if lower_words & NOISE_NAME_WORDS:
        return False
    if any(len(w) < 2 for w in words):
        return False
    # Reject all-uppercase single technical fragments like JAVA SQL after cleaning.
    return all(re.match(r"^[A-Za-z][A-Za-z.'-]*$", w) for w in words)


def extract_name(text: str, email=None, phone=None):
    for line in split_lines(text)[:12]:
        lower = line.lower()
        if email and email.lower() in lower:
            continue
        if phone and re.sub(r"\D", "", phone) in re.sub(r"\D", "", line):
            continue
        if any(header in lower for values in SECTION_HEADERS.values() for header in values):
            continue
        if is_probable_name(line):
            return re.sub(r"\s+", " ", line).strip()
    return None


def extract_section(text: str, section_names: List[str]) -> str:
    lines = split_lines(text)
    capture = False
    captured = []
    all_headers = [h for values in SECTION_HEADERS.values() for h in values]

    for line in lines:
        lower = line.lower().strip(" :-")
        if any(lower == name or lower.startswith(name + " ") or lower.startswith(name + ":") for name in section_names):
            capture = True
            continue
        if capture:
            if any(lower == header or lower.startswith(header + ":") for header in all_headers if header not in section_names):
                break
            if len(line) <= 60 and line.isupper() and len(captured) > 0:
                break
            captured.append(line)

    return " ".join(captured).strip()


def extract_education(text: str) -> str:
    edu = extract_section(text, SECTION_HEADERS["education"])
    if edu:
        return edu
    keywords = ["b.tech", "bca", "mca", "b.sc", "m.tech", "bachelor", "master", "university", "college", "institute", "computer science"]
    for line in split_lines(text):
        lower = line.lower()
        if any(k in lower for k in keywords):
            return line.strip()
    return "Not specified"


def parse_resume(text: str) -> Dict:
    text = clean_text(text)
    email = extract_email(text)
    phone = extract_phone(text)
    name = extract_name(text, email=email, phone=phone)

    projects = extract_section(text, SECTION_HEADERS["projects"]) or "Not specified"
    experience = extract_section(text, SECTION_HEADERS["experience"]) or "Not specified"
    certifications = extract_section(text, SECTION_HEADERS["certifications"]) or "Not specified"
    education = extract_education(text)

    words = re.findall(r"\b[A-Za-z][A-Za-z+#.\-]*\b", text)

    return {
        "name": name or "Not Found",
        "email": email,
        "phone": phone,
        "skills": extract_skills(text),
        "education": education,
        "experience": experience,
        "projects": projects,
        "certifications": certifications,
        "word_count": len(words),
        "raw_text_preview": text[:1200],
    }
