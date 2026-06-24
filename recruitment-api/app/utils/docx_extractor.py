import docx

def extract_text_from_docx(file_path: str) -> str:
    try:
        doc = docx.Document(file_path)
        full_text = [para.text for para in doc.paragraphs]
        return "\n".join(full_text)
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        return ""