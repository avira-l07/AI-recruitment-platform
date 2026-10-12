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
python -m alembic upgrade head
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
APP_ENV=development
SECRET_KEY=
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
GEMINI_API_KEY=
```

Copy `recruitment-api/.env.example` to `.env`. Set a persistent random
`SECRET_KEY` of at least 32 characters; a blank development key creates a new
secret on each process start and invalidates previous sessions. Production
(`APP_ENV=production`) requires a configured key and defaults to migrations
instead of automatic schema creation. Public registration creates candidates;
administrators create HR accounts. Bootstrap an administrator with
`python scripts/create_admin.py` from `recruitment-api`.

The frontend requires Node.js 20.19+ or 22.12+ (supported version ranges are in
`recruitment-client/package.json`). Use `npm ci` for reproducible installs.

## Audit and verification

See [AUDIT_REPORT.md](AUDIT_REPORT.md) for the faults found, applied fixes,
validation evidence, and remaining limitations from the October 12, 2026 audit.

```powershell
cd recruitment-api
pip install -r requirements-dev.txt
python -m pytest -q
```

```powershell
cd recruitment-client
npm ci
npm test
npm run build
npm audit
```

Verification analyzes supplied resume claims and text. Repository URLs,
credential IDs, and company references require human confirmation; supplied
links alone do not prove employment, certificate validity, or repository
activity. Hiring decisions remain with HR.

## Important Resume Rule

Incomplete or unreadable resumes are rejected. Passing the quality check does
not prove that a resume's claims are true.

Example rejected resume:

```text
Java SQL
```

Reason: It has no name, no contact, no education, no project/experience/certification, and too little readable text.

## Deployment Notes

Backend Render:

```text
Root Directory: recruitment-api
Build Command: pip install -r requirements.txt && python -m alembic upgrade head
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
