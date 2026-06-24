import os
import uuid
import shutil

def save_upload_file(file, upload_dir: str) -> str:
    os.makedirs(upload_dir, exist_ok=True)
    ext = get_file_extension(file.filename)
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return file_path

def get_file_extension(filename: str) -> str:
    if not filename:
        return ""
    return os.path.splitext(filename)[1].lower()

def is_allowed_file(filename: str) -> bool:
    ext = get_file_extension(filename)
    return ext in [".pdf", ".docx"]