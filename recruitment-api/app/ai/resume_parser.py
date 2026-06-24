import re
from app.ai.skill_extractor import extract_skills

def parse_resume(text: str) -> dict:
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'[\+]?[0-9][\s\-\.]?[\(]?[0-9]{3}[\)]?[\s\-\.]?[0-9]{3}[\s\-\.]?[0-9]{4}'
    
    email = None
    phone = None
    name = "Not Found"
    
    education = []
    experience = []
    projects = []
    certifications = []
    
    edu_keywords = ['b.tech', 'bca', 'mca', 'mba', 'b.sc', 'm.tech', 'computer science', 'ai', 'ml', 'artificial intelligence', 'machine learning', 'university', 'college', 'degree', 'bachelor', 'master']
    exp_keywords = ['internship', 'experience', 'developer', 'engineer', 'worked', 'company', 'organization', 'role', 'position']
    proj_keywords = ['project', 'app', 'website', 'system', 'platform', 'developed', 'built', 'created']
    cert_keywords = ['certificate', 'certification', 'course', 'training', 'completed', 'awarded']
    
    email_match = re.search(email_pattern, text)
    if email_match:
        email = email_match.group(0)
        
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        phone = phone_match.group(0)

    for line in lines:
        lower_line = line.lower()
        if name == "Not Found" and line != email and line != phone and len(line.split()) <= 4:
            if not any(k in lower_line for k in edu_keywords + exp_keywords + proj_keywords + cert_keywords):
                name = line

        if any(keyword in lower_line for keyword in edu_keywords):
            education.append(line)
        elif any(keyword in lower_line for keyword in exp_keywords):
            experience.append(line)
        elif any(keyword in lower_line for keyword in proj_keywords):
            projects.append(line)
        elif any(keyword in lower_line for keyword in cert_keywords):
            certifications.append(line)

    skills = extract_skills(text)

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "skills": skills,
        "education": education,
        "experience": experience,
        "projects": projects,
        "certifications": certifications
    }