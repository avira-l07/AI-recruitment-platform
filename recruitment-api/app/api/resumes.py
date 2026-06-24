import json
import os
import re
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from pypdf import PdfReader
from docx import Document

from app.core.database import get_db
from app.models.resume import Resume
from app.models.candidate import Candidate
from app.ai.career_advisor import get_career_suggestions

router = APIRouter(prefix="/resumes", tags=["resumes"])

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = [".pdf", ".docx"]

SKILL_KEYWORDS = [
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "C",
    "React", "Angular", "Vue", "Node.js", "Express", "Django", "Flask",
    "FastAPI", "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis",
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git", "Linux",
    "Machine Learning", "Deep Learning", "Artificial Intelligence",
    "Generative AI", "NLP", "Data Analysis", "Pandas", "NumPy",
    "TensorFlow", "PyTorch", "HTML", "CSS", "REST API", "GraphQL",
]

EDUCATION_KEYWORDS = [
    "Bachelor", "B.Tech", "B.Sc", "B.E.", "BCA", "Master", "M.Tech",
    "M.Sc", "MCA", "MBA", "PhD", "University", "College", "Institute",
]


def get_file_extension(filename: str) -> str:
    if not filename:
        return ""
    return os.path.splitext(filename)[1].lower()


def extract_text_from_pdf(file_path: str) -> str:
    try:
        reader = PdfReader(file_path)
        text = ""

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        return text
    except Exception as error:
        print(f"PDF extraction failed: {error}")
        return ""


def extract_text_from_docx(file_path: str) -> str:
    try:
        document = Document(file_path)
        paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
        return "\n".join(paragraphs)
    except Exception as error:
        print(f"DOCX extraction failed: {error}")
        return ""


def extract_text_from_file(file_path: str, extension: str) -> str:
    if extension == ".pdf":
        return extract_text_from_pdf(file_path)

    if extension == ".docx":
        return extract_text_from_docx(file_path)

    return ""


def extract_skills(text: str) -> list:
    found = []

    for skill in SKILL_KEYWORDS:
        pattern = r"\b" + re.escape(skill) + r"\b"

        if re.search(pattern, text, re.IGNORECASE):
            found.append(skill)

    return list(dict.fromkeys(found))


def extract_education(text: str) -> str:
    lines = text.split("\n")

    for line in lines:
        for keyword in EDUCATION_KEYWORDS:
            if keyword.lower() in line.lower():
                return line.strip()

    return "Not specified"


def extract_section(text: str, section_names: list) -> str:
    lines = text.split("\n")
    capture = False
    captured_lines = []

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()

        if any(
            lower == name.lower() or lower.startswith(name.lower())
            for name in section_names
        ):
            capture = True
            continue

        if capture and stripped.isupper() and len(stripped) < 40 and stripped != "":
            break

        if capture and stripped:
            captured_lines.append(stripped)

    result = " ".join(captured_lines).strip()

    return result if result else "Not specified"


def parse_resume_text(text: str) -> dict:
    return {
        "skills": extract_skills(text),
        "education": extract_education(text),
        "experience": extract_section(
            text,
            ["Experience", "Work Experience", "Projects & Practical Exposure", "Projects"]
        ),
        "certifications": extract_section(
            text,
            ["Certifications", "Certificates", "Training", "Courses"]
        ),
        "projects": extract_section(
            text,
            ["Projects", "Projects & Practical Exposure", "Portfolio"]
        ),
    }


@router.post("/upload")
def upload_resume(
    user_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(Candidate.user_id == user_id).first()

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate profile not found for this user."
        )

    extension = get_file_extension(file.filename)

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX resume files are allowed."
        )

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    safe_filename = os.path.basename(file.filename)
    file_location = os.path.join(UPLOAD_DIR, safe_filename)

    with open(file_location, "wb") as file_object:
        file_object.write(file.file.read())

    text = extract_text_from_file(file_location, extension)

    if not text.strip():
        parsed_data = {
            "skills": [],
            "education": "Could not read resume text. Please upload a text-based PDF or DOCX file.",
            "experience": "Not specified",
            "certifications": "Not specified",
            "projects": "Not specified",
        }
    else:
        parsed_data = parse_resume_text(text)

    resume = db.query(Resume).filter(Resume.candidate_id == candidate.id).first()

    if resume:
        resume.file_name = safe_filename
        resume.file_path = file_location
        resume.extracted_text = text
        resume.parsed_data = json.dumps(parsed_data)
    else:
        resume = Resume(
            candidate_id=candidate.id,
            file_name=safe_filename,
            file_path=file_location,
            extracted_text=text,
            parsed_data=json.dumps(parsed_data)
        )
        db.add(resume)

    candidate.skills = ",".join(parsed_data.get("skills", []))
    candidate.education = parsed_data.get("education", "Not specified")
    candidate.experience = parsed_data.get("experience", "Not specified")
    candidate.certifications = parsed_data.get("certifications", "Not specified")
    candidate.projects = parsed_data.get("projects", "Not specified")

    db.commit()
    db.refresh(resume)

    return {
        "message": "Resume uploaded successfully",
        "parsedResult": parsed_data
    }


@router.get("/{user_id}")
def get_resume(user_id: int, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.user_id == user_id).first()

    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    resume = db.query(Resume).filter(Resume.candidate_id == candidate.id).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    parsed_json = {}

    if resume.parsed_data:
        try:
            parsed_json = json.loads(resume.parsed_data)
        except Exception:
            parsed_json = {}

    return {
        "id": resume.id,
        "candidate_id": resume.candidate_id,
        "file_name": resume.file_name,
        "uploaded_at": resume.uploaded_at,
        "parsed_data": parsed_json
    }


@router.get("/{user_id}/career-suggestions")
def career_suggestions(user_id: int, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.user_id == user_id).first()

    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    resume = db.query(Resume).filter(Resume.candidate_id == candidate.id).first()

    if not resume:
        raise HTTPException(
            status_code=404,
            detail="Resume not found. Please upload a resume first."
        )

    parsed_json = {}

    if resume.parsed_data:
        try:
            parsed_json = json.loads(resume.parsed_data)
        except Exception:
            parsed_json = {}

    result = get_career_suggestions(parsed_json)

    return result