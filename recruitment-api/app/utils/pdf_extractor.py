from pypdf import PdfReader

def extract_text_from_pdf(file_path: str) -> str:
    try:
        reader = PdfReader(file_path)
        full_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text.append(text)
        return "\n".join(full_text)
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""