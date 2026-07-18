import json
import os
import threading
from datetime import datetime, timezone
from uuid import uuid4
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.resume import Resume
from app.models.candidate import Candidate
from app.ai.resume_parser import parse_resume
from app.ai.resume_quality import validate_resume_quality
from app.ai.resume_intelligence import build_local_resume_intelligence
from app.ai.career_advisor import (
    rule_based_career_suggestions,
    create_resume_hash,
    generate_gemini_career_suggestions,
    merge_local_and_gemini_results
)
from app.utils.file_handler import is_allowed_file, get_file_extension, MAX_UPLOAD_SIZE_BYTES
from app.utils.pdf_extractor import extract_text_from_pdf
from app.utils.docx_extractor import extract_text_from_docx
from app.core.dependencies import get_current_user, require_roles, verify_candidate_ownership
from app.core.rate_limit import rate_limiter
from app.services.notification_service import notify_all_hr

router = APIRouter(prefix="/resumes", tags=["resumes"])
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads")).resolve()
concurrency_lock = threading.Lock()


def _extract_text(file_path: str) -> str:
    ext = get_file_extension(file_path)
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    if ext == ".docx":
        return extract_text_from_docx(file_path)
    return ""


def _candidate_by_user(db: Session, user_id: int):
    return db.query(Candidate).filter(Candidate.user_id == user_id).first()


def classify_gemini_error(error: Exception) -> tuple[str, str]:
    err_str = str(error).lower()
    if "quota" in err_str or "exhausted" in err_str or "429" in err_str:
        return "quota_exceeded", "Gemini API quota exhausted. Local analysis remains available."
    if "timeout" in err_str:
        return "timeout", "AI enhancement connection timed out. Please retry."
    if "api key" in err_str or "api_key" in err_str or "unauthorized" in err_str:
        return "invalid_api_key", "AI integration credentials error. Local analysis remains active."
    if "permission" in err_str or "403" in err_str:
        return "permission_denied", "AI service access denied. Running in local fallback mode."
    if "unavailable" in err_str or "503" in err_str:
        return "temporarily_unavailable", "Gemini service is temporarily offline. Local analysis active."
    return "failed", "AI suggestions generation failed. Please try again."


def _validate_signature(content: bytes, extension: str) -> bool:
    if extension == ".pdf":
        return content.startswith(b"%PDF")
    if extension == ".docx":
        return content.startswith(b"PK\x03\x04")
    return False


@router.post("/upload", dependencies=[Depends(rate_limiter.dependency(10, 3600, "resume_upload"))])
def upload_resume(
    user_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role == "candidate":
        user_id = current_user.id
    elif current_user.role != "hr" and user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to upload resume for this user")

    candidate = _candidate_by_user(db, user_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found for this user.")

    if not file or not file.filename:
        raise HTTPException(status_code=422, detail="Please upload a PDF or DOCX resume file.")
    if not is_allowed_file(file.filename):
        raise HTTPException(status_code=422, detail="Only PDF and DOCX resumes are allowed.")

    extension = get_file_extension(file.filename)
    content = file.file.read()
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Resume file is too large. Maximum allowed size is 5 MB.")
    if len(content) < 200:
        raise HTTPException(status_code=422, detail="Resume file is too small or empty. Upload a complete resume.")
    if not _validate_signature(content, extension):
        raise HTTPException(status_code=422, detail="The uploaded file content does not match its extension.")

    # Prevent path traversal by resolving UPLOAD_DIR as a Path and using uuid name
    upload_dir_path = Path(UPLOAD_DIR).resolve()
    upload_dir_path.mkdir(parents=True, exist_ok=True)
    
    stored_name = f"{uuid4().hex}{extension}"
    file_location = upload_dir_path / stored_name
    
    # Check that file_location is actually inside upload_dir_path to prevent path traversal
    if not os.path.abspath(file_location).startswith(os.path.abspath(upload_dir_path)):
        raise HTTPException(status_code=400, detail="Invalid file destination path.")
        
    file_location.write_bytes(content)
    file_location_str = str(file_location)

    # Local processing only
    from app.utils.activity_logger import publish_event
    publish_event(db, "resume_parsing_started", candidate.id, user_id, {
        "file_name": file.filename
    })
    db.commit()

    text = _extract_text(file_location_str)
    parsed_data = parse_resume(text)

    publish_event(db, "resume_parsed", candidate.id, user_id, {
        "file_name": file.filename
    })
    db.commit()

    quality = validate_resume_quality(parsed_data, text)

    if not quality["accepted"]:
        file_location.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422,
            detail={
                "message": "This does not look like a complete professional resume.",
                "quality": quality,
                "parsed_preview": {
                    "name": parsed_data.get("name"),
                    "email": parsed_data.get("email"),
                    "phone": parsed_data.get("phone"),
                    "skills": parsed_data.get("skills"),
                    "word_count": parsed_data.get("word_count"),
                }
            }
        )

    ai_insights = build_local_resume_intelligence(parsed_data, quality)
    parsed_data["quality"] = quality
    parsed_data["ai_insights"] = ai_insights

    local_career = rule_based_career_suggestions(parsed_data)
    new_hash = create_resume_hash(parsed_data)

    existing_cached = db.query(Resume).filter(Resume.resume_hash == new_hash, Resume.status == "completed").first()
    resume = db.query(Resume).filter(Resume.candidate_id == candidate.id).first()

    resume_fields = {
        "file_name": file.filename,
        "file_path": file_location_str,
        "extracted_text": text[:20000],
        "parsed_data": json.dumps(parsed_data),
        "resume_hash": new_hash,
        "local_analysis_json": json.dumps(local_career),
        "error_type": None,
        "safe_error_message": None,
    }

    if existing_cached:
        resume_fields.update({
            "gemini_analysis_json": existing_cached.gemini_analysis_json,
            "combined_analysis_json": existing_cached.combined_analysis_json,
            "analysis_source": existing_cached.analysis_source,
            "status": "completed",
            "gemini_model": existing_cached.gemini_model,
            "generation_completed_at": existing_cached.generation_completed_at,
            "last_success_at": existing_cached.last_success_at,
        })
    else:
        resume_fields.update({
            "gemini_analysis_json": None,
            "combined_analysis_json": None,
            "analysis_source": "local",
            "status": "local_ready",
            "gemini_model": None,
            "generation_started_at": None,
            "generation_completed_at": None,
        })

    if resume:
        # Delete old file to save space and keep tidy
        try:
            if resume.file_path and os.path.exists(resume.file_path):
                os.remove(resume.file_path)
        except Exception:
            pass
        for k, v in resume_fields.items():
            setattr(resume, k, v)
    else:
        resume = Resume(candidate_id=candidate.id, **resume_fields)
        db.add(resume)

    candidate.full_name = parsed_data.get("name") if parsed_data.get("name") != "Not Found" else candidate.full_name
    candidate.email = parsed_data.get("email") or candidate.email
    candidate.phone = parsed_data.get("phone") or candidate.phone
    candidate.skills = ",".join(parsed_data.get("skills", []))
    candidate.education = parsed_data.get("education", "Not specified")
    candidate.experience = parsed_data.get("experience", "Not specified")
    candidate.certifications = parsed_data.get("certifications", "Not specified")
    candidate.projects = parsed_data.get("projects", "Not specified")

    db.commit()
    db.refresh(resume)

    publish_event(db, "local_analysis_completed", candidate.id, user_id, {
        "quality_score": quality.get("quality_score", 0),
        "status": resume.status
    }, resume_id=resume.id)
    
    notify_all_hr(
        db,
        title="New Resume Uploaded",
        message=f"Candidate {candidate.full_name or candidate.email} has uploaded a new resume.",
        notification_type="resume_upload",
        related_entity_type="candidate",
        related_entity_id=candidate.id,
    )
    db.commit()

    return {"message": "Resume uploaded successfully", "parsedResult": parsed_data, "resumeQuality": quality, "aiInsights": ai_insights}


@router.get("/{user_id}")
def get_resume(user_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    verify_candidate_ownership(user_id, current_user)
    candidate = _candidate_by_user(db, user_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    resume = db.query(Resume).filter(Resume.candidate_id == candidate.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    try:
        parsed_json = json.loads(resume.parsed_data) if resume.parsed_data else {}
    except Exception:
        parsed_json = {}
    return {"id": resume.id, "candidate_id": resume.candidate_id, "file_name": resume.file_name, "uploaded_at": resume.uploaded_at, "parsed_data": parsed_json}


@router.get("/{user_id}/intelligence")
def resume_intelligence(user_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    verify_candidate_ownership(user_id, current_user)
    resume_data = get_resume(user_id, db, current_user)["parsed_data"]
    quality = resume_data.get("quality") or validate_resume_quality(resume_data, resume_data.get("raw_text_preview", ""))
    return build_local_resume_intelligence(resume_data, quality)


@router.get("/{user_id}/career-suggestions")
def career_suggestions(user_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    verify_candidate_ownership(user_id, current_user)
    candidate = _candidate_by_user(db, user_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    resume = db.query(Resume).filter(Resume.candidate_id == candidate.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if resume.status == "completed" and resume.combined_analysis_json:
        try:
            combined = json.loads(resume.combined_analysis_json)
            return {
                "status": "completed",
                "source": resume.analysis_source,
                "cache_status": "hit",
                "suggestions": combined.get("suggestions", []),
                "aiInsights": combined.get("aiInsights", {}),
                "error_type": None,
                "safe_error_message": None
            }
        except Exception:
            pass

    # Cache miss
    local_data = None
    if resume.local_analysis_json:
        try:
            local_data = json.loads(resume.local_analysis_json)
        except Exception:
            pass

    try:
        parsed = json.loads(resume.parsed_data) if resume.parsed_data else {}
    except Exception:
        parsed = {}

    if not local_data:
        local_data = rule_based_career_suggestions(parsed)
        resume.local_analysis_json = json.dumps(local_data)
        db.commit()

    quality = parsed.get("quality") or {}
    ai_insights = parsed.get("ai_insights") or build_local_resume_intelligence(parsed, quality)

    return {
        "status": resume.status or "local_ready",
        "source": "local",
        "cache_status": "miss",
        "suggestions": local_data.get("suggestions", []),
        "aiInsights": ai_insights,
        "error_type": resume.error_type,
        "safe_error_message": resume.safe_error_message
    }


@router.post("/{user_id}/career-suggestions/generate", dependencies=[Depends(rate_limiter.dependency(20, 3600, "gemini_generation"))])
def generate_suggestions(
    user_id: int,
    force: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    verify_candidate_ownership(user_id, current_user)
    candidate = _candidate_by_user(db, user_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    resume = db.query(Resume).filter(Resume.candidate_id == candidate.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found. Upload a resume first.")

    # 1. Check cache when force=false
    if not force and resume.status == "completed" and resume.combined_analysis_json:
        try:
            combined = json.loads(resume.combined_analysis_json)
            return {
                "status": "completed",
                "source": resume.analysis_source,
                "cache_status": "hit",
                "suggestions": combined.get("suggestions", []),
                "aiInsights": combined.get("aiInsights", {}),
                "error_type": None,
                "safe_error_message": None
            }
        except Exception:
            pass

    # 2. Concurrency Lock
    with concurrency_lock:
        db.refresh(resume)
        if resume.status == "generating" and resume.generation_started_at:
            delta = datetime.now(timezone.utc).replace(tzinfo=None) - resume.generation_started_at
            if delta.total_seconds() < 300:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="AI Career suggestions generation is already in progress."
                )

        resume.status = "generating"
        resume.generation_started_at = datetime.now(timezone.utc).replace(tzinfo=None)
        resume.last_attempt_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()

        from app.utils.activity_logger import publish_event
        publish_event(db, "gemini_generation_started", candidate.id, user_id, {
            "force": force
        }, resume_id=resume.id)
        db.commit()

    # 3. Generation logic
    try:
        try:
            parsed = json.loads(resume.parsed_data) if resume.parsed_data else {}
        except Exception:
            parsed = {}

        local_res = None
        if resume.local_analysis_json:
            try:
                local_res = json.loads(resume.local_analysis_json)
            except Exception:
                pass
        if not local_res:
            local_res = rule_based_career_suggestions(parsed)
            resume.local_analysis_json = json.dumps(local_res)
            db.commit()

        ai_res = generate_gemini_career_suggestions(parsed, local_res)
        if not ai_res:
            raise Exception("Gemini returned invalid or empty career recommendations.")

        combined_res = merge_local_and_gemini_results(local_res, ai_res)

        resume.status = "completed"
        resume.analysis_source = "hybrid"
        resume.gemini_analysis_json = json.dumps(ai_res)
        resume.combined_analysis_json = json.dumps(combined_res)
        resume.gemini_model = "gemini-2.5-flash"
        resume.generation_completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        resume.last_success_at = datetime.now(timezone.utc).replace(tzinfo=None)
        resume.error_type = None
        resume.safe_error_message = None
        db.commit()

        from app.utils.activity_logger import publish_event
        publish_event(db, "gemini_generation_completed", candidate.id, user_id, {
            "status": "completed",
            "model": "gemini-2.5-flash",
            "cache_status": "miss"
        }, resume_id=resume.id)
        db.commit()

        return {
            "status": "completed",
            "source": "hybrid",
            "cache_status": "miss",
            "suggestions": combined_res.get("suggestions", []),
            "aiInsights": combined_res.get("aiInsights", {}),
            "error_type": None,
            "safe_error_message": None
        }

    except Exception as e:
        db.refresh(resume)
        err_type, safe_msg = classify_gemini_error(e)
        resume.status = "failed"
        resume.error_type = err_type
        resume.safe_error_message = safe_msg
        db.commit()

        from app.utils.activity_logger import publish_event
        event_name = "gemini_generation_failed"
        if err_type == "quota_exceeded":
            event_name = "gemini_quota_exceeded"
        elif err_type == "timeout":
            event_name = "gemini_timeout"

        publish_event(db, event_name, candidate.id, user_id, {
            "status": "failed",
            "error_type": err_type,
            "error_message": safe_msg
        }, resume_id=resume.id)
        db.commit()

        # Fallback to local
        local_res = None
        if resume.local_analysis_json:
            try:
                local_res = json.loads(resume.local_analysis_json)
            except Exception:
                pass
        if not local_res:
            try:
                parsed = json.loads(resume.parsed_data) if resume.parsed_data else {}
            except Exception:
                parsed = {}
            local_res = rule_based_career_suggestions(parsed)

        try:
            parsed = json.loads(resume.parsed_data) if resume.parsed_data else {}
        except Exception:
            parsed = {}
        quality = parsed.get("quality") or {}
        ai_insights = parsed.get("ai_insights") or build_local_resume_intelligence(parsed, quality)

        return {
            "status": "failed",
            "source": "local",
            "cache_status": "miss",
            "suggestions": local_res.get("suggestions", []),
            "aiInsights": ai_insights,
            "error_type": err_type,
            "safe_error_message": safe_msg
        }


@router.get("/me/download")
def download_my_resume(db: Session = Depends(get_db), current_user = Depends(require_roles(["candidate"]))):
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    resume = db.query(Resume).filter(Resume.candidate_id == candidate.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume record not found")
    if not resume.file_path or not os.path.exists(resume.file_path):
        raise HTTPException(status_code=404, detail="Resume file not found on disk")
        
    upload_root = Path(os.getenv("UPLOAD_DIR", "uploads")).resolve()
    stored_path = Path(resume.file_path)
    if stored_path.is_absolute():
        resume_path = stored_path.resolve()
    else:
        resume_path = (upload_root / stored_path).resolve()
        
    try:
        resume_path.relative_to(upload_root)
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid resume file path.")
        
    ext = get_file_extension(resume.file_name).lower()
    if ext == ".pdf":
        media_type = "application/pdf"
        disposition_type = "inline"
    elif ext == ".docx":
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        disposition_type = "attachment"
    else:
        raise HTTPException(status_code=415, detail="Unsupported resume file format.")
        
    original_filename = os.path.basename(resume.file_name)
    original_filename = "".join(c for c in original_filename if c not in "\r\n\0")
    original_filename = os.path.basename(original_filename)

    headers = {
        "Cache-Control": "private, no-store",
        "X-Content-Type-Options": "nosniff"
    }
    return FileResponse(
        path=resume_path,
        media_type=media_type,
        filename=original_filename,
        content_disposition_type=disposition_type,
        headers=headers
    )


@router.get("/{user_id}/download")
def download_resume_file(user_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.role != "candidate" or current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied. HR must use the application resume route.")

    verify_candidate_ownership(user_id, current_user)
    candidate = _candidate_by_user(db, user_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    resume = db.query(Resume).filter(Resume.candidate_id == candidate.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume record not found")
    if not resume.file_path or not os.path.exists(resume.file_path):
        raise HTTPException(status_code=404, detail="Resume file not found on disk")

    # Prevent path traversal relative to upload directory
    upload_root = Path(os.getenv("UPLOAD_DIR", "uploads")).resolve()
    stored_path = Path(resume.file_path)
    if stored_path.is_absolute():
        resume_path = stored_path.resolve()
    else:
        resume_path = (upload_root / stored_path).resolve()
        
    try:
        resume_path.relative_to(upload_root)
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Invalid resume file path."
        )

    ext = get_file_extension(resume.file_name).lower()
    if ext == ".pdf":
        media_type = "application/pdf"
        disposition_type = "inline"
    elif ext == ".docx":
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        disposition_type = "attachment"
    else:
        raise HTTPException(status_code=415, detail="Unsupported resume file format.")

    original_filename = os.path.basename(resume.file_name)
    original_filename = "".join(c for c in original_filename if c not in "\r\n\0")
    original_filename = os.path.basename(original_filename)

    headers = {
        "Cache-Control": "private, no-store",
        "X-Content-Type-Options": "nosniff"
    }

    return FileResponse(
        path=resume_path,
        media_type=media_type,
        filename=original_filename,
        content_disposition_type=disposition_type,
        headers=headers
    )