# AI Recruitment Intelligence Platform - Professional Hybrid AI Upgrade

A full-stack recruitment platform using FastAPI and React/Vite.

This upgraded version uses a professional hybrid AI approach:

```text
Rule-based scoring + AI semantic analysis + AI explanation + AI roadmap + AI HR summary
```

## What AI Does

- Reads and understands resume content
- Reviews resume quality
- Explains candidate-job fit
- Gives HR summary
- Gives candidate roadmap
- Generates interview questions
- Analyzes job descriptions
- Provides risk flags and HR recommendations

## What Backend Controls

- Final match score
- Matched skills
- Missing skills
- Resume acceptance/rejection
- Strong Fit / Good Fit / Explore label
- Guardrails against fake AI scores

This prevents wrong results like:

```text
Only React matched -> 88% Strong Fit
```

## Backend Setup

```powershell
cd recruitment-api
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000/docs
```

## Frontend Setup

```powershell
cd recruitment-client
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

## Local Environment

Create:

```text
recruitment-client/.env
```

Add:

```env
VITE_API_URL=http://localhost:8000
```

Backend optional `.env`:

```env
SECRET_KEY=change_this_secret
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
GEMINI_API_KEY=
```

## Important Resume Rule

Fake/incomplete resumes are rejected.

Example rejected resume:

```text
Java SQL
```

Reason: It has no name, no contact, no education, no project/experience/certification, and too little readable text.

## Deployment Notes

Backend Render:

```text
Root Directory: recruitment-api
Build Command: pip install -r requirements.txt
Start Command: python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Frontend Render:

```text
Root Directory: recruitment-client
Build Command: npm install && npm run build
Publish Directory: dist
```

Frontend Render env:

```env
VITE_API_URL=https://your-backend-url.onrender.com
```
