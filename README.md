# FitStack

AI-assisted adaptive fitness programming. The repository contains a React/Vite frontend and a FastAPI/PostgreSQL backend.

## Backend quick start

Prerequisites: Python 3.11+ and Docker.

```bash
cp .env.example .env
docker compose up -d --wait db
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
alembic upgrade head
cd backend
fastapi dev main.py
```

API documentation is available at `http://localhost:8000/docs`; the health check is `GET /health`.

Run backend tests from the repository root:

```bash
pytest
```

## Current API

- `POST /api/v1/profiles` creates an onboarding profile with goal, experience, equipment, weekly availability, session limits, and hard injury exclusions.
- `GET /api/v1/profiles/{id}` returns the profile.

The database schema is managed with Alembic. Do not call `Base.metadata.create_all()` in application startup; apply migrations instead.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

The configured development origin is `http://localhost:5173`.
