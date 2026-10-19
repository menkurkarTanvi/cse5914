# FitStack

An AI fitness coach that generates customized weekly workout plans from a user's goals, schedule and equipment, then adjusts them from logged workouts and feedback.

- **Frontend:** React
- **Backend:** FastAPI, async SQLAlchemy, Alembic
- **Database:** PostgreSQL with the pgvector extension, run in Docker
- **Agent:** LangGraph

This guide gets you from a fresh clone to running the backend tests. It also covers loading the exercise data so you can run the full app.

## What you need

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Python 3.13
- Git
- Node.js (only for the frontend)

You **do not** need an OpenAI API key, and you do not need to run exercise ingestion or enrichment. The tests create their own data, and the exercise data is shared as ready-made CSV files.

The commands below are for PowerShell on Windows. Run them from the `backend` folder unless a step says otherwise.

## 1. Get the code and data files

Clone the repo. Then get these two files from the team ([TODO: add shared drive link]) and save them as:

- `backend/data/exercises.csv` (899 exercises, already enriched and embedded)
- `backend/data/exercise_prescriptions.csv` (2,223 rows)

They are only needed in step 7, for running the app with real exercises. They are about 19 MB because of the embeddings, so don't commit them.

## 2. Set up Python

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install pytest pytest-asyncio httpx
```

If PowerShell blocks the activate script, run this once and try again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Your prompt should show `(.venv)` once the environment is active.

## 3. Create `backend/.env`

Do not commit this file.

```
DATABASE_URL=postgresql+asyncpg://fitstack:fitstack@localhost:5450/fitstack
TEST_DATABASE_URL=postgresql+asyncpg://fitstack:fitstack@localhost:5450/test_db
SECRET_KEY=<paste the output of the command below>
```

Generate a secret key:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

If you set `DB_PASSWORD` in the environment, use that password in both URLs instead of `fitstack`.

If an import fails with a `KeyError` for the OpenAI key, add `OPENAI_API_KEY=dummy` to the file. The tests never call the API.

## 4. Start the database

Run this from the folder that contains `docker-compose.yml`:

```powershell
docker compose up -d
docker compose ps
```

Wait until the `db` service shows `healthy`. The database is published on port **5450**.

## 5. Create the test database (once)

```powershell
docker compose exec db psql -U fitstack -d fitstack -c "CREATE DATABASE test_db;"
docker compose exec db psql -U fitstack -d test_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker compose exec db psql -U fitstack -d fitstack -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## 6. Run the tests

```powershell
python -m pytest -v
```

Useful variations:

```powershell
python -m pytest tests/test_users.py -v      # one file
python -m pytest -k login -v                 # tests with "login" in the name
python -m pytest -q                          # less output
```

How the tests work:

- Migrations run automatically on `test_db` at the start of the session.
- Every test runs inside a transaction that is rolled back, so tests don't affect each other and no data is left behind.
- The suite refuses to run unless the database name contains `test`, so it cannot touch your development data.
- Tests that need a user, profile or exercises build them with fixtures in `tests/conftest.py`. They don't need the CSV files.

## 7. Run the app with real data (optional)

This loads the exercise data into the development database. Do it once.

Create the tables (from `backend`):

```powershell
python -m alembic upgrade head
```

Copy the CSVs into the container and load them. Run these from the folder that contains `docker-compose.yml`, and adjust the `backend/data/` path if yours differs. Load `exercises` first, because prescriptions refer to it.

```powershell
docker compose cp backend/data/exercises.csv db:/tmp/exercises.csv
docker compose cp backend/data/exercise_prescriptions.csv db:/tmp/exercise_prescriptions.csv

docker compose exec db psql -U fitstack -d fitstack -c "\copy exercises (exercise_id,name,type,difficulty_level,force_type,mechanics,category,instructions,primary_muscles,secondary_muscles,tertiary_muscles,equipment_required,exercise_family,movement_pattern,training_role,unilateral,load_type,progression_methods,substitution_group,goal_suitability,mobility_requirements,balance_requirement,stability_requirement,fatigue_cost,embedding,searchable_text,embedding_model) FROM '/tmp/exercises.csv' WITH (FORMAT csv, HEADER true)"

docker compose exec db psql -U fitstack -d fitstack -c "\copy exercise_prescriptions (prescription_id,exercise_id,goal,sets_min,sets_max,reps_min,reps_max,rest_seconds,target_rpe_min,target_rpe_max) FROM '/tmp/exercise_prescriptions.csv' WITH (FORMAT csv, HEADER true)"
```

Check the row counts:

```powershell
docker compose exec db psql -U fitstack -d fitstack -c "SELECT count(*) FROM exercises;"
docker compose exec db psql -U fitstack -d fitstack -c "SELECT count(*) FROM exercise_prescriptions;"
```

You should see **899** and **2223**.

Only load into empty tables. To start over, run `docker compose down -v`, which deletes everything in the database, then repeat steps 4, 5 and 7.

Start the backend (from `backend`):

```powershell
uvicorn main:app --reload
```

Start the frontend, from the folder that contains the React app's `package.json`:

```powershell
npm install
npm run dev
```

Then register an account in the app. Users, profiles and workout programs are created in your own local database.

## Database migrations (Alembic)

Alembic manages the database schema. Run these from `backend` with the virtual environment active. They act on the database in `DATABASE_URL`.

**Everyone:**

```powershell
python -m alembic upgrade head     # apply all migrations. Run it after pulling new migration files
python -m alembic current          # which revision the database is at
python -m alembic history          # list all migrations
```

The test suite runs `upgrade head` on `test_db` by itself, so new migrations reach the tests automatically.

**If you change a model:**

1. Edit the model in `models/`. Make sure it is imported in `models/__init__.py`, or Alembic can't see it.
2. Generate a migration:

   ```powershell
   python -m alembic revision --autogenerate -m "short description"
   ```

3. Open the new file in `alembic/versions/` and **read it before applying it**. Autogenerate can miss changes or include unrelated ones. Two things to look for:
   - Adding a `NOT NULL` column to a table that already has rows fails. Make the column `nullable=True`, or add a `server_default`.
   - `op.drop_constraint(None, ...)` has no constraint name and fails when the migration is downgraded. Replace `None` with the real name.
4. Apply it: `python -m alembic upgrade head`
5. Commit the migration file together with the model change.

**Check that models and migrations agree:**

```powershell
python -m alembic check
```

It reports "No new upgrade operations detected" when they match. Run it against a database built only from migrations, because a database created any other way can hide missing migrations. For example, against `test_db`:

```powershell
$env:DATABASE_URL = "postgresql+asyncpg://fitstack:fitstack@localhost:5450/test_db"
python -m alembic upgrade head
python -m alembic check
Remove-Item Env:DATABASE_URL
```

**Undo the last migration** (development database only; it can delete data):

```powershell
python -m alembic downgrade -1
```

**Two people created migrations at the same time.** Pull first and rebase your migration where you can. If Alembic reports multiple heads:

```powershell
python -m alembic heads
python -m alembic merge heads -m "merge migrations"
python -m alembic upgrade head
```

## Stopping and resetting

```powershell
docker compose down        # stop the database, keep the data
docker compose down -v     # stop the database and delete all data
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'sqlalchemy'` | The virtual environment isn't active. Activate it, and use `python -m pytest` rather than bare `pytest`. |
| `role "postgres" does not exist` or a password error | The URLs must use the user `fitstack`, with the password from `DB_PASSWORD` (default `fitstack`). |
| `database "test_db" does not exist` | Repeat step 5. |
| `type "vector" does not exist` | Run `CREATE EXTENSION IF NOT EXISTS vector;` in that database (step 5). |
| Connection refused | Docker isn't running or the database isn't healthy yet. Check `docker compose ps`. |
| Port 5450 is already in use | Change the port in `docker-compose.yml` and in both URLs in `.env`. |
| `relation "..." already exists` during `upgrade head` | The tables were created before migrations ran. Reset with `docker compose down -v`, then repeat steps 4, 5 and 7. |
| `Multiple head revisions are present` | Two migrations were created in parallel. See "Two people created migrations" in the migrations section. |
| `Can't locate revision ...` | You're missing a migration file. Pull the latest code and try again. |
| `column "..." contains null values` during `upgrade head` | A migration adds a `NOT NULL` column to a table that has rows. Edit that migration to make the column nullable or give it a default. |
| Teardown error mentioning `DROP CONSTRAINT ... it has no name` | The tests passed. The error comes from an optional downgrade at the end of `tests/conftest.py`. Delete that line. |
| Output is full of SQL statements | Set `echo=False` in `database/database.py`. |

## Keeping the data files current

The CSVs match the database schema at a specific migration. If the models change, re-export both tables from a database at the latest migration and share the new files. Otherwise the `\copy` column lists in step 7 won't match.