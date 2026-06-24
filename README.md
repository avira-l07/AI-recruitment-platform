# AI-Powered Recruitment Intelligence Platform (Backend)

## Project Overview
This is the backend API for the AI-Powered Recruitment Intelligence Platform. It handles user authentication, candidate resume parsing, job management, rule-based job matching scoring, and HR analytics.

## Tech Stack
- **Framework**: FastAPI
- **Database**: SQLite
- **ORM**: SQLAlchemy
- **Auth**: JWT Tokens
- **Parsing/Extraction**: PyPDF, python-docx
- **AI Logic**: 100% Rule-based (No external API keys required)

## Setup & Installation

1. **Set up a virtual environment**:
   - Windows: `python -m venv venv` and `venv\Scripts\activate`
   - Linux/Mac: `python3 -m venv venv` and `source venv/bin/activate`

2. **Install requirements**:
   `pip install -r requirements.txt`

3. **Run the server**:
   `uvicorn app.main:app --reload`

## Database Tables
- `users`: Core user accounts (HR/Candidate)
- `candidates`: Candidate profiles
- `resumes`: Uploaded resumes and parsed JSON data
- `jobs`: Job postings created by HR
- `match_scores`: Evaluated scores comparing candidates to jobs

## AI Modules
- **Skill Extractor**: Matches words against a comprehensive predefined list of tech skills.
- **Resume Parser**: Extracts emails and phones via Regex. Associates context clues for Education, Experience, and Certifications based on keyword heuristics.
- **Job Matcher**: Calculates a total score out of 100 based on Skill Intersection (60%), Education alignment (20%), Experience (10%), and Projects (10%).

## API Routes Overview
- `POST /auth/register` - Create user
- `POST /auth/login` - Obtain JWT Token
- `GET /candidates` - List candidates
- `GET /candidates/{id}` - Retrieve candidate details
- `POST /resumes/upload` - Upload PDF/DOCX to parse details
- `GET /resumes/{id}` - Get resume data
- `POST /jobs` - Create a job posting
- `GET /jobs` - Fetch all jobs
- `POST /matching/calculate` - Generate match score
- `GET /matching/candidate/{id}` - Get jobs for a candidate
- `GET /matching/job/{id}` - Get candidate matches for a job
- `PUT /matching/{id}/status` - Shortlist/Reject candidates
- `GET /analytics/overview` - Statistical breakdown for HR

## Testing
Browse to `http://localhost:8000/docs` to interactively view and test the API using Swagger UI.