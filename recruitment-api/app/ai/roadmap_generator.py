from typing import List


def build_learning_roadmap(role: str, missing_skills: List[str], matched_skills: List[str] = None) -> List[str]:
    matched_skills = matched_skills or []
    roadmap = []

    if not missing_skills:
        return [
            f"Build one advanced {role} project to prove your skills.",
            "Add measurable project outcomes to your resume.",
            "Practice interview questions from your strongest skills.",
        ]

    for skill in missing_skills[:5]:
        roadmap.append(f"Learn/practice {skill} with one small hands-on project or exercise.")

    if matched_skills:
        roadmap.append(f"Use your existing {', '.join(matched_skills[:3])} knowledge to build a role-specific project.")

    roadmap.append("Update your resume with project links, GitHub links, and clear bullet points.")
    return roadmap[:6]
