SKILLS_LIST = [
    "Python", "Java", "C++", "C", "React", "JavaScript",
    "HTML", "CSS", "SQL", "MongoDB", "PostgreSQL", "FastAPI",
    "Flask", "Django", "Machine Learning", "Deep Learning",
    "NLP", "Generative AI", "Data Analysis", "Git", "GitHub",
    "Docker", "REST API", "Node.js", "Express.js",
    "Tailwind CSS", "Bootstrap", "Pandas", "NumPy",
    "Scikit-learn", "TypeScript", "AWS", "Linux"
]

def extract_skills(text: str) -> list:
    if not text:
        return []
    text_lower = text.lower()
    matched_skills = []
    
    for skill in SKILLS_LIST:
        if skill.lower() in text_lower:
            matched_skills.append(skill)
            
    return list(set(matched_skills))