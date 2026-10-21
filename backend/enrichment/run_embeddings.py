# run_embeddings.py

import asyncio
import models

from sqlalchemy import select, or_

from database.database import AsyncSessionLocal
from models.exercise import Exercise
from enrichment.embeddings import generate_embedding, EMBEDDING_MODEL

#Reembded the exercises that used gemini as we are using openai model
async def reembed_exercises():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Exercise).where(
                Exercise.searchable_text.is_not(None),
                or_(
                    Exercise.embedding_model.is_(None),
                    Exercise.embedding_model != EMBEDDING_MODEL,
                    Exercise.embedding.is_(None),
                ),
            )
        )

        exercises = result.scalars().all()

        print(f"Found {len(exercises)} exercises to re-embed.")

        for index, exercise in enumerate(exercises, start=1):
            print(f"[{index}/{len(exercises)}] {exercise.name}")

            exercise.embedding = await generate_embedding(
                exercise.searchable_text
            )
            exercise.embedding_model = EMBEDDING_MODEL

            await db.commit()

        print("Embedding update complete.")


if __name__ == "__main__":
    asyncio.run(reembed_exercises())