# FitStack

AI-assisted adaptive fitness programming. The repository contains a React/Vite frontend and a FastAPI/PostgreSQL backend.

## Backend quick start

Prerequisites: Python 3.11+ and Docker.

```bash
cp .env.example .env    # then fill in SECRET_KEY (and GOOGLE_API_KEY for the AI coach)
docker compose up -d --wait db
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
alembic upgrade head
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

## Data

From `backend/`, `python -m scripts.ingest` pulls the full exercise catalog (899 exercises) from the Kinetic API (`https://api.kinetic.place`) and upserts it into the `exercises` table. Running it as `python scripts/ingest.py` fails with `No module named 'database'`.

## AI coach

The AI Coach chat is `POST /coach/chat` (a LangGraph agent in `backend/agent/nodes/coach*.py`, tunable values in `backend/agent/coach_rules.py`). It answers exercise questions and can swap an exercise, shorten today's workout, or make it easier or harder, asking follow-up questions when it needs more detail. Changes are only saved after you confirm them.

It uses Gemini, so add a free API key from <https://aistudio.google.com/apikey> to `.env` as `GOOGLE_API_KEY`. Without it the route returns 503.

### Try it in your terminal

The frontend's AI Coach page isn't connected yet, so test it with `backend/scripts/coach_chat.py`. From `backend/`, with the virtual environment active:

```bash
python -m scripts.ingest              # once, if your exercises table is empty
python scripts/coach_chat.py --seed   # once: two demo users with 4-week plans
fastapi dev main.py                   # leave this running
```

Then in a second terminal (also in `backend/`, with the virtual environment active):

```bash
python scripts/coach_chat.py          # chat as the gym demo user
python scripts/coach_chat.py knee     # bodyweight beginner with a bad knee
python scripts/coach_chat.py you@example.com   # any account that has a profile
```

Things to try:

- "I want to shorten my workout today", then answer with a number of minutes, then "yes"
- "Swap the bench press, I don't have a barbell", then pick an option by number
- "Make the whole workout harder", then "no"
- "How do I do a goblet squat?"

After each reply the script shows the intent the coach picked and whether it's waiting for your answer. Type `reset` for a new conversation and `quit` to stop.

Confirmed changes are saved to that demo user's workout in your local database. To see them, look at `workout_plan_exercises` (for example `docker compose exec db psql -U fitstack -d fitstack`). To undo them, run `python scripts/coach_chat.py --reset`, which rebuilds both demo users' plans.

Each message uses your Gemini free-tier quota. If the coach says it's busy, wait a minute and try again.

### Tests

The coach tests use a fake model and need no API key. The shared `conftest.py` requires `TEST_DATABASE_URL`, so without one run:

```bash
pytest backend/tests/test_coach_*.py --noconftest
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

The configured development origin is `http://localhost:5173`.
