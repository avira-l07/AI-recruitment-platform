from typing import List

QUESTION_BANK = {
    "React": "Explain props, state, and one situation where you used them in React.",
    "JavaScript": "Explain closures or async/await with a simple example.",
    "HTML": "How do you structure an accessible web page?",
    "CSS": "How would you make a page responsive for mobile and desktop?",
    "REST API": "How do you call an API from a frontend and handle errors?",
    "Python": "Explain how you structure a Python project and handle errors.",
    "FastAPI": "How do you create a FastAPI endpoint and validate request data?",
    "SQL": "Write a query to find duplicate records or join two tables.",
    "Machine Learning": "Explain how you train and evaluate a machine learning model.",
    "Deep Learning": "What is overfitting, and how do you reduce it in neural networks?",
    "NLP": "How would you preprocess text before using it in an NLP model?",
    "Pandas": "How do you clean missing values and group data in Pandas?",
    "Docker": "Why is Docker useful in deployment?",
    "Git": "Explain branch, commit, merge, and pull request workflow.",
}


def generate_interview_questions(role: str, matched_skills: List[str], missing_skills: List[str]) -> List[str]:
    questions = []
    for skill in matched_skills[:4]:
        questions.append(QUESTION_BANK.get(skill, f"Explain your practical experience with {skill}."))
    for skill in missing_skills[:3]:
        questions.append(f"This resume does not clearly show {skill}. Ask the candidate to explain any experience with it.")
    if not questions:
        questions.append(f"Ask the candidate to explain one project relevant to {role} from start to finish.")
    return questions[:7]
