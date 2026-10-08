from sqlalchemy import select

from models.exercise import Exercise
from enrichment.enrich_exercise import enrich_exercise
from database.database import AsyncSessionLocal
import asyncio


async def enrich_all_exercises():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Exercise)
            .where(Exercise.exercise_family.is_(None))
            .limit(5)
        )
        exercises = result.scalars().all()

        print(f"Found {len(exercises)} exercises to enrich.")

        for i, exercise in enumerate(exercises, start=1):
            print(f"[{i}/{len(exercises)}] {exercise.name}")
            try:
                async with db.begin_nested():
                    await enrich_exercise(db=db, exercise=exercise)
                await db.commit()
                print(f"Exercise {i} enriched")
            except Exception as e:
                print(f"Exercise {i} failed to enrich: {e}")
        print("Enrichment complete.")


if __name__ == "__main__":
    asyncio.run(enrich_all_exercises())