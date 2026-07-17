import os
import uuid
import shutil
from pathlib import Path

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024


def get_file_extension(filename: str) -> str:
    if not filename:
        return ""
    return os.path.splitext(filename)[1].lower()


def is_allowed_file(filename: str) -> bool:
    return get_file_extension(filename) in ALLOWED_EXTENSIONS


def save_upload_file(file, upload_dir: str) -> str:
    Path(upload_dir).mkdir(parents=True, exist_ok=True)
    ext = get_file_extension(file.filename)
    safe_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(upload_dir, safe_name)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return file_path
