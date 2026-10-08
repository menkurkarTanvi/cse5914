import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from models.exercise import Exercise

from .gemini_client import enrich_with_gemini
from .searchable_text import build_searchable_text
from .embeddings import generate_embedding


EMBEDDING_MODEL = "gemini-embedding-001"


async def enrich_exercise(
    db: AsyncSession,
    exercise: Exercise,
) -> Exercise:

    # 1. Gemini classification — sync network call, offload to a thread
    enrichment = await asyncio.to_thread(enrich_with_gemini, exercise)

    exercise.exercise_family = enrichment.exercise_family
    exercise.movement_pattern = enrichment.movement_pattern
    exercise.training_role = enrichment.training_role
    exercise.unilateral = enrichment.unilateral
    exercise.load_type = enrichment.load_type
    exercise.progression_methods = enrichment.progression_methods
    exercise.substitution_group = enrichment.substitution_group
    exercise.goal_suitability = enrichment.goal_suitability
    exercise.mobility_requirements = enrichment.mobility_requirements
    exercise.balance_requirement = enrichment.balance_requirement
    exercise.stability_requirement = enrichment.stability_requirement
    exercise.fatigue_cost = enrichment.fatigue_cost

    # 2. Build searchable text
    exercise.searchable_text = build_searchable_text(exercise)

    # 3. Generate embedding — also sync, also offload
    exercise.embedding = await asyncio.to_thread(
        generate_embedding, exercise.searchable_text
    )
    exercise.embedding_model = EMBEDDING_MODEL

    db.add(exercise)

    return exercise