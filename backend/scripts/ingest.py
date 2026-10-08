"""
Fetches the Kinetic exercises dataset (kinetic-place/exercises-db) and
upserts it into the `exercises` table.
 
Run directly:
    python ingest_exercises.py
"""
 
import asyncio
 
import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
 
from database.database import AsyncSessionLocal
from models.exercise import Exercise
from scripts.kinetic_client import fetch_all_exercises

# Fields that exist in the enrichment step are intentionally left out here —
# this script only sets the fields the raw dataset actually provides.
UPDATE_COLUMNS = [
    "name",
    "type",
    "difficulty_level",
    "force_type",
    "mechanics",
    "category",
    "instructions",
    "primary_muscles",
    "secondary_muscles",
    "tertiary_muscles",
    "equipment_required",
]
 
 
 
def _map_exercise(exercise: dict) -> dict:
    """Convert one raw exercise dict into a row matching the Exercise model."""
    primary_muscles: list[str] = []
    secondary_muscles: list[str] = []
    tertiary_muscles: list[str] = []
 
    for muscle in exercise.get("muscleGroups", []):
        name = muscle["name"]
        muscle_type = muscle.get("type")
        if muscle_type == "primary":
            primary_muscles.append(name)
        elif muscle_type == "secondary":
            secondary_muscles.append(name)
        elif muscle_type == "tertiary":
            tertiary_muscles.append(name)
 
    equipment_required = [item["name"] for item in exercise.get("equipment", [])]
 
    return {
        "exercise_id": exercise["id"],
        "name": exercise["name"],
        "type": exercise["type"],
        # The source dataset allows null for these four fields, but the
        # Exercise model has them as NOT NULL — coalescing to "unknown"
        # here so ingestion doesn't crash on rows with missing values.
        # Decide if "unknown" is the right placeholder for your app, or
        # if these columns should be made nullable instead.
        "difficulty_level": exercise.get("difficultyLevel") or "unknown",
        "force_type": exercise.get("forceType") or "unknown",
        "mechanics": exercise.get("mechanics") or "unknown",
        "category": exercise.get("category") or "unknown",
        "instructions": " ".join(exercise.get("instructions", [])),
        "primary_muscles": primary_muscles,
        "secondary_muscles": secondary_muscles,
        "tertiary_muscles": tertiary_muscles,
        "equipment_required": equipment_required
    }
 
#Populate the exercise data into the database
async def populate_exercise_table(exercises: list[dict], db: AsyncSession) -> None:
    """Upsert every exercise in one statement, keyed on exercise_id."""
    rows = [_map_exercise(exercise) for exercise in exercises]
    if not rows:
        return

    stmt = pg_insert(Exercise.__table__).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["exercise_id"],
        set_={col: stmt.excluded[col] for col in UPDATE_COLUMNS},
    )
    await db.execute(stmt)
    await db.commit()
 
 
async def main() -> None:
    exercises = fetch_all_exercises()
    async with AsyncSessionLocal() as db:
        await populate_exercise_table(exercises, db)
    print(f"Upserted {len(exercises)} exercises.")
 
 
if __name__ == "__main__":
    asyncio.run(main())